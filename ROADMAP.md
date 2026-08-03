# Feuille de route — Détection 3D par LiDAR pour Unitree G1 et ROS 2

> **But final :** fournir un nœud ROS 2 simple à intégrer qui reçoit un modèle et un topic `sensor_msgs/msg/PointCloud2`, exécute une détection 3D et publie les détections. Le premier modèle détectera un ballon de football à partir du LiDAR 360° du Unitree G1. Le second détectera deux classes : `ball` et `unitree_g1`.

## 1. Vision du projet

Le travail est volontairement séparé en deux sous-projets :

1. **`lidar_detection_training`** : acquisition, préparation et versionnement des données, annotation, entraînement, évaluation et export des modèles ;
2. **`lidar_detection_ros`** : paquet ROS 2 d'inférence, indépendant autant que possible du framework d'entraînement.

Cette séparation est essentielle. Le code ROS ne doit pas connaître l'organisation du dataset, tandis que le projet d'entraînement doit pouvoir fonctionner hors du robot, sur une station NVIDIA. Le lien entre les deux est un **artefact de modèle versionné**, accompagné d'un manifeste qui décrit exactement ses entrées, sorties, classes et prétraitements.

### Critères de réussite

Le projet ne sera pas considéré terminé parce qu'un entraînement produit une courbe ou parce que le nœud démarre. Il sera terminé lorsque :

- une autre personne peut enregistrer et annoter une nouvelle session en suivant la documentation ;
- elle peut reproduire un entraînement à partir d'un commit, d'une configuration et d'une version du dataset ;
- un modèle exporté est accompagné de son manifeste et de ses métriques ;
- le nœud accepte au minimum les paramètres `model_path` et `input_topic` ;
- les détections sont publiées avec le timestamp et le repère du nuage source ;
- le même rosbag rejoué donne des résultats déterministes à tolérance numérique près ;
- latence, fréquence, mémoire GPU, rappels et faux positifs sont mesurés sur le matériel cible.

## 2. Hypothèses à vérifier avant toute annotation

Ne pas coder le réseau neuronal en premier. La première semaine doit répondre à des questions de capteur et d'intégration.

### 2.1 Topic réellement fourni par le G1

