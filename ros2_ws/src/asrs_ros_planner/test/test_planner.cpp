#include "asrs_ros_planner/planner.hpp"
#include <cassert>
#include <iostream>
int main() {
  const auto plan = asrs::plan_location("A-01-04");
  assert(plan.x_mm == 1500.0);
  assert(plan.z_mm == 4800.0);
  try { asrs::plan_location("A-00-99"); assert(false); }
  catch (const std::invalid_argument&) {}
  std::cout << "Planner tests passed\n";
}
