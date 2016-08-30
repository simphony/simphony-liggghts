from collections import namedtuple

import ctypes

from simphony.core.cuba import CUBA
from simphony.core.data_container import DataContainer

# name is lammps'name (e.g. "x")
# type = 0 = int or 1 = double
# count = # of per-atom values, 1 or 3, etc
_LammpsData = namedtuple(
    '_LammpsData', ['CUBA', 'lammps_name', "type", "count"])


class ParticleDataCache(object):
    """ Class handles particle-related data

    Class stores all particle-related data and has methods
    in order to retrieve this data from LAMMPS and send this
    data to LAMMPS.

    Parameters
    ----------
    lammps :
        lammps python wrapper

    """
    def __init__(self, lammps):
        self._lammps = lammps

        # TODO this should be based on what atom-style we are using
        # and configured by the user of this class (instead of
        # hard coded here)
        self._data_entries = [_LammpsData(CUBA=CUBA.VELOCITY,
                                          lammps_name="v",
                                          type=3,  # array of doubles
                                          count=3),
                              _LammpsData(CUBA=CUBA.ANGULAR_VELOCITY,
                                          lammps_name="omega",
                                          type=3,  # array of doubles
                                          count=3),
                              _LammpsData(CUBA=CUBA.DENSITY,
                                          lammps_name="density",
                                          type=2,  # vector of doubles
                                          count=1),
                              _LammpsData(CUBA=CUBA.MASS,
                                          lammps_name="rmass",
                                          type=2,  # vector of doubles
                                          count=1),
                              _LammpsData(CUBA=CUBA.RADIUS,
                                          lammps_name="radius",
                                          type=2,  # vector of doubles
                                          count=1),
                              _LammpsData(CUBA=CUBA.MATERIAL_TYPE,
                                          lammps_name="type",
                                          type=0,  # int
                                          count=1),
                              _LammpsData(CUBA=CUBA.EXTERNAL_APPLIED_FORCE,
                                          lammps_name="df",
                                          type=1,  # per-atom
                                          count=3)]  # array
        # map from uid to index in lammps arrays
        self._index_of_uid = {}

        # cache of particle-related data (stored by CUBA keyword)
        self._cache = {}

        # cache of coordinates
        self._coordinates = []

        for entry in self._data_entries:
            self._cache[entry.CUBA] = []

    def retrieve(self):
        """ Retrieve all data from lammps

        """
        natom = self._lammps.extract_global("nlocal", 0)
        pos = self._lammps.extract_atom("x", 3)
        k = 0
        for i in range(0, natom):
            for j in range(0, 3):
                self._coordinates[k] = pos[i][j]
                k += 1

        for entry in self._data_entries:
            if entry.CUBA is CUBA.EXTERNAL_APPLIED_FORCE:
                df_retrieve = self._lammps.extract_fix(entry.lammps_name, 1, 2)

                k = 0
                for i in range(0, natom):
                    for j in range(0, 3):
                        self._cache[entry.CUBA][k] = df_retrieve[i][j]
                        k += 1
            elif entry.count > 1:
                extract_prop = \
                    self._lammps.extract_atom(entry.lammps_name, entry.type)
                k = 0
                for i in range(0, natom):
                    for j in range(0, entry.count):
                        self._cache[entry.CUBA][k] = extract_prop[i][j]
                        k += 1
            else:
                extract_prop =\
                    self._lammps.extract_atom(entry.lammps_name, entry.type)
                k = 0
                for i in range(0, natom):
                    self._cache[entry.CUBA][k] = extract_prop[i]
                    k += 1

    def send(self):
        """ Send data to lammps

        """
        natom = self._lammps.extract_global("nlocal", 0)

        pos = self._lammps.extract_atom("x", 3)
        k = 0
        for i in range(0, natom):
            for j in range(0, 3):
                pos[i][j] = self._coordinates[k]
                k += 1

        for entry in self._data_entries:
            values = self._cache[entry.CUBA]
            if entry.CUBA is CUBA.EXTERNAL_APPLIED_FORCE:
                df_ext = self._lammps.extract_fix(entry.lammps_name, 1, 2)

                k = 0
                for i in range(0, natom):
                    for j in range(0, 3):
                        df_ext[i][j] = values[k]
                        k += 1
            elif entry.count > 1:
                extract_prop =\
                    self._lammps.extract_atom(entry.lammps_name, entry.type)
                k = 0
                for i in range(0, natom):
                    for j in range(0, entry.count):
                        extract_prop[i][j] = values[k]
                        k += 1
            else:
                extract_prop =\
                    self._lammps.extract_atom(entry.lammps_name, entry.type)
                k = 0
                for i in range(0, natom):
                    extract_prop[i] = values[k]
                    k += 1

    def send_radius(self):
        """ Send radius data to lammps

        """
        values = self._cache[CUBA.RADIUS]

        natom = self._lammps.extract_global("nlocal", 0)
        extract_rad = self._lammps.extract_atom("radius", 2)

        for i in range(0, natom):
            extract_rad[i] = values[i]

    def get_particle_data(self, uid):
        """ get particle data

        Parameters
        ----------
        uid : UUID
            uid for particle

        Returns
        -------
        data : DataContainer
            data of the particle
        """
        data = DataContainer()
        for entry in self._data_entries:
            i = self._index_of_uid[uid] * entry.count
            if entry.count > 1:
                # always assuming that its a tuple
                # ( see https://github.com/simphony/simphony-common/issues/18 )
                data[entry.CUBA] = tuple(
                    self._cache[entry.CUBA][i:i+entry.count])
            else:
                data[entry.CUBA] = self._cache[entry.CUBA][i]
        return data

    def set_particle(self, coordinates, data, uid):
        """ set particle coordinates and data

        Parameters
        ----------
        coordinates : tuple of floats
            particle coordinates
        data : DataContainer
            data of the particle
        uid : uuid
            uuid of the particle

        """
        if uid not in self._index_of_uid:
            self._index_of_uid[uid] = len(self._index_of_uid)

        i = self._index_of_uid[uid] * 3
        self._coordinates[i:i+3] = coordinates[0:3]

        index = self._index_of_uid[uid]
        for entry in self._data_entries:

            i = index * entry.count

            if entry.count > 1:
                self._cache[entry.CUBA][i:i+entry.count] = \
                    data[entry.CUBA][0:entry.count]
            else:
                if i < len(self._cache[entry.CUBA]):
                    self._cache[entry.CUBA][i] = data[entry.CUBA]
                elif i == len(self._cache[entry.CUBA]):
                    self._cache[entry.CUBA].append(data[entry.CUBA])
                else:
                    msg = "Problem with index {}".format(uid)
                    raise IndexError(msg)

    def get_coordinates(self, uid):
        """ Get coordinates for a particle

        Parameters
        ----------
        uid : uid
            uid of particle
        """
        i = self._index_of_uid[uid] * 3
        coords = self._coordinates[i:i+3]
        return tuple(coords)


def _get_ctype(entry):
    """ get ctype's type for entry

    Parameters
    ----------
    entry : LammpsData
        info about the atom parameter
    """
    if entry.type == 0:
        return ctypes.c_int
    elif entry.type == 1:
        return ctypes.c_double
    else:
        raise RuntimeError(
            "Unsupported type {}".format(entry.type))
