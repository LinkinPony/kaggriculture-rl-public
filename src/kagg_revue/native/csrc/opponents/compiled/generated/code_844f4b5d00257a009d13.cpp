// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_844f4b5d00257a009d13(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"obs", "priv"};
s->PrepareSlots(s_names);
auto v21943 = Get(s->LocalAt(0), Value("private"));
s->SetAt(1, v21943);
return ([&]() -> Value { auto v21944 = ([&]() -> Value { auto fn21945 = s->Global("int"); Arguments args21946; args21946.Add(([&]() -> Value { auto fn21947 = PrepareDictionaryGet(Get(s->LocalAt(1), Value("shed"))); Arguments args21948; args21948.positional.reserve(2); args21948.Add(Value("WHEAT"), false); args21948.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn21947, std::move(args21948)); }()), false); return Call(c, fn21945, std::move(args21946)); }()); return Binary("Add", v21944, ([&]() -> Value { auto fn21949 = s->Global("sum"); Arguments args21950; args21950.Add(([&]() -> Value { auto comp21951 = std::make_shared<Scope>(); comp21951->globals = s->globals; comp21951->parent = s; static constexpr const char* comp21951_names[] = {"inv"}; comp21951->PrepareSlots(comp21951_names); auto result21952 = List(); for (const auto& item21953 : Iterate(Get(s->LocalAt(1), Value("inventories")))) { comp21951->SetAt(0, item21953); result21952.node()->sequence.push_back(([&]() -> Value { auto fn21954 = comp21951->Global("int"); Arguments args21955; args21955.Add(([&]() -> Value { auto fn21956 = PrepareDictionaryGet(comp21951->LocalAt(0)); Arguments args21957; args21957.positional.reserve(2); args21957.Add(Value("WHEAT"), false); args21957.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn21956, std::move(args21957)); }()), false); return Call(c, fn21954, std::move(args21955)); }())); } return result21952; }()), false); return Call(c, fn21949, std::move(args21950)); }())); }());
return {};
}
}  // namespace kagg::opponents::compiled
