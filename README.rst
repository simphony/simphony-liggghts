simphony-liggghts
===============

The LIGGGHTS engine-wrapper for the SimPhoNy framework (www.simphony-project.eu).

.. image:: https://travis-ci.org/simphony/simphony-liggghts.svg?branch=master
   :target: https://travis-ci.org/simphony/simphony-liggghts
   :alt: Build status

.. image:: http://codecov.io/github/simphony/simphony-liggghts/coverage.svg?branch=master
   :target: http://codecov.io/github/simphony/simphony-liggghts?branch=master
   :alt: Test coverage

.. image:: https://readthedocs.org/projects/simphony-liggghts/badge/?version=master
   :target: https://readthedocs.org/projects/simphony-liggghts/?badge=master
   :alt: Documentation Status


Repository
----------

simphony-liggghts is hosted on github: https://github.com/simphony/simphony-liggghts

Requirements
------------

- pyyaml >= 3.11
- `simphony-common`_ ~= 0.5.0

Optional requirements
~~~~~~~~~~~~~~~~~~~~~

To support the documentation built you need the following packages:

- sphinx >= 1.2.3
- sphinxcontrib-napoleon >= 0.2.10

Installation
------------

The package requires python 2.7.x. Installation is based on setuptools::

    # build and install
    python setup.py install

or::

    # build for in-place development
    python setup.py develop

LIGGGHTS installation
~~~~~~~~~~~~~~~~~~~

This engine-wrapper uses LIGGGHTS DEM simulation engine. A recent stable
version (17 May 2016, tagged 3.4.0) of LIGGGHTS is supported and has been
tested. See ``install_external.sh`` for an example installation instructions.
For general LIGGGHTS install information, see https://github.com/CFDEMproject/LIGGGHTS-PUBLIC

LIGGGHTS installation varies depending on which interface is being used.  See the
manual for more details.


Usage
-----

After installation, the user should be able to import the ``liggghts`` engine plugin module by::

  from simphony.engine import liggghts
    engine = liggghts.LiggghtsWrapper()


Testing
-------

To run the full test-suite run::

    python -m unittest discover

Documentation
-------------

To build the documentation in the doc/build directory run::

    python setup.py build_sphinx

.. note::

    - One can use the --help option with a setup.py command
      to see all available options.
    - The documentation will be saved in the ``./build`` directory.


Directory structure
-------------------

- simliggghts -- holds the liggghts wrapper implementation

    - bench - benchmarking
    - common - contains general global files
    - config - holds configuration related files
    - internal - internal library communication with LIGGGHTS
    - io -- file-io related communication with LIGGGHTS
    - testing -- testing related utilities
- examples -- holds different examples
- doc -- Documentation related files

    - source -- Sphinx rst source files
    - build -- Documentation build directory, if documentation has been generated
      using the ``make`` script in the ``doc`` directory.

.. _simphony-common: https://github.com/simphony/simphony-common
