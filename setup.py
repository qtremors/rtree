from setuptools import setup

setup(
    name='rtree',
    version='1.0',
    py_modules=['tree'],  # Name of your python file (minus .py)
    install_requires=[],  # Add dependencies here if need to add external libs later
    entry_points={
        'console_scripts': [
            'rtree=tree:main',  # Command=File:Function
        ],
    },
)