// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_e64419397310cffaf9b3(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"money", "obs", "own", "player", "rival", "st", "step"};
s->PrepareSlots(s_names);
auto v6430 = ([&]() -> Value { auto fn6431 = s->Global("int"); Arguments args6432; args6432.Add(Get(s->LocalAt(1), Value("player")), false); return Call(c, fn6431, std::move(args6432)); }());
s->SetAt(3, v6430);
auto v6433 = ([&]() -> Value { auto fn6434 = s->Global("int"); Arguments args6435; args6435.Add(Get(s->LocalAt(1), Value("step")), false); return Call(c, fn6434, std::move(args6435)); }());
s->SetAt(6, v6433);
auto v6436 = ([&]() -> Value { auto fn6437 = PrepareDictionaryGet(s->Global("_R44_PROBES")); Arguments args6438; args6438.Add(s->LocalAt(3), false); return CallDictionaryGet(c, fn6437, std::move(args6438)); }());
s->SetAt(5, v6436);
if (static_cast<bool>(([&]() -> Value { auto v6439 = ([&]() -> Value { auto v6440 = s->LocalAt(5); Value v6441; v6441 = Value{}; if (!static_cast<bool>(Binary("Is", v6440, v6441))) return Value(false); v6440 = v6441; return Value(true); }()); if (static_cast<bool>(v6439)) return v6439; v6439 = ([&]() -> Value { auto v6442 = s->LocalAt(6); Value v6443; v6443 = Get(s->LocalAt(5), Value("step")); if (!static_cast<bool>(Binary("LtE", v6442, v6443))) return Value(false); v6442 = v6443; return Value(true); }()); return v6439; }()))) {
auto v6444 = ([&]() -> Value { auto dict6445 = Dict(); auto key6446 = Value("step"); Put(dict6445, key6446, Unary("USub", Value(int64_t{1}))); auto key6447 = Value("money"); Put(dict6445, key6447, Value{}); auto key6448 = Value("probe"); Put(dict6445, key6448, Value(int64_t{0})); auto key6449 = Value("matched"); Put(dict6445, key6449, Value(false)); return dict6445; }());
s->SetAt(5, v6444);
Put(s->Global("_R44_PROBES"), s->LocalAt(3), v6444);
}
if (static_cast<bool>(([&]() -> Value { auto v6450 = s->LocalAt(6); Value v6451; v6451 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v6450, v6451))) return Value(false); v6450 = v6451; return Value(true); }()))) {
(void)([&]() -> Value { auto fn6452 = Attribute(s->Global("_R44_REPORT"), "update"); Arguments args6453; args6453.Keyword("probe_matches", Value(int64_t{0})); args6453.Keyword("probe_four_turn_calls", Value(int64_t{0})); args6453.Keyword("probe_errors", Value(int64_t{0})); return Call(c, fn6452, std::move(args6453)); }());
}
auto v6454 = ([&]() -> Value { auto fn6455 = s->Global("tuple"); Arguments args6456; args6456.Add(([&]() -> Value { auto comp6457 = std::make_shared<Scope>(); comp6457->globals = s->globals; comp6457->parent = s; static constexpr const char* comp6457_names[] = {"i"}; comp6457->PrepareSlots(comp6457_names); auto result6458 = List(); for (const auto& item6459 : Iterate(Tuple({s->LocalAt(3), ([&]() -> Value { auto v6460 = Value(int64_t{1}); return Binary("Sub", v6460, s->LocalAt(3)); }())}))) { comp6457->SetAt(0, item6459); result6458.node()->sequence.push_back(([&]() -> Value { auto fn6461 = comp6457->Global("float"); Arguments args6462; args6462.Add(Get(Get(Get(comp6457->Captured("obs"), Value("farms")), comp6457->LocalAt(0)), Value("money")), false); return Call(c, fn6461, std::move(args6462)); }())); } return result6458; }()), false); return Call(c, fn6455, std::move(args6456)); }());
s->SetAt(0, v6454);
if (static_cast<bool>(([&]() -> Value { auto v6463 = ([&]() -> Value { auto v6464 = Get(s->LocalAt(5), Value("money")); Value v6465; v6465 = Value{}; if (!static_cast<bool>(Binary("IsNot", v6464, v6465))) return Value(false); v6464 = v6465; return Value(true); }()); if (!static_cast<bool>(v6463)) return v6463; v6463 = ([&]() -> Value { auto v6466 = Get(s->LocalAt(5), Value("probe")); Value v6467; v6467 = Value(int64_t{100}); if (!static_cast<bool>(Binary("GtE", v6466, v6467))) return Value(false); v6466 = v6467; return Value(true); }()); if (!static_cast<bool>(v6463)) return v6463; v6463 = ([&]() -> Value { auto v6468 = ([&]() -> Value { auto fn6470 = s->Global("_r37_similarity"); Arguments args6471; args6471.Add(s->LocalAt(1), false); return Call(c, fn6470, std::move(args6471)); }()); Value v6469; v6469 = Value(0.9); if (!static_cast<bool>(Binary("GtE", v6468, v6469))) return Value(false); v6468 = v6469; return Value(true); }()); return v6463; }()))) {
auto v6472 = ([&]() -> Value { auto v6473 = Get(s->LocalAt(0), Value(int64_t{0})); return Binary("Sub", v6473, Get(Get(s->LocalAt(5), Value("money")), Value(int64_t{0}))); }());
s->SetAt(2, v6472);
auto v6474 = ([&]() -> Value { auto v6475 = Get(s->LocalAt(0), Value(int64_t{1})); return Binary("Sub", v6475, Get(Get(s->LocalAt(5), Value("money")), Value(int64_t{1}))); }());
s->SetAt(4, v6474);
if (static_cast<bool>(([&]() -> Value { auto v6476 = ([&]() -> Value { auto v6477 = s->LocalAt(2); Value v6478; v6478 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v6477, v6478))) return Value(false); v6477 = v6478; return Value(true); }()); if (!static_cast<bool>(v6476)) return v6476; v6476 = ([&]() -> Value { auto v6479 = s->LocalAt(4); Value v6480; v6480 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v6479, v6480))) return Value(false); v6479 = v6480; return Value(true); }()); if (!static_cast<bool>(v6476)) return v6476; v6476 = ([&]() -> Value { auto v6481 = ([&]() -> Value { auto fn6483 = s->Global("abs"); Arguments args6484; args6484.Add(([&]() -> Value { auto v6485 = s->LocalAt(2); return Binary("Sub", v6485, s->LocalAt(4)); }()), false); return Call(c, fn6483, std::move(args6484)); }()); Value v6482; v6482 = ([&]() -> Value { auto fn6486 = s->Global("max"); Arguments args6487; args6487.positional.reserve(2); args6487.Add(Value(5.0), false); args6487.Add(([&]() -> Value { auto v6488 = Value(0.05); return Binary("Mult", v6488, Get(s->LocalAt(5), Value("probe"))); }()), false); return Call(c, fn6486, std::move(args6487)); }()); if (!static_cast<bool>(Binary("LtE", v6481, v6482))) return Value(false); v6481 = v6482; return Value(true); }()); return v6476; }()))) {
if (static_cast<bool>(Unary("Not", Get(s->LocalAt(5), Value("matched"))))) {
auto v6489 = s->Global("_R44_REPORT");
auto v6490 = Value("probe_matches");
auto v6491 = Get(v6489, v6490);
Put(v6489, v6490, Inplace("Add", v6491, Value(int64_t{1})));
}
auto v6492 = Value(true);
Put(s->LocalAt(5), Value("matched"), v6492);
}
}
(void)([&]() -> Value { auto fn6493 = Attribute(s->LocalAt(5), "update"); Arguments args6494; args6494.Keyword("step", s->LocalAt(6)); args6494.Keyword("money", s->LocalAt(0)); args6494.Keyword("probe", Value(int64_t{0})); return Call(c, fn6493, std::move(args6494)); }());
return s->LocalAt(5);
return {};
}
}  // namespace kagg::opponents::compiled
