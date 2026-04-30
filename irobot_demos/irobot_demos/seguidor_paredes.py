"""Demo: seguidor_paredes.py

Sigue la pared izquierda manteniéndose a distancia_objetivo.

RPLIDAR A1 en el iRobot Create 3 — ~720 muestras, 0.5° por muestra:
  angle_min ≈ -π  →  índice 0 ≈ FRENTE del robot (ángulo wrap-around ±π)
  frente:     índices 0-30 + 690-719  (±15° alrededor del wrap ±π)
  izquierda:  índices 150-210         (±15° centrado en 180 → robot_angle=+π/2)

Uso:
    ros2 run irobot_demos seguidor_paredes
"""

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


VEL_LINEAL  = 0.16   # m/s
GANANCIA    = 2.0    # ganancia proporcional
DIST_OBJ    = 0.75   # m — distancia deseada a la pared
DIST_MAX    = 10.0   # m — valor de saturación para lecturas inf


class SeguidorParedes(Node):
    def __init__(self):
        super().__init__('seguidor_paredes')

        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.sub = self.create_subscription(
            LaserScan, '/scan', self._scan_cb, 10)

        self.get_logger().info(
            f'Seguidor de paredes iniciado — dist_objetivo={DIST_OBJ} m')

    def _scan_cb(self, msg):
        def sector_min(a, b):
            vals = [r for r in msg.ranges[a:b] if 0.15 < r < DIST_MAX]
            return min(vals, default=DIST_MAX)

        def frente_min():
            vals = ([r for r in msg.ranges[0:31]   if 0.15 < r < DIST_MAX] +
                    [r for r in msg.ranges[690:720] if 0.15 < r < DIST_MAX])
            return min(vals, default=DIST_MAX)

        frontal   = frente_min()
        izquierda = sector_min(150, 210)   # robot_angle ≈ +π/2

        self.get_logger().info(
            f'frontal={frontal:.2f} m  izquierda={izquierda:.2f} m')

        cmd = Twist()

        if frontal < DIST_OBJ:
            cmd.linear.x  = 0.0
            cmd.angular.z = -GANANCIA * 0.75
            self.get_logger().info('Obstáculo al frente — girando a la derecha')
        elif izquierda > 3.0 * DIST_OBJ:
            cmd.linear.x  = VEL_LINEAL
            cmd.angular.z = 0.0
            self.get_logger().info('Sin pared — avanzando recto')
        else:
            error = izquierda - DIST_OBJ
            cmd.linear.x  = VEL_LINEAL
            cmd.angular.z = -GANANCIA * error
            self.get_logger().info(f'Siguiendo pared — error={error:.2f} m')

        self.pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = SeguidorParedes()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
