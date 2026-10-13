// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_901d361625ccbf8c6886(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"b", "io", "item", "qty"};
s->PrepareSlots(s_names);
auto v23202 = Tuple({Get(Get(s->LocalAt(1), Value(int64_t{1})), Value(int64_t{1})), ([&]() -> Value { auto fn23203 = s->Global("min"); Arguments args23204; args23204.positional.reserve(2); args23204.Add(([&]() -> Value { auto fn23205 = s->Global("int"); Arguments args23206; args23206.Add(Get(Get(s->LocalAt(1), Value(int64_t{1})), Value(int64_t{2})), false); return Call(c, fn23205, std::move(args23206)); }()), false); args23204.Add(([&]() -> Value { auto fn23207 = s->Global("max"); Arguments args23208; args23208.positional.reserve(2); args23208.Add(Value(int64_t{0}), false); args23208.Add(([&]() -> Value { auto fn23209 = s->Global("int"); Arguments args23210; args23210.Add(([&]() -> Value { auto fn23211 = PrepareDictionaryGet(s->Captured("proj")); Arguments args23212; args23212.positional.reserve(2); args23212.Add(Get(Get(s->LocalAt(1), Value(int64_t{1})), Value(int64_t{1})), false); args23212.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn23211, std::move(args23212)); }()), false); return Call(c, fn23209, std::move(args23210)); }()), false); return Call(c, fn23207, std::move(args23208)); }()), false); return Call(c, fn23203, std::move(args23204)); }())});
auto unpack23213 = Iterate(v23202);
ValidateUnpack(unpack23213, 2, false);
s->SetAt(2, unpack23213.at(0));
s->SetAt(3, unpack23213.at(1));
auto v23214 = ([&]() -> Value { auto fn23215 = s->Global("min"); Arguments args23216; args23216.positional.reserve(2); args23216.Add(s->Global("_OR2_CAP"), false); args23216.Add(([&]() -> Value { auto fn23217 = s->Global("int"); Arguments args23218; args23218.Add(([&]() -> Value { auto fn23219 = PrepareDictionaryGet(Get(s->Captured("st"), Value("stock"))); Arguments args23220; args23220.positional.reserve(2); args23220.Add(s->LocalAt(2), false); args23220.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn23219, std::move(args23220)); }()), false); return Call(c, fn23217, std::move(args23218)); }()), false); return Call(c, fn23215, std::move(args23216)); }());
s->SetAt(0, v23214);
return Tuple({Unary("USub", ([&]() -> Value { auto fn23221 = s->Global("_or2_exposure"); Arguments args23222; args23222.positional.reserve(4); args23222.Add(s->Captured("observation"), false); args23222.Add(s->LocalAt(2), false); args23222.Add(s->LocalAt(3), false); args23222.Add(s->LocalAt(0), false); return Call(c, fn23221, std::move(args23222)); }())), Unary("USub", ([&]() -> Value { auto fn23223 = s->Global("_r37_quote_priority"); Arguments args23224; args23224.positional.reserve(3); args23224.Add(s->Captured("observation"), false); args23224.Add(Get(s->LocalAt(1), Value(int64_t{1})), false); args23224.Add(s->Captured("proj"), false); return Call(c, fn23223, std::move(args23224)); }())), Get(s->LocalAt(1), Value(int64_t{0}))});
return {};
}
}  // namespace kagg::opponents::compiled
