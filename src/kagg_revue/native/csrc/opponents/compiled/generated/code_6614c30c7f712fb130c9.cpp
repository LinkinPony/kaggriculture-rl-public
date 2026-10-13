// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_6614c30c7f712fb130c9(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"buys", "index", "item", "n", "op", "order", "orders", "q", "sales", "shed", "stock"};
s->PrepareSlots(s_names);
auto v10167 = ([&]() -> Value { auto fn10168 = s->Global("dict"); Arguments args10169; args10169.Add(s->LocalAt(9), false); return Call(c, fn10168, std::move(args10169)); }());
s->SetAt(10, v10167);
auto v10170 = ([&]() -> Value { auto dict10171 = Dict(); return dict10171; }());
s->SetAt(0, v10170);
auto v10172 = ([&]() -> Value { auto dict10173 = Dict(); return dict10173; }());
s->SetAt(8, v10172);
for (const auto& item10174 : Iterate(([&]() -> Value { auto fn10175 = s->Global("enumerate"); Arguments args10176; args10176.Add(s->LocalAt(6), false); return Call(c, fn10175, std::move(args10176)); }()))) {
auto unpack10177 = Iterate(item10174);
ValidateUnpack(unpack10177, 2, false);
s->SetAt(1, unpack10177.at(0));
s->SetAt(5, unpack10177.at(1));
if (static_cast<bool>(([&]() -> Value { auto v10178 = ([&]() -> Value { auto fn10180 = s->Global("len"); Arguments args10181; args10181.Add(s->LocalAt(5), false); return Call(c, fn10180, std::move(args10181)); }()); Value v10179; v10179 = Value(int64_t{3}); if (!static_cast<bool>(Binary("Lt", v10178, v10179))) return Value(false); v10178 = v10179; return Value(true); }()))) {
continue;
}
auto v10182 = Slice(s->LocalAt(5), Value{}, Value(int64_t{3}), Value{});
auto unpack10183 = Iterate(v10182);
ValidateUnpack(unpack10183, 3, false);
s->SetAt(4, unpack10183.at(0));
s->SetAt(2, unpack10183.at(1));
s->SetAt(3, unpack10183.at(2));
auto v10184 = ([&]() -> Value { auto fn10185 = s->Global("max"); Arguments args10186; args10186.positional.reserve(2); args10186.Add(Value(int64_t{0}), false); args10186.Add(([&]() -> Value { auto fn10187 = s->Global("int"); Arguments args10188; args10188.Add(s->LocalAt(3), false); return Call(c, fn10187, std::move(args10188)); }()), false); return Call(c, fn10185, std::move(args10186)); }());
s->SetAt(3, v10184);
if (static_cast<bool>(([&]() -> Value { auto v10189 = s->LocalAt(4); Value v10190; v10190 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v10189, v10190))) return Value(false); v10189 = v10190; return Value(true); }()))) {
auto v10191 = ([&]() -> Value { auto fn10192 = s->Global("min"); Arguments args10193; args10193.positional.reserve(2); args10193.Add(s->LocalAt(3), false); args10193.Add(([&]() -> Value { auto fn10194 = s->Global("max"); Arguments args10195; args10195.positional.reserve(2); args10195.Add(Value(int64_t{0}), false); args10195.Add(([&]() -> Value { auto fn10196 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args10197; args10197.positional.reserve(2); args10197.Add(s->LocalAt(2), false); args10197.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn10196, std::move(args10197)); }()), false); return Call(c, fn10194, std::move(args10195)); }()), false); return Call(c, fn10192, std::move(args10193)); }());
s->SetAt(7, v10191);
auto v10198 = ([&]() -> Value { auto v10199 = ([&]() -> Value { auto fn10200 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args10201; args10201.positional.reserve(2); args10201.Add(s->LocalAt(2), false); args10201.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn10200, std::move(args10201)); }()); return Binary("Sub", v10199, s->LocalAt(7)); }());
Put(s->LocalAt(10), s->LocalAt(2), v10198);
auto v10202 = s->LocalAt(7);
Put(s->LocalAt(8), s->LocalAt(1), v10202);
}
else {
if (static_cast<bool>(([&]() -> Value { auto v10203 = s->LocalAt(4); Value v10204; v10204 = Tuple({Value("BUY_PRODUCT"), Value("BUY_ANIMAL")}); if (!static_cast<bool>(Binary("In", v10203, v10204))) return Value(false); v10203 = v10204; return Value(true); }()))) {
auto v10205 = ([&]() -> Value { auto fn10206 = s->Global("min"); Arguments args10207; args10207.positional.reserve(2); args10207.Add(s->LocalAt(3), false); args10207.Add(([&]() -> Value { auto fn10208 = s->Global("max"); Arguments args10209; args10209.positional.reserve(2); args10209.Add(Value(int64_t{0}), false); args10209.Add(([&]() -> Value { auto v10210 = Value(int64_t{100}); return Binary("Sub", v10210, ([&]() -> Value { auto fn10211 = s->Global("sum"); Arguments args10212; args10212.Add(([&]() -> Value { auto fn10213 = Attribute(s->LocalAt(10), "values"); Arguments args10214; return Call(c, fn10213, std::move(args10214)); }()), false); return Call(c, fn10211, std::move(args10212)); }())); }()), false); return Call(c, fn10208, std::move(args10209)); }()), false); return Call(c, fn10206, std::move(args10207)); }());
s->SetAt(7, v10205);
auto v10215 = ([&]() -> Value { auto v10216 = ([&]() -> Value { auto fn10217 = PrepareDictionaryGet(s->LocalAt(10)); Arguments args10218; args10218.positional.reserve(2); args10218.Add(s->LocalAt(2), false); args10218.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn10217, std::move(args10218)); }()); return Binary("Add", v10216, s->LocalAt(7)); }());
Put(s->LocalAt(10), s->LocalAt(2), v10215);
auto v10219 = s->LocalAt(7);
Put(s->LocalAt(0), s->LocalAt(1), v10219);
}
}
}
return Tuple({s->LocalAt(10), s->LocalAt(0), s->LocalAt(8)});
return {};
}
}  // namespace kagg::opponents::compiled
