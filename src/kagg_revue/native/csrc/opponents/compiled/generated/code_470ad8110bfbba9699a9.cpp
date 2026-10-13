// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_470ad8110bfbba9699a9(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "access", "action", "actor", "c", "chosen", "dx", "dy", "farm", "index", "native_hires", "obs", "positions"};
s->PrepareSlots(s_names);
auto v8785 = Get(Get(s->LocalAt(11), Value("farms")), Get(s->LocalAt(11), Value("player")));
s->SetAt(8, v8785);
auto v8786 = ([&]() -> Value { auto v8787 = List({([&]() -> Value { auto fn8788 = s->Global("list"); Arguments args8789; args8789.Add(Get(s->LocalAt(8), Value("farmer")), false); return Call(c, fn8788, std::move(args8789)); }())}); return Binary("Add", v8787, ([&]() -> Value { auto comp8790 = std::make_shared<Scope>(); comp8790->globals = s->globals; comp8790->parent = s; static constexpr const char* comp8790_names[] = {"p"}; comp8790->PrepareSlots(comp8790_names); auto result8791 = List(); for (const auto& item8792 : Iterate(Get(s->LocalAt(8), Value("hands")))) { comp8790->SetAt(0, item8792); result8791.node()->sequence.push_back(([&]() -> Value { auto fn8793 = comp8790->Global("list"); Arguments args8794; args8794.Add(comp8790->LocalAt(0), false); return Call(c, fn8793, std::move(args8794)); }())); } return result8791; }())); }());
s->SetAt(12, v8786);
for (const auto& item8795 : Iterate(([&]() -> Value { auto fn8796 = s->Global("enumerate"); Arguments args8797; args8797.Add(Slice(([&]() -> Value { Arguments args8800; args8800.Add(([&]() -> Value { auto v8801 = ([&]() -> Value { auto fn8802 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args8803; args8803.Add(Value("farmer"), false); return CallDictionaryGet(c, fn8802, std::move(args8803)); }()); if (static_cast<bool>(v8801)) return v8801; v8801 = List({Value("PASS")}); return v8801; }()), false); args8800.Add(([&]() -> Value { auto v8804 = ([&]() -> Value { auto fn8805 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args8806; args8806.Add(Value("hands"), false); return CallDictionaryGet(c, fn8805, std::move(args8806)); }()); if (static_cast<bool>(v8804)) return v8804; v8804 = List({}); return v8804; }()), true); return List(std::move(args8800.positional)); }()), Value{}, ([&]() -> Value { auto fn8798 = s->Global("len"); Arguments args8799; args8799.Add(s->LocalAt(12), false); return Call(c, fn8798, std::move(args8799)); }()), Value{}), false); return Call(c, fn8796, std::move(args8797)); }()))) {
auto unpack8807 = Iterate(item8795);
ValidateUnpack(unpack8807, 2, false);
s->SetAt(3, unpack8807.at(0));
s->SetAt(4, unpack8807.at(1));
if (static_cast<bool>(([&]() -> Value { auto v8808 = s->LocalAt(4); if (!static_cast<bool>(v8808)) return v8808; v8808 = ([&]() -> Value { auto v8809 = Get(s->LocalAt(4), Value(int64_t{0})); Value v8810; v8810 = s->Global("MOVES"); if (!static_cast<bool>(Binary("In", v8809, v8810))) return Value(false); v8809 = v8810; return Value(true); }()); return v8808; }()))) {
auto v8811 = Get(s->Global("MOVES"), Get(s->LocalAt(4), Value(int64_t{0})));
auto unpack8812 = Iterate(v8811);
ValidateUnpack(unpack8812, 2, false);
s->SetAt(6, unpack8812.at(0));
s->SetAt(7, unpack8812.at(1));
auto v8813 = List({([&]() -> Value { auto fn8814 = s->Global("max"); Arguments args8815; args8815.positional.reserve(2); args8815.Add(Value(int64_t{0}), false); args8815.Add(([&]() -> Value { auto fn8816 = s->Global("min"); Arguments args8817; args8817.positional.reserve(2); args8817.Add(Value(int64_t{9}), false); args8817.Add(([&]() -> Value { auto v8818 = Get(Get(s->LocalAt(12), s->LocalAt(3)), Value(int64_t{0})); return Binary("Add", v8818, s->LocalAt(6)); }()), false); return Call(c, fn8816, std::move(args8817)); }()), false); return Call(c, fn8814, std::move(args8815)); }()), ([&]() -> Value { auto fn8819 = s->Global("max"); Arguments args8820; args8820.positional.reserve(2); args8820.Add(Value(int64_t{0}), false); args8820.Add(([&]() -> Value { auto fn8821 = s->Global("min"); Arguments args8822; args8822.positional.reserve(2); args8822.Add(Value(int64_t{9}), false); args8822.Add(([&]() -> Value { auto v8823 = Get(Get(s->LocalAt(12), s->LocalAt(3)), Value(int64_t{1})); return Binary("Add", v8823, s->LocalAt(7)); }()), false); return Call(c, fn8821, std::move(args8822)); }()), false); return Call(c, fn8819, std::move(args8820)); }())});
Put(s->LocalAt(12), s->LocalAt(3), v8813);
}
}
auto v8824 = Tuple({Tuple({Value(int64_t{4}), Value(int64_t{4})}), Tuple({Value(int64_t{5}), Value(int64_t{4})}), Tuple({Value(int64_t{4}), Value(int64_t{5})}), Tuple({Value(int64_t{5}), Value(int64_t{5})})});
s->SetAt(1, v8824);
auto v8825 = ([&]() -> Value { auto fn8826 = s->Global("sum"); Arguments args8827; args8827.Add(([&]() -> Value { auto comp8828 = std::make_shared<Scope>(); comp8828->globals = s->globals; comp8828->parent = s; static constexpr const char* comp8828_names[] = {"o"}; comp8828->PrepareSlots(comp8828_names); auto result8829 = List(); for (const auto& item8830 : Iterate(([&]() -> Value { auto fn8831 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args8832; args8832.positional.reserve(2); args8832.Add(Value("market"), false); args8832.Add(List({}), false); return CallDictionaryGet(c, fn8831, std::move(args8832)); }()))) { comp8828->SetAt(0, item8830); result8829.node()->sequence.push_back(([&]() -> Value { auto v8833 = ([&]() -> Value { auto fn8834 = comp8828->Global("bool"); Arguments args8835; args8835.Add(comp8828->LocalAt(0), false); return Call(c, fn8834, std::move(args8835)); }()); if (!static_cast<bool>(v8833)) return v8833; v8833 = ([&]() -> Value { auto v8836 = Get(comp8828->LocalAt(0), Value(int64_t{0})); Value v8837; v8837 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v8836, v8837))) return Value(false); v8836 = v8837; return Value(true); }()); return v8833; }())); } return result8829; }()), false); return Call(c, fn8826, std::move(args8827)); }());
s->SetAt(10, v8825);
for (const auto& item8838 : Iterate(([&]() -> Value { auto fn8839 = s->Global("range"); Arguments args8840; args8840.Add(([&]() -> Value { auto v8841 = ([&]() -> Value { auto v8842 = s->LocalAt(10); return Binary("Add", v8842, s->LocalAt(9)); }()); return Binary("Add", v8841, Value(int64_t{1})); }()), false); return Call(c, fn8839, std::move(args8840)); }()))) {
s->SetAt(0, item8838);
auto v8843 = ([&]() -> Value { auto fn8844 = s->Global("min"); Arguments args8845; args8845.Add(s->LocalAt(1), false); args8845.Keyword("key", Define(&Code_e3f2f3deb66292d29224, s, Signature{{"p"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"p"}; return names; }())}, true, "<lambda>")); return Call(c, fn8844, std::move(args8845)); }());
s->SetAt(5, v8843);
(void)([&]() -> Value { auto fn8857 = Attribute(s->LocalAt(12), "append"); Arguments args8858; args8858.Add(([&]() -> Value { auto fn8859 = s->Global("list"); Arguments args8860; args8860.Add(s->LocalAt(5), false); return Call(c, fn8859, std::move(args8860)); }()), false); return Call(c, fn8857, std::move(args8858)); }());
}
return Tuple({([&]() -> Value { auto v8861 = ([&]() -> Value { auto fn8862 = s->Global("int"); Arguments args8863; args8863.Add(Get(s->LocalAt(11), Value("step")), false); return Call(c, fn8862, std::move(args8863)); }()); return Binary("Add", v8861, Value(int64_t{2})); }()), s->LocalAt(5)});
return {};
}
}  // namespace kagg::opponents::compiled
