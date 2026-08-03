# Détection 3D d'objets LiDAR pour Unitree G1

## Avant-propos

Ce projet fournit une chaîne complète et reproductible pour apprendre à
détecter des objets dans le nuage de points du LiDAR Livox Mid-360 d'un
Unitree G1, puis exécuter le modèle sur le GPU NVIDIA Orin du robot avec
ROS 2.

Le premier cas traité est un ballon de football de taille 5. Le dépôt couvre
les deux parties du travail :

1. transformer des enregistrements ROS 2 en données annotées, entraîner et
   évaluer un modèle PointPillars sur une machine NVIDIA ;
2. charger le modèle dans un conteneur sur le G1, recevoir le PointCloud2 en
   direct et publier des coordonnées numériques ainsi que des boîtes 3D pour
   Foxglove ou RViz.

Le checkpoint livré est un **modèle pilote**, pas un modèle de production. Il
a validé toute la chaîne sur quelques scènes statiques en intérieur, mais les
essais réels montrent encore une confiance parfois faible sur le ballon et des
scores élevés sur certains artefacts. Il faut maintenant l'entraîner avec des
scènes, positions et négatifs difficiles beaucoup plus variés. Cette limite est
importante : une bonne métrique sur quatre sessions proches ne garantit pas la
généralisation dans un nouvel environnement.

La même architecture pourra accueillir d'autres objets, mais le pilote actuel
est configuré pour la classe `ball` et une boîte fixe de 22 cm. Ajouter une
classe demande de créer sa taxonomie et ses annotations, d'adapter la
configuration MMDetection3D, puis de déclarer les nouvelles classes et tailles
dans le paquet de modèle et le nœud d'inférence.

## Ce qui entre et ce qui sort

### Entraînement

| Élément | Entrée | Sortie |
|---|---|---|
| Acquisition | Rosbags ROS 2 et métadonnées de session | Données brutes immuables et sommes SHA-256 |
| Préparation | `/utlidar/cloud_livox_mid360` de type `sensor_msgs/msg/PointCloud2` | Nuages canoniques corrigés, métadonnées et manifeste |
| Annotation | Nuages canoniques et boîtes 3D relues | JSON par échantillon : classe, centre, dimensions et lacet |
| Entraînement | Fichiers `x, y, z, intensity`, annotations et split par sessions | Checkpoints, logs, métriques et environnement figé |
| Livraison | Checkpoint sélectionné et configuration | Paquet versionné sous `model_registry/` |

### Inférence sur le robot

Entrée par défaut :

```text
/utlidar/cloud_livox_mid360  sensor_msgs/msg/PointCloud2
```

Sorties :

```text
/lidar/detections_json       std_msgs/msg/String
/lidar/detection_markers     visualization_msgs/msg/MarkerArray
/diagnostics                 diagnostic_msgs/msg/DiagnosticArray
```

Le JSON contient la classe, le score, le centre et la taille de chaque boîte,
le temps de traitement et les compteurs de trames reçues ou remplacées. Les
coordonnées corrigées suivent la convention `X avant, Y gauche, Z haut`. Les
marqueurs dessinent une boîte rouge et une étiquette superposables au nuage
dans Foxglove ou RViz.

## Architecture

```text
Unitree G1 / Livox
        │ rosbag PointCloud2
        ▼
Extraction canonique ─► annotation ─► split par sessions
        │                                      │
        │                                      ▼
        │                         entraînement PointPillars
        │                                      │
        │                                      ▼
        └──────────────────────────── paquet de modèle versionné
                                               │
                                               ▼
                             conteneur d'inférence sur l'Orin
                                               │
                         ┌─────────────────────┼──────────────────┐
                         ▼                     ▼                  ▼
                       JSON              marqueurs 3D        diagnostics
```

Le code d'entraînement ne dépend pas du nœud ROS. Le nœud ne connaît ni les
rosbags ni l'organisation du dataset : leur contrat commun est le paquet de
modèle contenant le checkpoint, sa configuration, ses classes, ses métriques
et ses empreintes.

