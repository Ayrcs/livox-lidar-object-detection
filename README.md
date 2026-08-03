**English** | [Français](README.fr.md)

# LiDAR 3D Object Detection for the Unitree G1

An end-to-end, reproducible pipeline for training LiDAR-based 3D object
detectors and deploying them on a Unitree G1 with ROS 2 and NVIDIA Jetson.

The project currently targets a size-5 football observed by the robot's Livox
Mid-360. It covers the complete lifecycle:

1. record ROS 2 point clouds and preserve their acquisition metadata;
2. extract a deterministic, ROS-independent dataset;
3. annotate 3D bounding boxes and split data by recording session;
4. train and evaluate PointPillars with MMDetection3D on an NVIDIA workstation;
5. package the selected checkpoint with its configuration and provenance;
6. run GPU inference on the G1's NVIDIA Orin and publish ROS 2 outputs for
   downstream software, Foxglove, and RViz.

## Project status

The technical pipeline is operational from data capture to live visualization.
The bundled checkpoint is deliberately labeled a **pilot model**, not a
production model. It was trained on a small set of static indoor sessions and
successfully validates the integration, but live testing has exposed weak
confidence on some ball detections and high-confidence false positives on
unseen artifacts.

The next milestone is therefore data quality and generalization rather than
runtime integration: collect varied environments, include hard negatives,
create independent train/validation/test splits, retrain, and evaluate the
failure cases explicitly.

The architecture can be extended to other object classes. The current pilot is
configured specifically for class `ball` and a fixed 0.22 m bounding box.
Adding another class requires a versioned taxonomy and annotations, an adapted
MMDetection3D configuration, and matching class and box metadata in the model
package and inference node.

## Inputs and outputs

### Training pipeline

| Stage | Input | Output |
|---|---|---|
| Data capture | ROS 2 bags and session metadata | Immutable raw recordings and SHA-256 checksums |
| Canonical extraction | `/utlidar/cloud_livox_mid360` as `sensor_msgs/msg/PointCloud2` | Corrected point clouds, per-sample metadata, and a dataset manifest |
| Annotation | Canonical clouds and reviewed 3D boxes | JSON annotations with class, center, dimensions, and yaw |
| Training | `x, y, z, intensity` points, annotations, and session-level splits | Checkpoints, logs, metrics, and a locked software environment |
| Model release | Selected checkpoint and resolved configuration | Immutable package under `model_registry/` |

### Live inference

Default input:

```text
/utlidar/cloud_livox_mid360  sensor_msgs/msg/PointCloud2
```

Published outputs:

```text
/lidar/detections_json       std_msgs/msg/String
/lidar/detection_markers     visualization_msgs/msg/MarkerArray
/diagnostics                 diagnostic_msgs/msg/DiagnosticArray
```

The JSON output includes class names, confidence scores, 3D centers, box sizes,
processing time, and received/dropped frame counters. Corrected coordinates use
`X forward, Y left, Z up`. The marker topic publishes red 3D wireframes and
labels that can be overlaid directly on the point cloud in Foxglove or RViz.

## System architecture

```text
Unitree G1 / Livox Mid-360
            │ ROS 2 PointCloud2 bags
            ▼
Canonical extraction ─► annotation ─► session-level split
            │                                  │
            │                                  ▼
            │                       PointPillars training
            │                                  │
            │                                  ▼
            └────────────────────── versioned model package
                                               │
                                               ▼
                                  Orin inference container
                                               │
                            ┌──────────────────┼──────────────────┐
                            ▼                  ▼                  ▼
                          JSON          3D markers         diagnostics
```

Training code is independent from the ROS 2 node. The runtime does not need to
know how the dataset or rosbags are organized. Their interface is a versioned
model package containing the checkpoint, configuration, classes, metrics,
environment information, and checksums.

## Reference platforms

- **Capture and inference:** Unitree G1, NVIDIA Orin NX, ARM64, Ubuntu 20.04,
  L4T R35.3.1, and ROS 2 Foxy.
- **Reference training host:** Ubuntu 22.04 x86_64, NVIDIA RTX 3090 24 GB,
  Docker, and NVIDIA Container Runtime.
- **Data preparation and tests:** Python 3.10 or newer. macOS and CPU-only hosts
  can prepare and validate data, but the reference MMDetection3D training stack
  requires an NVIDIA GPU.

The training workstation is recorded in
[`docs/training_machine_trojalab02.md`](docs/training_machine_trojalab02.md).
The G1 uses a non-default Cyclone DDS stack. Read the compatibility section in
[`docs/deployment_guide.md`](docs/deployment_guide.md) before building the
runtime for a different robot or software image.

## Repository layout

