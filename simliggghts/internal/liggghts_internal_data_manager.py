import uuid

from simphony.core.cuba import CUBA
from simphony.core.data_container import DataContainer
from simphony.cuds.particles import Particle

from ..common import globals
from ..config.domain import get_box
from .particle_data_cache import ParticleDataCache
from ..abc_data_manager import ABCDataManager
from ..cuba_extension import CUBAExtension
from ..config.script_writer import ScriptWriter


class LiggghtsInternalDataManager(ABCDataManager):
    """  Class managing LIGGGHTS data information using file-io

    The class performs communicating the data to and from LIGGGHTS using the
    internal interface (i.e. LIGGGHTS shared library).

    Parameters
    ----------
    liggghts :
        liggghts python wrapper
    atom_style : AtomStyle
           atom_style
    """
    def __init__(self, liggghts, atom_style):
        super(LiggghtsInternalDataManager, self).__init__()

        self._liggghts = liggghts

        dummy_bc = {CUBAExtension.BOX_FACES: ("periodic",
                                              "periodic",
                                              "periodic")}

        # create initial box with dummy values
        vectors = [(25.0, 0.0, 0.0),
                   (0.0, 22.0, 0.0),
                   (0.0, 0.0, 6.196)]
        dummy_box_data = {CUBAExtension.BOX_VECTORS: vectors,
                          CUBAExtension.BOX_ORIGIN: (0.0, 0.0, 0.0)}

        commands = "dimension 3\n"
        script_writer = ScriptWriter(atom_style)
        commands += script_writer.get_initial_setup()

        commands += ScriptWriter.get_boundary(dummy_bc)

        commands += "newton          off\n"
        commands += "communicate     single vel yes\n"

        commands += get_box([dummy_box_data], command_format=True)

        commands += "create_box {} box\n".format(globals.MAX_NUMBER_TYPES)

        for command in commands.splitlines():
            self._liggghts.command(command)

        # map from uname of Particles to Set of (particle) uids
        self._particles = {}

        # cache of coordinates and point data
        self._particle_data_cache = ParticleDataCache(liggghts=self._liggghts)

        # cache of particle containers's data
        self._pc_data = {}
        self._pc_data_extension = {}

    def get_data(self, uname):
        """Returns data container associated with particle container

        Parameters
        ----------
        uname : string
            non-changing unique name of particles

        """
        return DataContainer(self._pc_data[uname])

    def set_data(self, data, uname):
        """Sets data container associated with particle container

        Parameters
        ----------
        uname : string
            non-changing unique name of particles

        """

        self._pc_data[uname] = DataContainer(data)

    def get_data_extension(self, uname):
        """Returns data container extension associated with particle container

        Parameters
        ----------
        uname : string
            non-changing unique name of particles

        """

        return dict(self._pc_data_extension[uname])

    def set_data_extension(self, data, uname):
        """Sets data container extension associated with particle container

        Parameters
        ----------
        uname : string
            non-changing unique name of particles

        """

        self._pc_data_extension[uname] = dict(data)

    def _handle_delete_particles(self, uname):
        """Handle when a Particles is deleted

        Parameters
        ----------
        uname : string
            non-changing unique name of particles

        """
        uids_to_be_deleted = [uid for uid in self._particles[uname]]

        for uid in uids_to_be_deleted:
            self.remove_particle(uid, uname)

        del self._pc_data[uname]
        del self._pc_data_extension[uname]
        del self._particles[uname]

    def _handle_new_particles(self, uname, particles):
        """Add new particle container to this manager.

        Parameters
        ----------
        uname : string
            non-changing unique name of particles
        particles : ABCParticles
            particle container to be added

        """

        self._particles[uname] = set()

        self._pc_data[uname] = DataContainer(particles.data)

        if hasattr(particles, 'data_extension'):
            self._pc_data_extension[uname] = dict(particles.data_extension)
        else:
            # create empty dc extension
            self._pc_data_extension[uname] = {}

        self._update_simulation_box()

        # TODO have uniform way to check what is needed
        # and perform a check at a different spot.
        if CUBA.MATERIAL_TYPE not in self._pc_data[uname]:
            raise ValueError("Missing the required CUBA.MATERIAL_TYPE")

        self._add_atoms(iterable=particles.iter(item_type=CUBA.PARTICLE),
                        uname=uname,
                        safe=True)

    def _update_simulation_box(self):
        """Update simulation box

        """
        cmd = get_box([de for _, de in self._pc_data_extension.iteritems()],
                      command_format=True,
                      change_existing=True)
        self._liggghts.command(cmd)

    def get_particle(self, uid, uname):
        """Get particle

        Parameters
        ----------
        uid :
            uid of particle
        uname : string
            name of particle container

        """
        if uid in self._particles[uname]:
            coordinates = self._particle_data_cache.get_coordinates(uid)
            data = self._particle_data_cache.get_particle_data(uid)

            # TODO removing type from data as it not kept as a per-particle
            # data but currently it is on the container.
            # In liggghts it is only stored as a per-atom based attribute.
            # This should be changed once #9 issue is addressed
            del data[CUBA.MATERIAL_TYPE]

            p = Particle(uid=uid,
                         coordinates=coordinates,
                         data=data)
            return p
        else:
            raise KeyError("uid ({}) was not found".format(uid))

    def update_particles(self, iterable, uname):
        """Update particles

        """
        for particle in iterable:
            if particle.uid in self._particles[uname]:
                self._set_particle(particle, uname)
            else:
                raise ValueError(
                    "particle id ({}) was not found".format(particle.uid))

    def add_particles(self, iterable, uname):
        """Add particle

        """
        return self._add_atoms(iterable, uname, safe=False)

    def remove_particle(self, deleted_uid, uname):
        """Remove particle

        Parameters
        ----------
        uid :
            uid of particle
        uname : string
            non-changing unique name of particles

        """

        # remove the deleted id from our book keeping
        self._particles[uname].remove(deleted_uid)

        # Make a local copy of ALL the particles EXCEPT for the deleted one
        saved_particles = {}
        for uname in self._particles:
            saved_particles[uname] = {}
            for uid in self._particles[uname]:
                coordinates = self._particle_data_cache.get_coordinates(uid)
                data = self._particle_data_cache.get_particle_data(uid)

                p = Particle(uid=uid,
                             coordinates=coordinates,
                             data=data)
                saved_particles[uname][uid] = p

        self._liggghts.command("delete_atoms group all compress yes")

        # Use the new cache
        self._particle_data_cache = ParticleDataCache(liggghts=self._liggghts)

        # re-add the saved atoms
        for uname in saved_particles:
            self._add_atoms(saved_particles[uname].values(), uname, safe=True)

    def has_particle(self, uid, uname):
        """Has particle

        Parameters
        ----------
        uid :
            uid of particle
        uname : string
            non-changing unique name of particles

        """
        return uid in self._particles[uname]

    def iter_particles(self, uname, uids=None):
        """Iterate over the particles of a certain type

        Parameters
        ----------
        uids : list of particle uids
            sequence of uids of particles that should be iterated over. If
            uids is None then all particles will be iterated over.
        uname : string
            non-changing unique name of particles

        """
        if uids:
            for uid in uids:
                yield self.get_particle(uid, uname)
        else:
            for uid in self._particles[uname]:
                yield self.get_particle(uid, uname)

    def number_of_particles(self, uname):
        """Get number of particles in a container

        Parameters
        ----------
        uname : string
            non-changing unique name of particles

        """
        return len(self._particles[uname])

    def read(self):
        """read latest state

        """
        self._update_from_liggghts()

    def flush(self):
        """flush state

        """
        if self._pc_data:
            # update particles (container)'s data
            # (updating only MASS at the moment as MATERIAL_TYPE is sent as a
            # particle-based attribute to LIGGGHTS even though in SimPhoNy its
            # a container-based attribute)

            # update the particle-data
            self._particle_data_cache.send()

        else:
            raise RuntimeError(
                "No particles.  Liggghts cannot run without a particle")
        # TODO handle properly when there are no particle containers
        # or when some of them do not contain any particles
        # (i.e. someone has deleted all the particles)

    def flush_radius(self):
        """flush radius state

        """
        if self._pc_data:

            # update the particle-data
            self._particle_data_cache.send_radius()
        else:
            raise RuntimeError(
                "No particles.  Liggghts cannot run without a particle")

    def _update_from_liggghts(self):
        self._particle_data_cache.retrieve()

    def _set_particle(self, particle, uname):
        """ Set coordinates and data for a particle

        Parameters
        ----------
        particle : Particle
            particle to be set
        uname : string
            non-changing unique name of particle container

        """
        # TODO using type from container.  in liggghts it is only
        # stored as a per-atom based attribute.
        # this should be changed once #9 issue is addressed
        p_type = self._pc_data[uname][CUBA.MATERIAL_TYPE]
        data = DataContainer(particle.data)
        data[CUBA.MATERIAL_TYPE] = p_type

        # Update of mass, since this value is related to density
        data[CUBA.MASS] = data[CUBA.RADIUS] * data[CUBA.RADIUS] *\
            data[CUBA.RADIUS] *\
            4.0 / 3.0 * 3.141592654 * data[CUBA.DENSITY]

        self._particle_data_cache.set_particle(particle.coordinates,
                                               data,
                                               particle.uid)

    def _add_atoms(self, iterable, uname, safe=False):
        """ Add multiple particles as atoms to liggghts

        The number of atoms to be added are randomly added somewhere
        in the simulation box by LIGGGHTS and then their positions (and
        other values are corrected/updated)

        Parameters
        ----------
        iterable : iterable of Particle objects
            particle with CUBA.MATERIAL_TYPE

        uname : str
            non-changing unique name of particle container

        safe : bool
            True if uids do not need to be to be checked (e.g.. in the
            case that all particles are being added to an empty particle
            container). False if uids need to be checked.

        Returns
        -------
        uuid : list of UUID4
            uids of added particles

        """
        p_type = self._pc_data[uname][CUBA.MATERIAL_TYPE]

        uids = []
        for particle in iterable:
            if particle.uid is None:
                particle.uid = uuid.uuid4()

            if not safe and particle.uid in self._particles[uname]:
                raise ValueError(
                    "particle with same uid ({}) already exists".format(
                        particle.uid))

            self._particles[uname].add(particle.uid)
            self._set_particle(particle, uname)

            uids.append(particle.uid)

        # create atoms in liggghts
        self._liggghts.command(
            "create_atoms {} random {} 42 NULL".format(p_type, len(uids)))

        return uids
