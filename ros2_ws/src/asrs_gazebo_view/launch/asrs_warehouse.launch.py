"""Launch Gazebo Harmonic world + ROS/Gazebo transport bridge + WCS visual sync."""
import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    share = get_package_share_directory('asrs_gazebo_view')
    world = os.path.join(share, 'worlds', 'asrs_warehouse.sdf')
    topics = [
        '/asrs/crane/x_cmd@std_msgs/msg/Float64]gz.msgs.Double',
        '/asrs/crane/z_cmd@std_msgs/msg/Float64]gz.msgs.Double',
        '/asrs/crane/fork_cmd@std_msgs/msg/Float64]gz.msgs.Double',
    ]
    return LaunchDescription([
        ExecuteProcess(cmd=['gz', 'sim', '-r', '-v', '3', world], output='screen'),
        Node(package='ros_gz_bridge', executable='parameter_bridge',
             arguments=topics, output='screen'),
        Node(package='asrs_gazebo_view', executable='wcs_visual_sync', output='screen'),
        Node(package='asrs_gazebo_view', executable='pallet_visual_sync', output='screen'),
    ])
