// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_0945a994589513abeb54(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"farm", "pos", "t"};
s->PrepareSlots(s_names);
auto v23320 = Get(Get(Get(s->LocalAt(0), Value("tiles")), Get(s->LocalAt(1), Value(int64_t{1}))), Get(s->LocalAt(1), Value(int64_t{0})));
s->SetAt(2, v23320);
return ([&]() -> Value { auto v23321 = ([&]() -> Value { auto fn23322 = s->Global("isinstance"); Arguments args23323; args23323.positional.reserve(2); args23323.Add(s->LocalAt(2), false); args23323.Add(s->Global("dict"), false); return Call(c, fn23322, std::move(args23323)); }()); if (!static_cast<bool>(v23321)) return v23321; v23321 = ([&]() -> Value { auto v23324 = ([&]() -> Value { auto fn23326 = PrepareDictionaryGet(s->LocalAt(2)); Arguments args23327; args23327.Add(Value("kind"), false); return CallDictionaryGet(c, fn23326, std::move(args23327)); }()); Value v23325; v23325 = Value("WEED"); if (!static_cast<bool>(Binary("Eq", v23324, v23325))) return Value(false); v23324 = v23325; return Value(true); }()); return v23321; }());
return {};
}
}  // namespace kagg::opponents::compiled
