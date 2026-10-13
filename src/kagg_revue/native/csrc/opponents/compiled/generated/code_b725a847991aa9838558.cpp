// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_b725a847991aa9838558(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"cfg", "egg", "kind", "milk", "shops", "yarn"};
s->PrepareSlots(s_names);
auto v19673 = ([&]() -> Value { auto v19674 = Value("YARN_STORE"); Value v19675; v19675 = s->LocalAt(4); if (!static_cast<bool>(Binary("In", v19674, v19675))) return Value(false); v19674 = v19675; return Value(true); }());
s->SetAt(5, v19673);
auto v19676 = ([&]() -> Value { auto v19677 = ([&]() -> Value { auto v19678 = Value("BAKERY"); Value v19679; v19679 = s->LocalAt(4); if (!static_cast<bool>(Binary("In", v19678, v19679))) return Value(false); v19678 = v19679; return Value(true); }()); if (static_cast<bool>(v19677)) return v19677; v19677 = ([&]() -> Value { auto v19680 = Value("BRUNCH_SPOT"); Value v19681; v19681 = s->LocalAt(4); if (!static_cast<bool>(Binary("In", v19680, v19681))) return Value(false); v19680 = v19681; return Value(true); }()); return v19677; }());
s->SetAt(1, v19676);
auto v19682 = ([&]() -> Value { auto fn19683 = s->Global("sum"); Arguments args19684; args19684.Add(([&]() -> Value { auto comp19685 = std::make_shared<Scope>(); comp19685->globals = s->globals; comp19685->parent = s; static constexpr const char* comp19685_names[] = {"s"}; comp19685->PrepareSlots(comp19685_names); auto result19686 = List(); for (const auto& item19687 : Iterate(s->LocalAt(4))) { comp19685->SetAt(0, item19687); result19686.node()->sequence.push_back(([&]() -> Value { auto v19688 = comp19685->LocalAt(0); Value v19689; v19689 = Tuple({Value("PIZZA_SHOP"), Value("ICE_CREAM_SHOP"), Value("SMOOTHIE_SHOP")}); if (!static_cast<bool>(Binary("In", v19688, v19689))) return Value(false); v19688 = v19689; return Value(true); }())); } return result19686; }()), false); return Call(c, fn19683, std::move(args19684)); }());
s->SetAt(3, v19682);
if (static_cast<bool>(([&]() -> Value { auto v19690 = ([&]() -> Value { auto v19691 = s->LocalAt(2); Value v19692; v19692 = Value("SHEEP"); if (!static_cast<bool>(Binary("Eq", v19691, v19692))) return Value(false); v19691 = v19692; return Value(true); }()); if (!static_cast<bool>(v19690)) return v19690; v19690 = ([&]() -> Value { auto fn19693 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args19694; args19694.Add(Value("nosheep"), false); return CallDictionaryGet(c, fn19693, std::move(args19694)); }()); if (!static_cast<bool>(v19690)) return v19690; v19690 = Unary("Not", s->LocalAt(5)); if (!static_cast<bool>(v19690)) return v19690; v19690 = ([&]() -> Value { auto v19695 = s->LocalAt(3); Value v19696; v19696 = ([&]() -> Value { auto fn19697 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args19698; args19698.positional.reserve(2); args19698.Add(Value("min_milk"), false); args19698.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn19697, std::move(args19698)); }()); if (!static_cast<bool>(Binary("GtE", v19695, v19696))) return Value(false); v19695 = v19696; return Value(true); }()); return v19690; }()))) {
return Value("COW");
}
if (static_cast<bool>(([&]() -> Value { auto v19699 = ([&]() -> Value { auto v19700 = s->LocalAt(2); Value v19701; v19701 = Value("COW"); if (!static_cast<bool>(Binary("Eq", v19700, v19701))) return Value(false); v19700 = v19701; return Value(true); }()); if (!static_cast<bool>(v19699)) return v19699; v19699 = ([&]() -> Value { auto fn19702 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args19703; args19703.Add(Value("yarnsheep"), false); return CallDictionaryGet(c, fn19702, std::move(args19703)); }()); if (!static_cast<bool>(v19699)) return v19699; v19699 = s->LocalAt(5); return v19699; }()))) {
return Value("SHEEP");
}
if (static_cast<bool>(([&]() -> Value { auto v19704 = ([&]() -> Value { auto v19705 = s->LocalAt(2); Value v19706; v19706 = Value("GOOSE"); if (!static_cast<bool>(Binary("Eq", v19705, v19706))) return Value(false); v19705 = v19706; return Value(true); }()); if (!static_cast<bool>(v19704)) return v19704; v19704 = ([&]() -> Value { auto fn19707 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args19708; args19708.Add(Value("nogeese"), false); return CallDictionaryGet(c, fn19707, std::move(args19708)); }()); if (!static_cast<bool>(v19704)) return v19704; v19704 = Unary("Not", s->LocalAt(1)); return v19704; }()))) {
return (static_cast<bool>(s->LocalAt(5)) ? Value("SHEEP") : Value("COW"));
}
if (static_cast<bool>(([&]() -> Value { auto v19709 = ([&]() -> Value { auto v19710 = s->LocalAt(2); Value v19711; v19711 = Value("GOOSE"); if (!static_cast<bool>(Binary("Eq", v19710, v19711))) return Value(false); v19710 = v19711; return Value(true); }()); if (!static_cast<bool>(v19709)) return v19709; v19709 = ([&]() -> Value { auto fn19712 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args19713; args19713.Add(Value("yarngeese"), false); return CallDictionaryGet(c, fn19712, std::move(args19713)); }()); if (!static_cast<bool>(v19709)) return v19709; v19709 = s->LocalAt(5); return v19709; }()))) {
return Value("SHEEP");
}
return Value{};
return {};
}
}  // namespace kagg::opponents::compiled
