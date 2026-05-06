#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from sensor_msgs.msg import BatteryState
from irobot_create_msgs.msg import DockStatus
from action_msgs.msg import GoalStatus, GoalStatusArray
from nav2_msgs.action import NavigateToPose
from rviz_2d_overlay_msgs.msg import OverlayText


NAV_STATUS_MAP = {
    GoalStatus.STATUS_UNKNOWN:   'DESCONOCIDO',
    GoalStatus.STATUS_ACCEPTED:  'ACEPTADO',
    GoalStatus.STATUS_EXECUTING: 'NAVEGANDO',
    GoalStatus.STATUS_CANCELING: 'CANCELANDO',
    GoalStatus.STATUS_SUCCEEDED: 'COMPLETADO',
    GoalStatus.STATUS_CANCELED:  'CANCELADO',
    GoalStatus.STATUS_ABORTED:   'FALLIDO',
}


class RobotStatusOverlay(Node):
    def __init__(self):
        super().__init__('robot_status_overlay')

        self._battery_pct = None
        self._charging = False
        self._is_docked = None
        self._nav_goal_status = None  # solo cuando hay goal activo

        self.create_subscription(BatteryState, '/battery_state', self._battery_cb, 10)
        self.create_subscription(DockStatus, '/dock_status', self._dock_cb, 10)
        self.create_subscription(
            GoalStatusArray, '/navigate_to_pose/_action/status', self._nav_cb, 10)

        # ActionClient para detectar si Nav2 está levantado
        self._nav_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')

        self._pub = self.create_publisher(OverlayText, '/robot_status_overlay', 10)
        self.create_timer(1.0, self._publish)

    def _battery_cb(self, msg: BatteryState):
        self._battery_pct = msg.percentage * 100.0
        self._charging = (msg.power_supply_status == BatteryState.POWER_SUPPLY_STATUS_CHARGING)

    def _dock_cb(self, msg: DockStatus):
        self._is_docked = msg.is_docked

    def _nav_cb(self, msg: GoalStatusArray):
        # Filtrar solo goals activos (ACCEPTED o EXECUTING)
        active = [s for s in msg.status_list
                  if s.status in (GoalStatus.STATUS_ACCEPTED, GoalStatus.STATUS_EXECUTING)]
        if active:
            self._nav_goal_status = NAV_STATUS_MAP.get(active[-1].status, 'DESCONOCIDO')
        else:
            self._nav_goal_status = None

    def _bar(self, pct: float) -> str:
        filled = max(0, min(10, int(pct / 10)))
        return '[' + '█' * filled + '░' * (10 - filled) + ']'

    def _nav2_line(self) -> str:
        nav2_up = self._nav_client.server_is_ready()
        if not nav2_up:
            return 'Nav2:    NO ACTIVO'
        if self._nav_goal_status:
            return f'Nav2:    {self._nav_goal_status}'
        return 'Nav2:    LISTO'

    def _publish(self):
        msg = OverlayText()
        msg.action = OverlayText.ADD
        msg.width = 320
        msg.height = 130
        msg.horizontal_alignment = OverlayText.LEFT
        msg.vertical_alignment = OverlayText.TOP
        msg.horizontal_distance = 10
        msg.vertical_distance = 10
        msg.text_size = 10.0
        msg.line_width = 1
        msg.font = 'DejaVu Sans Mono'
        msg.bg_color.r = 0.0
        msg.bg_color.g = 0.0
        msg.bg_color.b = 0.0
        msg.bg_color.a = 0.65
        msg.fg_color.r = 1.0
        msg.fg_color.g = 1.0
        msg.fg_color.b = 1.0
        msg.fg_color.a = 1.0

        if self._battery_pct is not None:
            pct = self._battery_pct
            suffix = ' CARGANDO' if self._charging else ''
            bat_line = f'Bateria: {pct:5.1f}% {self._bar(pct)}{suffix}'
        else:
            bat_line = 'Bateria: ---'

        if self._is_docked is not None:
            dock_line = f'Dock:    {"DOCKEADO" if self._is_docked else "LIBRE"}'
        else:
            dock_line = 'Dock:    ---'

        msg.text = f'=== ESTADO DEL ROBOT ===\n{bat_line}\n{dock_line}\n{self._nav2_line()}'
        self._pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = RobotStatusOverlay()
    rclpy.spin(node)
    rclpy.shutdown()


if __name__ == '__main__':
    main()
