// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_9d4359dfd196e33efb84(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "actor", "command", "day", "desired", "inv", "key", "obs", "player", "quantity", "role", "state"};
s->PrepareSlots(s_names);
auto v9166 = ([&]() -> Value { auto fn9167 = s->Global("int"); Arguments args9168; args9168.Add(Get(s->LocalAt(7), Value("player")), false); return Call(c, fn9167, std::move(args9168)); }());
s->SetAt(8, v9166);
auto v9169 = ([&]() -> Value { auto v9170 = ([&]() -> Value { auto fn9171 = s->Global("int"); Arguments args9172; args9172.Add(Get(s->LocalAt(7), Value("step")), false); return Call(c, fn9171, std::move(args9172)); }()); return Binary("FloorDiv", v9170, Value(int64_t{24})); }());
s->SetAt(3, v9169);
for (const auto& item9173 : Iterate(([&]() -> Value { auto fn9174 = Attribute(([&]() -> Value { auto fn9176 = PrepareDictionaryGet(([&]() -> Value { auto fn9178 = PrepareDictionaryGet(s->Global("_V219_STATES")); Arguments args9179; args9179.positional.reserve(2); args9179.Add(s->LocalAt(8), false); args9179.Add(([&]() -> Value { auto dict9180 = Dict(); return dict9180; }()), false); return CallDictionaryGet(c, fn9178, std::move(args9179)); }())); Arguments args9177; args9177.positional.reserve(2); args9177.Add(Value("workers"), false); args9177.Add(([&]() -> Value { auto dict9181 = Dict(); return dict9181; }()), false); return CallDictionaryGet(c, fn9176, std::move(args9177)); }()), "items"); Arguments args9175; return Call(c, fn9174, std::move(args9175)); }()))) {
auto unpack9182 = Iterate(item9173);
ValidateUnpack(unpack9182, 2, false);
s->SetAt(1, unpack9182.at(0));
s->SetAt(10, unpack9182.at(1));
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn9183 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args9184; args9184.Add(Value("needs_fertilizer"), false); return CallDictionaryGet(c, fn9183, std::move(args9184)); }())))) {
continue;
}
auto v9185 = Tuple({s->LocalAt(3), s->LocalAt(1)});
s->SetAt(6, v9185);
auto v9186 = ([&]() -> Value { auto fn9187 = PrepareDictionaryGet(Get(Get(Get(s->LocalAt(7), Value("private")), Value("inventories")), s->LocalAt(1))); Arguments args9188; args9188.positional.reserve(2); args9188.Add(Value("FERTILIZER"), false); args9188.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn9187, std::move(args9188)); }());
s->SetAt(5, v9186);
if (static_cast<bool>(([&]() -> Value { auto v9189 = s->LocalAt(6); Value v9190; v9190 = Get(s->LocalAt(11), Value("roles")); if (!static_cast<bool>(Binary("NotIn", v9189, v9190))) return Value(false); v9189 = v9190; return Value(true); }()))) {
(void)([&]() -> Value { auto fn9191 = Attribute(Get(s->LocalAt(11), Value("roles")), "add"); Arguments args9192; args9192.Add(s->LocalAt(6), false); return Call(c, fn9191, std::move(args9192)); }());
auto v9193 = ([&]() -> Value { auto fn9194 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args9195; args9195.positional.reserve(2); args9195.Add(Value("fertilizer_quantity"), false); args9195.Add((static_cast<bool>(([&]() -> Value { auto v9196 = Get(s->LocalAt(10), Value("kind")); Value v9197; v9197 = Value("fertilizer"); if (!static_cast<bool>(Binary("Eq", v9196, v9197))) return Value(false); v9196 = v9197; return Value(true); }())) ? Value(int64_t{10}) : Value(int64_t{5})), false); return CallDictionaryGet(c, fn9194, std::move(args9195)); }());
s->SetAt(4, v9193);
if (static_cast<bool>(([&]() -> Value { auto v9198 = ([&]() -> Value { auto fn9199 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args9200; args9200.Add(Value("loaded"), false); return CallDictionaryGet(c, fn9199, std::move(args9200)); }()); if (!static_cast<bool>(v9198)) return v9198; v9198 = Unary("Not", ([&]() -> Value { auto fn9201 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args9202; args9202.Add(Value("pickup_requested"), false); return CallDictionaryGet(c, fn9201, std::move(args9202)); }())); if (!static_cast<bool>(v9198)) return v9198; v9198 = ([&]() -> Value { auto v9203 = s->LocalAt(5); Value v9204; v9204 = s->LocalAt(4); if (!static_cast<bool>(Binary("Lt", v9203, v9204))) return Value(false); v9203 = v9204; return Value(true); }()); return v9198; }()))) {
auto v9205 = s->Global("_R70_REPORT");
auto v9206 = Value("parent_input_shortfalls");
auto v9207 = Get(v9205, v9206);
Put(v9205, v9206, Inplace("Add", v9207, ([&]() -> Value { auto v9208 = s->LocalAt(4); return Binary("Sub", v9208, s->LocalAt(5)); }())));
}
}
auto v9209 = (static_cast<bool>(([&]() -> Value { auto v9210 = s->LocalAt(1); Value v9211; v9211 = ([&]() -> Value { auto fn9212 = s->Global("len"); Arguments args9213; args9213.Add(([&]() -> Value { auto fn9214 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args9215; args9215.positional.reserve(2); args9215.Add(Value("hands"), false); args9215.Add(List({}), false); return CallDictionaryGet(c, fn9214, std::move(args9215)); }()), false); return Call(c, fn9212, std::move(args9213)); }()); if (!static_cast<bool>(Binary("LtE", v9210, v9211))) return Value(false); v9210 = v9211; return Value(true); }())) ? Get(([&]() -> Value { auto fn9216 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args9217; args9217.positional.reserve(2); args9217.Add(Value("hands"), false); args9217.Add(List({}), false); return CallDictionaryGet(c, fn9216, std::move(args9217)); }()), ([&]() -> Value { auto v9218 = s->LocalAt(1); return Binary("Sub", v9218, Value(int64_t{1})); }())) : List({Value("PASS")}));
s->SetAt(2, v9209);
if (static_cast<bool>(([&]() -> Value { auto v9219 = ([&]() -> Value { auto v9220 = ([&]() -> Value { auto fn9222 = s->Global("len"); Arguments args9223; args9223.Add(s->LocalAt(2), false); return Call(c, fn9222, std::move(args9223)); }()); Value v9221; v9221 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v9220, v9221))) return Value(false); v9220 = v9221; return Value(true); }()); if (!static_cast<bool>(v9219)) return v9219; v9219 = ([&]() -> Value { auto v9224 = Slice(s->LocalAt(2), Value{}, Value(int64_t{2}), Value{}); Value v9225; v9225 = List({Value("PICKUP"), Value("FERTILIZER")}); if (!static_cast<bool>(Binary("Eq", v9224, v9225))) return Value(false); v9224 = v9225; return Value(true); }()); return v9219; }()))) {
auto v9226 = ([&]() -> Value { auto fn9227 = s->Global("max"); Arguments args9228; args9228.positional.reserve(2); args9228.Add(Value(int64_t{0}), false); args9228.Add((static_cast<bool>(([&]() -> Value { auto v9229 = ([&]() -> Value { auto fn9231 = s->Global("len"); Arguments args9232; args9232.Add(s->LocalAt(2), false); return Call(c, fn9231, std::move(args9232)); }()); Value v9230; v9230 = Value(int64_t{2}); if (!static_cast<bool>(Binary("Gt", v9229, v9230))) return Value(false); v9229 = v9230; return Value(true); }())) ? ([&]() -> Value { auto fn9233 = s->Global("int"); Arguments args9234; args9234.Add(Get(s->LocalAt(2), Value(int64_t{2})), false); return Call(c, fn9233, std::move(args9234)); }()) : Value(int64_t{1})), false); return Call(c, fn9227, std::move(args9228)); }());
s->SetAt(9, v9226);
auto v9235 = s->Global("_R70_REPORT");
auto v9236 = Value("parent_input_requests");
auto v9237 = Get(v9235, v9236);
Put(v9235, v9236, Inplace("Add", v9237, s->LocalAt(9)));
(void)([&]() -> Value { auto fn9238 = Attribute(Get(s->LocalAt(11), Value("pending")), "append"); Arguments args9239; args9239.Add(Tuple({s->LocalAt(1), s->LocalAt(9), ([&]() -> Value { auto fn9240 = s->Global("int"); Arguments args9241; args9241.Add(s->LocalAt(5), false); return Call(c, fn9240, std::move(args9241)); }())}), false); return Call(c, fn9238, std::move(args9239)); }());
}
}
return {};
}
}  // namespace kagg::opponents::compiled
