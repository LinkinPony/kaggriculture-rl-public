// Python is used only to authenticate/load assets and for diagnostics.
#include <pybind11/stl.h>

#include <functional>
#include <cmath>
#include <limits>

#include "core/engine.hpp"
#include "opponents/runtime.hpp"
#include "opponents/compiled/bindings.hpp"
#include "opponents/compiled/profiling.hpp"
#include "py_convert.hpp"

namespace kagg::opponents {
namespace py = pybind11;

namespace {

PlayerAction ParseTapeAction(py::dict raw) {
  auto action = pyconv::ParsePlayerAction(raw, std::numeric_limits<int>::max());
  const auto market = py::cast<py::list>(raw["market"]);
  // A zero-quantity order is a real slot in the scripts' intermediate queues.
  // The official parser removes its type; restore it until policy processing
  // ends.
  for (size_t i = 0; i < action.market.size(); ++i) {
    if (action.market[i] || market[i].is_none()) continue;
    if (!py::isinstance<py::list>(market[i])) continue;
    auto order = py::list(market[i]);
    if (order.size() != 3 || py::cast<int64_t>(order[2]) > 0) continue;
    const int64_t count = py::cast<int64_t>(order[2]);
    order[2] = 1;
    py::dict replacement;
    replacement["market"] = py::make_tuple(order);
    // ParsePlayerAction expects a list for the market boundary.
    replacement["market"] = py::list(replacement["market"]);
    const auto parsed = pyconv::ParsePlayerAction(replacement, 1);
    if (!parsed.market.empty() && parsed.market[0]) {
      action.market[i] = parsed.market[0];
      action.market[i]->remaining = count;
    }
  }
  return action;
}

void LoadShopRouting(py::dict model, Portfolio* portfolio) {
  if (py::cast<std::string>(model["kind"]) != "mmpq_multi_entry_v1" ||
      py::cast<int>(model["default"]) != 0)
    throw py::value_error("unsupported shop routing model");
  const auto stages = py::cast<py::list>(model["stages"]);
  if (stages.size() != 2) throw py::value_error("shop router requires two stages");
  for (size_t i = 0; i < stages.size(); ++i) {
    const auto stage = py::cast<py::dict>(stages[i]);
    const auto tree = py::cast<py::dict>(stage["tree"]);
    const auto left = py::cast<py::dict>(tree["left"]);
    const auto right = py::cast<py::dict>(tree["right"]);
    const ShopStage parsed{py::cast<int>(stage["step"]),
                           py::cast<int>(tree["feature"]),
                           py::cast<double>(tree["threshold"]),
                           py::cast<int>(left["choice"]),
                           py::cast<int>(right["choice"])};
    if (stage.size() != 2 || tree.size() != 4 || left.size() != 1 ||
        right.size() != 1 || parsed.step != (i == 0 ? 144 : 648) ||
        parsed.feature != (i == 0 ? 23 : 71) ||
        !std::isfinite(parsed.threshold) || parsed.left < 0 ||
        parsed.left >= 4 || parsed.right < 0 || parsed.right >= 4)
      throw py::value_error("unsupported shop routing stage");
    portfolio->shop_stages.push_back(parsed);
  }
}

std::shared_ptr<Portfolio> LoadPortfolio(py::dict data) {
  auto portfolio = std::make_shared<Portfolio>();
  portfolio->kind = py::cast<std::string>(data["agent_id"]);
  if (data.contains("constants")) {
    compiled::Values constants;
    for (auto value : py::cast<py::list>(data["constants"])) constants.push_back(compiled::FromPython(value));
    portfolio->compiled_program = std::make_shared<compiled::Program>(portfolio->kind, std::move(constants));
    return portfolio;
  }
  for (auto raw_route : py::cast<py::list>(data["routes"])) {
    std::vector<PlayerAction> route;
    for (auto raw : py::cast<py::list>(raw_route))
      route.push_back(ParseTapeAction(py::cast<py::dict>(raw)));
    portfolio->routes.push_back(std::move(route));
  }
  const auto& kind = portfolio->kind;
  const size_t expected = kind == "router_95"     ? 5
                          : kind == "farming_v4"  ? 4
                          : kind == "kaito_v58"   ? 10
                          : kind == "boatlee_v29" ? 1
                          : kind == "shop_router_0908" ? 4
                          : kind == "shop_router_0909" ? 13
                                                  : 0;
  if (!expected || portfolio->routes.size() != expected)
    throw py::value_error("invalid opponent route count");
  if (kind == "shop_router_0908")
    LoadShopRouting(py::cast<py::dict>(data["model"]), portfolio.get());
  if (kind == "router_95") {
    for (auto raw_tree : py::cast<py::list>(data["policy"])) {
      std::vector<Node> tree;
      for (auto raw_node : py::cast<py::list>(raw_tree)) {
        auto n = py::cast<py::list>(raw_node);
        if (n.size() != 5) throw py::value_error("invalid router node");
        tree.push_back({py::cast<int>(n[0]), py::cast<int>(n[1]),
                        py::cast<int>(n[2]), py::cast<int>(n[3]),
                        py::cast<double>(n[4])});
      }
      std::vector<int> visited(tree.size());
      std::function<void(int)> validate = [&](int index) {
        if (index < 0 || index >= static_cast<int>(tree.size()) ||
            visited[index] == 1)
          throw py::value_error("invalid router graph");
        if (visited[index] == 2) return;
        visited[index] = 1;
        const auto& node = tree[index];
        if (node.feature < -2 || node.feature >= 64 || node.route < -1 ||
            node.route >= static_cast<int>(expected))
          throw py::value_error("invalid router feature or route");
        if (node.feature != -1) {
          validate(node.yes);
          validate(node.no);
        }
        visited[index] = 2;
      };
      validate(0);
      portfolio->trees.push_back(std::move(tree));
    }
    if (portfolio->trees.size() != 10)
      throw py::value_error("router requires ten blocks");
  }
  if (kind == "farming_v4") {
    portfolio->prefixes =
        py::cast<std::vector<std::vector<int>>>(data["prefixes"]);
    if (portfolio->prefixes.size() != expected)
      throw py::value_error("invalid prefix matrix");
    for (const auto& row : portfolio->prefixes)
      if (row.size() != expected) throw py::value_error("invalid prefix row");
  }
  portfolio->Prepare();
  return portfolio;
}

}  // namespace

void BindBatch(py::module_& module);

void Bind(py::module_& module) {
  py::class_<Portfolio, std::shared_ptr<Portfolio>>(module,
                                                    "NativeOpponentPortfolio")
      .def(py::init(&LoadPortfolio));
  py::class_<Session>(module, "NativeOpponentSession")
      .def(py::init(
          [](std::shared_ptr<Portfolio> portfolio, int maximum_orders) {
            return Session(std::move(portfolio), maximum_orders);
          }))
      .def("clone", [](const Session& session) { return Session(session); })
      .def("enable_profiling", &Session::EnableProfiling)
      .def("profile", [](const Session& session) { return compiled::ToPython(session.Profile()); });
  module.def("native_opponent_diagnostics", [](const Session& session) {
    return compiled::ToPython(session.Diagnostics());
  });
  module.def("native_compiled_closure_lifetimes", &compiled::ValidateClosureLifetimes);
  module.def("native_compiled_dictionary_get", &compiled::ValidateDictionaryGet);
  module.def("native_compiled_function_profile", [] {
    return compiled::ToPython(compiled::FunctionProfile());
  });
  module.def("native_opponent_action",
             [](const PyEngine& engine, int player, Session& session) {
               PlayerAction action;
               {
                 py::gil_scoped_release release;
                 action = session.Act(engine.raw_engine(), player);
               }
               return pyconv::PlayerActionToPy(action);
             });
  module.def("canonical_opponent_action",
             [](py::dict action, int maximum_orders) {
               return pyconv::PlayerActionToPy(
                   pyconv::ParsePlayerAction(action, maximum_orders));
             });
  BindBatch(module);
}

}  // namespace kagg::opponents
