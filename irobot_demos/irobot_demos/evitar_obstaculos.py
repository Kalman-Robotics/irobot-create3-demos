"""Demo: evitar_obstaculos.py

Avanza en línea recta. Cuando detecta un obstáculo al frente a menos de
DIST_STOP metros, gira hacia el lado con más espacio libre hasta despejarse
y retoma el avance.

RPLIDAR A1 en el iRobot Create 3 — ~720 muestras, 0.5° por muestra:
  angle_min ≈ -π  →  índice 0 ≈ FRENTE del robot (ángulo wrap-around ±π)
  frente:     índices 0-30 + 690-719  (±15° alrededor del wrap ±π)
  izquierda:  índices 150-210         (±15° centrado en 180 → robot_angle=+π/2)
  derecha:    índices 510-570         (±15° centrado en 540 → robot_angle=-π/2)

Uso:
    ros2 run irobot_demos evitar_obstaculos
"""

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


VEL_LINEAL  = 0.10    # m/s
VEL_ANGULAR = 0.80    # rad/s
DIST_STOP   = 0.55    # m — distancia mínima al frente antes de girar
DIST_MAX    = 10.0    # m — saturación inf


class EvitarObstaculos(Node):
    def __init__(self):
        super().__init__('evitar_obstaculos')

        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.sub = self.create_subscription(
            LaserScan, '/scan', self._scan_cb, 10)

        self._girando = False
        self._dir_giro = 1.0  # +1 izquierda, -1 derecha

        self.get_logger().info(
            f'Evitar obstáculos iniciado — dist_stop={DIST_STOP} m')

    def _scan_cb(self, msg):
        def sector_min(a, b):
            vals = [r for r in msg.ranges[a:b] if 0.15 < r < DIST_MAX]
            return min(vals, default=DIST_MAX)

        def frente_min():
            # FRENTE cruza el wrap-around: cubre ±15° alrededor del índice 0/719
            vals = ([r for r in msg.ranges[0:31]   if 0.15 < r < DIST_MAX] +
                    [r for r in msg.ranges[690:720] if 0.15 < r < DIST_MAX])
            return min(vals, default=DIST_MAX)

        frente    = frente_min()
        izquierda = sector_min(150, 210)   # robot_angle ≈ +π/2
        derecha   = sector_min(510, 570)   # robot_angle ≈ -π/2

        self.get_logger().info(
            f'frente={frente:.2f}  der={derecha:.2f}  izq={izquierda:.2f}')

        cmd = Twist()

        if frente < DIST_STOP:
            if not self._girando:
                self._dir_giro = 1.0 if izquierda >= derecha else -1.0
                lado = 'izquierda' if self._dir_giro > 0 else 'derecha'
                self.get_logger().info(f'Obstáculo — girando a la {lado}')
                self._girando = True
            cmd.angular.z = VEL_ANGULAR * self._dir_giro
        else:
            self._girando = False
            cmd.linear.x  = VEL_LINEAL

        self.pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = EvitarObstaculos()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
