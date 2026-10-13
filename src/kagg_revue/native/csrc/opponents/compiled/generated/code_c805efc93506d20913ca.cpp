// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_c805efc93506d20913ca(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"actor", "actual", "obs", "old", "player", "quantity", "request", "state", "step"};
s->PrepareSlots(s_names);
auto v9119 = ([&]() -> Value { auto fn9120 = s->Global("int"); Arguments args9121; args9121.Add(Get(s->LocalAt(2), Value("player")), false); return Call(c, fn9120, std::move(args9121)); }());
s->SetAt(4, v9119);
auto v9122 = ([&]() -> Value { auto fn9123 = s->Global("int"); Arguments args9124; args9124.Add(Get(s->LocalAt(2), Value("step")), false); return Call(c, fn9123, std::move(args9124)); }());
s->SetAt(8, v9122);
auto v9125 = ([&]() -> Value { auto fn9126 = PrepareDictionaryGet(s->Global("_R70_STATES")); Arguments args9127; args9127.Add(s->LocalAt(4), false); return CallDictionaryGet(c, fn9126, std::move(args9127)); }());
s->SetAt(7, v9125);
if (static_cast<bool>(([&]() -> Value { auto v9128 = ([&]() -> Value { auto v9129 = s->LocalAt(7); Value v9130; v9130 = Value{}; if (!static_cast<bool>(Binary("Is", v9129, v9130))) return Value(false); v9129 = v9130; return Value(true); }()); if (static_cast<bool>(v9128)) return v9128; v9128 = ([&]() -> Value { auto v9131 = s->LocalAt(8); Value v9132; v9132 = Get(s->LocalAt(7), Value("step")); if (!static_cast<bool>(Binary("LtE", v9131, v9132))) return Value(false); v9131 = v9132; return Value(true); }()); return v9128; }()))) {
auto v9133 = ([&]() -> Value { auto dict9134 = Dict(); auto key9135 = Value("step"); Put(dict9134, key9135, Unary("USub", Value(int64_t{1}))); auto key9136 = Value("pending"); Put(dict9134, key9136, List({})); auto key9137 = Value("roles"); Put(dict9134, key9137, ([&]() -> Value { auto fn9138 = s->Global("set"); Arguments args9139; return Call(c, fn9138, std::move(args9139)); }())); return dict9134; }());
s->SetAt(7, v9133);
Put(s->Global("_R70_STATES"), s->LocalAt(4), v9133);
(void)([&]() -> Value { auto fn9140 = Attribute(s->Global("_R70_REPORT"), "update"); Arguments args9141; args9141.Keyword("parent_input_guard_turns", Value(int64_t{0})); args9141.Keyword("parent_input_guard_extra_units", Value(int64_t{0})); args9141.Keyword("parent_input_requests", Value(int64_t{0})); args9141.Keyword("parent_input_confirmed", Value(int64_t{0})); args9141.Keyword("parent_input_shortfalls", Value(int64_t{0})); args9141.Keyword("parent_input_errors", Value(int64_t{0})); args9141.Keyword("parent_input_capacity_declines", Value(int64_t{0})); return Call(c, fn9140, std::move(args9141)); }());
}
auto v9142 = s->LocalAt(8);
Put(s->LocalAt(7), Value("step"), v9142);
for (const auto& item9143 : Iterate(Get(s->LocalAt(7), Value("pending")))) {
s->SetAt(6, item9143);
auto v9144 = s->LocalAt(6);
auto unpack9145 = Iterate(v9144);
ValidateUnpack(unpack9145, 3, false);
s->SetAt(0, unpack9145.at(0));
s->SetAt(5, unpack9145.at(1));
s->SetAt(3, unpack9145.at(2));
auto v9146 = ([&]() -> Value { auto fn9147 = s->Global("max"); Arguments args9148; args9148.positional.reserve(2); args9148.Add(Value(int64_t{0}), false); args9148.Add(([&]() -> Value { auto v9149 = ([&]() -> Value { auto fn9150 = s->Global("int"); Arguments args9151; args9151.Add(([&]() -> Value { auto fn9152 = PrepareDictionaryGet(Get(Get(Get(s->LocalAt(2), Value("private")), Value("inventories")), s->LocalAt(0))); Arguments args9153; args9153.positional.reserve(2); args9153.Add(Value("FERTILIZER"), false); args9153.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn9152, std::move(args9153)); }()), false); return Call(c, fn9150, std::move(args9151)); }()); return Binary("Sub", v9149, s->LocalAt(3)); }()), false); return Call(c, fn9147, std::move(args9148)); }());
s->SetAt(1, v9146);
auto v9154 = s->Global("_R70_REPORT");
auto v9155 = Value("parent_input_confirmed");
auto v9156 = Get(v9154, v9155);
Put(v9154, v9155, Inplace("Add", v9156, ([&]() -> Value { auto fn9157 = s->Global("min"); Arguments args9158; args9158.positional.reserve(2); args9158.Add(s->LocalAt(5), false); args9158.Add(s->LocalAt(1), false); return Call(c, fn9157, std::move(args9158)); }())));
auto v9159 = s->Global("_R70_REPORT");
auto v9160 = Value("parent_input_shortfalls");
auto v9161 = Get(v9159, v9160);
Put(v9159, v9160, Inplace("Add", v9161, ([&]() -> Value { auto fn9162 = s->Global("max"); Arguments args9163; args9163.positional.reserve(2); args9163.Add(Value(int64_t{0}), false); args9163.Add(([&]() -> Value { auto v9164 = s->LocalAt(5); return Binary("Sub", v9164, s->LocalAt(1)); }()), false); return Call(c, fn9162, std::move(args9163)); }())));
}
auto v9165 = List({});
Put(s->LocalAt(7), Value("pending"), v9165);
return s->LocalAt(7);
return {};
}
}  // namespace kagg::opponents::compiled
