from setuptools import find_packages, setup


PACKAGE_NAME = "lidar_detection_ros"

setup(
    name=PACKAGE_NAME,
    version="0.1.0",
    packages=find_packages(exclude=("test",)),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{PACKAGE_NAME}"]),
        (f"share/{PACKAGE_NAME}", ["package.xml"]),
        (f"share/{PACKAGE_NAME}/launch", ["launch/detection.launch.py"]),
    ],
    install_requires=["setuptools", "numpy"],
    zip_safe=True,
    maintainer="Aymeric Schaeffer",
    maintainer_email="noreply@example.com",
    description="ROS 2 PointPillars inference for Unitree/Livox point clouds",
    license="Apache-2.0",
    entry_points={"console_scripts": ["lidar_detection_node = lidar_detection_ros.node:main"]},
)
