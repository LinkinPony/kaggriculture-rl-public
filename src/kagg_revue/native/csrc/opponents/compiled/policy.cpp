#include "opponents/compiled/policy.hpp"

#include <ctime>

#include "opponents/compiled/generated/declarations.hpp"

namespace kagg::opponents::compiled {
namespace {
double ThreadSeconds() {
  timespec value;
  clock_gettime(CLOCK_THREAD_CPUTIME_ID, &value);
  return value.tv_sec + value.tv_nsec * 1e-9;
}
}  // namespace
Program::Program(std::string name, std::vector<Value> constants)
    : kind(std::move(name)) {
  context.constants = std::move(constants);
  prototype = Dict({{"__name__", "native_public_policy"}});
  Initialize(kind, context, prototype);
  if (!Contains(prototype, "agent"))
    throw PortError("compiled policy lacks an entry point");
  if (!Contains(prototype, "_native_entrypoint"))
    Put(prototype, "_native_entrypoint", Get(prototype, "agent"));
  for (const auto& key : {"_ROUTES", "_TAPES", "_E361_LIB"})
    if (Contains(prototype, key)) Freeze(Get(prototype, key));
  // Predecoded forecast streams are read-only. Keep each cache dictionary
  // private so unseen shop keys can still be inserted by individual games.
  for (const auto& key : {"_V92_P_LIB", "_E352_LIB"}) {
    auto cache = GetOr(prototype, key);
    if (Is(cache, Kind::kDict))
      for (const auto& [name, streams] : cache.node()->entries) Freeze(streams);
  }
  if (Contains(prototype, "_IMPL")) {
    auto chassis = Attribute(Get(prototype, "_IMPL"), "chassis");
    Freeze(Attribute(chassis, "routes"));
  }
}
Policy::Policy(std::shared_ptr<const Program> program)
    : program_(std::move(program)) {
  context_.constants = program_->context.constants;
  globals_ = DeepCopy(program_->prototype, true);
}
Policy::Policy(const Policy& other)
    : program_(other.program_),
      context_(other.context_),
      globals_(DeepCopy(other.globals_, true)) {}
PlayerAction Policy::Act(const Engine& engine, int player) {
  if (profiling_) {
    const double start = ThreadSeconds();
    double built, executed, converted;
    PlayerAction result;
    {
      auto observation = Observation(engine, player);
      auto configuration = Configuration(engine.config());
      built = ThreadSeconds();
      auto value = Call(context_, Get(globals_, "_native_entrypoint"), {{observation, configuration}, {}});
      executed = ThreadSeconds();
      result = Action(value, engine.config().max_market_orders);
      converted = ThreadSeconds();
    }
    const double ended = ThreadSeconds();
    timings_[0] += built - start;
    timings_[1] += executed - built;
    timings_[2] += converted - executed;
    timings_[3] += ended - converted;
    ++decisions_;
    return result;
  }
  auto observation = Observation(engine, player);
  auto configuration = Configuration(engine.config());
  auto value = Call(context_, Get(globals_, "_native_entrypoint"),
                    {{observation, configuration}, {}});
  return Action(value, engine.config().max_market_orders);
}
Value Policy::Profile() const {
  return Dict({{"decisions", decisions_}, {"observation_cpu_seconds", timings_[0]},
               {"policy_cpu_seconds", timings_[1]}, {"action_cpu_seconds", timings_[2]},
               {"destruction_cpu_seconds", timings_[3]},
               {"dynamic_calls", static_cast<int64_t>(context_.calls)}});
}
Value Policy::Diagnostics() const {
  auto result = Dict();
  for (const auto& [key, value] : globals_.node()->entries)
    if (Is(key, Kind::kString) && Is(value, Kind::kDict) &&
        (key.string().ends_with("REPORT") || key.string().ends_with("STATS")))
      Put(result, key, DeepCopy(value));
  if (Contains(globals_, "_IMPL"))
    Put(result, "chassis",
        DeepCopy(Attribute(Attribute(Get(globals_, "_IMPL"), "chassis"),
                           "diagnostics")));
  return result;
}
}  // namespace kagg::opponents::compiled
