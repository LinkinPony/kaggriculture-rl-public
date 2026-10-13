// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_8e02ebc71d0b56e5f637(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"configuration", "observation", "plan", "player", "previous", "shops", "step"};
s->PrepareSlots(s_names);
auto v14026 = ([&]() -> Value { auto fn14027 = s->Global("int"); Arguments args14028; args14028.Add(Get(s->LocalAt(1), Value("step")), false); return Call(c, fn14027, std::move(args14028)); }());
s->SetAt(6, v14026);
auto v14029 = ([&]() -> Value { auto fn14030 = s->Global("int"); Arguments args14031; args14031.Add(Get(s->LocalAt(1), Value("player")), false); return Call(c, fn14030, std::move(args14031)); }());
s->SetAt(3, v14029);
auto v14032 = ([&]() -> Value { auto fn14033 = PrepareDictionaryGet(s->Global("_STATE")); Arguments args14034; args14034.Add(s->LocalAt(3), false); return CallDictionaryGet(c, fn14033, std::move(args14034)); }());
s->SetAt(4, v14032);
if (static_cast<bool>(([&]() -> Value { auto v14035 = ([&]() -> Value { auto v14036 = s->LocalAt(4); Value v14037; v14037 = Value{}; if (!static_cast<bool>(Binary("Is", v14036, v14037))) return Value(false); v14036 = v14037; return Value(true); }()); if (static_cast<bool>(v14035)) return v14035; v14035 = ([&]() -> Value { auto v14038 = s->LocalAt(6); Value v14039; v14039 = Get(s->LocalAt(4), Value(int64_t{0})); if (!static_cast<bool>(Binary("LtE", v14038, v14039))) return Value(false); v14038 = v14039; return Value(true); }()); return v14035; }()))) {
auto v14040 = Value(int64_t{0});
s->SetAt(2, v14040);
}
else {
auto v14041 = Get(s->LocalAt(4), Value(int64_t{1}));
s->SetAt(2, v14041);
}
auto v14042 = ([&]() -> Value { auto fn14043 = s->Global("tuple"); Arguments args14044; args14044.Add(Get(Get(s->LocalAt(1), Value("town")), Value("unlocked_shops")), false); return Call(c, fn14043, std::move(args14044)); }());
s->SetAt(5, v14042);
if (static_cast<bool>(([&]() -> Value { auto v14045 = s->LocalAt(6); Value v14046; v14046 = Value(int64_t{144}); if (!static_cast<bool>(Binary("Eq", v14045, v14046))) return Value(false); v14045 = v14046; return Value(true); }()))) {
auto v14047 = ([&]() -> Value { auto fn14048 = PrepareDictionaryGet(s->Global("_ROUTES")); Arguments args14049; args14049.positional.reserve(2); args14049.Add(Slice(s->LocalAt(5), Value{}, Value(int64_t{2}), Value{}), false); args14049.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn14048, std::move(args14049)); }());
s->SetAt(2, v14047);
}
if (static_cast<bool>(([&]() -> Value { auto v14050 = s->LocalAt(6); Value v14051; v14051 = Value(int64_t{648}); if (!static_cast<bool>(Binary("Eq", v14050, v14051))) return Value(false); v14050 = v14051; return Value(true); }()))) {
auto v14052 = Value(int64_t{1});
s->SetAt(2, v14052);
}
auto v14053 = Tuple({s->LocalAt(6), s->LocalAt(2)});
Put(s->Global("_STATE"), s->LocalAt(3), v14053);
return Get(Get(s->Global("_TAPES"), s->LocalAt(2)), s->LocalAt(6));
return {};
}
}  // namespace kagg::opponents::compiled
