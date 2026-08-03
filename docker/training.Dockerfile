FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-devel

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends git build-essential libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir openmim==0.3.9 \
    && mim install "mmengine==0.10.7" \
    && mim install "mmcv==2.1.0" \
    && mim install "mmdet==3.2.0"

RUN git clone --branch v1.4.0 --depth 1 \
      https://github.com/open-mmlab/mmdetection3d.git /opt/mmdetection3d \
    && python -m pip install --no-cache-dir -e /opt/mmdetection3d

WORKDIR /workspace
COPY lidar_detection_training /workspace/lidar_detection_training
RUN python -m pip install --no-cache-dir --no-deps -e /workspace/lidar_detection_training

CMD ["bash"]
