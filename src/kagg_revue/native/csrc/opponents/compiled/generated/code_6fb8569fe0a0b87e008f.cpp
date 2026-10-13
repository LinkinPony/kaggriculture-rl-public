// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_6fb8569fe0a0b87e008f(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"native", "seat", "t", "tape"};
s->PrepareSlots(s_names);
auto v23820 = ([&]() -> Value { auto fn23821 = PrepareDictionaryGet(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players")); Arguments args23822; args23822.Add(s->LocalAt(1), false); return CallDictionaryGet(c, fn23821, std::move(args23822)); }());
s->SetAt(0, v23820);
if (static_cast<bool>(([&]() -> Value { auto v23823 = Unary("Not", s->LocalAt(0)); if (static_cast<bool>(v23823)) return v23823; v23823 = ([&]() -> Value { auto v23824 = s->LocalAt(2); Value v23825; v23825 = Value(int64_t{719}); if (!static_cast<bool>(Binary("Gt", v23824, v23825))) return Value(false); v23824 = v23825; return Value(true); }()); return v23823; }()))) {
return ([&]() -> Value { auto dict23826 = Dict(); return dict23826; }());
}
auto v23827 = Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"), (static_cast<bool>(([&]() -> Value { auto v23828 = s->LocalAt(2); Value v23829; v23829 = Value(int64_t{648}); if (!static_cast<bool>(Binary("GtE", v23828, v23829))) return Value(false); v23828 = v23829; return Value(true); }())) ? Value(int64_t{2}) : Get(s->LocalAt(0), Value("route"))));
s->SetAt(3, v23827);
return (static_cast<bool>(([&]() -> Value { auto v23830 = ([&]() -> Value { auto v23831 = s->LocalAt(2); Value v23832; v23832 = ([&]() -> Value { auto fn23833 = s->Global("len"); Arguments args23834; args23834.Add(s->LocalAt(3), false); return Call(c, fn23833, std::move(args23834)); }()); if (!static_cast<bool>(Binary("Lt", v23831, v23832))) return Value(false); v23831 = v23832; return Value(true); }()); if (!static_cast<bool>(v23830)) return v23830; v23830 = ([&]() -> Value { auto fn23835 = s->Global("isinstance"); Arguments args23836; args23836.positional.reserve(2); args23836.Add(Get(s->LocalAt(3), s->LocalAt(2)), false); args23836.Add(s->Global("dict"), false); return Call(c, fn23835, std::move(args23836)); }()); return v23830; }())) ? Get(s->LocalAt(3), s->LocalAt(2)) : ([&]() -> Value { auto dict23837 = Dict(); return dict23837; }()));
return {};
}
}  // namespace kagg::opponents::compiled
