// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_3d5abc65629bdddc0f4e(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"k", "obs", "params", "patch"};
s->PrepareSlots(s_names);
auto v19185 = ([&]() -> Value { auto comp19186 = std::make_shared<Scope>(); comp19186->globals = s->globals; comp19186->parent = s; static constexpr const char* comp19186_names[] = {"k", "v"}; comp19186->PrepareSlots(comp19186_names); auto result19187 = Dict(); for (const auto& item19188 : Iterate(([&]() -> Value { auto fn19189 = Attribute(s->Global("_R37_MARKET_PARAMS"), "items"); Arguments args19190; return Call(c, fn19189, std::move(args19190)); }()))) { auto unpack19191 = Iterate(item19188); ValidateUnpack(unpack19191, 2, false); comp19186->SetAt(0, unpack19191.at(0)); comp19186->SetAt(1, unpack19191.at(1)); Put(result19187, comp19186->LocalAt(0), ([&]() -> Value { auto fn19192 = comp19186->Global("dict"); Arguments args19193; args19193.Add(comp19186->LocalAt(1), false); return Call(c, fn19192, std::move(args19193)); }())); } return result19187; }());
s->SetAt(2, v19185);
for (const auto& item19194 : Iterate(([&]() -> Value { auto fn19195 = Attribute(([&]() -> Value { auto v19197 = ([&]() -> Value { auto fn19198 = PrepareDictionaryGet(Get(s->LocalAt(1), Value("market"))); Arguments args19199; args19199.Add(Value("params"), false); return CallDictionaryGet(c, fn19198, std::move(args19199)); }()); if (static_cast<bool>(v19197)) return v19197; v19197 = ([&]() -> Value { auto dict19200 = Dict(); return dict19200; }()); return v19197; }()), "items"); Arguments args19196; return Call(c, fn19195, std::move(args19196)); }()))) {
auto unpack19201 = Iterate(item19194);
ValidateUnpack(unpack19201, 2, false);
s->SetAt(0, unpack19201.at(0));
s->SetAt(3, unpack19201.at(1));
if (static_cast<bool>(([&]() -> Value { auto v19202 = ([&]() -> Value { auto v19203 = s->LocalAt(0); Value v19204; v19204 = s->LocalAt(2); if (!static_cast<bool>(Binary("In", v19203, v19204))) return Value(false); v19203 = v19204; return Value(true); }()); if (!static_cast<bool>(v19202)) return v19202; v19202 = ([&]() -> Value { auto fn19205 = s->Global("isinstance"); Arguments args19206; args19206.positional.reserve(2); args19206.Add(s->LocalAt(3), false); args19206.Add(s->Global("dict"), false); return Call(c, fn19205, std::move(args19206)); }()); return v19202; }()))) {
(void)([&]() -> Value { auto fn19207 = Attribute(Get(s->LocalAt(2), s->LocalAt(0)), "update"); Arguments args19208; args19208.Add(s->LocalAt(3), false); return Call(c, fn19207, std::move(args19208)); }());
}
}
return s->LocalAt(2);
return {};
}
}  // namespace kagg::opponents::compiled
