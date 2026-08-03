# Guide d'entraînement — PointPillars ballon

## État actuel

Le premier entraînement est volontairement un **pilote** sur les quatre
sessions statiques en intérieur. Il vérifie le pipeline complet, mais ne prouve
pas une généralisation à un ballon roulant, à la pelouse ou à un autre lieu.

Les boîtes extrapolées par le suivi ont été exclues. Le dataset contient :

| Split | Positives | Négatives | Rôle |
|---|---:|---:|---|
| `overfit` | 64 | 16 | Vérifier que le réseau sait mémoriser un mini-lot |
| `train` | 266 | 144 | Premier entraînement pilote |
| `val_distance_holdout` | 113 | 0 | Mesurer le transfert vers 5 m |

Les sessions 1,5 m et 3 m ainsi que la session négative sont dans
l'entraînement. La session 5 m complète est tenue à l'écart. Aucune trame
adjacente d'une même session n'est répartie entre entraînement et validation.
Avec seulement quatre sessions, il n'existe pas encore de test indépendant.

## Environnement de référence

- Linux x86_64 avec GPU NVIDIA ;
- pilote compatible CUDA 11.7 ;
- PyTorch 2.0.1 + CUDA 11.7 ;
- MMEngine 0.10.7 ;
- MMCV 2.1.0 ;
- MMDetection 3.2.0 ;
- MMDetection3D 1.4.0.

Ces versions respectent les contraintes publiées par MMDetection3D 1.4.0.
Le Mac sert à préparer les données, pas à l'entraînement officiel, car les
opérations CUDA de MMDetection3D n'y sont pas disponibles.

Le premier hôte retenu est documenté dans
`docs/training_machine_trojalab02.md`. Les caractéristiques machine ne doivent
jamais rester uniquement dans un journal de terminal : chaque nouvel hôte doit
recevoir un manifeste sous `data_manifests/environments/`.

## Ordre d'exécution

Depuis la racine du dépôt sur la machine NVIDIA :

```bash
docker build -f docker/training.Dockerfile \
  -t lidar-pointpillars-training:1.0 .

docker run --rm --gpus all --shm-size=8g \
  -v "$PWD:/workspace" -w /workspace \
  lidar-pointpillars-training:1.0 \
  bash lidar_detection_training/tools/run_pointpillars_training.sh overfit
```

Le sur-apprentissage doit d'abord montrer une chute nette des pertes et un
rappel élevé sur le mini-lot. Après ce garde-fou :

```bash
docker run --rm --gpus all --shm-size=8g \
  -v "$PWD:/workspace" -w /workspace \
  lidar-pointpillars-training:1.0 \
  bash lidar_detection_training/tools/run_pointpillars_training.sh pilot
```

Les sorties vont dans `runs/`, avec versions de l'environnement, matériel,
commit, logs et checkpoints. Ne pas promouvoir ce checkpoint en modèle v1 de
production avant des acquisitions diversifiées.

La seed est fixée à `20260803`. Le mode CUDA strictement déterministe est en
revanche désactivé : avec PyTorch 2.0.1, il provoque un bogue connu d'affectation
indexée dans l'assigner d'ancres MMDetection3D. Les expériences restent
reproductibles par leurs données, split, configuration, seed, versions et
traces, mais deux entraînements GPU ne sont pas garantis identiques bit à bit.
Cette limite concerne l'entraînement ; le déterminisme de l'inférence est testé
séparément à tolérance numérique définie.

## Configuration spécifique au ballon

La zone pilote couvre X de 0,4 à 6 m et Y de -1 à 1 m. Les piliers mesurent
5 cm en X/Y afin de préserver un objet de 22 cm. L'ancre est une boîte fixe de
22 cm et le lacet n'est pas appris, car l'orientation d'une sphère n'a pas de
sens. La métrique principale associe prédiction et ballon lorsque l'erreur du
centre est inférieure à 30 cm.
