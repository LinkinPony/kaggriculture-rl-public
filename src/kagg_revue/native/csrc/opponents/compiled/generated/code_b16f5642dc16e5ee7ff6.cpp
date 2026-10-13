// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_b16f5642dc16e5ee7ff6(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"configuration", "k", "observation"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v31538 = ([&]() -> Value { auto fn31540 = s->Global("int"); Arguments args31541; args31541.Add(Get(s->LocalAt(2), Value("step")), false); return Call(c, fn31540, std::move(args31541)); }()); Value v31539; v31539 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v31538, v31539))) return Value(false); v31538 = v31539; return Value(true); }()))) {
for (const auto& item31542 : Iterate(s->Global("_V13V_REPORT"))) {
s->SetAt(1, item31542);
auto v31543 = Value(int64_t{0});
Put(s->Global("_V13V_REPORT"), s->LocalAt(1), v31543);
}
}
return ([&]() -> Value { auto fn31544 = s->Global("_V13V_PARENT"); Arguments args31545; args31545.positional.reserve(2); args31545.Add(s->LocalAt(2), false); args31545.Add(s->LocalAt(0), false); return Call(c, fn31544, std::move(args31545)); }());
return {};
}
}  // namespace kagg::opponents::compiled
