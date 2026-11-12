#include "asrs_ros_planner/planner.hpp"
#include <rclcpp/rclcpp.hpp>
#include <std_msgs/msg/string.hpp>

#include <arpa/inet.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>

#include <atomic>
#include <cerrno>
#include <cstring>
#include <iostream>
#include <regex>
#include <sstream>
#include <string>
#include <thread>

namespace {
std::string json_escape(const std::string &s) {
  std::string result;
  for (const char c : s) {
    if (c == '"' || c == '\\') result += '\\';
    if (c == '\n' || c == '\r') continue;
    result += c;
  }
  return result;
}
void reply(int fd, int status, const std::string &body) {
  const char *reason = status == 200 ? "OK" : status == 400 ? "Bad Request" : "Not Found";
  const std::string header = "HTTP/1.1 " + std::to_string(status) + " " + reason +
      "\r\nContent-Type: application/json\r\nContent-Length: " +
      std::to_string(body.size()) + "\r\nConnection: close\r\n\r\n";
  const std::string response = header + body;
  size_t written = 0;
  while (written < response.size()) {
    const auto n = ::send(fd, response.data() + written, response.size() - written, MSG_NOSIGNAL);
    if (n <= 0) break;
    written += static_cast<size_t>(n);
  }
}
} // namespace

class PlannerNode : public rclcpp::Node {
public:
  PlannerNode() : Node("asrs_ros_planner") {
    publisher_ = create_publisher<std_msgs::msg::String>("/asrs/plans", 10);
    server_thread_ = std::thread([this] { serve(); });
  }
  ~PlannerNode() override {
    running_ = false;
    if (server_fd_ >= 0) { ::shutdown(server_fd_, SHUT_RDWR); ::close(server_fd_); }
    if (server_thread_.joinable()) server_thread_.join();
  }
private:
  void serve() {
    const int fd = ::socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) { RCLCPP_ERROR(get_logger(), "socket failed"); return; }
    server_fd_ = fd;
    int reuse = 1;
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &reuse, sizeof(reuse));
    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_port = htons(8091);
    inet_pton(AF_INET, "127.0.0.1", &addr.sin_addr);
    if (::bind(fd, reinterpret_cast<sockaddr*>(&addr), sizeof(addr)) < 0 || ::listen(fd, 8) < 0) {
      RCLCPP_ERROR(get_logger(), "Cannot listen on 127.0.0.1:8091: %s", strerror(errno));
      ::close(fd); server_fd_ = -1; return;
    }
    RCLCPP_INFO(get_logger(), "ROS planner HTTP adapter: http://127.0.0.1:8091");
    while (running_) {
      const int client = ::accept(fd, nullptr, nullptr);
      if (client < 0) break;
      timeval timeout{}; timeout.tv_sec = 2;
      setsockopt(client, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));
      handle(client);
      ::close(client);
    }
  }
  void handle(int fd) {
    std::string request;
    char buffer[2048];
    size_t expected_total = 0;
    for (;;) {
      const auto n = ::recv(fd, buffer, sizeof(buffer), 0);
      if (n <= 0) break;
      request.append(buffer, static_cast<size_t>(n));
      if (request.size() > 8192) { reply(fd, 400, R"({"error":"request too large"})"); return; }
      const size_t split = request.find("\r\n\r\n");
      if (split != std::string::npos) {
        if (expected_total == 0) {
          std::smatch length_match;
          const std::regex pattern(R"(Content-Length:\s*([0-9]+))", std::regex::icase);
          if (std::regex_search(request, length_match, pattern)) {
            expected_total = split + 4 + static_cast<size_t>(std::stoul(length_match[1].str()));
          } else expected_total = split + 4;
        }
        if (request.size() >= expected_total) break;
      }
    }
    if (request.rfind("GET /health ", 0) == 0) {
      reply(fd, 200, R"({"status":"UP","service":"asrs_ros_planner"})");
      return;
    }
    if (request.rfind("POST /plan ", 0) != 0) {
      reply(fd, 404, R"({"error":"endpoint not found"})"); return;
    }
    const auto split = request.find("\r\n\r\n");
    if (split == std::string::npos) { reply(fd, 400, R"({"error":"missing body"})"); return; }
    const auto body = request.substr(split + 4);
    std::smatch match;
    if (!std::regex_search(body, match, std::regex(R"re("target"\s*:\s*"([A-Za-z0-9_-]+)")re"))) {
      reply(fd, 400, R"({"error":"expected JSON target"})"); return;
    }
    const auto target = match[1].str();
    try {
      const auto p = asrs::plan_location(target);
      std_msgs::msg::String event;
      event.data = "PLAN " + p.target + " xMm=" + std::to_string(p.x_mm) +
                   " zMm=" + std::to_string(p.z_mm);
      publisher_->publish(event);
      std::ostringstream out;
      out << "{\"target\":\"" << json_escape(p.target) << "\",\"xMm\":" << p.x_mm
          << ",\"zMm\":" << p.z_mm << ",\"valid\":true,\"message\":\"simulation plan only\"}";
      reply(fd, 200, out.str());
    } catch (const std::invalid_argument &e) {
      reply(fd, 400, "{\"target\":\"" + json_escape(target) +
                    "\",\"valid\":false,\"message\":\"" + json_escape(e.what()) + "\"}");
    }
  }
  std::atomic<bool> running_{true};
  int server_fd_{-1};
  std::thread server_thread_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr publisher_;
};

int main(int argc, char **argv) {
  rclcpp::init(argc, argv);
  auto node = std::make_shared<PlannerNode>();
  rclcpp::spin(node);
  node.reset();
  rclcpp::shutdown();
  return 0;
}
