from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


ARGUMENTS = [
    DeclareLaunchArgument('use_sim_time', default_value='false',
                          choices=['true', 'false'],
                          description='Use sim time'),
    DeclareLaunchArgument('namespace', default_value='',
                          description='Robot namespace'),
]


def generate_launch_description():
    pkg_irobot_navigation = get_package_share_directory('irobot_navigation')

    use_sim_time = LaunchConfiguration('use_sim_time')

    rviz_config = PathJoinSubstitution(
        [pkg_irobot_navigation, 'rviz', 'monitor.rviz'])

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': use_sim_time}],
        remappings=[
            ('/tf', 'tf'),
            ('/tf_static', 'tf_static'),
        ],
        output='screen'
    )

    robot_status_overlay = Node(
        package='irobot_navigation',
        executable='robot_status_overlay',
        name='robot_status_overlay',
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen'
    )

    ld = LaunchDescription(ARGUMENTS)
    ld.add_action(rviz)
    ld.add_action(robot_status_overlay)
    return ld
