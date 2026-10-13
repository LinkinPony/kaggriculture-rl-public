#include <algorithm>

#include "opponents/compiled/value.hpp"

namespace kagg::opponents::compiled {
namespace {
int64_t Index(const Value& key, int64_t length) {
  if (!key.integer())
    throw Error("TypeError", "sequence index must be integral");
  int64_t index = key.integer_value();
  if (index < 0) index += length;
  if (index < 0 || index >= length)
    throw Error("IndexError", "sequence index out of range");
  return index;
}
void Mutable(const Value& value) {
  if (value.node()->frozen)
    throw PortError("attempt to mutate a frozen route asset");
}
struct Bounds {
  int64_t start, stop, step;
};
Bounds Normalize(const Value& value, const Value& start, const Value& stop,
                 const Value& step) {
  const int64_t n = Length(value),
                stride = step.none() ? 1 : step.integer_value();
  if (!stride) throw Error("ValueError", "zero slice step");
  auto endpoint = [&](const Value& v, int64_t fallback) {
    if (v.none()) return fallback;
    int64_t x = v.integer_value();
    if (x < 0) x += n;
    return std::clamp(x, stride > 0 ? int64_t{0} : int64_t{-1},
                      stride > 0 ? n : n - 1);
  };
  return {endpoint(start, stride > 0 ? 0 : n - 1),
          endpoint(stop, stride > 0 ? n : -1), stride};
}
}  // namespace

bool Contains(const Value& container, const Value& key) {
  if (Is(container, Kind::kChainMap)) {
    for (const auto& map : container.node()->sequence)
      if (Contains(map, key)) return true;
    return false;
  }
  if (Is(container, Kind::kDict))
    return container.node()->index.contains(Key(key));
  if (Is(container, Kind::kString))
    return container.string().find(key.string()) != std::string::npos;
  if (Is(container, Kind::kList) || Is(container, Kind::kTuple) ||
      Is(container, Kind::kSet)) {
    for (const auto& item : container.node()->sequence)
      if (Equal(item, key)) return true;
    return false;
  }
  throw Error("TypeError", "membership requires a container");
}
Value Get(const Value& container, const Value& key) {
  if (Is(container, Kind::kChainMap)) {
    for (const auto& map : container.node()->sequence)
      if (Contains(map, key)) return Get(map, key);
    throw Error("KeyError", Repr(key));
  }
  if (Is(container, Kind::kBytes))
    return static_cast<int>(static_cast<unsigned char>(
        container.node()->text[Index(key, Length(container))]));
  if (Is(container, Kind::kDict)) {
    const auto& p = container.node();
    auto it = p->index.find(Key(key));
    if (it == p->index.end()) throw Error("KeyError", Repr(key));
    return p->entries[it->second].second;
  }
  if (Is(container, Kind::kString))
    return Value(
        std::string(1, container.string()[Index(key, Length(container))]));
  if (Is(container, Kind::kList) || Is(container, Kind::kTuple))
    return container.node()->sequence[Index(key, Length(container))];
  throw Error("TypeError", "value is not subscriptable");
}
Value GetOr(const Value& container, const Value& key, Value fallback) {
  if (Is(container, Kind::kChainMap))
    return Contains(container, key) ? Get(container, key) : fallback;
  if (!Is(container, Kind::kDict))
    throw Error("TypeError", "get requires a dictionary");
  auto& p = container.node();
  auto it = p->index.find(Key(key));
  return it == p->index.end() ? fallback : p->entries[it->second].second;
}
void Put(const Value& container, const Value& key, Value value) {
  if (!container.node())
    throw Error("TypeError", "assignment requires a container");
  Mutable(container);
  if (Is(container, Kind::kDict)) {
    auto& p = container.node();
    auto [it, added] = p->index.emplace(Key(key), p->entries.size());
    if (added)
      p->entries.emplace_back(key, std::move(value));
    else
      p->entries[it->second].second = std::move(value);
  } else if (Is(container, Kind::kList)) {
    container.node()->sequence[Index(key, Length(container))] =
        std::move(value);
  } else
    throw Error("TypeError", "unsupported assignment");
}
void Erase(const Value& container, const Value& key) {
  Mutable(container);
  if (Is(container, Kind::kDict)) {
    auto& p = container.node();
    auto it = p->index.find(Key(key));
    if (it == p->index.end()) throw Error("KeyError", Repr(key));
    p->entries.erase(p->entries.begin() + it->second);
    p->index.clear();
    for (size_t i = 0; i < p->entries.size(); ++i)
      p->index[Key(p->entries[i].first)] = i;
  } else if (Is(container, Kind::kList)) {
    auto& p = container.node();
    p->sequence.erase(p->sequence.begin() + Index(key, Length(container)));
  } else
    throw Error("TypeError", "unsupported deletion");
}
Values Iterate(const Value& value) {
  if (Is(value, Kind::kList) || Is(value, Kind::kTuple) ||
      Is(value, Kind::kSet))
    return value.node()->sequence;
  Values result;
  if (Is(value, Kind::kChainMap)) {
    auto keys = Dict();
    const auto& maps = value.node()->sequence;
    for (auto it = maps.rbegin(); it != maps.rend(); ++it)
      for (const auto& key : Iterate(*it)) Put(keys, key, {});
    return Iterate(keys);
  } else if (Is(value, Kind::kBytes)) {
    for (unsigned char c : value.node()->text) result.emplace_back(static_cast<int>(c));
  } else if (Is(value, Kind::kDict)) {
    for (const auto& [k, v] : value.node()->entries) result.push_back(k);
  } else if (Is(value, Kind::kString)) {
    for (char c : value.string()) result.emplace_back(std::string(1, c));
  } else if (Is(value, Kind::kIterator)) {
    auto& p = value.node();
    const auto& seq = p->sequence;
    while (p->position < seq.size()) result.push_back(seq[p->position++]);
  } else
    throw Error("TypeError", "value is not iterable");
  return result;
}
Value Slice(const Value& value, const Value& start, const Value& stop,
            const Value& step) {
  auto b = Normalize(value, start, stop, step);
  Values result;
  for (int64_t i = b.start; b.step > 0 ? i < b.stop : i > b.stop; i += b.step)
    result.push_back(Get(value, i));
  if (Is(value, Kind::kString)) {
    std::string s;
    for (const auto& v : result) s += v.string();
    return Value(s);
  }
  return Is(value, Kind::kTuple) ? Tuple(std::move(result))
                                 : List(std::move(result));
}
void PutSlice(const Value& value, const Value& start, const Value& stop,
              const Value& step, const Value& replacement) {
  if (!Is(value, Kind::kList))
    throw Error("TypeError", "slice assignment needs a list");
  Mutable(value);
  auto b = Normalize(value, start, stop, step);
  auto seq = Iterate(replacement);
  auto& dst = value.node()->sequence;
  if (b.step == 1) {
    auto end = std::max(b.start, b.stop);
    dst.erase(dst.begin() + b.start, dst.begin() + end);
    dst.insert(dst.begin() + b.start, seq.begin(), seq.end());
  } else {
    size_t j = 0;
    for (int64_t i = b.start; b.step > 0 ? i < b.stop : i > b.stop;
         i += b.step) {
      if (j >= seq.size())
        throw Error("ValueError", "extended slice size differs");
      dst[i] = seq[j++];
    }
    if (j != seq.size())
      throw Error("ValueError", "extended slice size differs");
  }
}
Value ShallowCopy(const Value& value) {
  if (Is(value, Kind::kDict)) return Dict(value.node()->entries);
  if (Is(value, Kind::kList)) return List(value.node()->sequence);
  if (Is(value, Kind::kSet)) return Set(value.node()->sequence);
  if (Is(value, Kind::kObject)) {
    auto p = std::make_shared<Node>(*value.node());
    p->attributes = ShallowCopy(p->attributes);
    return Value(p);
  }
  return value;
}

}  // namespace kagg::opponents::compiled
