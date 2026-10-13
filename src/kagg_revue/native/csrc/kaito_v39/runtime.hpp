// Source-authenticated native hot path for the frozen Kaito v39 notebook.
#pragma once

#include <memory>

#include "engine.hpp"
#include "kaito_v39/portfolio.hpp"
#include "types.hpp"

namespace pybind11 {
class module_;
}

namespace kagg::kaito_v39 {

class Session {
 public:
  explicit Session(std::shared_ptr<const Portfolio> portfolio);
  ~Session();
  Session(Session&&) noexcept;
  Session& operator=(Session&&) noexcept;
  Session(const Session& other);
  Session& operator=(const Session&) = delete;

  PlayerAction Act(const Engine& engine, int player);

 private:
  struct Impl;
  std::unique_ptr<Impl> impl_;
};

void Bind(pybind11::module_& module);

}  // namespace kagg::kaito_v39
