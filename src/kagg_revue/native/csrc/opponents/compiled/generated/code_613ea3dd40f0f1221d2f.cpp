// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_613ea3dd40f0f1221d2f(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"inv", "item", "lost", "night", "private", "q", "stock", "take"};
s->PrepareSlots(s_names);
auto v10220 = ([&]() -> Value { auto fn10221 = s->Global("dict"); Arguments args10222; args10222.Add(s->LocalAt(6), false); return Call(c, fn10221, std::move(args10222)); }());
s->SetAt(6, v10220);
auto v10223 = ([&]() -> Value { auto dict10224 = Dict(); return dict10224; }());
s->SetAt(2, v10223);
if (static_cast<bool>(s->LocalAt(3))) {
for (const auto& item10225 : Iterate(Get(s->LocalAt(4), Value("inventories")))) {
s->SetAt(0, item10225);
for (const auto& item10226 : Iterate(([&]() -> Value { auto fn10227 = Attribute(s->LocalAt(0), "items"); Arguments args10228; return Call(c, fn10227, std::move(args10228)); }()))) {
auto unpack10229 = Iterate(item10226);
ValidateUnpack(unpack10229, 2, false);
s->SetAt(1, unpack10229.at(0));
s->SetAt(5, unpack10229.at(1));
auto v10230 = ([&]() -> Value { auto fn10231 = s->Global("max"); Arguments args10232; args10232.positional.reserve(2); args10232.Add(Value(int64_t{0}), false); args10232.Add(([&]() -> Value { auto fn10233 = s->Global("int"); Arguments args10234; args10234.Add(s->LocalAt(5), false); return Call(c, fn10233, std::move(args10234)); }()), false); return Call(c, fn10231, std::move(args10232)); }());
s->SetAt(5, v10230);
auto v10235 = ([&]() -> Value { auto fn10236 = s->Global("min"); Arguments args10237; args10237.positional.reserve(2); args10237.Add(s->LocalAt(5), false); args10237.Add(([&]() -> Value { auto fn10238 = s->Global("max"); Arguments args10239; args10239.positional.reserve(2); args10239.Add(Value(int64_t{0}), false); args10239.Add(([&]() -> Value { auto v10240 = Value(int64_t{100}); return Binary("Sub", v10240, ([&]() -> Value { auto fn10241 = s->Global("sum"); Arguments args10242; args10242.Add(([&]() -> Value { auto fn10243 = Attribute(s->LocalAt(6), "values"); Arguments args10244; return Call(c, fn10243, std::move(args10244)); }()), false); return Call(c, fn10241, std::move(args10242)); }())); }()), false); return Call(c, fn10238, std::move(args10239)); }()), false); return Call(c, fn10236, std::move(args10237)); }());
s->SetAt(7, v10235);
auto v10245 = ([&]() -> Value { auto v10246 = ([&]() -> Value { auto fn10247 = PrepareDictionaryGet(s->LocalAt(6)); Arguments args10248; args10248.positional.reserve(2); args10248.Add(s->LocalAt(1), false); args10248.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn10247, std::move(args10248)); }()); return Binary("Add", v10246, s->LocalAt(7)); }());
Put(s->LocalAt(6), s->LocalAt(1), v10245);
if (static_cast<bool>(([&]() -> Value { auto v10249 = s->LocalAt(5); Value v10250; v10250 = s->LocalAt(7); if (!static_cast<bool>(Binary("Gt", v10249, v10250))) return Value(false); v10249 = v10250; return Value(true); }()))) {
auto v10251 = ([&]() -> Value { auto v10252 = ([&]() -> Value { auto v10253 = ([&]() -> Value { auto fn10254 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args10255; args10255.positional.reserve(2); args10255.Add(s->LocalAt(1), false); args10255.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn10254, std::move(args10255)); }()); return Binary("Add", v10253, s->LocalAt(5)); }()); return Binary("Sub", v10252, s->LocalAt(7)); }());
Put(s->LocalAt(2), s->LocalAt(1), v10251);
}
}
}
}
return Tuple({s->LocalAt(6), s->LocalAt(2)});
return {};
}
}  // namespace kagg::opponents::compiled