La documentation Unitree montre le topic LiDAR `/utlidar/cloud` et le repère `utlidar_lidar`, mais il faut vérifier le robot réel plutôt que figer ces valeurs dans le code. Le pilote Livox peut publier un `PointCloud2` standard ou un format personnalisé selon sa configuration. Sources : [Unitree ROS 2](https://github.com/unitreerobotics/unitree_ros2) et [Livox ROS Driver 2](https://github.com/Livox-SDK/livox_ros_driver2).

Commandes de diagnostic :

```bash
ros2 topic list -t
ros2 topic type /utlidar/cloud
ros2 topic info -v /utlidar/cloud
ros2 topic echo /utlidar/cloud --once --no-arr
ros2 topic hz /utlidar/cloud
ros2 topic bw /utlidar/cloud
ros2 interface show sensor_msgs/msg/PointCloud2
```

À noter dans `docs/sensor_inventory.md` :

- distribution et version ROS 2 ;
- version du SDK Unitree et du pilote Livox ;
- nom, type, fréquence et QoS du topic ;
- `frame_id` ;
- champs présents et types (`x`, `y`, `z`, `intensity`, éventuellement `tag`, `line`, `timestamp`) ;
- convention des axes ;
- nombre moyen/minimum/maximum de points par message ;
- horodatage et éventuelle synchronisation avec TF/IMU/odométrie.

En Python ROS 2, `sensor_msgs_py.point_cloud2.read_points_numpy()` est adapté aux calculs NumPy lorsque les champs demandés ont le même type ; `read_points()` conserve une structure par champ. Éviter `read_points_list()` dans la boucle temps réel, car il crée une liste d'objets Python et est moins efficace. Voir la [documentation ROS 2 de `sensor_msgs_py`](https://docs.ros.org/en/kilted/p/sensor_msgs_py/sensor_msgs_py.point_cloud2.html).

### 2.2 Le ballon est-il observable ?

Un ballon de taille 5 fait environ 22 cm de diamètre. Un LiDAR ne « voit » pas un ballon comme une caméra : à mesure que la distance augmente, le nombre de retours sur le ballon chute. Selon le motif de balayage, l'orientation, le matériau, le mouvement et l'occlusion, certaines trames peuvent ne contenir que quelques points, voire aucun.

Créer immédiatement un script `tools/measure_ball_returns.py` qui, sur des nuages annotés, calcule :

- nombre de points dans la boîte 3D du ballon ;
- distance et azimut du centre ;
- intensité moyenne et dispersion ;
- dimensions du cluster ;
- proportion de trames sans retour exploitable.

Produire un tableau par tranches, par exemple `0–2 m`, `2–4 m`, `4–6 m`, `6–8 m`, puis au-delà. La portée utile du futur détecteur doit être déduite de ces mesures, pas de la portée commerciale maximale du LiDAR.

Une règle de travail raisonnable, à confirmer expérimentalement :

- **moins de 3 points** sur le ballon : une boîte 3D fiable est généralement impossible sur cette seule trame ;
- **3 à 10 points** : détection possible mais instable, nécessitant contexte ou accumulation temporelle ;
- **plus de 10 à 20 points** : géométrie et apprentissage deviennent nettement plus exploitables.

Ce ne sont pas des garanties physiques : ces seuils servent uniquement à structurer le premier protocole de mesure.

### 2.3 Définir la sortie attendue

Pour le ballon, distinguer deux besoins :

- **détection** : classe, score et position 3D ;
- **boîte 3D complète** : centre, dimensions et orientation.

L'orientation d'une sphère n'a pas de sens. Pour `ball`, publier une boîte de taille fixe ou estimée et une orientation identité. Pour `unitree_g1`, une boîte orientée et un angle de lacet sont utiles.

Format ROS recommandé : `vision_msgs/msg/Detection3DArray`, qui représente une liste de détections 3D. Ajouter éventuellement un message léger spécifique au ballon si le contrôleur a surtout besoin de `x`, `y`, `z`, `confidence`, mais conserver `Detection3DArray` comme interface générique.

## 3. Architecture cible du dépôt

Une organisation possible est :

```text
project_root/
├── README.md
├── ROADMAP.md
├── docs/
│   ├── sensor_inventory.md
│   ├── data_collection_protocol.md
│   ├── annotation_guide.md
│   ├── training_guide.md
│   ├── deployment_guide.md
│   └── model_card_template.md
├── lidar_detection_training/
│   ├── pyproject.toml
│   ├── configs/
│   │   ├── data/
│   │   ├── models/
│   │   └── experiments/
│   ├── src/lidar_training/
│   │   ├── io/
│   │   ├── preprocessing/
│   │   ├── datasets/
│   │   ├── models/
│   │   ├── evaluation/
│   │   └── export/
│   ├── tools/
│   └── tests/
├── lidar_detection_ros/
│   ├── package.xml
│   ├── setup.py
│   ├── setup.cfg
│   ├── resource/
│   ├── launch/
│   ├── config/
│   ├── lidar_detection_ros/
│   │   ├── node.py
│   │   ├── pointcloud_adapter.py
│   │   ├── preprocessing.py
│   │   ├── postprocessing.py
│   │   ├── messages.py
│   │   └── backends/
│   │       ├── protocol.py
│   │       ├── pytorch_backend.py
│   │       ├── onnx_backend.py
│   │       └── tensorrt_backend.py
│   └── test/
├── model_registry/
│   └── README.md
└── docker/
    ├── training.Dockerfile
    └── inference.Dockerfile
```

Les gros rosbags, nuages, annotations et poids ne doivent pas être stockés directement dans Git. Utiliser un stockage objet/NAS et un outil de versionnement tel que DVC, ou au minimum des manifestes avec sommes SHA-256.

## 4. Sous-projet A — Entraînement reproductible

### Phase A0 — Spécification et baseline sans apprentissage

Avant le deep learning, construire un détecteur géométrique simple :

1. limiter le nuage à une zone d'intérêt ;
2. retirer les points du robot et les zones impossibles ;
3. estimer/retirer le sol ;
4. regrouper les points par clustering euclidien ou DBSCAN ;
5. filtrer les clusters par hauteur, diamètre, sphéricité et intensité ;
6. suivre le candidat dans le temps avec un filtre de Kalman simple.

Cette baseline fournit :

- une preuve que le ballon est observable ;
- un outil de pré-annotation ;
- un niveau minimal que le réseau doit dépasser ;
- un fallback lorsque le GPU ou le modèle échoue.

Exemple de premier espace de recherche, à adapter aux mesures :

```yaml
roi:
  x_m: [-1.0, 10.0]
  y_m: [-6.0, 6.0]
  z_m: [-1.5, 2.0]
ground_removal:
  method: ransac
  distance_threshold_m: 0.03
clustering:
  eps_m: 0.10
  min_points: 3
ball_candidate:
  diameter_m: [0.12, 0.35]
```

Ces valeurs ne sont que des points de départ. Les paramètres finaux doivent être justifiés par des histogrammes issus du capteur réel.

### Phase A1 — Acquisition des données

#### Protocole

Enregistrer des **sessions**, et non une longue capture homogène. Chaque session doit avoir un identifiant et des métadonnées :

- lieu et surface : gazon, sol sportif, béton, intérieur/extérieur ;
- lumière et météo même si le LiDAR est moins sensible qu'une caméra ;
- position et mouvement du robot ;
- distance, azimut et visibilité du ballon ;
- ballon statique, roulant, partiellement masqué ;
- présence de personnes, pieds, sacs, cônes et objets ronds ;
- pour la phase 2 : un ou plusieurs G1, poses, orientations et occlusions ;
- versions logicielles et configuration du capteur.

Commande minimale, à ajuster aux topics réels :

```bash
ros2 bag record \
  /utlidar/cloud \
  /tf \
  /tf_static \
  /odom \
  -o data/raw/session_YYYYMMDD_site_scenario
```

Ajouter l'IMU et l'état robot s'ils sont nécessaires à la compensation de mouvement. `ros2 bag record` crée un abonné supplémentaire sans interrompre les autres abonnés du topic, conformément au fonctionnement publish/subscribe de ROS 2 ([documentation ROS 2](https://docs.ros.org/en/ros2_documentation/kilted/Concepts/Basic/About-Topics.html)).

#### Ordres de grandeur initiaux

Planifier en deux paliers :

| Palier | Sessions | Trames annotées | Usage |
|---|---:|---:|---|
| Faisabilité | 10–20 | 500–1 500 | Mesurer les retours, tester la baseline et la chaîne d'annotation |
| Modèle ballon v1 | 30–60 | 5 000–15 000 | Couvrir distances, terrains, mouvements et négatifs |
| Ballon + G1 v1 | 50–100 | 10 000–30 000 | Ajouter diversité de robots, poses et interactions |

Ces chiffres sont des budgets de départ, pas une vérité universelle. Quelques milliers de trames très diversifiées et correctement annotées valent mieux que 100 000 trames quasi identiques. Utiliser les courbes d'apprentissage pour décider si davantage de données est utile.

Inclure beaucoup de **trames négatives** : terrain sans ballon, objets sphériques, jambes, chaussures, pieds du G1, murs, mobilier et autres robots. Une cible pratique initiale est 20 à 40 % de trames sans objet cible, à ajuster après analyse des faux positifs.

### Phase A2 — Extraction et format canonique

Écrire un extracteur déterministe de rosbag vers un format canonique. Chaque échantillon doit contenir :

```text
sample_id
session_id
timestamp_ns
frame_id
points: N x F (x, y, z, intensity, champs Livox utiles)
calibration/transformations applicables
source_bag + index du message
```

Conserver les données brutes. Les nuages filtrés ou accumulés sont des dérivés régénérables.

#### Accumulation temporelle

Pour un petit ballon, agréger 2 à 5 balayages peut augmenter le nombre de points, mais introduit du flou lorsque le robot ou le ballon bouge. Si plusieurs balayages sont utilisés :

- transformer chaque nuage vers un repère commun avec TF/odométrie ;
- conserver l'âge relatif de chaque point comme feature si possible ;
- comparer systématiquement `1 sweep`, `3 sweeps` et `5 sweeps` ;
- créer des scénarios avec ballon roulant ;
- ne jamais accumuler naïvement des nuages dans des repères mobiles.

À 10 Hz, 5 balayages représentent environ 0,5 s de passé : c'est déjà long pour une balle ou un robot en mouvement. Commencer avec 1 et 3 balayages.

### Phase A3 — Annotation 3D

#### Convention d'annotation

Définir une convention unique dans `docs/annotation_guide.md` :

- classes exactes : `ball`, puis `unitree_g1` ;
- repère et unité : mètres, repère du LiDAR ou repère de base clairement choisi ;
- boîte au plus près des retours visibles ou dimensions physiques complètes ;
- traitement des objets tronqués et occultés ;
- nombre minimal de points pour annoter ;
- attributs `occluded`, `truncated`, `moving`, `num_points`, `difficulty` ;
- orientation du G1 : axe avant du robot ;
- orientation du ballon fixée à zéro/identité ;
- règle pour les trames où le ballon est connu mais ne produit aucun retour.

Le ballon peut utiliser une boîte à dimensions normalisées proches de sa taille physique. Pour le G1, mesurer plusieurs poses : debout, accroupi, marche, chute. Une boîte trop rigide sur toutes les poses dégradera les annotations.

#### Contrôle qualité

- Annoter deux fois 5 à 10 % des données pour mesurer l'accord entre annotateurs.
- Afficher les boîtes dans une vue 3D et dans une projection vue de dessus.
- Rejeter automatiquement les boîtes vides ou aux dimensions aberrantes.
- Calculer `num_points_in_box` pour chaque annotation.
- Faire relire tous les cas difficiles au début du projet.

Ordre de grandeur : une annotation 3D propre peut prendre de 20 secondes à plusieurs minutes selon l'outil, la densité et la pré-annotation. Un lot de 10 000 trames peut donc représenter plusieurs dizaines à quelques centaines d'heures. Mesurer le temps sur 100 trames avant d'engager le budget complet.

### Phase A4 — Découpage du dataset

Ne jamais découper aléatoirement des trames adjacentes : elles sont presque identiques et provoqueraient une fuite entre train et validation.

Découper **par session complète** :

- train : environ 70 % des sessions ;
- validation : environ 15 % ;
- test interne : environ 15 % ;
- test « challenge » séparé : nouveau lieu, nouvelle journée ou nouveaux objets perturbateurs.

Stratifier autant que possible par distance, terrain, mouvement, visibilité et classe. Le test final ne doit servir qu'aux décisions de livraison, pas au réglage quotidien.

### Phase A5 — Choix du modèle

#### Progression recommandée

1. **Baseline géométrique** : clustering + filtres + suivi.
2. **PointPillars** : rapide, architecture connue, bon premier détecteur LiDAR temps réel.
3. **CenterPoint ou SECOND** : à essayer si PointPillars plafonne et si le budget GPU le permet.
4. **Approche fusion caméra–LiDAR** : seulement si le LiDAR seul n'offre pas assez de retours aux distances utiles.

MMDetection3D fournit notamment PointPillars, SECOND et CenterPoint ainsi que des guides pour datasets personnalisés et inférence ([projet officiel](https://github.com/open-mmlab/mmdetection3d)). Épingler toutes les versions : PyTorch, CUDA, MMCV, MMEngine, MMDetection et MMDetection3D. Les extensions CUDA rendent les mélanges de versions fragiles.

#### Cas particulier du ballon

Les configurations automobiles de KITTI ne conviennent pas directement :

- plage spatiale trop grande ;
- voxels souvent trop grossiers pour un objet de 22 cm ;
- ancres et tailles de boîtes prévues pour voitures/piétons ;
- déséquilibre extrême entre espace vide et petite cible.

Premiers hyperparamètres à explorer :

```yaml
classes: [ball]
point_cloud_range_m: [-2.0, -8.0, -2.0, 12.0, 8.0, 3.0]
voxel_size_m:
  candidates:
    - [0.025, 0.025, 0.05]
    - [0.05, 0.05, 0.10]
ball_box_size_m: [0.22, 0.22, 0.22]
score_threshold_candidates: [0.10, 0.20, 0.35, 0.50]
nms_iou_threshold_candidates: [0.05, 0.10, 0.20]
```

Un voxel plus fin préserve le ballon mais augmente mémoire et calcul. Toujours mesurer le nombre de voxels, l'utilisation VRAM et la latence. Pour le G1, utiliser une plage et des tailles de boîtes distinctes ; un détecteur multi-classe peut partager le backbone mais doit disposer de statistiques de tailles par classe.

### Phase A6 — Environnement de calcul

#### NVIDIA — environnement de référence

Utiliser de préférence Linux + GPU NVIDIA pour l'entraînement officiel, car les détecteurs 3D s'appuient souvent sur des opérations sparse/voxel CUDA. MMDetection3D indique que certaines configurations ne se construisent pas en environnement CPU-only et exige un alignement précis entre PyTorch, CUDA et les extensions ([guide d'installation](https://github.com/open-mmlab/mmdetection3d/blob/main/docs/en/get_started.md)).

À enregistrer pour chaque expérience :

```bash
nvidia-smi
python --version
python -c "import torch; print(torch.__version__, torch.version.cuda)"
pip freeze > environment.lock.txt
git rev-parse HEAD
```

Ordres de grandeur très approximatifs, à mesurer sur le modèle réel :

- PointPillars sur une zone réduite : souvent quelques Go de VRAM ;
- batch 2 à 8 : point de départ réaliste sur une carte GeForce de 8 à 16 Go ;
- 50 à 160 époques : plage d'exploration courante ;
- quelques heures à plus d'une journée par expérience selon GPU, résolution des voxels et taille du dataset.

Ne pas promettre ces durées. Lancer d'abord un « smoke training » sur 100 échantillons et 2 époques, puis chronométrer 1 000 itérations.

#### Mac Apple Silicon

PyTorch propose le backend `mps` pour utiliser le GPU via Metal ([documentation PyTorch](https://docs.pytorch.org/docs/stable/notes/mps.html)). Les Mac sont utiles pour :

- exploration, visualisation et annotation ;
- tests unitaires et traitement NumPy ;
- petits prototypes PyTorch compatibles MPS ;
- validation fonctionnelle de l'artefact exporté.

Ils ne doivent pas être la plateforme officielle d'entraînement tant que toutes les opérations sparse/voxel du framework n'ont pas été validées sur MPS. Prévoir un fallback CPU pour les outils, mais entraîner les modèles 3D de référence sur NVIDIA/Linux.

### Phase A7 — Boucle d'entraînement

Pour chaque expérience :

1. valider le dataset et compter les classes ;
2. vérifier visuellement 20 échantillons après augmentation ;
3. faire sur-apprendre 50 à 100 trames — si le modèle n'y arrive pas, chercher un bug avant d'ajouter des données ;
4. lancer un entraînement court ;
5. analyser pertes et métriques par distance/difficulté ;
6. lancer l'expérience complète ;
7. enregistrer configuration, seed, commit, dataset, matériel et durée ;
8. conserver meilleur et dernier checkpoint ;
9. évaluer sur validation puis, rarement, sur test.

Augmentations à tester prudemment :

- rotation autour de l'axe vertical ;
- miroir gauche/droite si cohérent avec le terrain ;
- translation et mise à l'échelle faibles ;
- suppression aléatoire de points ;
- bruit de position/intensité proche du capteur réel ;
- insertion d'objets annotés dans d'autres scènes, avec contrôle du sol et des collisions.

Éviter les transformations qui changent artificiellement la taille physique du ballon ou placent le G1 dans une posture impossible.

### Phase A8 — Métriques utiles

Ne pas se limiter à la loss ou à une mAP globale.

Mesurer au minimum :

- précision, rappel et F1 par classe ;
- AP 3D et AP en vue de dessus à plusieurs seuils adaptés aux objets ;
- erreur du centre `x/y/z` en mètres ;
- rappel par tranche de distance ;
- rappel par nombre de points dans la vérité terrain ;
- faux positifs par minute et par scène négative ;
- latence moyenne, médiane, p95 et p99 ;
- fréquence soutenue et taux de messages abandonnés ;
- stabilité temporelle : sauts de position et identifiants de piste.

L'IoU est sévère pour un petit ballon : un décalage de quelques centimètres fait chuter fortement l'IoU. Compléter l'AP par une métrique de distance du centre, par exemple rappel si l'erreur est inférieure à 10, 20 ou 30 cm selon la distance.

Créer des critères d'acceptation avant l'entraînement, par exemple :

```text
Zone obligatoire : 0,5 à 6 m
Rappel ballon cible : >= 90 % entre 0,5 et 4 m, >= 75 % entre 4 et 6 m
Erreur médiane XY : <= 0,15 m
Faux positifs : <= 1 par 5 minutes sur le jeu négatif
Latence p95 : <= 80 ms sur le calculateur cible
```

Ces nombres illustrent la forme d'un contrat ; l'équipe doit les ajuster aux exigences du robot et à ce que permet le capteur.

### Phase A9 — Export et registre de modèles

Chaque livraison doit être un dossier autonome :

```text
model_registry/ball_pointpillars_v1.0.0/
├── model.pth              # ou model.onnx / model.engine
├── manifest.yaml
├── config.yaml
├── classes.yaml
├── metrics.json
├── model_card.md
├── environment.lock.txt
└── SHA256SUMS
```

Exemple de manifeste :

```yaml
schema_version: 1
model_name: ball_pointpillars
model_version: 1.0.0
backend: pytorch
task: lidar_3d_detection
classes:
  0: ball
input:
  fields: [x, y, z, intensity]
  frame_convention: source_pointcloud_frame
  point_cloud_range_m: [-2.0, -8.0, -2.0, 12.0, 8.0, 3.0]
preprocessing:
  voxel_size_m: [0.05, 0.05, 0.10]
  sweeps: 1
output:
  box_order: [x, y, z, length, width, height, yaw]
training:
  dataset_version: ball-lidar-v1.2.0
  git_commit: REPLACE_ME
compatibility:
  ros_distro: humble
```

Un moteur TensorRT n'est généralement pas portable entre toutes les générations de GPU et versions logicielles. Conserver le checkpoint source et, si possible, l'ONNX à côté du moteur. TensorRT est destiné à optimiser l'inférence sur GPU NVIDIA et prend notamment en charge des chemins PyTorch/ONNX, mais l'export des opérations 3D personnalisées doit être validé modèle par modèle ([documentation NVIDIA](https://docs.nvidia.com/tensorrt/)).

## 5. Sous-projet B — Nœud ROS 2 d'inférence

### Phase B0 — Contrat public

Le nœud doit pouvoir être lancé ainsi :

```bash
ros2 launch lidar_detection_ros detector.launch.py \
  model_path:=/models/ball_pointpillars_v1.0.0 \
  input_topic:=/utlidar/cloud \
  output_topic:=/lidar/detections_3d
```

Paramètres minimaux :

| Paramètre | Exemple | Rôle |
|---|---|---|
| `model_path` | `/models/ball_v1` | Artefact + manifeste |
| `input_topic` | `/utlidar/cloud` | Entrée `PointCloud2` |
| `output_topic` | `/lidar/detections_3d` | Sortie `Detection3DArray` |
| `backend` | `auto`, `pytorch`, `onnx`, `tensorrt` | Runtime |
| `device` | `cuda:0`, `cpu`, `mps` | Calcul |
| `score_threshold` | `0.25` | Seuil global ou par classe |
| `target_frame` | vide ou `base_link` | Repère de sortie optionnel |
| `max_queue_size` | `1` | Éviter d'accumuler des nuages anciens |
| `publish_debug_cloud` | `false` | Nuage filtré/coloré |
| `publish_markers` | `true` | Visualisation RViz |

### Phase B1 — Séparer ROS du moteur

Définir une interface Python indépendante de `rclpy` :

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class Detection3D:
    class_id: int
    score: float
    center_xyz: tuple[float, float, float]
    size_lwh: tuple[float, float, float]
    yaw: float


class DetectorBackend(Protocol):
    def load(self, model_dir: Path) -> None: ...
    def predict(self, points: np.ndarray) -> list[Detection3D]: ...
```

Cette interface permet de tester le prétraitement, le modèle et le post-traitement dans PyCharm sans ROS installé. Le nœud ROS devient un adaptateur : message → NumPy → backend → messages ROS.

### Phase B2 — Pipeline d'un callback

```text
PointCloud2
    ↓ validation du type, frame et champs
conversion NumPy sans objets Python par point
    ↓
filtrage ROI / NaN / points du robot
    ↓
voxelisation exactement identique à l'entraînement
    ↓
inférence
    ↓
seuils + NMS + conversion des boîtes
    ↓
transformation TF optionnelle
    ↓
Detection3DArray + MarkerArray + diagnostics
```

Règles importantes :

- réutiliser le timestamp du nuage entrant ;
- publier dans le même `frame_id`, sauf transformation TF explicite réussie ;
- ne jamais étiqueter comme `base_link` des coordonnées encore exprimées dans le repère LiDAR ;
- vérifier l'ordre des dimensions et la convention de `yaw` ;
- abandonner une trame ancienne plutôt que créer une file qui augmente la latence ;
- charger le modèle une seule fois au démarrage ;
- faire un warm-up avant d'annoncer que le nœud est prêt ;
- publier un diagnostic si les champs attendus manquent.

### Phase B3 — QoS et temps réel souple

Commencer avec le profil QoS « sensor data » et une profondeur faible, puis vérifier qu'il est compatible avec le publisher Unitree. Une queue de taille 1 est souvent préférable pour la perception : le robot a besoin du nuage le plus récent, pas de traiter en retard dix anciens nuages.

Ne pas faire l'inférence lourde directement dans un callback qui bloque tout l'exécuteur sans stratégie. Options :

- worker dédié avec un unique slot « dernier nuage reçu » ;
- callback group et exécuteur multithread correctement contrôlés ;
- nœud composable/C++ plus tard si la conversion Python devient le goulot.

Mesurer séparément : conversion `PointCloud2 → NumPy`, prétraitement, GPU, post-traitement et publication.

### Phase B4 — Sorties et diagnostics

Publier :

- `/lidar/detections_3d` : `vision_msgs/msg/Detection3DArray` ;
- `/lidar/detection_markers` : `visualization_msgs/msg/MarkerArray` ;
- `/lidar/debug_cloud` : optionnel et désactivé par défaut ;
- `/diagnostics` : fréquence entrée/sortie, latence, drops, statut modèle/device.

Pour chaque boîte RViz, afficher classe, score et distance. Utiliser une durée de vie légèrement supérieure à la période nominale pour éviter les fantômes persistants.

### Phase B5 — Portabilité des backends

Ordre recommandé :

1. **PyTorch** pour obtenir rapidement une référence correcte ;
2. **ONNX Runtime** si toutes les opérations s'exportent correctement ;
3. **TensorRT** pour la cible NVIDIA lorsque le gain est mesuré et l'export validé ;
4. C++ uniquement si le profilage montre que Python est réellement limitant.

Le mode `auto` doit lire `manifest.yaml`, vérifier le matériel disponible et choisir un backend compatible. Il ne doit pas silencieusement changer la précision ou le prétraitement.

### Phase B6 — Tests

#### Hors ROS

- parsing du manifeste ;
- validation des champs du nuage ;
- filtrage ROI ;
- conversions de repères et de boîtes ;
- NMS et seuils ;
- backend factice déterministe ;
- comparaison avec des sorties « golden » sur quelques nuages figés.

#### Avec ROS 2

- démarrage/arrêt propre du nœud ;
- paramètres invalides ;
- réception d'un `PointCloud2` synthétique ;
- conservation du timestamp et du `frame_id` ;
- test de launch ;
- rosbag court en CI d'intégration si possible.

#### Sur robot

```bash
ros2 topic hz /utlidar/cloud
ros2 topic hz /lidar/detections_3d
ros2 topic delay /lidar/detections_3d
ros2 topic echo /lidar/detections_3d --once
rviz2
```

Faire trois essais séparés : ballon immobile, ballon roulant, robot en mouvement. Puis un essai négatif d'au moins 10 à 30 minutes.

## 6. Passage d'une classe à deux classes

Ne pas simplement ajouter quelques boîtes `unitree_g1` à l'ancien dataset.

1. Geler et documenter `ball_v1` comme baseline.
2. Ajouter des sessions contenant uniquement un G1, uniquement un ballon, les deux, aucun des deux et plusieurs robots.
3. Réannoter ou convertir l'ancien dataset avec une taxonomie versionnée.
4. Vérifier l'équilibre par classe, distance et nombre de points.
5. Initialiser depuis le modèle ballon seulement si l'expérience montre un bénéfice ; comparer à un entraînement depuis un backbone standard.
6. Évaluer les deux classes séparément et vérifier que le rappel du ballon ne régresse pas.
7. Ajouter un suivi temporel et des identifiants de piste dans un composant distinct du détecteur.

Le G1 a beaucoup plus de points que le ballon : la loss peut être dominée par cette classe. Examiner les poids de classes, l'échantillonnage et les métriques macro plutôt que la seule moyenne globale.

## 7. Gestion des expériences

Chaque run doit produire :

```text
runs/<experiment_id>/
├── resolved_config.yaml
├── dataset_manifest.json
├── environment.txt
├── metrics.json
├── checkpoints/
├── predictions/
├── plots/
└── notes.md
```

Nom conseillé :

```text
YYYYMMDD_model_dataset_short-purpose_seed
```

Exemple :

```text
20260812_pointpillars_ball-v1_voxel5cm_seed42
```

Utiliser TensorBoard, MLflow ou Weights & Biases selon les contraintes de confidentialité. Dans tous les cas, la configuration résolue et les métriques finales doivent rester exportables sous forme de fichiers.

## 8. Risques principaux et réponses

| Risque | Symptôme | Réponse |
|---|---|---|
| Ballon trop peu échantillonné | Rappel s'effondre avec la distance | Mesurer les points, réduire la portée contractuelle, accumuler quelques sweeps ou fusionner une caméra |
| Fuite train/test | Excellente validation, échec sur nouveau terrain | Split par session et test challenge |
| Annotation incohérente | Loss instable, plafond de métriques | Guide, double annotation et contrôles automatiques |
| Prétraitement différent entre train et ROS | Bon offline, mauvais sur robot | Bibliothèque commune ou tests golden bit-à-bit/tolérance |
| File ROS qui s'accumule | Détections correctes mais anciennes | Queue 1, latest-only worker, mesure de l'âge |
| Dépendances CUDA fragiles | Installation/reproduction impossible | Conteneur, versions épinglées, smoke test CI GPU |
| Export ONNX incomplet | Opération non supportée ou résultat différent | Garder backend PyTorch, tests de parité, plugins seulement si nécessaires |
| Surapprentissage au terrain | Faux positifs ailleurs | Sessions variées, négatifs difficiles, active learning |
| Modèle trop lourd pour la cible | Faible fréquence, surchauffe | Réduire ROI/voxels, FP16, architecture plus légère, TensorRT après profilage |

## 9. Planning indicatif par jalons

### Jalon 0 — Une semaine : capteur compris

- topic, QoS, champs, TF et fréquence documentés ;
- 10 petits rosbags variés ;
- outil de visualisation et mesure des points sur ballon ;
- décision sur la portée réaliste.

### Jalon 1 — Deux à quatre semaines : dataset pilote

- format canonique ;
- guide d'annotation ;
- 500 à 1 500 trames annotées ;
- split par session ;
- baseline géométrique évaluée.

### Jalon 2 — Deux à six semaines : modèle ballon v1

- pipeline PointPillars reproductible ;
- courbes d'apprentissage et ablations `1/3 sweeps`, voxel fin/grossier ;
- 5 000 à 15 000 trames selon les résultats ;
- artefact `ball_v1.0.0` et model card.

### Jalon 3 — Deux à quatre semaines : nœud ROS v1

- backend PyTorch ;
- `Detection3DArray`, markers et diagnostics ;
- tests sur rosbag et robot ;
- mesure latence/fréquence ;
- documentation d'installation et lancement.

### Jalon 4 — Deux à six semaines : optimisation

- profilage ;
- export ONNX/TensorRT si pertinent ;
- tests de parité ;
- endurance de 30 à 60 minutes ;
- gestion des erreurs et watchdog.

### Jalon 5 — Quatre à huit semaines : ballon + G1

- nouvelles sessions et taxonomie v2 ;
- modèle multi-classe ;
- évaluation séparée ;
- intégration sans casser l'API ROS.

Ces durées sont des ordres de grandeur pour une personne et dépendent surtout du temps d'accès au robot, de l'annotation et des surprises liées au capteur.

## 10. Checklist de démarrage immédiat

- [x] Confirmer la distribution ROS 2 et le calculateur qui exécutera l'inférence.
- [x] Confirmer `/utlidar/cloud`, son type, ses champs, sa fréquence et son QoS.
- [ ] Enregistrer 10 sessions courtes avec ballon à distances connues.
- [x] Écrire le visualiseur et `measure_ball_returns.py`.
- [x] Décider du repère canonique et de la zone d'intérêt.
- [x] Implémenter la baseline géométrique.
- [x] Choisir l'outil et rédiger la convention d'annotation.
- [x] Annoter un pilote de 500 à 1 500 trames.
- [x] Créer le split par session et les tests de validation du dataset.
- [x] Faire sur-apprendre un mini-lot avec PointPillars.
- [ ] Mesurer une première courbe rappel-distance.
- [ ] Définir les critères d'acceptation ballon v1.
- [x] Créer le squelette du nœud ROS avec un backend factice.
- [x] Remplacer le backend factice par le modèle validé.
- [ ] Rejouer un rosbag complet et mesurer latence, drops et faux positifs.

## 11. Définition de « terminé » pour la première version

La version `1.0.0` du module ballon est livrable lorsque :

- le dataset et le modèle sont versionnés et reproductibles ;
- la documentation permet à un nouvel étudiant d'ajouter une session ;
- les performances sont publiées par distance et nombre de points ;
- le nœud se configure sans modifier le code ;
- les sorties sont des messages ROS 2 standards et visualisables dans RViz ;
- les erreurs de type, champ, modèle, device et TF sont explicites ;
- le nœud tient la durée et la fréquence requises sur le calculateur cible ;
- un jeu de rosbags de non-régression permet de vérifier une nouvelle version ;
- les limites connues — portée, occlusion, mouvements, terrains — sont écrites dans la model card.

Le premier livrable utile n'est donc pas seulement un fichier de poids. C'est un ensemble cohérent **données → configuration → modèle → métriques → manifeste → nœud ROS → tests**, que quelqu'un d'autre peut comprendre et reproduire.
