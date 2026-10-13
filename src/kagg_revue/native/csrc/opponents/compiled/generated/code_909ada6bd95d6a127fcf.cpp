// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_909ada6bd95d6a127fcf(Context& c, const ScopePtr& s) {
return ([&]() -> Value { auto dict19663 = Dict(); auto key19664 = Value("last"); Put(dict19663, key19664, Unary("USub", Value(int64_t{1}))); auto key19665 = Value("pending"); Put(dict19663, key19665, List({})); auto key19666 = Value("credit"); Put(dict19663, key19666, ([&]() -> Value { auto dict19667 = Dict(); return dict19667; }())); auto key19668 = Value("sites"); Put(dict19663, key19668, ([&]() -> Value { auto dict19669 = Dict(); return dict19669; }())); auto key19670 = Value("sale"); Put(dict19663, key19670, ([&]() -> Value { auto dict19671 = Dict(); return dict19671; }())); auto key19672 = Value("coop_swap"); Put(dict19663, key19672, Value(int64_t{0})); return dict19663; }());
return {};
}
}  // namespace kagg::opponents::compiled
