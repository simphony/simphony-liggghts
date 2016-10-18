Converting from existing LIGGGHTS input files
===========================================

The Simphony-LIGGGHTS library provides a set of tools to convert existing
liggghts data files to SimPhoNy CUDS format. While these tools are not required when
using the LIGGGHTS SimPhoNy engine, they can be helpful in converting existing
LIGGGHTS data to SimPhoNy format.  See the following examples:


.. rubric:: Conversion from liggghts data file to list CUDS ```Particles```

.. literalinclude:: ../../examples/file_conversion/convert.py

.. note::

  There needs to be an executable called "liggghts" that can be found in
  the PATH for the example to work.