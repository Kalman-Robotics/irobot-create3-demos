#!/usr/bin/env python3
"""
Battery monitor: navega 4 waypoints en loop y registra datos de autonomía.
Reportes guardados en el directorio de ejecución actual.

Uso: ros2 run irobot_navigation battery_monitor
"""

import csv
import json
import math
import os
import signal
import threading
import time
from collections import deque
from datetime import datetime

import rclpy
from geometry_msgs.msg import PoseStamped, Twist
from nav_msgs.msg import Odometry
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import BatteryState

# ── Waypoints (nombre, x, y, qz, qw) ─────────────────────────────────────────
WAYPOINTS = [
    ('A', -0.589111,  -0.461646, -0.437039, 0.899443),
    ('B', -0.0857142, -3.13122,  -0.938253, 0.345949),
    ('C', -2.91348,   -3.25702,   0.896327, 0.443393),
    ('D', -3.11585,   -0.467072,  0.362506, 0.931981),
]

STOP_BATTERY_PCT  = 0.15   # para al llegar al 15%
HEARTBEAT_SEC     = 30.0   # log periódico mínimo
DELTA_BATTERY_PCT = 0.005  # log si batería baja ≥ 0.5%
DELTA_CURRENT_A   = 0.10   # log si corriente cambia ≥ 0.1A


