# Machine d'entraînement de référence — trojalab02

## Relevé du 3 août 2026

| Élément | Valeur observée |
|---|---|
| Système | Ubuntu 22.04.5 LTS (Jammy) |
| Noyau | Linux 6.8.0-136-generic |
| Architecture | x86_64 |
| GPU | NVIDIA GeForce RTX 3090 |
| VRAM | 24 576 MiB |
| Pilote NVIDIA | 580.173.02 |
| Version CUDA maximale annoncée par le pilote | 13.0 |
| Docker | 29.6.2, build `dfc4efb` |
| Stockage disponible | 606 GiB sur la partition de travail |

Au moment du relevé, environ 840 MiB de VRAM étaient utilisés par l'affichage
et les services graphiques. Cette occupation est faible devant les 24 GiB
disponibles, mais `nvidia-smi` doit être enregistré pour chaque expérience afin
de repérer un entraînement concurrent.

La valeur « CUDA 13.0 » affichée par `nvidia-smi` décrit la version maximale
prise en charge par le pilote, et non nécessairement le toolkit installé sur
l'hôte. L'environnement du projet utilise son propre runtime CUDA 11.7 dans
Docker. Le pilote récent est rétrocompatible avec ce runtime.

## État de Docker

Le moteur Docker est installé, mais le compte d'entraînement n'a pas accès au
socket `/var/run/docker.sock`. Les commandes utilisent donc `sudo docker`.

Le runtime `nvidia`, `nvidia-container-toolkit 1.19.1-1` et
`libnvidia-container1 1.19.1-1` sont installés. Le passage du GPU a été vérifié
avec l'image `nvidia/cuda:11.7.1-base-ubuntu22.04`, digest
`sha256:3abc181c23dba195104750afcc27d9459760d9f72c3d79582306491098133a78`.
Dans ce conteneur, `nvidia-smi` détecte bien la RTX 3090 et ses 24 576 MiB.

Ne pas ajouter automatiquement un utilisateur au groupe `docker` sans accord
de l'administrateur : ce groupe donne, en pratique, des privilèges équivalents
à ceux de `root`. L'alternative est d'utiliser `sudo docker` pour les commandes
d'entraînement.

## Preuves à conserver pour chaque entraînement

Le script `run_pointpillars_training.sh` enregistre automatiquement dans
`runs/<experience>/` :

- la sortie de `nvidia-smi` ;
- la version de Python ;
- la liste exacte des paquets Python ;
- le commit Git ;
- les journaux et checkpoints MMDetection3D.

Il faut ajouter au rapport final la durée, le pic de VRAM, le meilleur epoch et
les métriques. Cela permet de comparer une RTX 3090 à une autre machine sans
supposer que les performances seront identiques.

## Réutilisation pour un autre objet

La machine n'est pas spécifique au ballon. Pour entraîner un autre objet, il
faut créer un nouveau dataset et une nouvelle expérience, puis adapter :

1. la taxonomie des classes ;
2. la zone spatiale utile ;
3. la taille des voxels selon la taille de l'objet ;
4. les dimensions et plages des ancres ;
5. les augmentations physiquement possibles ;
6. les critères d'association et métriques ;
7. les splits par sessions complètes.

Les données, configurations, métriques et poids du nouvel objet doivent recevoir
leurs propres identifiants de version. Il ne faut pas écraser l'expérience du
ballon.
