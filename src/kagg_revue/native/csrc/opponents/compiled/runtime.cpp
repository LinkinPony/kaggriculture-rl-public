#include "opponents/compiled/runtime.hpp"
#include "opponents/compiled/profiling.hpp"

#include <algorithm>

namespace kagg::opponents::compiled {
void Arguments::Add(Value value, bool expand) {
  if (expand) {
    auto values = Iterate(value);
    positional.insert(positional.end(), values.begin(), values.end());
  } else
    positional.push_back(std::move(value));
}
void Arguments::Keyword(std::string name, Value value) {
  for (const auto& [key, old] : keywords)
    if (key == name) throw Error("TypeError", "duplicate keyword " + name);
  keywords.emplace_back(std::move(name), std::move(value));
}
void Arguments::ExpandKeywords(const Value& value) {
  if (!Is(value, Kind::kDict))
    throw Error("TypeError", "keyword expansion requires dictionary");
  for (const auto& [key, item] : value.node()->entries)
    Keyword(key.string(), item);
}
namespace {
const Value* Lookup(const Value& mapping, const char* name) {
  const auto& p = mapping.node();
  const auto found = p->index.find(std::string("s") + name);
  return found == p->index.end() ? nullptr : &p->entries[found->second].second;
}
}  // namespace
Value Scope::Local(const char* name) const {
  if (const auto value = FindLocal(name)) return *value;
  throw Error("UnboundLocalError", name);
}
Value Scope::Captured(const char* name) const {
  for (auto scope = parent; scope; scope = scope->parent)
    if (const auto value = scope->FindLocal(name)) return *value;
  return Global(name);
}
Value Scope::Global(const char* name) const {
  if (const auto value = Lookup(globals, name)) return *value;
  return GlobalBuiltin(name);
}
void Scope::Set(const char* name, Value value) {
  for (size_t i = 0; i < slot_names.size(); ++i) {
    if (std::string_view(slot_names[i]) == name) {
      SetAt(i, std::move(value));
      return;
    }
  }
  const auto& p = locals.node();
  const std::string key = std::string("s") + name;
  const auto found = p->index.find(key);
  if (found != p->index.end()) {
    p->entries[found->second].second = std::move(value);
    return;
  }
  p->index.emplace(key, p->entries.size());
  p->entries.emplace_back(Value(name), std::move(value));
}
ScopeCleanup::~ScopeCleanup() {
  if (scope->module) return;
  for (auto& slot : scope->slots) {
    if (slot && Is(*slot, Kind::kFunction) &&
        slot->node()->function->closure == scope)
      slot.reset();
  }
  // Named functions and locally assigned lambdas can both own this frame.
  // Drop those back-references while retaining values needed by escaped
  // closures. Frozen policies never return mutually recursive local helpers.
  Values functions;
  for (const auto& [name, value] : scope->locals.node()->entries) {
    if (Is(value, Kind::kFunction) && value.node()->function->closure == scope)
      functions.push_back(name);
  }
  for (const auto& name : functions) Erase(scope->locals, name);
  scope->globals =
      {};  // Closures retain locals; functions hold a weak global namespace.
}
void Scope::PrepareSlots(std::span<const char* const> names) {
  if (module) throw PortError("invalid local slot initialization");
  if (!slot_names.empty()) {
    if (slot_names.size() != names.size()) throw PortError("inconsistent local slot layout");
    return;
  }
  slot_names = names;
  slots.resize(names.size());
  for (size_t i = 0; i < names.size(); ++i)
    if (const auto value = Lookup(locals, names[i])) slots[i] = *value;
  // Arguments are now owned by slots. Captured frames use the same storage.
  locals = Dict();
}
const Value* Scope::FindLocal(const char* name) const {
  for (size_t i = 0; i < slot_names.size(); ++i)
    if (std::string_view(slot_names[i]) == name)
      return slots[i] ? &*slots[i] : nullptr;
  return Lookup(locals, name);
}
ScopePtr Module(Value globals) {
  auto result = std::make_shared<Scope>();
  result->globals = globals;
  result->locals = globals;
  result->module = true;
  return result;
}
Value Builtin(const std::string& name, Value bound) {
  auto p = std::make_shared<Node>(Kind::kBuiltin);
  p->text = name;
  p->base = std::move(bound);
  return Value(p);
}
Value GlobalBuiltin(const char* name) {
  const std::string key(name);
  static thread_local std::unordered_map<std::string, Value> cached;
  const auto found = cached.find(key);
  if (found != cached.end()) return found->second;
  static const std::vector<std::string> allowed = {"id", "len",
                                                   "int",
                                                   "float",
                                                   "bool",
                                                   "str",
                                                   "list",
                                                   "tuple",
                                                   "dict",
                                                   "set",
                                                   "frozenset",
                                                   "min",
                                                   "max",
                                                   "sum",
                                                   "abs",
                                                   "round",
                                                   "any",
                                                   "all",
                                                   "range",
                                                   "enumerate",
                                                   "zip",
                                                   "sorted",
                                                   "reversed",
                                                   "iter",
                                                   "next",
                                                   "map",
                                                   "getattr",
                                                   "setattr",
                                                   "hasattr",
                                                   "callable",
                                                   "isinstance",
                                                   "type",
                                                   "staticmethod",
                                                   "Exception",
                                                   "ValueError",
                                                   "TypeError",
                                                   "KeyError",
                                                   "IndexError",
                                                   "RuntimeError",
                                                   "AssertionError",
                                                   "print",
                                                   "ZeroDivisionError",
                                                   "StopIteration",
                                                   "object",
                                                   "__builtins__"};
  if (std::find(allowed.begin(), allowed.end(), key) == allowed.end())
    throw Error("NameError", key);
  return cached.emplace(key, Builtin(key)).first->second;
}
namespace {
Value ClassMember(Value cls, const std::string& name) {
  while (Is(cls, Kind::kClass)) {
    if (Contains(cls.node()->attributes, name))
      return Get(cls.node()->attributes, name);
    cls = cls.node()->base;
  }
  throw Error("AttributeError", name);
}
Value Bind(Value function, Value self) {
  if (!Is(function, Kind::kFunction) ||
      function.node()->function->static_method)
    return function;
  auto p = std::make_shared<Node>(*function.node());
  p->function = std::make_shared<Function>(*p->function);
  p->function->bound = std::move(self);
  return Value(p);
}
}  // namespace
Value Attribute(const Value& value, const std::string& name) {
  auto& p = value.node();
  if (!p) throw Error("AttributeError", name);
  if (!p->attributes.none() && Contains(p->attributes, name))
    return Get(p->attributes, name);
  if (p->kind == Kind::kClass) return ClassMember(value, name);
  if (p->kind == Kind::kObject) return Bind(ClassMember(p->base, name), value);
  if (p->kind == Kind::kSuper)
    return Bind(ClassMember(p->base.node()->base, name), p->sequence.at(0));
  if (p->kind == Kind::kChainMap && name == "maps") return List(p->sequence);
  if (p->kind == Kind::kBuiltin) return Builtin(p->text + "." + name, p->base);
  const auto accepts = [&](const std::string& methods) {
    return methods.find("|" + name + "|") != std::string::npos;
  };
  if ((p->kind == Kind::kString && accepts("|join|split|")) ||
      (p->kind == Kind::kChainMap && accepts("|get|")) ||
      (p->kind == Kind::kDict &&
       accepts("|get|items|keys|values|copy|setdefault|pop|clear|update|")) ||
      (p->kind == Kind::kList &&
       accepts(
           "|copy|pop|clear|append|extend|insert|remove|count|index|sort|reverse|")) ||
      (p->kind == Kind::kTuple && accepts("|count|index|")) ||
      (p->kind == Kind::kSet && accepts("|copy|clear|update|add|")))
    return Builtin("method." + name, value);
  throw Error("AttributeError", name);
}
Value AttributeOr(const Value& value, const std::string& name, Value fallback) {
  try {
    return Attribute(value, name);
  } catch (const Error& error) {
    if (error.type == "AttributeError") return fallback;
    throw;
  }
}
void SetAttribute(const Value& value, const std::string& name,
                  Value attribute) {
  auto& p = value.node();
  if (!p) throw Error("AttributeError", name);
  if (p->attributes.none()) p->attributes = Dict();
  Put(p->attributes, name, std::move(attribute));
}
Value Define(Code code, const ScopePtr& scope, Signature signature,
             bool capture, const std::string& name, Specialization specialization) {
  auto p = std::make_shared<Node>(Kind::kFunction);
  p->text = name;
  p->attributes = Dict();
  p->function = std::make_shared<Function>();
  p->function->code = code;
  p->function->specialization = specialization;
  p->function->signature = std::move(signature);
  const auto& sig = p->function->signature;
  for (const auto& parameter : sig.positional) {
    for (size_t i = 0; i < sig.slots.size(); ++i) {
      if (parameter == sig.slots[i]) {
        p->function->positional_slots.push_back(i);
        break;
      }
    }
  }
  if (!sig.slots.empty() && p->function->positional_slots.size() != sig.positional.size())
    throw PortError("function parameters missing from native local layout");
  p->function->globals = scope->globals.node();
  if (capture && !scope->module) p->function->closure = scope;
  return Value(p);
}
Value Class(const std::string& name, Value base, Value attributes) {
  auto p = std::make_shared<Node>(Kind::kClass);
  p->text = name;
  p->base = std::move(base);
  p->attributes = std::move(attributes);
  return Value(p);
}
Value MakeSuper(Value cls, Value self) {
  auto p = std::make_shared<Node>(Kind::kSuper);
  p->base = std::move(cls);
  p->sequence.push_back(std::move(self));
  return Value(p);
}
Value Call(Context& context, Value function, Arguments arguments) {
  ++context.calls;
  if (Is(function, Kind::kBuiltin))
    return CallBuiltin(context, function, std::move(arguments));
  if (Is(function, Kind::kClass)) {
    auto p = std::make_shared<Node>(Kind::kObject);
    p->base = function;
    p->attributes = Dict();
    Value object(p);
    auto base = function;
    while (Is(base, Kind::kClass)) base = base.node()->base;
    if (Is(base, Kind::kBuiltin) &&
        (base.node()->text == "Exception" || base.node()->text.ends_with("Error"))) {
      p->text = "exception:" + function.node()->text;
      Put(p->attributes, "message",
          arguments.positional.empty() ? Value("") : arguments.positional[0]);
      return object;
    }
    auto init = AttributeOr(object, "__init__", {});
    if (!init.none()) Call(context, init, std::move(arguments));
    return object;
  }
  if (Is(function, Kind::kObject)) {
    return Call(context, Attribute(function, "__call__"), std::move(arguments));
  }
  if (!Is(function, Kind::kFunction))
    throw Error("TypeError", "value is not callable: " + Repr(function));
  const auto fn = function.node()->function;
  const auto& sig = fn->signature;
  if (!fn->bound.none())
    arguments.positional.insert(arguments.positional.begin(), fn->bound);
  if (fn->specialization != Specialization::kNone && arguments.keywords.empty()) {
    const Value globals(fn->globals.lock());
    const auto& values = arguments.positional;
    // These guards cover only the AST-proven branch. Rebound builtins, keyword
    // arguments, missing arguments and all other types use the original body.
    if (globals.node() && fn->specialization == Specialization::kInteger &&
        values.size() >= 1 && values.size() <= 2 && values[0].integer() &&
        Lookup(globals, "int") == nullptr) {
      return Value(values[0].integer_value());
    }
    if (globals.node() && fn->specialization == Specialization::kDictGet &&
        values.size() >= 2 && values.size() <= 3 && Is(values[0], Kind::kDict) &&
        Lookup(globals, "isinstance") == nullptr && Lookup(globals, "dict") == nullptr) {
      return GetOr(values[0], values[1], values.size() == 3 ? values[2] : sig.defaults[0]);
    }
  }
  auto scope = std::make_shared<Scope>();
  scope->locals.node()->entries.reserve(sig.positional.size() + sig.keyword_only.size());
  scope->globals = Value(fn->globals.lock());
  scope->parent = fn->closure;
  if (!scope->globals.node())
    throw PortError("expired native function namespace");
  const size_t supplied = arguments.positional.size();
  if (supplied > sig.positional.size() && sig.vararg.empty())
    throw Error("TypeError", "too many arguments for " + function.node()->text);
  if (!sig.slots.empty() && arguments.keywords.empty() && sig.vararg.empty() &&
      sig.kwarg.empty() && sig.keyword_only.empty()) {
    const size_t required = sig.positional.size() - sig.defaults.size();
    if (supplied < required)
      throw Error("TypeError", "missing argument " + sig.positional[supplied]);
    scope->slot_names = sig.slots;
    scope->slots.resize(sig.slots.size());
    for (size_t i = 0; i < supplied; ++i)
      scope->SetAt(fn->positional_slots[i], std::move(arguments.positional[i]));
    for (size_t i = supplied; i < sig.positional.size(); ++i)
      scope->SetAt(fn->positional_slots[i], sig.defaults[i - required]);
    ScopeCleanup cleanup{scope};
    return kProfileFunctions ? ProfileCall(context, *fn, function.node()->text, scope)
                             : fn->code(context, scope);
  }
  for (size_t i = 0; i < std::min(supplied, sig.positional.size()); ++i)
    scope->Set(sig.positional[i].c_str(), arguments.positional[i]);
  Value extra;
  if (!sig.kwarg.empty()) extra = Dict();
  for (const auto& [k, v] : arguments.keywords) {
    const bool declared =
        std::find(sig.positional.begin(), sig.positional.end(), k) !=
            sig.positional.end() ||
        std::find(sig.keyword_only.begin(), sig.keyword_only.end(), k) !=
            sig.keyword_only.end();
    if (declared) {
      if (Lookup(scope->locals, k.c_str()) != nullptr)
        throw Error("TypeError", "duplicate argument " + k);
      scope->Set(k.c_str(), v);
    } else if (!sig.kwarg.empty())
      Put(extra, k, v);
    else
      throw Error("TypeError", "unexpected keyword " + k);
  }
  for (size_t i = std::min(supplied, sig.positional.size()); i < sig.positional.size(); ++i) {
    const auto& name = sig.positional[i];
    if (Lookup(scope->locals, name.c_str()) != nullptr) continue;
    const size_t required = sig.positional.size() - sig.defaults.size();
    if (i < required) throw Error("TypeError", "missing argument " + name);
    scope->Set(name.c_str(), sig.defaults[i - required]);
  }
  for (size_t i = 0; i < sig.keyword_only.size(); ++i)
    if (Lookup(scope->locals, sig.keyword_only[i].c_str()) == nullptr) {
      const auto value = sig.keyword_defaults.at(i);
      if (Is(value, Kind::kBuiltin) && value.node()->text == "missing")
        throw Error("TypeError", "missing keyword");
      scope->Set(sig.keyword_only[i].c_str(), value);
    }
  if (!sig.kwarg.empty()) scope->Set(sig.kwarg.c_str(), extra);
  if (!sig.vararg.empty()) {
    Values rest;
    if (supplied > sig.positional.size())
      rest.assign(arguments.positional.begin() + sig.positional.size(),
                  arguments.positional.end());
    scope->Set(sig.vararg.c_str(), Tuple(std::move(rest)));
  }
  ScopeCleanup cleanup{scope};
  return kProfileFunctions ? ProfileCall(context, *fn, function.node()->text, scope)
                           : fn->code(context, scope);
}
void Merge(const Value& target, const Value& source) {
  if (Is(source, Kind::kDict)) {
    for (const auto& [k, v] : source.node()->entries) Put(target, k, v);
  } else
    for (const auto& row : Iterate(source)) {
      auto pair = Iterate(row);
      ValidateUnpack(pair, 2, false);
      Put(target, pair[0], pair[1]);
    }
}
bool Matches(const Error& error, const Value& types) {
  if (Is(types, Kind::kTuple)) {
    for (const auto& t : Iterate(types))
      if (Matches(error, t)) return true;
    return false;
  }
  if (!types.node()) return false;
  return types.node()->text == "Exception" || types.node()->text == error.type;
}
Value MakeException(const Value& type, const Value& message) {
  auto p = std::make_shared<Node>(Kind::kObject);
  p->text = "exception:" + type.node()->text;
  p->attributes = Dict({{"message", message}});
  return Value(p);
}
void Raise(const Value& exception) {
  if (exception.node() && exception.node()->text.starts_with("exception:"))
    throw Error(exception.node()->text.substr(10),
                Repr(Get(exception.node()->attributes, "message")));
  throw Error("TypeError", "invalid exception");
}
void ValidateUnpack(const Values& values, size_t count, bool starred) {
  if (starred ? values.size() < count : values.size() != count)
    throw Error("ValueError", "unpacking size differs");
}
}  // namespace kagg::opponents::compiled
