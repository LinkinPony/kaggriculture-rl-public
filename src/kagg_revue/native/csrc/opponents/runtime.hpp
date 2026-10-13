// Episode-local mutable strategy state; all route data is shared and immutable.
#pragma once

#include <pybind11/pybind11.h>

#include <variant>

#include "opponents/boatlee.hpp"
#include "opponents/compiled/policy.hpp"
#include "opponents/farming.hpp"
#include "opponents/kaito.hpp"
#include "opponents/router.hpp"
#include "opponents/shop.hpp"
#include "opponents/shop_reactive.hpp"

namespace kagg::opponents {

class Session {
 public:
  Session(SharedPortfolio portfolio, int maximum_orders);
  PlayerAction Act(const Engine& engine, int player);
  const std::string& kind() const { return portfolio_->kind; }
  compiled::Value Diagnostics() const;
  void EnableProfiling();
  compiled::Value Profile() const;

 private:
  SharedPortfolio portfolio_;
  int maximum_orders_;
  std::variant<Router, Farming, Kaito, Boatlee, ShopRouter, ReactiveShopRouter, compiled::Policy> policy_;
};

void Bind(pybind11::module_& module);

}  // namespace kagg::opponents
