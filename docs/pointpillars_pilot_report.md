# Rapport — PointPillars ballon pilote v1

**Date :** 3 août 2026

## Protocole

PointPillars apprend sur 410 trames : les sessions ballon à 1,5 m et 3 m ainsi
que la session négative sans ballon. La session ballon à 5 m, soit 113 trames
annotées mesurées, est tenue à l'écart et utilisée uniquement pour la
validation. Aucune session n'est partagée entre les deux ensembles.

L'entraînement comporte 40 époques sur la RTX 3090 documentée. Le checkpoint
est choisi selon le meilleur F1 à une tolérance de 30 cm sur le centre.

## Meilleur résultat

Le meilleur checkpoint est obtenu dès l'époque 5 :

| Mesure sur la session 5 m | Résultat |
|---|---:|
| Précision | 100 % |
| Rappel | 96,46 % |
| F1 | 98,20 % |
| Erreur médiane du centre | 8,22 cm |
| Faux positifs par trame | 0 |

Cela correspond approximativement à 109 détections correctes et 4 ballons
manqués sur 113 trames, sans boîte supplémentaire. Les époques suivantes
réduisent encore la loss d'entraînement mais dégradent le F1 de validation :
elles commencent donc à suradapter le modèle aux sessions d'apprentissage.

## Traçabilité

- commit d'entraînement : `069b88366e1a587e12a297c2c53444e65379fda6` ;
- checkpoint : `best_ball_f1_center_0p30m_epoch_5.pth` ;
- SHA-256 :
  `33f2bc0f652f5a473b8c7d690bb2a578d7dc65231c3199a22f9373668e2a5944` ;
- métriques machine : `reports/pointpillars_ball_pilot_v1/metrics.json`.

## Interprétation et limite

Le réseau apprend correctement le ballon et transfère de 1,5–3 m vers la
session 5 m. Ce résultat autorise le passage à l'intégration d'inférence.
Cependant, le jeu de validation vient du même lieu et du même jour, ne contient
pas de scène entièrement négative et ne couvre ni mouvement, ni pelouse, ni
occultation. Le modèle est donc versionné comme **pilote v0.1.0**, pas comme
modèle de production.
