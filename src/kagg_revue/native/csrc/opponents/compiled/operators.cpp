#include <cmath>
#include <limits>
#include <string_view>

#include "opponents/compiled/value.hpp"

namespace kagg::opponents::compiled {
Value Inplace(const char* operation, const Value& left, const Value& right) {
  if (std::string_view(operation) == "Add" && Is(left, Kind::kList)) {
    if (left.node()->frozen) throw PortError("mutation of frozen route data");
    auto more = Iterate(right);
    auto& values = left.node()->sequence;
    values.insert(values.end(), more.begin(), more.end());
    return left;
  }
  return Binary(operation, left, right);
}
Value Unary(const char* operation, const Value& value) {
  const std::string_view op(operation);
  if (op == "Not") return !static_cast<bool>(value);
  if (op == "USub")
    return value.integer() ? Value(-value.integer_value())
                           : Value(-value.number());
  if (op == "UAdd") return value;
  if (op == "Invert") return ~value.integer_value();
  throw PortError("unsupported native unary operator");
}
Value Binary(const char* operation, const Value& left, const Value& right) {
  const std::string_view op(operation);
  if (op == "Eq") return Equal(left, right);
  if (op == "NotEq") return !Equal(left, right);
  if (op == "Is") return Identical(left, right);
  if (op == "IsNot") return !Identical(left, right);
  if (op == "In") return Contains(right, left);
  if (op == "NotIn") return !Contains(right, left);
  if (op == "Lt") return Compare(left, right) < 0;
  if (op == "LtE") return Compare(left, right) <= 0;
  if (op == "Gt") return Compare(left, right) > 0;
  if (op == "GtE") return Compare(left, right) >= 0;
  if (op == "Mod" && Is(left, Kind::kString)) {
    const Values values = Is(right, Kind::kTuple) ? Iterate(right) : Values{right};
    const auto& format = left.string();
    std::string result;
    size_t argument = 0;
    for (size_t i = 0; i < format.size(); ++i) {
      if (format[i] != '%') { result += format[i]; continue; }
      if (++i == format.size()) throw Error("ValueError", "incomplete format");
      if (format[i] == '%') { result += '%'; continue; }
      if (argument == values.size()) throw Error("TypeError", "too few format arguments");
      const auto& value = values[argument++];
      if (format[i] == 's') result += Repr(value);
      else if (format[i] == 'd') result += std::to_string(value.integer_value());
      else throw PortError("unreviewed string format conversion");
    }
    if (argument != values.size()) throw Error("TypeError", "too many format arguments");
    return result;
  }
  if (op == "Add") {
    if (Is(left, Kind::kString) && Is(right, Kind::kString))
      return left.string() + right.string();
    if ((Is(left, Kind::kList) && Is(right, Kind::kList)) ||
        (Is(left, Kind::kTuple) && Is(right, Kind::kTuple))) {
      auto seq = left.node()->sequence;
      const auto& add = right.node()->sequence;
      seq.insert(seq.end(), add.begin(), add.end());
      return Is(left, Kind::kTuple) ? Tuple(std::move(seq))
                                    : List(std::move(seq));
    }
  }
  if (op == "Mult" && (!left.numeric() || !right.numeric())) {
    const auto& seq = left.integer() ? right : left;
    int64_t count = (left.integer() ? left : right).integer_value();
    if (count < 0) count = 0;
    if (Is(seq, Kind::kString)) {
      std::string out;
      for (int64_t i = 0; i < count; ++i) out += seq.string();
      return out;
    }
    Values result;
    const auto items = Iterate(seq);
    for (int64_t i = 0; i < count; ++i)
      result.insert(result.end(), items.begin(), items.end());
    return Is(seq, Kind::kTuple) ? Tuple(std::move(result))
                                 : List(std::move(result));
  }
  if ((op == "BitOr" || op == "BitAnd" || op == "Sub") &&
      Is(left, Kind::kSet) && Is(right, Kind::kSet)) {
    Values out;
    for (const auto& v : Iterate(left))
      if (op == "BitOr" ||
          (op == "BitAnd" ? Contains(right, v) : !Contains(right, v)))
        out.push_back(v);
    if (op == "BitOr")
      for (const auto& v : Iterate(right)) out.push_back(v);
    return Set(std::move(out));
  }
  if (op == "BitOr" && Is(left, Kind::kDict) && Is(right, Kind::kDict)) {
    auto out = ShallowCopy(left);
    for (const auto& [k, v] : right.node()->entries) Put(out, k, v);
    return out;
  }
  if (!left.numeric() || !right.numeric())
    throw Error("TypeError", "invalid binary operands");
  const bool integral = left.integer() && right.integer();
  if (op == "Add")
    return integral ? Value(left.integer_value() + right.integer_value())
                    : Value(left.number() + right.number());
  if (op == "Sub")
    return integral ? Value(left.integer_value() - right.integer_value())
                    : Value(left.number() - right.number());
  if (op == "Mult")
    return integral ? Value(left.integer_value() * right.integer_value())
                    : Value(left.number() * right.number());
  if (op == "Div" || op == "FloorDiv" || op == "Mod") {
    if (!right.number()) throw Error("ZeroDivisionError", "division by zero");
    double q = std::floor(left.number() / right.number());
    if (op == "Div") return left.number() / right.number();
    if (op == "FloorDiv")
      return integral ? Value(static_cast<int64_t>(q)) : Value(q);
    if (integral)
      return left.integer_value() -
             static_cast<int64_t>(q) * right.integer_value();
    return left.number() - q * right.number();
  }
  if (op == "Pow") return std::pow(left.number(), right.number());
  if (op == "BitAnd") return left.integer_value() & right.integer_value();
  if (op == "BitOr") return left.integer_value() | right.integer_value();
  if (op == "LShift" || op == "RShift") {
    const int64_t value = left.integer_value(), shift = right.integer_value();
    if (shift < 0) throw Error("ValueError", "negative shift count");
    if (op == "RShift") return shift >= 63 ? Value(value < 0 ? -1 : 0) : Value(value >> shift);
    if (value < 0 || shift >= 63 || value > (std::numeric_limits<int64_t>::max() >> shift))
      throw PortError("left shift exceeds the reviewed integer range");
    return value << shift;
  }
  throw PortError("unsupported native binary operator: " + std::string(op));
}
}  // namespace kagg::opponents::compiled
