from simphony.core.cuba import CUBA
from simphony.cuds.abc_particles import ABCParticles


class LiggghtsParticles(ABCParticles):
    """ Responsible class to synchronize operations on particles

    Attributes
    ----------
    name : string
        name of particles
    data : DataContainer
        holds data
    data_extension : dict
        holds non-approved CUBA keywords

    """
    def __init__(self, manager, uname):
        # most of the work is delegated here to this manger
        self._manager = manager
        self._uname = uname

    @property
    def name(self):
        return self._manager.get_name(self._uname)

    @name.setter
    def name(self, value):
        self._manager.rename(self._uname, value)

    @property
    def data(self):
        return self._manager.get_data(self._uname)

    @data.setter
    def data(self, value):
        self._manager.set_data(value, self._uname)

    @property
    def data_extension(self):
        return self._manager.get_data_extension(self._uname)

    @data_extension.setter
    def data_extension(self, value):
        self._manager.set_data_extension(value, self._uname)

    # Particle methods ######################################################

    def _add_particles(self, iterable):
        """Adds a set of particles from the provided iterable
        to the container.

        If any particle have no uids, the container
        will generate a new uids for it. If the particle has
        already an uids, it won't add the particle if a particle
        with the same uid already exists. If the user wants to replace
        an existing particle in the container there is an 'update_particles'
        method for that purpose.

        Parameters
        ----------
        iterable : iterable of Particle objects
            the new set of particles that will be included in the container.

        Returns
        -------
        uids : list of uuid.UUID
            The uids of the added particles.

        Raises
        ------
        ValueError :
            when there is a particle with an uids that already exists
            in the container.
        """
        return self._manager.add_particles(iterable, self._uname)

    def _update_particles(self, iterable):
        """Update particles

        """
        self._manager.update_particles(iterable, self._uname)

    def _get_particle(self, uid):
        """Get particle

        """
        return self._manager.get_particle(uid, self._uname)

    def _remove_particles(self, uids):
        """Remove particles

        """
        for uid in uids:
            self._manager.remove_particle(uid, self._uname)

    def _has_particle(self, uid):
        """Has particle

        """
        return self._manager.has_particle(uid, self._uname)

    def _iter_particles(self, uids=None):
        """Get iterator over particles

        """
        for p in self._manager.iter_particles(self._uname, uids):
            yield p

    # Bond methods #######################################################

    def _add_bonds(self, bonds):
        """Add bonds

        """
        raise NotImplementedError

    def _update_bonds(self, bonds):
        """Update particle

        """
        raise NotImplementedError

    def _get_bond(self, uid):
        """Get bond

        """
        raise KeyError("get bond not implemented. "
                       "uid {} not found".format(uid))

    def _remove_bonds(self, uid):
        """Remove bond

        """
        raise KeyError("remove bond not implemented. "
                       "uid {} not found".format(uid))

    def _has_bond(self, uid):
        """Has bond

        """
        return False

    def _iter_bonds(self, uids=None):
        """Get iterator over bonds

        """
        for _ in []:
            yield _

    # count methods #######################################################
    def count_of(self, item_type):
        """ Return the count of item_type in the container.

        Parameters
        ----------
        item_type : CUBA enum
            The CUBA enum of the type of the items to return the count of.

        Returns
        -------
        count : int
            The number of items of item_type in the container.

        Raises
        ------
        ValueError :
            If the type of the item is not supported in the current
            container.

        """
        if item_type == CUBA.PARTICLE:
            return self._manager.number_of_particles(self._uname)
        elif item_type == CUBA.BOND:
            return 0
        else:
            error_str = "Trying to obtain count a of non-supported item: {}"
            raise ValueError(error_str.format(item_type))
