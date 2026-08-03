# Rapport — Sur-apprentissage PointPillars ballon v1

**Date :** 3 août 2026

## Objectif

Vérifier que le format des nuages, les coordonnées des boîtes, les ancres et le
réseau PointPillars permettent effectivement d'apprendre le ballon. Ce test
utilise volontairement les mêmes 80 trames pour l'entraînement et la mesure.
Il ne mesure donc pas la généralisation.

## Données et machine

- 64 trames positives et 16 trames négatives ;
- scènes statiques en intérieur sur béton ;
- RTX 3090 de 24 GiB documentée dans
  `docs/training_machine_trojalab02.md` ;
- commit exécuté : `d9668ac` ;
- 30 époques, seed `20260803`.

## Résultats

| Époque | Loss | Précision | Rappel | F1 | Erreur médiane du centre | Faux positifs/trame |
|---:|---:|---:|---:|---:|---:|---:|
| 5 | 0,8481 | 34,03 % | 61,25 % | 43,75 % | 7,40 cm | 1,1875 |
| 15 | 0,0330 | 76,19 % | 100 % | 86,49 % | 3,29 cm | 0,3125 |
| 20 | 0,0174 | 100 % | 100 % | 100 % | 1,18 cm | 0 |
| 30 | 0,0035 | 100 % | 100 % | 100 % | 0,93 cm | 0 |

Le pic de mémoire GPU journalisé est d'environ 445 MiB. Le réseau atteint le
critère de mémorisation dès l'époque 20. La chaîne données → PointPillars → loss
→ prédictions → métriques est donc fonctionnelle.

## Décision

Le garde-fou est validé. L'entraînement pilote peut maintenant utiliser les
410 trames prévues, avec la session 5 m tenue à l'écart. Le checkpoint optimal
sera désormais choisi sur le F1 et non sur le seul rappel, afin de pénaliser les
fausses détections multiples.
