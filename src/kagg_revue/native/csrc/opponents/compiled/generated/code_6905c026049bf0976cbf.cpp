// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_6905c026049bf0976cbf(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"native", "seat", "t", "tape"};
s->PrepareSlots(s_names);
auto v21718 = ([&]() -> Value { auto fn21719 = PrepareDictionaryGet(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "players")); Arguments args21720; args21720.Add(s->LocalAt(1), false); return CallDictionaryGet(c, fn21719, std::move(args21720)); }());
s->SetAt(0, v21718);
if (static_cast<bool>(([&]() -> Value { auto v21721 = Unary("Not", s->LocalAt(0)); if (static_cast<bool>(v21721)) return v21721; v21721 = ([&]() -> Value { auto v21722 = s->LocalAt(2); Value v21723; v21723 = Value(int64_t{719}); if (!static_cast<bool>(Binary("Gt", v21722, v21723))) return Value(false); v21722 = v21723; return Value(true); }()); return v21721; }()))) {
return ([&]() -> Value { auto dict21724 = Dict(); return dict21724; }());
}
auto v21725 = Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"), (static_cast<bool>(([&]() -> Value { auto v21726 = s->LocalAt(2); Value v21727; v21727 = Value(int64_t{648}); if (!static_cast<bool>(Binary("GtE", v21726, v21727))) return Value(false); v21726 = v21727; return Value(true); }())) ? Value(int64_t{2}) : Get(s->LocalAt(0), Value("route"))));
s->SetAt(3, v21725);
return (static_cast<bool>(([&]() -> Value { auto v21728 = ([&]() -> Value { auto v21729 = s->LocalAt(2); Value v21730; v21730 = ([&]() -> Value { auto fn21731 = s->Global("len"); Arguments args21732; args21732.Add(s->LocalAt(3), false); return Call(c, fn21731, std::move(args21732)); }()); if (!static_cast<bool>(Binary("Lt", v21729, v21730))) return Value(false); v21729 = v21730; return Value(true); }()); if (!static_cast<bool>(v21728)) return v21728; v21728 = ([&]() -> Value { auto fn21733 = s->Global("isinstance"); Arguments args21734; args21734.positional.reserve(2); args21734.Add(Get(s->LocalAt(3), s->LocalAt(2)), false); args21734.Add(s->Global("dict"), false); return Call(c, fn21733, std::move(args21734)); }()); return v21728; }())) ? Get(s->LocalAt(3), s->LocalAt(2)) : ([&]() -> Value { auto dict21735 = Dict(); return dict21735; }()));
return {};
}
}  // namespace kagg::opponents::compiled
