// Read-only game data for planners; sourced from the engine's rule tables.

#include <pybind11/pybind11.h>

#include "types.hpp"

namespace py = pybind11;

namespace kagg {
namespace {

py::dict GameRules() {
  py::dict crops;
  for (int crop_index = 0; crop_index < kNumCrops; ++crop_index) {
    const CropData& crop = kCrops[crop_index];
    py::dict entry;
    entry["seed_cost"] = crop.seed_cost;
    entry["first_yield_day"] = crop.first_yield_day;
    entry["max_yield_day"] = crop.max_yield_day;
    entry["interval"] = crop.interval;
    entry["max_yield"] = crop.max_yield;
    entry["ongoing"] = crop.ongoing;
    crops[kItemNames[crop_index]] = entry;
  }

  py::dict animals;
  for (int animal_index = 0; animal_index < kNumAnimals; ++animal_index) {
    const AnimalData& animal = kAnimals[animal_index];
    py::dict entry;
    entry["cost"] = animal.cost;
    entry["structure"] =
        animal.structure == StructureKind::kCoop ? "COOP" : "PASTURE";
    entry["first_yield_day"] = animal.first_yield_day;
    entry["interval"] = animal.interval;
    entry["max_held"] = animal.max_held;
    entry["product"] = kItemNames[animal.product];
    animals[kItemNames[item::kGoose + animal_index]] = entry;
  }

  py::list products;
  py::dict product_base_prices;
  for (int item_index = 0; item_index < kNumProducts; ++item_index) {
    products.append(kItemNames[item_index]);
    product_base_prices[kItemNames[item_index]] =
        kDefaultMarketParams[item_index].base;
  }

  py::list land_prices;
  for (const int64_t price : kLandPrices) land_prices.append(price);

  py::dict shops;
  for (const ShopData& shop : kShops) {
    py::list demanded_products;
    for (int product_index = 0; product_index < shop.n_products;
         ++product_index) {
      demanded_products.append(kItemNames[shop.products[product_index]]);
    }
    py::dict entry;
    entry["products"] = demanded_products;
    entry["quantity_multiplier"] = shop.n_products == 1 ? 2 : 1;
    shops[shop.name] = entry;
  }

  py::dict out;
  out["crops"] = crops;
  out["animals"] = animals;
  out["products"] = products;
  out["product_base_prices"] = product_base_prices;
  out["land_prices"] = land_prices;
  out["shops"] = shops;
  return out;
}

}  // namespace

void BindRules(py::module_& module) {
  module.def("game_rules", &GameRules,
             "Return planner-facing game data from the native rule tables.");
}

}  // namespace kagg
