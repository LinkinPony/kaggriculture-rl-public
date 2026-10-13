// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Initialize(const std::string& kind, Context& c, Value globals) {
auto scope = Module(globals);
if (kind == "ahmed_v45") return Init_0212d8956ca9adfa4244(c, scope);
if (kind == "metacounter_r1") return Init_8aba67b944e7549ca085(c, scope);
if (kind == "shop_router_0913") return Init_2c06a380e1db3bf8aa56(c, scope);
if (kind == "rayk_v38_low_pressure") return Init_f1a2dded542068f3234e(c, scope);
if (kind == "farming_v4_0914") return Init_c8546a5ebe1b740fcdeb(c, scope);
if (kind == "ahmed_v53") return Init_b243d3022a3237cb6b42(c, scope);
if (kind == "thomas_metav4") return Init_b756f27a2020228c3d82(c, scope);
throw PortError("unknown compiled policy");
}
}
