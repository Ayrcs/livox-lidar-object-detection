custom_imports = dict(imports=['lidar_training.mmdet3d_dataset'], allow_failed_imports=False)

class_names = ['ball']
metainfo = dict(classes=class_names)
dataset_type = 'BallLidarDataset'
data_root = 'data/processed/ball_lidar_pilot_v1_mmdet3d/'
point_cloud_range = [0.4, -1.0, -1.5, 6.0, 1.0, -0.7]
voxel_size = [0.05, 0.05, 0.8]

model = dict(
    type='VoxelNet',
    data_preprocessor=dict(
        type='Det3DDataPreprocessor',
        voxel=True,
        voxel_layer=dict(
            max_num_points=32,
            point_cloud_range=point_cloud_range,
            voxel_size=voxel_size,
            max_voxels=(4000, 8000))),
    voxel_encoder=dict(
        type='PillarFeatureNet',
        in_channels=4,
        feat_channels=[64],
        with_distance=False,
        voxel_size=voxel_size,
        point_cloud_range=point_cloud_range),
    middle_encoder=dict(type='PointPillarsScatter', in_channels=64, output_shape=[40, 112]),
    backbone=dict(
        type='SECOND',
        in_channels=64,
        layer_nums=[3, 5, 5],
        layer_strides=[2, 2, 2],
        out_channels=[64, 128, 256]),
    neck=dict(
        type='SECONDFPN',
        in_channels=[64, 128, 256],
        upsample_strides=[1, 2, 4],
        out_channels=[128, 128, 128]),
    bbox_head=dict(
        type='Anchor3DHead',
        num_classes=1,
        in_channels=384,
        feat_channels=384,
        # MMDetection3D 1.4 returns loss_dir=None when this head is disabled,
        # which MMEngine 0.10 cannot aggregate. Keep the tensor-producing head
        # enabled with zero loss weight; ball yaw is reset to zero downstream.
        use_direction_classifier=True,
        assign_per_class=False,
        anchor_generator=dict(
            type='AlignedAnchor3DRangeGenerator',
            ranges=[[0.4, -1.0, -1.25, 6.0, 1.0, -1.25]],
            sizes=[[0.22, 0.22, 0.22]],
            rotations=[0.0],
            reshape_out=True),
        diff_rad_by_sin=True,
        bbox_coder=dict(type='DeltaXYZWLHRBBoxCoder'),
        loss_cls=dict(
            type='mmdet.FocalLoss', use_sigmoid=True, gamma=2.0, alpha=0.25, loss_weight=1.0),
        loss_bbox=dict(type='mmdet.SmoothL1Loss', beta=1.0 / 9.0, loss_weight=2.0),
        loss_dir=dict(
            type='mmdet.CrossEntropyLoss',
            use_sigmoid=False,
            loss_weight=0.0)),
    train_cfg=dict(
        assigner=dict(
            type='Max3DIoUAssigner',
            iou_calculator=dict(type='BboxOverlapsNearest3D'),
            pos_iou_thr=0.45,
            neg_iou_thr=0.25,
            min_pos_iou=0.25,
            ignore_iof_thr=-1),
        allowed_border=0,
        pos_weight=-1,
        debug=False),
    test_cfg=dict(
        use_rotate_nms=True,
        nms_across_levels=False,
        nms_thr=0.05,
        score_thr=0.10,
        min_bbox_size=0,
        nms_pre=200,
        max_num=20))

train_pipeline = [
    dict(type='LoadPointsFromFile', coord_type='LIDAR', load_dim=4, use_dim=4),
    dict(type='LoadAnnotations3D', with_bbox_3d=True, with_label_3d=True),
    dict(type='RandomFlip3D', flip_ratio_bev_horizontal=0.5),
    dict(
        type='GlobalRotScaleTrans',
        rot_range=[-0.12, 0.12],
        scale_ratio_range=[1.0, 1.0],
        translation_std=[0.02, 0.02, 0.01]),
    dict(type='PointsRangeFilter', point_cloud_range=point_cloud_range),
    dict(type='ObjectRangeFilter', point_cloud_range=point_cloud_range),
    dict(type='ObjectNameFilter', classes=class_names),
    dict(type='PointShuffle'),
    dict(type='Pack3DDetInputs', keys=['points', 'gt_bboxes_3d', 'gt_labels_3d']),
]

