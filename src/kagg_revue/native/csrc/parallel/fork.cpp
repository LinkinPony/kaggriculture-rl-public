// Counterfactual roots include all engine, visible history and opponent memory.
#include "parallel/batch.hpp"

#include <stdexcept>

namespace kagg::parallel {

Batch::Batch(const Batch& source, const int64_t* parents, int count)
    : config_(source.config_), units_(source.units_), workers_(source.workers_),
      quantities_(source.quantities_) {
  engines_.reserve(count);
  history_.reserve(count);
  seats_.reserve(count);
  opponents_.reserve(source.opponents_.empty() ? 0 : count);
  teachers_.reserve(source.teachers_.empty() ? 0 : count);
  py::gil_scoped_release release;
  for (int i = 0; i < count; ++i) {
    const int parent = parents[i];
    engines_.push_back(source.engines_[parent]);
    history_.push_back(source.history_[parent]);
    seats_.push_back(source.seats_[parent]);
    if (!source.opponents_.empty()) opponents_.push_back(source.opponents_[parent].clone());
    if (!source.teachers_.empty()) teachers_.push_back(source.teachers_[parent].clone());
    if (!source.prepared_steps_.empty()) {
      prepared_steps_.push_back(source.prepared_steps_[parent]);
      prepared_opponents_.push_back(source.prepared_opponents_[parent]);
    }
  }
}

std::unique_ptr<Batch> Batch::Fork(py::array parents) const {
  if (parents.ndim() != 1 || parents.size() == 0 ||
      !(parents.flags() & py::array::c_style) || !parents.dtype().is(py::dtype::of<int64_t>())) {
    throw std::invalid_argument("fork requires a nonempty contiguous int64 parent index vector");
  }
  const auto* indices = static_cast<const int64_t*>(parents.data());
  for (py::ssize_t i = 0; i < parents.size(); ++i) {
    if (indices[i] < 0 || indices[i] >= size()) throw std::out_of_range("invalid fork parent");
  }
  return std::unique_ptr<Batch>(new Batch(*this, indices, parents.size()));
}

}  // namespace kagg::parallel
