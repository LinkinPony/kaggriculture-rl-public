// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_02db12f32a9a43740923(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "configuration", "k", "observation"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v20404 = ([&]() -> Value { auto fn20406 = s->Global("int"); Arguments args20407; args20407.Add(([&]() -> Value { auto fn20408 = PrepareDictionaryGet(s->LocalAt(3)); Arguments args20409; args20409.positional.reserve(2); args20409.Add(Value("step"), false); args20409.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn20408, std::move(args20409)); }()), false); return Call(c, fn20406, std::move(args20407)); }()); Value v20405; v20405 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v20404, v20405))) return Value(false); v20404 = v20405; return Value(true); }()))) {
for (const auto& item20410 : Iterate(s->Global("_E334_REPORT"))) {
s->SetAt(2, item20410);
auto v20411 = Value(int64_t{0});
Put(s->Global("_E334_REPORT"), s->LocalAt(2), v20411);
}
}
auto v20412 = ([&]() -> Value { auto fn20413 = s->Global("_E334_BASE"); Arguments args20414; args20414.positional.reserve(2); args20414.Add(s->LocalAt(3), false); args20414.Add(s->LocalAt(1), false); return Call(c, fn20413, std::move(args20414)); }());
s->SetAt(0, v20412);
try {
return ([&]() -> Value { auto fn20416 = s->Global("_e334_compact"); Arguments args20417; args20417.positional.reserve(2); args20417.Add(s->LocalAt(3), false); args20417.Add(s->LocalAt(0), false); return Call(c, fn20416, std::move(args20417)); }());
} catch (const Error& error20415) {
if (Matches(error20415, s->Global("Exception"))) {
auto v20418 = s->Global("_E334_REPORT");
auto v20419 = Value("errors");
auto v20420 = Get(v20418, v20419);
Put(v20418, v20419, Inplace("Add", v20420, Value(int64_t{1})));
return s->LocalAt(0);
}
else { throw; }
}
return {};
}
}  // namespace kagg::opponents::compiled
