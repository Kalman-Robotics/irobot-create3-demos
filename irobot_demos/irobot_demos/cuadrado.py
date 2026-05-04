"""Demo: cuadrado.py

Traza un cuadrado de lado configurable usando odometría.

Uso:
    ros2 run irobot_demos cuadrado
    ros2 run irobot_demos cuadrado --ros-args -p lado:=0.5
"""

import math

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data


VEL_LINEAL  = 0.10     # m/s
VEL_ANGULAR = 0.40     # rad/s
TOL_POS     = 0.02     # m  — tolerancia de posición
TOL_ANG     = 0.03     # rad — tolerancia angular


class Estado:
    AVANZAR = 'avanzar'
    GIRAR   = 'girar'
    LISTO   = 'listo'


class Cuadrado(Node):
    def __init__(self):
        super().__init__('cuadrado')

        self.declare_parameter('lado', 0.4)  # metros
        self.lado = self.get_parameter('lado').value

        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.sub = self.create_subscription(
            Odometry, '/odom', self._odom_cb, qos_profile_sensor_data)

        self._x0 = None
        self._y0 = None
        self._yaw0 = None
        self._yaw = None

        self._estado = Estado.AVANZAR
        self._lados_completos = 0
        self._giros_completos = 0

        self.timer = self.create_timer(0.05, self._loop)
        self.get_logger().info(f'Cuadrado iniciado — lado={self.lado} m')

    # ── callbacks ──────────────────────────────────────────────────────────

    def _odom_cb(self, msg):
        pos = msg.pose.pose.position
        q   = msg.pose.pose.orientation
        self._yaw = self._quat_to_yaw(q)

        if self._x0 is None:
            self._x0 = pos.x
            self._y0 = pos.y
            self._yaw0 = self._yaw

        self._x = pos.x
        self._y = pos.y

    # ── bucle principal ────────────────────────────────────────────────────

    def _loop(self):
        if self._x0 is None:
            return

        cmd = Twist()

        if self._estado == Estado.AVANZAR:
            dist = math.hypot(self._x - self._x0, self._y - self._y0)
            if dist < self.lado - TOL_POS:
                cmd.linear.x = VEL_LINEAL
            else:
                self._lados_completos += 1
                self._x0 = self._x
                self._y0 = self._y
                self._yaw0 = self._yaw
                self._estado = Estado.GIRAR
                self.get_logger().info(
                    f'Lado {self._lados_completos} completo — girando')

        elif self._estado == Estado.GIRAR:
            angulo_girado = self._angle_diff(self._yaw, self._yaw0)
            if abs(angulo_girado) < math.pi / 2 - TOL_ANG:
                cmd.angular.z = VEL_ANGULAR
            else:
                self._giros_completos += 1
                self._x0 = self._x
                self._y0 = self._y
                self._yaw0 = self._yaw

                if self._lados_completos < 4:
                    self._estado = Estado.AVANZAR
                    self.get_logger().info(
                        f'Giro {self._giros_completos} completo — avanzando')
                else:
                    self._estado = Estado.LISTO
                    self.get_logger().info('¡Cuadrado completado!')

        elif self._estado == Estado.LISTO:
            self.timer.cancel()
            raise SystemExit

        self.pub.publish(cmd)

    # ── utilidades ─────────────────────────────────────────────────────────

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
    node = Cuadrado()
    try:
        rclpy.spin(node)
    except SystemExit:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
