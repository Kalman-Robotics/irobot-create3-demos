"""Demo: control_p.py

Controlador proporcional de orientación.
El robot gira hasta alcanzar un ángulo objetivo (en grados) y se detiene.

Uso:
    ros2 run irobot_demos control_p
    ros2 run irobot_demos control_p --ros-args -p angulo_objetivo:=90.0
    ros2 run irobot_demos control_p --ros-args -p angulo_objetivo:=-45.0
"""

import math

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data


KP      = 1.2     # ganancia proporcional
VEL_MAX = 0.40    # rad/s — límite de salida del controlador
TOL_ANG = 0.03    # rad  — tolerancia para considerar que llegó


class ControlP(Node):
    def __init__(self):
        super().__init__('control_p')

        self.declare_parameter('angulo_objetivo', 90.0)  # grados
        objetivo_deg = self.get_parameter('angulo_objetivo').value
        self._objetivo = math.radians(objetivo_deg)

        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.sub = self.create_subscription(
            Odometry, '/odom', self._odom_cb, qos_profile_sensor_data)

        self._yaw_inicial = None
        self._listo = False

        self.get_logger().info(
            f'Control P de orientación — objetivo={objetivo_deg:.1f}°  Kp={KP}')

    def _odom_cb(self, msg):
        if self._listo:
            return

        q   = msg.pose.pose.orientation
        yaw = self._quat_to_yaw(q)

        if self._yaw_inicial is None:
            self._yaw_inicial = yaw
            self.get_logger().info(f'Yaw inicial: {math.degrees(yaw):.1f}°')

        error = self._angle_diff(self._objetivo, yaw - self._yaw_inicial)

        cmd = Twist()
        if abs(error) > TOL_ANG:
            cmd.angular.z = max(-VEL_MAX, min(VEL_MAX, KP * error))
            self.get_logger().info(
                f'error={math.degrees(error):.1f}°  '
                f'omega={cmd.angular.z:.3f} rad/s')
        else:
            self._listo = True
            self.get_logger().info(
                f'¡Objetivo alcanzado! error final={math.degrees(error):.2f}°')
            self.pub.publish(cmd)
            raise SystemExit

        self.pub.publish(cmd)

    @staticmethod
    def _quat_to_yaw(q):
        siny = 2.0 * (q.w * q.z + q.x * q.y)
        cosy = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        return math.atan2(siny, cosy)

    @staticmethod
    def _angle_diff(a, b):
        d = a - b
        while d >  math.pi: d -= 2 * math.pi
        while d < -math.pi: d += 2 * math.pi
        return d


def main(args=None):
    rclpy.init(args=args)
    node = ControlP()
    try:
        rclpy.spin(node)
    except SystemExit:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
