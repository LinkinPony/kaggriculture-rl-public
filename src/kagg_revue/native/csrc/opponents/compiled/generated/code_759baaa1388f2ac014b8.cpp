// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_759baaa1388f2ac014b8(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"act", "adjacent", "animal", "board", "dx", "dy", "inv", "is_dict", "item", "kind", "op", "pos", "seeds", "tile", "x", "y"};
s->PrepareSlots(s_names);
if (static_cast<bool>(Unary("Not", s->LocalAt(0)))) {
return Value(true);
}
auto v114 = Get(s->LocalAt(0), Value(int64_t{0}));
s->SetAt(10, v114);
auto v115 = Tuple({Get(s->LocalAt(11), Value(int64_t{0})), Get(s->LocalAt(11), Value(int64_t{1}))});
auto unpack116 = Iterate(v115);
ValidateUnpack(unpack116, 2, false);
s->SetAt(14, unpack116.at(0));
s->SetAt(15, unpack116.at(1));
if (static_cast<bool>(([&]() -> Value { auto v117 = s->LocalAt(10); Value v118; v118 = s->Global("MOVES"); if (!static_cast<bool>(Binary("In", v117, v118))) return Value(false); v117 = v118; return Value(true); }()))) {
auto v119 = Get(s->Global("MOVES"), s->LocalAt(10));
auto unpack120 = Iterate(v119);
ValidateUnpack(unpack120, 2, false);
s->SetAt(4, unpack120.at(0));
s->SetAt(5, unpack120.at(1));
return Unary("Not", ([&]() -> Value { auto v121 = ([&]() -> Value { auto v122 = Value(int64_t{0}); Value v123; v123 = ([&]() -> Value { auto v124 = s->LocalAt(14); return Binary("Add", v124, s->LocalAt(4)); }()); if (!static_cast<bool>(Binary("LtE", v122, v123))) return Value(false); v122 = v123; v123 = s->LocalAt(3); if (!static_cast<bool>(Binary("Lt", v122, v123))) return Value(false); v122 = v123; return Value(true); }()); if (!static_cast<bool>(v121)) return v121; v121 = ([&]() -> Value { auto v125 = Value(int64_t{0}); Value v126; v126 = ([&]() -> Value { auto v127 = s->LocalAt(15); return Binary("Add", v127, s->LocalAt(5)); }()); if (!static_cast<bool>(Binary("LtE", v125, v126))) return Value(false); v125 = v126; v126 = s->LocalAt(3); if (!static_cast<bool>(Binary("Lt", v125, v126))) return Value(false); v125 = v126; return Value(true); }()); return v121; }()));
}
if (static_cast<bool>(([&]() -> Value { auto v128 = s->LocalAt(10); Value v129; v129 = Value("PASS"); if (!static_cast<bool>(Binary("Eq", v128, v129))) return Value(false); v128 = v129; return Value(true); }()))) {
return Value(true);
}
auto v130 = ([&]() -> Value { auto fn131 = s->Global("_shed_adjacent"); Arguments args132; args132.positional.reserve(2); args132.Add(s->LocalAt(11), false); args132.Add(s->LocalAt(3), false); return Call(c, fn131, std::move(args132)); }());
s->SetAt(1, v130);
if (static_cast<bool>(([&]() -> Value { auto v133 = s->LocalAt(10); Value v134; v134 = Value("DROP"); if (!static_cast<bool>(Binary("Eq", v133, v134))) return Value(false); v133 = v134; return Value(true); }()))) {
return ([&]() -> Value { auto v135 = Unary("Not", s->LocalAt(1)); if (static_cast<bool>(v135)) return v135; v135 = Unary("Not", s->LocalAt(6)); return v135; }());
}
if (static_cast<bool>(([&]() -> Value { auto v136 = s->LocalAt(10); Value v137; v137 = Value("PICKUP"); if (!static_cast<bool>(Binary("Eq", v136, v137))) return Value(false); v136 = v137; return Value(true); }()))) {
return Unary("Not", s->LocalAt(1));
}
if (static_cast<bool>(([&]() -> Value { auto v138 = s->LocalAt(10); Value v139; v139 = Value("PLACE"); if (!static_cast<bool>(Binary("Eq", v138, v139))) return Value(false); v138 = v139; return Value(true); }()))) {
auto v140 = (static_cast<bool>(([&]() -> Value { auto v141 = ([&]() -> Value { auto fn143 = s->Global("len"); Arguments args144; args144.Add(s->LocalAt(0), false); return Call(c, fn143, std::move(args144)); }()); Value v142; v142 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v141, v142))) return Value(false); v141 = v142; return Value(true); }())) ? Get(s->LocalAt(0), Value(int64_t{1})) : Value{});
s->SetAt(8, v140);
if (static_cast<bool>(([&]() -> Value { auto v145 = ([&]() -> Value { auto v146 = s->LocalAt(8); Value v147; v147 = s->Global("ANIMAL_STRUCTURE"); if (!static_cast<bool>(Binary("In", v146, v147))) return Value(false); v146 = v147; return Value(true); }()); if (!static_cast<bool>(v145)) return v145; v145 = ([&]() -> Value { auto fn148 = s->Global("isinstance"); Arguments args149; args149.positional.reserve(2); args149.Add(s->LocalAt(13), false); args149.Add(s->Global("dict"), false); return Call(c, fn148, std::move(args149)); }()); if (!static_cast<bool>(v145)) return v145; v145 = ([&]() -> Value { auto v150 = ([&]() -> Value { auto fn152 = s->Global("_get"); Arguments args153; args153.positional.reserve(2); args153.Add(s->LocalAt(13), false); args153.Add(Value("kind"), false); return Call(c, fn152, std::move(args153)); }()); Value v151; v151 = Get(s->Global("ANIMAL_STRUCTURE"), s->LocalAt(8)); if (!static_cast<bool>(Binary("Eq", v150, v151))) return Value(false); v150 = v151; return Value(true); }()); if (!static_cast<bool>(v145)) return v145; v145 = ([&]() -> Value { auto v154 = ([&]() -> Value { auto fn156 = s->Global("_get"); Arguments args157; args157.positional.reserve(2); args157.Add(s->LocalAt(13), false); args157.Add(Value("animal"), false); return Call(c, fn156, std::move(args157)); }()); Value v155; v155 = Value{}; if (!static_cast<bool>(Binary("Is", v154, v155))) return Value(false); v154 = v155; return Value(true); }()); return v145; }()))) {
return ([&]() -> Value { auto v158 = ([&]() -> Value { auto fn160 = s->Global("_int"); Arguments args161; args161.Add(([&]() -> Value { auto fn162 = s->Global("_get"); Arguments args163; args163.positional.reserve(3); args163.Add(s->LocalAt(6), false); args163.Add(s->LocalAt(8), false); args163.Add(Value(int64_t{0}), false); return Call(c, fn162, std::move(args163)); }()), false); return Call(c, fn160, std::move(args161)); }()); Value v159; v159 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v158, v159))) return Value(false); v158 = v159; return Value(true); }());
}
return ([&]() -> Value { auto v164 = Unary("Not", s->LocalAt(1)); if (static_cast<bool>(v164)) return v164; v164 = ([&]() -> Value { auto v165 = ([&]() -> Value { auto fn167 = s->Global("_int"); Arguments args168; args168.Add(([&]() -> Value { auto fn169 = s->Global("_get"); Arguments args170; args170.positional.reserve(3); args170.Add(s->LocalAt(6), false); args170.Add(s->LocalAt(8), false); args170.Add(Value(int64_t{0}), false); return Call(c, fn169, std::move(args170)); }()), false); return Call(c, fn167, std::move(args168)); }()); Value v166; v166 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v165, v166))) return Value(false); v165 = v166; return Value(true); }()); return v164; }());
}
if (static_cast<bool>(([&]() -> Value { auto v171 = s->LocalAt(13); Value v172; v172 = Value("LOCKED"); if (!static_cast<bool>(Binary("Eq", v171, v172))) return Value(false); v171 = v172; return Value(true); }()))) {
return Value(true);
}
auto v173 = ([&]() -> Value { auto fn174 = s->Global("isinstance"); Arguments args175; args175.positional.reserve(2); args175.Add(s->LocalAt(13), false); args175.Add(s->Global("dict"), false); return Call(c, fn174, std::move(args175)); }());
s->SetAt(7, v173);
auto v176 = (static_cast<bool>(s->LocalAt(7)) ? ([&]() -> Value { auto fn177 = s->Global("_get"); Arguments args178; args178.positional.reserve(2); args178.Add(s->LocalAt(13), false); args178.Add(Value("kind"), false); return Call(c, fn177, std::move(args178)); }()) : Value{});
s->SetAt(9, v176);
auto v179 = ([&]() -> Value { auto v180 = s->LocalAt(7); if (!static_cast<bool>(v180)) return v180; v180 = ([&]() -> Value { auto v181 = ([&]() -> Value { auto fn183 = s->Global("_get"); Arguments args184; args184.positional.reserve(2); args184.Add(s->LocalAt(13), false); args184.Add(Value("animal"), false); return Call(c, fn183, std::move(args184)); }()); Value v182; v182 = Value{}; if (!static_cast<bool>(Binary("IsNot", v181, v182))) return Value(false); v181 = v182; return Value(true); }()); return v180; }());
s->SetAt(2, v179);
if (static_cast<bool>(([&]() -> Value { auto v185 = s->LocalAt(10); Value v186; v186 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v185, v186))) return Value(false); v185 = v186; return Value(true); }()))) {
return ([&]() -> Value { auto v187 = ([&]() -> Value { auto v188 = s->LocalAt(13); Value v189; v189 = Value{}; if (!static_cast<bool>(Binary("IsNot", v188, v189))) return Value(false); v188 = v189; return Value(true); }()); if (static_cast<bool>(v187)) return v187; v187 = ([&]() -> Value { auto v190 = ([&]() -> Value { auto fn192 = s->Global("_int"); Arguments args193; args193.Add(([&]() -> Value { auto fn194 = s->Global("_get"); Arguments args195; args195.positional.reserve(3); args195.Add(s->LocalAt(12), false); args195.Add((static_cast<bool>(([&]() -> Value { auto v196 = ([&]() -> Value { auto fn198 = s->Global("len"); Arguments args199; args199.Add(s->LocalAt(0), false); return Call(c, fn198, std::move(args199)); }()); Value v197; v197 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v196, v197))) return Value(false); v196 = v197; return Value(true); }())) ? Get(s->LocalAt(0), Value(int64_t{1})) : Value{}), false); args195.Add(Value(int64_t{0}), false); return Call(c, fn194, std::move(args195)); }()), false); return Call(c, fn192, std::move(args193)); }()); Value v191; v191 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v190, v191))) return Value(false); v190 = v191; return Value(true); }()); return v187; }());
}
if (static_cast<bool>(([&]() -> Value { auto v200 = s->LocalAt(10); Value v201; v201 = Value("WATER"); if (!static_cast<bool>(Binary("Eq", v200, v201))) return Value(false); v200 = v201; return Value(true); }()))) {
return ([&]() -> Value { auto v202 = ([&]() -> Value { auto v203 = s->LocalAt(9); Value v204; v204 = Value("PLANT"); if (!static_cast<bool>(Binary("NotEq", v203, v204))) return Value(false); v203 = v204; return Value(true); }()); if (static_cast<bool>(v202)) return v202; v202 = ([&]() -> Value { auto fn205 = s->Global("bool"); Arguments args206; args206.Add(([&]() -> Value { auto fn207 = s->Global("_get"); Arguments args208; args208.positional.reserve(2); args208.Add(s->LocalAt(13), false); args208.Add(Value("watered_today"), false); return Call(c, fn207, std::move(args208)); }()), false); return Call(c, fn205, std::move(args206)); }()); return v202; }());
}
if (static_cast<bool>(([&]() -> Value { auto v209 = s->LocalAt(10); Value v210; v210 = Value("HARVEST"); if (!static_cast<bool>(Binary("Eq", v209, v210))) return Value(false); v209 = v210; return Value(true); }()))) {
return ([&]() -> Value { auto v211 = Unary("Not", s->LocalAt(7)); if (static_cast<bool>(v211)) return v211; v211 = ([&]() -> Value { auto v212 = ([&]() -> Value { auto fn214 = s->Global("_int"); Arguments args215; args215.Add(([&]() -> Value { auto fn216 = s->Global("_get"); Arguments args217; args217.positional.reserve(3); args217.Add(s->LocalAt(13), false); args217.Add(Value("yield_units"), false); args217.Add(Value(int64_t{0}), false); return Call(c, fn216, std::move(args217)); }()), false); return Call(c, fn214, std::move(args215)); }()); Value v213; v213 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v212, v213))) return Value(false); v212 = v213; return Value(true); }()); return v211; }());
}
if (static_cast<bool>(([&]() -> Value { auto v218 = s->LocalAt(10); Value v219; v219 = Value("FERTILIZE"); if (!static_cast<bool>(Binary("Eq", v218, v219))) return Value(false); v218 = v219; return Value(true); }()))) {
return ([&]() -> Value { auto v220 = ([&]() -> Value { auto v221 = s->LocalAt(9); Value v222; v222 = Value("PLANT"); if (!static_cast<bool>(Binary("NotEq", v221, v222))) return Value(false); v221 = v222; return Value(true); }()); if (static_cast<bool>(v220)) return v220; v220 = ([&]() -> Value { auto v223 = ([&]() -> Value { auto fn225 = s->Global("_int"); Arguments args226; args226.Add(([&]() -> Value { auto fn227 = s->Global("_get"); Arguments args228; args228.positional.reserve(3); args228.Add(s->LocalAt(6), false); args228.Add(Value("FERTILIZER"), false); args228.Add(Value(int64_t{0}), false); return Call(c, fn227, std::move(args228)); }()), false); return Call(c, fn225, std::move(args226)); }()); Value v224; v224 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v223, v224))) return Value(false); v223 = v224; return Value(true); }()); return v220; }());
}
if (static_cast<bool>(([&]() -> Value { auto v229 = s->LocalAt(10); Value v230; v230 = Value("DIG"); if (!static_cast<bool>(Binary("Eq", v229, v230))) return Value(false); v229 = v230; return Value(true); }()))) {
return ([&]() -> Value { auto v231 = ([&]() -> Value { auto v232 = s->LocalAt(13); Value v233; v233 = Value{}; if (!static_cast<bool>(Binary("Is", v232, v233))) return Value(false); v232 = v233; return Value(true); }()); if (static_cast<bool>(v231)) return v231; v231 = s->LocalAt(2); return v231; }());
}
if (static_cast<bool>(([&]() -> Value { auto v234 = s->LocalAt(10); Value v235; v235 = Tuple({Value("BUILD_COOP"), Value("BUILD_PASTURE")}); if (!static_cast<bool>(Binary("In", v234, v235))) return Value(false); v234 = v235; return Value(true); }()))) {
return ([&]() -> Value { auto v236 = s->LocalAt(13); Value v237; v237 = Value{}; if (!static_cast<bool>(Binary("IsNot", v236, v237))) return Value(false); v236 = v237; return Value(true); }());
}
if (static_cast<bool>(([&]() -> Value { auto v238 = s->LocalAt(10); Value v239; v239 = Value("FEED"); if (!static_cast<bool>(Binary("Eq", v238, v239))) return Value(false); v238 = v239; return Value(true); }()))) {
return ([&]() -> Value { auto v240 = Unary("Not", s->LocalAt(2)); if (static_cast<bool>(v240)) return v240; v240 = ([&]() -> Value { auto fn241 = s->Global("bool"); Arguments args242; args242.Add(([&]() -> Value { auto fn243 = s->Global("_get"); Arguments args244; args244.positional.reserve(2); args244.Add(s->LocalAt(13), false); args244.Add(Value("fed_today"), false); return Call(c, fn243, std::move(args244)); }()), false); return Call(c, fn241, std::move(args242)); }()); if (static_cast<bool>(v240)) return v240; v240 = ([&]() -> Value { auto v245 = ([&]() -> Value { auto fn247 = s->Global("_int"); Arguments args248; args248.Add(([&]() -> Value { auto fn249 = s->Global("_get"); Arguments args250; args250.positional.reserve(3); args250.Add(s->LocalAt(6), false); args250.Add(Value("WHEAT"), false); args250.Add(Value(int64_t{0}), false); return Call(c, fn249, std::move(args250)); }()), false); return Call(c, fn247, std::move(args248)); }()); Value v246; v246 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v245, v246))) return Value(false); v245 = v246; return Value(true); }()); return v240; }());
}
if (static_cast<bool>(([&]() -> Value { auto v251 = s->LocalAt(10); Value v252; v252 = Value("COLLECT_FERTILIZER"); if (!static_cast<bool>(Binary("Eq", v251, v252))) return Value(false); v251 = v252; return Value(true); }()))) {
return ([&]() -> Value { auto v253 = Unary("Not", s->LocalAt(2)); if (static_cast<bool>(v253)) return v253; v253 = Unary("Not", ([&]() -> Value { auto fn254 = s->Global("_get"); Arguments args255; args255.positional.reserve(2); args255.Add(s->LocalAt(13), false); args255.Add(Value("fertilizer_available"), false); return Call(c, fn254, std::move(args255)); }())); return v253; }());
}
if (static_cast<bool>(([&]() -> Value { auto v256 = s->LocalAt(10); Value v257; v257 = Value("CARE"); if (!static_cast<bool>(Binary("Eq", v256, v257))) return Value(false); v256 = v257; return Value(true); }()))) {
return ([&]() -> Value { auto v258 = Unary("Not", s->LocalAt(2)); if (static_cast<bool>(v258)) return v258; v258 = ([&]() -> Value { auto fn259 = s->Global("bool"); Arguments args260; args260.Add(([&]() -> Value { auto fn261 = s->Global("_get"); Arguments args262; args262.positional.reserve(2); args262.Add(s->LocalAt(13), false); args262.Add(Value("cared_today"), false); return Call(c, fn261, std::move(args262)); }()), false); return Call(c, fn259, std::move(args260)); }()); return v258; }());
}
return Value(true);
return {};
}
}  // namespace kagg::opponents::compiled
