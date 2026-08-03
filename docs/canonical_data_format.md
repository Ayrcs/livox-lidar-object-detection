# Format canonique des nuages LiDAR

## Rôle pratique

Le format canonique sépare les données du rosbag et de ROS. L'entraînement, la
visualisation et les contrôles qualité peuvent ainsi lire les mêmes fichiers sur
Linux, macOS ou une station NVIDIA sans dépendre de `rclpy`.

Une extraction produit :

```text
dataset_root/
├── dataset_manifest.json
├── points/
│   └── <sample_id>.npy
└── metadata/
    └── <sample_id>.json
```

## Points

Chaque fichier `.npy` contient un tableau NumPy contigu `N × 6`, little-endian,
en `float32`. Les colonnes sont toujours :

```text
x, y, z, intensity, ring, time
```

La valeur entière `ring` est conservée exactement dans un `float32` pour garder
un tableau homogène. La correction vérifiée du montage tête en bas est déjà
appliquée : `(x, y, z) → (x, -y, -z)`. Les coordonnées sont donc exprimées dans
`lidar_corrected`, avec X avant, Y gauche et Z haut.

## Métadonnées d'un échantillon

Le JSON associé conserve au minimum :

- `sample_id`, `session_id` et le nombre de points ;
- timestamp du header et timestamp d'écriture du rosbag en nanosecondes ;
- repère source et repère canonique ;
- rosbag, topic et index exact du message source ;
- transformation appliquée ;
- champs et type du tableau.

Le manifeste global contient les SHA-256 des rosbags sources et de chaque paire
NPY/JSON. Les clés JSON et les échantillons sont triés. Un même rosbag, une même
configuration et la même version du code produisent donc les mêmes octets et les
mêmes sommes SHA-256.

## Commande d'extraction

```bash
.venv/bin/python lidar_detection_training/tools/extract_canonical_dataset.py \
  --config lidar_detection_training/configs/data/canonical_v1.yaml \
  --bags-root remote-g1/lidar_data/raw \
  --output-dir data/processed/ball_lidar_feasibility_v1
```

Les données extraites restent hors Git. Le résumé versionnable de cette version
est `data_manifests/datasets/ball_lidar_feasibility_v1.yaml`.

## État actuel

`ball_lidar_feasibility_v1` contient 578 trames extraites et non annotées. Son
manifeste canonique a pour SHA-256 :

```text
5c7a98d69a91b1499edf8f452168b87a7d49e61bfda6497015ff54d5a89ad6ad
```

Une double extraction réduite a produit des manifests identiques et le premier
échantillon complet a été comparé bit à bit au message rosbag désérialisé.
