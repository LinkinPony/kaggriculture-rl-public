// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_4a4706a4805758aa4ce6(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"config", "farm", "index", "mismatch", "n", "obs", "parent_action", "plan", "private", "result", "step"};
s->PrepareSlots(s_names);
auto v3852 = ([&]() -> Value { auto fn3853 = s->Global("int"); Arguments args3854; args3854.Add(([&]() -> Value { auto fn3855 = s->Global("_get"); Arguments args3856; args3856.positional.reserve(3); args3856.Add(s->LocalAt(5), false); args3856.Add(Value("step"), false); args3856.Add(Unary("USub", Value(int64_t{1})), false); return Call(c, fn3855, std::move(args3856)); }()), false); return Call(c, fn3853, std::move(args3854)); }());
s->SetAt(10, v3852);
if (static_cast<bool>(([&]() -> Value { auto v3857 = Unary("Not", s->LocalAt(7)); if (static_cast<bool>(v3857)) return v3857; v3857 = Unary("Not", ([&]() -> Value { auto fn3858 = PrepareDictionaryGet(s->LocalAt(7)); Arguments args3859; args3859.Add(Value("accepted"), false); return CallDictionaryGet(c, fn3858, std::move(args3859)); }())); if (static_cast<bool>(v3857)) return v3857; v3857 = Unary("Not", ([&]() -> Value { auto v3860 = s->Global("START"); Value v3861; v3861 = s->LocalAt(10); if (!static_cast<bool>(Binary("LtE", v3860, v3861))) return Value(false); v3860 = v3861; v3861 = s->Global("FINAL"); if (!static_cast<bool>(Binary("LtE", v3860, v3861))) return Value(false); v3860 = v3861; return Value(true); }())); return v3857; }()))) {
return s->LocalAt(6);
}
if (static_cast<bool>(([&]() -> Value { auto fn3862 = PrepareDictionaryGet(s->LocalAt(7)); Arguments args3863; args3863.Add(Value("abandoned"), false); return CallDictionaryGet(c, fn3862, std::move(args3863)); }()))) {
return (static_cast<bool>(([&]() -> Value { auto fn3864 = PrepareDictionaryGet(s->LocalAt(7)); Arguments args3865; args3865.Add(Value("deviated"), false); return CallDictionaryGet(c, fn3864, std::move(args3865)); }())) ? ([&]() -> Value { auto fn3866 = s->Global("_recover_observed"); Arguments args3867; args3867.positional.reserve(4); args3867.Add(s->LocalAt(5), false); args3867.Add(s->LocalAt(0), false); args3867.Add(s->LocalAt(6), false); args3867.Add(s->LocalAt(7), false); return Call(c, fn3866, std::move(args3867)); }()) : s->LocalAt(6));
}
auto v3868 = ([&]() -> Value { auto v3869 = s->LocalAt(10); return Binary("Sub", v3869, s->Global("START")); }());
s->SetAt(2, v3868);
auto v3870 = ([&]() -> Value { auto v3871 = Value(int64_t{1}); return Binary("Add", v3871, ([&]() -> Value { auto fn3872 = s->Global("len"); Arguments args3873; args3873.Add(Get(Get(([&]() -> Value { auto fn3874 = s->Global("physical_state"); Arguments args3875; args3875.Add(s->LocalAt(5), false); return Call(c, fn3874, std::move(args3875)); }()), Value(int64_t{0})), Value("hands")), false); return Call(c, fn3872, std::move(args3873)); }())); }());
s->SetAt(4, v3870);
auto v3876 = ([&]() -> Value { auto v3877 = ([&]() -> Value { auto v3878 = ([&]() -> Value { auto fn3880 = s->Global("physical_state"); Arguments args3881; args3881.Add(s->LocalAt(5), false); return Call(c, fn3880, std::move(args3881)); }()); Value v3879; v3879 = Get(Get(s->LocalAt(7), Value("expected_states")), s->LocalAt(2)); if (!static_cast<bool>(Binary("NotEq", v3878, v3879))) return Value(false); v3878 = v3879; return Value(true); }()); if (static_cast<bool>(v3877)) return v3877; v3877 = ([&]() -> Value { auto v3882 = ([&]() -> Value { auto fn3884 = s->Global("_effective_action"); Arguments args3885; args3885.positional.reserve(2); args3885.Add(s->LocalAt(6), false); args3885.Add(s->LocalAt(4), false); return Call(c, fn3884, std::move(args3885)); }()); Value v3883; v3883 = ([&]() -> Value { auto fn3886 = s->Global("_effective_action"); Arguments args3887; args3887.positional.reserve(2); args3887.Add(Get(Get(s->LocalAt(7), Value("baseline")), s->LocalAt(2)), false); args3887.Add(s->LocalAt(4), false); return Call(c, fn3886, std::move(args3887)); }()); if (!static_cast<bool>(Binary("NotEq", v3882, v3883))) return Value(false); v3882 = v3883; return Value(true); }()); return v3877; }());
s->SetAt(3, v3876);
if (static_cast<bool>(s->LocalAt(3))) {
auto v3888 = Value(true);
Put(s->LocalAt(7), Value("abandoned"), v3888);
auto v3889 = s->LocalAt(10);
Put(s->LocalAt(7), Value("abandon_step"), v3889);
auto v3890 = Value("physical observation or effective baseline action diverged");
Put(s->LocalAt(7), Value("reason"), v3890);
auto v3891 = Value(true);
Put(s->LocalAt(7), Value("safety_failure"), v3891);
return (static_cast<bool>(([&]() -> Value { auto fn3892 = PrepareDictionaryGet(s->LocalAt(7)); Arguments args3893; args3893.Add(Value("deviated"), false); return CallDictionaryGet(c, fn3892, std::move(args3893)); }())) ? ([&]() -> Value { auto fn3894 = s->Global("_recover_observed"); Arguments args3895; args3895.positional.reserve(4); args3895.Add(s->LocalAt(5), false); args3895.Add(s->LocalAt(0), false); args3895.Add(s->LocalAt(6), false); args3895.Add(s->LocalAt(7), false); return Call(c, fn3894, std::move(args3895)); }()) : s->LocalAt(6));
}
auto v3896 = ([&]() -> Value { auto fn3897 = s->Global("deepcopy"); Arguments args3898; args3898.Add(Get(Get(s->LocalAt(7), Value("actions")), s->LocalAt(2)), false); return Call(c, fn3897, std::move(args3898)); }());
s->SetAt(9, v3896);
if (static_cast<bool>(([&]() -> Value { auto v3899 = s->LocalAt(10); Value v3900; v3900 = s->Global("FINAL"); if (!static_cast<bool>(Binary("Eq", v3899, v3900))) return Value(false); v3899 = v3900; return Value(true); }()))) {
auto v3901 = ([&]() -> Value { auto fn3902 = s->Global("physical_state"); Arguments args3903; args3903.Add(s->LocalAt(5), false); return Call(c, fn3902, std::move(args3903)); }());
auto unpack3904 = Iterate(v3901);
ValidateUnpack(unpack3904, 2, false);
s->SetAt(1, unpack3904.at(0));
s->SetAt(8, unpack3904.at(1));
auto v3905 = ([&]() -> Value { auto fn3906 = s->Global("shop_liquidation"); Arguments args3907; args3907.positional.reserve(3); args3907.Add(s->LocalAt(1), false); args3907.Add(s->LocalAt(8), false); args3907.Add(Get(([&]() -> Value { auto fn3908 = s->Global("_get"); Arguments args3909; args3909.positional.reserve(2); args3909.Add(s->LocalAt(5), false); args3909.Add(Value("market"), false); return Call(c, fn3908, std::move(args3909)); }()), Value("prices")), false); return Call(c, fn3906, std::move(args3907)); }());
s->SetAt(9, v3905);
}
if (static_cast<bool>(([&]() -> Value { auto v3910 = ([&]() -> Value { auto fn3912 = s->Global("_commands"); Arguments args3913; args3913.positional.reserve(2); args3913.Add(s->LocalAt(9), false); args3913.Add(s->LocalAt(4), false); return Call(c, fn3912, std::move(args3913)); }()); Value v3911; v3911 = ([&]() -> Value { auto fn3914 = s->Global("_commands"); Arguments args3915; args3915.positional.reserve(2); args3915.Add(s->LocalAt(6), false); args3915.Add(s->LocalAt(4), false); return Call(c, fn3914, std::move(args3915)); }()); if (!static_cast<bool>(Binary("NotEq", v3910, v3911))) return Value(false); v3910 = v3911; return Value(true); }()))) {
auto v3916 = Value(true);
Put(s->LocalAt(7), Value("deviated"), v3916);
}
return s->LocalAt(9);
return {};
}
}  // namespace kagg::opponents::compiled