val_pipeline = [
    dict(type='LoadPointsFromFile', coord_type='LIDAR', load_dim=4, use_dim=4),
    dict(type='LoadAnnotations3D', with_bbox_3d=True, with_label_3d=True),
    dict(type='PointsRangeFilter', point_cloud_range=point_cloud_range),
    dict(type='Pack3DDetInputs', keys=['points', 'gt_bboxes_3d', 'gt_labels_3d']),
]

# Runtime inference has no ground-truth annotation. Keep this pipeline separate
# from validation so mmdet3d.apis.inference_detector can consume a raw N x 4
# NumPy point cloud.
test_pipeline = [
    dict(type='LoadPointsFromFile', coord_type='LIDAR', load_dim=4, use_dim=4),
    dict(type='PointsRangeFilter', point_cloud_range=point_cloud_range),
    dict(type='Pack3DDetInputs', keys=['points']),
]

train_dataloader = dict(
    batch_size=8,
    num_workers=4,
    persistent_workers=True,
    sampler=dict(type='DefaultSampler', shuffle=True),
    dataset=dict(
        type=dataset_type,
        data_root=data_root,
        ann_file='ball_infos_train.pkl',
        data_prefix=dict(pts=''),
        pipeline=train_pipeline,
        modality=dict(use_lidar=True, use_camera=False),
        test_mode=False,
        metainfo=metainfo,
        box_type_3d='LiDAR'))

val_dataloader = dict(
    batch_size=4,
    num_workers=2,
    persistent_workers=True,
    drop_last=False,
    sampler=dict(type='DefaultSampler', shuffle=False),
    dataset=dict(
        type=dataset_type,
        data_root=data_root,
        ann_file='ball_infos_val_distance_holdout.pkl',
        data_prefix=dict(pts=''),
        pipeline=val_pipeline,
        modality=dict(use_lidar=True, use_camera=False),
        test_mode=False,
        metainfo=metainfo,
        box_type_3d='LiDAR'))
test_dataloader = dict(
    batch_size=1,
    num_workers=1,
    persistent_workers=False,
    drop_last=False,
    sampler=dict(type='DefaultSampler', shuffle=False),
    dataset=dict(
        type=dataset_type,
        data_root=data_root,
        ann_file='ball_infos_val_distance_holdout.pkl',
        data_prefix=dict(pts=''),
        pipeline=test_pipeline,
        modality=dict(use_lidar=True, use_camera=False),
        test_mode=True,
        metainfo=metainfo,
        box_type_3d='LiDAR'))

val_evaluator = dict(type='BallCenterMetric', match_distance_m=0.30, score_threshold=0.10)
test_evaluator = val_evaluator

optim_wrapper = dict(
    type='OptimWrapper',
    optimizer=dict(type='AdamW', lr=0.001, weight_decay=0.01),
    clip_grad=dict(max_norm=10, norm_type=2))
param_scheduler = [
    dict(type='LinearLR', start_factor=0.1, by_epoch=False, begin=0, end=100),
    dict(type='CosineAnnealingLR', by_epoch=True, begin=0, end=40, T_max=40, eta_min=1e-5),
]
train_cfg = dict(type='EpochBasedTrainLoop', max_epochs=40, val_interval=5)
val_cfg = dict(type='ValLoop')
test_cfg = dict(type='TestLoop')

default_scope = 'mmdet3d'
default_hooks = dict(
    timer=dict(type='IterTimerHook'),
    logger=dict(type='LoggerHook', interval=10),
    param_scheduler=dict(type='ParamSchedulerHook'),
    checkpoint=dict(
        type='CheckpointHook',
        interval=5,
        save_best='ball/f1_center_0p30m',
        rule='greater'),
    sampler_seed=dict(type='DistSamplerSeedHook'))
env_cfg = dict(cudnn_benchmark=False, mp_cfg=dict(mp_start_method='fork', opencv_num_threads=0))
log_level = 'INFO'
# Strict CUDA determinism triggers a known PyTorch 2.0 advanced-indexing bug
# in MMDetection3D's anchor assignment. The seed remains fixed, but training is
# reproducible at the experiment level rather than bit-for-bit.
randomness = dict(seed=20260803, deterministic=False)
visualizer = dict(type='Det3DLocalVisualizer', vis_backends=[dict(type='LocalVisBackend')], name='visualizer')
work_dir = 'runs/pointpillars_ball_pilot_v1'
load_from = None
resume = False
