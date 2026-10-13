// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_256017e44dfb590432ff(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "accepted", "acquired", "actor", "amount", "baseline", "baseline_remaining", "baseline_value", "begun", "best", "best_value", "bundle_count", "changes", "command", "config", "current", "delta", "deposited_gain", "dst", "e", "evaluated", "exc", "fallback", "final", "i", "improved", "item", "key", "max_simulations", "n", "obs", "offset", "passes", "physical", "plan", "prices", "proposals_per_actor", "required", "route", "score", "simulations", "sweep", "trial", "winner", "worker_change"};
s->PrepareSlots(s_names);
auto v3374 = ([&]() -> Value { auto fn3375 = s->Global("perf_counter"); Arguments args3376; return Call(c, fn3375, std::move(args3376)); }());
s->SetAt(8, v3374);
auto v3377 = ([&]() -> Value { auto dict3378 = Dict(); auto key3379 = Value("accepted"); Put(dict3378, key3379, Value(false)); auto key3380 = Value("reason"); Put(dict3378, key3380, Value("")); auto key3381 = Value("actions"); Put(dict3378, key3381, Value{}); auto key3382 = Value("simulations"); Put(dict3378, key3382, Value(int64_t{0})); return dict3378; }());
s->SetAt(22, v3377);
try {
if (static_cast<bool>(([&]() -> Value { auto v3384 = ([&]() -> Value { auto v3385 = ([&]() -> Value { auto fn3387 = s->Global("int"); Arguments args3388; args3388.Add(([&]() -> Value { auto fn3389 = s->Global("_get"); Arguments args3390; args3390.positional.reserve(3); args3390.Add(s->LocalAt(30), false); args3390.Add(Value("step"), false); args3390.Add(Unary("USub", Value(int64_t{1})), false); return Call(c, fn3389, std::move(args3390)); }()), false); return Call(c, fn3387, std::move(args3388)); }()); Value v3386; v3386 = s->Global("START"); if (!static_cast<bool>(Binary("NotEq", v3385, v3386))) return Value(false); v3385 = v3386; return Value(true); }()); if (static_cast<bool>(v3384)) return v3384; v3384 = ([&]() -> Value { auto v3391 = ([&]() -> Value { auto fn3393 = s->Global("len"); Arguments args3394; args3394.Add(s->LocalAt(6), false); return Call(c, fn3393, std::move(args3394)); }()); Value v3392; v3392 = ([&]() -> Value { auto v3395 = ([&]() -> Value { auto v3396 = s->Global("FINAL"); return Binary("Sub", v3396, s->Global("START")); }()); return Binary("Add", v3395, Value(int64_t{1})); }()); if (!static_cast<bool>(Binary("NotEq", v3391, v3392))) return Value(false); v3391 = v3392; return Value(true); }()); return v3384; }()))) {
Raise(([&]() -> Value { auto fn3397 = s->Global("Unsupported"); Arguments args3398; args3398.Add(Value("planning requires step 712 and exactly seven actions through 718"), false); return Call(c, fn3397, std::move(args3398)); }()));
}
auto v3399 = ([&]() -> Value { auto fn3400 = s->Global("min"); Arguments args3401; args3401.positional.reserve(2); args3401.Add(Value(int64_t{256}), false); args3401.Add(([&]() -> Value { auto fn3402 = s->Global("max"); Arguments args3403; args3403.positional.reserve(2); args3403.Add(Value(int64_t{1}), false); args3403.Add(([&]() -> Value { auto fn3404 = s->Global("int"); Arguments args3405; args3405.Add(s->LocalAt(28), false); return Call(c, fn3404, std::move(args3405)); }()), false); return Call(c, fn3402, std::move(args3403)); }()), false); return Call(c, fn3400, std::move(args3401)); }());
s->SetAt(28, v3399);
auto v3406 = ([&]() -> Value { auto fn3407 = s->Global("min"); Arguments args3408; args3408.positional.reserve(2); args3408.Add(Value(int64_t{2}), false); args3408.Add(([&]() -> Value { auto fn3409 = s->Global("max"); Arguments args3410; args3410.positional.reserve(2); args3410.Add(Value(int64_t{1}), false); args3410.Add(([&]() -> Value { auto fn3411 = s->Global("int"); Arguments args3412; args3412.Add(s->LocalAt(32), false); return Call(c, fn3411, std::move(args3412)); }()), false); return Call(c, fn3409, std::move(args3410)); }()), false); return Call(c, fn3407, std::move(args3408)); }());
s->SetAt(32, v3406);
auto v3413 = ([&]() -> Value { auto fn3414 = s->Global("min"); Arguments args3415; args3415.positional.reserve(2); args3415.Add(Value(int64_t{16}), false); args3415.Add(([&]() -> Value { auto fn3416 = s->Global("max"); Arguments args3417; args3417.positional.reserve(2); args3417.Add(Value(int64_t{1}), false); args3417.Add(([&]() -> Value { auto fn3418 = s->Global("int"); Arguments args3419; args3419.Add(s->LocalAt(36), false); return Call(c, fn3418, std::move(args3419)); }()), false); return Call(c, fn3416, std::move(args3417)); }()), false); return Call(c, fn3414, std::move(args3415)); }());
s->SetAt(36, v3413);
auto v3420 = ([&]() -> Value { auto fn3421 = s->Global("simulate"); Arguments args3422; args3422.positional.reserve(3); args3422.Add(s->LocalAt(30), false); args3422.Add(s->LocalAt(14), false); args3422.Add(s->LocalAt(6), false); args3422.Keyword("detailed", Value(true)); return Call(c, fn3421, std::move(args3422)); }());
s->SetAt(5, v3420);
auto v3423 = ([&]() -> Value { auto comp3424 = std::make_shared<Scope>(); comp3424->globals = s->globals; comp3424->parent = s; static constexpr const char* comp3424_names[] = {"item"}; comp3424->PrepareSlots(comp3424_names); auto result3425 = Dict(); for (const auto& item3426 : Iterate(s->Global("PRODUCTS"))) { comp3424->SetAt(0, item3426); Put(result3425, comp3424->LocalAt(0), ([&]() -> Value { auto fn3427 = comp3424->Global("max"); Arguments args3428; args3428.positional.reserve(2); args3428.Add(Value(int64_t{1}), false); args3428.Add(([&]() -> Value { auto fn3429 = comp3424->Global("float"); Arguments args3430; args3430.Add(([&]() -> Value { auto fn3431 = PrepareDictionaryGet(([&]() -> Value { auto fn3433 = PrepareDictionaryGet(([&]() -> Value { auto fn3435 = comp3424->Global("_get"); Arguments args3436; args3436.positional.reserve(3); args3436.Add(comp3424->Captured("obs"), false); args3436.Add(Value("market"), false); args3436.Add(([&]() -> Value { auto dict3437 = Dict(); return dict3437; }()), false); return Call(c, fn3435, std::move(args3436)); }())); Arguments args3434; args3434.positional.reserve(2); args3434.Add(Value("prices"), false); args3434.Add(([&]() -> Value { auto dict3438 = Dict(); return dict3438; }()), false); return CallDictionaryGet(c, fn3433, std::move(args3434)); }())); Arguments args3432; args3432.positional.reserve(2); args3432.Add(comp3424->LocalAt(0), false); args3432.Add(Value(int64_t{1}), false); return CallDictionaryGet(c, fn3431, std::move(args3432)); }()), false); return Call(c, fn3429, std::move(args3430)); }()), false); return Call(c, fn3427, std::move(args3428)); }())); } return result3425; }());
s->SetAt(35, v3423);
auto v3439 = Tuple({([&]() -> Value { auto fn3440 = s->Global("_clone_schedule"); Arguments args3441; args3441.Add(s->LocalAt(6), false); return Call(c, fn3440, std::move(args3441)); }()), s->LocalAt(5)});
auto unpack3442 = Iterate(v3439);
ValidateUnpack(unpack3442, 2, false);
s->SetAt(15, unpack3442.at(0));
s->SetAt(9, unpack3442.at(1));
auto v3443 = ([&]() -> Value { auto fn3444 = s->Global("_value"); Arguments args3445; args3445.positional.reserve(2); args3445.Add(s->LocalAt(5), false); args3445.Add(s->LocalAt(35), false); return Call(c, fn3444, std::move(args3445)); }());
s->SetAt(7, v3443);
s->SetAt(10, v3443);
auto v3446 = Tuple({List({}), Value(int64_t{0})});
auto unpack3447 = Iterate(v3446);
ValidateUnpack(unpack3447, 2, false);
s->SetAt(12, unpack3447.at(0));
s->SetAt(40, unpack3447.at(1));
auto v3448 = ([&]() -> Value { auto fn3449 = s->Global("len"); Arguments args3450; args3450.Add(Get(Get(s->LocalAt(5), Value("private")), Value("inventories")), false); return Call(c, fn3449, std::move(args3450)); }());
s->SetAt(29, v3448);
for (const auto& item3451 : Iterate(([&]() -> Value { auto fn3452 = s->Global("range"); Arguments args3453; args3453.Add(s->LocalAt(32), false); return Call(c, fn3452, std::move(args3453)); }()))) {
s->SetAt(41, item3451);
auto v3454 = Value(false);
s->SetAt(25, v3454);
for (const auto& item3455 : Iterate(([&]() -> Value { auto fn3456 = s->Global("range"); Arguments args3457; args3457.Add(s->LocalAt(29), false); return Call(c, fn3456, std::move(args3457)); }()))) {
s->SetAt(3, item3455);
auto v3458 = Value{};
s->SetAt(43, v3458);
for (const auto& item3459 : Iterate(([&]() -> Value { auto fn3460 = s->Global("_proposals"); Arguments args3461; args3461.positional.reserve(4); args3461.Add(s->LocalAt(9), false); args3461.Add(s->LocalAt(3), false); args3461.Add(s->LocalAt(35), false); args3461.Add(s->LocalAt(36), false); return Call(c, fn3460, std::move(args3461)); }()))) {
auto unpack3462 = Iterate(item3459);
ValidateUnpack(unpack3462, 4, false);
s->SetAt(0, unpack3462.at(0));
s->SetAt(31, unpack3462.at(1));
s->SetAt(38, unpack3462.at(2));
s->SetAt(11, unpack3462.at(3));
if (static_cast<bool>(([&]() -> Value { auto v3463 = s->LocalAt(40); Value v3464; v3464 = s->LocalAt(28); if (!static_cast<bool>(Binary("GtE", v3463, v3464))) return Value(false); v3463 = v3464; return Value(true); }()))) {
break;
}
auto v3465 = ([&]() -> Value { auto fn3466 = s->Global("_clone_schedule"); Arguments args3467; args3467.Add(s->LocalAt(15), false); return Call(c, fn3466, std::move(args3467)); }());
s->SetAt(42, v3465);
for (const auto& item3468 : Iterate(([&]() -> Value { auto fn3469 = s->Global("enumerate"); Arguments args3470; args3470.positional.reserve(2); args3470.Add(s->LocalAt(38), false); args3470.Add(s->LocalAt(31), false); return Call(c, fn3469, std::move(args3470)); }()))) {
auto unpack3471 = Iterate(item3468);
ValidateUnpack(unpack3471, 2, false);
s->SetAt(24, unpack3471.at(0));
s->SetAt(13, unpack3471.at(1));
if (static_cast<bool>(([&]() -> Value { auto v3472 = s->LocalAt(3); Value v3473; v3473 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v3472, v3473))) return Value(false); v3472 = v3473; return Value(true); }()))) {
auto v3474 = s->LocalAt(13);
Put(Get(s->LocalAt(42), s->LocalAt(24)), Value("farmer"), v3474);
}
else {
(void)([&]() -> Value { auto fn3475 = Attribute(Get(s->LocalAt(42), s->LocalAt(24)), "setdefault"); Arguments args3476; args3476.positional.reserve(2); args3476.Add(Value("hands"), false); args3476.Add(List({}), false); return Call(c, fn3475, std::move(args3476)); }());
while (static_cast<bool>(([&]() -> Value { auto v3477 = ([&]() -> Value { auto fn3479 = s->Global("len"); Arguments args3480; args3480.Add(Get(Get(s->LocalAt(42), s->LocalAt(24)), Value("hands")), false); return Call(c, fn3479, std::move(args3480)); }()); Value v3478; v3478 = ([&]() -> Value { auto v3481 = s->LocalAt(29); return Binary("Sub", v3481, Value(int64_t{1})); }()); if (!static_cast<bool>(Binary("Lt", v3477, v3478))) return Value(false); v3477 = v3478; return Value(true); }()))) {
(void)([&]() -> Value { auto fn3482 = Attribute(Get(Get(s->LocalAt(42), s->LocalAt(24)), Value("hands")), "append"); Arguments args3483; args3483.Add(List({Value("PASS")}), false); return Call(c, fn3482, std::move(args3483)); }());
}
auto v3484 = s->LocalAt(13);
Put(Get(Get(s->LocalAt(42), s->LocalAt(24)), Value("hands")), ([&]() -> Value { auto v3485 = s->LocalAt(3); return Binary("Sub", v3485, Value(int64_t{1})); }()), v3484);
}
}
auto v3486 = ([&]() -> Value { auto fn3487 = s->Global("simulate"); Arguments args3488; args3488.positional.reserve(3); args3488.Add(s->LocalAt(30), false); args3488.Add(s->LocalAt(14), false); args3488.Add(s->LocalAt(42), false); return Call(c, fn3487, std::move(args3488)); }());
s->SetAt(20, v3486);
auto v3489 = s->LocalAt(40);
s->SetAt(40, Inplace("Add", v3489, Value(int64_t{1})));
auto v3490 = ([&]() -> Value { auto fn3491 = s->Global("_value"); Arguments args3492; args3492.positional.reserve(2); args3492.Add(s->LocalAt(20), false); args3492.Add(s->LocalAt(35), false); return Call(c, fn3491, std::move(args3492)); }());
s->SetAt(39, v3490);
if (static_cast<bool>(([&]() -> Value { auto v3493 = ([&]() -> Value { auto v3494 = s->LocalAt(39); Value v3495; v3495 = s->LocalAt(10); if (!static_cast<bool>(Binary("Gt", v3494, v3495))) return Value(false); v3494 = v3495; return Value(true); }()); if (!static_cast<bool>(v3493)) return v3493; v3493 = ([&]() -> Value { auto fn3496 = s->Global("dominates"); Arguments args3497; args3497.positional.reserve(2); args3497.Add(s->LocalAt(20), false); args3497.Add(s->LocalAt(5), false); return Call(c, fn3496, std::move(args3497)); }()); return v3493; }()))) {
auto v3498 = ([&]() -> Value { auto comp3499 = std::make_shared<Scope>(); comp3499->globals = s->globals; comp3499->parent = s; static constexpr const char* comp3499_names[] = {"e"}; comp3499->PrepareSlots(comp3499_names); auto result3500 = Dict(); for (const auto& item3501 : Iterate(Get(s->LocalAt(9), Value("events")))) { comp3499->SetAt(0, item3501); if (!static_cast<bool>(([&]() -> Value { auto v3502 = ([&]() -> Value { auto v3503 = Value("acquired"); Value v3504; v3504 = comp3499->LocalAt(0); if (!static_cast<bool>(Binary("In", v3503, v3504))) return Value(false); v3503 = v3504; return Value(true); }()); if (!static_cast<bool>(v3502)) return v3502; v3502 = ([&]() -> Value { auto v3505 = Get(comp3499->LocalAt(0), Value("actor")); Value v3506; v3506 = comp3499->Captured("actor"); if (!static_cast<bool>(Binary("NotEq", v3505, v3506))) return Value(false); v3505 = v3506; return Value(true); }()); return v3502; }()))) continue; Put(result3500, Tuple({([&]() -> Value { auto fn3507 = comp3499->Global("tuple"); Arguments args3508; args3508.Add(Get(comp3499->LocalAt(0), Value("xy")), false); return Call(c, fn3507, std::move(args3508)); }()), Get(comp3499->LocalAt(0), Value("op")), Get(comp3499->LocalAt(0), Value("actor"))}), Get(comp3499->LocalAt(0), Value("acquired"))); } return result3500; }());
s->SetAt(37, v3498);
auto v3509 = ([&]() -> Value { auto dict3510 = Dict(); return dict3510; }());
s->SetAt(2, v3509);
for (const auto& item3511 : Iterate(Get(s->LocalAt(20), Value("events")))) {
s->SetAt(19, item3511);
if (static_cast<bool>(([&]() -> Value { auto v3512 = Value("acquired"); Value v3513; v3513 = s->LocalAt(19); if (!static_cast<bool>(Binary("In", v3512, v3513))) return Value(false); v3512 = v3513; return Value(true); }()))) {
auto v3514 = Tuple({([&]() -> Value { auto fn3515 = s->Global("tuple"); Arguments args3516; args3516.Add(Get(s->LocalAt(19), Value("xy")), false); return Call(c, fn3515, std::move(args3516)); }()), Get(s->LocalAt(19), Value("op")), Get(s->LocalAt(19), Value("actor"))});
s->SetAt(27, v3514);
auto v3517 = ([&]() -> Value { auto fn3518 = Attribute(s->LocalAt(2), "setdefault"); Arguments args3519; args3519.positional.reserve(2); args3519.Add(s->LocalAt(27), false); args3519.Add(([&]() -> Value { auto dict3520 = Dict(); return dict3520; }()), false); return Call(c, fn3518, std::move(args3519)); }());
s->SetAt(18, v3517);
for (const auto& item3521 : Iterate(([&]() -> Value { auto fn3522 = Attribute(Get(s->LocalAt(19), Value("acquired")), "items"); Arguments args3523; return Call(c, fn3522, std::move(args3523)); }()))) {
auto unpack3524 = Iterate(item3521);
ValidateUnpack(unpack3524, 2, false);
s->SetAt(26, unpack3524.at(0));
s->SetAt(4, unpack3524.at(1));
auto v3525 = ([&]() -> Value { auto v3526 = ([&]() -> Value { auto fn3527 = PrepareDictionaryGet(s->LocalAt(18)); Arguments args3528; args3528.positional.reserve(2); args3528.Add(s->LocalAt(26), false); args3528.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn3527, std::move(args3528)); }()); return Binary("Add", v3526, s->LocalAt(4)); }());
Put(s->LocalAt(18), s->LocalAt(26), v3525);
}
}
}
if (static_cast<bool>(([&]() -> Value { auto comp3529 = std::make_shared<Scope>(); comp3529->globals = s->globals; comp3529->parent = s; static constexpr const char* comp3529_names[] = {"k", "v"}; comp3529->PrepareSlots(comp3529_names); auto result3530 = List(); for (const auto& item3531 : Iterate(([&]() -> Value { auto fn3532 = Attribute(s->LocalAt(37), "items"); Arguments args3533; return Call(c, fn3532, std::move(args3533)); }()))) { auto unpack3534 = Iterate(item3531); ValidateUnpack(unpack3534, 2, false); comp3529->SetAt(0, unpack3534.at(0)); comp3529->SetAt(1, unpack3534.at(1)); if (!static_cast<bool>(([&]() -> Value { auto fn3535 = comp3529->Global("_ge"); Arguments args3536; args3536.positional.reserve(2); args3536.Add(([&]() -> Value { auto fn3537 = PrepareDictionaryGet(comp3529->Captured("acquired")); Arguments args3538; args3538.positional.reserve(2); args3538.Add(comp3529->LocalAt(0), false); args3538.Add(([&]() -> Value { auto dict3539 = Dict(); return dict3539; }()), false); return CallDictionaryGet(c, fn3537, std::move(args3538)); }()), false); args3536.Add(comp3529->LocalAt(1), false); return Call(c, fn3535, std::move(args3536)); }()))) return Value(false); } return Value(true); }()))) {
auto v3540 = Tuple({Tuple({s->LocalAt(42), s->LocalAt(31), s->LocalAt(11)}), s->LocalAt(39)});
auto unpack3541 = Iterate(v3540);
ValidateUnpack(unpack3541, 2, false);
s->SetAt(43, unpack3541.at(0));
s->SetAt(10, unpack3541.at(1));
}
}
}
if (static_cast<bool>(s->LocalAt(43))) {
auto v3542 = s->LocalAt(43);
auto unpack3543 = Iterate(v3542);
ValidateUnpack(unpack3543, 3, false);
s->SetAt(15, unpack3543.at(0));
s->SetAt(31, unpack3543.at(1));
s->SetAt(11, unpack3543.at(2));
auto v3544 = ([&]() -> Value { auto fn3545 = s->Global("simulate"); Arguments args3546; args3546.positional.reserve(3); args3546.Add(s->LocalAt(30), false); args3546.Add(s->LocalAt(14), false); args3546.Add(s->LocalAt(15), false); args3546.Keyword("detailed", Value(true)); return Call(c, fn3545, std::move(args3546)); }());
s->SetAt(9, v3544);
(void)([&]() -> Value { auto fn3547 = Attribute(s->LocalAt(12), "append"); Arguments args3548; args3548.Add(([&]() -> Value { auto dict3549 = Dict(); auto key3550 = Value("pass"); Put(dict3549, key3550, s->LocalAt(41)); auto key3551 = Value("actor"); Put(dict3549, key3551, s->LocalAt(3)); auto key3552 = Value("from_step"); Put(dict3549, key3552, ([&]() -> Value { auto v3553 = s->Global("START"); return Binary("Add", v3553, s->LocalAt(31)); }())); auto key3554 = Value("resource_bundles"); Put(dict3549, key3554, s->LocalAt(11)); auto key3555 = Value("estimated_stock_value"); Put(dict3549, key3555, s->LocalAt(10)); return dict3549; }()), false); return Call(c, fn3547, std::move(args3548)); }());
auto v3556 = Value(true);
s->SetAt(25, v3556);
}
if (static_cast<bool>(([&]() -> Value { auto v3557 = s->LocalAt(40); Value v3558; v3558 = s->LocalAt(28); if (!static_cast<bool>(Binary("GtE", v3557, v3558))) return Value(false); v3557 = v3558; return Value(true); }()))) {
break;
}
}
if (static_cast<bool>(([&]() -> Value { auto v3559 = Unary("Not", s->LocalAt(25)); if (static_cast<bool>(v3559)) return v3559; v3559 = ([&]() -> Value { auto v3560 = s->LocalAt(40); Value v3561; v3561 = s->LocalAt(28); if (!static_cast<bool>(Binary("GtE", v3560, v3561))) return Value(false); v3560 = v3561; return Value(true); }()); return v3559; }()))) {
break;
}
}
if (static_cast<bool>(([&]() -> Value { auto v3562 = Unary("Not", s->LocalAt(12)); if (static_cast<bool>(v3562)) return v3562; v3562 = ([&]() -> Value { auto v3563 = s->LocalAt(10); Value v3564; v3564 = s->LocalAt(7); if (!static_cast<bool>(Binary("LtE", v3563, v3564))) return Value(false); v3563 = v3564; return Value(true); }()); return v3562; }()))) {
return ([&]() -> Value { auto dict3565 = Dict(); Merge(dict3565, s->LocalAt(22)); auto key3566 = Value("reason"); Put(dict3565, key3566, Value("no positive physical delivery gain")); auto key3567 = Value("simulations"); Put(dict3565, key3567, s->LocalAt(40)); auto key3568 = Value("changed_workers"); Put(dict3565, key3568, List({})); auto key3569 = Value("changes"); Put(dict3565, key3569, List({})); auto key3570 = Value("certificate"); Put(dict3565, key3570, ([&]() -> Value { auto dict3571 = Dict(); auto key3572 = Value("stock_value_gain_at_initial_prices"); Put(dict3571, key3572, Value(int64_t{0})); auto key3573 = Value("sold_unit_delta"); Put(dict3571, key3573, ([&]() -> Value { auto fn3574 = Attribute(s->Global("dict"), "fromkeys"); Arguments args3575; args3575.positional.reserve(2); args3575.Add(s->Global("PRODUCTS"), false); args3575.Add(Value(int64_t{0}), false); return Call(c, fn3574, std::move(args3575)); }())); return dict3571; }())); auto key3576 = Value("planning_ms"); Put(dict3565, key3576, ([&]() -> Value { auto v3577 = ([&]() -> Value { auto v3578 = ([&]() -> Value { auto fn3579 = s->Global("perf_counter"); Arguments args3580; return Call(c, fn3579, std::move(args3580)); }()); return Binary("Sub", v3578, s->LocalAt(8)); }()); return Binary("Mult", v3577, Value(int64_t{1000})); }())); return dict3565; }());
}
auto v3581 = ([&]() -> Value { auto fn3582 = s->Global("simulate"); Arguments args3583; args3583.positional.reserve(3); args3583.Add(s->LocalAt(30), false); args3583.Add(s->LocalAt(14), false); args3583.Add(s->LocalAt(15), false); args3583.Keyword("final_liquidate", Value(true)); args3583.Keyword("detailed", Value(true)); return Call(c, fn3582, std::move(args3583)); }());
s->SetAt(23, v3581);
auto v3584 = ([&]() -> Value { auto fn3585 = s->Global("simulate"); Arguments args3586; args3586.positional.reserve(3); args3586.Add(s->LocalAt(30), false); args3586.Add(s->LocalAt(14), false); args3586.Add(s->LocalAt(15), false); return Call(c, fn3585, std::move(args3586)); }());
s->SetAt(33, v3584);
if (static_cast<bool>(Unary("Not", ([&]() -> Value { auto fn3587 = s->Global("dominates"); Arguments args3588; args3588.positional.reserve(2); args3588.Add(s->LocalAt(33), false); args3588.Add(s->LocalAt(5), false); return Call(c, fn3587, std::move(args3588)); }())))) {
Raise(([&]() -> Value { auto fn3589 = s->Global("Unsupported"); Arguments args3590; args3590.Add(Value("no zero-overflow dominating continuation"), false); return Call(c, fn3589, std::move(args3590)); }()));
}
auto v3591 = ([&]() -> Value { auto comp3592 = std::make_shared<Scope>(); comp3592->globals = s->globals; comp3592->parent = s; static constexpr const char* comp3592_names[] = {"item"}; comp3592->PrepareSlots(comp3592_names); auto result3593 = Dict(); for (const auto& item3594 : Iterate(s->Global("PRODUCTS"))) { comp3592->SetAt(0, item3594); Put(result3593, comp3592->LocalAt(0), ([&]() -> Value { auto v3595 = ([&]() -> Value { auto fn3596 = PrepareDictionaryGet(Get(comp3592->Captured("final"), Value("sold"))); Arguments args3597; args3597.positional.reserve(2); args3597.Add(comp3592->LocalAt(0), false); args3597.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn3596, std::move(args3597)); }()); return Binary("Sub", v3595, ([&]() -> Value { auto fn3598 = PrepareDictionaryGet(Get(comp3592->Captured("baseline"), Value("sold"))); Arguments args3599; args3599.positional.reserve(2); args3599.Add(comp3592->LocalAt(0), false); args3599.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn3598, std::move(args3599)); }())); }())); } return result3593; }());
s->SetAt(16, v3591);
auto v3600 = ([&]() -> Value { auto comp3601 = std::make_shared<Scope>(); comp3601->globals = s->globals; comp3601->parent = s; static constexpr const char* comp3601_names[] = {"actor", "item"}; comp3601->PrepareSlots(comp3601_names); auto result3602 = List(); for (const auto& item3603 : Iterate(([&]() -> Value { auto fn3604 = s->Global("range"); Arguments args3605; args3605.Add(s->LocalAt(29), false); return Call(c, fn3604, std::move(args3605)); }()))) { comp3601->SetAt(0, item3603); for (const auto& item3606 : Iterate(comp3601->Global("PRODUCTS"))) { comp3601->SetAt(1, item3606); if (static_cast<bool>(([&]() -> Value { auto v3607 = ([&]() -> Value { auto fn3609 = PrepareDictionaryGet(Get(Get(Get(Get(comp3601->Captured("final"), Value("rows")), Unary("USub", Value(int64_t{1}))), Value("deposited_by_actor")), comp3601->LocalAt(0))); Arguments args3610; args3610.positional.reserve(2); args3610.Add(comp3601->LocalAt(1), false); args3610.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn3609, std::move(args3610)); }()); Value v3608; v3608 = ([&]() -> Value { auto fn3611 = PrepareDictionaryGet(Get(Get(Get(Get(comp3601->Captured("baseline"), Value("rows")), Unary("USub", Value(int64_t{1}))), Value("deposited_by_actor")), comp3601->LocalAt(0))); Arguments args3612; args3612.positional.reserve(2); args3612.Add(comp3601->LocalAt(1), false); args3612.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn3611, std::move(args3612)); }()); if (!static_cast<bool>(Binary("Gt", v3607, v3608))) return Value(false); v3607 = v3608; return Value(true); }()))) return Value(true); } } return Value(false); }());
s->SetAt(17, v3600);
auto v3613 = ([&]() -> Value { auto comp3614 = std::make_shared<Scope>(); comp3614->globals = s->globals; comp3614->parent = s; static constexpr const char* comp3614_names[] = {"new", "old"}; comp3614->PrepareSlots(comp3614_names); auto result3615 = List(); for (const auto& item3616 : Iterate(([&]() -> Value { auto fn3617 = s->Global("zip"); Arguments args3618; args3618.positional.reserve(2); args3618.Add(Get(s->LocalAt(23), Value("actions")), false); args3618.Add(Get(s->LocalAt(5), Value("actions")), false); return Call(c, fn3617, std::move(args3618)); }()))) { auto unpack3619 = Iterate(item3616); ValidateUnpack(unpack3619, 2, false); comp3614->SetAt(0, unpack3619.at(0)); comp3614->SetAt(1, unpack3619.at(1)); if (static_cast<bool>(([&]() -> Value { auto v3620 = ([&]() -> Value { auto fn3622 = comp3614->Global("_commands"); Arguments args3623; args3623.positional.reserve(2); args3623.Add(comp3614->LocalAt(0), false); args3623.Add(comp3614->Captured("n"), false); return Call(c, fn3622, std::move(args3623)); }()); Value v3621; v3621 = ([&]() -> Value { auto fn3624 = comp3614->Global("_commands"); Arguments args3625; args3625.positional.reserve(2); args3625.Add(comp3614->LocalAt(1), false); args3625.Add(comp3614->Captured("n"), false); return Call(c, fn3624, std::move(args3625)); }()); if (!static_cast<bool>(Binary("NotEq", v3620, v3621))) return Value(false); v3620 = v3621; return Value(true); }()))) return Value(true); } return Value(false); }());
s->SetAt(44, v3613);
auto v3626 = ([&]() -> Value { auto v3627 = s->LocalAt(44); if (!static_cast<bool>(v3627)) return v3627; v3627 = s->LocalAt(17); if (!static_cast<bool>(v3627)) return v3627; v3627 = ([&]() -> Value { auto comp3628 = std::make_shared<Scope>(); comp3628->globals = s->globals; comp3628->parent = s; static constexpr const char* comp3628_names[] = {"v"}; comp3628->PrepareSlots(comp3628_names); auto result3629 = List(); for (const auto& item3630 : Iterate(([&]() -> Value { auto fn3631 = Attribute(s->LocalAt(16), "values"); Arguments args3632; return Call(c, fn3631, std::move(args3632)); }()))) { comp3628->SetAt(0, item3630); if (static_cast<bool>(([&]() -> Value { auto v3633 = comp3628->LocalAt(0); Value v3634; v3634 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v3633, v3634))) return Value(false); v3633 = v3634; return Value(true); }()))) return Value(true); } return Value(false); }()); if (!static_cast<bool>(v3627)) return v3627; v3627 = ([&]() -> Value { auto comp3635 = std::make_shared<Scope>(); comp3635->globals = s->globals; comp3635->parent = s; static constexpr const char* comp3635_names[] = {"v"}; comp3635->PrepareSlots(comp3635_names); auto result3636 = List(); for (const auto& item3637 : Iterate(([&]() -> Value { auto fn3638 = Attribute(s->LocalAt(16), "values"); Arguments args3639; return Call(c, fn3638, std::move(args3639)); }()))) { comp3635->SetAt(0, item3637); if (!static_cast<bool>(([&]() -> Value { auto v3640 = comp3635->LocalAt(0); Value v3641; v3641 = Value(int64_t{0}); if (!static_cast<bool>(Binary("GtE", v3640, v3641))) return Value(false); v3640 = v3641; return Value(true); }()))) return Value(false); } return Value(true); }()); return v3627; }());
s->SetAt(1, v3626);
auto v3642 = ([&]() -> Value { auto dict3643 = Dict(); auto key3644 = Value("accepted"); Put(dict3643, key3644, s->LocalAt(1)); auto key3645 = Value("reason"); Put(dict3643, key3645, (static_cast<bool>(s->LocalAt(1)) ? Value("joint physical dominance") : Value("no improvement"))); auto key3646 = Value("baseline"); Put(dict3643, key3646, ([&]() -> Value { auto fn3647 = s->Global("_clone_schedule"); Arguments args3648; args3648.Add(s->LocalAt(6), false); return Call(c, fn3647, std::move(args3648)); }())); auto key3649 = Value("actions"); Put(dict3643, key3649, Get(s->LocalAt(23), Value("actions"))); auto key3650 = Value("expected_states"); Put(dict3643, key3650, Slice(Get(s->LocalAt(23), Value("states")), Value{}, Unary("USub", Value(int64_t{1})), Value{})); auto key3651 = Value("simulations"); Put(dict3643, key3651, s->LocalAt(40)); auto key3652 = Value("changes"); Put(dict3643, key3652, s->LocalAt(12)); auto key3653 = Value("abandoned"); Put(dict3643, key3653, Value(false)); auto key3654 = Value("changed_workers"); Put(dict3643, key3654, ([&]() -> Value { auto fn3655 = s->Global("sorted"); Arguments args3656; args3656.Add(([&]() -> Value { auto comp3657 = std::make_shared<Scope>(); comp3657->globals = s->globals; comp3657->parent = s; static constexpr const char* comp3657_names[] = {"c"}; comp3657->PrepareSlots(comp3657_names); auto result3658 = List(); for (const auto& item3659 : Iterate(s->LocalAt(12))) { comp3657->SetAt(0, item3659); result3658.node()->sequence.push_back(Get(comp3657->LocalAt(0), Value("actor"))); } return Set(result3658.node()->sequence); }()), false); return Call(c, fn3655, std::move(args3656)); }())); auto key3660 = Value("certificate"); Put(dict3643, key3660, ([&]() -> Value { auto dict3661 = Dict(); auto key3662 = Value("baseline_rows"); Put(dict3661, key3662, Get(s->LocalAt(5), Value("rows"))); auto key3663 = Value("physical_rows"); Put(dict3661, key3663, Get(s->LocalAt(33), Value("rows"))); auto key3664 = Value("baseline_overflow"); Put(dict3661, key3664, Get(s->LocalAt(5), Value("overflow_units"))); auto key3665 = Value("candidate_overflow"); Put(dict3661, key3665, Get(s->LocalAt(23), Value("overflow_units"))); auto key3666 = Value("sold_unit_delta"); Put(dict3661, key3666, s->LocalAt(16)); auto key3667 = Value("stock_value_gain_at_initial_prices"); Put(dict3661, key3667, ([&]() -> Value { auto v3668 = s->LocalAt(10); return Binary("Sub", v3668, s->LocalAt(7)); }())); auto key3669 = Value("baseline_final_shed"); Put(dict3661, key3669, Get(Get(s->LocalAt(5), Value("private")), Value("shed"))); auto key3670 = Value("final_shed"); Put(dict3661, key3670, Get(Get(s->LocalAt(23), Value("private")), Value("shed"))); auto key3671 = Value("positive_physical_deposit_gain"); Put(dict3661, key3671, s->LocalAt(17)); auto key3672 = Value("markets_712_717_unchanged"); Put(dict3661, key3672, ([&]() -> Value { auto comp3673 = std::make_shared<Scope>(); comp3673->globals = s->globals; comp3673->parent = s; static constexpr const char* comp3673_names[] = {"i"}; comp3673->PrepareSlots(comp3673_names); auto result3674 = List(); for (const auto& item3675 : Iterate(([&]() -> Value { auto fn3676 = s->Global("range"); Arguments args3677; args3677.Add(([&]() -> Value { auto v3678 = s->Global("FINAL"); return Binary("Sub", v3678, s->Global("START")); }()), false); return Call(c, fn3676, std::move(args3677)); }()))) { comp3673->SetAt(0, item3675); if (!static_cast<bool>(([&]() -> Value { auto v3679 = ([&]() -> Value { auto fn3681 = PrepareDictionaryGet(Get(Get(comp3673->Captured("final"), Value("actions")), comp3673->LocalAt(0))); Arguments args3682; args3682.positional.reserve(2); args3682.Add(Value("market"), false); args3682.Add(List({}), false); return CallDictionaryGet(c, fn3681, std::move(args3682)); }()); Value v3680; v3680 = ([&]() -> Value { auto fn3683 = PrepareDictionaryGet(Get(comp3673->Captured("baseline_remaining"), comp3673->LocalAt(0))); Arguments args3684; args3684.positional.reserve(2); args3684.Add(Value("market"), false); args3684.Add(List({}), false); return CallDictionaryGet(c, fn3683, std::move(args3684)); }()); if (!static_cast<bool>(Binary("Eq", v3679, v3680))) return Value(false); v3679 = v3680; return Value(true); }()))) return Value(false); } return Value(true); }())); return dict3661; }())); return dict3643; }());
s->SetAt(34, v3642);
} catch (const Error& error3383) {
if (Matches(error3383, Tuple({s->Global("Unsupported"), s->Global("KeyError"), s->Global("TypeError"), s->Global("ValueError"), s->Global("IndexError")}))) {
s->SetAt(21, Value(error3383.what()));
auto v3685 = ([&]() -> Value { auto dict3686 = Dict(); Merge(dict3686, s->LocalAt(22)); auto key3687 = Value("reason"); Put(dict3686, key3687, ([&]() -> Value { auto fn3688 = s->Global("str"); Arguments args3689; args3689.Add(s->LocalAt(21), false); return Call(c, fn3688, std::move(args3689)); }())); return dict3686; }());
s->SetAt(34, v3685);
}
else { throw; }
}
auto v3690 = ([&]() -> Value { auto v3691 = ([&]() -> Value { auto v3692 = ([&]() -> Value { auto fn3693 = s->Global("perf_counter"); Arguments args3694; return Call(c, fn3693, std::move(args3694)); }()); return Binary("Sub", v3692, s->LocalAt(8)); }()); return Binary("Mult", v3691, Value(int64_t{1000})); }());
Put(s->LocalAt(34), Value("planning_ms"), v3690);
return s->LocalAt(34);
return {};
}
}  // namespace kagg::opponents::compiled
