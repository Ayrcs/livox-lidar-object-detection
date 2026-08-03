_base_ = ['../models/pointpillars_ball_pilot.py']

train_dataloader = dict(
    batch_size=8,
    num_workers=2,
    dataset=dict(ann_file='ball_infos_overfit.pkl', pipeline={{_base_.train_pipeline}}))

# No augmentation: this gate must prove that the model can memorize 80 samples.
train_pipeline = [
    dict(type='LoadPointsFromFile', coord_type='LIDAR', load_dim=4, use_dim=4),
    dict(type='LoadAnnotations3D', with_bbox_3d=True, with_label_3d=True),
    dict(type='PointsRangeFilter', point_cloud_range={{_base_.point_cloud_range}}),
    dict(type='ObjectRangeFilter', point_cloud_range={{_base_.point_cloud_range}}),
    dict(type='ObjectNameFilter', classes={{_base_.class_names}}),
    dict(type='Pack3DDetInputs', keys=['points', 'gt_bboxes_3d', 'gt_labels_3d']),
]
train_dataloader = dict(
    batch_size=8,
    num_workers=2,
    persistent_workers=True,
    sampler=dict(type='DefaultSampler', shuffle=True),
    dataset=dict(
        type={{_base_.dataset_type}},
        data_root={{_base_.data_root}},
        ann_file='ball_infos_overfit.pkl',
        data_prefix=dict(pts=''),
        pipeline=train_pipeline,
        modality=dict(use_lidar=True, use_camera=False),
        test_mode=False,
        metainfo={{_base_.metainfo}},
        box_type_3d='LiDAR'))

train_cfg = dict(type='EpochBasedTrainLoop', max_epochs=30, val_interval=5)
work_dir = 'runs/pointpillars_ball_overfit_v1'