## Machines utilisées

- **Acquisition et inférence :** Unitree G1, NVIDIA Orin NX, ARM64,
  Ubuntu 20.04, L4T R35.3.1 et ROS 2 Foxy.
- **Entraînement de référence :** Ubuntu 22.04 x86_64 avec RTX 3090 24 Go,
  Docker et NVIDIA Container Runtime.
- **Préparation et tests :** Python 3.10 ou plus récent. Un Mac ou une machine
  sans CUDA peut préparer et contrôler les données, mais l'entraînement
  MMDetection3D officiel nécessite un GPU NVIDIA.

Les versions exactes de la station sont consignées dans
[`docs/training_machine_trojalab02.md`](docs/training_machine_trojalab02.md).
La pile Cyclone DDS du G1 est particulière : lire impérativement la section de
compatibilité dans
[`docs/deployment_guide.md`](docs/deployment_guide.md) avant de construire
l'image pour un autre robot.

## Organisation du dépôt

```text
├── README.md                      point d'entrée et démarrage rapide
├── ROADMAP.md                     architecture cible, décisions et étapes
├── docs/                          protocoles, guides et rapports lisibles
├── data/                          données locales brutes/traitées, hors Git
├── remote-g1/                     zone locale de transfert depuis le robot
├── data_manifests/                description versionnée des données
│   ├── sessions/                  conditions de chaque acquisition
│   ├── datasets/                  composition et provenance des datasets
│   ├── annotations/               versions des jeux d'annotations
│   └── environments/              machines et environnements d'expérience
├── lidar_detection_training/      préparation, annotation, métriques, entraînement
│   ├── configs/                   données, splits, modèles et expériences
│   ├── src/lidar_training/        bibliothèque Python testable
│   ├── tools/                     commandes de préparation et d'entraînement
│   └── tests/                     tests du pipeline de données
├── lidar_detection_ros/           paquet ROS 2 d'inférence
│   ├── launch/                    lancement paramétrable
│   ├── lidar_detection_ros/       backend, adaptation PointCloud2 et messages
│   ├── tools/                     inférence hors ROS sur un nuage `.bin`
│   └── test/                      tests du runtime ROS
├── docker/                        images d'entraînement et d'inférence Jetson
├── model_registry/                modèles livrables, manifests et SHA-256
├── reports/                       métriques et preuves versionnées
└── runs/                          sorties locales d'entraînement, hors Git
```

`data/`, `remote-g1/` et `runs/` peuvent devenir volumineux et restent hors de
Git. Les manifestes, configurations, rapports et petits modèles explicitement
autorisés sont versionnés pour garder la traçabilité.

## Documentation

### Comprendre le capteur et les données

- [`ROADMAP.md`](ROADMAP.md) : vision globale, choix techniques et critères de
  réussite.
- [`docs/sensor_inventory.md`](docs/sensor_inventory.md) : système, topic,
  champs, fréquence, QoS, repères et horodatage réellement observés.
- [`docs/ball_visibility_report.md`](docs/ball_visibility_report.md) : nombre
  de retours LiDAR sur le ballon selon la distance.
- [`docs/data_collection_protocol.md`](docs/data_collection_protocol.md) :
  scénarios à enregistrer et règles de conservation des rosbags.
- [`docs/session_metadata_template.yaml`](docs/session_metadata_template.yaml) :
  métadonnées à copier dans chaque session.
- [`docs/canonical_data_format.md`](docs/canonical_data_format.md) : format
  indépendant de ROS et correction du montage tête en bas.

### Annoter et établir une référence

- [`docs/annotation_guide.md`](docs/annotation_guide.md) : convention des boîtes
  3D, format JSON, difficultés et contrôle humain.
- [`docs/preannotation_report.md`](docs/preannotation_report.md) : méthode et
  limites des préannotations géométriques.
- [`docs/geometric_baseline_report.md`](docs/geometric_baseline_report.md) :
  résultats du détecteur sans apprentissage.

