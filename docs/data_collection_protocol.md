# Protocole d'acquisition

Une session est courte, homogène et possède un identifiant
`YYYYMMDD_site_scenario_runNN`. Avant l'enregistrement, noter dans un fichier de
métadonnées : surface, intérieur/extérieur, météo, mouvements du robot et du
ballon, distances mesurées, azimuts, occultations, perturbateurs et versions
logicielles.

Copier `docs/session_metadata_template.yaml` dans le dossier du rosbag sous le
nom `session.yaml`, compléter les champs `REPLACE_ME`, puis renseigner après la
capture la durée et les nombres de messages donnés par `ros2 bag info`.

Enregistrer le nuage, TF et l'odométrie (plus IMU/état robot si la compensation
de mouvement l'exige) :

```bash
ros2 bag record /utlidar/cloud /tf /tf_static /odom \
  -o data/raw/session_YYYYMMDD_site_scenario
```

Pour le pilote de faisabilité, produire 10 à 20 sessions indépendantes :

- distances 0,5–2 m, 2–4 m, 4–6 m, 6–8 m et hors portée supposée ;
- ballon immobile, roulant, partiellement masqué et absent ;
- robot immobile puis mobile ;
- au moins deux surfaces et des négatifs difficiles (jambes, chaussures,
  cônes, sacs et objets ronds).

Après chaque session : vérifier la durée et les topics avec `ros2 bag info`,
rejouer un extrait, calculer SHA-256, sauvegarder séparément les données brutes
et mettre à jour le manifeste. Ne jamais modifier un rosbag brut.

Les manifestes descriptifs versionnables sont conservés sous
`data_manifests/sessions/`. Une copie nommée `session.yaml` accompagne également
le rosbag dans le stockage brut et est couverte par `SHA256SUMS`.
