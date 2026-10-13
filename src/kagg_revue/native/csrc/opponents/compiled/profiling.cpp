#include "opponents/compiled/profiling.hpp"

#include <chrono>
#include <cstdlib>

namespace kagg::opponents::compiled {
const bool kProfileFunctions = std::getenv("KAGG_NATIVE_FUNCTION_PROFILE") != nullptr;
namespace {
using Clock = std::chrono::steady_clock;
struct Timing {
  std::string name;
  int64_t calls = 0, inclusive = 0, exclusive = 0;
};
thread_local std::unordered_map<Code, Timing> timings;
thread_local int64_t accounted = 0;
struct Timer {
  Code code;
  const std::string& name;
  Clock::time_point start = Clock::now();
  int64_t children = accounted;
  ~Timer() {
    const int64_t elapsed =
        std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now() - start).count();
    const int64_t own = elapsed - (accounted - children);
    accounted += own;
    auto& row = timings[code];
    if (row.name.empty()) row.name = name;
    ++row.calls;
    row.inclusive += elapsed;
    row.exclusive += own;
  }
};
}  // namespace
Value ProfileCall(Context& context, const Function& function,
                  const std::string& name, const ScopePtr& scope) {
  Timer timer{function.code, name};
  return function.code(context, scope);
}
Value FunctionProfile() {
  Values rows;
  for (const auto& [code, row] : timings)
    rows.push_back(Dict({{"name", row.name}, {"calls", row.calls},
                         {"self_seconds", row.exclusive * 1e-9},
                         {"inclusive_seconds", row.inclusive * 1e-9}}));
  timings.clear();
  accounted = 0;
  return List(std::move(rows));
}
}  // namespace kagg::opponents::compiled
