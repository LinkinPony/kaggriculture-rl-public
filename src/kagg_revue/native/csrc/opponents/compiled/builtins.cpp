#include <algorithm>
#include <array>
#include <charconv>
#include <chrono>
#include <cmath>
#include <limits>
#include <numeric>

#include "opponents/compiled/runtime.hpp"

namespace kagg::opponents::compiled {
namespace {
Value Keyword(const Arguments& args, const std::string& key,
              Value fallback = {}) {
  for (const auto& [name, value] : args.keywords)
    if (name == key) return value;
  return fallback;
}
bool Callable(const Value& value) {
  return Is(value, Kind::kFunction) || Is(value, Kind::kClass) ||
         Is(value, Kind::kBuiltin) ||
         (Is(value, Kind::kObject) &&
          !AttributeOr(value, "__call__", {}).none());
}
Values Sorted(Context& ctx, Values seq, Value key, bool reverse) {
  std::vector<std::pair<Value, Value>> pairs;
  for (const auto& v : seq)
    pairs.emplace_back(key.none() ? v : Call(ctx, key, {{v}, {}}), v);
  std::stable_sort(pairs.begin(), pairs.end(),
                   [&](const auto& a, const auto& b) {
                     return reverse ? Compare(a.first, b.first) > 0
                                    : Compare(a.first, b.first) < 0;
                   });
  seq.clear();
  for (const auto& [k, v] : pairs) seq.push_back(v);
  return seq;
}
}  // namespace

bool InstanceOf(const Value& value, const Value& type) {
  if (Is(type, Kind::kTuple)) {
    for (const auto& t : Iterate(type))
      if (InstanceOf(value, t)) return true;
    return false;
  }
  if (Is(type, Kind::kClass)) {
    if (!Is(value, Kind::kObject)) return false;
    auto base = value.node()->base;
    while (Is(base, Kind::kClass)) {
      if (Identical(base, type)) return true;
      base = base.node()->base;
    }
    return false;
  }
  if (!Is(type, Kind::kBuiltin))
    throw Error("TypeError", "isinstance expects a type");
  const auto& name = type.node()->text;
  if (name == "int") return value.integer();
  if (name == "float") return value.numeric() && !value.integer();
  if (name == "bool") return value.boolean();
  if (name == "dict") return Is(value, Kind::kDict);
  if (name == "list") return Is(value, Kind::kList);
  if (name == "tuple") return Is(value, Kind::kTuple);
  if (name == "set" || name == "frozenset") return Is(value, Kind::kSet);
  if (name == "str") return Is(value, Kind::kString);
  if (name == "object") return true;
  throw PortError("unsupported isinstance type: " + name);
}
Value CallBuiltin(Context& ctx, const Value& function, Arguments args) {
  const auto& name = function.node()->text;
  const auto& a = args.positional;
  const auto arg = [&](size_t i, Value fallback = {}) {
    return i < a.size() ? a[i] : fallback;
  };
  if (name.starts_with("method."))
    return CallMethod(ctx, name.substr(7), function.node()->base,
                      std::move(args));
  if (name == "len") return Length(a.at(0));
  if (name == "id") {
    if (!a.at(0).node()) throw PortError("native id requires a heap value");
    return static_cast<int64_t>(reinterpret_cast<uintptr_t>(a[0].node().get()));
  }
  if (name == "collections.ChainMap") {
    auto p = std::make_shared<Node>(Kind::kChainMap);
    p->sequence = a.empty() ? Values{Dict()} : a;
    return Value(p);
  }
  if (name == "os.environ.get") {
    // Public submission bundles run without optional local research libraries.
    if (a.size() != 1 || a[0].string() != "V92_SELL_LIB")
      throw PortError("unreviewed environment access in public policy");
    return {};
  }
  if (name == "bool") return static_cast<bool>(arg(0));
  if (name == "int" || name == "float") {
    if (a.empty()) return name == "int" ? Value(0) : Value(0.0);
    if (Is(a[0], Kind::kString)) {
      try {
        size_t consumed = 0;
        if (name == "int") {
          int64_t v = std::stoll(a[0].string(), &consumed);
          if (consumed != a[0].string().size())
            throw Error("ValueError", "invalid integer");
          return v;
        }
        double v = std::stod(a[0].string(), &consumed);
        if (consumed != a[0].string().size())
          throw Error("ValueError", "invalid float");
        return v;
      } catch (const std::invalid_argument&) {
        throw Error("ValueError", "invalid numeric string");
      }
    }
    return name == "int" ? Value(a[0].integer_value()) : Value(a[0].number());
  }
  if (name == "str") return a.empty() ? Value("") : Value(Repr(a[0]));
  if (name == "list") return List(a.empty() ? Values{} : Iterate(a[0]));
  if (name == "tuple") return Tuple(a.empty() ? Values{} : Iterate(a[0]));
  if (name == "set" || name == "frozenset")
    return Set(a.empty() ? Values{} : Iterate(a[0]));
  if (name == "dict" || name == "dict.fromkeys") {
    auto out = Dict();
    if (name == "dict.fromkeys") {
      for (const auto& k : Iterate(a.at(0))) Put(out, k, arg(1));
    } else if (!a.empty())
      Merge(out, a[0]);
    for (const auto& [k, v] : args.keywords) Put(out, k, v);
    return out;
  }
  if (name == "copy.copy") return ShallowCopy(a.at(0));
  if (name == "copy.deepcopy" || name == "deepcopy") return DeepCopy(a.at(0));
  if (name == "getattr")
    return a.size() == 3 ? AttributeOr(a[0], a[1].string(), a[2])
                         : Attribute(a[0], a[1].string());
  if (name == "setattr") {
    SetAttribute(a.at(0), a.at(1).string(), a.at(2));
    return {};
  }
  if (name == "hasattr") {
    auto result = AttributeOr(a.at(0), a.at(1).string(), Builtin("missing"));
    return !(Is(result, Kind::kBuiltin) && result.node()->text == "missing");
  }
  if (name == "callable") return Callable(a.at(0));
  if (name == "isinstance") return InstanceOf(a.at(0), a.at(1));
  if (name == "staticmethod") {
    auto p = std::make_shared<Node>(*a.at(0).node());
    p->function = std::make_shared<Function>(*p->function);
    p->function->static_method = true;
    return Value(p);
  }
  if (name == "type") {
    if (a[0].boolean()) return Builtin("bool");
    if (a[0].integer()) return Builtin("int");
    if (a[0].numeric()) return Builtin("float");
    if (Is(a[0], Kind::kObject)) return a[0].node()->base;
    for (const auto& t : {"str", "dict", "list", "tuple", "set"})
      if (InstanceOf(a[0], Builtin(t))) return Builtin(t);
    return Builtin("NoneType");
  }
  if (name == "range") {
    int64_t start = a.size() == 1 ? 0 : a.at(0).integer_value();
    int64_t end = a.at(a.size() == 1 ? 0 : 1).integer_value();
    int64_t step = a.size() == 3 ? a[2].integer_value() : 1;
    if (!step) throw Error("ValueError", "range step is zero");
    Values out;
    for (int64_t i = start; step > 0 ? i < end : i > end; i += step)
      out.emplace_back(i);
    return List(std::move(out));
  }
  if (name == "iter") {
    auto p = std::make_shared<Node>(Kind::kIterator);
    p->sequence = Iterate(a.at(0));
    return Value(p);
  }
  if (name == "next") {
    if (!Is(a.at(0), Kind::kIterator))
      throw Error("TypeError", "next requires iterator");
    auto p = a[0].node();
    if (p->position < p->sequence.size()) return p->sequence[p->position++];
    if (a.size() > 1) return a[1];
    throw Error("StopIteration", "iterator exhausted");
  }
  if (name == "enumerate") {
    Values out;
    int64_t i = a.size() > 1 ? a[1].integer_value() : 0;
    for (const auto& x : Iterate(a.at(0))) out.push_back(Tuple({i++, x}));
    return List(std::move(out));
  }
  if (name == "zip") {
    std::vector<Values> seqs;
    size_t n = a.empty() ? 0 : std::numeric_limits<size_t>::max();
    for (const auto& x : a) {
      seqs.push_back(Iterate(x));
      n = std::min(n, seqs.back().size());
    }
    Values out;
    for (size_t i = 0; i < n; ++i) {
      Values row;
      for (const auto& seq : seqs) row.push_back(seq[i]);
      out.push_back(Tuple(std::move(row)));
    }
    return List(std::move(out));
  }
  if (name == "map") {
    Values out;
    for (const auto& x : Iterate(a.at(1)))
      out.push_back(Call(ctx, a.at(0), {{x}, {}}));
    return List(std::move(out));
  }
  if (name == "sum") {
    auto total = arg(1, 0);
    for (const auto& x : Iterate(a.at(0))) total = Binary("Add", total, x);
    return total;
  }
  if (name == "any" || name == "all") {
    for (const auto& x : Iterate(a.at(0)))
      if (static_cast<bool>(x) == (name == "any")) return name == "any";
    return name == "all";
  }
  if (name == "sorted" || name == "reversed") {
    auto seq = Iterate(a.at(0));
    if (name == "reversed")
      std::reverse(seq.begin(), seq.end());
    else
      seq = Sorted(ctx, std::move(seq), Keyword(args, "key"),
                   static_cast<bool>(Keyword(args, "reverse", false)));
    return List(std::move(seq));
  }
  if (name == "min" || name == "max") {
    auto seq = a.size() == 1 ? Iterate(a.at(0)) : a;
    if (seq.empty()) {
      for (const auto& [k, v] : args.keywords)
        if (k == "default") return v;
      throw Error("ValueError", "empty min/max");
    }
    auto key = Keyword(args, "key");
    auto best = seq[0];
    auto best_key = key.none() ? best : Call(ctx, key, {{best}, {}});
    for (size_t i = 1; i < seq.size(); ++i) {
      auto candidate = key.none() ? seq[i] : Call(ctx, key, {{seq[i]}, {}});
      const int cmp = Compare(candidate, best_key);
      if (name == "min" ? cmp < 0 : cmp > 0) {
        best = seq[i];
        best_key = candidate;
      }
    }
    return best;
  }
  if (name == "abs")
    return a.at(0).integer() ? Value(std::abs(a[0].integer_value()))
                             : Value(std::abs(a[0].number()));
  if (name == "round") {
    if (a.size() == 2) {
      const int64_t digits = a[1].integer_value();
      if (digits < 0 || digits > 15)
        throw PortError("decimal rounding outside the reviewed precision range");
      if (a[0].integer()) return a[0];
      std::array<char, 512> buffer;
      auto result = std::to_chars(buffer.data(), buffer.data() + buffer.size(),
                                  a[0].number(), std::chars_format::fixed, digits);
      if (result.ec != std::errc{}) throw PortError("decimal rounding conversion failed");
      return std::stod(std::string(buffer.data(), result.ptr));
    }
    return static_cast<int64_t>(std::nearbyint(a.at(0).number()));
  }
  if (name == "math.sqrt") return std::sqrt(a.at(0).number());
  if (name == "math.log")
    return a.size() > 1 ? std::log(a[0].number()) / std::log(a[1].number())
                        : std::log(a[0].number());
  if (name == "math.log10") return std::log10(a.at(0).number());
  if (name == "math.ceil")
    return static_cast<int64_t>(std::ceil(a.at(0).number()));
  if (name == "perf_counter")
    return std::chrono::duration<double>(
               std::chrono::steady_clock::now().time_since_epoch())
        .count();
  if (name == "permutations" || name == "itertools.permutations") {
    auto seq = Iterate(a.at(0));
    size_t r = a.size() > 1 ? a[1].integer_value() : seq.size();
    Values out, row;
    std::vector<bool> used(seq.size());
    const auto visit = [&](auto&& self) -> void {
      if (row.size() == r) {
        out.push_back(Tuple(row));
        return;
      }
      for (size_t i = 0; i < seq.size(); ++i)
        if (!used[i]) {
          used[i] = true;
          row.push_back(seq[i]);
          self(self);
          row.pop_back();
          used[i] = false;
        }
    };
    visit(visit);
    return List(std::move(out));
  }
  if (name == "print") return {};
  if (name == "Exception" || name.ends_with("Error"))
    return MakeException(function, arg(0, ""));
  throw PortError("unsupported compiled builtin: " + name);
}
}  // namespace kagg::opponents::compiled
