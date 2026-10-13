// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_a1e1304826b4b2616781(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"actor", "c", "cs", "day", "farm", "missing", "obs", "offset", "private", "tile", "x", "y"};
s->PrepareSlots(s_names);
auto v11711 = Tuple({([&]() -> Value { auto fn11712 = Attribute(s->Global("copy"), "deepcopy"); Arguments args11713; args11713.Add(s->LocalAt(4), false); return Call(c, fn11712, std::move(args11713)); }()), ([&]() -> Value { auto fn11714 = Attribute(s->Global("copy"), "deepcopy"); Arguments args11715; args11715.Add(s->LocalAt(8), false); return Call(c, fn11714, std::move(args11715)); }())});
auto unpack11716 = Iterate(v11711);
ValidateUnpack(unpack11716, 2, false);
s->SetAt(4, unpack11716.at(0));
s->SetAt(8, unpack11716.at(1));
auto v11717 = Value(int64_t{0});
s->SetAt(5, v11717);
auto v11718 = ([&]() -> Value { auto v11719 = ([&]() -> Value { auto fn11720 = s->Global("int"); Arguments args11721; args11721.Add(Get(s->LocalAt(6), Value("step")), false); return Call(c, fn11720, std::move(args11721)); }()); return Binary("FloorDiv", v11719, Value(int64_t{24})); }());
s->SetAt(3, v11718);
for (const auto& item11722 : Iterate(([&]() -> Value { auto fn11723 = s->Global("range"); Arguments args11724; args11724.positional.reserve(2); args11724.Add(Value(int64_t{1}), false); args11724.Add(([&]() -> Value { auto fn11725 = s->Global("min"); Arguments args11726; args11726.positional.reserve(2); args11726.Add(Value(int64_t{5}), false); args11726.Add(([&]() -> Value { auto v11727 = Value(int64_t{24}); return Binary("Sub", v11727, ([&]() -> Value { auto v11728 = ([&]() -> Value { auto fn11729 = s->Global("int"); Arguments args11730; args11730.Add(Get(s->LocalAt(6), Value("step")), false); return Call(c, fn11729, std::move(args11730)); }()); return Binary("Mod", v11728, Value(int64_t{24})); }())); }()), false); return Call(c, fn11725, std::move(args11726)); }()), false); return Call(c, fn11723, std::move(args11724)); }()))) {
s->SetAt(7, item11722);
auto v11731 = ([&]() -> Value { auto fn11732 = s->Global("_r128_commands"); Arguments args11733; args11733.Add(([&]() -> Value { auto fn11734 = s->Global("_r128_future"); Arguments args11735; args11735.positional.reserve(2); args11735.Add(s->LocalAt(6), false); args11735.Add(s->LocalAt(7), false); return Call(c, fn11734, std::move(args11735)); }()), false); return Call(c, fn11732, std::move(args11733)); }());
s->SetAt(2, v11731);
auto v11736 = (static_cast<bool>(([&]() -> Value { auto v11737 = s->LocalAt(0); Value v11738; v11738 = ([&]() -> Value { auto fn11739 = s->Global("len"); Arguments args11740; args11740.Add(s->LocalAt(2), false); return Call(c, fn11739, std::move(args11740)); }()); if (!static_cast<bool>(Binary("Lt", v11737, v11738))) return Value(false); v11737 = v11738; return Value(true); }())) ? Get(s->LocalAt(2), s->LocalAt(0)) : List({Value("PASS")}));
s->SetAt(1, v11736);
if (static_cast<bool>(([&]() -> Value { auto v11741 = Slice(s->LocalAt(1), Value{}, Value(int64_t{2}), Value{}); Value v11742; v11742 = List({Value("PICKUP"), Value("WHEAT")}); if (!static_cast<bool>(Binary("Eq", v11741, v11742))) return Value(false); v11741 = v11742; return Value(true); }()))) {
break;
}
if (static_cast<bool>(([&]() -> Value { auto v11743 = s->LocalAt(1); Value v11744; v11744 = List({Value("FEED")}); if (!static_cast<bool>(Binary("Eq", v11743, v11744))) return Value(false); v11743 = v11744; return Value(true); }()))) {
auto v11745 = (static_cast<bool>(([&]() -> Value { auto v11746 = s->LocalAt(0); Value v11747; v11747 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v11746, v11747))) return Value(false); v11746 = v11747; return Value(true); }())) ? Get(s->LocalAt(4), Value("farmer")) : Get(Get(s->LocalAt(4), Value("hands")), ([&]() -> Value { auto v11748 = s->LocalAt(0); return Binary("Sub", v11748, Value(int64_t{1})); }())));
auto unpack11749 = Iterate(v11745);
ValidateUnpack(unpack11749, 2, false);
s->SetAt(10, unpack11749.at(0));
s->SetAt(11, unpack11749.at(1));
auto v11750 = Get(Get(Get(s->LocalAt(4), Value("tiles")), s->LocalAt(11)), s->LocalAt(10));
s->SetAt(9, v11750);
if (static_cast<bool>(([&]() -> Value { auto v11751 = ([&]() -> Value { auto fn11752 = s->Global("isinstance"); Arguments args11753; args11753.positional.reserve(2); args11753.Add(s->LocalAt(9), false); args11753.Add(s->Global("dict"), false); return Call(c, fn11752, std::move(args11753)); }()); if (!static_cast<bool>(v11751)) return v11751; v11751 = ([&]() -> Value { auto fn11754 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args11755; args11755.Add(Value("animal"), false); return CallDictionaryGet(c, fn11754, std::move(args11755)); }()); if (!static_cast<bool>(v11751)) return v11751; v11751 = Unary("Not", ([&]() -> Value { auto fn11756 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args11757; args11757.Add(Value("fed_today"), false); return CallDictionaryGet(c, fn11756, std::move(args11757)); }())); if (!static_cast<bool>(v11751)) return v11751; v11751 = ([&]() -> Value { auto v11758 = ([&]() -> Value { auto fn11760 = PrepareDictionaryGet(Get(Get(s->LocalAt(8), Value("inventories")), s->LocalAt(0))); Arguments args11761; args11761.positional.reserve(2); args11761.Add(Value("WHEAT"), false); args11761.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn11760, std::move(args11761)); }()); Value v11759; v11759 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v11758, v11759))) return Value(false); v11758 = v11759; return Value(true); }()); return v11751; }()))) {
auto v11762 = Value(int64_t{1});
Put(Get(Get(s->LocalAt(8), Value("inventories")), s->LocalAt(0)), Value("WHEAT"), v11762);
auto v11763 = s->LocalAt(5);
s->SetAt(5, Inplace("Add", v11763, Value(int64_t{1})));
}
}
(void)([&]() -> Value { auto fn11764 = Get(s->Global("_PLANNER_NS"), Value("_apply_unit_action")); Arguments args11765; args11765.positional.reserve(8); args11765.Add(s->LocalAt(4), false); args11765.Add(s->LocalAt(8), false); args11765.Add(s->LocalAt(0), false); args11765.Add(s->LocalAt(1), false); args11765.Add(Value(int64_t{10}), false); args11765.Add(s->LocalAt(3), false); args11765.Add(Value(int64_t{24}), false); args11765.Add(Value(int64_t{100}), false); return Call(c, fn11764, std::move(args11765)); }());
}
return s->LocalAt(5);
return {};
}
}  // namespace kagg::opponents::compiled
