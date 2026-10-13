// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_769530f992e6e003dbac(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"farm", "prices", "private"};
s->PrepareSlots(s_names);
return ([&]() -> Value { auto fn2768 = s->Global("liquidate"); Arguments args2769; args2769.Add(([&]() -> Value { auto fn2770 = s->Global("FarmView"); Arguments args2771; args2771.Add(([&]() -> Value { auto dict2772 = Dict(); auto key2773 = Value("player"); Put(dict2772, key2773, Value(int64_t{0})); auto key2774 = Value("farms"); Put(dict2772, key2774, List({s->LocalAt(0)})); auto key2775 = Value("private"); Put(dict2772, key2775, s->LocalAt(2)); auto key2776 = Value("market"); Put(dict2772, key2776, ([&]() -> Value { auto dict2777 = Dict(); auto key2778 = Value("prices"); Put(dict2777, key2778, s->LocalAt(1)); return dict2777; }())); return dict2772; }()), false); return Call(c, fn2770, std::move(args2771)); }()), false); return Call(c, fn2768, std::move(args2769)); }());
return {};
}
}  // namespace kagg::opponents::compiled