```text
├── README.md                      English project overview and quick start
├── README.fr.md                   French project overview and quick start
├── ROADMAP.md                     target architecture, decisions, and milestones
├── docs/                          protocols, operational guides, and reports
├── data/                          local raw/processed data, excluded from Git
├── remote-g1/                     local staging area for files copied from the G1
├── data_manifests/                version-controlled dataset provenance
│   ├── sessions/                  capture conditions for each recording
│   ├── datasets/                  dataset composition and source lineage
│   ├── annotations/               annotation-set versions
│   └── environments/              experiment machines and environments
├── lidar_detection_training/      preparation, annotation, metrics, and training
│   ├── configs/                   data, split, model, and experiment configs
│   ├── src/lidar_training/        testable Python library
│   ├── tools/                     preparation and training entry points
│   └── tests/                     data-pipeline tests
├── lidar_detection_ros/           ROS 2 inference package
│   ├── launch/                    parameterized launch file
│   ├── lidar_detection_ros/       backend, PointCloud2 adapter, and publishers
│   ├── tools/                     offline inference on a `.bin` cloud
│   └── test/                      runtime and ROS-message tests
├── docker/                        training and Jetson inference images
├── model_registry/                releasable models, manifests, and checksums
├── reports/                       version-controlled metrics and evidence
└── runs/                          local training outputs, excluded from Git
```

`data/`, `remote-g1/`, and `runs/` may become large and are intentionally kept
out of Git. Small explicitly approved checkpoints, manifests, configurations,
and reports remain version-controlled to preserve reproducibility.

## Documentation map

Most detailed project notes were written during the original French
development workflow. Filenames and commands are stable; the English summary
below explains where to start.

### Sensor and data

- [`ROADMAP.md`](ROADMAP.md) — target architecture, engineering decisions, and
  delivery criteria.
- [`docs/sensor_inventory.md`](docs/sensor_inventory.md) — measured system,
  topic, fields, frequency, QoS, frames, and timestamp behavior.
- [`docs/ball_visibility_report.md`](docs/ball_visibility_report.md) — measured
  LiDAR returns on the ball at different distances.
- [`docs/data_collection_protocol.md`](docs/data_collection_protocol.md) —
  recording scenarios and raw-data preservation rules.
- [`docs/session_metadata_template.yaml`](docs/session_metadata_template.yaml)
  — metadata template copied into every recording session.
- [`docs/canonical_data_format.md`](docs/canonical_data_format.md) —
  ROS-independent dataset format and upside-down sensor correction.

### Annotation and baseline

- [`docs/annotation_guide.md`](docs/annotation_guide.md) — 3D box convention,
  JSON schema, difficulty levels, and human review rules.
- [`docs/preannotation_report.md`](docs/preannotation_report.md) — geometric
  pre-annotation method and limitations.
- [`docs/geometric_baseline_report.md`](docs/geometric_baseline_report.md) —
  evaluation of the non-learning baseline.

### Training and evaluation

- [`docs/training_guide.md`](docs/training_guide.md) — Docker environment,
  PointPillars commands, dataset requirements, and reproducibility rules.
- [`docs/training_machine_trojalab02.md`](docs/training_machine_trojalab02.md)
  — reference NVIDIA workstation.
- [`docs/pointpillars_overfit_report.md`](docs/pointpillars_overfit_report.md) —
  mini-dataset overfit check.
- [`docs/pointpillars_pilot_report.md`](docs/pointpillars_pilot_report.md) —
  pilot metrics, live observations, and known limitations.
- [`docs/model_card_template.md`](docs/model_card_template.md) — required model
  documentation template.

### Deployment and visualization

- [`docs/deployment_guide.md`](docs/deployment_guide.md) — Jetson build,
  Cyclone DDS compatibility, launch procedure, and troubleshooting.
- [`docs/foxglove_visualization.md`](docs/foxglove_visualization.md) — point
  cloud, red detection boxes, and JSON visualization in Foxglove.
- [`model_registry/README.md`](model_registry/README.md) — model-package
  requirements.

## Install the data tools and run the tests

Python 3.10 or newer is required for the training utilities:

```bash
git clone https://github.com/Ayrcs/livox-lidar-object-detection.git
cd livox-lidar-object-detection

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e './lidar_detection_training[test,rosbag,analysis]'
```

Run the complete local test suite:

```bash
PYTHONPATH=lidar_detection_ros:lidar_detection_training/src \
  python -m pytest -q lidar_detection_training/tests lidar_detection_ros/test
```

## Build a dataset

1. Record multiple independent sessions using the collection protocol.
2. Store the rosbags under `remote-g1/lidar_data/raw/`, or update the configured
   root path.
3. Create session manifests and verify their SHA-256 checksums.
4. Extract deterministic canonical samples:

```bash
.venv/bin/python lidar_detection_training/tools/extract_canonical_dataset.py \
  --config lidar_detection_training/configs/data/canonical_v1.yaml \
  --bags-root remote-g1/lidar_data/raw \
  --output-dir data/processed/ball_lidar_feasibility_v1
```

