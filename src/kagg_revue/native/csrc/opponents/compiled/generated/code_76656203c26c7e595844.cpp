// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_76656203c26c7e595844(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"future", "t"};
s->PrepareSlots(s_names);
auto v18310 = Get(Get(Attribute(Attribute(s->Global("_IMPL"), "chassis"), "routes"), (static_cast<bool>(([&]() -> Value { auto v18311 = s->LocalAt(1); Value v18312; v18312 = Value(int64_t{648}); if (!static_cast<bool>(Binary("GtE", v18311, v18312))) return Value(false); v18311 = v18312; return Value(true); }())) ? Value(int64_t{2}) : Get(s->Captured("native"), Value("route")))), s->LocalAt(1));
s->SetAt(0, v18310);
return ([&]() -> Value { auto comp18313 = std::make_shared<Scope>(); comp18313->globals = s->globals; comp18313->parent = s; static constexpr const char* comp18313_names[] = {"o"}; comp18313->PrepareSlots(comp18313_names); auto result18314 = List(); for (const auto& item18315 : Iterate(([&]() -> Value { auto fn18316 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args18317; args18317.positional.reserve(2); args18317.Add(Value("market"), false); args18317.Add(List({}), false); return CallDictionaryGet(c, fn18316, std::move(args18317)); }()))) { comp18313->SetAt(0, item18315); if (static_cast<bool>(([&]() -> Value { auto v18318 = ([&]() -> Value { auto v18319 = ([&]() -> Value { auto fn18321 = comp18313->Global("len"); Arguments args18322; args18322.Add(comp18313->LocalAt(0), false); return Call(c, fn18321, std::move(args18322)); }()); Value v18320; v18320 = Value(int64_t{3}); if (!static_cast<bool>(Binary("GtE", v18319, v18320))) return Value(false); v18319 = v18320; return Value(true); }()); if (!static_cast<bool>(v18318)) return v18318; v18318 = ([&]() -> Value { auto v18323 = Get(comp18313->LocalAt(0), Value(int64_t{0})); Value v18324; v18324 = Value("SELL"); if (!static_cast<bool>(Binary("Eq", v18323, v18324))) return Value(false); v18323 = v18324; return Value(true); }()); if (!static_cast<bool>(v18318)) return v18318; v18318 = ([&]() -> Value { auto v18325 = Get(comp18313->LocalAt(0), Value(int64_t{1})); Value v18326; v18326 = comp18313->Captured("item"); if (!static_cast<bool>(Binary("Eq", v18325, v18326))) return Value(false); v18325 = v18326; return Value(true); }()); return v18318; }()))) return Value(true); } return Value(false); }());
return {};
}
}  // namespace kagg::opponents::compiled
