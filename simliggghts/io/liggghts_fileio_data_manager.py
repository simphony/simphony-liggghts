import os

from simphony.core.cuba import CUBA
from simphony.core.data_container import DataContainer
from simphony.cuds.particles import Particles, Particle

from .liggghts_data_file_parser import LiggghtsDataFileParser
from .liggghts_simple_data_handler import LiggghtsSimpleDataHandler
from .liggghts_data_line_interpreter import LiggghtsDataLineInterpreter
from .liggghts_data_file_writer import LiggghtsDataFileWriter

from ..common.atom_style_description import (ATOM_STYLE_DESCRIPTIONS,
                                             get_attributes)

from ..config.domain import get_box

from ..abc_data_manager import ABCDataManager


def _filter_unsupported_data(iterable, supported_cuba):
    """Ensure iterators only provide particles with only supported data

    Parameters
    ----------
    iterable : iterator of Particles
        iterable of particles
    supported_cuba: list of CUBA
        what cuba is supported

    """
    for particle in iterable:
        data = particle.data
        supported_data = {cuba: data[cuba] for cuba in
                          data if cuba in supported_cuba}
        supported_particle = Particle(coordinates=particle.coordinates,
                                      uid=particle.uid,
                                      data=supported_data)
        yield supported_particle


class LiggghtsFileIoDataManager(ABCDataManager):
    """  Class managing Liggghts data information using file-io

    The class performs communicating the data to and from Liggghts using
    FILE-IO communications (i.e. through input and output files). The class
    manages data existing in Liggghts (via Liggghts data file) and allows this
    data to be queried and to be changed.

    Class maintains a cache of the particle information. This information
    is read from file whenever the read() method is called and written to
    the file whenever the flush() method is called.

    Parameters
    ----------
    atom_style : str

    """
    def __init__(self, atom_style):
        super(LiggghtsFileIoDataManager, self).__init__()

        self._atom_style = atom_style

        # map from Liggghts-id to simphony-uid
        self._liggghtsid_to_uid = {}

        # cache of particle containers
        self._pc_cache = {}

        # cache of data container extensions
        self._dc_extension_cache = {}

        self._supported_cuba = get_attributes(self._atom_style)

    def get_data(self, uname):
        """Returns data container associated with particle container

        Parameters
        ----------
        uname : string
            non-changing unique name of particles

        """
        return DataContainer(self._pc_cache[uname].data)

    def set_data(self, data, uname):
        """Sets data container associated with particle container

        Parameters
        ----------
        uname : string
            non-changing unique name of particles

        """
        self._pc_cache[uname].data = DataContainer(data)

    def get_data_extension(self, uname):
        """Returns data container extension associated with particle container

        Parameters
        ----------
        uname : string
            non-changing unique name of particles

        """
        return dict(self._dc_extension_cache[uname])

    def set_data_extension(self, data, uname):
        """Sets data container extension associated with particle container

        Parameters
        ----------
        uname : string
            non-changing unique name of particles

        """
        self._dc_extension_cache[uname] = dict(data)

    def _handle_delete_particles(self, uname):
        """Handle when a Particles is deleted

        Parameters
        ----------
        uname : string
            non-changing unique name of particles

        """
        del self._pc_cache[uname]
        del self._dc_extension_cache[uname]

    def _handle_new_particles(self, uname, particles):
        """Add new particle container to this manager.


        Parameters
        ----------
        uname : string
            non-changing unique name of particles
        particles : ABCParticles
            particle container to be added

        """
        # create stand-alone particle container to use
        # as a cache of for input/output to Liggghts
        pc = Particles(name="_")
        pc.data = DataContainer(particles.data)

        for p in particles.iter(item_type=CUBA.PARTICLE):
            pc.add([p])

        for b in particles.iter(item_type=CUBA.BOND):
            pc.add([b])

        self._pc_cache[uname] = pc

        if hasattr(particles, 'data_extension'):
            self._dc_extension_cache[uname] = dict(particles.data_extension)
        else:
            # create empty dc extension
            self._dc_extension_cache[uname] = {}

    def get_particle(self, uid, uname):
        """Get particle

        Parameters
        ----------
        uid :
            uid of particle
        uname : string
            name of particle container

        """
        return self._pc_cache[uname].get(uid)

    def update_particles(self, iterable, uname):
        """Update particles

        """
        self._pc_cache[uname].update(
            _filter_unsupported_data(iterable, self._supported_cuba))

    def add_particles(self, iterable, uname):
        """Add particles

        """
        uids = self._pc_cache[uname].add(iterable)

        # filter the cached particles of unsupported CUBA
        self._pc_cache[uname].update(_filter_unsupported_data(
            self._pc_cache[uname].iter(uids), self._supported_cuba))

        return uids

    def remove_particle(self, uid, uname):
        """Remove particle

        Parameters
        ----------
        uid :
            uid of particle
        uname : string
            name of particle container

        """
        self._pc_cache[uname].remove([uid])

    def has_particle(self, uid, uname):
        """Has particle

        Parameters
        ----------
        uid :
            uid of particle
        uname : string
            name of particle container

        """
        return self._pc_cache[uname].has(uid)

    def iter_particles(self, uname, uids=None):
        """Iterate over the particles of a certain type

        Parameters
        ----------
        uids : list of particle uids
            sequence of uids of particles that should be iterated over. If
            uids is None then all particles will be iterated over.

        """
        return self._pc_cache[uname].iter(uids, item_type=CUBA.PARTICLE)

    def number_of_particles(self, uname):
        """Get number of particles in a container

        Parameters
        ----------
        uname : string
            non-changing unique name of particles

        """
        return self._pc_cache[uname].count_of(CUBA.PARTICLE)

    def flush(self, input_data_filename):
        """flush to file

        Parameters
        ----------
        input_data_filename :
            name of data-file where inform is written to
            (i.e Liggghts's input).
        """
        if self._pc_cache:
            self._write_data_file(input_data_filename)
        else:
            raise RuntimeError(
                "No particles.  Liggghts cannot run without a particle")
        # TODO handle properly when there are no particle containers
        # or when some of them do not contain any particles
        # (i.e. someone has deleted all the particles)

    def read(self, output_data_filename):
        """read from file

        Parameters
        ----------
        output_data_filename :
            name of data-file where info read from (i.e Liggghts's output).
        """
        self._update_from_liggghts(output_data_filename)

