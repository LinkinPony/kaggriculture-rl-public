// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_b2baf0d7104a2962778e(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"entries", "farm", "fertilizer", "harvest", "item", "key", "mature", "offset", "prices", "private", "row", "run", "snapshots", "tile", "x", "y"};
s->PrepareSlots(s_names);
auto v17949 = ([&]() -> Value { auto fn17950 = s->Global("tuple"); Arguments args17951; args17951.Add(([&]() -> Value { auto fn17952 = Attribute(s->LocalAt(8), "items"); Arguments args17953; return Call(c, fn17952, std::move(args17953)); }()), false); return Call(c, fn17950, std::move(args17951)); }());
s->SetAt(5, v17949);
if (static_cast<bool>(([&]() -> Value { auto v17954 = ([&]() -> Value { auto v17955 = s->Global("_EXP303_RESOURCE_RUN"); Value v17956; v17956 = s->LocalAt(11); if (!static_cast<bool>(Binary("Is", v17955, v17956))) return Value(false); v17955 = v17956; return Value(true); }()); if (!static_cast<bool>(v17954)) return v17954; v17954 = ([&]() -> Value { auto v17957 = s->Global("_EXP303_RESOURCE_PRICES"); Value v17958; v17958 = s->LocalAt(5); if (!static_cast<bool>(Binary("Eq", v17957, v17958))) return Value(false); v17957 = v17958; return Value(true); }()); return v17954; }()))) {
return s->Global("_EXP303_RESOURCES");
}
auto v17959 = List({});
s->SetAt(12, v17959);
for (const auto& item17960 : Iterate(([&]() -> Value { auto fn17961 = s->Global("range"); Arguments args17962; args17962.Add(([&]() -> Value { auto fn17963 = s->Global("len"); Arguments args17964; args17964.Add(Get(s->LocalAt(11), Value("rows")), false); return Call(c, fn17963, std::move(args17964)); }()), false); return Call(c, fn17961, std::move(args17962)); }()))) {
s->SetAt(7, item17960);
auto v17965 = Get(Get(s->LocalAt(11), Value("states")), s->LocalAt(7));
auto unpack17966 = Iterate(v17965);
ValidateUnpack(unpack17966, 2, false);
s->SetAt(1, unpack17966.at(0));
s->SetAt(9, unpack17966.at(1));
auto v17967 = List({});
s->SetAt(0, v17967);
for (const auto& item17968 : Iterate(([&]() -> Value { auto fn17969 = s->Global("enumerate"); Arguments args17970; args17970.Add(Get(s->LocalAt(1), Value("tiles")), false); return Call(c, fn17969, std::move(args17970)); }()))) {
auto unpack17971 = Iterate(item17968);
ValidateUnpack(unpack17971, 2, false);
s->SetAt(15, unpack17971.at(0));
s->SetAt(10, unpack17971.at(1));
for (const auto& item17972 : Iterate(([&]() -> Value { auto fn17973 = s->Global("enumerate"); Arguments args17974; args17974.Add(s->LocalAt(10), false); return Call(c, fn17973, std::move(args17974)); }()))) {
auto unpack17975 = Iterate(item17972);
ValidateUnpack(unpack17975, 2, false);
s->SetAt(14, unpack17975.at(0));
s->SetAt(13, unpack17975.at(1));
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn17976 = s->Global("isinstance"); Arguments args17977; args17977.positional.reserve(2); args17977.Add(s->LocalAt(13), false); args17977.Add(s->Global("dict"), false); return Call(c, fn17976, std::move(args17977)); }())))) {
continue;
}
auto v17978 = Tuple({Value{}, Value{}});
auto unpack17979 = Iterate(v17978);
ValidateUnpack(unpack17979, 2, false);
s->SetAt(3, unpack17979.at(0));
s->SetAt(2, unpack17979.at(1));
if (static_cast<bool>(([&]() -> Value { auto v17980 = ([&]() -> Value { auto fn17982 = PrepareDictionaryGet(s->LocalAt(13)); Arguments args17983; args17983.positional.reserve(2); args17983.Add(Value("yield_units"), false); args17983.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn17982, std::move(args17983)); }()); Value v17981; v17981 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v17980, v17981))) return Value(false); v17980 = v17981; return Value(true); }()))) {
auto v17984 = (static_cast<bool>(([&]() -> Value { auto v17985 = ([&]() -> Value { auto fn17987 = PrepareDictionaryGet(s->LocalAt(13)); Arguments args17988; args17988.Add(Value("kind"), false); return CallDictionaryGet(c, fn17987, std::move(args17988)); }()); Value v17986; v17986 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v17985, v17986))) return Value(false); v17985 = v17986; return Value(true); }())) ? ([&]() -> Value { auto fn17989 = PrepareDictionaryGet(s->LocalAt(13)); Arguments args17990; args17990.Add(Value("crop"), false); return CallDictionaryGet(c, fn17989, std::move(args17990)); }()) : ([&]() -> Value { auto fn17991 = PrepareDictionaryGet(([&]() -> Value { auto fn17993 = PrepareDictionaryGet(s->Global("ANIMALS")); Arguments args17994; args17994.positional.reserve(2); args17994.Add(([&]() -> Value { auto fn17995 = PrepareDictionaryGet(s->LocalAt(13)); Arguments args17996; args17996.Add(Value("animal"), false); return CallDictionaryGet(c, fn17995, std::move(args17996)); }()), false); args17994.Add(([&]() -> Value { auto dict17997 = Dict(); return dict17997; }()), false); return CallDictionaryGet(c, fn17993, std::move(args17994)); }())); Arguments args17992; args17992.Add(Value("product"), false); return CallDictionaryGet(c, fn17991, std::move(args17992)); }()));
s->SetAt(4, v17984);
auto v17998 = ([&]() -> Value { auto v17999 = s->LocalAt(4); if (!static_cast<bool>(v17999)) return v17999; v17999 = ([&]() -> Value { auto v18000 = ([&]() -> Value { auto v18001 = Value("animal"); Value v18002; v18002 = s->LocalAt(13); if (!static_cast<bool>(Binary("In", v18001, v18002))) return Value(false); v18001 = v18002; return Value(true); }()); if (static_cast<bool>(v18000)) return v18000; v18000 = ([&]() -> Value { auto v18003 = ([&]() -> Value { auto v18005 = ([&]() -> Value { auto v18006 = ([&]() -> Value { auto v18007 = s->Global("START"); return Binary("Add", v18007, s->LocalAt(7)); }()); return Binary("FloorDiv", v18006, Value(int64_t{24})); }()); return Binary("Sub", v18005, Get(s->LocalAt(13), Value("planted_day"))); }()); Value v18004; v18004 = Get(Get(s->Global("CROPS"), s->LocalAt(4)), Value("first_yield_day")); if (!static_cast<bool>(Binary("GtE", v18003, v18004))) return Value(false); v18003 = v18004; return Value(true); }()); return v18000; }()); return v17999; }());
s->SetAt(6, v17998);
if (static_cast<bool>(s->LocalAt(6))) {
auto v18008 = ([&]() -> Value { auto v18009 = Get(s->LocalAt(8), s->LocalAt(4)); return Binary("Mult", v18009, Get(s->LocalAt(13), Value("yield_units"))); }());
s->SetAt(3, v18008);
}
}
if (static_cast<bool>(([&]() -> Value { auto v18010 = ([&]() -> Value { auto fn18011 = PrepareDictionaryGet(s->LocalAt(13)); Arguments args18012; args18012.Add(Value("fertilizer_available"), false); return CallDictionaryGet(c, fn18011, std::move(args18012)); }()); if (!static_cast<bool>(v18010)) return v18010; v18010 = ([&]() -> Value { auto v18013 = Value("animal"); Value v18014; v18014 = s->LocalAt(13); if (!static_cast<bool>(Binary("In", v18013, v18014))) return Value(false); v18013 = v18014; return Value(true); }()); return v18010; }()))) {
auto v18015 = Get(s->LocalAt(8), Value("FERTILIZER"));
s->SetAt(2, v18015);
}
if (static_cast<bool>(([&]() -> Value { auto v18016 = ([&]() -> Value { auto v18017 = s->LocalAt(3); Value v18018; v18018 = Value{}; if (!static_cast<bool>(Binary("IsNot", v18017, v18018))) return Value(false); v18017 = v18018; return Value(true); }()); if (static_cast<bool>(v18016)) return v18016; v18016 = ([&]() -> Value { auto v18019 = s->LocalAt(2); Value v18020; v18020 = Value{}; if (!static_cast<bool>(Binary("IsNot", v18019, v18020))) return Value(false); v18019 = v18020; return Value(true); }()); return v18016; }()))) {
(void)([&]() -> Value { auto fn18021 = Attribute(s->LocalAt(0), "append"); Arguments args18022; args18022.Add(Tuple({Tuple({s->LocalAt(14), s->LocalAt(15)}), s->LocalAt(3), s->LocalAt(2)}), false); return Call(c, fn18021, std::move(args18022)); }());
}
}
}
(void)([&]() -> Value { auto fn18023 = Attribute(s->LocalAt(12), "append"); Arguments args18024; args18024.Add(s->LocalAt(0), false); return Call(c, fn18023, std::move(args18024)); }());
}
auto v18025 = Tuple({s->LocalAt(11), s->LocalAt(5), s->LocalAt(12)});
auto unpack18026 = Iterate(v18025);
ValidateUnpack(unpack18026, 3, false);
Put(s->globals, "_EXP303_RESOURCE_RUN", unpack18026.at(0));
Put(s->globals, "_EXP303_RESOURCE_PRICES", unpack18026.at(1));
Put(s->globals, "_EXP303_RESOURCES", unpack18026.at(2));
return s->LocalAt(12);
return {};
}
}  // namespace kagg::opponents::compiled
