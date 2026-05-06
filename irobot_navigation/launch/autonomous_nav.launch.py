from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node


ARGUMENTS = [
    DeclareLaunchArgument('use_sim_time', default_value='true',
                          choices=['true', 'false'],
                          description='Use sim time'),
    DeclareLaunchArgument('namespace', default_value='',
                          description='Robot namespace'),
    DeclareLaunchArgument('rviz', default_value='false',
                          choices=['true', 'false'],
                          description='Start RViz'),
    DeclareLaunchArgument('localization', default_value='false',
                          choices=['true', 'false'],
                          description='Whether to launch localization'),
    DeclareLaunchArgument('slam', default_value='false',
                          choices=['true', 'false'],
                          description='Whether to launch SLAM'),
    DeclareLaunchArgument('nav2', default_value='false',
                          choices=['true', 'false'],
                          description='Whether to launch Nav2'),
]


def generate_launch_description():
    pkg_irobot_navigation = get_package_share_directory('irobot_navigation')

    namespace = LaunchConfiguration('namespace')
    use_sim_time = LaunchConfiguration('use_sim_time')

    # Map file for localization
    map_arg = DeclareLaunchArgument(
        'map',
        default_value=PathJoinSubstitution(
            [pkg_irobot_navigation, 'maps', 'mapa.yaml']),
        description='Full path to map yaml file to load')

    # Localization parameters
    localization_params_arg = DeclareLaunchArgument(
        'localization_params',
        default_value=PathJoinSubstitution(
            [pkg_irobot_navigation, 'config', 'localization.yaml']),
        description='Localization parameters')

    # SLAM parameters
    slam_params_arg = DeclareLaunchArgument(
        'slam_params',
        default_value=PathJoinSubstitution(
            [pkg_irobot_navigation, 'config', 'slam.yaml']),
        description='SLAM parameters')

    # Nav2 parameters
    nav2_params_arg = DeclareLaunchArgument(
        'nav2_params',
        default_value=PathJoinSubstitution(
            [pkg_irobot_navigation, 'config', 'nav2.yaml']),
        description='Nav2 parameters')

    # Launch paths
    localization_launch = PathJoinSubstitution(
        [pkg_irobot_navigation, 'launch', 'localization.launch.py'])
    slam_launch = PathJoinSubstitution(
        [pkg_irobot_navigation, 'launch', 'slam.launch.py'])
    nav2_launch = PathJoinSubstitution(
        [pkg_irobot_navigation, 'launch', 'nav2.launch.py'])

    # Localization
    localization = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([localization_launch]),
        launch_arguments={
            'namespace': namespace,
            'use_sim_time': use_sim_time,
            'map': LaunchConfiguration('map'),
            'params': LaunchConfiguration('localization_params')
        }.items(),
        condition=IfCondition(LaunchConfiguration('localization'))
    )

    # SLAM
    slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([slam_launch]),
        launch_arguments={
            'namespace': namespace,
            'use_sim_time': use_sim_time,
            'params': LaunchConfiguration('slam_params')
        }.items(),
        condition=IfCondition(LaunchConfiguration('slam'))
    )

    # Nav2
    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([nav2_launch]),
        launch_arguments={
            'namespace': namespace,
            'use_sim_time': use_sim_time,
            'params_file': LaunchConfiguration('nav2_params')
        }.items(),
        condition=IfCondition(LaunchConfiguration('nav2'))
    )

    # RViz
    rviz_config = PathJoinSubstitution(
        [pkg_irobot_navigation, 'rviz', 'navigation.rviz'])

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
        condition=IfCondition(LaunchConfiguration('rviz'))
    )

    # Robot status overlay (solo cuando RViz está activo)
    robot_status_overlay = Node(
        package='irobot_navigation',
        executable='robot_status_overlay',
        name='robot_status_overlay',
        output='screen',
        condition=IfCondition(LaunchConfiguration('rviz'))
    )

    # Define LaunchDescription
    ld = LaunchDescription(ARGUMENTS)
    ld.add_action(map_arg)
    ld.add_action(localization_params_arg)
    ld.add_action(slam_params_arg)
    ld.add_action(nav2_params_arg)
    ld.add_action(localization)
    ld.add_action(slam)
    ld.add_action(nav2)
    ld.add_action(rviz)
    ld.add_action(robot_status_overlay)
    return ld
