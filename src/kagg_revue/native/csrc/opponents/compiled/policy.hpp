// Shared compiled program, private native episode state, and engine adapter.
#pragma once

#include <array>

#include "engine.hpp"
#include "opponents/compiled/runtime.hpp"

namespace kagg::opponents::compiled {
struct Program {
  std::string kind;
  Context context;
  Value prototype;
  Program(std::string name, std::vector<Value> constants);
};
class Policy {
 public:
  explicit Policy(std::shared_ptr<const Program> program);
  Policy(const Policy& other);
  Policy(Policy&&) noexcept = default;
  Policy& operator=(Policy&&) noexcept = default;
  PlayerAction Act(const Engine& engine, int player);
  Value Diagnostics() const;
  void EnableProfiling() { profiling_ = true; timings_.fill(0); decisions_ = 0; }
  Value Profile() const;

 private:
  std::shared_ptr<const Program> program_;
  Context context_;
  Value globals_;
  bool profiling_ = false;
  std::array<double, 4> timings_{};
  int64_t decisions_ = 0;
};
Value Observation(const Engine& engine, int player);
Value Configuration(const Config& config);
PlayerAction Action(const Value& value, int maximum_orders);
}  // namespace kagg::opponents::compiled
