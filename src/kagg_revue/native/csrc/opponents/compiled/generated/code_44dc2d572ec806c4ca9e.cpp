// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_44dc2d572ec806c4ca9e(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"care", "day", "first", "interval", "next_use", "pending", "produces", "tile", "tomorrow"};
s->PrepareSlots(s_names);
auto v9900 = Get(s->Global("_R88_ANIMAL_DAYS"), Get(s->LocalAt(7), Value("animal")));
auto unpack9901 = Iterate(v9900);
ValidateUnpack(unpack9901, 2, false);
s->SetAt(2, unpack9901.at(0));
s->SetAt(3, unpack9901.at(1));
auto v9902 = s->LocalAt(2);
s->SetAt(2, Inplace("Add", v9902, ([&]() -> Value { auto fn9903 = s->Global("int"); Arguments args9904; args9904.Add(Get(s->LocalAt(7), Value("placed_day")), false); return Call(c, fn9903, std::move(args9904)); }())));
auto v9905 = ([&]() -> Value { auto v9906 = s->LocalAt(1); return Binary("Add", v9906, Value(int64_t{1})); }());
s->SetAt(8, v9905);
auto v9907 = ([&]() -> Value { auto v9908 = ([&]() -> Value { auto v9909 = s->LocalAt(8); Value v9910; v9910 = s->LocalAt(2); if (!static_cast<bool>(Binary("GtE", v9909, v9910))) return Value(false); v9909 = v9910; return Value(true); }()); if (!static_cast<bool>(v9908)) return v9908; v9908 = ([&]() -> Value { auto v9911 = ([&]() -> Value { auto v9913 = ([&]() -> Value { auto v9914 = s->LocalAt(8); return Binary("Sub", v9914, s->LocalAt(2)); }()); return Binary("Mod", v9913, s->LocalAt(3)); }()); Value v9912; v9912 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v9911, v9912))) return Value(false); v9911 = v9912; return Value(true); }()); return v9908; }());
s->SetAt(6, v9907);
auto v9915 = ([&]() -> Value { auto fn9916 = s->Global("max"); Arguments args9917; args9917.positional.reserve(2); args9917.Add(Value(int64_t{0}), false); args9917.Add(([&]() -> Value { auto fn9918 = s->Global("int"); Arguments args9919; args9919.Add(([&]() -> Value { auto fn9920 = PrepareDictionaryGet(s->LocalAt(7)); Arguments args9921; args9921.positional.reserve(2); args9921.Add(Value("pending_care_bonus"), false); args9921.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn9920, std::move(args9921)); }()), false); return Call(c, fn9918, std::move(args9919)); }()), false); return Call(c, fn9916, std::move(args9917)); }());
s->SetAt(5, v9915);
if (static_cast<bool>(([&]() -> Value { auto v9922 = s->Global("_R88_PHASE"); if (!static_cast<bool>(v9922)) return v9922; v9922 = Unary("Not", s->LocalAt(6)); return v9922; }()))) {
auto v9923 = Value(int64_t{0});
s->SetAt(5, v9923);
}
auto v9924 = Value(int64_t{1});
s->SetAt(0, v9924);
if (static_cast<bool>(s->Global("_R88_HORIZON"))) {
auto v9925 = s->LocalAt(2);
s->SetAt(4, v9925);
if (static_cast<bool>(([&]() -> Value { auto v9926 = s->LocalAt(4); Value v9927; v9927 = s->LocalAt(8); if (!static_cast<bool>(Binary("LtE", v9926, v9927))) return Value(false); v9926 = v9927; return Value(true); }()))) {
auto v9928 = s->LocalAt(4);
s->SetAt(4, Inplace("Add", v9928, ([&]() -> Value { auto v9929 = ([&]() -> Value { auto v9930 = ([&]() -> Value { auto v9931 = ([&]() -> Value { auto v9932 = s->LocalAt(8); return Binary("Sub", v9932, s->LocalAt(4)); }()); return Binary("FloorDiv", v9931, s->LocalAt(3)); }()); return Binary("Add", v9930, Value(int64_t{1})); }()); return Binary("Mult", v9929, s->LocalAt(3)); }())));
}
if (static_cast<bool>(([&]() -> Value { auto v9933 = s->LocalAt(4); Value v9934; v9934 = Value(int64_t{29}); if (!static_cast<bool>(Binary("Gt", v9933, v9934))) return Value(false); v9933 = v9934; return Value(true); }()))) {
auto v9935 = Value(int64_t{0});
s->SetAt(0, v9935);
}
}
return ([&]() -> Value { auto v9936 = s->LocalAt(5); return Binary("Add", v9936, s->LocalAt(0)); }());
return {};
}
}  // namespace kagg::opponents::compiled
