// Generated from authenticated public notebook source; do not edit.
#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
Value Code_a5e232a77a3dc5b09222(Context& c, const ScopePtr& s) {
static constexpr const char* s_names[] = {"_", "action", "actor", "all_commands", "amount", "before_inv", "before_shed", "blocked", "cap", "command", "config", "delta", "demand", "deposited", "detailed", "events", "executed", "farm", "farm0", "final_liquidate", "inv", "item", "n", "obs", "offset", "order_cap", "overflow", "pos", "pre_market", "preserve_final_commands", "prices", "private", "private0", "quantity", "requested", "rows", "schedule", "size", "snapshots", "sold", "step", "t", "turns", "xy"};
s->PrepareSlots(s_names);
auto v2779 = ([&]() -> Value { auto fn2780 = s->Global("_settings"); Arguments args2781; args2781.Add(s->LocalAt(10), false); return Call(c, fn2780, std::move(args2781)); }());
auto unpack2782 = Iterate(v2779);
ValidateUnpack(unpack2782, 4, false);
s->SetAt(37, unpack2782.at(0));
s->SetAt(42, unpack2782.at(1));
s->SetAt(8, unpack2782.at(2));
s->SetAt(25, unpack2782.at(3));
auto v2783 = ([&]() -> Value { auto fn2784 = s->Global("int"); Arguments args2785; args2785.Add(([&]() -> Value { auto fn2786 = s->Global("_get"); Arguments args2787; args2787.positional.reserve(3); args2787.Add(s->LocalAt(23), false); args2787.Add(Value("step"), false); args2787.Add(Unary("USub", Value(int64_t{1})), false); return Call(c, fn2786, std::move(args2787)); }()), false); return Call(c, fn2784, std::move(args2785)); }());
s->SetAt(40, v2783);
if (static_cast<bool>(([&]() -> Value { auto v2788 = ([&]() -> Value { auto v2789 = s->LocalAt(40); Value v2790; v2790 = s->Global("START"); if (!static_cast<bool>(Binary("Lt", v2789, v2790))) return Value(false); v2789 = v2790; return Value(true); }()); if (static_cast<bool>(v2788)) return v2788; v2788 = ([&]() -> Value { auto v2791 = ([&]() -> Value { auto v2793 = ([&]() -> Value { auto v2794 = s->LocalAt(40); return Binary("Add", v2794, ([&]() -> Value { auto fn2795 = s->Global("len"); Arguments args2796; args2796.Add(s->LocalAt(36), false); return Call(c, fn2795, std::move(args2796)); }())); }()); return Binary("Sub", v2793, Value(int64_t{1})); }()); Value v2792; v2792 = s->Global("FINAL"); if (!static_cast<bool>(Binary("Gt", v2791, v2792))) return Value(false); v2791 = v2792; return Value(true); }()); if (static_cast<bool>(v2788)) return v2788; v2788 = Unary("Not", s->LocalAt(36)); return v2788; }()))) {
Raise(([&]() -> Value { auto fn2797 = s->Global("Unsupported"); Arguments args2798; args2798.Add(Value("outside 712..718; no day boundary or terminal auto-drop"), false); return Call(c, fn2797, std::move(args2798)); }()));
}
if (static_cast<bool>(([&]() -> Value { auto comp2799 = std::make_shared<Scope>(); comp2799->globals = s->globals; comp2799->parent = s; static constexpr const char* comp2799_names[] = {"t"}; comp2799->PrepareSlots(comp2799_names); auto result2800 = List(); for (const auto& item2801 : Iterate(([&]() -> Value { auto fn2802 = s->Global("range"); Arguments args2803; args2803.positional.reserve(2); args2803.Add(s->LocalAt(40), false); args2803.Add(([&]() -> Value { auto v2804 = s->LocalAt(40); return Binary("Add", v2804, ([&]() -> Value { auto fn2805 = s->Global("len"); Arguments args2806; args2806.Add(s->LocalAt(36), false); return Call(c, fn2805, std::move(args2806)); }())); }()), false); return Call(c, fn2802, std::move(args2803)); }()))) { comp2799->SetAt(0, item2801); if (static_cast<bool>(([&]() -> Value { auto v2807 = ([&]() -> Value { auto v2809 = ([&]() -> Value { auto v2810 = comp2799->LocalAt(0); return Binary("Add", v2810, Value(int64_t{1})); }()); return Binary("Mod", v2809, comp2799->Captured("turns")); }()); Value v2808; v2808 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v2807, v2808))) return Value(false); v2807 = v2808; return Value(true); }()))) return Value(true); } return Value(false); }()))) {
Raise(([&]() -> Value { auto fn2811 = s->Global("Unsupported"); Arguments args2812; args2812.Add(Value("day boundary"), false); return Call(c, fn2811, std::move(args2812)); }()));
}
auto v2813 = ([&]() -> Value { auto fn2814 = s->Global("physical_state"); Arguments args2815; args2815.Add(s->LocalAt(23), false); return Call(c, fn2814, std::move(args2815)); }());
auto unpack2816 = Iterate(v2813);
ValidateUnpack(unpack2816, 2, false);
s->SetAt(18, unpack2816.at(0));
s->SetAt(32, unpack2816.at(1));
auto v2817 = ([&]() -> Value { auto fn2818 = s->Global("_clone_state"); Arguments args2819; args2819.positional.reserve(2); args2819.Add(s->LocalAt(18), false); args2819.Add(s->LocalAt(32), false); return Call(c, fn2818, std::move(args2819)); }());
auto unpack2820 = Iterate(v2817);
ValidateUnpack(unpack2820, 2, false);
s->SetAt(17, unpack2820.at(0));
s->SetAt(31, unpack2820.at(1));
auto v2821 = ([&]() -> Value { auto v2822 = Value(int64_t{1}); return Binary("Add", v2822, ([&]() -> Value { auto fn2823 = s->Global("len"); Arguments args2824; args2824.Add(Get(s->LocalAt(17), Value("hands")), false); return Call(c, fn2823, std::move(args2824)); }())); }());
s->SetAt(22, v2821);
if (static_cast<bool>(([&]() -> Value { auto v2825 = ([&]() -> Value { auto v2826 = ([&]() -> Value { auto fn2828 = s->Global("len"); Arguments args2829; args2829.Add(Get(s->LocalAt(31), Value("inventories")), false); return Call(c, fn2828, std::move(args2829)); }()); Value v2827; v2827 = s->LocalAt(22); if (!static_cast<bool>(Binary("NotEq", v2826, v2827))) return Value(false); v2826 = v2827; return Value(true); }()); if (static_cast<bool>(v2825)) return v2825; v2825 = ([&]() -> Value { auto v2830 = s->LocalAt(22); Value v2831; v2831 = Value(int64_t{32}); if (!static_cast<bool>(Binary("Gt", v2830, v2831))) return Value(false); v2830 = v2831; return Value(true); }()); return v2825; }()))) {
Raise(([&]() -> Value { auto fn2832 = s->Global("Unsupported"); Arguments args2833; args2833.Add(Value("invalid/unbounded worker inventory shape"), false); return Call(c, fn2832, std::move(args2833)); }()));
}
(void)([&]() -> Value { auto fn2834 = s->Global("_validate"); Arguments args2835; args2835.positional.reserve(3); args2835.Add(s->LocalAt(36), false); args2835.Add(s->LocalAt(22), false); args2835.Add(s->LocalAt(25), false); return Call(c, fn2834, std::move(args2835)); }());
auto v2836 = ([&]() -> Value { auto comp2837 = std::make_shared<Scope>(); comp2837->globals = s->globals; comp2837->parent = s; static constexpr const char* comp2837_names[] = {"_"}; comp2837->PrepareSlots(comp2837_names); auto result2838 = List(); for (const auto& item2839 : Iterate(([&]() -> Value { auto fn2840 = s->Global("range"); Arguments args2841; args2841.Add(s->LocalAt(22), false); return Call(c, fn2840, std::move(args2841)); }()))) { comp2837->SetAt(0, item2839); result2838.node()->sequence.push_back(([&]() -> Value { auto fn2842 = comp2837->Global("dict"); Arguments args2843; return Call(c, fn2842, std::move(args2843)); }())); } return result2838; }());
s->SetAt(13, v2836);
auto v2844 = ([&]() -> Value { auto dict2845 = Dict(); return dict2845; }());
s->SetAt(39, v2844);
auto v2846 = Tuple({List({}), List({}), List({})});
auto unpack2847 = Iterate(v2846);
ValidateUnpack(unpack2847, 3, false);
s->SetAt(38, unpack2847.at(0));
s->SetAt(35, unpack2847.at(1));
s->SetAt(15, unpack2847.at(2));
auto v2848 = ([&]() -> Value { auto fn2849 = s->Global("_clone_schedule"); Arguments args2850; args2850.Add(s->LocalAt(36), false); return Call(c, fn2849, std::move(args2850)); }());
s->SetAt(16, v2848);
auto v2851 = Value(int64_t{0});
s->SetAt(26, v2851);
for (const auto& item2852 : Iterate(([&]() -> Value { auto fn2853 = s->Global("enumerate"); Arguments args2854; args2854.Add(s->LocalAt(16), false); return Call(c, fn2853, std::move(args2854)); }()))) {
auto unpack2855 = Iterate(item2852);
ValidateUnpack(unpack2855, 2, false);
s->SetAt(24, unpack2855.at(0));
s->SetAt(1, unpack2855.at(1));
auto v2856 = ([&]() -> Value { auto v2857 = s->LocalAt(40); return Binary("Add", v2857, s->LocalAt(24)); }());
s->SetAt(41, v2856);
if (static_cast<bool>(s->LocalAt(14))) {
(void)([&]() -> Value { auto fn2858 = Attribute(s->LocalAt(38), "append"); Arguments args2859; args2859.Add(([&]() -> Value { auto fn2860 = s->Global("_clone_state"); Arguments args2861; args2861.positional.reserve(2); args2861.Add(s->LocalAt(17), false); args2861.Add(s->LocalAt(31), false); return Call(c, fn2860, std::move(args2861)); }()), false); return Call(c, fn2858, std::move(args2859)); }());
}
if (static_cast<bool>(([&]() -> Value { auto v2862 = ([&]() -> Value { auto v2863 = s->LocalAt(41); Value v2864; v2864 = s->Global("FINAL"); if (!static_cast<bool>(Binary("Eq", v2863, v2864))) return Value(false); v2863 = v2864; return Value(true); }()); if (!static_cast<bool>(v2862)) return v2862; v2862 = Unary("Not", s->LocalAt(29)); return v2862; }()))) {
auto v2865 = ([&]() -> Value { auto fn2866 = s->Global("shop_liquidation"); Arguments args2867; args2867.positional.reserve(3); args2867.Add(s->LocalAt(17), false); args2867.Add(s->LocalAt(31), false); args2867.Add(Get(([&]() -> Value { auto fn2868 = s->Global("_get"); Arguments args2869; args2869.positional.reserve(2); args2869.Add(s->LocalAt(23), false); args2869.Add(Value("market"), false); return Call(c, fn2868, std::move(args2869)); }()), Value("prices")), false); return Call(c, fn2866, std::move(args2867)); }());
s->SetAt(1, v2865);
auto v2870 = s->LocalAt(1);
Put(s->LocalAt(16), s->LocalAt(24), v2870);
}
auto v2871 = ([&]() -> Value { Arguments args2872; args2872.Add(([&]() -> Value { auto fn2873 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args2874; args2874.positional.reserve(2); args2874.Add(Value("farmer"), false); args2874.Add(List({Value("PASS")}), false); return CallDictionaryGet(c, fn2873, std::move(args2874)); }()), false); args2872.Add(([&]() -> Value { auto fn2875 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args2876; args2876.positional.reserve(2); args2876.Add(Value("hands"), false); args2876.Add(List({}), false); return CallDictionaryGet(c, fn2875, std::move(args2876)); }()), true); return List(std::move(args2872.positional)); }());
s->SetAt(3, v2871);
auto v2877 = ([&]() -> Value { auto dict2878 = Dict(); return dict2878; }());
s->SetAt(12, v2877);
for (const auto& item2879 : Iterate(s->LocalAt(3))) {
s->SetAt(9, item2879);
if (static_cast<bool>(([&]() -> Value { auto v2880 = Get(s->LocalAt(9), Value(int64_t{0})); Value v2881; v2881 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v2880, v2881))) return Value(false); v2880 = v2881; return Value(true); }()))) {
auto v2882 = ([&]() -> Value { auto v2883 = ([&]() -> Value { auto fn2884 = PrepareDictionaryGet(s->LocalAt(12)); Arguments args2885; args2885.positional.reserve(2); args2885.Add(Get(s->LocalAt(9), Value(int64_t{1})), false); args2885.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn2884, std::move(args2885)); }()); return Binary("Add", v2883, Value(int64_t{1})); }());
Put(s->LocalAt(12), Get(s->LocalAt(9), Value(int64_t{1})), v2882);
}
}
auto v2886 = ([&]() -> Value { auto comp2887 = std::make_shared<Scope>(); comp2887->globals = s->globals; comp2887->parent = s; static constexpr const char* comp2887_names[] = {"count", "item"}; comp2887->PrepareSlots(comp2887_names); auto result2888 = List(); for (const auto& item2889 : Iterate(([&]() -> Value { auto fn2890 = Attribute(s->LocalAt(12), "items"); Arguments args2891; return Call(c, fn2890, std::move(args2891)); }()))) { auto unpack2892 = Iterate(item2889); ValidateUnpack(unpack2892, 2, false); comp2887->SetAt(1, unpack2892.at(0)); comp2887->SetAt(0, unpack2892.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v2893 = comp2887->LocalAt(0); Value v2894; v2894 = ([&]() -> Value { auto fn2895 = PrepareDictionaryGet(Get(comp2887->Captured("private"), Value("seeds"))); Arguments args2896; args2896.positional.reserve(2); args2896.Add(comp2887->LocalAt(1), false); args2896.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn2895, std::move(args2896)); }()); if (!static_cast<bool>(Binary("Gt", v2893, v2894))) return Value(false); v2893 = v2894; return Value(true); }()))) continue; result2888.node()->sequence.push_back(comp2887->LocalAt(1)); } return Set(result2888.node()->sequence); }());
s->SetAt(7, v2886);
for (const auto& item2897 : Iterate(([&]() -> Value { auto fn2898 = s->Global("enumerate"); Arguments args2899; args2899.Add(([&]() -> Value { auto fn2900 = s->Global("_commands"); Arguments args2901; args2901.positional.reserve(2); args2901.Add(s->LocalAt(1), false); args2901.Add(s->LocalAt(22), false); return Call(c, fn2900, std::move(args2901)); }()), false); return Call(c, fn2898, std::move(args2899)); }()))) {
auto unpack2902 = Iterate(item2897);
ValidateUnpack(unpack2902, 2, false);
s->SetAt(2, unpack2902.at(0));
s->SetAt(9, unpack2902.at(1));
if (static_cast<bool>(([&]() -> Value { auto v2903 = ([&]() -> Value { auto v2904 = Get(s->LocalAt(9), Value(int64_t{0})); Value v2905; v2905 = Value("PLANT"); if (!static_cast<bool>(Binary("Eq", v2904, v2905))) return Value(false); v2904 = v2905; return Value(true); }()); if (!static_cast<bool>(v2903)) return v2903; v2903 = ([&]() -> Value { auto v2906 = Get(s->LocalAt(9), Value(int64_t{1})); Value v2907; v2907 = s->LocalAt(7); if (!static_cast<bool>(Binary("In", v2906, v2907))) return Value(false); v2906 = v2907; return Value(true); }()); return v2903; }()))) {
auto v2908 = List({Value("PASS")});
s->SetAt(9, v2908);
}
auto v2909 = (static_cast<bool>(([&]() -> Value { auto v2910 = s->LocalAt(2); Value v2911; v2911 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Eq", v2910, v2911))) return Value(false); v2910 = v2911; return Value(true); }())) ? Get(s->LocalAt(17), Value("farmer")) : Get(Get(s->LocalAt(17), Value("hands")), ([&]() -> Value { auto v2912 = s->LocalAt(2); return Binary("Sub", v2912, Value(int64_t{1})); }())));
s->SetAt(27, v2909);
auto v2913 = ([&]() -> Value { auto fn2914 = s->Global("tuple"); Arguments args2915; args2915.Add(s->LocalAt(27), false); return Call(c, fn2914, std::move(args2915)); }());
s->SetAt(43, v2913);
auto v2916 = Get(Get(s->LocalAt(31), Value("inventories")), s->LocalAt(2));
s->SetAt(20, v2916);
auto v2917 = (static_cast<bool>(([&]() -> Value { auto v2918 = Get(s->LocalAt(9), Value(int64_t{0})); Value v2919; v2919 = Set({Value("DROP"), Value("HARVEST"), Value("COLLECT_FERTILIZER")}); if (!static_cast<bool>(Binary("In", v2918, v2919))) return Value(false); v2918 = v2919; return Value(true); }())) ? ([&]() -> Value { auto fn2920 = s->Global("dict"); Arguments args2921; args2921.Add(s->LocalAt(20), false); return Call(c, fn2920, std::move(args2921)); }()) : Value{});
s->SetAt(5, v2917);
auto v2922 = (static_cast<bool>(([&]() -> Value { auto v2923 = Get(s->LocalAt(9), Value(int64_t{0})); Value v2924; v2924 = Set({Value("DROP"), Value("PLACE")}); if (!static_cast<bool>(Binary("In", v2923, v2924))) return Value(false); v2923 = v2924; return Value(true); }())) ? ([&]() -> Value { auto fn2925 = s->Global("dict"); Arguments args2926; args2926.Add(Get(s->LocalAt(31), Value("shed")), false); return Call(c, fn2925, std::move(args2926)); }()) : Value{});
s->SetAt(6, v2922);
(void)([&]() -> Value { auto fn2927 = s->Global("_apply_unit_action"); Arguments args2928; args2928.positional.reserve(8); args2928.Add(s->LocalAt(17), false); args2928.Add(s->LocalAt(31), false); args2928.Add(s->LocalAt(2), false); args2928.Add(s->LocalAt(9), false); args2928.Add(s->LocalAt(37), false); args2928.Add(([&]() -> Value { auto v2929 = s->LocalAt(41); return Binary("FloorDiv", v2929, s->LocalAt(42)); }()), false); args2928.Add(s->LocalAt(42), false); args2928.Add(s->LocalAt(8), false); return Call(c, fn2927, std::move(args2928)); }());
if (static_cast<bool>(([&]() -> Value { auto v2930 = s->LocalAt(6); Value v2931; v2931 = Value{}; if (!static_cast<bool>(Binary("IsNot", v2930, v2931))) return Value(false); v2930 = v2931; return Value(true); }()))) {
auto v2932 = ([&]() -> Value { auto comp2933 = std::make_shared<Scope>(); comp2933->globals = s->globals; comp2933->parent = s; static constexpr const char* comp2933_names[] = {"amount", "item"}; comp2933->PrepareSlots(comp2933_names); auto result2934 = Dict(); for (const auto& item2935 : Iterate(([&]() -> Value { auto fn2936 = Attribute(Get(s->LocalAt(31), Value("shed")), "items"); Arguments args2937; return Call(c, fn2936, std::move(args2937)); }()))) { auto unpack2938 = Iterate(item2935); ValidateUnpack(unpack2938, 2, false); comp2933->SetAt(1, unpack2938.at(0)); comp2933->SetAt(0, unpack2938.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v2939 = comp2933->LocalAt(0); Value v2940; v2940 = ([&]() -> Value { auto fn2941 = PrepareDictionaryGet(comp2933->Captured("before_shed")); Arguments args2942; args2942.positional.reserve(2); args2942.Add(comp2933->LocalAt(1), false); args2942.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn2941, std::move(args2942)); }()); if (!static_cast<bool>(Binary("Gt", v2939, v2940))) return Value(false); v2939 = v2940; return Value(true); }()))) continue; Put(result2934, comp2933->LocalAt(1), ([&]() -> Value { auto v2943 = comp2933->LocalAt(0); return Binary("Sub", v2943, ([&]() -> Value { auto fn2944 = PrepareDictionaryGet(comp2933->Captured("before_shed")); Arguments args2945; args2945.positional.reserve(2); args2945.Add(comp2933->LocalAt(1), false); args2945.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn2944, std::move(args2945)); }())); }())); } return result2934; }());
s->SetAt(11, v2932);
for (const auto& item2946 : Iterate(([&]() -> Value { auto fn2947 = Attribute(s->LocalAt(11), "items"); Arguments args2948; return Call(c, fn2947, std::move(args2948)); }()))) {
auto unpack2949 = Iterate(item2946);
ValidateUnpack(unpack2949, 2, false);
s->SetAt(21, unpack2949.at(0));
s->SetAt(4, unpack2949.at(1));
auto v2950 = ([&]() -> Value { auto v2951 = ([&]() -> Value { auto fn2952 = PrepareDictionaryGet(Get(s->LocalAt(13), s->LocalAt(2))); Arguments args2953; args2953.positional.reserve(2); args2953.Add(s->LocalAt(21), false); args2953.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn2952, std::move(args2953)); }()); return Binary("Add", v2951, s->LocalAt(4)); }());
Put(Get(s->LocalAt(13), s->LocalAt(2)), s->LocalAt(21), v2950);
}
if (static_cast<bool>(s->LocalAt(11))) {
(void)([&]() -> Value { auto fn2954 = Attribute(s->LocalAt(15), "append"); Arguments args2955; args2955.Add(([&]() -> Value { auto dict2956 = Dict(); auto key2957 = Value("offset"); Put(dict2956, key2957, s->LocalAt(24)); auto key2958 = Value("actor"); Put(dict2956, key2958, s->LocalAt(2)); auto key2959 = Value("op"); Put(dict2956, key2959, Get(s->LocalAt(9), Value(int64_t{0}))); auto key2960 = Value("xy"); Put(dict2956, key2960, s->LocalAt(43)); auto key2961 = Value("deposited"); Put(dict2956, key2961, s->LocalAt(11)); return dict2956; }()), false); return Call(c, fn2954, std::move(args2955)); }());
}
if (static_cast<bool>(([&]() -> Value { auto v2962 = Get(s->LocalAt(9), Value(int64_t{0})); Value v2963; v2963 = Value("DROP"); if (!static_cast<bool>(Binary("Eq", v2962, v2963))) return Value(false); v2962 = v2963; return Value(true); }()))) {
auto v2964 = s->LocalAt(26);
s->SetAt(26, Inplace("Add", v2964, ([&]() -> Value { auto fn2965 = s->Global("sum"); Arguments args2966; args2966.Add(([&]() -> Value { auto comp2967 = std::make_shared<Scope>(); comp2967->globals = s->globals; comp2967->parent = s; static constexpr const char* comp2967_names[] = {"amount", "item"}; comp2967->PrepareSlots(comp2967_names); auto result2968 = List(); for (const auto& item2969 : Iterate(([&]() -> Value { auto fn2970 = Attribute(s->LocalAt(5), "items"); Arguments args2971; return Call(c, fn2970, std::move(args2971)); }()))) { auto unpack2972 = Iterate(item2969); ValidateUnpack(unpack2972, 2, false); comp2967->SetAt(1, unpack2972.at(0)); comp2967->SetAt(0, unpack2972.at(1)); result2968.node()->sequence.push_back(([&]() -> Value { auto fn2973 = comp2967->Global("max"); Arguments args2974; args2974.positional.reserve(2); args2974.Add(Value(int64_t{0}), false); args2974.Add(([&]() -> Value { auto v2975 = ([&]() -> Value { auto v2976 = comp2967->LocalAt(0); return Binary("Sub", v2976, ([&]() -> Value { auto fn2977 = PrepareDictionaryGet(comp2967->Captured("inv")); Arguments args2978; args2978.positional.reserve(2); args2978.Add(comp2967->LocalAt(1), false); args2978.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn2977, std::move(args2978)); }())); }()); return Binary("Sub", v2975, ([&]() -> Value { auto fn2979 = PrepareDictionaryGet(comp2967->Captured("delta")); Arguments args2980; args2980.positional.reserve(2); args2980.Add(comp2967->LocalAt(1), false); args2980.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn2979, std::move(args2980)); }())); }()), false); return Call(c, fn2973, std::move(args2974)); }())); } return result2968; }()), false); return Call(c, fn2965, std::move(args2966)); }())));
}
}
if (static_cast<bool>(([&]() -> Value { auto v2981 = Get(s->LocalAt(9), Value(int64_t{0})); Value v2982; v2982 = Set({Value("HARVEST"), Value("COLLECT_FERTILIZER")}); if (!static_cast<bool>(Binary("In", v2981, v2982))) return Value(false); v2981 = v2982; return Value(true); }()))) {
auto v2983 = ([&]() -> Value { auto comp2984 = std::make_shared<Scope>(); comp2984->globals = s->globals; comp2984->parent = s; static constexpr const char* comp2984_names[] = {"amount", "item"}; comp2984->PrepareSlots(comp2984_names); auto result2985 = Dict(); for (const auto& item2986 : Iterate(([&]() -> Value { auto fn2987 = Attribute(s->LocalAt(20), "items"); Arguments args2988; return Call(c, fn2987, std::move(args2988)); }()))) { auto unpack2989 = Iterate(item2986); ValidateUnpack(unpack2989, 2, false); comp2984->SetAt(1, unpack2989.at(0)); comp2984->SetAt(0, unpack2989.at(1)); if (!static_cast<bool>(([&]() -> Value { auto v2990 = comp2984->LocalAt(0); Value v2991; v2991 = ([&]() -> Value { auto fn2992 = PrepareDictionaryGet(comp2984->Captured("before_inv")); Arguments args2993; args2993.positional.reserve(2); args2993.Add(comp2984->LocalAt(1), false); args2993.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn2992, std::move(args2993)); }()); if (!static_cast<bool>(Binary("Gt", v2990, v2991))) return Value(false); v2990 = v2991; return Value(true); }()))) continue; Put(result2985, comp2984->LocalAt(1), ([&]() -> Value { auto v2994 = comp2984->LocalAt(0); return Binary("Sub", v2994, ([&]() -> Value { auto fn2995 = PrepareDictionaryGet(comp2984->Captured("before_inv")); Arguments args2996; args2996.positional.reserve(2); args2996.Add(comp2984->LocalAt(1), false); args2996.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn2995, std::move(args2996)); }())); }())); } return result2985; }());
s->SetAt(11, v2983);
if (static_cast<bool>(s->LocalAt(11))) {
(void)([&]() -> Value { auto fn2997 = Attribute(s->LocalAt(15), "append"); Arguments args2998; args2998.Add(([&]() -> Value { auto dict2999 = Dict(); auto key3000 = Value("offset"); Put(dict2999, key3000, s->LocalAt(24)); auto key3001 = Value("actor"); Put(dict2999, key3001, s->LocalAt(2)); auto key3002 = Value("op"); Put(dict2999, key3002, Get(s->LocalAt(9), Value(int64_t{0}))); auto key3003 = Value("xy"); Put(dict2999, key3003, s->LocalAt(43)); auto key3004 = Value("acquired"); Put(dict2999, key3004, s->LocalAt(11)); return dict2999; }()), false); return Call(c, fn2997, std::move(args2998)); }());
}
}
}
auto v3005 = ([&]() -> Value { auto fn3006 = s->Global("dict"); Arguments args3007; args3007.Add(Get(s->LocalAt(31), Value("shed")), false); return Call(c, fn3006, std::move(args3007)); }());
s->SetAt(28, v3005);
if (static_cast<bool>(([&]() -> Value { auto v3008 = ([&]() -> Value { auto v3009 = s->LocalAt(41); Value v3010; v3010 = s->Global("FINAL"); if (!static_cast<bool>(Binary("Eq", v3009, v3010))) return Value(false); v3009 = v3010; return Value(true); }()); if (!static_cast<bool>(v3008)) return v3008; v3008 = s->LocalAt(29); if (!static_cast<bool>(v3008)) return v3008; v3008 = s->LocalAt(19); return v3008; }()))) {
auto v3011 = ([&]() -> Value { auto fn3012 = s->Global("liquidation"); Arguments args3013; args3013.positional.reserve(3); args3013.Add(s->LocalAt(28), false); args3013.Add(List({}), false); args3013.Add(s->LocalAt(25), false); return Call(c, fn3012, std::move(args3013)); }());
Put(s->LocalAt(1), Value("market"), v3011);
auto v3014 = Get(([&]() -> Value { auto fn3015 = s->Global("_get"); Arguments args3016; args3016.positional.reserve(2); args3016.Add(s->LocalAt(23), false); args3016.Add(Value("market"), false); return Call(c, fn3015, std::move(args3016)); }()), Value("prices"));
s->SetAt(30, v3014);
(void)([&]() -> Value { auto fn3017 = Attribute(Get(s->LocalAt(1), Value("market")), "sort"); Arguments args3018; args3018.Keyword("key", Define(&Code_40ea0a105badcdd327b9, s, Signature{{"order"}, {}, {}, {}, "", "", ([]() -> std::span<const char* const> { static constexpr const char* names[] = {"order"}; return names; }())}, true, "<lambda>")); return Call(c, fn3017, std::move(args3018)); }());
}
for (const auto& item3024 : Iterate(([&]() -> Value { auto fn3025 = PrepareDictionaryGet(s->LocalAt(1)); Arguments args3026; args3026.positional.reserve(2); args3026.Add(Value("market"), false); args3026.Add(List({}), false); return CallDictionaryGet(c, fn3025, std::move(args3026)); }()))) {
auto unpack3027 = Iterate(item3024);
ValidateUnpack(unpack3027, 3, false);
s->SetAt(0, unpack3027.at(0));
s->SetAt(21, unpack3027.at(1));
s->SetAt(34, unpack3027.at(2));
auto v3028 = ([&]() -> Value { auto fn3029 = s->Global("min"); Arguments args3030; args3030.positional.reserve(3); args3030.Add(s->LocalAt(34), false); args3030.Add(([&]() -> Value { auto fn3031 = PrepareDictionaryGet(Get(s->LocalAt(31), Value("shed"))); Arguments args3032; args3032.positional.reserve(2); args3032.Add(s->LocalAt(21), false); args3032.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn3031, std::move(args3032)); }()), false); args3030.Add(Value(int64_t{99999}), false); return Call(c, fn3029, std::move(args3030)); }());
s->SetAt(33, v3028);
if (static_cast<bool>(([&]() -> Value { auto v3033 = s->LocalAt(33); Value v3034; v3034 = Value(int64_t{0}); if (!static_cast<bool>(Binary("Gt", v3033, v3034))) return Value(false); v3033 = v3034; return Value(true); }()))) {
auto v3035 = Get(s->LocalAt(31), Value("shed"));
auto v3036 = s->LocalAt(21);
auto v3037 = Get(v3035, v3036);
Put(v3035, v3036, Inplace("Sub", v3037, s->LocalAt(33)));
auto v3038 = ([&]() -> Value { auto v3039 = ([&]() -> Value { auto fn3040 = PrepareDictionaryGet(s->LocalAt(39)); Arguments args3041; args3041.positional.reserve(2); args3041.Add(s->LocalAt(21), false); args3041.Add(Value(int64_t{0}), false); return CallDictionaryGet(c, fn3040, std::move(args3041)); }()); return Binary("Add", v3039, s->LocalAt(33)); }());
Put(s->LocalAt(39), s->LocalAt(21), v3038);
}
}
(void)([&]() -> Value { auto fn3042 = s->Global("_decay_plants"); Arguments args3043; args3043.positional.reserve(2); args3043.Add(s->LocalAt(17), false); args3043.Add(s->LocalAt(41), false); return Call(c, fn3042, std::move(args3043)); }());
(void)([&]() -> Value { auto fn3044 = Attribute(s->LocalAt(35), "append"); Arguments args3045; args3045.Add(([&]() -> Value { auto dict3046 = Dict(); auto key3047 = Value("pre_market_shed"); Put(dict3046, key3047, s->LocalAt(28)); auto key3048 = Value("post_market_shed"); Put(dict3046, key3048, ([&]() -> Value { auto fn3049 = s->Global("dict"); Arguments args3050; args3050.Add(Get(s->LocalAt(31), Value("shed")), false); return Call(c, fn3049, std::move(args3050)); }())); auto key3051 = Value("deposited_by_actor"); Put(dict3046, key3051, ([&]() -> Value { auto comp3052 = std::make_shared<Scope>(); comp3052->globals = s->globals; comp3052->parent = s; static constexpr const char* comp3052_names[] = {"v"}; comp3052->PrepareSlots(comp3052_names); auto result3053 = List(); for (const auto& item3054 : Iterate(s->LocalAt(13))) { comp3052->SetAt(0, item3054); result3053.node()->sequence.push_back(([&]() -> Value { auto fn3055 = comp3052->Global("dict"); Arguments args3056; args3056.Add(comp3052->LocalAt(0), false); return Call(c, fn3055, std::move(args3056)); }())); } return result3053; }())); auto key3057 = Value("sold"); Put(dict3046, key3057, ([&]() -> Value { auto fn3058 = s->Global("dict"); Arguments args3059; args3059.Add(s->LocalAt(39), false); return Call(c, fn3058, std::move(args3059)); }())); return dict3046; }()), false); return Call(c, fn3044, std::move(args3045)); }());
}
if (static_cast<bool>(s->LocalAt(14))) {
(void)([&]() -> Value { auto fn3060 = Attribute(s->LocalAt(38), "append"); Arguments args3061; args3061.Add(([&]() -> Value { auto fn3062 = s->Global("_clone_state"); Arguments args3063; args3063.positional.reserve(2); args3063.Add(s->LocalAt(17), false); args3063.Add(s->LocalAt(31), false); return Call(c, fn3062, std::move(args3063)); }()), false); return Call(c, fn3060, std::move(args3061)); }());
}
return ([&]() -> Value { auto dict3064 = Dict(); auto key3065 = Value("rows"); Put(dict3064, key3065, s->LocalAt(35)); auto key3066 = Value("states"); Put(dict3064, key3066, s->LocalAt(38)); auto key3067 = Value("events"); Put(dict3064, key3067, s->LocalAt(15)); auto key3068 = Value("actions"); Put(dict3064, key3068, s->LocalAt(16)); auto key3069 = Value("overflow_units"); Put(dict3064, key3069, s->LocalAt(26)); auto key3070 = Value("farm"); Put(dict3064, key3070, s->LocalAt(17)); auto key3071 = Value("private"); Put(dict3064, key3071, s->LocalAt(31)); auto key3072 = Value("sold"); Put(dict3064, key3072, s->LocalAt(39)); return dict3064; }());
return {};
}
}  // namespace kagg::opponents::compiled
