from simphony.cuds.particles import Particle, Particles
from simphony.core.data_container import DataContainer
from simphony.core.cuba import CUBA

from ..common import globals
from .liggghts_data_file_parser import LiggghtsDataFileParser
from .liggghts_simple_data_handler import LiggghtsSimpleDataHandler
from .liggghts_data_line_interpreter import LiggghtsDataLineInterpreter
from ..config.domain import get_box
from ..cuba_extension import CUBAExtension
from ..common.atom_style import (AtomStyle, get_atom_style)
from .liggghts_data_file_writer import LiggghtsDataFileWriter


def read_data_file(filename, atom_style=None):
    """ Reads liggghts data file and create CUDS objects

    Reads liggghts data file and create list of Particles. The returned list
    of Particles will contain a Particles for each atom type (i.e.
    CUBA.MATERIAL_TYPE). The name of the Particles will be the atom type (e.g.
    a Particles with atom_type/CUBA.MATERIAL_TYPE of 1 will have the name "1")

    The attributes for each particle are based upon what atom-style
    the file contains (i.e. "sphere" means that particles in addition to having
    CUBA.VELOCITY will also have a CUBA.RADIUS and CUBA.MASS). See
    'atom_style' for more details.

    Parameters
    ----------
    filename : str
        filename of liggghts data file

    atom_style : AtomStyle
        type of atoms in the file.  If None, then an attempt of
        interpreting the atom-style in the file is performed.

    Returns
    -------
    particles_list : list of Particles
        list of Particles where each Particles has a name equal
        to their CUBA.MATERIAL_TYPE and is filled up with
        particles of that type.

    """
    handler = LiggghtsSimpleDataHandler()
    parser = LiggghtsDataFileParser(handler=handler)

    parser.parse(filename)

    if atom_style is None:
        atom_style = (
            get_atom_style(handler.get_atom_type())
            if handler.get_atom_type()
            else AtomStyle.GRANULAR)

    interpreter = LiggghtsDataLineInterpreter(atom_style)

    types = (atom_t for atom_t in range(1, handler.get_number_atom_types()+1))
    atoms = handler.get_atoms()
    velocities = handler.get_velocities()

    globals.MAX_NUMBER_TYPES = handler.get_number_atom_types()

    box_origin = handler.get_box_origin()
    box_vectors = handler.get_box_vectors()

    type_to_particles_map = {}

    # set up a Particles for each different type
    for atom_type in types:
        data = DataContainer()
        data[CUBA.MATERIAL_TYPE] = atom_type

        data_extension = {CUBAExtension.BOX_ORIGIN: box_origin,
                          CUBAExtension.BOX_VECTORS: box_vectors}

        particles = Particles(name="{}".format(atom_type))
        particles.data = data
        particles.data_extension = dict(data_extension)

        type_to_particles_map[atom_type] = particles

    # add each particle to each Particles
    for liggghts_id, values in atoms.iteritems():
        coordinates, data = interpreter.convert_atom_values(values)
        data.update(
            interpreter.convert_velocity_values(velocities[liggghts_id]))

        p = Particle(coordinates=coordinates, data=data)

        # TODO #9 (removing material type
        atom_type = p.data[CUBA.MATERIAL_TYPE]
        del p.data[CUBA.MATERIAL_TYPE]

        type_to_particles_map[atom_type].add([p])

    return type_to_particles_map.values()


def write_data_file(filename, particles_list, atom_style=AtomStyle.GRANULAR):
    """ Writes liggghts data file from CUDS objects

    Writes liggghts data file from a list of Particles.

    The particles will be annotated with their Simphony-uid. For example::

        10 1 17 -1.0 10.0 5.0 6.0   # particles_name:'foo' uid:'40fb302c-6e71-11e5-b35f-08606e7c2200'  # noqa


    Parameters
    ----------
    filename : str
        filename of liggghts data file

    particles_list : iterable of Particles
        particles

    atom_style : AtomStyle
        type of atoms to be written to file

    """

    num_particles = sum(
        pc.count_of(CUBA.PARTICLE) for pc in particles_list)
    types = set(pc.data[CUBA.MATERIAL_TYPE] for pc in particles_list)

    box = get_box([pc.data_extension for pc in particles_list])

    material_type_to_mass = None if not _style_has_masses(
        atom_style) else _get_mass([pc.data for pc in particles_list])

    writer = LiggghtsDataFileWriter(
                filename,
                atom_style=atom_style,
                number_atoms=num_particles,
                number_atom_types=len(types),
                simulation_box=box,
                material_type_to_mass=material_type_to_mass)

    for particles in particles_list:
        material_type = particles.data[CUBA.MATERIAL_TYPE]
        for p in particles.iter(item_type=CUBA.PARTICLE):
            writer.write_atom(p, material_type)
    writer.close()


def _style_has_masses(atom_style):
    """ Returns if atom style has masses

    """
    # TODO have a relationship between atom_style and if masses are needed
    return atom_style != AtomStyle.GRANULAR


def _get_mass(high_level_data):
    """ Get a dictionary from 'material type' to 'mass'.

    Check that fits what liggghts can handle as well
    as ensure that it works with the limitations
    of how we are currently handling this info.

    Raises
    ------
    RuntimeError :
        if there are particles' which have the same
        material type (CUBA.MATERIAL_TYPE) but different
        masses (CUBA.MASS)

    """
    mass = {}
    for data in high_level_data:
        material_type = data[CUBA.MATERIAL_TYPE]
        if material_type in mass:
            # check that mass is consistent with an matching type
            if data[CUBA.MASS] != mass[material_type]:
                raise RuntimeError(
                    "Each material type must have the same mass")
        else:
            mass[material_type] = data[CUBA.MASS]
    return mass
