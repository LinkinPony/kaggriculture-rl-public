"""Execute generated cleanup on successful returns and exceptional policy calls."""

import ast
import subprocess
from pathlib import Path

import pytest

from kagg_revue.opponents.compilation.compiler import Compiler
from kagg_revue.opponents.compilation.model import Lexical, Program


def test_generated_finally_restores_on_return_and_exception(tmp_path: Path) -> None:
    """Run emitted C++, checking single evaluation and cleanup exception precedence."""
    tree = ast.parse("def policy():\n    try: return pending\n    finally: restored = True\n")
    function = tree.body[0]
    assert isinstance(function, ast.FunctionDef)
    program = Program()
    Compiler(program, Lexical(module=True)).function(function)
    name, body = next(iter(program.functions.items()))
    harness = r"""
#include <memory>
#include <span>
#include <stdexcept>
using Value = int;
struct Context {};
struct Scope {
  bool fail = false;
  bool cleanup_fails = false;
  int calls = 0;
  int restored = 0;
  Value Global(const char*) {
    ++calls;
    if (fail) throw std::runtime_error("policy failure");
    return 7;
  }
  void Set(const char*, Value value) {
    restored = value;
    if (cleanup_fails) throw std::logic_error("cleanup failure");
  }
  void PrepareSlots(std::span<const char* const>) {}
  void SetAt(size_t, Value value) { Set(nullptr, value); }
};
using ScopePtr = std::shared_ptr<Scope>;
"""
    driver = r"""
int main() {
  Context context;
  for (bool fail : {false, true}) {
    for (bool cleanup_fails : {false, true}) {
      auto scope = std::make_shared<Scope>();
      scope->fail = fail;
      scope->cleanup_fails = cleanup_fails;
      int caught = 0;
      try {
        if (POLICY(context, scope) != 7) return 1;
      } catch (const std::logic_error&) {
        caught = 2;
      } catch (const std::runtime_error&) {
        caught = 1;
      }
      const int expected = cleanup_fails ? 2 : fail ? 1 : 0;
      if (caught != expected || scope->restored != 1 || scope->calls != 1) return 2;
    }
  }
}
"""
    source = tmp_path / "finally.cpp"
    source.write_text(harness + body + driver.replace("POLICY", name))
    executable = tmp_path / "finally"
    subprocess.run(["c++", "-std=c++20", str(source), "-o", str(executable)], check=True)
    subprocess.run([str(executable)], check=True)


def test_finally_rejects_unimplemented_control_flow() -> None:
    """Reject broader syntax instead of silently dropping its cleanup semantics."""
    tree = ast.parse("try:\n    pending = 7\nfinally:\n    restored = True\n")
    with pytest.raises(TypeError, match="single try-return"):
        Compiler(Program(), Lexical(module=True)).module_code(tree, "unsupported")
