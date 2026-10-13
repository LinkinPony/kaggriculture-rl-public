// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_173a1fedb4ce851cc6c0(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"farms", "own", "player", "rival"};
s->PrepareSlots(s_names);
auto v12935 = Tuple({Get(s->LocalAt(0), s->LocalAt(2)), Get(s->LocalAt(0), ([&]() -> Value { auto v12936 = Value(int64_t{1}); return Binary("Sub", v12936, s->LocalAt(2)); }()))});
auto unpack12937 = Iterate(v12935);
ValidateUnpack(unpack12937, 2, false);
s->SetAt(1, unpack12937.at(0));
s->SetAt(3, unpack12937.at(1));
return ([&]() -> Value { auto v12938 = ([&]() -> Value { auto v12939 = ([&]() -> Value { auto fn12941 = s->Global("len"); Arguments args12942; args12942.Add(Get(s->LocalAt(1), Value("hands")), false); return Call(c, fn12941, std::move(args12942)); }()); Value v12940; v12940 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v12939, v12940))) return Value(false); v12939 = v12940; return Value(true); }()); if (!static_cast<bool>(v12938)) return v12938; v12938 = ([&]() -> Value { auto v12943 = Get(s->LocalAt(1), Value("hands")); Value v12944; v12944 = Get(s->LocalAt(3), Value("hands")); if (!static_cast<bool>(Binary("Eq", v12943, v12944))) return Value(false); v12943 = v12944; return Value(true); }()); if (!static_cast<bool>(v12938)) return v12938; v12938 = ([&]() -> Value { auto v12945 = Get(s->LocalAt(1), Value("farmer")); Value v12946; v12946 = Get(s->LocalAt(3), Value("farmer")); if (!static_cast<bool>(Binary("Eq", v12945, v12946))) return Value(false); v12945 = v12946; return Value(true); }()); return v12938; }());
return {};
}
}  // namespace kagg::opponents::compiled
