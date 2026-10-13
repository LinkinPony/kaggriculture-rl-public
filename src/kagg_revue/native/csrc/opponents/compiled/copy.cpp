#include <unordered_set>

#include "opponents/compiled/runtime.hpp"

namespace kagg::opponents::compiled {
namespace {
struct Copier {
  bool session;
  std::unordered_map<const Node*, Value> nodes;
  std::unordered_map<const Scope*, ScopePtr> scopes;

  ScopePtr ScopeCopy(const ScopePtr& scope) {
    if (!scope) return {};
    if (auto it = scopes.find(scope.get()); it != scopes.end())
      return it->second;
    auto out = std::make_shared<Scope>();
    scopes.emplace(scope.get(), out);
    out->globals = Copy(scope->globals);
    out->locals = Copy(scope->locals);
    out->parent = ScopeCopy(scope->parent);
    out->definitions = scope->definitions;
    out->module = scope->module;
    out->slot_names = scope->slot_names;
    for (const auto& slot : scope->slots)
      out->slots.push_back(slot ? std::optional<Value>(Copy(*slot)) : std::nullopt);
    return out;
  }
  Value Copy(const Value& value) {
    const auto& p = value.node();
    if (!p || p->kind == Kind::kString || p->kind == Kind::kBytes ||
        (session && p->frozen)) return value;
    if (!session && (p->kind == Kind::kFunction || p->kind == Kind::kClass ||
                     p->kind == Kind::kBuiltin))
      return value;
    if (auto it = nodes.find(p.get()); it != nodes.end()) return it->second;
    auto n = std::make_shared<Node>(p->kind);
    Value out(n);
    nodes.emplace(p.get(), out);
    n->text = p->text;
    n->position = p->position;
    for (const auto& x : p->sequence) n->sequence.push_back(Copy(x));
    for (const auto& [k, v] : p->entries) {
      n->index.emplace(Key(k), n->entries.size());
      n->entries.emplace_back(Copy(k), Copy(v));
    }
    n->base = Copy(p->base);
    n->attributes = Copy(p->attributes);
    if (p->function) {
      auto f = std::make_shared<Function>(*p->function);
      n->function = f;
      f->globals = Copy(Value(p->function->globals.lock())).node();
      f->closure = ScopeCopy(p->function->closure);
      f->bound = Copy(p->function->bound);
      for (auto& v : f->signature.defaults) v = Copy(v);
      for (auto& v : f->signature.keyword_defaults) v = Copy(v);
    }
    return out;
  }
};
void Mark(const Value& value, std::unordered_set<const Node*>* seen) {
  const auto& p = value.node();
  if (!p || !seen->insert(p.get()).second) return;
  if (p->kind != Kind::kDict && p->kind != Kind::kList &&
      p->kind != Kind::kTuple && p->kind != Kind::kString && p->kind != Kind::kBytes)
    throw PortError("only immutable route data may be frozen");
  p->frozen = true;
  for (const auto& v : p->sequence) Mark(v, seen);
  for (const auto& [k, v] : p->entries) {
    Mark(k, seen);
    Mark(v, seen);
  }
}
}  // namespace
Value DeepCopy(const Value& value, bool session) {
  return Copier{session, {}, {}}.Copy(value);
}
void Freeze(const Value& value) {
  std::unordered_set<const Node*> seen;
  Mark(value, &seen);
}
}  // namespace kagg::opponents::compiled
