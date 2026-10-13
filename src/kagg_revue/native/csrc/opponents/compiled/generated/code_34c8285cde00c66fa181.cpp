// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_34c8285cde00c66fa181(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"inv", "item", "n"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v2159 = ([&]() -> Value { auto fn2161 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args2162; args2162.positional.reserve(2); args2162.Add(s->LocalAt(1), false); args2162.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn2161, std::move(args2162)); }()); Value v2160; v2160 = s->LocalAt(2); if (!static_cast<bool>(Binary("Lt", v2159, v2160))) return Value(false); v2159 = v2160; return Value(true); }()))) {
return Value(false);
}
auto v2163 = s->LocalAt(0);
auto v2164 = s->LocalAt(1);
auto v2165 = Get(v2163, v2164);
Put(v2163, v2164, Inplace("Sub", v2165, s->LocalAt(2)));
if (static_cast<bool>(([&]() -> Value { auto v2166 = Get(s->LocalAt(0), s->LocalAt(1)); Value v2167; v2167 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v2166, v2167))) return Value(false); v2166 = v2167; return Value(true); }()))) {
Erase(s->LocalAt(0), s->LocalAt(1));
}
return Value(true);
return {};
}
}  // namespace kagg::opponents::compiled
