// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_46774da9096ce18bf037(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "observation", "seat", "state", "step"};
s->PrepareSlots(s_names);
auto v20243 = ([&]() -> Value { auto fn20244 = s->Global("_Y_HOST"); Arguments args20245; args20245.positional.reserve(2); args20245.Add(s->LocalAt(2), false); args20245.Add(s->LocalAt(1), false); return Call(c, fn20244, std::move(args20245)); }());
s->SetAt(0, v20243);
try {
auto v20247 = ([&]() -> Value { auto fn20248 = s->Global("int"); Arguments args20249; args20249.Add(Get(s->LocalAt(2), Value("player")), false); return Call(c, fn20248, std::move(args20249)); }());
s->SetAt(3, v20247);
auto v20250 = ([&]() -> Value { auto fn20251 = s->Global("int"); Arguments args20252; args20252.Add(Get(s->LocalAt(2), Value("step")), false); return Call(c, fn20251, std::move(args20252)); }());
s->SetAt(5, v20250);
auto v20253 = ([&]() -> Value { auto fn20254 = PrepareDictionaryGet(s->Global("_Y_STATES")); Arguments args20255; args20255.Add(s->LocalAt(3), false); return CallDictionaryGet(c, fn20254, std::move(args20255)); }());
s->SetAt(4, v20253);
if (static_cast<bool>(([&]() -> Value { auto v20256 = ([&]() -> Value { auto v20257 = s->LocalAt(4); Value v20258; v20258 = Value{}; if (!static_cast<bool>(Binary("Is", v20257, v20258))) return Value(false); v20257 = v20258; return Value(true); }()); if (static_cast<bool>(v20256)) return v20256; v20256 = ([&]() -> Value { auto v20259 = s->LocalAt(5); Value v20260; v20260 = Get(s->LocalAt(4), Value("last")); if (!static_cast<bool>(Binary("LtE", v20259, v20260))) return Value(false); v20259 = v20260; return Value(true); }()); return v20256; }()))) {
auto v20261 = ([&]() -> Value { auto fn20262 = s->Global("_y_new_state"); Arguments args20263; return Call(c, fn20262, std::move(args20263)); }());
s->SetAt(4, v20261);
Put(s->Global("_Y_STATES"), s->LocalAt(3), v20261);
}
auto v20264 = s->LocalAt(5);
Put(s->LocalAt(4), Value("last"), v20264);
return ([&]() -> Value { auto fn20265 = s->Global("_y_controller"); Arguments args20266; args20266.positional.reserve(4); args20266.Add(s->LocalAt(2), false); args20266.Add(s->LocalAt(0), false); args20266.Add(s->LocalAt(4), false); args20266.Add(s->Global("_Y_CFG"), false); return Call(c, fn20265, std::move(args20266)); }());
} catch (const Error& error20246) {
if (Matches(error20246, s->Global("Exception"))) {
auto v20267 = s->Global("_Y_REPORT");
auto v20268 = Value("errors");
auto v20269 = Get(v20267, v20268);
Put(v20267, v20268, Inplace("Add", v20269, Value(int64_t{1})));
return s->LocalAt(0);
}
else { throw; }
}
return {};
}
}  // namespace kagg::opponents::compiled
