# Rapport de préannotation géométrique v1

**Date :** 3 août 2026
**Dataset source :** `ball_lidar_feasibility_v1`
**État :** préannotations non validées humainement

## Objectif

La baseline géométrique et son suivi temporel ont été utilisés pour proposer
des boîtes de ballon. Le but est d'accélérer la future annotation manuelle, pas
de produire automatiquement une vérité terrain.

## Résultats

| Mesure | Valeur |
|---|---:|
| Trames canoniques traitées | 578 |
| Boîtes proposées | 431 |
| Trames sans boîte | 147 |
| Boîtes faciles (au moins 10 retours) | 202 |
| Boîtes moyennes (3 à 9 retours) | 183 |
| Boîtes difficiles (moins de 3 retours) | 46 |
| Boîtes extrapolées par le suivi | 52 |

Toutes les boîtes et tous les fichiers portent explicitement
`review_status=unreviewed`. Les 144 trames de la session sans ballon ne
contiennent aucune boîte. Une absence de boîte dans une session positive ne
doit toutefois pas être considérée comme un négatif validé sans inspection.

## Validation automatique

Le validateur a contrôlé les 578 annotations par rapport aux échantillons
canoniques : unicité et existence du `sample_id`, `frame_id`, schéma, valeurs
finies, dimensions, classe, lacet nul du ballon, sommes SHA-256, nombre de
boîtes et recomptage des points inclus. Résultat : **0 erreur**.

Le rapport machine est conservé dans
`reports/preannotations_v1/validation.json`. La planche
`reports/preannotations_v1/qa_contact_sheet.png` présente des vues de dessus et
de côté pour cinq cas déterministes : 1,5 m facile, 3 m moyen, 5 m difficile,
5 m extrapolé par le suivi et scène négative.

## Reproduction

```bash
.venv/bin/python lidar_detection_training/tools/generate_preannotations.py \
  --config lidar_detection_training/configs/experiments/geometric_baseline_v1.yaml \
  --output-dir data/processed/ball_lidar_feasibility_v1/preannotations_v1

.venv/bin/python lidar_detection_training/tools/validate_preannotations.py \
  --dataset-root data/processed/ball_lidar_feasibility_v1 \
  --preannotations-root data/processed/ball_lidar_feasibility_v1/preannotations_v1 \
  --report reports/preannotations_v1/validation.json

.venv/bin/python lidar_detection_training/tools/plot_preannotation_qa.py \
  --dataset-root data/processed/ball_lidar_feasibility_v1 \
  --preannotations-root data/processed/ball_lidar_feasibility_v1/preannotations_v1 \
  --output reports/preannotations_v1/qa_contact_sheet.png
```

## Décision

La chaîne de préannotation est techniquement valide et reproductible. Le
prochain jalon est une inspection humaine de la planche, puis la définition de
la procédure de correction et de revue. Aucune métrique d'apprentissage ne doit
utiliser ces fichiers comme vérité terrain avant cette revue.

### Mise à jour après contrôle visuel

Les exemples mesurés à 1,5 m, 3 m et 5 m ont été jugés correctement placés.
L'exemple extrapolé par le suivi à 5 m a été rejeté. Une version v2 a donc été
générée en excluant systématiquement les 52 extrapolations : 379 boîtes
mesurées restent disponibles. À la demande du porteur du projet, cette revue
allégée est acceptée uniquement pour un entraînement pilote rapide ; elle ne
remplace pas le contrôle qualité du futur dataset diversifié.
