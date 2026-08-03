# Rapport — Baseline géométrique ballon v1

**Expérience :** `geometric_baseline_v1`
**Dataset :** `ball_lidar_feasibility_v1`
**Statut :** baseline pilote, ajustée et évaluée sur les mêmes quatre sessions

## Rôle pratique

Cette baseline démontre qu'un détecteur sans apprentissage peut proposer une
position de ballon à partir du nuage LiDAR. Elle servira de pré-annotation, de
référence minimale à dépasser par le réseau et, après validation plus large, de
fallback lorsque le modèle n'est pas disponible.

Elle ne constitue pas encore une mesure de généralisation : les paramètres ont
été choisis à partir des mêmes sessions statiques utilisées pour cette première
évaluation.

## Pipeline

Pour chaque nuage canonique :

1. limitation au couloir frontal mesuré : X de 1,2 à 6,0 m et `|Y| ≤ 0,8 m` ;
2. estimation robuste du plan du sol ;
3. conservation des points situés de 2,5 à 35 cm au-dessus du sol ;
4. clustering euclidien par table de hachage spatiale ;
5. rayon adapté à la distance : 8 cm, 10 cm puis 15 cm ;
6. filtrage des dimensions du cluster ;
7. fusion des fragments proches ;
8. suivi mono-cible alpha-bêta, confirmé après deux observations et autorisant
   deux balayages manquants.

Les paramètres complets sont versionnés dans
`lidar_detection_training/configs/experiments/geometric_baseline_v1.yaml`.

## Résultats

Une prédiction est associée au ballon lorsque son erreur XY est inférieure ou
égale à 30 cm.

| Session | Rappel candidat/trame | Rappel après suivi | Faux suivis/trame | Erreur XY médiane | Erreur XY p95 |
|---|---:|---:|---:|---:|---:|
| Ballon à 1,5 m | 100,0 % | 99,3 % | 0 | 4,3 cm | 5,4 cm |
| Ballon à 3 m | 84,8 % | 99,3 % | 0 | 3,1 cm | 4,6 cm |
| Ballon à 5 m | 79,2 % | 99,3 % | 0 | 2,7 cm | 4,0 cm |
| Scène négative appariée | sans objet | sans sortie suivie | 0 | — | — |

Le rappel suivi de 99,3 % correspond à toutes les trames sauf la première : la
piste exige deux observations avant confirmation. Les séquences étant statiques,
ce bon résultat mesure surtout la capacité du suivi à combler les balayages peu
denses ; il ne prédit pas encore son comportement avec un ballon roulant.

Sur le Mac de développement, le détecteur seul prend environ 1,5 à 2,8 ms en
moyenne et moins de 3,2 ms au p95 selon la session. Cette mesure exclut lecture
du rosbag, désérialisation, publication ROS et transfert vers un éventuel GPU ;
elle ne remplace donc pas le profilage sur le Jetson.

## Limites

- Un seul lieu, un seul ballon et un sol type béton.
- Robot et ballon immobiles.
- Couloir frontal étroit, pas de couverture 360° validée.
- Vérité terrain issue des positions mesurées puis ajustées visuellement.
- Session négative de seulement 14,3 secondes, insuffisante pour annoncer un
  taux de faux positifs par minute robuste.
- Aucun sac, pied, cône, objet rond, mouvement ou occlusion difficile.
- Le suivi ne gère actuellement qu'une seule piste.

## Reproduction

```bash
.venv/bin/python lidar_detection_training/tools/evaluate_geometric_baseline.py \
  --config lidar_detection_training/configs/experiments/geometric_baseline_v1.yaml \
  --output-dir reports/geometric_baseline_v1
```

Les métriques structurées sont dans `reports/geometric_baseline_v1/metrics.json`
et les sorties par trame dans `reports/geometric_baseline_v1/predictions.csv`.

## Décision

La baseline est suffisamment utile pour devenir un outil de pré-annotation du
dataset pilote. La prochaine étape n'est pas d'optimiser davantage ces quatre
séquences, mais de définir le format d'annotation, générer des pré-annotations,
les contrôler visuellement puis évaluer sur de nouvelles situations.
