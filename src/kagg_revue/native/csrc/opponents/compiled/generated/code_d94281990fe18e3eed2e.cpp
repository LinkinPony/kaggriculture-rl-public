// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_d94281990fe18e3eed2e(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "actor", "carrying", "changed", "command", "commands", "depot", "farm", "free", "inventory", "observation", "placed", "player", "positions", "private", "quantity", "result", "state", "step", "take", "tile", "x", "y"};
s->PrepareSlots(s_names);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn16173 = PrepareDictionaryGet(s->LocalAt(17)); Arguments args16174; args16174.Add(Value("confirmed"), false); return CallDictionaryGet(c, fn16173, std::move(args16174)); }())))) {
return s->LocalAt(0);
}
auto v16175 = ([&]() -> Value { auto fn16176 = s->Global("int"); Arguments args16177; args16177.Add(Get(s->LocalAt(10), Value("step")), false); return Call(c, fn16176, std::move(args16177)); }());
s->SetAt(18, v16175);
auto v16178 = ([&]() -> Value { auto fn16179 = s->Global("int"); Arguments args16180; args16180.Add(Get(s->LocalAt(10), Value("player")), false); return Call(c, fn16179, std::move(args16180)); }());
s->SetAt(12, v16178);
auto v16181 = Get(Get(s->LocalAt(10), Value("farms")), s->LocalAt(12));
s->SetAt(7, v16181);
auto v16182 = Get(s->LocalAt(10), Value("private"));
s->SetAt(14, v16182);
auto v16183 = ([&]() -> Value { Arguments args16184; args16184.Add(Get(s->LocalAt(7), Value("farmer")), false); args16184.Add(Get(s->LocalAt(7), Value("hands")), true); return List(std::move(args16184.positional)); }());
s->SetAt(13, v16183);
auto v16185 = ([&]() -> Value { auto fn16186 = s->Global("_r132_commands"); Arguments args16187; args16187.Add(s->LocalAt(0), false); return Call(c, fn16186, std::move(args16187)); }());
s->SetAt(5, v16185);
auto v16188 = ([&]() -> Value { auto fn16189 = s->Global("max"); Arguments args16190; args16190.positional.reserve(2); args16190.Add(Value(int64_t{0}), false); args16190.Add(([&]() -> Value { auto v16191 = ([&]() -> Value { auto fn16192 = s->Global("_r134_animals"); Arguments args16193; args16193.positional.reserve(2); args16193.Add(s->LocalAt(7), false); args16193.Add(Value("GOOSE"), false); return Call(c, fn16192, std::move(args16193)); }()); return Binary("Sub", v16191, Get(s->LocalAt(17), Value("initial_geese"))); }()), false); return Call(c, fn16189, std::move(args16190)); }());
s->SetAt(11, v16188);
if (static_cast<bool>(([&]() -> Value { auto v16194 = s->LocalAt(11); Value v16195; v16195 = Get(s->LocalAt(17), Value("quota")); if (!static_cast<bool>(Binary("GtE", v16194, v16195))) return Value(false); v16194 = v16195; return Value(true); }()))) {
auto v16196 = Value(false);
Put(s->LocalAt(17), Value("confirmed"), v16196);
auto v16197 = s->Global("_R134_REPORT");
auto v16198 = Value("egg_substitution_completed");
auto v16199 = Get(v16197, v16198);
Put(v16197, v16198, Inplace("Add", v16199, Value(int64_t{1})));
return s->LocalAt(0);
}
auto v16200 = ([&]() -> Value { auto fn16201 = s->Global("sum"); Arguments args16202; args16202.Add(([&]() -> Value { auto comp16203 = std::make_shared<Scope>(); comp16203->globals = s->globals; comp16203->parent = s; static constexpr const char* comp16203_names[] = {"inventory"}; comp16203->PrepareSlots(comp16203_names); auto result16204 = List(); for (const auto& item16205 : Iterate(Get(s->LocalAt(14), Value("inventories")))) { comp16203->SetAt(0, item16205); result16204.node()->sequence.push_back(([&]() -> Value { auto fn16206 = comp16203->Global("int"); Arguments args16207; args16207.Add(([&]() -> Value { auto fn16208 = PrepareDictionaryGet(comp16203->LocalAt(0)); Arguments args16209; args16209.positional.reserve(2); args16209.Add(Value("GOOSE"), false); args16209.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn16208, std::move(args16209)); }()), false); return Call(c, fn16206, std::move(args16207)); }())); } return result16204; }()), false); return Call(c, fn16201, std::move(args16202)); }());
s->SetAt(2, v16200);
auto v16210 = ([&]() -> Value { auto fn16211 = s->Global("max"); Arguments args16212; args16212.positional.reserve(2); args16212.Add(Value(int64_t{0}), false); args16212.Add(([&]() -> Value { auto v16213 = ([&]() -> Value { auto v16214 = Get(s->LocalAt(17), Value("quota")); return Binary("Sub", v16214, s->LocalAt(11)); }()); return Binary("Sub", v16213, s->LocalAt(2)); }()), false); return Call(c, fn16211, std::move(args16212)); }());
s->SetAt(8, v16210);
auto v16215 = ([&]() -> Value { auto fn16216 = s->Global("max"); Arguments args16217; args16217.positional.reserve(2); args16217.Add(Value(int64_t{0}), false); args16217.Add(([&]() -> Value { auto fn16218 = s->Global("int"); Arguments args16219; args16219.Add(([&]() -> Value { auto fn16220 = PrepareDictionaryGet(Get(s->LocalAt(14), Value("shed"))); Arguments args16221; args16221.positional.reserve(2); args16221.Add(Value("GOOSE"), false); args16221.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn16220, std::move(args16221)); }()), false); return Call(c, fn16218, std::move(args16219)); }()), false); return Call(c, fn16216, std::move(args16217)); }());
s->SetAt(6, v16215);
auto v16222 = Value(false);
s->SetAt(3, v16222);
for (const auto& item16223 : Iterate(([&]() -> Value { auto fn16224 = s->Global("enumerate"); Arguments args16225; args16225.Add(Slice(s->LocalAt(5), Value{}, ([&]() -> Value { auto fn16226 = s->Global("len"); Arguments args16227; args16227.Add(Get(s->LocalAt(14), Value("inventories")), false); return Call(c, fn16226, std::move(args16227)); }()), Value{}), false); return Call(c, fn16224, std::move(args16225)); }()))) {
auto unpack16228 = Iterate(item16223);
ValidateUnpack(unpack16228, 2, false);
s->SetAt(1, unpack16228.at(0));
s->SetAt(4, unpack16228.at(1));
auto v16229 = Get(Get(s->LocalAt(14), Value("inventories")), s->LocalAt(1));
s->SetAt(9, v16229);
auto v16230 = Get(s->LocalAt(13), s->LocalAt(1));
auto unpack16231 = Iterate(v16230);
ValidateUnpack(unpack16231, 2, false);
s->SetAt(21, unpack16231.at(0));
s->SetAt(22, unpack16231.at(1));
auto v16232 = Get(Get(Get(s->LocalAt(7), Value("tiles")), s->LocalAt(22)), s->LocalAt(21));
s->SetAt(20, v16232);
if (static_cast<bool>(([&]() -> Value { auto v16233 = ([&]() -> Value { auto v16234 = Slice(s->LocalAt(4), Value{}, Value(int64_t{2}), Value{}); Value v16235; v16235 = List({Value("PICKUP"), Value("COW")}); if (!static_cast<bool>(Binary("Eq", v16234, v16235))) return Value(false); v16234 = v16235; return Value(true); }()); if (!static_cast<bool>(v16233)) return v16233; v16233 = ([&]() -> Value { auto v16236 = s->LocalAt(8); Value v16237; v16237 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v16236, v16237))) return Value(false); v16236 = v16237; return Value(true); }()); if (!static_cast<bool>(v16233)) return v16233; v16233 = ([&]() -> Value { auto v16238 = s->LocalAt(6); Value v16239; v16239 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v16238, v16239))) return Value(false); v16238 = v16239; return Value(true); }()); return v16233; }()))) {
auto v16240 = ([&]() -> Value { auto fn16241 = s->Global("max"); Arguments args16242; args16242.positional.reserve(2); args16242.Add(Value(int64_t{0}), false); args16242.Add((static_cast<bool>(([&]() -> Value { auto v16243 = ([&]() -> Value { auto fn16245 = s->Global("len"); Arguments args16246; args16246.Add(s->LocalAt(4), false); return Call(c, fn16245, std::move(args16246)); }()); Value v16244; v16244 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Gt", v16243, v16244))) return Value(false); v16243 = v16244; return Value(true); }())) ? ([&]() -> Value { auto fn16247 = s->Global("int"); Arguments args16248; args16248.Add(Get(s->LocalAt(4), Value(int64_t{2})), false); return Call(c, fn16247, std::move(args16248)); }()) : Value(int64_t{1})), false); return Call(c, fn16241, std::move(args16242)); }());
s->SetAt(15, v16240);
auto v16249 = ([&]() -> Value { auto fn16250 = s->Global("min"); Arguments args16251; args16251.positional.reserve(3); args16251.Add(s->LocalAt(15), false); args16251.Add(s->LocalAt(8), false); args16251.Add(s->LocalAt(6), false); return Call(c, fn16250, std::move(args16251)); }());
s->SetAt(19, v16249);
if (static_cast<bool>(([&]() -> Value { auto v16252 = ([&]() -> Value { auto v16253 = s->LocalAt(19); Value v16254; v16254 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v16253, v16254))) return Value(false); v16253 = v16254; return Value(true); }()); if (!static_cast<bool>(v16252)) return v16252; v16252 = ([&]() -> Value { auto fn16255 = s->Global("_shed_adjacent"); Arguments args16256; args16256.positional.reserve(2); args16256.Add(Tuple({s->LocalAt(21), s->LocalAt(22)}), false); args16256.Add(Value(int64_t{10}), false); return Call(c, fn16255, std::move(args16256)); }()); return v16252; }()))) {
auto v16257 = List({Value("PICKUP"), Value("GOOSE"), s->LocalAt(19)});
Put(s->LocalAt(5), s->LocalAt(1), v16257);
auto v16258 = s->LocalAt(8);
s->SetAt(8, Inplace("Sub", v16258, s->LocalAt(19)));
auto v16259 = s->LocalAt(6);
s->SetAt(6, Inplace("Sub", v16259, s->LocalAt(19)));
auto v16260 = Value(true);
s->SetAt(3, v16260);
auto v16261 = s->Global("_R134_REPORT");
auto v16262 = Value("egg_substitution_pickups");
auto v16263 = Get(v16261, v16262);
Put(v16261, v16262, Inplace("Add", v16263, s->LocalAt(19)));
}
}
else {
if (static_cast<bool>(([&]() -> Value { auto v16264 = ([&]() -> Value { auto v16265 = s->LocalAt(4); Value v16266; v16266 = List({Value("BUILD_PASTURE")}); if (!static_cast<bool>(Binary("Eq", v16265, v16266))) return Value(false); v16265 = v16266; return Value(true); }()); if (!static_cast<bool>(v16264)) return v16264; v16264 = ([&]() -> Value { auto v16267 = ([&]() -> Value { auto fn16269 = s->Global("int"); Arguments args16270; args16270.Add(([&]() -> Value { auto fn16271 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args16272; args16272.positional.reserve(2); args16272.Add(Value("GOOSE"), false); args16272.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn16271, std::move(args16272)); }()), false); return Call(c, fn16269, std::move(args16270)); }()); Value v16268; v16268 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v16267, v16268))) return Value(false); v16267 = v16268; return Value(true); }()); return v16264; }()))) {
if (static_cast<bool>(([&]() -> Value { auto v16273 = s->LocalAt(20); Value v16274; v16274 = Value{}; if (!static_cast<bool>(Binary("Is", v16273, v16274))) return Value(false); v16273 = v16274; return Value(true); }()))) {
auto v16275 = List({Value("BUILD_COOP")});
Put(s->LocalAt(5), s->LocalAt(1), v16275);
auto v16276 = Value(true);
s->SetAt(3, v16276);
auto v16277 = s->Global("_R134_REPORT");
auto v16278 = Value("egg_substitution_coops");
auto v16279 = Get(v16277, v16278);
Put(v16277, v16278, Inplace("Add", v16279, Value(int64_t{1})));
}
}
else {
if (static_cast<bool>(([&]() -> Value { auto v16280 = ([&]() -> Value { auto v16281 = Slice(s->LocalAt(4), Value{}, Value(int64_t{2}), Value{}); Value v16282; v16282 = List({Value("PLACE"), Value("COW")}); if (!static_cast<bool>(Binary("Eq", v16281, v16282))) return Value(false); v16281 = v16282; return Value(true); }()); if (!static_cast<bool>(v16280)) return v16280; v16280 = ([&]() -> Value { auto v16283 = ([&]() -> Value { auto fn16285 = s->Global("int"); Arguments args16286; args16286.Add(([&]() -> Value { auto fn16287 = PrepareDictionaryGet(s->LocalAt(9)); Arguments args16288; args16288.positional.reserve(2); args16288.Add(Value("GOOSE"), false); args16288.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn16287, std::move(args16288)); }()), false); return Call(c, fn16285, std::move(args16286)); }()); Value v16284; v16284 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v16283, v16284))) return Value(false); v16283 = v16284; return Value(true); }()); return v16280; }()))) {
if (static_cast<bool>(([&]() -> Value { auto v16289 = ([&]() -> Value { auto fn16290 = s->Global("isinstance"); Arguments args16291; args16291.positional.reserve(2); args16291.Add(s->LocalAt(20), false); args16291.Add(s->Global("dict"), false); return Call(c, fn16290, std::move(args16291)); }()); if (!static_cast<bool>(v16289)) return v16289; v16289 = ([&]() -> Value { auto v16292 = ([&]() -> Value { auto fn16294 = PrepareDictionaryGet(s->LocalAt(20)); Arguments args16295; args16295.Add(Value("kind"), false); return CallDictionaryGet(c, fn16294, std::move(args16295)); }()); Value v16293; v16293 = Value("COOP"); if (!static_cast<bool>(Binary("Eq", v16292, v16293))) return Value(false); v16292 = v16293; return Value(true); }()); if (!static_cast<bool>(v16289)) return v16289; v16289 = ([&]() -> Value { auto v16296 = ([&]() -> Value { auto fn16298 = PrepareDictionaryGet(s->LocalAt(20)); Arguments args16299; args16299.Add(Value("animal"), false); return CallDictionaryGet(c, fn16298, std::move(args16299)); }()); Value v16297; v16297 = Value{}; if (!static_cast<bool>(Binary("Is", v16296, v16297))) return Value(false); v16296 = v16297; return Value(true); }()); return v16289; }()))) {
auto v16300 = List({Value("PLACE"), Value("GOOSE")});
Put(s->LocalAt(5), s->LocalAt(1), v16300);
auto v16301 = Value(true);
s->SetAt(3, v16301);
auto v16302 = s->Global("_R134_REPORT");
auto v16303 = Value("egg_substitution_placements");
auto v16304 = Get(v16302, v16303);
Put(v16302, v16303, Inplace("Add", v16304, Value(int64_t{1})));
}
}
}
}
}
if (static_cast<bool>(([&]() -> Value { auto v16305 = ([&]() -> Value { auto v16306 = s->LocalAt(18); Value v16307; v16307 = Value(int64_t{216}); if (!static_cast<bool>(Binary("Gt", v16306, v16307))) return Value(false); v16306 = v16307; return Value(true); }()); if (!static_cast<bool>(v16305)) return v16305; v16305 = ([&]() -> Value { auto v16308 = s->LocalAt(11); Value v16309; v16309 = Get(s->LocalAt(17), Value("quota")); if (!static_cast<bool>(Binary("Lt", v16308, v16309))) return Value(false); v16308 = v16309; return Value(true); }()); return v16305; }()))) {
auto v16310 = Value(false);
Put(s->LocalAt(17), Value("confirmed"), v16310);
auto v16311 = s->Global("_R134_REPORT");
auto v16312 = Value("egg_substitution_aborted");
auto v16313 = Get(v16311, v16312);
Put(v16311, v16312, Inplace("Add", v16313, Value(int64_t{1})));
}
if (static_cast<bool>(Unary("Not", s->LocalAt(3)))) {
return s->LocalAt(0);
}
auto v16314 = ([&]() -> Value { auto fn16315 = Attribute(s->Global("copy"), "deepcopy"); Arguments args16316; args16316.Add(s->LocalAt(0), false); return Call(c, fn16315, std::move(args16316)); }());
s->SetAt(16, v16314);
auto v16317 = Tuple({Get(s->LocalAt(5), Value(int64_t{0})), Slice(s->LocalAt(5), Value(int64_t{1}), Value{}, Value{})});
auto unpack16318 = Iterate(v16317);
ValidateUnpack(unpack16318, 2, false);
Put(s->LocalAt(16), Value("farmer"), unpack16318.at(0));
Put(s->LocalAt(16), Value("hands"), unpack16318.at(1));
return s->LocalAt(16);
return {};
}
}  // namespace kagg::opponents::compiled
