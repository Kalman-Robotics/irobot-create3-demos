#!/bin/bash

# Wait for nav2 to be ready
sleep 5

# Send a dummy goal to trigger the waypoint mission
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
  "{pose: {header: {frame_id: 'map'}, pose: {position: {x: 0.0, y: 0.0}}}}" &

echo "Waypoint mission started!"
