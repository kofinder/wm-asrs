#pragma once
#include <regex>
#include <stdexcept>
#include <string>

namespace asrs {
struct Plan {
  std::string target;
  double x_mm;
  double z_mm;
};

// Demonstration coordinates ONLY. Real rack geometry is calibrated equipment data.
inline Plan plan_location(const std::string &target) {
  static const std::regex pattern(R"(^A-([0-9]{2})-([0-9]{2})$)");
  std::smatch m;
  if (!std::regex_match(target, m, pattern)) {
    throw std::invalid_argument("expected rack code A-CC-LL");
  }
  const int column = std::stoi(m[1].str());
  const int level = std::stoi(m[2].str());
  if (column < 1 || column > 20 || level < 1 || level > 12) {
    throw std::invalid_argument("rack location outside simulated bounds");
  }
  return {target, column * 1500.0, level * 1200.0};
}
} // namespace asrs
