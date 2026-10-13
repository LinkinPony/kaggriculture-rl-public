// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Init_c35312f21925818ec9c8(Context& c, const ScopePtr& s) {
auto v17946 = Value{};
s->Set("_EXP303_RESOURCE_RUN", v17946);
auto v17947 = Value{};
s->Set("_EXP303_RESOURCE_PRICES", v17947);
auto v17948 = Value{};
s->Set("_EXP303_RESOURCES", v17948);
s->Set("_exp303_resources", Define(&Code_b2baf0d7104a2962778e, s, Signature{{"run", "prices"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"entries", "farm", "fertilizer", "harvest", "item", "key", "mature", "offset", "prices", "private", "row", "run", "snapshots", "tile", "x", "y"}; return names; }())}, false, "_exp303_resources"));
s->Set("_proposals", Define(&Code_0e670e0d0edfb4d06c2c, s, Signature{{"run", "actor", "prices", "max_per_actor"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"_", "actor", "bundles", "carried", "chosen", "cursor", "direct", "distance", "event", "farm", "fertilizer", "first", "future_deposits", "harvest", "horizon", "inventory", "key", "max_per_actor", "obligation", "offset", "operations", "ops", "owners", "pos", "prefix_deposits", "prices", "private", "proposals", "route", "run", "second", "seen", "stops", "value", "variants", "xy"}; return names; }())}, false, "_proposals"));
return {};
}
}  // namespace kagg::opponents::compiled
