"""Run generated nested loop control flow, including exhaustion and targeted breaks."""

import ast
import subprocess
from pathlib import Path

from kagg_revue.opponents.compilation.compiler import Compiler
from kagg_revue.opponents.compilation.model import Lexical, Program


def test_nested_loop_else(tmp_path: Path) -> None:
    """Inner breaks must not suppress an outer else; empty loops must exhaust."""
    tree = ast.parse("""
def policy():
    for item in items:
        for child in children:
            break
        else:
            continue
        if stop:
            break
    else:
        return 9
    return 7
""")
    function = tree.body[0]
    assert isinstance(function, ast.FunctionDef)
    program = Program()
    Compiler(program, Lexical(module=True)).function(function)
    name, body = next(iter(program.functions.items()))
    harness = r"""
#include <memory>
#include <span>
#include <string>
#include <unordered_map>
#include <vector>
using Value = int;
struct Context {};
struct Scope {
  std::unordered_map<std::string, Value> values;
  Value Global(const char* key) { return values.at(key); }
  void Set(const char* key, Value value) { values[key] = value; }
  void PrepareSlots(std::span<const char* const>) {}
  void SetAt(size_t, Value) {}
};
using ScopePtr = std::shared_ptr<Scope>;
std::vector<Value> Iterate(Value count) { return std::vector<Value>(count, 1); }
"""
    driver = r"""
int main() {
  Context context;
  for (int items : {0, 2}) for (int children : {0, 2}) for (int stop : {0, 1}) {
    auto scope = std::make_shared<Scope>();
    scope->values = {{"items", items}, {"children", children}, {"stop", stop}};
    if (POLICY(context, scope) != (items && children && stop ? 7 : 9)) return 1;
  }
}
"""
    source = tmp_path / "loops.cpp"
    source.write_text(harness + body + driver.replace("POLICY", name))
    executable = tmp_path / "loops"
    subprocess.run(["c++", "-std=c++20", str(source), "-o", str(executable)], check=True)
    subprocess.run([str(executable)], check=True)
