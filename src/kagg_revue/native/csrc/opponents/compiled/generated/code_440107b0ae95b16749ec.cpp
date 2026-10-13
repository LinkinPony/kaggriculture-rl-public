// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_440107b0ae95b16749ec(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"o"};
s->PrepareSlots(s_names);
return ([&]() -> Value { auto fn6414 = s->Global("_r37_quote_priority"); Arguments args6415; args6415.positional.reserve(3); args6415.Add(s->Captured("observation"), false); args6415.Add(s->LocalAt(0), false); args6415.Add(s->Captured("stock"), false); return Call(c, fn6414, std::move(args6415)); }());
return {};
}
}  // namespace kagg::opponents::compiled
