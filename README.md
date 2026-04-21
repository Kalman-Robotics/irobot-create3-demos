# iRobot Create 3 Demos

Nodos ROS 2 de demostración para el iRobot Create 3. Diseñados para ejecutarse directamente desde tu laptop conectada al robot del laboratorio remoto.

## Prerrequisitos

- ROS 2 Humble instalado en tu laptop
- Conectado al laboratorio remoto (Husarnet activo, acceso al robot)
- RPLIDAR A1 montado en el robot (requerido por los demos reactivos a sensores)

## Inicio rápido

### 1. Crear el workspace y clonar

```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
git clone https://github.com/Kalman-Robotics/irobot-create3-demos.git
```

### 2. Instalar dependencias del sistema

```bash
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
```

### 3. Compilar

```bash
colcon build --packages-select irobot_demos
source install/setup.bash
```

> Agrega `source ~/ros2_ws/install/setup.bash` a tu `~/.bashrc` para no tener que ejecutarlo cada vez.

### 4. Ejecutar un demo

```bash
ros2 run irobot_demos cuadrado
```

## Demos disponibles

### Movimiento y trayectorias

| Comando | Descripción |
|---|---|
| `ros2 run irobot_demos cuadrado` | Traza un cuadrado de lado configurable usando odometría |
| `ros2 run irobot_demos espiral` | Traza una espiral hacia adentro y se detiene al completarla |

### Reactivo a sensores (RPLIDAR A1)

| Comando | Descripción |
|---|---|
| `ros2 run irobot_demos evitar_obstaculos` | Avanza, detecta obstáculo al frente y gira hacia el lado con más espacio libre |
| `ros2 run irobot_demos explorador` | Patrullaje autónomo: siempre en movimiento, orienta el robot hacia el espacio más abierto |
| `ros2 run irobot_demos seguidor_paredes` | Se mantiene a distancia constante de la pared izquierda |

### Control

| Comando | Descripción |
|---|---|
| `ros2 run irobot_demos control_p` | Controlador proporcional: gira hasta alcanzar un ángulo objetivo y se detiene |

### IMU

| Comando | Descripción |
|---|---|
| `ros2 run irobot_demos antivuelco` | Detecta inclinación mayor al umbral (levantamiento o empuje) y detiene el robot |

### Visualización

| Comando | Descripción |
|---|---|
| `ros2 run irobot_demos telemetria_live` | Dashboard en terminal: posición, velocidad, batería, IMU y estado del dock en tiempo real |
| `ros2 run irobot_demos radar` | Vista del LiDAR estilo radar actualizándose en terminal a ~2 Hz |

### Parámetros opcionales

```bash
ros2 run irobot_demos cuadrado          --ros-args -p lado:=0.5
ros2 run irobot_demos espiral           --ros-args -p duracion:=90.0
ros2 run irobot_demos explorador        --ros-args -p burbuja:=0.28
ros2 run irobot_demos control_p         --ros-args -p angulo_objetivo:=90.0
ros2 run irobot_demos antivuelco        --ros-args -p umbral:=20.0
ros2 run irobot_demos radar             --ros-args -p escala:=0.05 -p radio:=2.0
```
