"""Demo: telemetria_live.py

Dashboard en terminal con la telemetría del iRobot Create 3 en tiempo real.
Se actualiza a 2 Hz mostrando: posición, velocidad, batería, IMU y estado del dock.

Uso:
    ros2 run irobot_demos telemetria_live
"""

import math
import os

import rclpy
from nav_msgs.msg import Odometry
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import BatteryState, Imu

try:
    from irobot_create_msgs.msg import DockStatus
    DOCK_OK = True
except ImportError:
    DOCK_OK = False


class TelemetriaLive(Node):
    def __init__(self):
        super().__init__('telemetria_live')

        self._pos      = (0.0, 0.0)
        self._yaw      = 0.0
        self._vlin     = 0.0
        self._vang     = 0.0
        self._bat_v    = 0.0
        self._bat_p    = 0.0
        self._roll     = 0.0
        self._pitch    = 0.0
        self._is_docked = None   # None = sin datos

        self.create_subscription(Odometry, '/odom', self._odom_cb,
                                 qos_profile_sensor_data)
        self.create_subscription(BatteryState, '/battery_state',
                                 self._bat_cb, 10)
        self.create_subscription(Imu, '/imu', self._imu_cb, 10)

        if DOCK_OK:
            self.create_subscription(DockStatus, '/dock_status',
                                     self._dock_cb, 10)

        self.timer = self.create_timer(0.5, self._mostrar)  # 2 Hz

    # ── callbacks ──────────────────────────────────────────────────────────

    def _odom_cb(self, msg):
        p = msg.pose.pose.position
        self._pos  = (p.x, p.y)
        self._yaw  = self._quat_to_yaw(msg.pose.pose.orientation)
        t = msg.twist.twist
        self._vlin = t.linear.x
        self._vang = t.angular.z

    def _bat_cb(self, msg):
        self._bat_v = msg.voltage
        self._bat_p = msg.percentage * 100.0 if msg.percentage >= 0 else -1.0

    def _imu_cb(self, msg):
        self._roll, self._pitch, _ = self._quat_to_euler(msg.orientation)

    def _dock_cb(self, msg):
        self._is_docked = msg.is_docked

    # ── display ────────────────────────────────────────────────────────────

    def _mostrar(self):
        os.system('clear')

        bat_str = (f'{self._bat_v:.2f} V  ({self._bat_p:.0f} %)'
                   if self._bat_p >= 0 else f'{self._bat_v:.2f} V')

        if self._is_docked is None:
            dock_str = 'n/d'
        else:
            dock_str = 'cargando ✓' if self._is_docked else 'libre'

        print('╔══════════════════════════════════════════════╗')
        print('║    iRobot Create 3 — Telemetría en vivo      ║')
        print('╠══════════════════════════════════════════════╣')
        print(f'║  Posición    x={self._pos[0]:+.3f} m  y={self._pos[1]:+.3f} m'.ljust(47) + '║')
        print(f'║  Orientación yaw={math.degrees(self._yaw):+.1f}°'.ljust(47) + '║')
        print(f'║  Velocidad   lin={self._vlin:+.3f} m/s  ang={self._vang:+.3f} rad/s'.ljust(47) + '║')
        print('╠══════════════════════════════════════════════╣')
        print(f'║  Batería     {bat_str}'.ljust(47) + '║')
        print(f'║  Dock        {dock_str}'.ljust(47) + '║')
        print('╠══════════════════════════════════════════════╣')
        print(f'║  IMU  roll={math.degrees(self._roll):+.1f}°  pitch={math.degrees(self._pitch):+.1f}°'.ljust(47) + '║')
        print('╚══════════════════════════════════════════════╝')
        print('  Ctrl+C para salir')

    # ── utilidades ─────────────────────────────────────────────────────────

    @staticmethod
    def _quat_to_yaw(q):
        siny = 2.0 * (q.w * q.z + q.x * q.y)
        cosy = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        return math.atan2(siny, cosy)

    @staticmethod
    def _quat_to_euler(q):
        sinr = 2.0 * (q.w * q.x + q.y * q.z)
        cosr = 1.0 - 2.0 * (q.x * q.x + q.y * q.y)
        roll = math.atan2(sinr, cosr)
        sinp = max(-1.0, min(1.0, 2.0 * (q.w * q.y - q.z * q.x)))
        pitch = math.asin(sinp)
        siny = 2.0 * (q.w * q.z + q.x * q.y)
        cosy = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        yaw = math.atan2(siny, cosy)
        return roll, pitch, yaw


def main(args=None):
    rclpy.init(args=args)
    node = TelemetriaLive()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
