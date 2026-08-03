# Déploiement du détecteur sur le Unitree G1

## Interface publiée

Le nœud s'abonne par défaut à :

```text
/utlidar/cloud_livox_mid360  sensor_msgs/msg/PointCloud2
```

Il publie deux sorties complémentaires :

```text
/lidar/detections_json       std_msgs/msg/String
/lidar/detection_markers     visualization_msgs/msg/MarkerArray
```

Le JSON contient les coordonnées corrigées `X avant, Y gauche, Z haut`, la
classe, le score, la taille de boîte et les coordonnées équivalentes dans le
repère source. Les marqueurs sont des cubes rouges exprimés directement dans le
`frame_id` du PointCloud2. Foxglove et RViz peuvent donc les superposer au
nuage sans transformation TF supplémentaire.

## Environnement cible observé

- Unitree G1, NVIDIA Orin NX Developer Kit, architecture `aarch64` ;
- Ubuntu 20.04 et L4T R35.3.1 ;
- ROS 2 Foxy avec Cyclone DDS ;
- Docker 24.0.7 ;
- NVIDIA Container Runtime disponible ;
- ni PyTorch, ni MMDetection3D installés sur l'hôte.

Le projet ne modifie pas l'installation Python du robot. L'inférence et ses
dépendances sont isolées dans une image Docker ARM64. L'image de base NVIDIA
`nvcr.io/nvidia/l4t-pytorch:r35.2.1-pth2.0-py3` fournit PyTorch 2.0 pour la
famille JetPack 5/L4T R35. La compatibilité exacte avec l'hôte R35.3.1 doit être
confirmée par le test GPU après construction.

## Construction sur le robot

Depuis la racine du dépôt :

```bash
sudo docker build \
  --network host \
  -f docker/inference-jetson.Dockerfile \
  -t lidar-detection-jetson:0.1.0 \
  .
```

MMCV et MMDetection3D compilent des extensions CUDA ARM64. Cette première
construction est longue ; les constructions suivantes réutilisent le cache
Docker.

## Test du GPU et des versions

```bash
sudo docker run --rm --runtime nvidia --network host \
  lidar-detection-jetson:0.1.0 \
  python3 -c "import torch, mmcv, mmdet, mmdet3d; print(torch.cuda.is_available(), torch.__version__, mmcv.__version__, mmdet.__version__, mmdet3d.__version__)"
```

## Lancement du nœud

Le checkpoint pilote est inclus dans Git. Après un clonage du dépôt, son
répertoire est monté en lecture seule dans le conteneur :

```bash
sudo docker run --rm --runtime nvidia --network host --ipc host \
  -v "$PWD/model_registry/ball_pointpillars_pilot_v0.1.0:/model:ro" \
  lidar-detection-jetson:0.1.0 \
  ros2 launch lidar_detection_ros detection.launch.py \
    model_path:=/model/model.pth \
    config_path:=/model/config.py \
    input_topic:=/utlidar/cloud_livox_mid360 \
    score_threshold:=0.10
```

Contrôles fonctionnels :

```bash
ros2 topic echo /lidar/detections_json
ros2 topic hz /lidar/detections_json
ros2 topic info /lidar/detection_markers
```

Dans Foxglove, ajouter `/lidar/detection_markers` à la vue 3D contenant déjà
`/utlidar/cloud_livox_mid360`. Ajouter `/lidar/detections_json` dans un panneau
Raw Messages pour lire les valeurs numériques.
