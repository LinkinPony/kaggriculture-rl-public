// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_c082d10755ad54a24a54(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"added", "best", "config", "farm", "obs", "offset", "prefix", "private", "projected", "row", "rows", "tail", "trial"};
s->PrepareSlots(s_names);
if (static_cast<bool>(([&]() -> Value { auto v16937 = ([&]() -> Value { auto v16938 = s->LocalAt(5); Value v16939; v16939 = Value(int64_t{0}); if (!static_cast<bool>(Binary("LtE", v16938, v16939))) return Value(false); v16938 = v16939; return Value(true); }()); if (static_cast<bool>(v16937)) return v16937; v16937 = Get(s->LocalAt(1), Value("overflow_units")); if (static_cast<bool>(v16937)) return v16937; v16937 = ([&]() -> Value { auto v16940 = ([&]() -> Value { auto fn16942 = s->Global("len"); Arguments args16943; args16943.Add(Get(s->LocalAt(1), Value("states")), false); return Call(c, fn16942, std::move(args16943)); }()); Value v16941; v16941 = ([&]() -> Value { auto v16944 = ([&]() -> Value { auto fn16945 = s->Global("len"); Arguments args16946; args16946.Add(s->LocalAt(12), false); return Call(c, fn16945, std::move(args16946)); }()); return Binary("Add", v16944, Value(int64_t{1})); }()); if (!static_cast<bool>(Binary("NotEq", v16940, v16941))) return Value(false); v16940 = v16941; return Value(true); }()); return v16937; }()))) {
return ([&]() -> Value { auto fn16947 = s->Global("simulate"); Arguments args16948; args16948.positional.reserve(3); args16948.Add(s->LocalAt(4), false); args16948.Add(s->LocalAt(2), false); args16948.Add(s->LocalAt(12), false); return Call(c, fn16947, std::move(args16948)); }());
}
auto v16949 = Get(Get(s->LocalAt(1), Value("states")), s->LocalAt(5));
auto unpack16950 = Iterate(v16949);
ValidateUnpack(unpack16950, 2, false);
s->SetAt(3, unpack16950.at(0));
s->SetAt(7, unpack16950.at(1));
auto v16951 = ([&]() -> Value { auto fn16952 = s->Global("dict"); Arguments args16953; args16953.Add(s->LocalAt(4), false); return Call(c, fn16952, std::move(args16953)); }());
s->SetAt(8, v16951);
auto v16954 = ([&]() -> Value { auto fn16955 = s->Global("list"); Arguments args16956; args16956.Add(([&]() -> Value { auto fn16957 = s->Global("_get"); Arguments args16958; args16958.positional.reserve(2); args16958.Add(s->LocalAt(4), false); args16958.Add(Value("farms"), false); return Call(c, fn16957, std::move(args16958)); }()), false); return Call(c, fn16955, std::move(args16956)); }());
Put(s->LocalAt(8), Value("farms"), v16954);
auto v16959 = s->LocalAt(3);
Put(Get(s->LocalAt(8), Value("farms")), ([&]() -> Value { auto fn16960 = s->Global("int"); Arguments args16961; args16961.Add(([&]() -> Value { auto fn16962 = s->Global("_get"); Arguments args16963; args16963.positional.reserve(3); args16963.Add(s->LocalAt(4), false); args16963.Add(Value("player"), false); args16963.Add(Value(int64_t{0}), false); return Call(c, fn16962, std::move(args16963)); }()), false); return Call(c, fn16960, std::move(args16961)); }()), v16959);
auto v16964 = s->LocalAt(7);
Put(s->LocalAt(8), Value("private"), v16964);
auto v16965 = ([&]() -> Value { auto v16966 = ([&]() -> Value { auto fn16967 = s->Global("int"); Arguments args16968; args16968.Add(([&]() -> Value { auto fn16969 = s->Global("_get"); Arguments args16970; args16970.positional.reserve(2); args16970.Add(s->LocalAt(4), false); args16970.Add(Value("step"), false); return Call(c, fn16969, std::move(args16970)); }()), false); return Call(c, fn16967, std::move(args16968)); }()); return Binary("Add", v16966, s->LocalAt(5)); }());
Put(s->LocalAt(8), Value("step"), v16965);
auto v16971 = ([&]() -> Value { auto fn16972 = s->Global("simulate"); Arguments args16973; args16973.positional.reserve(3); args16973.Add(s->LocalAt(8), false); args16973.Add(s->LocalAt(2), false); args16973.Add(Slice(s->LocalAt(12), s->LocalAt(5), Value{}, Value{}), false); return Call(c, fn16972, std::move(args16973)); }());
s->SetAt(11, v16971);
auto v16974 = Get(Get(s->LocalAt(1), Value("rows")), ([&]() -> Value { auto v16975 = s->LocalAt(5); return Binary("Sub", v16975, Value(int64_t{1})); }()));
s->SetAt(6, v16974);
s->SetAt(0, Define(&Code_8d54b023e81e6e3761ff, s, Signature{{"a", "b"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"a", "b", "key", "result", "value"}; return names; }())}, true, "added"));
s->definitions.push_back("added");
auto v16987 = ([&]() -> Value { auto fn16988 = s->Global("list"); Arguments args16989; args16989.Add(Slice(Get(s->LocalAt(1), Value("rows")), Value{}, s->LocalAt(5), Value{}), false); return Call(c, fn16988, std::move(args16989)); }());
s->SetAt(10, v16987);
for (const auto& item16990 : Iterate(Get(s->LocalAt(11), Value("rows")))) {
s->SetAt(9, item16990);
auto v16991 = ([&]() -> Value { auto fn16992 = s->Global("dict"); Arguments args16993; args16993.Add(s->LocalAt(9), false); return Call(c, fn16992, std::move(args16993)); }());
s->SetAt(9, v16991);
auto v16994 = ([&]() -> Value { auto fn16995 = s->LocalAt(0); Arguments args16996; args16996.positional.reserve(2); args16996.Add(Get(s->LocalAt(6), Value("sold")), false); args16996.Add(Get(s->LocalAt(9), Value("sold")), false); return Call(c, fn16995, std::move(args16996)); }());
Put(s->LocalAt(9), Value("sold"), v16994);
auto v16997 = ([&]() -> Value { auto comp16998 = std::make_shared<Scope>(); comp16998->globals = s->globals; comp16998->parent = s; static constexpr const char* comp16998_names[] = {"a", "b"}; comp16998->PrepareSlots(comp16998_names); auto result16999 = List(); for (const auto& item17000 : Iterate(([&]() -> Value { auto fn17001 = s->Global("zip"); Arguments args17002; args17002.positional.reserve(2); args17002.Add(Get(s->LocalAt(6), Value("deposited_by_actor")), false); args17002.Add(Get(s->LocalAt(9), Value("deposited_by_actor")), false); return Call(c, fn17001, std::move(args17002)); }()))) { auto unpack17003 = Iterate(item17000); ValidateUnpack(unpack17003, 2, false); comp16998->SetAt(0, unpack17003.at(0)); comp16998->SetAt(1, unpack17003.at(1)); result16999.node()->sequence.push_back(([&]() -> Value { auto fn17004 = comp16998->Captured("added"); Arguments args17005; args17005.positional.reserve(2); args17005.Add(comp16998->LocalAt(0), false); args17005.Add(comp16998->LocalAt(1), false); return Call(c, fn17004, std::move(args17005)); }())); } return result16999; }());
Put(s->LocalAt(9), Value("deposited_by_actor"), v16997);
(void)([&]() -> Value { auto fn17006 = Attribute(s->LocalAt(10), "append"); Arguments args17007; args17007.Add(s->LocalAt(9), false); return Call(c, fn17006, std::move(args17007)); }());
}
auto v17008 = s->LocalAt(10);
Put(s->LocalAt(11), Value("rows"), v17008);
auto v17009 = ([&]() -> Value { auto fn17010 = s->LocalAt(0); Arguments args17011; args17011.positional.reserve(2); args17011.Add(Get(s->LocalAt(6), Value("sold")), false); args17011.Add(Get(s->LocalAt(11), Value("sold")), false); return Call(c, fn17010, std::move(args17011)); }());
Put(s->LocalAt(11), Value("sold"), v17009);
auto v17012 = ([&]() -> Value { auto v17013 = ([&]() -> Value { auto comp17014 = std::make_shared<Scope>(); comp17014->globals = s->globals; comp17014->parent = s; static constexpr const char* comp17014_names[] = {"e"}; comp17014->PrepareSlots(comp17014_names); auto result17015 = List(); for (const auto& item17016 : Iterate(Get(s->LocalAt(1), Value("events")))) { comp17014->SetAt(0, item17016); if (!static_cast<bool>(([&]() -> Value { auto v17017 = Get(comp17014->LocalAt(0), Value("offset")); Value v17018; v17018 = comp17014->Captured("offset"); if (!static_cast<bool>(Binary("Lt", v17017, v17018))) return Value(false); v17017 = v17018; return Value(true); }()))) continue; result17015.node()->sequence.push_back(comp17014->LocalAt(0)); } return result17015; }()); return Binary("Add", v17013, ([&]() -> Value { auto comp17019 = std::make_shared<Scope>(); comp17019->globals = s->globals; comp17019->parent = s; static constexpr const char* comp17019_names[] = {"e"}; comp17019->PrepareSlots(comp17019_names); auto result17020 = List(); for (const auto& item17021 : Iterate(Get(s->LocalAt(11), Value("events")))) { comp17019->SetAt(0, item17021); result17020.node()->sequence.push_back(([&]() -> Value { auto fn17022 = comp17019->Global("dict"); Arguments args17023; args17023.Add(comp17019->LocalAt(0), false); args17023.Keyword("offset", ([&]() -> Value { auto v17024 = Get(comp17019->LocalAt(0), Value("offset")); return Binary("Add", v17024, comp17019->Captured("offset")); }())); return Call(c, fn17022, std::move(args17023)); }())); } return result17020; }())); }());
Put(s->LocalAt(11), Value("events"), v17012);
auto v17025 = ([&]() -> Value { auto v17026 = ([&]() -> Value { auto fn17027 = s->Global("_clone_schedule"); Arguments args17028; args17028.Add(Slice(s->LocalAt(12), Value{}, s->LocalAt(5), Value{}), false); return Call(c, fn17027, std::move(args17028)); }()); return Binary("Add", v17026, Get(s->LocalAt(11), Value("actions"))); }());
Put(s->LocalAt(11), Value("actions"), v17025);
return s->LocalAt(11);
return {};
}
}  // namespace kagg::opponents::compiled
