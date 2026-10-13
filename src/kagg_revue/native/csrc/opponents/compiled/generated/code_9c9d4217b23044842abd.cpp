// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_9c9d4217b23044842abd(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"cache", "i", "inv0", "item", "margin", "opp", "opp_schedules", "order", "padded", "params", "stock"};
s->PrepareSlots(s_names);
auto v19324 = ([&]() -> Value { auto dict19325 = Dict(); return dict19325; }());
s->SetAt(0, v19324);
auto v19326 = ([&]() -> Value { auto dict19327 = Dict(); return dict19327; }());
s->SetAt(6, v19326);
for (const auto& item19328 : Iterate(([&]() -> Value { auto fn19329 = s->Global("enumerate"); Arguments args19330; args19330.Add(s->LocalAt(5), false); return Call(c, fn19329, std::move(args19330)); }()))) {
auto unpack19331 = Iterate(item19328);
ValidateUnpack(unpack19331, 2, false);
s->SetAt(1, unpack19331.at(0));
s->SetAt(7, unpack19331.at(1));
if (static_cast<bool>(([&]() -> Value { auto v19332 = s->LocalAt(7); if (!static_cast<bool>(v19332)) return v19332; v19332 = ([&]() -> Value { auto v19333 = ([&]() -> Value { auto fn19335 = s->Global("len"); Arguments args19336; args19336.Add(s->LocalAt(7), false); return Call(c, fn19335, std::move(args19336)); }()); Value v19334; v19334 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v19333, v19334))) return Value(false); v19333 = v19334; return Value(true); }()); if (!static_cast<bool>(v19332)) return v19332; v19332 = ([&]() -> Value { auto v19337 = Get(s->LocalAt(7), Value(int64_t{0})); Value v19338; v19338 = Tuple({Value("SELL"), Value("BUY_PRODUCT")}); if (!static_cast<bool>(Binary("In", v19337, v19338))) return Value(false); v19337 = v19338; return Value(true); }()); if (!static_cast<bool>(v19332)) return v19332; v19332 = ([&]() -> Value { auto v19339 = Get(s->LocalAt(7), Value(int64_t{1})); Value v19340; v19340 = s->LocalAt(9); if (!static_cast<bool>(Binary("In", v19339, v19340))) return Value(false); v19339 = v19340; return Value(true); }()); return v19332; }()))) {
auto v19341 = Get(s->LocalAt(7), Value(int64_t{1}));
s->SetAt(3, v19341);
auto v19342 = ([&]() -> Value { auto fn19343 = Attribute(s->LocalAt(6), "setdefault"); Arguments args19344; args19344.positional.reserve(2); args19344.Add(s->LocalAt(3), false); args19344.Add(([&]() -> Value { auto comp19345 = std::make_shared<Scope>(); comp19345->globals = s->globals; comp19345->parent = s; static constexpr const char* comp19345_names[] = {"_"}; comp19345->PrepareSlots(comp19345_names); auto result19346 = List(); for (const auto& item19347 : Iterate(s->LocalAt(5))) { comp19345->SetAt(0, item19347); result19346.node()->sequence.push_back(List({})); } return result19346; }()), false); return Call(c, fn19343, std::move(args19344)); }());
s->SetAt(8, v19342);
auto v19348 = s->LocalAt(7);
Put(s->LocalAt(8), s->LocalAt(1), v19348);
}
}
s->SetAt(4, Define(&Code_233952d2513f478389c2, s, Signature{{"cand"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"a", "b", "cand", "i", "item", "key", "mine", "n", "op", "order", "schedule", "schedules", "theirs", "total", "value"}; return names; }())}, true, "margin"));
s->definitions.push_back("margin");
return s->LocalAt(4);
return {};
}
}  // namespace kagg::opponents::compiled