### Entraîner et évaluer

- [`docs/training_guide.md`](docs/training_guide.md) : environnement Docker,
  commandes PointPillars et règles de reproductibilité.
- [`docs/training_machine_trojalab02.md`](docs/training_machine_trojalab02.md) :
  machine NVIDIA utilisée.
- [`docs/pointpillars_overfit_report.md`](docs/pointpillars_overfit_report.md) :
  test de mémorisation du mini-dataset.
- [`docs/pointpillars_pilot_report.md`](docs/pointpillars_pilot_report.md) :
  métriques et limites du premier modèle.
- [`docs/model_card_template.md`](docs/model_card_template.md) : fiche à remplir
  pour toute nouvelle version de modèle.

### Déployer et visualiser

- [`docs/deployment_guide.md`](docs/deployment_guide.md) : construction Jetson,
  compatibilité Cyclone DDS, lancement et diagnostic.
- [`docs/foxglove_visualization.md`](docs/foxglove_visualization.md) : ajout du
  nuage, des boîtes rouges et du JSON dans Foxglove.
- [`model_registry/README.md`](model_registry/README.md) : contenu obligatoire
  d'un paquet de modèle.

## Installation pour préparer les données et lancer les tests

Depuis une machine avec Python 3.10 ou plus récent :

```bash
git clone https://github.com/Ayrcs/livox-lidar-object-detection.git
cd livox-lidar-object-detection

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e './lidar_detection_training[test,rosbag,analysis]'
```

Vérifier l'installation :

```bash
PYTHONPATH=lidar_detection_ros:lidar_detection_training/src \
  python -m pytest -q lidar_detection_training/tests lidar_detection_ros/test
```

## Préparer un dataset

1. Enregistrer plusieurs sessions en suivant le protocole d'acquisition.
2. Conserver les rosbags sous `remote-g1/lidar_data/raw/` ou adapter le chemin.
3. Créer les manifestes de session et vérifier leurs SHA-256.
4. Extraire les nuages dans le format canonique :

```bash
.venv/bin/python lidar_detection_training/tools/extract_canonical_dataset.py \
  --config lidar_detection_training/configs/data/canonical_v1.yaml \
  --bags-root remote-g1/lidar_data/raw \
  --output-dir data/processed/ball_lidar_feasibility_v1
```

5. Produire éventuellement des préannotations, puis **relire humainement toutes
   les boîtes et toutes les scènes négatives** selon le guide d'annotation.
6. Définir les sessions d'entraînement, validation et test dans une nouvelle
   configuration de split. Ne jamais répartir des trames voisines d'une même
   session entre plusieurs splits.
7. Construire puis vérifier le dataset MMDetection3D :

```bash
.venv/bin/python lidar_detection_training/tools/build_pilot_dataset.py \
  --config lidar_detection_training/configs/data/pilot_split_v1.yaml

.venv/bin/python lidar_detection_training/tools/validate_pilot_dataset.py \
  --dataset-root data/processed/ball_lidar_pilot_v1_mmdet3d \
  --report reports/pilot_dataset_v1/validation.json
```

Ces commandes reproduisent le pilote actuel. Pour un nouveau dataset, créer des
identifiants et chemins versionnés plutôt que remplacer silencieusement les
fichiers `v1`.

## Entraîner PointPillars

Sur la machine NVIDIA, construire une fois l'image :

```bash
docker build -f docker/training.Dockerfile \
  -t lidar-pointpillars-training:1.0 .
```

Commencer par vérifier que le réseau sait mémoriser un petit sous-ensemble :

```bash
docker run --rm --gpus all --shm-size=8g \
  -v "$PWD:/workspace" -w /workspace \
  lidar-pointpillars-training:1.0 \
  bash lidar_detection_training/tools/run_pointpillars_training.sh overfit
```

Puis lancer l'entraînement pilote :

```bash
docker run --rm --gpus all --shm-size=8g \
  -v "$PWD:/workspace" -w /workspace \
  lidar-pointpillars-training:1.0 \
  bash lidar_detection_training/tools/run_pointpillars_training.sh pilot
```

