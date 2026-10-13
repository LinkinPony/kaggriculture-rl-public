// Native ownership invariants for offline regression qualification.
#include "opponents/compiled/runtime.hpp"

namespace kagg::opponents::compiled {
bool ValidateDictionaryGet() {
  Context context;
  auto dictionary = Dict({{"answer", 1}});
  auto captured = PrepareDictionaryGet(dictionary);
  Put(dictionary, "answer", 42);
  SetAttribute(dictionary, "get", Builtin("len"));
  if (!Equal(CallDictionaryGet(context, captured, {{"answer"}, {}}), 42) ||
      !Equal(CallDictionaryGet(context, captured, {{"missing", 7}, {}}), 7))
    return false;
  auto overridden = PrepareDictionaryGet(dictionary);
  SetAttribute(dictionary, "get", Builtin("bool"));
  if (!Equal(CallDictionaryGet(context, overridden, {{List({1, 2})}, {}}), 2) ||
      context.calls != 3)
    return false;
  try {
    PrepareDictionaryGet(1);
  } catch (const Error& error) {
    return error.type == "AttributeError";
  }
  return false;
}

bool ValidateClosureLifetimes() {
  Value globals = Dict();
  std::weak_ptr<Scope> frame;
  {
    static constexpr const char* names[] = {"answer", "alias", "helper", "missing"};
    auto scope = std::make_shared<Scope>();
    ScopeCleanup cleanup{scope};
    scope->globals = globals;
    scope->Set("answer", 42);
    scope->PrepareSlots(names);
    if (!Equal(scope->LocalAt(0), 42)) return false;
    scope->SetAt(3, {});
    if (!scope->LocalAt(3).none()) return false;
    scope->EraseAt(3);
    bool unbound = false;
    try { scope->LocalAt(3); }
    catch (const Error& error) { unbound = error.type == "UnboundLocalError"; }
    if (!unbound) return false;
    auto helper = Define(nullptr, scope, {}, true, "helper");
    scope->SetAt(1, helper);
    scope->SetAt(2, helper);
    auto child = std::make_shared<Scope>();
    child->parent = scope;
    if (!Equal(child->Captured("answer"), 42)) return false;
    // The session clone owns independent captured slots and keeps aliasing.
    auto clone = DeepCopy(helper, true);
    auto copied = clone.node()->function->closure;
    ScopeCleanup copied_cleanup{copied};
    copied->SetAt(0, 7);
    if (!Equal(scope->LocalAt(0), 42) || !Equal(copied->LocalAt(0), 7) ||
        !Identical(copied->LocalAt(1), copied->LocalAt(2))) return false;
    frame = scope;
  }
  if (!frame.expired()) return false;
  {
    auto scope = std::make_shared<Scope>();
    ScopeCleanup cleanup{scope};
    scope->globals = globals;
    auto helper = Define(nullptr, scope, {}, true, "<lambda>");
    scope->Set("helper", helper);
    scope->Set("alias", helper);
    frame = scope;
  }
  if (!frame.expired()) return false;
  Value escaped;
  {
    auto scope = std::make_shared<Scope>();
    ScopeCleanup cleanup{scope};
    scope->globals = globals;
    scope->Set("answer", 42);
    escaped = Define(nullptr, scope, {}, true, "escaped");
    scope->Set("escaped", escaped);
    frame = scope;
  }
  if (frame.expired() ||
      !Equal(Get(escaped.node()->function->closure->locals, "answer"), 42))
    return false;
  escaped = {};
  return frame.expired();
}
}  // namespace kagg::opponents::compiled
