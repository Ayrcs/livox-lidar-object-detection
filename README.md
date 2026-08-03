# LiDAR object detection

Ce dépôt prépare une chaîne reproductible de détection 3D LiDAR pour le
Unitree G1. Il sépare volontairement :

- `lidar_detection_training` : données, mesures, baseline et entraînement ;
- `lidar_detection_ros` : adaptation ROS 2 et inférence ;
- `model_registry` : contrat des artefacts livrables.

La stratégie et les critères de livraison sont décrits dans [ROADMAP.md](ROADMAP.md).
Les valeurs propres au robot doivent être relevées dans
[`docs/sensor_inventory.md`](docs/sensor_inventory.md), sans être codées en dur.
Les premières mesures de visibilité sont consignées dans
[`docs/ball_visibility_report.md`](docs/ball_visibility_report.md).
Le format d'extraction reproductible est décrit dans
[`docs/canonical_data_format.md`](docs/canonical_data_format.md).
La première baseline sans apprentissage est évaluée dans
[`docs/geometric_baseline_report.md`](docs/geometric_baseline_report.md).

## Démarrage hors ROS

```bash
python -m pip install -e './lidar_detection_training[test,rosbag,analysis]'
pytest lidar_detection_training/tests
```

## Démarrage ROS 2 (prévu)

La cible robot mesurée est ROS 2 Foxy. Le paquet d'inférence n'est pas encore
implémenté ; son contrat de lancement prévu est :

```bash
colcon build --packages-select lidar_detection_ros
source install/setup.bash
ros2 launch lidar_detection_ros detector.launch.py \
  model_path:=/chemin/vers/un/artefact \
  input_topic:=/utlidar/cloud_livox_mid360
```

Le dépôt ne contient ni rosbag, ni annotation, ni poids. Ces artefacts sont
volumineux et doivent être référencés par manifeste et somme SHA-256.
