// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_f5035d136d45ab7a817e(Context& c, const ScopePtr& s) {
return ([&]() -> Value { auto dict5281 = Dict(); auto key5282 = Value("last"); Put(dict5281, key5282, Unary("USub", Value(int64_t{1}))); auto key5283 = Value("confirmed"); Put(dict5281, key5283, Value(int64_t{0})); auto key5284 = Value("reserved"); Put(dict5281, key5284, Value(int64_t{0})); auto key5285 = Value("pending_buy"); Put(dict5281, key5285, Value{}); auto key5286 = Value("carrying"); Put(dict5281, key5286, ([&]() -> Value { auto dict5287 = Dict(); return dict5287; }())); auto key5288 = Value("pending_places"); Put(dict5281, key5288, List({})); auto key5289 = Value("sites"); Put(dict5281, key5289, ([&]() -> Value { auto dict5290 = Dict(); return dict5290; }())); auto key5291 = Value("milk_credit"); Put(dict5281, key5291, Value(int64_t{0})); auto key5292 = Value("requested"); Put(dict5281, key5292, Value(int64_t{0})); auto key5293 = Value("failed_purchase_units"); Put(dict5281, key5293, Value(int64_t{0})); auto key5294 = Value("picked"); Put(dict5281, key5294, Value(int64_t{0})); auto key5295 = Value("placed"); Put(dict5281, key5295, Value(int64_t{0})); auto key5296 = Value("failed_placements"); Put(dict5281, key5296, Value(int64_t{0})); auto key5297 = Value("extra_milk_harvested"); Put(dict5281, key5297, Value(int64_t{0})); auto key5298 = Value("extra_milk_sale_requests"); Put(dict5281, key5298, Value(int64_t{0})); return dict5281; }());
return {};
}
}  // namespace kagg::opponents::compiled
