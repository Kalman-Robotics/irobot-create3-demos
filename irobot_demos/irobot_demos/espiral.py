"""Demo: espiral.py

Traza una espiral hacia adentro y termina detenido.

Estrategia:
  - La velocidad lineal (v) va disminuyendo gradualmente de v_max a 0.
  - La velocidad angular (ω) va aumentando gradualmente de 0 a ω_max.
  - Al inicio: v alto + ω bajo  → trayectoria casi recta (arcos amplios)
  - Al final:  v bajo + ω alto  → círculos cerrados (espiral hacia adentro)
  - Cuando v llega a 0, el robot se detiene.

Uso:
    ros2 run irobot_demos espiral
    ros2 run irobot_demos espiral --ros-args -p duracion:=90.0
"""

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node


VEL_LIN_MAX = 0.10    # m/s
VEL_ANG_MAX = 0.50    # rad/s
FREQ_HZ     = 20


class Espiral(Node):
    def __init__(self):
        super().__init__('espiral')

        self.declare_parameter('duracion', 25.0)   # segundos totales
        self._duracion = self.get_parameter('duracion').value

        self._tick  = 0
        self._total = int(self._duracion * FREQ_HZ)

        self.pub   = self.create_publisher(Twist, '/cmd_vel', 10)
        self.timer = self.create_timer(1.0 / FREQ_HZ, self._loop)

        self.get_logger().info(f'Espiral iniciada — duración={self._duracion} s')

    def _loop(self):
        if self._tick >= self._total:
            self.pub.publish(Twist())
            self.timer.cancel()
            self.get_logger().info('¡Espiral completada!')
            raise SystemExit

        t = self._tick / self._total

        v     = VEL_LIN_MAX * (1.0 - t)
        omega = VEL_ANG_MAX * t

        cmd = Twist()
        cmd.linear.x  = v
        cmd.angular.z = omega
        self.pub.publish(cmd)

        self.get_logger().debug(
            f't={t:.2f}  v={v:.3f} m/s  ω={omega:.3f} rad/s')

        self._tick += 1


def main(args=None):
    rclpy.init(args=args)
    node = Espiral()
    try:
        rclpy.spin(node)
    except SystemExit:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
