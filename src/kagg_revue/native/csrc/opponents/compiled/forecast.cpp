#include "opponents/compiled/forecast.hpp"

#include <algorithm>
#include <limits>
#include <unordered_set>

#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
namespace {
uint64_t Encode(int64_t turn, int64_t item) {
  return (uint64_t{static_cast<uint32_t>(turn)} << 32) | static_cast<uint32_t>(item);
}
std::pair<int64_t, int64_t> Event(const Value& key) {
  if (!Is(key, Kind::kTuple) || key.node()->sequence.size() != 2)
    throw PortError("forecast stream has an unreviewed event key");
  const auto& values = key.node()->sequence;
  for (const auto& value : values)
    if (!value.integer() || value.integer_value() < 0 ||
        value.integer_value() >= std::numeric_limits<int32_t>::max())
      throw PortError("forecast event exceeds its reviewed integer range");
  return {values[0].integer_value(), values[1].integer_value()};
}
struct Stream {
  std::vector<std::pair<int64_t, int64_t>> events;
  std::unordered_set<uint64_t> lookup;
};
std::shared_ptr<const Stream> ReadStream(const Value& value) {
  if (!Is(value, Kind::kDict)) throw PortError("forecast stream must be a mapping");
  struct Cached {
    std::weak_ptr<Node> owner;
    std::shared_ptr<const Stream> stream;
  };
  // Only immutable source data is cached. Every game's observed events and
  // scores are recomputed; a reused allocation cannot inherit another stream.
  static thread_local std::unordered_map<const Node*, Cached> cache;
  const auto& node = value.node();
  if (node->frozen) {
    const auto found = cache.find(node.get());
    if (found != cache.end() && found->second.owner.lock() == node)
      return found->second.stream;
    if (cache.size() >= 512) {
      std::erase_if(cache, [](const auto& row) { return row.second.owner.expired(); });
      if (cache.size() >= 512) cache.clear();
    }
  }
  auto stream = std::make_shared<Stream>();
  stream->events.reserve(node->entries.size());
  stream->lookup.reserve(node->entries.size());
  for (const auto& [key, quantity] : node->entries) {
    const auto event = Event(key);
    stream->events.push_back(event);
    stream->lookup.insert(Encode(event.first, event.second));
  }
  std::sort(stream->events.begin(), stream->events.end());
  if (node->frozen) cache[node.get()] = {node, stream};
  return stream;
}
}  // namespace

std::optional<Value> Forecast(Context& context, const ScopePtr& scope) {
  // Rebound Python builtins retain the original generated implementation.
  for (const auto& name : {"int", "tuple", "sum"})
    if (Contains(scope->globals, name)) return std::nullopt;
  const auto top = scope->Global("_V92_P_TOP");
  const auto episode = scope->Global("_V92_EP");
  if (!top.integer() || top.integer_value() < 0 ||
      (!episode.none() && !episode.integer())) return std::nullopt;
  const auto observation = scope->Local("obs");
  const int64_t step = Get(observation, "step").integer_value();
  const auto shops = Get(Get(observation, "town"), "unlocked_shops");
  const auto pair = Tuple(Iterate(Slice(shops, {}, 2)));
  const auto loader = scope->Global("_v92_p_pair");
  const auto candidates = Call(context, loader, {{pair}, {}});
  // This exact packed-library loader is lazy, unlike the eager JSON variant.
  // Its returned event mappings are source data, only read by all consumers in
  // the authenticated portfolio. Freeze them once for safe index reuse/cloning.
  if (Is(loader, Kind::kFunction) &&
      loader.node()->function->code == &Code_2c1563d545db7df1f456) {
    for (const auto& candidate : Iterate(candidates)) {
      const auto events = Get(candidate, 1);
      if (!events.node()->frozen) Freeze(events);
    }
  }
  const auto seen = Get(scope->Local("st"), "obs");
  if (!Is(seen, Kind::kDict)) throw PortError("forecast observations must be a mapping");
  const int64_t low = step - 240;
  std::unordered_set<uint64_t> observed;
  std::vector<std::pair<int64_t, int64_t>> recent;
  for (const auto& [key, quantity] : seen.node()->entries) {
    const auto [turn, item] = Event(key);
    observed.insert(Encode(turn, item));
    if (turn >= low) recent.emplace_back(turn, item);
  }
  std::vector<std::pair<double, Value>> scored;
  for (const auto& candidate : Iterate(candidates)) {
    if (!episode.none()) {
      const auto candidate_episode = Get(candidate, 0);
      if (!candidate_episode.integer()) return std::nullopt;
      if ((candidate_episode.integer_value() & 1) == (episode.integer_value() & 1)) continue;
    }
    const auto events = Get(candidate, 1);
    const auto stream = ReadStream(events);
    const auto& expected = stream->lookup;
    int64_t matched = 0, extra = 0, missed = 0;
    const auto begin = std::lower_bound(stream->events.begin(), stream->events.end(),
                                        std::pair<int64_t, int64_t>{low, 0});
    for (auto entry = begin; entry != stream->events.end() && entry->first < step - 1; ++entry) {
      const auto [turn, item] = *entry;
        if (observed.contains(Encode(turn, item)) ||
            observed.contains(Encode(turn - 1, item)) ||
            observed.contains(Encode(turn + 1, item)))
          ++matched;
        else
          ++extra;
    }
    for (const auto& [turn, item] : recent)
      if (!expected.contains(Encode(turn, item)) &&
          !expected.contains(Encode(turn - 1, item)) &&
          !expected.contains(Encode(turn + 1, item)))
        ++missed;
    scored.emplace_back(matched - 0.5 * extra - 0.5 * missed, events);
  }
  std::stable_sort(scored.begin(), scored.end(),
                   [](const auto& left, const auto& right) { return left.first > right.first; });
  Values result;
  const size_t count = std::min(scored.size(), static_cast<size_t>(top.integer_value()));
  for (size_t i = 0; i < count; ++i) result.push_back(scored[i].second);
  return List(std::move(result));
}
}  // namespace kagg::opponents::compiled
