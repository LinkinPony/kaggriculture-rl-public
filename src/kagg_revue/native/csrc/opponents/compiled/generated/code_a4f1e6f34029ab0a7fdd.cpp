// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_a4f1e6f34029ab0a7fdd(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"pos", "target", "tx", "ty", "x", "y"};
s->PrepareSlots(s_names);
auto v4448 = s->LocalAt(0);
auto unpack4449 = Iterate(v4448);
ValidateUnpack(unpack4449, 2, false);
s->SetAt(4, unpack4449.at(0));
s->SetAt(5, unpack4449.at(1));
auto v4450 = s->LocalAt(1);
auto unpack4451 = Iterate(v4450);
ValidateUnpack(unpack4451, 2, false);
s->SetAt(2, unpack4451.at(0));
s->SetAt(3, unpack4451.at(1));
if (static_cast<bool>(([&]() -> Value { auto v4452 = s->LocalAt(4); Value v4453; v4453 = s->LocalAt(2); if (!static_cast<bool>(Binary("NotEq", v4452, v4453))) return Value(false); v4452 = v4453; return Value(true); }()))) {
return List({(static_cast<bool>(([&]() -> Value { auto v4454 = s->LocalAt(4); Value v4455; v4455 = s->LocalAt(2); if (!static_cast<bool>(Binary("Lt", v4454, v4455))) return Value(false); v4454 = v4455; return Value(true); }())) ? Value("EAST") : Value("WEST"))});
}
if (static_cast<bool>(([&]() -> Value { auto v4456 = s->LocalAt(5); Value v4457; v4457 = s->LocalAt(3); if (!static_cast<bool>(Binary("NotEq", v4456, v4457))) return Value(false); v4456 = v4457; return Value(true); }()))) {
return List({(static_cast<bool>(([&]() -> Value { auto v4458 = s->LocalAt(5); Value v4459; v4459 = s->LocalAt(3); if (!static_cast<bool>(Binary("Lt", v4458, v4459))) return Value(false); v4458 = v4459; return Value(true); }())) ? Value("SOUTH") : Value("NORTH"))});
}
return Value{};
return {};
}
}  // namespace kagg::opponents::compiled
