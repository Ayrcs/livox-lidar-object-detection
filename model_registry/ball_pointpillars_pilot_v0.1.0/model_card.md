# Ball PointPillars Pilot v0.1.0

Premier checkpoint PointPillars fonctionnel pour détecter un ballon de football
taille 5 avec le Mid-360 du Unitree G1. Il est destiné à valider l'intégration
d'inférence, pas à une utilisation autonome en production.

## Usage prévu

- un seul balayage PointCloud2 ;
- convention X avant, Y gauche, Z haut ;
- couloir frontal X 0,4–6 m et Y ±1 m ;
- sortie `ball` avec boîte 22 cm et lacet nul.

## Performances observées

Sur 113 trames statiques à 5 m tenues hors entraînement : précision 100 %,
rappel 96,46 %, F1 98,20 % et erreur médiane du centre 8,22 cm.

## Ne pas conclure

Ces métriques ne couvrent pas un autre lieu, la pelouse, un ballon roulant, un
robot mobile, les occultations ou des négatifs difficiles. Tout nouvel objet
doit recevoir son propre dataset, ses tailles d'ancres, ses critères et sa carte
de modèle.
