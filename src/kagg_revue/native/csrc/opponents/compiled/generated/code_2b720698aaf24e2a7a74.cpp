// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_2b720698aaf24e2a7a74(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "observation", "player", "st", "step"};
s->PrepareSlots(s_names);
auto v29767 = Tuple({([&]() -> Value { auto fn29768 = s->Global("int"); Arguments args29769; args29769.Add(Get(s->LocalAt(2), Value("player")), false); return Call(c, fn29768, std::move(args29769)); }()), ([&]() -> Value { auto fn29770 = s->Global("int"); Arguments args29771; args29771.Add(Get(s->LocalAt(2), Value("step")), false); return Call(c, fn29770, std::move(args29771)); }())});
auto unpack29772 = Iterate(v29767);
ValidateUnpack(unpack29772, 2, false);
s->SetAt(3, unpack29772.at(0));
s->SetAt(5, unpack29772.at(1));
auto v29773 = ([&]() -> Value { auto fn29774 = PrepareDictionaryGet(s->Global("_V92_Q")); Arguments args29775; args29775.Add(s->LocalAt(3), false); return CallDictionaryGet(c, fn29774, std::move(args29775)); }());
s->SetAt(4, v29773);
if (static_cast<bool>(([&]() -> Value { auto v29776 = ([&]() -> Value { auto v29777 = s->LocalAt(4); Value v29778; v29778 = Value{}; if (!static_cast<bool>(Binary("Is", v29777, v29778))) return Value(false); v29777 = v29778; return Value(true); }()); if (static_cast<bool>(v29776)) return v29776; v29776 = ([&]() -> Value { auto v29779 = s->LocalAt(5); Value v29780; v29780 = Get(s->LocalAt(4), Value("step")); if (!static_cast<bool>(Binary("LtE", v29779, v29780))) return Value(false); v29779 = v29780; return Value(true); }()); return v29776; }()))) {
auto v29781 = ([&]() -> Value { auto fn29782 = s->Global("_v92_q_new_state"); Arguments args29783; return Call(c, fn29782, std::move(args29783)); }());
s->SetAt(4, v29781);
Put(s->Global("_V92_Q"), s->LocalAt(3), v29781);
}
auto v29784 = s->LocalAt(5);
Put(s->LocalAt(4), Value("step"), v29784);
auto v29785 = ([&]() -> Value { auto fn29786 = s->Global("_V92_Q_PARENT"); Arguments args29787; args29787.positional.reserve(2); args29787.Add(s->LocalAt(2), false); args29787.Add(s->LocalAt(1), false); return Call(c, fn29786, std::move(args29787)); }());
s->SetAt(0, v29785);
try {
return ([&]() -> Value { auto fn29789 = s->Global("_v92_predict2"); Arguments args29790; args29790.positional.reserve(3); args29790.Add(s->LocalAt(2), false); args29790.Add(s->LocalAt(0), false); args29790.Add(s->LocalAt(4), false); return Call(c, fn29789, std::move(args29790)); }());
} catch (const Error& error29788) {
if (Matches(error29788, s->Global("Exception"))) {
auto v29791 = s->Global("_V92_Q_REPORT");
auto v29792 = Value("pred_errors");
auto v29793 = Get(v29791, v29792);
Put(v29791, v29792, Inplace("Add", v29793, Value(int64_t{1})));
return s->LocalAt(0);
}
else { throw; }
}
return {};
}
}  // namespace kagg::opponents::compiled