5. Optionally generate geometric pre-annotations, then **review every box and
   every negative frame manually** using the annotation guide.
6. Define train, validation, and test sessions in a new split configuration.
   Never place adjacent frames from the same recording in different splits.
7. Build and validate the MMDetection3D dataset:

```bash
.venv/bin/python lidar_detection_training/tools/build_pilot_dataset.py \
  --config lidar_detection_training/configs/data/pilot_split_v1.yaml

.venv/bin/python lidar_detection_training/tools/validate_pilot_dataset.py \
  --dataset-root data/processed/ball_lidar_pilot_v1_mmdet3d \
  --report reports/pilot_dataset_v1/validation.json
```

These commands reproduce the current pilot. New datasets should use new,
versioned identifiers and paths rather than silently overwriting the `v1`
artifacts.

## Train PointPillars

Build the reference training image once on the NVIDIA workstation:

```bash
docker build -f docker/training.Dockerfile \
  -t lidar-pointpillars-training:1.0 .
```

First verify that the network can memorize a small subset:

```bash
docker run --rm --gpus all --shm-size=8g \
  -v "$PWD:/workspace" -w /workspace \
  lidar-pointpillars-training:1.0 \
  bash lidar_detection_training/tools/run_pointpillars_training.sh overfit
```

Then run the pilot experiment:

```bash
docker run --rm --gpus all --shm-size=8g \
  -v "$PWD:/workspace" -w /workspace \
  lidar-pointpillars-training:1.0 \
  bash lidar_detection_training/tools/run_pointpillars_training.sh pilot
```

Checkpoints and logs are written to `runs/`. Select a checkpoint on a
validation split that is independent from training, then report final numbers
on a separate test set containing target-free scenes and hard distractors. A
low training loss alone is not a model-selection criterion.

A stronger ball model should cover multiple sites and surfaces, including
grass; stationary and rolling balls; different ranges and lateral positions;
stationary and moving robot motion; occlusion; target-free frames; and every
artifact that currently produces high-confidence false positives. See the
training guide for the complete collection requirements.

## Package and release a model

Each accepted model is stored in a new immutable directory, for example:

```text
model_registry/ball_pointpillars_v0.2.0/
├── model.pth
├── config.py
├── manifest.yaml
├── classes.yaml
├── metrics.json
├── model_card.md
├── environment.lock.txt
└── SHA256SUMS
```

The manifest records input fields, coordinate convention, transforms, spatial
range, classes, box sizes, software versions, training data, and known
limitations. The runtime verifies `SHA256SUMS`, `model.pth`, and `config.py`
before loading the package. Published versions are immutable: create a new
version instead of replacing an existing model in place.

## Build and run inference on the G1

Clone the repository on the robot and build the three Docker layers:

```bash
git clone https://github.com/Ayrcs/livox-lidar-object-detection.git
cd livox-lidar-object-detection
sudo ./docker/build-jetson.sh
```

The initial CUDA/MMDetection3D build is slow. Later builds reuse that base. The
DDS layer must match the Cyclone DDS version actually loaded by the G1. The
current build reproduces the reference robot with Cyclone DDS 0.10.2; do not
assume that the system package version is the active runtime on another robot.

Launch the bundled pilot model:

```bash
sudo docker run --rm \
  --runtime nvidia \
  --network host \
  --ipc host \
  -v "$PWD/model_registry/ball_pointpillars_pilot_v0.1.0:/model:ro" \
  lidar-detection-jetson:0.2.0 \
  ros2 launch lidar_detection_ros detection.launch.py \
    model_path:=/model \
    input_topic:=/utlidar/cloud_livox_mid360 \
    score_threshold:=0.10
```

Initial model loading on the Orin takes approximately 15–20 seconds. The node
then keeps the model in GPU memory and retains only the newest point cloud to
avoid building a latency backlog.

Inspect the outputs from a second terminal on the G1:

```bash
ros2 topic echo /lidar/detections_json
ros2 topic hz /lidar/detections_json
ros2 topic echo /diagnostics
```

For Foxglove, start `rosbridge_websocket`, display
`/utlidar/cloud_livox_mid360`, and enable `/lidar/detection_markers` in the same
3D panel. Refer to the Foxglove guide if the JSON is published but no box is
visible.

## Roadmap

The end-to-end engineering path is validated: acquisition, deterministic
extraction, pilot annotation, RTX 3090 training, model packaging, CUDA
inference on the Orin, ROS 2 publication, and Foxglove visualization.

The next milestones are:

1. collect a diverse ball dataset with substantially more hard negatives;
2. review its annotations and build site/session-independent splits;
3. retrain, calibrate the confidence threshold, and analyze false positives by
   scenario;
4. measure recall by range, center error, target-free false positives, latency,
   and dropped frames on the G1;
5. extend the taxonomy to additional object classes only after the ball model
   generalizes reliably.

Always interpret reported metrics together with the matching model card and
dataset limitations.
