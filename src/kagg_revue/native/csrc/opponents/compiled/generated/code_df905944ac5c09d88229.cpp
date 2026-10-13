// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_df905944ac5c09d88229(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"farms", "observation", "player", "state"};
s->PrepareSlots(s_names);
auto v12947 = Get(s->LocalAt(1), Value("farms"));
s->SetAt(0, v12947);
auto v12948 = ([&]() -> Value { auto fn12949 = s->Global("int"); Arguments args12950; args12950.Add(Get(s->LocalAt(1), Value("player")), false); return Call(c, fn12949, std::move(args12950)); }());
s->SetAt(2, v12948);
if (static_cast<bool>(([&]() -> Value { auto v12951 = ([&]() -> Value { auto fn12953 = s->Global("len"); Arguments args12954; args12954.Add(Get(Get(s->LocalAt(0), s->LocalAt(2)), Value("hands")), false); return Call(c, fn12953, std::move(args12954)); }()); Value v12952; v12952 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v12951, v12952))) return Value(false); v12951 = v12952; return Value(true); }()))) {
(void)([&]() -> Value { auto fn12955 = Attribute(Get(s->LocalAt(3), Value("hist")), "append"); Arguments args12956; args12956.Add(([&]() -> Value { auto fn12957 = s->Global("_race_positions_equal"); Arguments args12958; args12958.positional.reserve(2); args12958.Add(s->LocalAt(0), false); args12958.Add(s->LocalAt(2), false); return Call(c, fn12957, std::move(args12958)); }()), false); return Call(c, fn12955, std::move(args12956)); }());
if (static_cast<bool>(([&]() -> Value { auto v12959 = ([&]() -> Value { auto fn12961 = s->Global("len"); Arguments args12962; args12962.Add(Get(s->LocalAt(3), Value("hist")), false); return Call(c, fn12961, std::move(args12962)); }()); Value v12960; v12960 = Value(int64_t{6}); if (!static_cast<bool>(Binary("Gt", v12959, v12960))) return Value(false); v12959 = v12960; return Value(true); }()))) {
(void)([&]() -> Value { auto fn12963 = Attribute(Get(s->LocalAt(3), Value("hist")), "pop"); Arguments args12964; args12964.Add(Value(int64_t{0}), false); return Call(c, fn12963, std::move(args12964)); }());
}
}
return ([&]() -> Value { auto v12965 = ([&]() -> Value { auto v12966 = ([&]() -> Value { auto fn12968 = s->Global("len"); Arguments args12969; args12969.Add(Get(s->LocalAt(3), Value("hist")), false); return Call(c, fn12968, std::move(args12969)); }()); Value v12967; v12967 = Value(int64_t{4}); if (!static_cast<bool>(Binary("GtE", v12966, v12967))) return Value(false); v12966 = v12967; return Value(true); }()); if (!static_cast<bool>(v12965)) return v12965; v12965 = ([&]() -> Value { auto v12970 = ([&]() -> Value { auto fn12972 = s->Global("sum"); Arguments args12973; args12973.Add(Get(s->LocalAt(3), Value("hist")), false); return Call(c, fn12972, std::move(args12973)); }()); Value v12971; v12971 = Value(int64_t{4}); if (!static_cast<bool>(Binary("GtE", v12970, v12971))) return Value(false); v12970 = v12971; return Value(true); }()); if (!static_cast<bool>(v12965)) return v12965; v12965 = ([&]() -> Value { auto v12974 = ([&]() -> Value { auto fn12976 = s->Global("_r37_similarity"); Arguments args12977; args12977.Add(s->LocalAt(1), false); return Call(c, fn12976, std::move(args12977)); }()); Value v12975; v12975 = Value(0.95); if (!static_cast<bool>(Binary("GtE", v12974, v12975))) return Value(false); v12974 = v12975; return Value(true); }()); return v12965; }());
return {};
}
}  // namespace kagg::opponents::compiled
