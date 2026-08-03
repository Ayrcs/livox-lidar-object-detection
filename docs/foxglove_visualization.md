# Visualiser les détections dans Foxglove

## Résultat attendu

La vue 3D affiche simultanément :

- le nuage `/utlidar/cloud_livox_mid360` ;
- une boîte filaire rouge de 22 cm autour de chaque ballon détecté ;
- une étiquette indiquant la classe, le score et la distance horizontale ;
- les coordonnées numériques complètes dans un panneau Raw Messages.

## Topics

```text
/utlidar/cloud_livox_mid360  sensor_msgs/msg/PointCloud2
/lidar/detection_markers     visualization_msgs/msg/MarkerArray
/lidar/detections_json       std_msgs/msg/String
/diagnostics                 diagnostic_msgs/msg/DiagnosticArray
```

Les marqueurs sont reconvertis dans le `frame_id` original du nuage. Ils se
superposent donc sans publier de TF artificiel. Le JSON conserve en parallèle
les coordonnées corrigées utiles au contrôle : `X avant, Y gauche, Z haut`.

## Configuration de la vue 3D

1. Démarrer `rosbridge_websocket` et connecter Foxglove comme pour le nuage
   LiDAR actuel.
2. Ouvrir ou conserver un panneau **3D**.
3. Dans **Topics**, activer `/utlidar/cloud_livox_mid360`.
4. Activer `/lidar/detection_markers` dans le même panneau.
5. Conserver `livox_frame` comme repère d'affichage si Foxglove le sélectionne
   automatiquement.

Une détection crée une boîte rouge et une étiquette du type :

```text
ball 0.20 | 4.97 m
```

## Valeurs numériques

Ajouter un panneau **Raw Messages**, puis choisir
`/lidar/detections_json`. Le champ `data` contient notamment la classe, le
score, `x`, `y`, `z`, `processing_ms`, `received_frames` et `dropped_frames`.

`processing_ms` est mesuré sur le G1. `dropped_frames` compte les nuages
remplacés par une trame plus récente pendant que le GPU travaille.

## Si aucune boîte n'apparaît

Vérifier dans cet ordre :

```bash
ros2 topic hz /lidar/detections_json
ros2 topic echo /lidar/detections_json
ros2 topic info /lidar/detection_markers
ros2 topic echo /diagnostics
```

- Si le JSON contient `"detections":[]`, le nœud fonctionne mais aucune
  prédiction ne dépasse le seuil.
- Si le JSON contient une détection mais aucun marqueur, vérifier que
  `/lidar/detection_markers` est activé dans les paramètres du panneau 3D.
- Si aucun message JSON n'arrive, consulter le terminal du conteneur et
  `/diagnostics`.
