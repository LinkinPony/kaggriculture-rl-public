// Native values used by the statically compiled public policy control flow.
// This runtime does not link CPython or interpret source/bytecode.
#pragma once

#include <cstdint>
#include <memory>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <variant>
#include <vector>

namespace kagg::opponents::compiled {

struct Node;
struct Function;
struct Scope;
struct Context;
using ScopePtr = std::shared_ptr<Scope>;

struct Error : std::runtime_error {
  std::string type;
  Error(std::string kind, std::string message)
      : std::runtime_error(std::move(message)), type(std::move(kind)) {}
};

// An implementation failure is deliberately outside source-level except blocks.
struct PortError : std::runtime_error {
  using std::runtime_error::runtime_error;
};

class Value {
 public:
  using Storage = std::variant<std::monostate, bool, int64_t, double,
                               std::shared_ptr<Node>>;
  Value() = default;
  Value(bool value) : data_(value) {}
  Value(int value) : data_(static_cast<int64_t>(value)) {}
  Value(int64_t value) : data_(value) {}
  Value(double value) : data_(value) {}
  Value(const char* value);
  Value(const std::string& value);
  explicit Value(std::shared_ptr<Node> value) : data_(std::move(value)) {}
  bool none() const;
  bool boolean() const;
  bool integer() const;
  bool numeric() const;
  int64_t integer_value() const;
  double number() const;
  const std::string& string() const;
  const std::shared_ptr<Node>& node() const {
    static const std::shared_ptr<Node> empty;
    const auto value = std::get_if<std::shared_ptr<Node>>(&data_);
    return value ? *value : empty;
  }
  explicit operator bool() const;
  const Storage& storage() const { return data_; }

 private:
  Storage data_;
};

using Values = std::vector<Value>;
using Pairs = std::vector<std::pair<Value, Value>>;
using Keywords = std::vector<std::pair<std::string, Value>>;

enum class Kind {
  kString,
  kBytes,
  kChainMap,
  kList,
  kTuple,
  kDict,
  kSet,
  kFunction,
  kClass,
  kObject,
  kBuiltin,
  kIterator,
  kSuper
};

struct Node {
  explicit Node(Kind tag) : kind(tag) {}
  Kind kind;
  bool frozen = false;
  std::string text;
  Values sequence;
  Pairs entries;
  std::unordered_map<std::string, size_t> index;
  Value attributes;
  Value base;
  std::shared_ptr<Function> function;
  size_t position = 0;
};

inline bool Is(const Value& value, Kind kind) {
  const auto& p = value.node();
  return p && p->kind == kind;
}
bool Equal(const Value& left, const Value& right);
int Compare(const Value& left, const Value& right);
bool Identical(const Value& left, const Value& right);
std::string Key(const Value& value);
std::string Repr(const Value& value);
int64_t Length(const Value& value);
Value List(Values values = {});
Value Bytes(std::string value);
Value Tuple(Values values = {});
Value Dict(Pairs values = {});
Value Set(Values values = {});
Value Get(const Value& container, const Value& key);
Value GetOr(const Value& container, const Value& key, Value fallback = {});
void Put(const Value& container, const Value& key, Value value);
void Erase(const Value& container, const Value& key);
bool Contains(const Value& container, const Value& key);
Values Iterate(const Value& value);
Value Slice(const Value& value, const Value& start, const Value& stop,
            const Value& step = {});
void PutSlice(const Value& value, const Value& start, const Value& stop,
              const Value& step, const Value& replacement);
Value Unary(const char* operation, const Value& value);
Value Binary(const char* operation, const Value& left, const Value& right);
Value Inplace(const char* operation, const Value& left, const Value& right);
Value ShallowCopy(const Value& value);
Value DeepCopy(const Value& value, bool session = false);
void Freeze(const Value& value);

}  // namespace kagg::opponents::compiled
