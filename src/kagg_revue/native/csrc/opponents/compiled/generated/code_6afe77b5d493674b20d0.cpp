// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_6afe77b5d493674b20d0(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "observation"};
s->PrepareSlots(s_names);
try {
auto v1950 = ([&]() -> Value { auto fn1951 = s->Global("_IMPL"); Arguments args1952; args1952.positional.reserve(2); args1952.Add(s->LocalAt(2), false); args1952.Add(s->LocalAt(1), false); return Call(c, fn1951, std::move(args1952)); }());
s->SetAt(0, v1950);
return s->LocalAt(0);
} catch (const Error& error1949) {
if (Matches(error1949, s->Global("Exception"))) {
return ([&]() -> Value { auto dict1953 = Dict(); auto key1954 = Value("farmer"); Put(dict1953, key1954, List({Value("PASS")})); auto key1955 = Value("hands"); Put(dict1953, key1955, List({})); auto key1956 = Value("market"); Put(dict1953, key1956, List({})); return dict1953; }());
}
else { throw; }
}
return {};
}
}  // namespace kagg::opponents::compiled
