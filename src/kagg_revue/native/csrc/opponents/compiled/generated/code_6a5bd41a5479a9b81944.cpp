// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_6a5bd41a5479a9b81944(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "actor", "command", "crop", "demand", "observation", "parent", "position", "tile", "view"};
s->PrepareSlots(s_names);
auto v15452 = ([&]() -> Value { auto fn15453 = s->Global("FarmView"); Arguments args15454; args15454.Add(s->LocalAt(5), false); return Call(c, fn15453, std::move(args15454)); }());
s->SetAt(9, v15452);
if (static_cast<bool>(([&]() -> Value { auto v15455 = s->LocalAt(1); Value v15456; v15456 = ([&]() -> Value { auto fn15457 = s->Global("len"); Arguments args15458; args15458.Add(Attribute(s->LocalAt(9), "positions"), false); return Call(c, fn15457, std::move(args15458)); }()); if (!static_cast<bool>(Binary("GtE", v15455, v15456))) return Value(false); v15455 = v15456; return Value(true); }()))) {
return Value(false);
}
auto v15459 = Get(Attribute(s->LocalAt(9), "positions"), s->LocalAt(1));
s->SetAt(7, v15459);
auto v15460 = ([&]() -> Value { auto fn15461 = s->Global("_tile_at"); Arguments args15462; args15462.positional.reserve(2); args15462.Add(Attribute(s->LocalAt(9), "tiles"), false); args15462.Add(s->LocalAt(7), false); return Call(c, fn15461, std::move(args15462)); }());
s->SetAt(8, v15460);
if (static_cast<bool>(([&]() -> Value { auto fn15463 = s->Global("_is_noop"); Arguments args15464; args15464.positional.reserve(6); args15464.Add(s->LocalAt(2), false); args15464.Add(s->LocalAt(8), false); args15464.Add(([&]() -> Value { auto fn15465 = Attribute(s->LocalAt(9), "inv"); Arguments args15466; args15466.Add(s->LocalAt(1), false); return Call(c, fn15465, std::move(args15466)); }()), false); args15464.Add(Attribute(s->LocalAt(9), "seeds"), false); args15464.Add(s->LocalAt(7), false); args15464.Add(Attribute(s->LocalAt(9), "board"), false); return Call(c, fn15463, std::move(args15464)); }()))) {
return Value(false);
}
if (static_cast<bool>(([&]() -> Value { auto v15467 = s->LocalAt(2); if (!static_cast<bool>(v15467)) return v15467; v15467 = ([&]() -> Value { auto v15468 = Get(s->LocalAt(2), Value(int64_t{0})); Value v15469; v15469 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v15468, v15469))) return Value(false); v15468 = v15469; return Value(true); }()); return v15467; }()))) {
auto v15470 = Get(s->LocalAt(2), Value(int64_t{1}));
s->SetAt(3, v15470);
auto v15471 = ([&]() -> Value { auto fn15472 = s->Global("sum"); Arguments args15473; args15473.Add(([&]() -> Value { auto comp15474 = std::make_shared<Scope>(); comp15474->globals = s->globals; comp15474->parent = s; static constexpr const char* comp15474_names[] = {"current"}; comp15474->PrepareSlots(comp15474_names); auto result15475 = List(); for (const auto& item15476 : Iterate(([&]() -> Value { auto fn15477 = s->Global("_r132_commands"); Arguments args15478; args15478.Add(s->LocalAt(0), false); return Call(c, fn15477, std::move(args15478)); }()))) { comp15474->SetAt(0, item15476); if (!static_cast<bool>(([&]() -> Value { auto v15479 = Slice(comp15474->LocalAt(0), Value{}, Value(int64_t{2}), Value{}); Value v15480; v15480 = List({Value("PLANT"), comp15474->Captured("crop")}); if (!static_cast<bool>(Binary("Eq", v15479, v15480))) return Value(false); v15479 = v15480; return Value(true); }()))) continue; result15475.node()->sequence.push_back(Value(int64_t{1})); } return result15475; }()), false); return Call(c, fn15472, std::move(args15473)); }());
s->SetAt(4, v15471);
auto v15481 = Get(([&]() -> Value { auto fn15482 = s->Global("_r132_commands"); Arguments args15483; args15483.Add(s->LocalAt(0), false); return Call(c, fn15482, std::move(args15483)); }()), s->LocalAt(1));
s->SetAt(6, v15481);
auto v15484 = s->LocalAt(4);
s->SetAt(4, Inplace("Add", v15484, ([&]() -> Value { auto fn15485 = s->Global("int"); Arguments args15486; args15486.Add(([&]() -> Value { auto v15487 = Slice(s->LocalAt(6), Value{}, Value(int64_t{2}), Value{}); Value v15488; v15488 = List({Value("PLANT"), s->LocalAt(3)}); if (!static_cast<bool>(Binary("NotEq", v15487, v15488))) return Value(false); v15487 = v15488; return Value(true); }()), false); return Call(c, fn15485, std::move(args15486)); }())));
if (static_cast<bool>(([&]() -> Value { auto v15489 = s->LocalAt(4); Value v15490; v15490 = ([&]() -> Value { auto fn15491 = s->Global("int"); Arguments args15492; args15492.Add(([&]() -> Value { auto fn15493 = PrepareDictionaryGet(Attribute(s->LocalAt(9), "seeds")); Arguments args15494; args15494.positional.reserve(2); args15494.Add(s->LocalAt(3), false); args15494.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn15493, std::move(args15494)); }()), false); return Call(c, fn15491, std::move(args15492)); }()); if (!static_cast<bool>(Binary("Gt", v15489, v15490))) return Value(false); v15489 = v15490; return Value(true); }()))) {
return Value(false);
}
}
return Value(true);
return {};
}
}  // namespace kagg::opponents::compiled