Les checkpoints et journaux sont écrits dans `runs/`. Choisir le modèle sur un
split de validation indépendant de l'entraînement, puis l'évaluer sur un test
indépendant contenant aussi des scènes sans cible et des distracteurs. La loss
d'entraînement seule ne permet pas de choisir un modèle.

Pour un modèle de ballon plus robuste, le nouveau dataset devra notamment
contenir : plusieurs lieux et sols, pelouse, ballon immobile et roulant,
différentes distances et positions latérales, robot immobile et mobile,
occultations, trames sans ballon et objets provoquant actuellement de fortes
fausses confiances. Les détails sont dans le guide d'entraînement.

## Livrer un modèle

Chaque modèle accepté reçoit un dossier immuable, par exemple :

```text
model_registry/ball_pointpillars_v0.2.0/
├── model.pth
├── config.py
├── manifest.yaml
├── classes.yaml
├── metrics.json
├── model_card.md
├── environment.lock.txt
└── SHA256SUMS
```

Le manifeste doit préciser les champs d'entrée, le repère, la transformation,
la zone couverte, les classes, les tailles de boîtes, les versions logicielles
et les limites connues. Le nœud refuse un paquet incomplet ou dont une empreinte
ne correspond pas. Ne jamais remplacer le contenu d'une version déjà publiée :
créer une nouvelle version.

## Installer et lancer l'inférence sur le G1

Cloner le dépôt sur le robot, puis construire les trois couches Docker :

```bash
git clone https://github.com/Ayrcs/livox-lidar-object-detection.git
cd livox-lidar-object-detection
sudo ./docker/build-jetson.sh
```

La première construction de la base CUDA/MMDetection3D est longue. Les builds
suivants réutilisent cette base. La couche DDS doit correspondre à la version
de Cyclone réellement chargée sur le G1 ; le script actuel reproduit le robot
de référence avec Cyclone DDS 0.10.2.

Lancer le modèle pilote :

```bash
sudo docker run --rm \
  --runtime nvidia \
  --network host \
  --ipc host \
  -v "$PWD/model_registry/ball_pointpillars_pilot_v0.1.0:/model:ro" \
  lidar-detection-jetson:0.2.0 \
  ros2 launch lidar_detection_ros detection.launch.py \
    model_path:=/model \
    input_topic:=/utlidar/cloud_livox_mid360 \
    score_threshold:=0.10
```

Le chargement initial du modèle sur l'Orin prend environ 15 à 20 secondes. Le
nœud garde ensuite le modèle en mémoire et ne conserve que le nuage le plus
récent afin de ne pas accumuler de retard.

Dans un deuxième terminal du G1 :

```bash
ros2 topic echo /lidar/detections_json
ros2 topic hz /lidar/detections_json
ros2 topic echo /diagnostics
```

Pour Foxglove, lancer `rosbridge_websocket`, afficher
`/utlidar/cloud_livox_mid360`, puis activer
`/lidar/detection_markers` dans le même panneau 3D. Le guide Foxglove décrit
les réglages et le diagnostic si aucune boîte n'apparaît.

## État actuel et prochaines étapes

La chaîne technique est validée de bout en bout : acquisition, extraction,
annotation pilote, entraînement sur RTX 3090, paquet de modèle, inférence CUDA
sur Orin, publications ROS et affichage Foxglove.

Le travail prioritaire n'est plus l'intégration, mais la qualité du modèle :

1. enregistrer un dataset ballon diversifié avec davantage de négatifs
   difficiles ;
2. annoter et relire les nouvelles sessions ;
3. créer des splits par sessions et lieux avec un vrai jeu de test ;
4. réentraîner, calibrer le seuil et analyser les faux positifs par scénario ;
5. seulement ensuite étendre la taxonomie à d'autres objets.

Les résultats doivent toujours être interprétés avec la model card et les
limites du dataset correspondant.
