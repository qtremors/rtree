from setuptools import setup

setup(
    name='rtree',
    version='1.1.0',
    py_modules=['rtree'],
    install_requires=[],  # Add dependencies here if need to add external libs later
    entry_points={
        'console_scripts': [
            'rtree=rtree:main',  # Command=File:Function
        ],
    },
)