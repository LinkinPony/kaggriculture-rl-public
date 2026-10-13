// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_94598f9502b2968caf8d(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"item", "items", "out", "shop", "shops", "step"};
s->PrepareSlots(s_names);
auto v12978 = ([&]() -> Value { auto dict12979 = Dict(); return dict12979; }());
s->SetAt(2, v12978);
if (static_cast<bool>(([&]() -> Value { auto v12980 = ([&]() -> Value { auto v12982 = s->LocalAt(5); return Binary("Mod", v12982, Value(int64_t{4})); }()); Value v12981; v12981 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v12980, v12981))) return Value(false); v12980 = v12981; return Value(true); }()))) {
for (const auto& item12983 : Iterate(s->LocalAt(4))) {
s->SetAt(3, item12983);
auto v12984 = ([&]() -> Value { auto fn12985 = PrepareDictionaryGet(s->Global("_RACE_SHOPS")); Arguments args12986; args12986.positional.reserve(2); args12986.Add(s->LocalAt(3), false); args12986.Add(Tuple({}), false); return CallDictionaryGet(c, fn12985, std::move(args12986)); }());
s->SetAt(1, v12984);
for (const auto& item12987 : Iterate(s->LocalAt(1))) {
s->SetAt(0, item12987);
auto v12988 = ([&]() -> Value { auto v12989 = ([&]() -> Value { auto fn12990 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args12991; args12991.positional.reserve(2); args12991.Add(s->LocalAt(0), false); args12991.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn12990, std::move(args12991)); }()); return Binary("Add", v12989, (static_cast<bool>(([&]() -> Value { auto v12992 = ([&]() -> Value { auto fn12994 = s->Global("len"); Arguments args12995; args12995.Add(s->LocalAt(1), false); return Call(c, fn12994, std::move(args12995)); }()); Value v12993; v12993 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Eq", v12992, v12993))) return Value(false); v12992 = v12993; return Value(true); }())) ? Value(int64_t{2}) : Value(int64_t{1}))); }());
Put(s->LocalAt(2), s->LocalAt(0), v12988);
}
}
}
if (static_cast<bool>(([&]() -> Value { auto v12996 = ([&]() -> Value { auto v12998 = s->LocalAt(5); return Binary("Mod", v12998, Value(int64_t{24})); }()); Value v12997; v12997 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v12996, v12997))) return Value(false); v12996 = v12997; return Value(true); }()))) {
for (const auto& item12999 : Iterate(s->Global("_RACE_ITEMS"))) {
s->SetAt(0, item12999);
auto v13000 = ([&]() -> Value { auto v13001 = ([&]() -> Value { auto fn13002 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args13003; args13003.positional.reserve(2); args13003.Add(s->LocalAt(0), false); args13003.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn13002, std::move(args13003)); }()); return Binary("Add", v13001, Value(int64_t{1})); }());
Put(s->LocalAt(2), s->LocalAt(0), v13000);
}
}
return s->LocalAt(2);
return {};
}
}  // namespace kagg::opponents::compiled
