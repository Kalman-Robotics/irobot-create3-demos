from setuptools import setup

package_name = 'irobot_demos'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Kalman Robotics',
    maintainer_email='kalmanrobotics@gmail.com',
    description='Demos en Python para el iRobot Create 3 de Kalman Robotics',
    license='Apache License, Version 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'cuadrado          = irobot_demos.cuadrado:main',
            'espiral           = irobot_demos.espiral:main',
            'evitar_obstaculos = irobot_demos.evitar_obstaculos:main',
            'explorador        = irobot_demos.explorador:main',
            'seguidor_paredes  = irobot_demos.seguidor_paredes:main',
            'control_p         = irobot_demos.control_p:main',
            'antivuelco        = irobot_demos.antivuelco:main',
            'telemetria_live   = irobot_demos.telemetria_live:main',
            'radar             = irobot_demos.radar:main',
        ],
    },
)
