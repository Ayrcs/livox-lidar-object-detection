# Guide d'annotation 3D

## Convention

- Classes exactes : `ball`, puis `unitree_g1` dans la taxonomie v2.
- Coordonnées en mètres, dans le `frame_id` de l'échantillon canonique.
- Ordre des boîtes : centre `x,y,z`, dimensions `length,width,height`, puis
  `yaw` autour de +Z.
- `ball` utilise une orientation nulle et, par défaut, des dimensions physiques
  de `0.22 × 0.22 × 0.22 m`.
- `unitree_g1` est serré autour des retours associés ; son axe avant définit le
  lacet. Les poses debout, accroupie et au sol ne partagent pas une taille fixe.
- Une cible connue sans retour exploitable n'a pas de boîte : l'indiquer dans
  les métadonnées comme `no_return`, sans inventer des points.
- Une boîte avec moins de 3 points est `difficulty=hard` et doit être relue.

Chaque annotation contient `class_name`, `center_xyz`, `size_lwh`, `yaw`, ainsi
que `occluded`, `truncated`, `moving`, `num_points` et `difficulty`.

## Format JSON version 1

Un fichier porte le même `sample_id` que le nuage canonique. Exemple abrégé :

```json
{
  "schema_version": 1,
  "sample_id": "session_000042",
  "frame_id": "lidar_corrected",
  "review_status": "reviewed",
  "boxes": [{
    "annotation_id": "session_000042_ball_0",
    "class_name": "ball",
    "center_xyz": [3.0, 0.2, -1.08],
    "size_lwh": [0.22, 0.22, 0.22],
    "yaw": 0.0,
    "review_status": "reviewed",
    "attributes": {
      "occluded": false,
      "truncated": false,
      "moving": false,
      "num_points": 8,
      "num_points_in_box": 12,
      "difficulty": "medium"
    }
  }]
}
```

`num_points` compte les retours plausibles de la cible au-dessus du sol ;
`num_points_in_box` compte tous les retours géométriquement inclus dans la
boîte, sol compris. Difficulté : `hard` pour moins de 3 retours cibles,
`medium` de 3 à 9, `easy` à partir de 10.

## Préannotations et validation humaine

La baseline géométrique peut créer des fichiers `review_status=unreviewed`.
Ils ne constituent jamais une vérité terrain. L'annotateur doit afficher le
nuage, déplacer ou supprimer chaque boîte incorrecte, ajouter toute cible
manquée, renseigner les attributs inconnus puis passer la boîte et l'échantillon
à `reviewed`. Une boîte extrapolée par le suivi
(`predicted_by_tracker=true`) exige une attention particulière.

Une trame sans boîte peut signifier soit une vraie scène négative, soit une
cible manquée. Elle doit donc également être revue avant de devenir une
annotation négative validée.

## Contrôle qualité

Valider automatiquement nombres finis, dimensions positives, classes de la
taxonomie et présence de points. Visualiser en 3D et en vue de dessus. Faire une
double annotation indépendante de 5 à 10 % des trames et publier l'accord sur
le centre, les dimensions et l'IoU. Le split est effectué par sessions entières,
jamais par trames voisines.
