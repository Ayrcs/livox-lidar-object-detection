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
/diagnostics                 diagnostic_msgs/msg/DiagnosticArray
```

Le JSON contient les coordonnées corrigées `X avant, Y gauche, Z haut`, la
classe, le score, la taille de boîte, le nombre de points et le temps de
traitement `processing_ms`. Il fournit également les coordonnées équivalentes
dans le repère source ainsi que les compteurs `received_frames` et
`dropped_frames`. Un worker dédié conserve uniquement le dernier nuage reçu :
une trame obsolète est remplacée au lieu d'augmenter la latence. Les marqueurs
sont des cubes rouges exprimés directement
dans le `frame_id` du PointCloud2. Foxglove et RViz peuvent donc les superposer
au nuage sans transformation TF supplémentaire.

`/diagnostics` publie les mêmes compteurs sous forme ROS standard avec l'état
du modèle, le device, la latence et le nombre de détections.

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

Le 3 août 2026, l'image `lidar-detection-jetson:0.1.0` a été construite avec
succès directement sur l'Orin NX R35.3.1 à partir du commit `2fdf087`. Cette
validation couvre la résolution des dépendances et la compilation ARM64/CUDA ;
le chargement CUDA et l'inférence ROS restent des contrôles séparés.

Le test du conteneur sur cette même machine confirme ensuite : CUDA disponible,
GPU `Orin`, PyTorch `2.0.0a0+ec3941ad.nv23.02`, MMCV `2.1.0`, MMDetection
`3.2.0` et MMDetection3D `1.4.0`.

## Construction sur le robot

L'environnement lourd et l'application sont séparés :

- `lidar-detection-jetson-base:0.1.0` contient ROS, PyTorch, MMCV et
  MMDetection3D ;
- `lidar-detection-jetson:0.1.0` contient seulement le code du nœud.

Depuis la racine du dépôt, le script construit la base uniquement si elle
n'existe pas, puis reconstruit la couche applicative :

```bash
sudo ./docker/build-jetson.sh
```

MMCV et MMDetection3D compilent des extensions CUDA ARM64. Cette première
construction est longue. Tant que le tag de base ne change pas, les évolutions
du code ne recompilent plus MMCV.

### Migration depuis l'ancienne image combinée

Si `lidar-detection-jetson:0.1.0` a déjà été construit avec l'ancien
Dockerfile combiné, il contient toutes les dépendances lourdes. Il peut devenir
la base sans recompilation :

```bash
sudo docker tag \
  lidar-detection-jetson:0.1.0 \
  lidar-detection-jetson-base:0.1.0

sudo ./docker/build-jetson.sh
```

Le point d'entrée source ROS Foxy puis ajoute `/usr/local` à
`AMENT_PREFIX_PATH`, car le paquet `ament_python` est installé par `pip` dans ce
préfixe. Sans cette étape, `ros2 launch` ne voit que les paquets de
`/opt/ros/foxy`.

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
    model_path:=/model \
    input_topic:=/utlidar/cloud_livox_mid360 \
    score_threshold:=0.10
```

Lorsque `model_path` désigne un dossier, le nœud vérifie tous les fichiers de
`SHA256SUMS`, puis résout automatiquement `model.pth` et `config.py`. Il refuse
de démarrer si le paquet est incomplet ou si une empreinte ne correspond pas.

Contrôles fonctionnels :

```bash
ros2 topic echo /lidar/detections_json
ros2 topic hz /lidar/detections_json
ros2 topic info /lidar/detection_markers
```

Dans Foxglove, ajouter `/lidar/detection_markers` à la vue 3D contenant déjà
`/utlidar/cloud_livox_mid360`. Ajouter `/lidar/detections_json` dans un panneau
Raw Messages pour lire les valeurs numériques.

La procédure détaillée et le diagnostic d'affichage sont décrits dans
[`foxglove_visualization.md`](foxglove_visualization.md).
