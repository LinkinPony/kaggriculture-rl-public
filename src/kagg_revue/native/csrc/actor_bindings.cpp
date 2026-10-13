// Python boundary for the deploy-visible observation encoder.

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <array>
#include <string>
#include <vector>

#include "actor_encoding.hpp"
#include "py_convert.hpp"

namespace py = pybind11;

namespace kagg {
namespace {

int ShopIndex(const std::string& name) {
  for (int index = 0; index < kNumShops; ++index) {
    if (name == kShops[index].name) return index;
  }
  return -1;
}

struct ParsedObservation {
  Config config;
  Farm own_farm;
  Farm opponent_farm;
  PrivateState own_private;
  actor::SeatView view;
};

std::array<double, kNumItems> ParseOpponentShedEstimate(py::handle value) {
  std::array<double, kNumItems> result{};
  if (value.is_none()) return result;
  const auto sequence = py::reinterpret_borrow<py::sequence>(value);
  for (int index = 0; index < kNumItems && index < static_cast<int>(sequence.size()); ++index) {
    result[index] = py::cast<double>(sequence[index]);
  }
  return result;
}

void ParseObservation(const py::dict& observation, py::object configuration,
                      const std::array<double, kNumItems>& opponent_shed_estimate,
                      ParsedObservation* output) {
  output->config = pyconv::ParseConfig(configuration);
  const int player = py::cast<int>(observation["player"]);
  if (player < 0 || player > 1) {
    throw py::value_error("observation player must be 0 or 1");
  }
  const int step = py::cast<int>(observation["step"]);
  const auto farms = py::reinterpret_borrow<py::list>(observation["farms"]);
  output->own_farm = pyconv::ParseFarm(
      py::reinterpret_borrow<py::dict>(farms[player]), output->config.board_size);
  output->opponent_farm = pyconv::ParseFarm(
      py::reinterpret_borrow<py::dict>(farms[1 - player]), output->config.board_size);
  output->own_private =
      pyconv::ParsePrivate(py::reinterpret_borrow<py::dict>(observation["private"]));

  actor::SeatView& view = output->view;
  view.config = &output->config;
  view.step = step;
  view.own_farm = &output->own_farm;
  view.opponent_farm = &output->opponent_farm;
  view.own_private = &output->own_private;
  view.opponent_shed_estimate = opponent_shed_estimate;
  const auto market = py::reinterpret_borrow<py::dict>(observation["market"]);
  const auto inventory = py::reinterpret_borrow<py::dict>(market["inventory"]);
  const auto prices = py::reinterpret_borrow<py::dict>(market["prices"]);
  for (int product = 0; product < kNumProducts; ++product) {
    view.market_inventory[product] = py::cast<int64_t>(inventory[kItemNames[product]]);
    view.market_prices[product] = py::cast<int64_t>(prices[kItemNames[product]]);
  }
  view.shop_counts.fill(0);
  const auto town = py::reinterpret_borrow<py::dict>(observation["town"]);
  for (py::handle value : py::reinterpret_borrow<py::list>(town["unlocked_shops"])) {
    const int shop = ShopIndex(py::cast<std::string>(value));
    if (shop >= 0) ++view.shop_counts[shop];
  }
}

template <typename T>
py::array_t<T> MakeArray(const std::vector<py::ssize_t>& shape) {
  return py::array_t<T>(shape);
}

py::tuple EncodeArrays(const py::dict& observation, py::object configuration,
                       int unit_limit, py::handle opponent_shed_estimate) {
  if (unit_limit < 1) throw py::value_error("unit_limit must be positive");
  ParsedObservation parsed;
  ParseObservation(observation, configuration,
                   ParseOpponentShedEstimate(opponent_shed_estimate), &parsed);
  const int board_size = parsed.config.board_size;

  auto board = MakeArray<float>({2, actor::kBoardChannels, board_size, board_size});
  const size_t farm_size =
      static_cast<size_t>(actor::kBoardChannels) * board_size * board_size;
  actor::EncodeBoard(parsed.config, parsed.own_farm, parsed.view.step, board.mutable_data());
  actor::EncodeBoard(parsed.config, parsed.opponent_farm, parsed.view.step,
                     board.mutable_data() + farm_size);
  auto units = MakeArray<float>({2, unit_limit, actor::kUnitFeat});
  const size_t unit_size = static_cast<size_t>(unit_limit) * actor::kUnitFeat;
  actor::EncodeUnits(parsed.config, parsed.own_farm, &parsed.own_private, parsed.view.step,
                     unit_limit, units.mutable_data());
  actor::EncodeUnits(parsed.config, parsed.opponent_farm, nullptr, parsed.view.step,
                     unit_limit, units.mutable_data() + unit_size);
  auto global = MakeArray<float>({actor::kGlobalFeat});
  actor::EncodeGlobal(parsed.view, global.mutable_data());
  return py::make_tuple(std::move(board), std::move(units), std::move(global));
}

py::dict EncodeActorObservation(const py::dict& observation, py::object configuration,
                                int unit_limit, py::handle opponent_shed_estimate) {
  const py::tuple arrays = EncodeArrays(observation, configuration, unit_limit,
                                       opponent_shed_estimate);
  py::dict output;
  output["board"] = arrays[0];
  output["units"] = arrays[1];
  output["global"] = arrays[2];
  return output;
}

py::dict ActorEncoderSpec() {
  py::dict output;
  output["version"] = actor::kEncoderSpecVersion;
  output["board_channels"] = actor::kBoardChannels;
  output["unit_feat"] = actor::kUnitFeat;
  output["unit_base_feat"] = actor::kUnitBaseFeat;
  output["unit_priv_slice"] =
      py::make_tuple(actor::kUnitPrivFirst, actor::kUnitPrivLast);
  output["unit_order_slice"] =
      py::make_tuple(actor::kUnitOrderFirst, actor::kUnitFeat);
  output["global_feat"] = actor::kGlobalFeat;
  output["num_items"] = kNumItems;
  output["num_crops"] = kNumCrops;
  output["num_animals"] = kNumAnimals;
  output["num_products"] = kNumProducts;
  std::vector<std::string> item_names;
  item_names.reserve(kNumItems);
  for (int index = 0; index < kNumItems; ++index) {
    item_names.emplace_back(kItemNames[index]);
  }
  output["item_names"] = item_names;
  return output;
}

}  // namespace

void BindActorEncoding(py::module_& module) {
  module.def("actor_encoder_spec", &ActorEncoderSpec,
             "Return the deploy-visible observation encoder identity and shapes.");
  module.def("encode_actor_observation", &EncodeActorObservation,
             py::arg("observation"), py::arg("configuration"),
             py::arg("unit_limit"), py::arg("opponent_shed_estimate") = py::none(),
             "Encode one official seat observation without action masks or simulator truth.");
  module.def("encode_official_observation_numeric", &EncodeArrays,
             py::arg("observation"), py::arg("configuration"),
             py::arg("unit_limit"), py::arg("opponent_shed_estimate") = py::none(),
             "Parse the official boundary once and return contiguous actor arrays.");
}

}  // namespace kagg
