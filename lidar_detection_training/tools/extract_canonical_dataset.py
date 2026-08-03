#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import yaml

from lidar_training.canonical_io import sha256_file, write_canonical_sample, write_dataset_manifest
from lidar_training.rosbag_io import iter_pointcloud_frames


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract ROS 2 bags into deterministic canonical samples")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--bags-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-frames-per-session", type=int)
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    entries: list[dict[str, object]] = []
    source_sessions: list[dict[str, object]] = []
    for session_id in config["sessions"]:
        bag_dir = args.bags_root / session_id
        database_files = sorted(bag_dir.glob("*.db3"))
        if len(database_files) != 1:
            raise ValueError(f"expected one db3 file in {bag_dir}, found {len(database_files)}")
        source_sessions.append(
            {
                "session_id": session_id,
                "database_file": database_files[0].name,
                "database_sha256": sha256_file(database_files[0]),
            }
        )
        for frame in iter_pointcloud_frames(bag_dir):
            if args.max_frames_per_session is not None and frame.message_index >= args.max_frames_per_session:
                break
            sample_id = f"{session_id}_{frame.message_index:06d}"
            entries.append(
                write_canonical_sample(
                    args.output_dir,
                    sample_id,
                    frame.points,
                    {
                        "session_id": session_id,
                        "header_timestamp_ns": frame.header_timestamp_ns,
                        "bag_timestamp_ns": frame.bag_timestamp_ns,
                        "frame_id": config["output_frame"],
                        "source": {
                            "bag_directory": session_id,
                            "database_file": database_files[0].name,
                            "message_index": frame.message_index,
                            "topic": config["source_topic"],
                            "source_frame": frame.frame_id,
                        },
                        "transform_applied": config["transform"],
                    },
                )
            )

    manifest_path = write_dataset_manifest(
        args.output_dir,
        entries,
        {
            "dataset_name": config["dataset_name"],
            "config": json.loads(json.dumps(config)),
            "source_sessions": source_sessions,
        },
    )
    print(f"Wrote {len(entries)} samples to {args.output_dir}")
    print(manifest_path)


if __name__ == "__main__":
    main()
