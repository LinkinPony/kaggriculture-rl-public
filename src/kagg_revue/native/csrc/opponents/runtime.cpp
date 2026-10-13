#include "opponents/runtime.hpp"

#include <stdexcept>

namespace kagg::opponents {

Session::Session(SharedPortfolio portfolio, int maximum_orders)
    : portfolio_(std::move(portfolio)),
      maximum_orders_(maximum_orders),
      policy_(Router(portfolio_)) {
  if (maximum_orders < 1)
    throw std::invalid_argument("maximum orders must be positive");
  if (portfolio_->compiled_program)
    policy_.emplace<compiled::Policy>(portfolio_->compiled_program);
  else if (portfolio_->kind == "farming_v4")
    policy_.emplace<Farming>(portfolio_);
  else if (portfolio_->kind == "kaito_v58")
    policy_.emplace<Kaito>(portfolio_);
  else if (portfolio_->kind == "boatlee_v29")
    policy_.emplace<Boatlee>(portfolio_);
  else if (portfolio_->kind == "shop_router_0908")
    policy_.emplace<ShopRouter>(portfolio_);
  else if (portfolio_->kind == "shop_router_0909")
    policy_.emplace<ReactiveShopRouter>(portfolio_);
  else if (portfolio_->kind != "router_95")
    throw std::invalid_argument("unknown native opponent");
}

PlayerAction Session::Act(const Engine& engine, int player) {
  if (player < 0 || player > 1)
    throw std::invalid_argument("player must be 0 or 1");
  auto result = std::visit(
      [&](auto& policy) { return policy.Act(engine, player); }, policy_);
  if (result.market.size() > static_cast<size_t>(maximum_orders_))
    result.market.resize(maximum_orders_);
  return result;
}
compiled::Value Session::Diagnostics() const {
  if (auto policy = std::get_if<compiled::Policy>(&policy_)) return policy->Diagnostics();
  return compiled::Dict();
}

void Session::EnableProfiling() {
  std::get<compiled::Policy>(policy_).EnableProfiling();
}

compiled::Value Session::Profile() const {
  return std::get<compiled::Policy>(policy_).Profile();
}

}  // namespace kagg::opponents
