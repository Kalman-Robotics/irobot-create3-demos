# irobot_navigation

- [irobot\_navigation](#irobot_navigation)
  - [Archivos Launch](#archivos-launch)
    - [`slam.launch.py`](#slamlaunchpy)
    - [`localization.launch.py`](#localizationlaunchpy)
    - [`nav2.launch.py`](#nav2launchpy)
    - [`autonomous_nav.launch.py`](#autonomous_navlaunchpy)
  - [Uso](#uso)
    - [Mapeo](#mapeo)
    - [Navegación con mapa existente](#navegación-con-mapa-existente)
    - [SLAM + navegación simultáneos](#slam--navegación-simultáneos)

## Archivos Launch

### `slam.launch.py`
Lanza únicamente SLAM Toolbox para mapear el entorno. No inicia Nav2 ni RViz.

**Argumentos:**
- `use_sim_time`: Usar reloj de simulación (default: `true`)
  - Valores aceptados: `true`, `false`
- `sync`: Usar modo síncrono de SLAM (default: `true`)
  - Valores aceptados: `true`, `false`
- `namespace`: Namespace del robot (default: `''`)
- `params`: Ruta al archivo de configuración de SLAM (default: `<irobot_navigation>/config/slam.yaml`)

---

### `localization.launch.py`
Lanza AMCL para localizar el robot sobre un mapa previamente guardado. No inicia Nav2.

**Argumentos:**
- `use_sim_time`: Usar reloj de simulación (default: `true`)
  - Valores aceptados: `true`, `false`
- `map`: Ruta al archivo de mapa (default: `<irobot_navigation>/maps/mapa.yaml`)
- `namespace`: Namespace del robot (default: `''`)
- `params`: Ruta al archivo de configuración de localización (default: `<irobot_navigation>/config/localization.yaml`)

---

### `nav2.launch.py`
Lanza el stack de navegación Nav2. Requiere que AMCL o SLAM ya estén activos para disponer del mapa.

**Argumentos:**
- `use_sim_time`: Usar reloj de simulación (default: `true`)
  - Valores aceptados: `true`, `false`
- `namespace`: Namespace del robot (default: `''`)
- `params_file`: Ruta al archivo de configuración de Nav2 (default: `<irobot_navigation>/config/nav2.yaml`)

---

### `autonomous_nav.launch.py`
Orquestador del stack completo. Permite combinar en un único comando: SLAM, localización, Nav2 y RViz. Cada componente se activa de forma independiente mediante sus argumentos.

**Argumentos:**
- `use_sim_time`: Usar reloj de simulación (default: `true`)
  - Valores aceptados: `true`, `false`
- `slam`: Lanzar SLAM Toolbox (default: `false`)
  - Valores aceptados: `true`, `false`
- `localization`: Lanzar localización AMCL (default: `false`)
  - Valores aceptados: `true`, `false`
- `nav2`: Lanzar Nav2 (default: `false`)
  - Valores aceptados: `true`, `false`
- `rviz`: Lanzar RViz con configuración de navegación (default: `false`)
  - Valores aceptados: `true`, `false`
- `map`: Ruta al archivo de mapa para localización (default: `<irobot_navigation>/maps/mapa.yaml`)
- `namespace`: Namespace del robot (default: `''`)
- `localization_params`: Parámetros de localización (default: `<irobot_navigation>/config/localization.yaml`)
- `slam_params`: Parámetros de SLAM (default: `<irobot_navigation>/config/slam.yaml`)
- `nav2_params`: Parámetros de Nav2 (default: `<irobot_navigation>/config/nav2.yaml`)

## Uso

### Mapeo
Explora el entorno con el robot para construir un mapa. Usa `rviz:=true` para ver el mapa formándose en tiempo real.
```bash
ros2 launch irobot_navigation autonomous_nav.launch.py use_sim_time:=false slam:=true rviz:=true
```

Para guardar el mapa generado:
```bash
ros2 service call /slam_toolbox/save_map slam_toolbox/srv/SaveMap "name:
  data: '$(pwd)/mapa'"
```
Esto genera `mapa.pgm` y `mapa.yaml` en el directorio actual. Copia ambos archivos a `maps/` dentro del paquete y recompila para que queden disponibles como mapa por defecto.

### Navegación con mapa existente
Localiza el robot sobre el mapa guardado y habilita la navegación autónoma.
```bash
ros2 launch irobot_navigation autonomous_nav.launch.py use_sim_time:=false localization:=true nav2:=true rviz:=true
```

Al abrirse RViz:
1. Establecer la posición inicial del robot con la herramienta **2D Pose Estimate**.
2. Para mejorar la localización, girar el robot manualmente o con teleoperación.
3. Usar la herramienta **2D Nav Goal** para enviar un destino; el robot navegará automáticamente.

### SLAM + navegación simultáneos
Construye el mapa y navega al mismo tiempo, sin necesidad de un mapa previo.
```bash
ros2 launch irobot_navigation autonomous_nav.launch.py use_sim_time:=false slam:=true nav2:=true rviz:=true
```
