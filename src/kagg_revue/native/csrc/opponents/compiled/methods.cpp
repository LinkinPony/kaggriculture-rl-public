#include <algorithm>

#include "opponents/compiled/runtime.hpp"

namespace kagg::opponents::compiled {
DictionaryGet PrepareDictionaryGet(Value receiver) {
  if (Is(receiver, Kind::kDict) &&
      (receiver.node()->attributes.none() ||
       !Contains(receiver.node()->attributes, "get"))) {
    return {std::move(receiver), {}};
  }
  return {{}, Attribute(receiver, "get")};
}

Value CallDictionaryGet(Context& context, DictionaryGet method, Arguments arguments) {
  if (method.dictionary.none())
    return Call(context, std::move(method.function), std::move(arguments));
  ++context.calls;
  return CallMethod(context, "get", std::move(method.dictionary), std::move(arguments));
}

Value CallMethod(Context& context, const std::string& method, Value self,
                 Arguments args) {
  const auto& a = args.positional;
  auto& p = self.node();
  const auto mutable_check = [&] {
    if (p->frozen) throw PortError("mutation of frozen route data");
  };
  if (method == "get" && (Is(self, Kind::kDict) || Is(self, Kind::kChainMap)))
    return GetOr(self, a.at(0), a.size() > 1 ? a[1] : Value{});
  if (method == "join" && Is(self, Kind::kString)) {
    std::string result;
    bool first = true;
    for (const auto& value : Iterate(a.at(0))) {
      if (!first) result += self.string();
      result += value.string();
      first = false;
    }
    return result;
  }
  if (method == "split" && Is(self, Kind::kString)) {
    if (a.size() != 1) throw PortError("native split requires an explicit separator");
    const auto& separator = a[0].string();
    if (separator.empty()) throw Error("ValueError", "empty separator");
    Values result;
    size_t start = 0, end;
    while ((end = self.string().find(separator, start)) != std::string::npos) {
      result.emplace_back(self.string().substr(start, end - start));
      start = end + separator.size();
    }
    result.emplace_back(self.string().substr(start));
    return List(std::move(result));
  }
  if (method == "items" || method == "keys" || method == "values") {
    if (!Is(self, Kind::kDict)) throw Error("AttributeError", method);
    Values out;
    for (const auto& [k, v] : p->entries)
      out.push_back(method == "items"  ? Tuple({k, v})
                    : method == "keys" ? k
                                       : v);
    return List(std::move(out));
  }
  if (method == "copy") return ShallowCopy(self);
  if (method == "setdefault" && Is(self, Kind::kDict)) {
    if (Contains(self, a.at(0))) return Get(self, a[0]);
    auto value = a.size() > 1 ? a[1] : Value{};
    Put(self, a[0], value);
    return value;
  }
  if (method == "pop") {
    mutable_check();
    if (Is(self, Kind::kDict)) {
      if (!Contains(self, a.at(0))) {
        if (a.size() > 1) return a[1];
        throw Error("KeyError", Repr(a[0]));
      }
      auto value = Get(self, a[0]);
      Erase(self, a[0]);
      return value;
    }
    if (Is(self, Kind::kList)) {
      auto index = a.empty() ? Value(-1) : a[0];
      auto value = Get(self, index);
      Erase(self, index);
      return value;
    }
  }
  if (method == "clear") {
    mutable_check();
    p->sequence.clear();
    p->entries.clear();
    p->index.clear();
    return {};
  }
  if (method == "update") {
    mutable_check();
    if (Is(self, Kind::kDict)) {
      if (!a.empty()) Merge(self, a[0]);
      for (const auto& [k, v] : args.keywords) Put(self, k, v);
    } else if (Is(self, Kind::kSet)) {
      for (const auto& values : a)
        for (const auto& v : Iterate(values))
          if (!Contains(self, v)) p->sequence.push_back(v);
    } else
      throw Error("AttributeError", method);
    return {};
  }
  if (method == "add" && Is(self, Kind::kSet)) {
    mutable_check();
    if (!Contains(self, a.at(0))) p->sequence.push_back(a[0]);
    return {};
  }
  if (method == "append" && Is(self, Kind::kList)) {
    mutable_check();
    p->sequence.push_back(a.at(0));
    return {};
  }
  if (method == "extend" && Is(self, Kind::kList)) {
    mutable_check();
    auto more = Iterate(a.at(0));
    p->sequence.insert(p->sequence.end(), more.begin(), more.end());
    return {};
  }
  if (method == "insert" && Is(self, Kind::kList)) {
    mutable_check();
    int64_t i = a.at(0).integer_value();
    if (i < 0) i += Length(self);
    i = std::clamp(i, int64_t{0}, Length(self));
    p->sequence.insert(p->sequence.begin() + i, a.at(1));
    return {};
  }
  if (method == "remove" && Is(self, Kind::kList)) {
    mutable_check();
    for (auto it = p->sequence.begin(); it != p->sequence.end(); ++it)
      if (Equal(*it, a.at(0))) {
        p->sequence.erase(it);
        return {};
      }
    throw Error("ValueError", "value absent from list");
  }
  if (method == "count") {
    int64_t count = 0;
    for (const auto& v : Iterate(self))
      if (Equal(v, a.at(0))) ++count;
    return count;
  }
  if (method == "index") {
    auto values = Iterate(self);
    for (size_t i = 0; i < values.size(); ++i)
      if (Equal(values[i], a.at(0))) return static_cast<int64_t>(i);
    throw Error("ValueError", "value absent from sequence");
  }
  if (method == "sort" && Is(self, Kind::kList)) {
    mutable_check();
    Arguments sorted;
    sorted.positional = {self};
    sorted.keywords = args.keywords;
    auto result = CallBuiltin(context, Builtin("sorted"), std::move(sorted));
    p->sequence = result.node()->sequence;
    return {};
  }
  if (method == "reverse" && Is(self, Kind::kList)) {
    mutable_check();
    std::reverse(p->sequence.begin(), p->sequence.end());
    return {};
  }
  throw PortError("unsupported compiled method: " + method);
}
}  // namespace kagg::opponents::compiled
