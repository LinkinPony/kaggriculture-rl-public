// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_cf9b57155631545a5558(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"board_size", "half"};
s->PrepareSlots(s_names);
auto v2091 = ([&]() -> Value { auto v2092 = s->LocalAt(0); return Binary("FloorDiv", v2092, Value(int64_t{2})); }());
s->SetAt(1, v2091);
return List({Tuple({([&]() -> Value { auto v2093 = s->LocalAt(1); return Binary("Sub", v2093, Value(int64_t{1})); }()), ([&]() -> Value { auto v2094 = s->LocalAt(1); return Binary("Sub", v2094, Value(int64_t{1})); }())}), Tuple({s->LocalAt(1), ([&]() -> Value { auto v2095 = s->LocalAt(1); return Binary("Sub", v2095, Value(int64_t{1})); }())}), Tuple({([&]() -> Value { auto v2096 = s->LocalAt(1); return Binary("Sub", v2096, Value(int64_t{1})); }()), s->LocalAt(1)}), Tuple({s->LocalAt(1), s->LocalAt(1)})});
return {};
}
}  // namespace kagg::opponents::compiled
