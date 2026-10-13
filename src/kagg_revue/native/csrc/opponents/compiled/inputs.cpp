// Exact eight-wide, eight-depth beam search from the frozen public input planner.
#include "opponents/compiled/inputs.hpp"

#include <algorithm>
#include <array>
#include <cmath>

#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
namespace {
struct Target {
  int x, y, birth, until, capacity, baseline, harvest;
  Value crop;
  std::vector<int> water;
};

int Integer(const Value& value) {
  if (!value.integer() || std::abs(value.number()) > 1000000)
    throw Error("TypeError", "typed input planner requires bounded integers");
  return static_cast<int>(value.integer_value());
}

std::vector<Target> Targets(const Value& values) {
  if (!Is(values, Kind::kDict) || values.node()->entries.size() > 128)
    throw Error("TypeError", "typed input planner requires coordinate targets");
  std::vector<Target> targets;
  for (const auto& [position, value] : values.node()->entries) {
    if (!Is(position, Kind::kTuple) || Length(position) != 2)
      throw Error("TypeError", "typed input planner requires coordinate pairs");
    auto crop = Get(value, "crop");
    if (!Is(crop, Kind::kString) || (crop.string() != "WHEAT" && crop.string() != "CARROT"))
      throw Error("TypeError", "unsupported input crop");
    const auto harvest = Get(value, "harvest");
    Target target{Integer(Get(position, 0)), Integer(Get(position, 1)),
                  Integer(Get(value, "birth")), Integer(Get(value, "until")),
                  Integer(Get(value, "cap")), Integer(Get(value, "yield")),
                  harvest.none() ? -1 : Integer(harvest), crop, {}};
    const auto water = Get(value, "water");
    if (!Is(water, Kind::kList)) throw Error("TypeError", "expected water schedule");
    for (const auto& item : water.node()->sequence) {
      const int turn = Integer(item);
      if (turn < 0) throw Error("TypeError", "negative water schedule");
      target.water.push_back(turn);
      target.baseline += turn / 24 <= target.until ? 2 : 1;
    }
    targets.push_back(std::move(target));
  }
  return targets;
}

struct Candidate {
  double score = 0;
  int64_t gross = 0;
  int now = 0, x = 0, y = 0, length = 0, wheat = 0, carrot = 0;
  std::array<int, 8> path{};
  unsigned __int128 used = 0;
};

bool Earlier(const Candidate& a, const Candidate& b, const std::vector<Target>& targets) {
  if (a.score != b.score) return a.score > b.score;
  if (a.gross != b.gross) return a.gross > b.gross;
  if (a.now != b.now) return a.now < b.now;
  for (int i = 0; i < std::min(a.length, b.length); ++i) {
    const auto& x = targets[a.path[i]];
    const auto& y = targets[b.path[i]];
    if (x.x != y.x) return x.x < y.x;
    if (x.y != y.y) return x.y < y.y;
    if (x.crop.string() != y.crop.string()) return x.crop.string() < y.crop.string();
    if (x.birth != y.birth) return x.birth < y.birth;
  }
  return a.length < b.length;
}
}  // namespace

std::optional<Value> InputPath(Context& context, const ScopePtr& scope) {
  const auto gain = scope->Global("_r51_input_gain");
  const auto start = scope->Global("_r62_input_start");
  if (!Is(gain, Kind::kFunction) || gain.node()->function->code != &Code_544c29264f2b5df724f9 ||
      !Is(start, Kind::kFunction) || start.node()->function->code != &Code_470ad8110bfbba9699a9)
    return std::nullopt;
  for (const char* name : {"int", "max", "abs", "len", "range", "frozenset", "list"}) {
    if (Contains(scope->globals, name)) return std::nullopt;
  }
  const auto observation = scope->Local("obs");
  std::vector<Target> targets;
  int step, wheat_price, carrot_price, inventory;
  try {
    targets = Targets(scope->Local("targets"));
    step = Integer(Get(observation, "step"));
    if (step < 0) return std::nullopt;
    const auto market = Get(observation, "market");
    const auto prices = Get(market, "prices");
    wheat_price = std::max(1, Integer(Get(prices, "WHEAT")) - 2);
    carrot_price = std::max(1, Integer(Get(prices, "CARROT")) - 2);
    inventory = Integer(Get(Get(market, "inventory"), "FERTILIZER"));
  } catch (const Error&) {
    return std::nullopt;
  }
  const int day = step / 24;
  const auto initial = Call(context, start,
      {{observation, scope->Local("action"), scope->Local("index")}, {}});
  const auto position = Get(initial, 1);
  Candidate first;
  first.now = Integer(Get(initial, 0));
  first.x = Integer(Get(position, 0));
  first.y = Integer(Get(position, 1));
  const auto quote = Call(context, scope->Global("_r37_market_price"),
                          {{"FERTILIZER", inventory - 16}, {}});
  const int fertilizer = std::max(1, Integer(quote) + 2);
  std::vector<Candidate> beam{first}, expanded;
  std::optional<Candidate> best;
  const auto earlier = [&](const Candidate& a, const Candidate& b) {
    return Earlier(a, b, targets);
  };
  for (int depth = 0; depth < 8; ++depth) {
    expanded.clear();
    for (const auto& parent : beam) {
      for (size_t i = 0; i < targets.size(); ++i) {
        const auto bit = static_cast<unsigned __int128>(1) << i;
        if (parent.used & bit) continue;
        const auto& target = targets[i];
        const int arrival = parent.now + std::abs(parent.x - target.x) + std::abs(parent.y - target.y);
        if (arrival >= day * 24 + 23 || target.harvest < 0 || target.harvest <= arrival) continue;
        int extra = 0;
        for (int turn : target.water) {
          extra += arrival < turn && turn <= target.harvest && day <= turn / 24 &&
                   turn / 24 <= day + 2 && turn / 24 > target.until;
        }
        const int amount = std::max(0, std::min(extra, target.capacity - target.baseline));
        if (!amount) continue;
        Candidate child = parent;
        const bool wheat = target.crop.string() == "WHEAT";
        child.gross += static_cast<int64_t>(amount) * (wheat ? wheat_price : carrot_price);
        child.path[child.length++] = i;
        child.score = child.gross - 1.5 * fertilizer * child.length;
        child.now = arrival + 1;
        child.x = target.x;
        child.y = target.y;
        child.used |= bit;
        child.wheat += wheat ? amount : 0;
        child.carrot += wheat ? 0 : amount;
        expanded.push_back(child);
      }
    }
    if (expanded.empty()) break;
    std::stable_sort(expanded.begin(), expanded.end(), earlier);
    beam.assign(expanded.begin(), expanded.begin() + std::min<size_t>(8, expanded.size()));
    if (depth >= 2 && (!best || earlier(beam[0], *best))) best = beam[0];
  }
  Values path;
  if (best) {
    for (int i = 0; i < best->length; ++i) {
      const auto& target = targets[best->path[i]];
      path.push_back(Tuple({target.x, target.y, target.crop, target.birth}));
    }
  }
  return Tuple({List(std::move(path)), Dict({{"WHEAT", best ? best->wheat : 0},
                                            {"CARROT", best ? best->carrot : 0}})});
}
}  // namespace kagg::opponents::compiled
