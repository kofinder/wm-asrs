from setuptools import setup
from glob import glob
import os

package_name = 'asrs_gazebo_view'
setup(
    name=package_name,
    version='0.2.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'worlds'), glob('worlds/*.sdf')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ASRS lab',
    maintainer_email='lab@example.invalid',
    description='Offline Gazebo Harmonic ASRS warehouse and read-only WCS visual adapter',
    license='MIT',
    entry_points={'console_scripts': [
        'wcs_visual_sync=asrs_gazebo_view.wcs_visual_sync:main',
        'pallet_visual_sync=asrs_gazebo_view.pallet_visual_sync:main',
    ]},
)
