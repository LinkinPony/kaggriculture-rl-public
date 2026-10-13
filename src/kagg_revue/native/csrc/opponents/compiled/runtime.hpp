// Native callable and object semantics for generated C++ policy functions.
#pragma once

#include <span>
#include <optional>

#include "opponents/compiled/value.hpp"

namespace kagg::opponents::compiled {
using Code = Value (*)(Context&, const ScopePtr&);

struct Arguments {
  Values positional;
  Keywords keywords;
  void Add(Value value, bool expand = false);
  void Keyword(std::string name, Value value);
  void ExpandKeywords(const Value& value);
};
struct Signature {
  std::vector<std::string> positional;
  Values defaults;
  std::vector<std::string> keyword_only;
  Values keyword_defaults;
  std::string vararg;
  std::string kwarg;
  std::span<const char* const> slots;
};
enum class Specialization { kNone, kInteger, kDictGet };
struct Function {
  Code code = nullptr;
  Signature signature;
  std::weak_ptr<Node> globals;
  ScopePtr closure;
  Value bound;
  bool static_method = false;
  Specialization specialization = Specialization::kNone;
  std::vector<size_t> positional_slots;
};
struct Scope {
  Value globals;
  Value locals = Dict();
  ScopePtr parent;
  std::vector<std::string> definitions;
  bool module = false;
  std::span<const char* const> slot_names;
  std::vector<std::optional<Value>> slots;
  void PrepareSlots(std::span<const char* const> names);
  const Value* FindLocal(const char* name) const;
  Value LocalAt(size_t index) const {
    if (!slots[index]) throw Error("UnboundLocalError", slot_names[index]);
    return *slots[index];
  }
  void SetAt(size_t index, Value value) { slots[index] = std::move(value); }
  void EraseAt(size_t index) {
    if (!slots[index]) throw Error("UnboundLocalError", slot_names[index]);
    slots[index].reset();
  }
  Value Local(const char* name) const;
  Value Captured(const char* name) const;
  Value Global(const char* name) const;
  void Set(const char* name, Value value);
};
struct ScopeCleanup {
  ScopePtr scope;
  ~ScopeCleanup();
};
struct Context {
  // Immutable decoded data is loaded once per portfolio, never per action.
  std::vector<Value> constants;
  size_t calls = 0;
};

// Resolve the receiver before arguments, preserving bound-method semantics.
struct DictionaryGet {
  Value dictionary;
  Value function;
};
DictionaryGet PrepareDictionaryGet(Value receiver);
Value CallDictionaryGet(Context& context, DictionaryGet method, Arguments arguments);

Value Builtin(const std::string& name, Value bound = {});
Value GlobalBuiltin(const char* name);
Value Attribute(const Value& value, const std::string& name);
Value AttributeOr(const Value& value, const std::string& name, Value fallback);
void SetAttribute(const Value& value, const std::string& name, Value attribute);
Value Define(Code code, const ScopePtr& scope, Signature signature,
             bool capture, const std::string& name,
             Specialization specialization = Specialization::kNone);
Value Class(const std::string& name, Value base, Value attributes);
Value MakeSuper(Value cls, Value self);
Value Call(Context& context, Value function, Arguments arguments);
Value CallBuiltin(Context& context, const Value& function, Arguments arguments);
Value CallMethod(Context& context, const std::string& method, Value self,
                 Arguments arguments);
bool InstanceOf(const Value& value, const Value& type);
ScopePtr Module(Value globals);
void Merge(const Value& target, const Value& source);
Value MakeException(const Value& type, const Value& message);
bool Matches(const Error& error, const Value& types);
void Raise(const Value& exception);
void ValidateUnpack(const Values& values, size_t count, bool starred);
bool ValidateClosureLifetimes();
bool ValidateDictionaryGet();

}  // namespace kagg::opponents::compiled
