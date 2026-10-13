// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_d6e15344a983b8ea8def(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"configuration", "observation", "result", "state"};
s->PrepareSlots(s_names);
auto v9243 = Value{};
s->SetAt(3, v9243);
try {
auto v9245 = ([&]() -> Value { auto fn9246 = s->Global("_r70_before"); Arguments args9247; args9247.Add(s->LocalAt(1), false); return Call(c, fn9246, std::move(args9247)); }());
s->SetAt(3, v9245);
} catch (const Error& error9244) {
if (Matches(error9244, s->Global("Exception"))) {
auto v9248 = ([&]() -> Value { auto v9249 = ([&]() -> Value { auto fn9250 = PrepareDictionaryGet(s->Global("_R70_REPORT")); Arguments args9251; args9251.positional.reserve(2); args9251.Add(Value("parent_input_errors"), false); args9251.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn9250, std::move(args9251)); }()); return Binary("Add", v9249, Value(int64_t{1})); }());
Put(s->Global("_R70_REPORT"), Value("parent_input_errors"), v9248);
}
else { throw; }
}
auto v9252 = ([&]() -> Value { auto fn9253 = s->Global("_R70_PARENT"); Arguments args9254; args9254.positional.reserve(2); args9254.Add(s->LocalAt(1), false); args9254.Add(s->LocalAt(0), false); return Call(c, fn9253, std::move(args9254)); }());
s->SetAt(2, v9252);
try {
if (static_cast<bool>(([&]() -> Value { auto v9256 = s->LocalAt(3); Value v9257; v9257 = Value{}; if (!static_cast<bool>(Binary("IsNot", v9256, v9257))) return Value(false); v9256 = v9257; return Value(true); }()))) {
(void)([&]() -> Value { auto fn9258 = s->Global("_r70_after"); Arguments args9259; args9259.positional.reserve(3); args9259.Add(s->LocalAt(1), false); args9259.Add(s->LocalAt(2), false); args9259.Add(s->LocalAt(3), false); return Call(c, fn9258, std::move(args9259)); }());
}
} catch (const Error& error9255) {
if (Matches(error9255, s->Global("Exception"))) {
auto v9260 = ([&]() -> Value { auto v9261 = ([&]() -> Value { auto fn9262 = PrepareDictionaryGet(s->Global("_R70_REPORT")); Arguments args9263; args9263.positional.reserve(2); args9263.Add(Value("parent_input_errors"), false); args9263.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn9262, std::move(args9263)); }()); return Binary("Add", v9261, Value(int64_t{1})); }());
Put(s->Global("_R70_REPORT"), Value("parent_input_errors"), v9260);
}
else { throw; }
}
(void)([&]() -> Value { auto fn9264 = Attribute(s->Global("_R70_REPORT"), "update"); Arguments args9265; args9265.Add(([&]() -> Value { auto fn9266 = s->Global("getattr"); Arguments args9267; args9267.positional.reserve(3); args9267.Add(s->Global("_R70_PARENT"), false); args9267.Add(Value("telemetry"), false); args9267.Add(([&]() -> Value { auto dict9268 = Dict(); return dict9268; }()), false); return Call(c, fn9266, std::move(args9267)); }()), false); return Call(c, fn9264, std::move(args9265)); }());
return s->LocalAt(2);
return {};
}
}  // namespace kagg::opponents::compiled
