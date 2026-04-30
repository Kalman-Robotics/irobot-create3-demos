"""Demo: explorador.py  (patrullaje autónomo)

Algoritmo de patrullaje continuo basado en el rayo más libre:
  1. Escanea el semicírculo frontal y localiza el rayo más lejano.
  2. Orienta el robot suavemente hacia ese rayo (siempre hay movimiento).
  3. Si el lateral izquierdo o derecho entra en la burbuja de seguridad,
     corrige la angular_z incrementalmente para alejarse.

No hay estados discretos — la velocidad angular se actualiza cada ciclo
de forma fluida, lo que produce trayectorias más naturales que un
alternado avanzar/girar.

RPLIDAR A1 en el iRobot Create 3 — ~720 muestras, 0.5° por muestra:
  angle_min ≈ -π  →  índice 0 ≈ FRENTE del robot (ángulo wrap-around ±π)
  Transformación:  robot_angle = index * angle_increment  (normalizado a ±π)
  frente (wrap):   índices 0-180 y 540-719  (semicírculo ±90°)
  izquierda:       índices 150-210          (robot_angle ≈ +π/2)
  derecha:         índices 510-570          (robot_angle ≈ -π/2)

Uso:
    ros2 run irobot_demos explorador
    ros2 run irobot_demos explorador --ros-args -p burbuja:=0.28
"""

import math

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


# ── Parámetros del robot ────────────────────────────────────────────────────
VEL_LINEAL   = 0.16          # m/s
VEL_ANG_MAX  = 1.0           # rad/s — saturación de angular_z
GAIN_DIR     = 1.0            # ganancia proporcional sobre la dirección más libre
VARIACION    = 1.2            # rad/s — paso de corrección lateral por ciclo

# Zonas de análisis (índices sobre ~720 muestras, angle_min≈-π, 0.5°/muestra)
# robot_angle = index * angle_increment  (se normaliza a ±π)
# FRENTE wrap-around: indices 0-180 (frente→izquierda) y 540-719 (derecha→frente)
FRONT_LMIN   = 0     # inicio mitad izquierda del semicírculo frontal
FRONT_LMAX   = 181   # fin   mitad izquierda (hasta 90°)
FRONT_RMIN   = 539   # inicio mitad derecha  (desde -90°)
FRONT_RMAX   = 720   # fin   mitad derecha
LEFT_MIN     = 150   # inicio zona lateral izquierda (robot_angle ≈ +π/2)
LEFT_MAX     = 210   # fin   zona lateral izquierda
RIGHT_MIN    = 510   # inicio zona lateral derecha   (robot_angle ≈ -π/2)
RIGHT_MAX    = 570   # fin   zona lateral derecha

MAX_RANGE    = 3.5    # m — distancia máxima válida (ignora inf)
ANCHO_VENTANA = 120   # rayos — ancho mínimo de paso (~20° a 0.5°/rayo, ≈ ancho del robot a 1m)


class Explorador(Node):
    def __init__(self):
        super().__init__('explorador')

        self.declare_parameter('burbuja', 0.45)   # m — radio de seguridad lateral
        self._burbuja = self.get_parameter('burbuja').value

        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.sub = self.create_subscription(
            LaserScan, '/scan', self._scan_cb, 10)

        self._scan = None
        self._angular_z = 0.05
        self._angle_inc = math.pi / 360   # rad/muestra (se actualiza con el primer scan)

        self.timer = self.create_timer(0.1, self._control_cb)

        self.get_logger().info(
            f'Explorador iniciado — burbuja={self._burbuja} m')

    # ── callbacks ──────────────────────────────────────────────────────────

    def _scan_cb(self, msg):
        self._scan = msg
        self._angle_inc = msg.angle_increment

    def _control_cb(self):
        if self._scan is None:
            return

        self._actualizar_direccion()
        self._verificar_laterales()
        self._saturar_angular()

        cmd = Twist()
        cmd.linear.x  = VEL_LINEAL
        cmd.angular.z = self._angular_z
        self.pub.publish(cmd)

    # ── lógica de navegación ───────────────────────────────────────────────

    def _actualizar_direccion(self):
        """Busca la ventana de ANCHO_VENTANA rayos consecutivos cuyo mínimo
        es el mayor (= paso más ancho y despejado que cabe el robot).

        robot_angle = index * angle_increment, normalizado a (-π, π]:
          index=0   → 0 rad → FRENTE
          index=180 → +π/2  → IZQUIERDA
          index=540 → -π/2  → DERECHA  (3π/2 normalizado a -π/2)
        """
        ranges = self._scan.ranges
        n = len(ranges)
        indices_frontales = list(range(FRONT_LMIN, FRONT_LMAX)) + list(range(FRONT_RMIN, FRONT_RMAX))

        mejor_score = -1.0
        mejor_centro = 0

        for k in range(len(indices_frontales) - ANCHO_VENTANA + 1):
            ventana = indices_frontales[k:k + ANCHO_VENTANA]
            vals = [ranges[i] for i in ventana if 0.15 < ranges[i] < MAX_RANGE]
            if not vals:
                continue
            score = min(vals)   # el paso más estrecho dentro de la ventana
            if score > mejor_score:
                mejor_score = score
                mejor_centro = indices_frontales[k + ANCHO_VENTANA // 2]

        direction = mejor_centro * self._angle_inc
        if direction > math.pi:
            direction -= 2 * math.pi

        self._angular_z = direction * GAIN_DIR

        self.get_logger().info(
            f'ventana_centro={math.degrees(direction):.1f}°  '
            f'paso_min={mejor_score:.2f} m  omega={self._angular_z:.3f} rad/s')

    def _verificar_laterales(self):
        """Si algún lateral entra en la burbuja de seguridad,
        corrige angular_z incrementalmente para alejarse."""
        ranges = self._scan.ranges

        espacio_izq = self._sector_min(ranges, LEFT_MIN,  LEFT_MAX)
        espacio_der = self._sector_min(ranges, RIGHT_MIN, RIGHT_MAX)

        if espacio_izq < self._burbuja:
            self._angular_z -= VARIACION
            self.get_logger().info(
                f'Burbuja izquierda ({espacio_izq:.2f} m) — corrigiendo a la derecha')

        if espacio_der < self._burbuja:
            self._angular_z += VARIACION
            self.get_logger().info(
                f'Burbuja derecha ({espacio_der:.2f} m) — corrigiendo a la izquierda')

    def _saturar_angular(self):
        if self._angular_z >  VEL_ANG_MAX:
            self._angular_z =  VEL_ANG_MAX
        elif self._angular_z < -VEL_ANG_MAX:
            self._angular_z = -VEL_ANG_MAX

    # ── utilidades ─────────────────────────────────────────────────────────

    @staticmethod
    def _sector_min(ranges, a, b):
        vals = [r for r in ranges[a:b] if 0.15 < r < MAX_RANGE]
        return min(vals) if vals else MAX_RANGE


def main(args=None):
    rclpy.init(args=args)
    node = Explorador()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
