// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_d0180fe7f08270b83601(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"act", "days", "need", "seat", "step", "t", "units"};
s->PrepareSlots(s_names);
auto v21958 = Value(int64_t{0});
s->SetAt(2, v21958);
for (const auto& item21959 : Iterate(([&]() -> Value { auto fn21960 = s->Global("range"); Arguments args21961; args21961.positional.reserve(2); args21961.Add(s->LocalAt(4), false); args21961.Add(([&]() -> Value { auto v21962 = ([&]() -> Value { auto fn21963 = s->Global("min"); Arguments args21964; args21964.positional.reserve(2); args21964.Add(Value(int64_t{719}), false); args21964.Add(([&]() -> Value { auto v21965 = s->LocalAt(4); return Binary("Add", v21965, ([&]() -> Value { auto v21966 = Value(int64_t{24}); return Binary("Mult", v21966, s->LocalAt(1)); }())); }()), false); return Call(c, fn21963, std::move(args21964)); }()); return Binary("Add", v21962, Value(int64_t{1})); }()), false); return Call(c, fn21960, std::move(args21961)); }()))) {
s->SetAt(5, item21959);
auto v21967 = ([&]() -> Value { auto fn21968 = s->Global("_ca_tape"); Arguments args21969; args21969.positional.reserve(2); args21969.Add(s->LocalAt(3), false); args21969.Add(s->LocalAt(5), false); return Call(c, fn21968, std::move(args21969)); }());
s->SetAt(0, v21967);
auto v21970 = ([&]() -> Value { auto v21971 = List({([&]() -> Value { auto v21972 = ([&]() -> Value { auto fn21973 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args21974; args21974.Add(Value("farmer"), false); return CallDictionaryGet(c, fn21973, std::move(args21974)); }()); if (static_cast<bool>(v21972)) return v21972; v21972 = List({Value("PASS")}); return v21972; }())}); return Binary("Add", v21971, ([&]() -> Value { auto fn21975 = s->Global("list"); Arguments args21976; args21976.Add(([&]() -> Value { auto v21977 = ([&]() -> Value { auto fn21978 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args21979; args21979.Add(Value("hands"), false); return CallDictionaryGet(c, fn21978, std::move(args21979)); }()); if (static_cast<bool>(v21977)) return v21977; v21977 = List({}); return v21977; }()), false); return Call(c, fn21975, std::move(args21976)); }())); }());
s->SetAt(6, v21970);
auto v21980 = s->LocalAt(2);
s->SetAt(2, Inplace("Add", v21980, ([&]() -> Value { auto fn21981 = s->Global("sum"); Arguments args21982; args21982.Add(([&]() -> Value { auto comp21983 = std::make_shared<Scope>(); comp21983->globals = s->globals; comp21983->parent = s; static constexpr const char* comp21983_names[] = {"c"}; comp21983->PrepareSlots(comp21983_names); auto result21984 = List(); for (const auto& item21985 : Iterate(s->LocalAt(6))) { comp21983->SetAt(0, item21985); if (!static_cast<bool>(([&]() -> Value { auto v21986 = comp21983->LocalAt(0); if (!static_cast<bool>(v21986)) return v21986; v21986 = ([&]() -> Value { auto v21987 = Get(comp21983->LocalAt(0), Value(int64_t{0})); Value v21988; v21988 = Value("FEED"); if (!static_cast<bool>(Binary("Eq", v21987, v21988))) return Value(false); v21987 = v21988; return Value(true); }()); return v21986; }()))) continue; result21984.node()->sequence.push_back(Value(int64_t{1})); } return result21984; }()), false); return Call(c, fn21981, std::move(args21982)); }())));
}
return s->LocalAt(2);
return {};
}
}  // namespace kagg::opponents::compiled
