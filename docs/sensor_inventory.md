# Inventaire du capteur

> Statut : mesures en cours sur le Unitree G1 réel. Ne pas remplacer une mesure
> par une valeur provenant uniquement de la documentation constructeur.

## Plateforme

| Élément | Valeur mesurée |
|---|---|
| Date / opérateur | 2026-07-30 / opérateur du projet |
| Distribution ROS 2 | Foxy, sélectionnée par défaut dans `.bashrc` (fin de support amont) |
| Système | Ubuntu 20.04.6 LTS (Focal), Linux `5.10.104-tegra`, glibc 2.29 |
| Architecture | `aarch64` |
| Calculateur d'inférence | NVIDIA Orin NX Developer Kit |
| Jetson Linux / L4T | R35.3.1, GCID 32827747, board `t186ref` |
| Middleware RMW actif | `rmw_cyclonedds_cpp` 0.7.11 |
| SDK Unitree (version/commit) | TODO |
| Publisher du topic canonique | Application DDS native Unitree, exposée par ROS comme `_CREATED_BY_BARE_DDS_APP_` ; binaire/version à identifier |
| Pilote Livox ROS séparé | `livox_ros_driver2` 1.0.0 sous `/home/unitree/livox_ws`; publie `/livox/lidar` en `livox_ros_driver2/msg/CustomMsg` lorsqu'il est lancé |

## Topic PointCloud2

| Propriété | Valeur mesurée |
|---|---|
| Nom | `/utlidar/cloud_livox_mid360` (1 publisher observé) |
| Type | `sensor_msgs/msg/PointCloud2` |
| Frame ID | `livox_frame` |
| Fréquence mesurée | 9,980 Hz sur 132 intervalles (mesure de 15 s) |
| Période min/max/écart-type | 0,098 s / 0,103 s / 0,00090 s sur la fenêtre finale |
| Bande passante | 4,42 MB/s sur une fenêtre de 100 messages |
| Taille sérialisée observée | moyenne/min/max affichées à 0,44 MB ; données brutes : 441 408 octets/trame |
| QoS publisher | Reliability `RELIABLE`, durability `VOLATILE`, liveliness `AUTOMATIC`, deadline/lifespan/lease non contraints |
| Abonnés observés | 3 abonnés `BEST_EFFORT` et `VOLATILE` ; compatibles avec le publisher fiable |
| Organisation observée | `height=1` (nuage non organisé), `is_dense=true`, little-endian |
| Échantillon initial | 20 064 points, `point_step=22`, `row_step=441408` octets |
| Points/message min/moy/max | 19 957 / 20 043,96 / 20 256 sur 100 trames |
| Écart-type des points/message | 44,75 points (environ 0,22 % de la moyenne) |
| Champs (`name`, type, offset) | `x`: FLOAT32@0, `y`: FLOAT32@4, `z`: FLOAT32@8, `intensity`: FLOAT32@12, `ring`: UINT16@16, `time`: FLOAT32@18 ; tous `count=1` |
| Taille d'un point | 22 octets, cohérente avec 5 × FLOAT32 + 1 × UINT16 |
| Unités et axes | TODO |
| Source d'horodatage | À identifier ; le header n'est pas synchronisé avec l'horloge du Jetson |
| Décalage temporel observé | 70,367 s de retard moyen, min 70,364 s, max 70,369 s, écart-type 0,00100 s sur 59 mesures `ros2 topic delay` |

Le sens, l'unité et la référence du champ Livox `time` restent à confirmer dans
la configuration ou le code exact du pilote avant toute accumulation de
balayages.

Le décalage d'environ 70 secondes interdit pour l'instant d'associer directement
les nuages à TF, IMU ou odométrie. Identifier d'abord la source du timestamp et
synchroniser les horloges ; ne pas masquer ce défaut en remplaçant silencieusement
le header par l'heure de réception dans le futur nœud de production.

Le Jetson n'est pas la source du défaut : `timedatectl` confirme horloge système
synchronisée, NTP `systemd-timesyncd` actif, RTC en UTC et fuseau
`Europe/Prague`. Chrony n'est pas installé.

L'IMU Mid-360 présente elle aussi un retard stable : moyenne 70,268 s,
min/max 70,268/70,269 s et écart-type 0,00018 s sur 1 199 mesures. Le décalage
est donc commun à l'horloge du capteur. Le nuage a environ 99 ms de retard
supplémentaire par rapport à l'IMU, soit presque exactement sa période à 10 Hz ;
le header paraît dater le début de la fenêtre de balayage publiée.

Les services `ptp4l` et `phc2sys` sont inactifs et aucun processus correspondant
n'est lancé. Ce point ne bloque pas le traitement d'une trame isolée ; il est
reporté comme prérequis avant fusion TF/odométrie ou accumulation multi-sweeps.

## Validation rosbag initiale

Le smoke test `smoke_20260730_172354` a été enregistré sous
`/home/unitree/aymeric-lidar-object-detection/lidar_data/raw` : durée 14,400 s,
taille 61,5 MiB, 143 nuages (environ 9,93 Hz) et 2 881 messages IMU (environ
200,07 Hz), stockage SQLite3 et sérialisation CDR. Cette validation prouve
l'enregistrement, pas encore la qualité fonctionnelle ni la synchronisation.

