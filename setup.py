from setuptools import setup, find_packages

setup(
    name='pybmt',
    version='0.1.0',
    python_requires='>3.6',
    description='Python Ball Motion Tracking (pymbt): A python interface for closed loop fictrac (https://github.com/rjdmoore/fictrac)',
    author='David Turner',
    author_email='dmturner@princeton.edu',
    license='Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License',
    keywords='fictive, tracking, animal tracking, webcamera, sphere, closed loop',
    url="https://github.com/murthylab/pybmt",
    packages=find_packages(),
    install_requires=[
        'pyzmq',
        'numpy',
        'matplotlib',
        'pytest'],
    zip_safe=False
)