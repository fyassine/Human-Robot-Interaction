from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'human_motion_tracker'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='you@example.com',
    description='Publishes dummy human measurements for safety_shield_node',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'human_motion_tracker = human_motion_tracker.human_motion_tracker:main',
            'human_motion_tracker_debug = human_motion_tracker.human_motion_tracker_debug:main',
            'motion_replay = human_motion_tracker.motion_replay:main',
        ],
    },
)