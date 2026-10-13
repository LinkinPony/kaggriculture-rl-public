// Checked boundaries for typed kernels; unsupported inputs use generated source.
#pragma once

#include "opponents/compiled/typed.hpp"

namespace kagg::opponents::compiled::typed {
struct Unsupported {};
inline const Value& Field(const Value& object, const char* key) {
  if (!Is(object, Kind::kDict)) throw Unsupported{};
  const auto& node = object.node();
  auto found = node->index.find(std::string("s") + key);
  if (found == node->index.end()) throw Unsupported{};
  return node->entries[found->second].second;
}
inline const Value& Maybe(const Value& object, const char* key) {
  if (!Is(object, Kind::kDict)) throw Unsupported{};
  static const Value missing;
  const auto& node = object.node();
  auto found = node->index.find(std::string("s") + key);
  return found == node->index.end() ? missing : node->entries[found->second].second;
}
inline const Value& Member(const Value& object, const char* key) {
  if (!object.node() || !Is(object.node()->attributes, Kind::kDict)) throw Unsupported{};
  return Field(object.node()->attributes, key);
}
inline const Values& Sequence(const Value& value) {
  if (!Is(value, Kind::kList) && !Is(value, Kind::kTuple)) throw Unsupported{};
  return value.node()->sequence;
}
inline int64_t Integer(const Value& value) {
  if (!value.integer() || value.number() < -1000000000 || value.number() > 1000000000)
    throw Unsupported{};
  return value.integer_value();
}
inline Value Dictionary(const Value& value) {
  if (!Is(value, Kind::kDict)) throw Unsupported{};
  return Dict(value.node()->entries);
}
inline void Builtins(const ScopePtr& scope, std::initializer_list<const char*> names) {
  for (const auto* name : names)
    if (Contains(scope->globals, name)) throw Unsupported{};
}
inline void Helper(const ScopePtr& scope, const char* name, Specialization kind) {
  const auto function = scope->Global(name);
  if (!Is(function, Kind::kFunction) || function.node()->function->specialization != kind)
    throw Unsupported{};
}
}  // namespace kagg::opponents::compiled::typed
