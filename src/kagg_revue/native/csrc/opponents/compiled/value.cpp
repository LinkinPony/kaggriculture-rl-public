#include "opponents/compiled/value.hpp"

#include <algorithm>
#include <cmath>
#include <sstream>

namespace kagg::opponents::compiled {

Value::Value(const char* value) : Value(std::string(value)) {}
Value::Value(const std::string& value) {
  auto result = std::make_shared<Node>(Kind::kString);
  result->text = value;
  data_ = std::move(result);
}
bool Value::none() const {
  return std::holds_alternative<std::monostate>(data_);
}
bool Value::boolean() const { return std::holds_alternative<bool>(data_); }
bool Value::integer() const {
  return std::holds_alternative<int64_t>(data_) || boolean();
}
bool Value::numeric() const {
  return integer() || std::holds_alternative<double>(data_);
}
int64_t Value::integer_value() const {
  if (boolean()) return std::get<bool>(data_);
  if (std::holds_alternative<int64_t>(data_)) return std::get<int64_t>(data_);
  if (std::holds_alternative<double>(data_))
    return static_cast<int64_t>(std::get<double>(data_));
  throw Error("TypeError", "expected number: " + Repr(*this));
}
double Value::number() const {
  if (integer()) return static_cast<double>(integer_value());
  if (std::holds_alternative<double>(data_)) return std::get<double>(data_);
  throw Error("TypeError", "expected number: " + Repr(*this));
}
const std::string& Value::string() const {
  if (!Is(*this, Kind::kString)) throw Error("TypeError", "expected string");
  return node()->text;
}
Value::operator bool() const {
  if (none()) return false;
  if (numeric()) return number() != 0;
  const auto p = node();
  switch (p->kind) {
    case Kind::kString:
    case Kind::kBytes:
      return !p->text.empty();
    case Kind::kChainMap:
      return std::any_of(p->sequence.begin(), p->sequence.end(),
                         [](const Value& v) { return static_cast<bool>(v); });
    case Kind::kList:
    case Kind::kTuple:
    case Kind::kSet:
      return !p->sequence.empty();
    case Kind::kDict:
      return !p->entries.empty();
    default:
      return true;
  }
}
bool Identical(const Value& left, const Value& right) {
  if (left.none() || right.none()) return left.none() && right.none();
  if (left.boolean() && right.boolean())
    return left.integer_value() == right.integer_value();
  if (Is(left, Kind::kBuiltin) && Is(right, Kind::kBuiltin) &&
      left.node()->base.none() && right.node()->base.none())
    return left.node()->text == right.node()->text;
  return left.node() && left.node() == right.node();
}
bool Equal(const Value& left, const Value& right) {
  if (left.none() || right.none()) return left.none() && right.none();
  if (left.numeric() && right.numeric()) return left.number() == right.number();
  auto a = left.node(), b = right.node();
  if (!a || !b || a->kind != b->kind) return false;
  if (a == b) return true;
  switch (a->kind) {
    case Kind::kString:
    case Kind::kBytes:
      return a->text == b->text;
    case Kind::kList:
    case Kind::kTuple:
      if (a->sequence.size() != b->sequence.size()) return false;
      for (size_t i = 0; i < a->sequence.size(); ++i)
        if (!Equal(a->sequence[i], b->sequence[i])) return false;
      return true;
    case Kind::kSet:
      if (a->sequence.size() != b->sequence.size()) return false;
      for (const auto& v : a->sequence)
        if (!Contains(right, v)) return false;
      return true;
    case Kind::kDict:
      if (a->entries.size() != b->entries.size()) return false;
      for (const auto& [k, v] : a->entries)
        if (!Contains(right, k) || !Equal(v, Get(right, k))) return false;
      return true;
    default:
      return false;
  }
}
int Compare(const Value& left, const Value& right) {
  if (Equal(left, right)) return 0;
  if (left.numeric() && right.numeric())
    return left.number() < right.number() ? -1 : 1;
  if (Is(left, Kind::kString) && Is(right, Kind::kString))
    return left.string() < right.string() ? -1 : 1;
  if ((Is(left, Kind::kList) && Is(right, Kind::kList)) ||
      (Is(left, Kind::kTuple) && Is(right, Kind::kTuple))) {
    const auto& a = left.node()->sequence;
    const auto& b = right.node()->sequence;
    for (size_t i = 0; i < std::min(a.size(), b.size()); ++i) {
      int c = Compare(a[i], b[i]);
      if (c) return c;
    }
    return a.size() < b.size() ? -1 : 1;
  }
  throw Error("TypeError",
              "unorderable values " + Repr(left) + " and " + Repr(right));
}
std::string Key(const Value& value) {
  if (value.none()) return "n";
  if (value.integer()) return "i" + std::to_string(value.integer_value());
  if (value.numeric()) return "f" + Repr(value);
  if (Is(value, Kind::kString)) return "s" + value.string();
  if (Is(value, Kind::kTuple)) {
    std::string result = "t";
    for (const auto& x : value.node()->sequence) {
      auto part = Key(x);
      result += std::to_string(part.size()) + ":" + part;
    }
    return result;
  }
  throw Error("TypeError", "unhashable native value");
}
std::string Repr(const Value& value) {
  if (value.none()) return "None";
  if (value.boolean()) return value.integer_value() ? "True" : "False";
  if (value.integer()) return std::to_string(value.integer_value());
  if (value.numeric()) {
    std::ostringstream s;
    s.precision(17);
    s << value.number();
    return s.str();
  }
  if (Is(value, Kind::kString)) return value.string();
  if (Is(value, Kind::kObject) && value.node()->text.starts_with("exception:"))
    return Repr(Get(value.node()->attributes, "message"));
  if (Is(value, Kind::kList) || Is(value, Kind::kTuple) ||
      Is(value, Kind::kSet)) {
    std::string result = "[";
    for (const auto& item : value.node()->sequence) {
      if (result.size() > 1) result += ", ";
      result += Repr(item);
    }
    return result + "]";
  }
  if (Is(value, Kind::kDict)) {
    std::string result = "{";
    for (const auto& [k, v] : value.node()->entries) {
      if (result.size() > 1) result += ", ";
      result += Repr(k) + ": " + Repr(v);
    }
    return result + "}";
  }
  return "<native " + value.node()->text + ">";
}
int64_t Length(const Value& value) {
  if (Is(value, Kind::kString)) return value.string().size();
  if (Is(value, Kind::kBytes)) return value.node()->text.size();
  if (Is(value, Kind::kChainMap)) return Iterate(value).size();
  if (Is(value, Kind::kDict)) return value.node()->entries.size();
  if (Is(value, Kind::kList) || Is(value, Kind::kTuple) ||
      Is(value, Kind::kSet))
    return value.node()->sequence.size();
  throw Error("TypeError", "object has no length");
}
Value List(Values values) {
  auto p = std::make_shared<Node>(Kind::kList);
  p->sequence = std::move(values);
  return Value(p);
}
Value Bytes(std::string value) {
  auto p = std::make_shared<Node>(Kind::kBytes);
  p->text = std::move(value);
  return Value(p);
}
Value Tuple(Values values) {
  auto v = List(std::move(values));
  v.node()->kind = Kind::kTuple;
  return v;
}
Value Dict(Pairs values) {
  Value result(std::make_shared<Node>(Kind::kDict));
  result.node()->entries.reserve(values.size());
  if (!values.empty()) result.node()->index.reserve(values.size());
  for (auto& [k, v] : values) Put(result, k, std::move(v));
  return result;
}
Value Set(Values values) {
  Value result(std::make_shared<Node>(Kind::kSet));
  for (const auto& v : values)
    if (!Contains(result, v)) result.node()->sequence.push_back(v);
  return result;
}

}  // namespace kagg::opponents::compiled
