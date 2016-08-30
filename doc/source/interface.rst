LIGGGHTS engine for SimPhoNy
==========================

The SimPhoNy engine for LIGGGHTS is available in the SimPhoNy through the engine plugin named ``lammps``

After installation, the user should be able to import the ``lammps`` engine plugin module::

  from simphony.engine import lammps
    engine = lammps.LammpsWrapper()



Interface to LIGGGHTS
--------------------

The SimPhoNy LIGGGHTS engine (see :class:`LiggghtsWrapper`) can be configured to
interface with LIGGGHTS in two separate ways:

* FILE-IO - input and output files are used to configure and run LIGGGHTS engine
* INTERNAL - the LIGGGHTS library interface is used to run LIGGGHTS and access the
  internal state.

Despite performance differences, it should not matter whether the user is
using the File-IO or the INTERNAL interface as the API is the same.

::

   # wrapper defaults to FILE-IO
   from simphony.engine import liggghts
       engine = liggghts.LiggghtsWrapper()

::

   # or use INTERNAL wrapper
   from simphony.engine import liggghts
       engine = liggghts.LiggghtsWrapper(use_internal_interface=true)


Installation of LIGGGHTS
----------------------

This engine-wrapper uses LIGGGHTS Molecular Dynamics Simulator. A recent stable
version (17 May 2016, tagged 3.4.0) of LIGGGHTS is supported and has been
tested. See ``install_external.sh`` for an example installation instructions.
For general LIGGGHTS install information, see https://github.com/CFDEMproject/LIGGGHTS-PUBLIC

The installation of LIGGGHTS differs depending on what interface is used:

- FILE-IO: There needs to be an executable called "liggghts" that can be found in
  the PATH.
- INTERNAL:  The LIGGGHTS-provided Python wrapper to LIGGGHTS needs to be
  installed. Instructions on building LIGGGHTS as a shared library and installing
  the Python wrapper can be found in ``install_external.sh``.

Limitations of the INTERNAL interface
-------------------------------------
The following are known limitations when using the INTERNAL interface to LIGGGHTS:
 - Currently an upper limit of particle types (CUBA.MATERIAL_TYPE) is set due to
   the fact that LIGGGHTS only allows the number of types be configured at start
   (and not changed later) (https://github.com/simphony/simphony-lammps-md/issues/66)
 - No notification is provided to the user when an internal error occurs in the
   LIGGGHTS shared library as the library calls `exit(1)` and the process
   immediately exists (without an exception or writing to standard
   output/error).  (https://github.com/simphony/simphony-lammps-md/issues/63)