class MonitorNode(Node):

    def __init__(self):
        super().__init__('battery_monitor')
        self._lock = threading.Lock()

        # Estado batería
        self.battery_pct = 1.0
        self.voltage     = 0.0
        self.current     = 0.0
        self.temperature = 0.0

        # Velocidad
        self.vel_linear  = 0.0
        self.vel_angular = 0.0

        # Odometría
        self.odom_x         = 0.0
        self.odom_y         = 0.0
        self._prev_x        = None
        self._prev_y        = None
        self.total_distance = 0.0

        # Tiempos y laps
        self.start_time     = time.time()
        self.battery_start  = None   # se fija en el primer mensaje
        self.laps           = []

        # Smart sampling
        self._last_log_time    = 0.0
        self._last_log_battery = None
        self._last_log_current = 0.0

        # Historial para tasa de descarga (time, pct)
        self._discharge_history = deque(maxlen=30)

        # Archivos de salida en el directorio actual
        ts = datetime.now().strftime('%Y-%m-%d_%H-%M')
        cwd = os.getcwd()
        self.csv_path    = os.path.join(cwd, f'battery_raw_{ts}.csv')
        self.report_path = os.path.join(cwd, f'battery_report_{ts}.json')

        self._csv_file   = open(self.csv_path, 'w', newline='')
        self._csv_writer = csv.writer(self._csv_file)
        self._csv_writer.writerow([
            'timestamp', 'elapsed_s', 'event',
            'lap', 'waypoint',
            'battery_pct', 'voltage_V', 'current_A', 'temperature_C',
            'vel_linear', 'vel_angular',
            'odom_x', 'odom_y', 'distance_total_m',
        ])

        # Suscripciones
        self.create_subscription(BatteryState, '/battery_state', self._battery_cb, qos_profile_sensor_data)
        self.create_subscription(Twist, '/cmd_vel', self._vel_cb, 10)
        self.create_subscription(Odometry, '/odom', self._odom_cb, qos_profile_sensor_data)

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _battery_cb(self, msg: BatteryState):
        with self._lock:
            self.battery_pct  = msg.percentage
            self.voltage      = msg.voltage
            self.current      = msg.current
            self.temperature  = msg.temperature
            if self.battery_start is None:
                self.battery_start = msg.percentage
                self._last_log_battery = msg.percentage
            self._discharge_history.append((time.time(), msg.percentage))

    def _vel_cb(self, msg: Twist):
        with self._lock:
            self.vel_linear  = msg.linear.x
            self.vel_angular = msg.angular.z

    def _odom_cb(self, msg: Odometry):
        with self._lock:
            x = msg.pose.pose.position.x
            y = msg.pose.pose.position.y
            if self._prev_x is not None:
                dx = x - self._prev_x
                dy = y - self._prev_y
                self.total_distance += math.sqrt(dx * dx + dy * dy)
            self._prev_x = x
            self._prev_y = y
            self.odom_x  = x
            self.odom_y  = y

    # ── Logging ───────────────────────────────────────────────────────────────

    def _write_row(self, event: str, lap: int, waypoint: str):
        with self._lock:
            elapsed = time.time() - self.start_time
            self._csv_writer.writerow([
                datetime.now().isoformat(),
                f'{elapsed:.1f}',
                event,
                lap, waypoint,
                f'{self.battery_pct:.4f}',
                f'{self.voltage:.3f}',
                f'{self.current:.3f}',
                f'{self.temperature:.1f}',
                f'{self.vel_linear:.3f}',
                f'{self.vel_angular:.3f}',
                f'{self.odom_x:.3f}',
                f'{self.odom_y:.3f}',
                f'{self.total_distance:.2f}',
            ])
            self._csv_file.flush()
            self._last_log_time    = time.time()
            self._last_log_battery = self.battery_pct
            self._last_log_current = self.current

    def try_log(self, lap: int):
        with self._lock:
            if self._last_log_battery is None:
                return
            d_bat  = abs(self.battery_pct - self._last_log_battery)
            d_cur  = abs(self.current - self._last_log_current)
            d_time = time.time() - self._last_log_time

        if d_bat >= DELTA_BATTERY_PCT:
            self._write_row('battery_drop', lap, '')
        elif d_cur >= DELTA_CURRENT_A:
            self._write_row('current_spike', lap, '')
        elif d_time >= HEARTBEAT_SEC:
            self._write_row('heartbeat', lap, '')

    def log_waypoint(self, wp: str, lap: int):
        self._write_row('waypoint', lap, wp)

    # ── Métricas ──────────────────────────────────────────────────────────────

    def discharge_rate_pct_per_min(self) -> float:
        with self._lock:
            history = list(self._discharge_history)
        if len(history) < 2:
            return 0.0
        t0, p0 = history[0]
        t1, p1 = history[-1]
        elapsed_min = (t1 - t0) / 60.0
        if elapsed_min < 0.1:
            return 0.0
        return (p0 - p1) / elapsed_min

    def estimated_remaining_min(self) -> float:
        rate = self.discharge_rate_pct_per_min()
        if rate <= 0:
            return float('inf')
        return (self.battery_pct - STOP_BATTERY_PCT) / rate

    # ── Reporte final ─────────────────────────────────────────────────────────

    def save_report(self) -> dict:
        self._csv_file.close()

        with self._lock:
            elapsed_s   = time.time() - self.start_time
            bat_end     = self.battery_pct
            bat_start   = self.battery_start if self.battery_start else bat_end
            total_dist  = self.total_distance

        consumed = bat_start - bat_end
        rate     = self.discharge_rate_pct_per_min()

        report = {
            'run_date':                   datetime.now().isoformat(),
            'battery_start_pct':          round(bat_start * 100, 1),
            'battery_end_pct':            round(bat_end * 100, 1),
            'battery_consumed_pct':       round(consumed * 100, 1),
            'total_laps':                 len(self.laps),
            'total_distance_m':           round(total_dist, 2),
            'total_time_s':               round(elapsed_s, 1),
            'total_time_hms':             time.strftime('%H:%M:%S', time.gmtime(elapsed_s)),
            'discharge_rate_pct_per_min': round(rate * 100, 3),
            'estimated_full_run_time_min': round(bat_start / rate, 1) if rate > 0 else None,
            'meters_per_pct':             round(total_dist / (consumed * 100), 2) if consumed > 0.001 else None,
            'time_per_pct_s':             round(elapsed_s / (consumed * 100), 1) if consumed > 0.001 else None,
            'laps':                       self.laps,
            'raw_csv':                    self.csv_path,
        }

        def _sanitize(obj):
            if isinstance(obj, float) and (math.isinf(obj) or math.isnan(obj)):
                return None
            if isinstance(obj, dict):
                return {k: _sanitize(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_sanitize(v) for v in obj]
            return obj

        with open(self.report_path, 'w') as f:
            json.dump(_sanitize(report), f, indent=2, ensure_ascii=False)

        return report


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_pose(x: float, y: float, qz: float, qw: float) -> PoseStamped:
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.pose.position.x = x
    pose.pose.position.y = y
    pose.pose.orientation.z = qz
    pose.pose.orientation.w = qw
    return pose


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    rclpy.init()
    monitor   = MonitorNode()
    navigator = BasicNavigator()

    executor = MultiThreadedExecutor()
    executor.add_node(monitor)
    spin_thread = threading.Thread(target=executor.spin, daemon=True)
    spin_thread.start()

    interrupted = threading.Event()

    def handle_signal(sig, frame):
        print('\n[battery_monitor] Interrupción — guardando reporte...')
        interrupted.set()

    signal.signal(signal.SIGINT, handle_signal)

    navigator.waitUntilNav2Active()

    print('[battery_monitor] Nav2 listo. Iniciando monitoreo de batería.')
    print(f'[battery_monitor] CSV     → {monitor.csv_path}')
    print(f'[battery_monitor] Reporte → {monitor.report_path}')
    print(f'[battery_monitor] Para con batería ≤ {STOP_BATTERY_PCT*100:.0f}%\n')

    lap = 0
    try:
        while not interrupted.is_set() and monitor.battery_pct > STOP_BATTERY_PCT:
            lap += 1
            lap_start_time     = time.time()
            lap_start_pct      = monitor.battery_pct
            lap_start_distance = monitor.total_distance

            print(f'[battery_monitor] ── Lap {lap} | '
                  f'Batería: {lap_start_pct*100:.1f}% | '
                  f'Estimado restante: {monitor.estimated_remaining_min():.0f} min ──')

            wp_data = {}
            for wp_name, x, y, qz, qw in WAYPOINTS:
                if interrupted.is_set() or monitor.battery_pct <= STOP_BATTERY_PCT:
                    break

                print(f'[battery_monitor]   → {wp_name} ({x:.2f}, {y:.2f})')
                navigator.goToPose(make_pose(x, y, qz, qw))

                while not navigator.isTaskComplete():
                    if interrupted.is_set():
                        navigator.cancelTask()
                        break
                    monitor.try_log(lap)
                    time.sleep(1.0)

                result = navigator.getResult()
                monitor.log_waypoint(wp_name, lap)

                wp_data[wp_name] = {
                    'arrival_time_s': round(time.time() - monitor.start_time, 1),
                    'battery_pct':    round(monitor.battery_pct * 100, 1),
                    'result':         'ok' if result == TaskResult.SUCCEEDED else 'failed',
                }

            lap_time_s   = time.time() - lap_start_time
            lap_consumed = (lap_start_pct - monitor.battery_pct) * 100
            lap_distance = monitor.total_distance - lap_start_distance

            monitor.laps.append({
                'lap':                  lap,
                'time_s':               round(lap_time_s, 1),
                'battery_start_pct':    round(lap_start_pct * 100, 1),
                'battery_end_pct':      round(monitor.battery_pct * 100, 1),
                'battery_consumed_pct': round(lap_consumed, 1),
                'distance_m':           round(lap_distance, 2),
                'est_remaining_min':    round(monitor.estimated_remaining_min(), 1),
                'waypoints':            wp_data,
            })

            print(f'[battery_monitor]   Lap {lap} OK — '
                  f'{lap_time_s:.0f}s | {lap_distance:.1f}m | -{lap_consumed:.1f}%')

    finally:
        report = monitor.save_report()

        sep = '=' * 60
        print(f'\n{sep}')
        print('  REPORTE DE AUTONOMÍA')
        print(sep)
        print(f"  Fecha             : {report['run_date'][:19]}")
        print(f"  Laps completados  : {report['total_laps']}")
        print(f"  Distancia total   : {report['total_distance_m']} m")
        print(f"  Tiempo total      : {report['total_time_hms']}")
        print(f"  Batería inicio    : {report['battery_start_pct']}%")
        print(f"  Batería fin       : {report['battery_end_pct']}%")
        print(f"  Batería consumida : {report['battery_consumed_pct']}%")
        print(f"  Tasa descarga     : {report['discharge_rate_pct_per_min']} %/min")
        if report['estimated_full_run_time_min']:
            print(f"  Autonomía estimada: {report['estimated_full_run_time_min']} min")
        if report['meters_per_pct']:
            print(f"  Metros por 1%     : {report['meters_per_pct']} m/%")
        if report['time_per_pct_s']:
            print(f"  Tiempo por 1%     : {report['time_per_pct_s']} s/%")
        print(sep)
        print(f"  Reporte JSON → {report['report_path'] if 'report_path' in report else monitor.report_path}")
        print(f"  Datos crudos → {report['raw_csv']}")
        print(sep + '\n')

        executor.shutdown()
        navigator.destroy_node()
        monitor.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
