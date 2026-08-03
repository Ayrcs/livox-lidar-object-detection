# Rapport de faisabilité — Visibilité d'un ballon par le LiDAR

**Date de l'essai :** 30 juillet 2026
**Capteur :** Livox Mid-360 du Unitree G1
**Objet :** ballon de football taille 5, diamètre approximatif 0,22 m
**Environnement :** intérieur, sol de type béton

## 1. Objectif

Cet essai vise à déterminer si un ballon de football produit suffisamment de
retours LiDAR pour envisager sa détection 3D, et comment ce nombre de retours
évolue avec la distance. Il ne s'agit pas encore d'une évaluation d'un modèle
d'apprentissage.

## 2. Protocole

Le robot et le ballon sont restés immobiles pendant chaque acquisition. Le
ballon a été placé approximativement droit devant le robot à trois distances
mesurées depuis le LiDAR : 1,50 m, 3,00 m et 5,00 m. Une quatrième session a été
enregistrée à 5 m après retrait du ballon, sans déplacer le robot ni les autres
éléments de la scène.

Chaque session dure environ 14,4 secondes et contient 144 ou 145 nuages à
environ 10 Hz. Les données brutes sont des
`sensor_msgs/msg/PointCloud2` dans `livox_frame`. La correction d'orientation
validée sur le robot, un roll de 180 degrés, a été appliquée pendant l'analyse
pour obtenir X vers l'avant, Y vers la gauche et Z vers le haut.

Sessions utilisées :

| Condition | Identifiant de session | Nuages |
|---|---|---:|
| Ballon à 1,50 m | `20260730_indoor_ball_1p5m_front_static_run01` | 145 |
| Ballon à 3,00 m | `20260730_indoor_ball_3m_front_static_run01` | 145 |
| Ballon à 5,00 m | `20260730_indoor_ball_5m_front_static_run01` | 144 |
| Même scène sans ballon | `20260730_indoor_no_ball_5m_paired_static_run01` | 144 |

Les manifests détaillés et versionnables se trouvent dans
`data_manifests/sessions/`. Les rosbags bruts restent hors Git.

## 3. Méthode de mesure

Pour chaque session :

1. les messages PointCloud2 sont désérialisés avec le typestore ROS 2 Foxy ;
2. la rotation de 180 degrés autour de X est appliquée ;
3. le plan du sol local est estimé de manière robuste dans le couloir central ;
4. une zone de 0,24 m × 0,24 m est placée autour de la position observée du
   ballon ;
5. seuls les retours situés entre 2 cm et 24 cm au-dessus du sol sont comptés,
   afin d'exclure les points du béton.

La boîte a été positionnée après inspection des nuages agrégés. Les résultats
sont donc une mesure de faisabilité préliminaire, et non une annotation de
vérité terrain indépendante.

### Reproduction

L'analyse est définie par
`lidar_detection_training/configs/feasibility/ball_visibility_20260730.yaml` et
exécutée par `lidar_detection_training/tools/analyze_ball_visibility.py`.
Depuis l'environnement virtuel du projet :

```bash
.venv/bin/python lidar_detection_training/tools/analyze_ball_visibility.py \
  --config lidar_detection_training/configs/feasibility/ball_visibility_20260730.yaml \
  --bags-root remote-g1/lidar_data/raw \
  --output-dir reports/ball_visibility_20260730
```

Les résultats complets sont conservés dans
`reports/ball_visibility_20260730/metrics.json` et les comptages de chaque trame
dans `reports/ball_visibility_20260730/frame_counts.csv`.

## 4. Résultats

| Condition | Moyenne points/trame | Écart-type | Minimum | Médiane | Maximum | Trames à 0 point | Trames avec < 3 points | Trames avec < 10 points |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Ballon à 1,50 m | 35,77 | 4,76 | 25 | 35 | 53 | 0,0 % | 0,0 % | 0,0 % |
| Ballon à 3,00 m | 8,60 | 3,80 | 1 | 9 | 20 | 0,0 % | 13,8 % | 55,9 % |
| Ballon à 5,00 m | 4,06 | 1,63 | 0 | 4 | 7 | 3,5 % | 18,1 % | 100,0 % |
| Scène sans ballon à 5 m | 0,13 | 0,41 | 0 | 0 | 2 | 90,3 % | 100,0 % | 100,0 % |

L'intensité moyenne des retours sélectionnés sur le ballon est proche de 47 à
49 selon la distance. À ce stade, elle ne montre pas de séparation évidente
entre les trois distances et ne doit pas être utilisée seule pour reconnaître
le ballon.

## 5. Interprétation

- **À 1,50 m**, le ballon est nettement observable sur chaque trame. Plus de 25
  retours sont présents même dans la trame la moins dense de cet essai.
- **À 3,00 m**, le ballon reste observable, mais le nombre de retours devient
  irrégulier. Plus de la moitié des trames contiennent moins de 10 points.
- **À 5,00 m**, le ballon produit encore un signal distinct de la scène
  négative, mais seulement quatre points en moyenne. Une boîte 3D stable à
  partir d'une seule trame sera difficile ; le contexte spatial, le suivi ou
  une accumulation temporelle courte pourront devenir nécessaires.
- La session sans ballon contient au maximum deux points dans la même zone et
  confirme que la majorité des retours comptés à 5 m sont associés au ballon.

Le ballon avait été placé manuellement et légèrement décalé vers la gauche. Le
décalage latéral observé dans les nuages ne doit donc pas être interprété comme
une erreur de yaw du LiDAR.

## 6. Limites

- Un seul ballon, un seul lieu et un seul type de sol ont été testés.
- Le ballon et le robot étaient immobiles.
- Les boîtes de mesure ont été ajustées après inspection des données.
- Les trames consécutives d'une même session sont corrélées et ne représentent
  pas 145 scènes d'entraînement indépendantes.
- L'horloge du Mid-360 présente un retard stable d'environ 70,27 secondes par
  rapport au Jetson ; cela devra être résolu avant fusion avec odométrie/TF ou
  accumulation compensée.
- La pelouse, les occultations, le ballon roulant, le robot en mouvement et les
  objets perturbateurs n'ont pas encore été évalués.

## 7. Conclusion et décision

Le Mid-360 voit suffisamment le ballon pour poursuivre le projet. La plage de
1,5 à 3 m est clairement exploitable dans les conditions testées. La distance de
5 m reste possible mais constitue déjà un cas difficile sur une trame isolée.

La collecte exhaustive est suspendue à ce stade afin de construire d'abord la
chaîne reproductible d'extraction, d'annotation et de baseline géométrique. Les
prochaines acquisitions devront ensuite ajouter de la diversité plutôt que
répéter uniquement la même scène : négatifs difficiles, azimuts, occultations,
mouvement et, dans une phase ultérieure, pelouse.
