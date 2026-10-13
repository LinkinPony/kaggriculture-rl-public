// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_db853126e1ead0bcb292(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "actor", "command", "commands", "config", "farm", "inv", "item", "items", "obs", "parent_action", "plan", "pos", "positions", "prices", "private", "problems", "quantity", "remaining", "room", "route"};
s->PrepareSlots(s_names);
auto v3699 = ([&]() -> Value { auto fn3700 = s->Global("physical_state"); Arguments args3701; args3701.Add(s->LocalAt(9), false); return Call(c, fn3700, std::move(args3701)); }());
auto unpack3702 = Iterate(v3699);
ValidateUnpack(unpack3702, 2, false);
s->SetAt(5, unpack3702.at(0));
s->SetAt(15, unpack3702.at(1));
auto v3703 = ([&]() -> Value { Arguments args3704; args3704.Add(Get(s->LocalAt(5), Value("farmer")), false); args3704.Add(Get(s->LocalAt(5), Value("hands")), true); return List(std::move(args3704.positional)); }());
s->SetAt(13, v3703);
auto v3705 = ([&]() -> Value { auto v3706 = ([&]() -> Value { auto v3707 = s->Global("FINAL"); return Binary("Sub", v3707, ([&]() -> Value { auto fn3708 = s->Global("int"); Arguments args3709; args3709.Add(([&]() -> Value { auto fn3710 = s->Global("_get"); Arguments args3711; args3711.positional.reserve(2); args3711.Add(s->LocalAt(9), false); args3711.Add(Value("step"), false); return Call(c, fn3710, std::move(args3711)); }()), false); return Call(c, fn3708, std::move(args3709)); }())); }()); return Binary("Add", v3706, Value(int64_t{1})); }());
s->SetAt(18, v3705);
auto v3712 = ([&]() -> Value { auto fn3713 = s->Global("max"); Arguments args3714; args3714.positional.reserve(2); args3714.Add(Value(int64_t{0}), false); args3714.Add(([&]() -> Value { auto v3715 = ([&]() -> Value { auto fn3716 = s->Global("int"); Arguments args3717; args3717.Add(([&]() -> Value { auto fn3718 = s->Global("_get"); Arguments args3719; args3719.positional.reserve(3); args3719.Add(s->LocalAt(4), false); args3719.Add(Value("shedCapacity"), false); args3719.Add(Value(int64_t{100}), false); return Call(c, fn3718, std::move(args3719)); }()), false); return Call(c, fn3716, std::move(args3717)); }()); return Binary("Sub", v3715, ([&]() -> Value { auto fn3720 = s->Global("sum"); Arguments args3721; args3721.Add(([&]() -> Value { auto fn3722 = Attribute(Get(s->LocalAt(15), Value("shed")), "values"); Arguments args3723; return Call(c, fn3722, std::move(args3723)); }()), false); return Call(c, fn3720, std::move(args3721)); }())); }()), false); return Call(c, fn3713, std::move(args3714)); }());
s->SetAt(19, v3712);
auto v3724 = List({});
s->SetAt(3, v3724);
auto v3725 = List({});
s->SetAt(16, v3725);
auto v3726 = ([&]() -> Value { auto fn3727 = PrepareDictionaryGet(([&]() -> Value { auto fn3729 = s->Global("_get"); Arguments args3730; args3730.positional.reserve(3); args3730.Add(s->LocalAt(9), false); args3730.Add(Value("market"), false); args3730.Add(([&]() -> Value { auto dict3731 = Dict(); return dict3731; }()), false); return Call(c, fn3729, std::move(args3730)); }())); Arguments args3728; args3728.positional.reserve(2); args3728.Add(Value("prices"), false); args3728.Add(([&]() -> Value { auto dict3732 = Dict(); return dict3732; }()), false); return CallDictionaryGet(c, fn3727, std::move(args3728)); }());
s->SetAt(14, v3726);
for (const auto& item3733 : Iterate(([&]() -> Value { auto fn3734 = s->Global("enumerate"); Arguments args3735; args3735.Add(([&]() -> Value { auto fn3736 = s->Global("zip"); Arguments args3737; args3737.positional.reserve(2); args3737.Add(s->LocalAt(13), false); args3737.Add(Get(s->LocalAt(15), Value("inventories")), false); return Call(c, fn3736, std::move(args3737)); }()), false); return Call(c, fn3734, std::move(args3735)); }()))) {
auto unpack3738 = Iterate(item3733);
ValidateUnpack(unpack3738, 2, false);
s->SetAt(1, unpack3738.at(0));
auto unpack3739 = Iterate(unpack3738.at(1));
ValidateUnpack(unpack3739, 2, false);
s->SetAt(12, unpack3739.at(0));
s->SetAt(6, unpack3739.at(1));
auto v3740 = List({Value("PASS")});
s->SetAt(2, v3740);
if (static_cast<bool>(([&]() -> Value { auto comp3741 = std::make_shared<Scope>(); comp3741->globals = s->globals; comp3741->parent = s; static constexpr const char* comp3741_names[] = {"v"}; comp3741->PrepareSlots(comp3741_names); auto result3742 = List(); for (const auto& item3743 : Iterate(([&]() -> Value { auto fn3744 = Attribute(s->LocalAt(6), "values"); Arguments args3745; return Call(c, fn3744, std::move(args3745)); }()))) { comp3741->SetAt(0, item3743); if (static_cast<bool>(([&]() -> Value { auto v3746 = comp3741->LocalAt(0); Value v3747; v3747 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v3746, v3747))) return Value(false); v3746 = v3747; return Value(true); }()))) return Value(true); } return Value(false); }()))) {
auto v3748 = ([&]() -> Value { auto fn3749 = s->Global("_return"); Arguments args3750; args3750.Add(s->LocalAt(12), false); return Call(c, fn3749, std::move(args3750)); }());
s->SetAt(20, v3748);
if (static_cast<bool>(([&]() -> Value { auto v3751 = ([&]() -> Value { auto fn3753 = s->Global("len"); Arguments args3754; args3754.Add(s->LocalAt(20), false); return Call(c, fn3753, std::move(args3754)); }()); Value v3752; v3752 = s->LocalAt(18); if (!static_cast<bool>(Binary("Gt", v3751, v3752))) return Value(false); v3751 = v3752; return Value(true); }()))) {
(void)([&]() -> Value { auto fn3755 = Attribute(s->LocalAt(16), "append"); Arguments args3756; args3756.Add(([&]() -> Value { auto dict3757 = Dict(); auto key3758 = Value("actor"); Put(dict3757, key3758, s->LocalAt(1)); auto key3759 = Value("reason"); Put(dict3757, key3759, Value("unreachable cargo")); return dict3757; }()), false); return Call(c, fn3755, std::move(args3756)); }());
}
else {
if (static_cast<bool>(([&]() -> Value { auto v3760 = ([&]() -> Value { auto fn3762 = s->Global("len"); Arguments args3763; args3763.Add(s->LocalAt(20), false); return Call(c, fn3762, std::move(args3763)); }()); Value v3761; v3761 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v3760, v3761))) return Value(false); v3760 = v3761; return Value(true); }()))) {
auto v3764 = Get(s->LocalAt(20), Value(int64_t{0}));
s->SetAt(2, v3764);
}
else {
if (static_cast<bool>(([&]() -> Value { auto v3765 = ([&]() -> Value { auto fn3767 = s->Global("sum"); Arguments args3768; args3768.Add(([&]() -> Value { auto comp3769 = std::make_shared<Scope>(); comp3769->globals = s->globals; comp3769->parent = s; static constexpr const char* comp3769_names[] = {"q"}; comp3769->PrepareSlots(comp3769_names); auto result3770 = List(); for (const auto& item3771 : Iterate(([&]() -> Value { auto fn3772 = Attribute(s->LocalAt(6), "values"); Arguments args3773; return Call(c, fn3772, std::move(args3773)); }()))) { comp3769->SetAt(0, item3771); result3770.node()->sequence.push_back(([&]() -> Value { auto fn3774 = comp3769->Global("max"); Arguments args3775; args3775.positional.reserve(2); args3775.Add(Value(int64_t{0}), false); args3775.Add(comp3769->LocalAt(0), false); return Call(c, fn3774, std::move(args3775)); }())); } return result3770; }()), false); return Call(c, fn3767, std::move(args3768)); }()); Value v3766; v3766 = s->LocalAt(19); if (!static_cast<bool>(Binary("LtE", v3765, v3766))) return Value(false); v3765 = v3766; return Value(true); }()))) {
auto v3776 = List({Value("DROP")});
s->SetAt(2, v3776);
auto v3777 = s->LocalAt(19);
s->SetAt(19, Inplace("Sub", v3777, ([&]() -> Value { auto fn3778 = s->Global("sum"); Arguments args3779; args3779.Add(([&]() -> Value { auto comp3780 = std::make_shared<Scope>(); comp3780->globals = s->globals; comp3780->parent = s; static constexpr const char* comp3780_names[] = {"q"}; comp3780->PrepareSlots(comp3780_names); auto result3781 = List(); for (const auto& item3782 : Iterate(([&]() -> Value { auto fn3783 = Attribute(s->LocalAt(6), "values"); Arguments args3784; return Call(c, fn3783, std::move(args3784)); }()))) { comp3780->SetAt(0, item3782); result3781.node()->sequence.push_back(([&]() -> Value { auto fn3785 = comp3780->Global("max"); Arguments args3786; args3786.positional.reserve(2); args3786.Add(Value(int64_t{0}), false); args3786.Add(comp3780->LocalAt(0), false); return Call(c, fn3785, std::move(args3786)); }())); } return result3781; }()), false); return Call(c, fn3778, std::move(args3779)); }())));
}
else {
auto v3787 = ([&]() -> Value { auto comp3788 = std::make_shared<Scope>(); comp3788->globals = s->globals; comp3788->parent = s; static constexpr const char* comp3788_names[] = {"item"}; comp3788->PrepareSlots(comp3788_names); auto result3789 = List(); for (const auto& item3790 : Iterate(s->Global("PRODUCTS"))) { comp3788->SetAt(0, item3790); if (!static_cast<bool>(([&]() -> Value { auto v3791 = ([&]() -> Value { auto fn3793 = PrepareDictionaryGet(comp3788->Captured("inv")); Arguments args3794; args3794.positional.reserve(2); args3794.Add(comp3788->LocalAt(0), false); args3794.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn3793, std::move(args3794)); }()); Value v3792; v3792 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v3791, v3792))) return Value(false); v3791 = v3792; return Value(true); }()))) continue; result3789.node()->sequence.push_back(comp3788->LocalAt(0)); } return result3789; }());
s->SetAt(8, v3787);
if (static_cast<bool>(([&]() -> Value { auto v3795 = s->LocalAt(19); if (!static_cast<bool>(v3795)) return v3795; v3795 = s->LocalAt(8); return v3795; }()))) {
auto v3796 = ([&]() -> Value { auto fn3797 = s->Global("max"); Arguments args3798; args3798.Add(s->LocalAt(8), false); args3798.Keyword("key", Define(&Code_a9762d5481e5280eda47, s, Signature{{"i"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"i"}; return names; }())}, true, "<lambda>")); return Call(c, fn3797, std::move(args3798)); }());
s->SetAt(7, v3796);
auto v3806 = ([&]() -> Value { auto fn3807 = s->Global("min"); Arguments args3808; args3808.positional.reserve(2); args3808.Add(Get(s->LocalAt(6), s->LocalAt(7)), false); args3808.Add(s->LocalAt(19), false); return Call(c, fn3807, std::move(args3808)); }());
s->SetAt(17, v3806);
auto v3809 = List({Value("PLACE"), s->LocalAt(7), s->LocalAt(17)});
s->SetAt(2, v3809);
auto v3810 = s->LocalAt(19);
s->SetAt(19, Inplace("Sub", v3810, s->LocalAt(17)));
}
else {
(void)([&]() -> Value { auto fn3811 = Attribute(s->LocalAt(16), "append"); Arguments args3812; args3812.Add(([&]() -> Value { auto dict3813 = Dict(); auto key3814 = Value("actor"); Put(dict3813, key3814, s->LocalAt(1)); auto key3815 = Value("reason"); Put(dict3813, key3815, Value("no shed capacity")); return dict3813; }()), false); return Call(c, fn3811, std::move(args3812)); }());
}
}
}
}
}
(void)([&]() -> Value { auto fn3816 = Attribute(s->LocalAt(3), "append"); Arguments args3817; args3817.Add(s->LocalAt(2), false); return Call(c, fn3816, std::move(args3817)); }());
}
auto v3818 = ([&]() -> Value { auto dict3819 = Dict(); auto key3820 = Value("farmer"); Put(dict3819, key3820, Get(s->LocalAt(3), Value(int64_t{0}))); auto key3821 = Value("hands"); Put(dict3819, key3821, Slice(s->LocalAt(3), Value(int64_t{1}), Value{}, Value{})); auto key3822 = Value("market"); Put(dict3819, key3822, ([&]() -> Value { auto fn3823 = s->Global("deepcopy"); Arguments args3824; args3824.Add(([&]() -> Value { auto fn3825 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args3826; args3826.positional.reserve(2); args3826.Add(Value("market"), false); args3826.Add(List({}), false); return CallDictionaryGet(c, fn3825, std::move(args3826)); }()), false); return Call(c, fn3823, std::move(args3824)); }())); return dict3819; }());
s->SetAt(0, v3818);
if (static_cast<bool>(([&]() -> Value { auto v3827 = ([&]() -> Value { auto fn3829 = s->Global("int"); Arguments args3830; args3830.Add(([&]() -> Value { auto fn3831 = s->Global("_get"); Arguments args3832; args3832.positional.reserve(2); args3832.Add(s->LocalAt(9), false); args3832.Add(Value("step"), false); return Call(c, fn3831, std::move(args3832)); }()), false); return Call(c, fn3829, std::move(args3830)); }()); Value v3828; v3828 = s->Global("FINAL"); if (!static_cast<bool>(Binary("Eq", v3827, v3828))) return Value(false); v3827 = v3828; return Value(true); }()))) {
auto v3833 = List({});
Put(s->LocalAt(0), Value("market"), v3833);
auto v3834 = Get(Get(([&]() -> Value { auto fn3835 = s->Global("simulate"); Arguments args3836; args3836.positional.reserve(3); args3836.Add(s->LocalAt(9), false); args3836.Add(s->LocalAt(4), false); args3836.Add(List({s->LocalAt(0)}), false); args3836.Keyword("final_liquidate", Value(true)); args3836.Keyword("preserve_final_commands", Value(true)); return Call(c, fn3835, std::move(args3836)); }()), Value("actions")), Value(int64_t{0}));
s->SetAt(0, v3834);
}
auto v3837 = ([&]() -> Value { auto v3838 = ([&]() -> Value { auto fn3839 = PrepareDictionaryGet(s->LocalAt(11)); Arguments args3840; args3840.positional.reserve(2); args3840.Add(Value("recovery_steps"), false); args3840.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn3839, std::move(args3840)); }()); return Binary("Add", v3838, Value(int64_t{1})); }());
Put(s->LocalAt(11), Value("recovery_steps"), v3837);
if (static_cast<bool>(s->LocalAt(16))) {
(void)([&]() -> Value { auto fn3841 = Attribute(([&]() -> Value { auto fn3843 = Attribute(s->LocalAt(11), "setdefault"); Arguments args3844; args3844.positional.reserve(2); args3844.Add(Value("recovery_failures"), false); args3844.Add(List({}), false); return Call(c, fn3843, std::move(args3844)); }()), "append"); Arguments args3842; args3842.Add(([&]() -> Value { auto dict3845 = Dict(); auto key3846 = Value("step"); Put(dict3845, key3846, ([&]() -> Value { auto fn3847 = s->Global("int"); Arguments args3848; args3848.Add(([&]() -> Value { auto fn3849 = s->Global("_get"); Arguments args3850; args3850.positional.reserve(2); args3850.Add(s->LocalAt(9), false); args3850.Add(Value("step"), false); return Call(c, fn3849, std::move(args3850)); }()), false); return Call(c, fn3847, std::move(args3848)); }())); auto key3851 = Value("problems"); Put(dict3845, key3851, s->LocalAt(16)); return dict3845; }()), false); return Call(c, fn3841, std::move(args3842)); }());
}
return s->LocalAt(0);
return {};
}
}  // namespace kagg::opponents::compiled
