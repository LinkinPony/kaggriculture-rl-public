// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_e7ddba6e5f99eff1bd95(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"board", "half", "pos"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v91 = Unary("Not", ([&]() -> Value { auto fn92 = s->Global("isinstance"); Arguments args93; args93.positional.reserve(2); args93.Add(s->LocalAt(2), false); args93.Add(Tuple({s->Global("list"), s->Global("tuple")}), false); return Call(c, fn92, std::move(args93)); }())); if (static_cast<bool>(v91)) return v91; v91 = ([&]() -> Value { auto v94 = ([&]() -> Value { auto fn96 = s->Global("len"); Arguments args97; args97.Add(s->LocalAt(2), false); return Call(c, fn96, std::move(args97)); }()); Value v95; v95 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Lt", v94, v95))) return Value(false); v94 = v95; return Value(true); }()); return v91; }()))) {
return Value(false);
}
auto v98 = ([&]() -> Value { auto v99 = s->LocalAt(0); return Binary("FloorDiv", v99, Value(int64_t{2})); }());
s->SetAt(1, v98);
return ([&]() -> Value { auto v100 = ([&]() -> Value { auto v101 = Get(s->LocalAt(2), Value(int64_t{0})); Value v102; v102 = Tuple({([&]() -> Value { auto v103 = s->LocalAt(1); return Binary("Sub", v103, Value(int64_t{1})); }()), s->LocalAt(1)}); if (!static_cast<bool>(Binary("In", v101, v102))) return Value(false); v101 = v102; return Value(true); }()); if (!static_cast<bool>(v100)) return v100; v100 = ([&]() -> Value { auto v104 = Get(s->LocalAt(2), Value(int64_t{1})); Value v105; v105 = Tuple({([&]() -> Value { auto v106 = s->LocalAt(1); return Binary("Sub", v106, Value(int64_t{1})); }()), s->LocalAt(1)}); if (!static_cast<bool>(Binary("In", v104, v105))) return Value(false); v104 = v105; return Value(true); }()); return v100; }());
return {};
}
}  // namespace kagg::opponents::compiled
