// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_f6c830621556c74c3b29(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"pos", "target", "tx", "ty", "x", "y"};
s->PrepareSlots(s_names);
auto v20564 = s->LocalAt(0);
auto unpack20565 = Iterate(v20564);
ValidateUnpack(unpack20565, 2, false);
s->SetAt(4, unpack20565.at(0));
s->SetAt(5, unpack20565.at(1));
auto v20566 = s->LocalAt(1);
auto unpack20567 = Iterate(v20566);
ValidateUnpack(unpack20567, 2, false);
s->SetAt(2, unpack20567.at(0));
s->SetAt(3, unpack20567.at(1));
return ([&]() -> Value { auto v20568 = ([&]() -> Value { auto v20569 = ([&]() -> Value { auto v20570 = ([&]() -> Value { auto v20571 = List({List({Value("EAST")})}); return Binary("Mult", v20571, ([&]() -> Value { auto fn20572 = s->Global("max"); Arguments args20573; args20573.positional.reserve(2); args20573.Add(Value(int64_t{0}), false); args20573.Add(([&]() -> Value { auto v20574 = s->LocalAt(2); return Binary("Sub", v20574, s->LocalAt(4)); }()), false); return Call(c, fn20572, std::move(args20573)); }())); }()); return Binary("Add", v20570, ([&]() -> Value { auto v20575 = List({List({Value("WEST")})}); return Binary("Mult", v20575, ([&]() -> Value { auto fn20576 = s->Global("max"); Arguments args20577; args20577.positional.reserve(2); args20577.Add(Value(int64_t{0}), false); args20577.Add(([&]() -> Value { auto v20578 = s->LocalAt(4); return Binary("Sub", v20578, s->LocalAt(2)); }()), false); return Call(c, fn20576, std::move(args20577)); }())); }())); }()); return Binary("Add", v20569, ([&]() -> Value { auto v20579 = List({List({Value("SOUTH")})}); return Binary("Mult", v20579, ([&]() -> Value { auto fn20580 = s->Global("max"); Arguments args20581; args20581.positional.reserve(2); args20581.Add(Value(int64_t{0}), false); args20581.Add(([&]() -> Value { auto v20582 = s->LocalAt(3); return Binary("Sub", v20582, s->LocalAt(5)); }()), false); return Call(c, fn20580, std::move(args20581)); }())); }())); }()); return Binary("Add", v20568, ([&]() -> Value { auto v20583 = List({List({Value("NORTH")})}); return Binary("Mult", v20583, ([&]() -> Value { auto fn20584 = s->Global("max"); Arguments args20585; args20585.positional.reserve(2); args20585.Add(Value(int64_t{0}), false); args20585.Add(([&]() -> Value { auto v20586 = s->LocalAt(5); return Binary("Sub", v20586, s->LocalAt(3)); }()), false); return Call(c, fn20584, std::move(args20585)); }())); }())); }());
return {};
}
}  // namespace kagg::opponents::compiled
