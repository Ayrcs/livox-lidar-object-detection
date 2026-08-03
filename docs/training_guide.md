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

L'intégration en direct a confirmé que le ballon peut être détecté, mais elle a
aussi révélé des confiances faibles sur la cible et des confiances élevées sur
certains artefacts. La campagne suivante doit donc privilégier la diversité et
les négatifs difficiles, plutôt qu'un nouvel entraînement sur les quatre mêmes
sessions.

## Dataset suivant pour un ballon robuste

Conserver des sessions entières indépendantes pour `train`, `validation` et
`test`, idéalement séparées aussi par lieu ou journée. Enregistrer au minimum :

- plusieurs distances et positions latérales dans toute la zone utile ;
- ballon immobile, roulant, partiellement masqué et momentanément sans retour ;
- robot immobile puis mobile ;
- béton, pelouse et autres sols visés par l'usage final ;
- scènes sans ballon dans chacun des environnements ;
- objets ayant produit une fausse détection, conservés sans boîte `ball` ;
- personnes, pieds, chaussures, sacs, cônes et objets ronds comme négatifs
  difficiles.

Une session négative ne doit pas servir uniquement à l'entraînement : le jeu de
validation et le test doivent eux aussi permettre de mesurer précision, faux
positifs par trame et calibration des scores. Photographier ou décrire les
artefacts problématiques dans les métadonnées afin de pouvoir analyser les
erreurs par famille après l'entraînement.

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

La sortie technique de classification de direction de `Anchor3DHead` reste
activée avec un poids de loss nul. MMDetection3D 1.4 en a besoin pour fournir un
tenseur que MMEngine peut agréger ; cette sortie n'influence pas les poids et le
lacet publié pour `ball` reste forcé à zéro.
