// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_20d3410c5f625a0c7654(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"market", "observation"};
s->PrepareSlots(s_names);
auto v13079 = Get(s->LocalAt(1), Value("market"));
s->SetAt(0, v13079);
return ([&]() -> Value { auto fn13080 = s->Global("dict"); Arguments args13081; args13081.Keyword("step", ([&]() -> Value { auto fn13082 = s->Global("int"); Arguments args13083; args13083.Add(Get(s->LocalAt(1), Value("step")), false); return Call(c, fn13082, std::move(args13083)); }())); args13081.Keyword("inventory", ([&]() -> Value { auto fn13084 = s->Global("dict"); Arguments args13085; args13085.Add(Get(s->LocalAt(0), Value("inventory")), false); return Call(c, fn13084, std::move(args13085)); }())); args13081.Keyword("prices", ([&]() -> Value { auto fn13086 = s->Global("dict"); Arguments args13087; args13087.Add(Get(s->LocalAt(0), Value("prices")), false); return Call(c, fn13086, std::move(args13087)); }())); args13081.Keyword("shops", ([&]() -> Value { auto fn13088 = s->Global("list"); Arguments args13089; args13089.Add(([&]() -> Value { auto fn13090 = PrepareDictionaryGet(Get(s->LocalAt(1), Value("town"))); Arguments args13091; args13091.positional.reserve(2); args13091.Add(Value("unlocked_shops"), false); args13091.Add(List({}), false); return CallDictionaryGet(c, fn13090, std::move(args13091)); }()), false); return Call(c, fn13088, std::move(args13089)); }())); args13081.Keyword("view", ([&]() -> Value { auto fn13092 = s->Global("FarmView"); Arguments args13093; args13093.Add(s->LocalAt(1), false); return Call(c, fn13092, std::move(args13093)); }())); return Call(c, fn13080, std::move(args13081)); }());
return {};
}
}  // namespace kagg::opponents::compiled
