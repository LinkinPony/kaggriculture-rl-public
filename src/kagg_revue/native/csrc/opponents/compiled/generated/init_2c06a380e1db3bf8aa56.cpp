// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Init_2c06a380e1db3bf8aa56(Context& c, const ScopePtr& s) {
s->Set("base64", Builtin("base64"));
s->Set("json", Builtin("json"));
s->Set("zlib", Builtin("zlib"));
auto v14016 = c.constants.at(2);
s->Set("_DATA", v14016);
auto v14017 = Get(s->Global("_DATA"), Value("tapes"));
s->Set("_TAPES", v14017);
auto v14018 = ([&]() -> Value { auto comp14019 = std::make_shared<Scope>(); comp14019->globals = s->globals; comp14019->parent = s; static constexpr const char* comp14019_names[] = {"row"}; comp14019->PrepareSlots(comp14019_names); auto result14020 = Dict(); for (const auto& item14021 : Iterate(Get(s->Global("_DATA"), Value("routes")))) { comp14019->SetAt(0, item14021); Put(result14020, ([&]() -> Value { auto fn14022 = comp14019->Global("tuple"); Arguments args14023; args14023.Add(Get(comp14019->LocalAt(0), Value("shops")), false); return Call(c, fn14022, std::move(args14023)); }()), Get(comp14019->LocalAt(0), Value("plan"))); } return result14020; }());
s->Set("_ROUTES", v14018);
auto v14024 = ([&]() -> Value { auto dict14025 = Dict(); return dict14025; }());
s->Set("_STATE", v14024);
s->Set("agent", Define(&Code_8e02ebc71d0b56e5f637, s, Signature{{"observation", "configuration"}, {Value{}}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"configuration", "observation", "plan", "player", "previous", "shops", "step"}; return names; }())}, false, "agent"));
return {};
}
}  // namespace kagg::opponents::compiled