# Private methods #######################################################
    def _update_from_liggghts(self, output_data_filename):
        """read from file and update cache

        """
        assert os.path.isfile(output_data_filename)

        handler = LiggghtsSimpleDataHandler()
        parser = LiggghtsDataFileParser(handler)
        parser.parse(output_data_filename)

        interpreter = LiggghtsDataLineInterpreter(self._atom_style)

        atoms = handler.get_atoms()
        number_atom_types = handler.get_number_atom_types()
        velocities = handler.get_velocities()
        masses = handler.get_masses()

        assert(len(atoms) == len(velocities))

        type_data = {}

        for atom_type in range(1, number_atom_types+1):
            type_data[atom_type] = DataContainer()

        for atom_type, mass in masses.iteritems():
            type_data[atom_type][CUBA.MASS] = mass

        # update each particle container with these
        # material-specific attributes
        # TODO updating the material_type from Liggghts should possibly be
        # removed as Liggghts is not going to change it
        for _, pc in self._pc_cache.iteritems():
            data = type_data[pc.data[CUBA.MATERIAL_TYPE]]
            for key, value in data.iteritems():
                pc.data[key] = value

        for liggghts_id, values in atoms.iteritems():
            uname, uid = self._liggghtsid_to_uid[liggghts_id]
            cache_pc = self._pc_cache[uname]
            p = cache_pc.get(uid)
            p.coordinates, p.data = interpreter.convert_atom_values(values)
            p.data.update(
                interpreter.convert_velocity_values(velocities[liggghts_id]))

            cache_pc.update_particles([p])

            # TODO #9 (removing material type
            atom_type = p.data[CUBA.MATERIAL_TYPE]
            del p.data[CUBA.MATERIAL_TYPE]

            # set the pc's material type
            # (current requirement/assumption is that each
            # pc has particle containers of one type)
            # (also related to #9)
            cache_pc.data[CUBA.MATERIAL_TYPE] = atom_type

    def _write_data_file(self, filename):
        """ Write data file containing current state of simulation

        """
        # recreate (and store) map from Liggghts-id to simphony-id
        self._liggghtsid_to_uid = {}

        # determine the number of particles
        # and collect the different material types
        # in oder to determine the number of types
        num_particles = sum(
            pc.count_of(
                CUBA.PARTICLE) for pc in self._pc_cache.itervalues())
        types = set(pc.data[CUBA.MATERIAL_TYPE]
                    for pc in self._pc_cache.itervalues())

        box = get_box([de for _, de in self._dc_extension_cache.iteritems()])

        mass = self._get_mass() \
            if ATOM_STYLE_DESCRIPTIONS[self._atom_style].has_mass_per_type \
            else None
        writer = LiggghtsDataFileWriter(filename,
                                        atom_style=self._atom_style,
                                        number_atoms=num_particles,
                                        number_atom_types=len(types),
                                        simulation_box=box,
                                        material_type_to_mass=mass)
        for uname, pc in self._pc_cache.iteritems():
            material_type = pc.data[CUBA.MATERIAL_TYPE]
            for p in pc.iter_particles():
                liggghts_id = writer.write_atom(p, material_type)
                self._liggghtsid_to_uid[liggghts_id] = (uname, p.uid)
        writer.close()

    def _get_mass(self):
        """ Get a dictionary from 'material type' to 'mass'.

        Check that fits what Liggghts can handle as well
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
        for uname, pc in self._pc_cache.iteritems():
            data = pc.data
            material_type = data[CUBA.MATERIAL_TYPE]
            if material_type in mass:
                # check that mass is consistent with an matching type
                if data[CUBA.MASS] != mass[material_type]:
                    raise RuntimeError(
                        "Each material type must have the same mass")
            else:
                mass[material_type] = data[CUBA.MASS]
        return mass
