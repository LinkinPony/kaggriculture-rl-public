// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_ddb9cde47d66efee28a0(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"action", "budget", "committed", "day", "deadline", "expected", "extra", "farm", "hour", "incoming", "initial", "last_native_hire", "market", "native", "o", "obs", "parent_hires", "planned", "result", "state", "step", "stock"};
s->PrepareSlots(s_names);
auto v6748 = ([&]() -> Value { auto fn6749 = s->Global("int"); Arguments args6750; args6750.Add(Get(s->LocalAt(15), Value("step")), false); return Call(c, fn6749, std::move(args6750)); }());
s->SetAt(20, v6748);
auto v6751 = ([&]() -> Value { auto v6752 = s->LocalAt(20); return Binary("FloorDiv", v6752, Value(int64_t{24})); }());
s->SetAt(3, v6751);
auto v6753 = ([&]() -> Value { auto v6754 = s->LocalAt(20); return Binary("Mod", v6754, Value(int64_t{24})); }());
s->SetAt(8, v6753);
if (static_cast<bool>(([&]() -> Value { auto v6755 = ([&]() -> Value { auto fn6757 = PrepareDictionaryGet(s->LocalAt(19)); Arguments args6758; args6758.Add(Value("requested_day"), false); return CallDictionaryGet(c, fn6757, std::move(args6758)); }()); Value v6756; v6756 = s->LocalAt(3); if (!static_cast<bool>(Binary("Eq", v6755, v6756))) return Value(false); v6755 = v6756; return Value(true); }()))) {
return s->LocalAt(0);
}
auto v6759 = ([&]() -> Value { auto fn6760 = PrepareDictionaryGet(s->LocalAt(19)); Arguments args6761; args6761.Add(Value("committed"), false); return CallDictionaryGet(c, fn6760, std::move(args6761)); }());
s->SetAt(2, v6759);
if (static_cast<bool>(([&]() -> Value { auto v6762 = Unary("Not", s->LocalAt(2)); if (!static_cast<bool>(v6762)) return v6762; v6762 = ([&]() -> Value { auto v6763 = ([&]() -> Value { auto v6764 = s->LocalAt(8); Value v6765; v6765 = Value(int64_t{1}); if (!static_cast<bool>(Binary("Gt", v6764, v6765))) return Value(false); v6764 = v6765; return Value(true); }()); if (static_cast<bool>(v6763)) return v6763; v6763 = ([&]() -> Value { auto v6766 = s->LocalAt(3); Value v6767; v6767 = Value(int64_t{12}); if (!static_cast<bool>(Binary("NotEq", v6766, v6767))) return Value(false); v6766 = v6767; return Value(true); }()); if (static_cast<bool>(v6763)) return v6763; v6763 = Unary("Not", ([&]() -> Value { auto fn6768 = s->Global("_v233_eligible"); Arguments args6769; args6769.positional.reserve(2); args6769.Add(s->LocalAt(15), false); args6769.Add(s->LocalAt(13), false); return Call(c, fn6768, std::move(args6769)); }())); return v6763; }()); return v6762; }()))) {
return s->LocalAt(0);
}
auto v6770 = ([&]() -> Value { auto fn6771 = s->Global("_v219_native_day"); Arguments args6772; args6772.positional.reserve(2); args6772.Add(s->LocalAt(13), false); args6772.Add(s->LocalAt(3), false); return Call(c, fn6771, std::move(args6772)); }());
s->SetAt(17, v6770);
auto v6773 = (static_cast<bool>(s->LocalAt(2)) ? Value(int64_t{2}) : Value(int64_t{1}));
s->SetAt(4, v6773);
if (static_cast<bool>(s->LocalAt(2))) {
auto v6774 = ([&]() -> Value { auto fn6775 = s->Global("max"); Arguments args6776; args6776.Add(([&]() -> Value { auto comp6777 = std::make_shared<Scope>(); comp6777->globals = s->globals; comp6777->parent = s; static constexpr const char* comp6777_names[] = {"a", "h"}; comp6777->PrepareSlots(comp6777_names); auto result6778 = List(); for (const auto& item6779 : Iterate(([&]() -> Value { auto fn6780 = s->Global("enumerate"); Arguments args6781; args6781.Add(s->LocalAt(17), false); return Call(c, fn6780, std::move(args6781)); }()))) { auto unpack6782 = Iterate(item6779); ValidateUnpack(unpack6782, 2, false); comp6777->SetAt(1, unpack6782.at(0)); comp6777->SetAt(0, unpack6782.at(1)); if (!static_cast<bool>(([&]() -> Value { auto comp6783 = std::make_shared<Scope>(); comp6783->globals = comp6777->globals; comp6783->parent = comp6777; static constexpr const char* comp6783_names[] = {"o"}; comp6783->PrepareSlots(comp6783_names); auto result6784 = List(); for (const auto& item6785 : Iterate(([&]() -> Value { auto fn6786 = PrepareDictionaryGet(comp6777->LocalAt(0)); Arguments args6787; args6787.positional.reserve(2); args6787.Add(Value("market"), false); args6787.Add(List({}), false); return CallDictionaryGet(c, fn6786, std::move(args6787)); }()))) { comp6783->SetAt(0, item6785); if (static_cast<bool>(([&]() -> Value { auto v6788 = comp6783->LocalAt(0); if (!static_cast<bool>(v6788)) return v6788; v6788 = ([&]() -> Value { auto v6789 = Get(comp6783->LocalAt(0), Value(int64_t{0})); Value v6790; v6790 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v6789, v6790))) return Value(false); v6789 = v6790; return Value(true); }()); return v6788; }()))) return Value(true); } return Value(false); }()))) continue; result6778.node()->sequence.push_back(comp6777->LocalAt(1)); } return result6778; }()), false); args6776.Keyword("default", Value(int64_t{0})); return Call(c, fn6775, std::move(args6776)); }());
s->SetAt(11, v6774);
if (static_cast<bool>(([&]() -> Value { auto v6791 = Value(int64_t{2}); Value v6792; v6792 = s->LocalAt(11); if (!static_cast<bool>(Binary("Lt", v6791, v6792))) return Value(false); v6791 = v6792; v6792 = Value(int64_t{6}); if (!static_cast<bool>(Binary("LtE", v6791, v6792))) return Value(false); v6791 = v6792; return Value(true); }()))) {
auto v6793 = Value(int64_t{6});
s->SetAt(4, v6793);
}
}
if (static_cast<bool>(([&]() -> Value { auto v6794 = s->LocalAt(8); Value v6795; v6795 = s->LocalAt(4); if (!static_cast<bool>(Binary("Gt", v6794, v6795))) return Value(false); v6794 = v6795; return Value(true); }()))) {
return s->LocalAt(0);
}
if (static_cast<bool>(([&]() -> Value { auto comp6796 = std::make_shared<Scope>(); comp6796->globals = s->globals; comp6796->parent = s; static constexpr const char* comp6796_names[] = {"a", "o"}; comp6796->PrepareSlots(comp6796_names); auto result6797 = List(); for (const auto& item6798 : Iterate(Slice(s->LocalAt(17), ([&]() -> Value { auto v6799 = s->LocalAt(8); return Binary("Add", v6799, Value(int64_t{1})); }()), Value{}, Value{}))) { comp6796->SetAt(0, item6798); for (const auto& item6800 : Iterate(([&]() -> Value { auto fn6801 = PrepareDictionaryGet(comp6796->LocalAt(0)); Arguments args6802; args6802.positional.reserve(2); args6802.Add(Value("market"), false); args6802.Add(List({}), false); return CallDictionaryGet(c, fn6801, std::move(args6802)); }()))) { comp6796->SetAt(1, item6800); if (static_cast<bool>(([&]() -> Value { auto v6803 = comp6796->LocalAt(1); if (!static_cast<bool>(v6803)) return v6803; v6803 = ([&]() -> Value { auto v6804 = Get(comp6796->LocalAt(1), Value(int64_t{0})); Value v6805; v6805 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v6804, v6805))) return Value(false); v6804 = v6805; return Value(true); }()); return v6803; }()))) return Value(true); } } return Value(false); }()))) {
return s->LocalAt(0);
}
auto v6806 = Get(Get(s->LocalAt(15), Value("farms")), Get(s->LocalAt(15), Value("player")));
s->SetAt(7, v6806);
auto v6807 = ([&]() -> Value { auto fn6808 = PrepareDictionaryGet(s->LocalAt(0)); Arguments args6809; args6809.positional.reserve(2); args6809.Add(Value("market"), false); args6809.Add(List({}), false); return CallDictionaryGet(c, fn6808, std::move(args6809)); }());
s->SetAt(12, v6807);
auto v6810 = ([&]() -> Value { auto fn6811 = s->Global("sum"); Arguments args6812; args6812.Add(([&]() -> Value { auto comp6813 = std::make_shared<Scope>(); comp6813->globals = s->globals; comp6813->parent = s; static constexpr const char* comp6813_names[] = {"o"}; comp6813->PrepareSlots(comp6813_names); auto result6814 = List(); for (const auto& item6815 : Iterate(s->LocalAt(12))) { comp6813->SetAt(0, item6815); result6814.node()->sequence.push_back(([&]() -> Value { auto v6816 = ([&]() -> Value { auto fn6817 = comp6813->Global("bool"); Arguments args6818; args6818.Add(comp6813->LocalAt(0), false); return Call(c, fn6817, std::move(args6818)); }()); if (!static_cast<bool>(v6816)) return v6816; v6816 = ([&]() -> Value { auto v6819 = Get(comp6813->LocalAt(0), Value(int64_t{0})); Value v6820; v6820 = Value("HIRE"); if (!static_cast<bool>(Binary("Eq", v6819, v6820))) return Value(false); v6819 = v6820; return Value(true); }()); return v6816; }())); } return result6814; }()), false); return Call(c, fn6811, std::move(args6812)); }());
s->SetAt(16, v6810);
auto v6821 = ([&]() -> Value { auto fn6822 = s->Global("max"); Arguments args6823; args6823.Add(([&]() -> Value { auto comp6824 = std::make_shared<Scope>(); comp6824->globals = s->globals; comp6824->parent = s; static constexpr const char* comp6824_names[] = {"a"}; comp6824->PrepareSlots(comp6824_names); auto result6825 = List(); for (const auto& item6826 : Iterate(s->LocalAt(17))) { comp6824->SetAt(0, item6826); result6825.node()->sequence.push_back(([&]() -> Value { auto fn6827 = comp6824->Global("len"); Arguments args6828; args6828.Add(([&]() -> Value { auto fn6829 = PrepareDictionaryGet(comp6824->LocalAt(0)); Arguments args6830; args6830.positional.reserve(2); args6830.Add(Value("hands"), false); args6830.Add(List({}), false); return CallDictionaryGet(c, fn6829, std::move(args6830)); }()), false); return Call(c, fn6827, std::move(args6828)); }())); } return result6825; }()), false); return Call(c, fn6822, std::move(args6823)); }());
s->SetAt(5, v6821);
if (static_cast<bool>(([&]() -> Value { auto v6831 = ([&]() -> Value { auto v6833 = ([&]() -> Value { auto fn6834 = s->Global("len"); Arguments args6835; args6835.Add(Get(s->LocalAt(7), Value("hands")), false); return Call(c, fn6834, std::move(args6835)); }()); return Binary("Add", v6833, s->LocalAt(16)); }()); Value v6832; v6832 = s->LocalAt(5); if (!static_cast<bool>(Binary("NotEq", v6831, v6832))) return Value(false); v6831 = v6832; return Value(true); }()))) {
return s->LocalAt(0);
}
auto v6836 = Unary("Not", ([&]() -> Value { auto fn6837 = PrepareDictionaryGet(s->LocalAt(19)); Arguments args6838; args6838.Add(Value("committed"), false); return CallDictionaryGet(c, fn6837, std::move(args6838)); }()));
s->SetAt(10, v6836);
auto v6839 = ([&]() -> Value { auto v6840 = (static_cast<bool>(s->LocalAt(10)) ? List({List({Value("BUY_LAND")}), List({Value("BUY_ANIMAL"), Value("SHEEP"), Value(int64_t{6})})}) : List({})); return Binary("Add", v6840, List({List({Value("BUY_PRODUCT"), Value("WHEAT"), Value(int64_t{6})}), List({Value("HIRE")}), List({Value("HIRE")})})); }());
s->SetAt(6, v6839);
if (static_cast<bool>(([&]() -> Value { auto v6841 = ([&]() -> Value { auto v6843 = ([&]() -> Value { auto fn6844 = s->Global("len"); Arguments args6845; args6845.Add(s->LocalAt(12), false); return Call(c, fn6844, std::move(args6845)); }()); return Binary("Add", v6843, ([&]() -> Value { auto fn6846 = s->Global("len"); Arguments args6847; args6847.Add(s->LocalAt(6), false); return Call(c, fn6846, std::move(args6847)); }())); }()); Value v6842; v6842 = s->Global("MAX_ORDERS"); if (!static_cast<bool>(Binary("Gt", v6841, v6842))) return Value(false); v6841 = v6842; return Value(true); }()))) {
return s->LocalAt(0);
}
auto v6848 = ([&]() -> Value { auto fn6849 = s->Global("projected_shed"); Arguments args6850; args6850.positional.reserve(2); args6850.Add(s->LocalAt(0), false); args6850.Add(([&]() -> Value { auto fn6851 = s->Global("FarmView"); Arguments args6852; args6852.Add(s->LocalAt(15), false); return Call(c, fn6851, std::move(args6852)); }()), false); return Call(c, fn6849, std::move(args6850)); }());
s->SetAt(21, v6848);
auto v6853 = ([&]() -> Value { auto v6854 = Value(int64_t{6}); return Binary("Add", v6854, ([&]() -> Value { auto v6855 = Value(int64_t{6}); return Binary("Mult", v6855, s->LocalAt(10)); }())); }());
s->SetAt(9, v6853);
auto v6856 = ([&]() -> Value { auto v6857 = ([&]() -> Value { auto v6858 = Value(int64_t{7000}); return Binary("Mult", v6858, s->LocalAt(10)); }()); return Binary("Add", v6857, ([&]() -> Value { auto v6859 = Value(int64_t{6}); return Binary("Mult", v6859, ([&]() -> Value { auto v6860 = ([&]() -> Value { auto fn6861 = s->Global("int"); Arguments args6862; args6862.Add(Get(Get(Get(s->LocalAt(15), Value("market")), Value("prices")), Value("WHEAT")), false); return Call(c, fn6861, std::move(args6862)); }()); return Binary("Add", v6860, Value(int64_t{10})); }())); }())); }());
s->SetAt(1, v6856);
auto v6863 = s->LocalAt(1);
s->SetAt(1, Inplace("Add", v6863, ([&]() -> Value { auto fn6864 = s->Global("sum"); Arguments args6865; args6865.Add(([&]() -> Value { auto comp6866 = std::make_shared<Scope>(); comp6866->globals = s->globals; comp6866->parent = s; static constexpr const char* comp6866_names[] = {"n"}; comp6866->PrepareSlots(comp6866_names); auto result6867 = List(); for (const auto& item6868 : Iterate(([&]() -> Value { auto fn6869 = s->Global("range"); Arguments args6870; args6870.positional.reserve(2); args6870.Add(Get(s->LocalAt(7), Value("hires_today")), false); args6870.Add(([&]() -> Value { auto v6871 = ([&]() -> Value { auto v6872 = Get(s->LocalAt(7), Value("hires_today")); return Binary("Add", v6872, s->LocalAt(16)); }()); return Binary("Add", v6871, Value(int64_t{2})); }()), false); return Call(c, fn6869, std::move(args6870)); }()))) { comp6866->SetAt(0, item6868); result6867.node()->sequence.push_back(([&]() -> Value { auto fn6873 = comp6866->Global("_v219_fib"); Arguments args6874; args6874.Add(comp6866->LocalAt(0), false); return Call(c, fn6873, std::move(args6874)); }())); } return result6867; }()), false); return Call(c, fn6864, std::move(args6865)); }())));
for (const auto& item6875 : Iterate(s->LocalAt(12))) {
s->SetAt(14, item6875);
if (static_cast<bool>(Unary("Not", s->LocalAt(14)))) {
continue;
}
if (static_cast<bool>(([&]() -> Value { auto v6876 = Get(s->LocalAt(14), Value(int64_t{0})); Value v6877; v6877 = Value("BUY_LAND"); if (!static_cast<bool>(Binary("Eq", v6876, v6877))) return Value(false); v6876 = v6877; return Value(true); }()))) {
return s->LocalAt(0);
}
if (static_cast<bool>(([&]() -> Value { auto v6878 = Get(s->LocalAt(14), Value(int64_t{0})); Value v6879; v6879 = Value("BUY_PRODUCT"); if (!static_cast<bool>(Binary("Eq", v6878, v6879))) return Value(false); v6878 = v6879; return Value(true); }()))) {
auto v6880 = s->LocalAt(9);
s->SetAt(9, Inplace("Add", v6880, ([&]() -> Value { auto fn6881 = s->Global("int"); Arguments args6882; args6882.Add(Get(s->LocalAt(14), Value(int64_t{2})), false); return Call(c, fn6881, std::move(args6882)); }())));
auto v6883 = s->LocalAt(1);
s->SetAt(1, Inplace("Add", v6883, ([&]() -> Value { auto v6884 = ([&]() -> Value { auto fn6885 = s->Global("int"); Arguments args6886; args6886.Add(Get(s->LocalAt(14), Value(int64_t{2})), false); return Call(c, fn6885, std::move(args6886)); }()); return Binary("Mult", v6884, ([&]() -> Value { auto v6887 = ([&]() -> Value { auto fn6888 = s->Global("int"); Arguments args6889; args6889.Add(Get(Get(Get(s->LocalAt(15), Value("market")), Value("prices")), Get(s->LocalAt(14), Value(int64_t{1}))), false); return Call(c, fn6888, std::move(args6889)); }()); return Binary("Add", v6887, Value(int64_t{10})); }())); }())));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v6890 = Get(s->LocalAt(14), Value(int64_t{0})); Value v6891; v6891 = Value("BUY_ANIMAL"); if (!static_cast<bool>(Binary("Eq", v6890, v6891))) return Value(false); v6890 = v6891; return Value(true); }()))) {
auto v6892 = s->LocalAt(9);
s->SetAt(9, Inplace("Add", v6892, ([&]() -> Value { auto fn6893 = s->Global("int"); Arguments args6894; args6894.Add(Get(s->LocalAt(14), Value(int64_t{2})), false); return Call(c, fn6893, std::move(args6894)); }())));
auto v6895 = s->LocalAt(1);
s->SetAt(1, Inplace("Add", v6895, ([&]() -> Value { auto v6896 = ([&]() -> Value { auto fn6897 = s->Global("int"); Arguments args6898; args6898.Add(Get(s->LocalAt(14), Value(int64_t{2})), false); return Call(c, fn6897, std::move(args6898)); }()); return Binary("Mult", v6896, Get(([&]() -> Value { auto dict6899 = Dict(); auto key6900 = Value("SHEEP"); Put(dict6899, key6900, Value(int64_t{500})); auto key6901 = Value("COW"); Put(dict6899, key6901, Value(int64_t{400})); auto key6902 = Value("GOOSE"); Put(dict6899, key6902, Value(int64_t{300})); return dict6899; }()), Get(s->LocalAt(14), Value(int64_t{1})))); }())));
}
else {
if (static_cast<bool>(([&]() -> Value { auto v6903 = Get(s->LocalAt(14), Value(int64_t{0})); Value v6904; v6904 = Value("BUY_SEED"); if (!static_cast<bool>(Binary("Eq", v6903, v6904))) return Value(false); v6903 = v6904; return Value(true); }()))) {
auto v6905 = s->LocalAt(1);
s->SetAt(1, Inplace("Add", v6905, ([&]() -> Value { auto v6906 = ([&]() -> Value { auto fn6907 = s->Global("int"); Arguments args6908; args6908.Add(Get(s->LocalAt(14), Value(int64_t{2})), false); return Call(c, fn6907, std::move(args6908)); }()); return Binary("Mult", v6906, Get(([&]() -> Value { auto dict6909 = Dict(); auto key6910 = Value("WHEAT"); Put(dict6909, key6910, Value(int64_t{10})); auto key6911 = Value("CARROT"); Put(dict6909, key6911, Value(int64_t{20})); auto key6912 = Value("TOMATO"); Put(dict6909, key6912, Value(int64_t{50})); auto key6913 = Value("STRAWBERRY"); Put(dict6909, key6913, Value(int64_t{100})); auto key6914 = Value("MELON"); Put(dict6909, key6914, Value(int64_t{80})); return dict6909; }()), Get(s->LocalAt(14), Value(int64_t{1})))); }())));
}
}
}
}
if (static_cast<bool>(([&]() -> Value { auto v6915 = ([&]() -> Value { auto v6917 = ([&]() -> Value { auto fn6918 = s->Global("sum"); Arguments args6919; args6919.Add(([&]() -> Value { auto fn6920 = Attribute(s->LocalAt(21), "values"); Arguments args6921; return Call(c, fn6920, std::move(args6921)); }()), false); return Call(c, fn6918, std::move(args6919)); }()); return Binary("Add", v6917, s->LocalAt(9)); }()); Value v6916; v6916 = Value(int64_t{100}); if (!static_cast<bool>(Binary("Gt", v6915, v6916))) return Value(false); v6915 = v6916; return Value(true); }()))) {
auto v6922 = s->Global("_V233_REPORT");
auto v6923 = Value("sheep_capacity_declines");
auto v6924 = Get(v6922, v6923);
Put(v6922, v6923, Inplace("Add", v6924, Value(int64_t{1})));
return s->LocalAt(0);
}
if (static_cast<bool>(([&]() -> Value { auto v6925 = Get(s->LocalAt(7), Value("money")); Value v6926; v6926 = ([&]() -> Value { auto v6927 = s->LocalAt(1); return Binary("Add", v6927, (static_cast<bool>(s->LocalAt(10)) ? Value(int64_t{3000}) : Value(int64_t{1000}))); }()); if (!static_cast<bool>(Binary("Lt", v6925, v6926))) return Value(false); v6925 = v6926; return Value(true); }()))) {
auto v6928 = s->Global("_V233_REPORT");
auto v6929 = Value("sheep_budget_declines");
auto v6930 = Get(v6928, v6929);
Put(v6928, v6929, Inplace("Add", v6930, Value(int64_t{1})));
return s->LocalAt(0);
}
auto v6931 = s->LocalAt(3);
Put(s->LocalAt(19), Value("requested_day"), v6931);
auto v6932 = ([&]() -> Value { auto dict6933 = Dict(); auto key6934 = Value("first"); Put(dict6933, key6934, ([&]() -> Value { auto v6935 = s->LocalAt(5); return Binary("Add", v6935, Value(int64_t{1})); }())); auto key6936 = Value("initial"); Put(dict6933, key6936, s->LocalAt(10)); return dict6933; }());
Put(s->LocalAt(19), Value("pending"), v6932);
auto v6937 = s->Global("_V233_REPORT");
auto v6938 = Value("sheep_hire_requests");
auto v6939 = Get(v6937, v6938);
Put(v6937, v6938, Inplace("Add", v6939, Value(int64_t{2})));
auto v6940 = s->Global("_V233_REPORT");
auto v6941 = Value("sheep_feed_buy_requests");
auto v6942 = Get(v6940, v6941);
Put(v6940, v6941, Inplace("Add", v6942, Value(int64_t{6})));
if (static_cast<bool>(s->LocalAt(10))) {
auto v6943 = s->Global("_V233_REPORT");
auto v6944 = Value("sheep_commit_requests");
auto v6945 = Get(v6943, v6944);
Put(v6943, v6944, Inplace("Add", v6945, Value(int64_t{1})));
}
auto v6946 = ([&]() -> Value { auto fn6947 = Attribute(s->Global("copy"), "deepcopy"); Arguments args6948; args6948.Add(s->LocalAt(0), false); return Call(c, fn6947, std::move(args6948)); }());
s->SetAt(18, v6946);
auto v6949 = ([&]() -> Value { auto v6950 = s->LocalAt(12); return Binary("Add", v6950, s->LocalAt(6)); }());
Put(s->LocalAt(18), Value("market"), v6949);
return s->LocalAt(18);
return {};
}
}  // namespace kagg::opponents::compiled
