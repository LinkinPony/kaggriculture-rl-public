// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_8d54b023e81e6e3761ff(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"a", "b", "key", "result", "value"};
s->PrepareSlots(s_names);
auto v16976 = ([&]() -> Value { auto fn16977 = s->Global("dict"); Arguments args16978; args16978.Add(s->LocalAt(0), false); return Call(c, fn16977, std::move(args16978)); }());
s->SetAt(3, v16976);
for (const auto& item16979 : Iterate(([&]() -> Value { auto fn16980 = Attribute(s->LocalAt(1), "items"); Arguments args16981; return Call(c, fn16980, std::move(args16981)); }()))) {
auto unpack16982 = Iterate(item16979);
ValidateUnpack(unpack16982, 2, false);
s->SetAt(2, unpack16982.at(0));
s->SetAt(4, unpack16982.at(1));
auto v16983 = ([&]() -> Value { auto v16984 = ([&]() -> Value { auto fn16985 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args16986; args16986.positional.reserve(2); args16986.Add(s->LocalAt(2), false); args16986.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn16985, std::move(args16986)); }()); return Binary("Add", v16984, s->LocalAt(4)); }());
Put(s->LocalAt(3), s->LocalAt(2), v16983);
}
return s->LocalAt(3);
return {};
}
}  // namespace kagg::opponents::compiled