Une instance séparée de `livox_ros_driver2_node`, lancée avec le nom
`livox_lidar_publisher` et plusieurs fichiers `/tmp/launch_params_*`, publie le
topic personnalisé `/livox/lidar`. Elle ne publie pas le topic canonique
`/utlidar/cloud_livox_mid360`, dont le publisher est une application DDS native.
Aucun service systemd LiDAR/Livox actif n'a été trouvé lors de la mesure.

Paramètres actifs relevés :

| Paramètre | Valeur |
|---|---:|
| `xfer_format` | 1 |
| `multi_topic` | 0 |
| `data_src` | 0 |
| `publish_freq` | 10.0 |
| `output_data_type` | 0 |
| `frame_id` | `livox_frame` |
| `lvx_file_path` | `/home/livox/livox_test.lvx` |
| `user_config_path` | `/home/unitree/livox_ws/install/livox_ros_driver2/share/livox_ros_driver2/config/MID360_config.json` |
| `cmdline_input_bd_code` | `livox0000000001` |

Avec `xfer_format=1`, `/livox/lidar` est un
`livox_ros_driver2/msg/CustomMsg`. Il contient un `timebase` de message et, pour
chaque point, `offset_time`, `x/y/z`, `reflectivity`, `tag` et `line`. Il ne doit
pas être confondu avec le `PointCloud2` Unitree, et n'est pas directement une
entrée PointCloud2 standard pour les visualiseurs.

Le bloc `extrinsic_parameter` actif vaut zéro pour `roll`, `pitch`, `yaw`, `x`,
`y` et `z`. Observation physique de l'opérateur : le Mid-360 est monté tête en
bas. Une rotation de 180 degrés est donc nécessaire pour obtenir Z vers le haut,
mais l'axe de rotation doit être déterminé en vérifiant les directions X/Y ; un
demi-tour en pitch et un demi-tour en roll n'ont pas le même effet sur
l'avant/arrière et la gauche/droite.

Observation dans Foxglove avant correction : le sol apparaît au-dessus et le
plafond en dessous ; +X pointe vers l'avant du robot et +Y a été identifié vers
la gauche. Le maintien de +X vers l'avant favorise une correction de 180 degrés
en roll. La direction Y doit être vérifiée après cette rotation, car une rotation
rigide en roll inverse nécessairement Y et Z.

Validation sur le robot : une transformation statique temporaire de
`livox_frame` vers le repère parent `lidar_corrected`, avec yaw=0, pitch=0 et
roll=π radians, remet correctement le nuage à l'endroit tout en conservant +X
vers l'avant. Après correction, +Y pointe vers la gauche et +Z vers le haut : le
repère `lidar_corrected` respecte donc la convention ROS X avant, Y gauche, Z
haut. Cette correction doit être publiée par la future configuration ROS ; ne
pas modifier le `MID360_config.json` du pilote séparé, qui n'est pas le publisher
du topic Unitree canonique.

## IMU Mid-360

Le topic `/utlidar/imu_livox_mid360` publie `sensor_msgs/msg/Imu`. Sur le message
inspecté, `frame_id` est vide, le quaternion d'orientation vaut `(0,0,0,0)` et
toutes les covariances valent zéro. L'accélération Z au repos est proche de
`-1`, ce qui suggère une valeur possiblement exprimée en g plutôt qu'en m/s² ;
cette hypothèse doit être vérifiée. Ne pas utiliser ce flux pour la compensation
de mouvement avant confirmation du repère, des unités, des covariances et de la
synchronisation.

## TF, odométrie et synchronisation

Documenter la chaîne entre le repère LiDAR et `base_link`, la disponibilité de
`/tf`, `/tf_static`, l'odométrie et l'IMU, puis mesurer le décalage temporel.

Première mesure : les topics `/tf` et `/tf_static` ne sont pas publiés. Un
rapport `view_frames.py` écouté pendant 5 secondes retourne une graphe vide
(`No tf data received`). La frame `base_link` est donc absente. Le repère
canonique initial est `livox_frame` et le nœud devra le conserver tant qu'une
transformation mesurée et réellement publiée n'aura pas été validée.

Foxglove reçoit et affiche directement le `PointCloud2` Unitree via Rosbridge ;
aucune conversion de format ni transformation TF n'est nécessaire. Il faut
activer explicitement `/utlidar/cloud_livox_mid360` dans les paramètres du
panneau 3D et sélectionner directement `livox_frame` comme repère d'affichage.

## Commandes utilisées

```bash
ros2 topic list -t
ros2 topic type /utlidar/cloud
ros2 topic info -v /utlidar/cloud
ros2 topic echo /utlidar/cloud --once --no-arr
ros2 topic hz /utlidar/cloud
ros2 topic bw /utlidar/cloud
ros2 interface show sensor_msgs/msg/PointCloud2
ros2 run tf2_tools view_frames
```

Joindre les sorties datées dans le stockage de la session, puis référencer leur
URI et SHA-256 ici. Les secrets et identifiants d'accès ne doivent jamais être
enregistrés.
