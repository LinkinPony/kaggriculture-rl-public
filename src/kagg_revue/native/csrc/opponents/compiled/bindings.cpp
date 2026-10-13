#include "opponents/compiled/bindings.hpp"

namespace kagg::opponents::compiled {
namespace py = pybind11;
Value FromPython(py::handle value) {
  if (value.is_none()) return {};
  if (py::isinstance<py::bool_>(value)) return py::cast<bool>(value);
  if (py::isinstance<py::int_>(value)) return py::cast<int64_t>(value);
  if (py::isinstance<py::float_>(value)) return py::cast<double>(value);
  if (py::isinstance<py::str>(value)) return py::cast<std::string>(value);
  if (py::isinstance<py::bytes>(value)) return Bytes(py::cast<std::string>(value));
  if (py::isinstance<py::dict>(value)) {
    auto result = Dict();
    for (auto item : py::reinterpret_borrow<py::dict>(value))
      Put(result, FromPython(item.first), FromPython(item.second));
    return result;
  }
  if (py::isinstance<py::list>(value) || py::isinstance<py::tuple>(value)) {
    Values result;
    for (auto item : py::reinterpret_borrow<py::sequence>(value))
      result.push_back(FromPython(item));
    return py::isinstance<py::tuple>(value) ? Tuple(std::move(result))
                                            : List(std::move(result));
  }
  throw py::value_error("unsupported compiled policy asset value");
}
py::object ToPython(const Value& value) {
  if (value.none()) return py::none();
  if (value.boolean()) return py::bool_(value.integer_value());
  if (value.integer()) return py::int_(value.integer_value());
  if (value.numeric()) return py::float_(value.number());
  if (Is(value, Kind::kString)) return py::str(value.string());
  if (Is(value, Kind::kBytes)) return py::bytes(value.node()->text);
  if (Is(value, Kind::kDict)) {
    py::dict result;
    for (const auto& [k, v] : value.node()->entries)
      result[ToPython(k)] = ToPython(v);
    return result;
  }
  if (Is(value, Kind::kList) || Is(value, Kind::kTuple) ||
      Is(value, Kind::kSet)) {
    py::list result;
    for (const auto& v : value.node()->sequence) result.append(ToPython(v));
    return result;
  }
  throw py::value_error(
      "only data values may leave compiled policy diagnostics");
}
}  // namespace kagg::opponents::compiled
