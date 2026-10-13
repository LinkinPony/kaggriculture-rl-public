// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_629214b05bb096429897(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"configuration", "count", "observation", "result"};
s->PrepareSlots(s_names);
try {
auto v6639 = ([&]() -> Value { auto fn6640 = s->Global("_RELEASE_PARENT"); Arguments args6641; args6641.positional.reserve(2); args6641.Add(s->LocalAt(2), false); args6641.Add(s->LocalAt(0), false); return Call(c, fn6640, std::move(args6641)); }());
s->SetAt(3, v6639);
} catch (const Error& error6638) {
if (Matches(error6638, s->Global("Exception"))) {
auto v6642 = s->Global("_RELEASE_ERRORS");
Put(s->globals, "_RELEASE_ERRORS", Inplace("Add", v6642, Value(int64_t{1})));
auto v6643 = Value(int64_t{0});
s->SetAt(1, v6643);
try {
auto v6645 = ([&]() -> Value { auto fn6646 = s->Global("min"); Arguments args6647; args6647.positional.reserve(2); args6647.Add(Value(int64_t{64}), false); args6647.Add(([&]() -> Value { auto fn6648 = s->Global("len"); Arguments args6649; args6649.Add(Get(Get(Get(s->LocalAt(2), Value("farms")), ([&]() -> Value { auto fn6650 = s->Global("int"); Arguments args6651; args6651.Add(Get(s->LocalAt(2), Value("player")), false); return Call(c, fn6650, std::move(args6651)); }())), Value("hands")), false); return Call(c, fn6648, std::move(args6649)); }()), false); return Call(c, fn6646, std::move(args6647)); }());
s->SetAt(1, v6645);
} catch (const Error& error6644) {
if (Matches(error6644, s->Global("Exception"))) {
}
else { throw; }
}
auto v6652 = ([&]() -> Value { auto dict6653 = Dict(); auto key6654 = Value("farmer"); Put(dict6653, key6654, List({Value("PASS")})); auto key6655 = Value("hands"); Put(dict6653, key6655, ([&]() -> Value { auto comp6656 = std::make_shared<Scope>(); comp6656->globals = s->globals; comp6656->parent = s; static constexpr const char* comp6656_names[] = {"_"}; comp6656->PrepareSlots(comp6656_names); auto result6657 = List(); for (const auto& item6658 : Iterate(([&]() -> Value { auto fn6659 = s->Global("range"); Arguments args6660; args6660.Add(s->LocalAt(1), false); return Call(c, fn6659, std::move(args6660)); }()))) { comp6656->SetAt(0, item6658); result6657.node()->sequence.push_back(List({Value("PASS")})); } return result6657; }())); auto key6661 = Value("market"); Put(dict6653, key6661, List({})); return dict6653; }());
s->SetAt(3, v6652);
}
else { throw; }
}
(void)([&]() -> Value { auto fn6662 = Attribute(s->Global("_RELEASE_REPORT"), "update"); Arguments args6663; args6663.Add(([&]() -> Value { auto fn6664 = s->Global("getattr"); Arguments args6665; args6665.positional.reserve(3); args6665.Add(s->Global("_RELEASE_PARENT"), false); args6665.Add(Value("telemetry"), false); args6665.Add(([&]() -> Value { auto dict6666 = Dict(); return dict6666; }()), false); return Call(c, fn6664, std::move(args6665)); }()), false); return Call(c, fn6662, std::move(args6663)); }());
auto v6667 = s->Global("_RELEASE_ERRORS");
Put(s->Global("_RELEASE_REPORT"), Value("release_errors"), v6667);
return s->LocalAt(3);
return {};
}
}  // namespace kagg::opponents::compiled
