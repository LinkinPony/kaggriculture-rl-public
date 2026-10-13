// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_41426670890e05e283eb(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"configuration", "k", "observation", "result"};
s->PrepareSlots(s_names);
try {
if (static_cast<bool>(([&]() -> Value { auto v7460 = ([&]() -> Value { auto fn7462 = s->Global("int"); Arguments args7463; args7463.Add(([&]() -> Value { auto fn7464 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args7465; args7465.positional.reserve(2); args7465.Add(Value("step"), false); args7465.Add(Unary("USub", Value(int64_t{1})), false); return CallDictionaryGet(c, fn7464, std::move(args7465)); }()), false); return Call(c, fn7462, std::move(args7463)); }()); Value v7461; v7461 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v7460, v7461))) return Value(false); v7460 = v7461; return Value(true); }()))) {
for (const auto& item7466 : Iterate(s->Global("_V233_REPORT"))) {
s->SetAt(1, item7466);
auto v7467 = Value(int64_t{0});
Put(s->Global("_V233_REPORT"), s->LocalAt(1), v7467);
}
}
auto v7468 = ([&]() -> Value { auto fn7469 = s->Global("_R46_SHEEP_AGENT"); Arguments args7470; args7470.positional.reserve(2); args7470.Add(s->LocalAt(2), false); args7470.Add(s->LocalAt(0), false); return Call(c, fn7469, std::move(args7470)); }());
s->SetAt(3, v7468);
} catch (const Error& error7459) {
if (Matches(error7459, s->Global("Exception"))) {
auto v7471 = ([&]() -> Value { auto v7472 = ([&]() -> Value { auto fn7473 = PrepareDictionaryGet(s->Global("_R46_REPORT")); Arguments args7474; args7474.positional.reserve(2); args7474.Add(Value("sheep_overlay_errors"), false); args7474.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn7473, std::move(args7474)); }()); return Binary("Add", v7472, Value(int64_t{1})); }());
Put(s->Global("_R46_REPORT"), Value("sheep_overlay_errors"), v7471);
auto v7475 = ([&]() -> Value { auto dict7476 = Dict(); auto key7477 = Value("farmer"); Put(dict7476, key7477, List({Value("PASS")})); auto key7478 = Value("hands"); Put(dict7476, key7478, List({})); auto key7479 = Value("market"); Put(dict7476, key7479, List({})); return dict7476; }());
s->SetAt(3, v7475);
}
else { throw; }
}
(void)([&]() -> Value { auto fn7480 = Attribute(s->Global("_R46_REPORT"), "update"); Arguments args7481; args7481.Add(([&]() -> Value { auto fn7482 = s->Global("getattr"); Arguments args7483; args7483.positional.reserve(3); args7483.Add(s->Global("_V233_PARENT"), false); args7483.Add(Value("telemetry"), false); args7483.Add(([&]() -> Value { auto dict7484 = Dict(); return dict7484; }()), false); return Call(c, fn7482, std::move(args7483)); }()), false); return Call(c, fn7480, std::move(args7481)); }());
(void)([&]() -> Value { auto fn7485 = Attribute(s->Global("_R46_REPORT"), "update"); Arguments args7486; args7486.Add(s->Global("_V233_REPORT"), false); return Call(c, fn7485, std::move(args7486)); }());
return s->LocalAt(3);
return {};
}
}  // namespace kagg::opponents::compiled
