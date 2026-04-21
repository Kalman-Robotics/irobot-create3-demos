"""Demo: radar.py

Visualización del LiDAR en terminal estilo radar, actualizándose a ~2 Hz.
Dibuja un mapa ASCII de 61×31 caracteres centrado en el robot.

  '>' = robot (centro, apuntando hacia abajo = frente)
  'X' = obstáculo detectado
  ' ' = espacio libre o sin lectura

Mapeo de pantalla (convención ROS base_link):
  abajo   = frente del robot (+x)
  derecha  = derecha del robot (-y)
  izquierda = izquierda del robot (+y)

Uso:
    ros2 run irobot_demos radar
    ros2 run irobot_demos radar --ros-args -p escala:=0.05 -p radio:=2.0
"""

import math
import os

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


COLS    = 61   # debe ser impar
FILAS   = 31   # debe ser impar
REFRESCO = 0.5  # segundos entre renders


class Radar(Node):
    def __init__(self):
        super().__init__('radar')

        self.declare_parameter('escala', 0.05)   # m/celda
        self.declare_parameter('radio',  2.0)    # m — rango máximo a mostrar

        self._escala = self.get_parameter('escala').value
        self._radio  = self.get_parameter('radio').value

        self._puntos: list[tuple[int, int]] = []

        self.sub = self.create_subscription(
            LaserScan, '/scan', self._scan_cb, 10)
        self.timer = self.create_timer(REFRESCO, self._render)

        self.get_logger().info(
            f'Radar iniciado — escala={self._escala} m/cel  '
            f'radio={self._radio} m')

    # ── callbacks ──────────────────────────────────────────────────────────

    def _scan_cb(self, msg):
        puntos = []
        cx = COLS // 2
        cy = FILAS // 2

        for i, r in enumerate(msg.ranges):
            if not (msg.range_min < r < min(msg.range_max, self._radio)):
                continue
            angulo = msg.angle_min + i * msg.angle_increment

            # Coordenadas en base_link: x=adelante, y=izquierda
            x_r =  r * math.cos(angulo)
            y_r =  r * math.sin(angulo)

            # Mapeo a pantalla: frente=abajo, derecha=columna+
            col = cx - int(round(y_r / self._escala))   # +y (izq) → col-
            fil = cy - int(round(x_r / self._escala))   # +x (adelante) → fil-

            if 0 <= col < COLS and 0 <= fil < FILAS:
                puntos.append((fil, col))

        self._puntos = puntos

    # ── render ─────────────────────────────────────────────────────────────

    def _render(self):
        cx = COLS // 2
        cy = FILAS // 2

        grid = [[' '] * COLS for _ in range(FILAS)]
        for (f, c) in self._puntos:
            grid[f][c] = 'X'
        grid[cy][cx] = '↓'   # ↓ apunta hacia abajo = frente del robot

        borde_h = '─' * COLS
        lineas = [f'┌{borde_h}┐']
        for fila in grid:
            lineas.append('│' + ''.join(fila) + '│')
        lineas.append(f'└{borde_h}┘')

        alcance_m = self._radio
        escala_m  = self._escala * COLS / 2

        os.system('clear')
        print('  iRobot Create 3 — Radar LiDAR  '
              f'(escala={self._escala} m/cel  radio={alcance_m} m)')
        print('\n'.join(lineas))
        print(f'  [↓] robot (frente=abajo)   [X] obstáculo   '
              f'ancho={escala_m:.1f} m a cada lado')
        print('  Ctrl+C para salir')


def main(args=None):
    rclpy.init(args=args)
    node = Radar()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
