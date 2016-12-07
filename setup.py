import os

from setuptools import setup, find_packages

with open('README.rst', 'r') as readme:
    README_TEXT = readme.read()

VERSION = '0.1.6'


def write_version_py(filename=None):
    if filename is None:
        filename = os.path.join(
            os.path.dirname(__file__), 'simliggghts', 'version.py')
    ver = """\
version = '%s'
"""
    fh = open(filename, 'wb')
    try:
        fh.write(ver % VERSION)
    finally:
        fh.close()


write_version_py()

setup(
    name='simliggghts',
    version=VERSION,
    author='SimPhoNy, EU FP7 Project (Nr. 604005) www.simphony-project.eu',
    description='The liggghts wrapper for the SimPhoNy framework',
    long_description=README_TEXT,
    entry_points={
        'simphony.engine': ['liggghts = simliggghts']},
    packages=find_packages(),
    install_requires=["simphony ~= 0.4",
                      "pyyaml >= 3.11"]
    )
