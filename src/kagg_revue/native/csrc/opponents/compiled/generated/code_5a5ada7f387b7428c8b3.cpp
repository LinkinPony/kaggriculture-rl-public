// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_5a5ada7f387b7428c8b3(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"a", "b", "first", "mls"};
s->PrepareSlots(s_names);
auto v21867 = ([&]() -> Value { auto fn21868 = s->Global("max"); Arguments args21869; args21869.positional.reserve(2); args21869.Add(s->LocalAt(0), false); args21869.Add(s->LocalAt(3), false); return Call(c, fn21868, std::move(args21869)); }());
s->SetAt(0, v21867);
if (static_cast<bool>(([&]() -> Value { auto v21870 = s->LocalAt(1); Value v21871; v21871 = s->LocalAt(0); if (!static_cast<bool>(Binary("LtE", v21870, v21871))) return Value(false); v21870 = v21871; return Value(true); }()))) {
return Value(int64_t{0});
}
auto v21872 = (static_cast<bool>(([&]() -> Value { auto v21873 = ([&]() -> Value { auto v21875 = ([&]() -> Value { auto v21876 = s->LocalAt(0); return Binary("Sub", v21876, s->LocalAt(3)); }()); return Binary("Mod", v21875, Value(int64_t{2})); }()); Value v21874; v21874 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v21873, v21874))) return Value(false); v21873 = v21874; return Value(true); }())) ? s->LocalAt(0) : ([&]() -> Value { auto v21877 = s->LocalAt(0); return Binary("Add", v21877, Value(int64_t{1})); }()));
s->SetAt(2, v21872);
return (static_cast<bool>(([&]() -> Value { auto v21878 = s->LocalAt(2); Value v21879; v21879 = s->LocalAt(1); if (!static_cast<bool>(Binary("GtE", v21878, v21879))) return Value(false); v21878 = v21879; return Value(true); }())) ? Value(int64_t{0}) : ([&]() -> Value { auto v21880 = ([&]() -> Value { auto v21881 = ([&]() -> Value { auto v21882 = ([&]() -> Value { auto v21883 = s->LocalAt(1); return Binary("Sub", v21883, Value(int64_t{1})); }()); return Binary("Sub", v21882, s->LocalAt(2)); }()); return Binary("FloorDiv", v21881, Value(int64_t{2})); }()); return Binary("Add", v21880, Value(int64_t{1})); }()));
return {};
}
}  // namespace kagg::opponents::compiled
