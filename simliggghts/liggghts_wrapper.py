""" LAMMPS SimPhoNy Wrapper

This module provides a wrapper for  LAMMPS-md
"""
import contextlib
import os
import tempfile
import shutil
from enum import (IntEnum, unique)
from random import randint
from simphony.core.cuba import CUBA

from simphony.cuds.abc_modeling_engine import ABCModelingEngine
from simphony.cuds.abc_particles import ABCParticles
from simphony.core.data_container import DataContainer

from .common import globals
from .io.lammps_fileio_data_manager import LammpsFileIoDataManager
from .io.lammps_process import LammpsProcess
from .internal.lammps_internal_data_manager import (
    LammpsInternalDataManager)
from .config.script_writer import ScriptWriter
from .common.atom_style import AtomStyle
from .cuba_extension import CUBAExtension


@contextlib.contextmanager
def _temp_directory():
    """ context manager that provides temp directory

    The name of the created temp directory is returned when context is entered
    and this directory is deleted when context is exited
    """
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


class LiggghtsWrapper(ABCModelingEngine):
    """ Wrapper to LAMMPS-md


    """
    def __init__(self,use_internal_interface=False):
        """ Constructor.

        Parameters
        ----------
        engine_type : EngineType
            type of engine

        use_internal_interface : bool, optional
            If true, then the internal interface (library) is used when
            communicating with LAMMPS, if false, then file-io interface is
            used where input/output files are used to communicate with LAMMPS

        """

        self._use_internal_interface = use_internal_interface

        atom_style = AtomStyle.GRANULAR
        self._executable_name = "liggghts"
        self._script_writer = ScriptWriter(atom_style)

        if self._use_internal_interface:
            import liggghts
            self._lammps = liggghts.liggghts(cmdargs=["-screen", "none",
                                                 "-log", "none"])
            self._data_manager = LammpsInternalDataManager(self._lammps,
                                                           atom_style)
            
                
        else:
            self._data_manager = LammpsFileIoDataManager(atom_style)

        self.BC = DataContainer()
        self.CM = DataContainer()
        self.SP = DataContainer()
        self.CM_extension = {}
        self.SP_extension = {}
        self.BC_extension = {}


    def add_dataset(self, container):
        """Add a CUDS container

        Parameters
        ----------
        container : {ABCParticles}
            The CUDS container to add to the engine.

        Raises
        ------
        TypeError:
            If the container type is not supported (i.e. ABCLattice, ABCMesh).
        ValueError:
            If there is already a dataset with the given name.

        """
        
        
        if not isinstance(container, ABCParticles):
            raise TypeError(
                "The type of the dataset container is not supported")

        if container.name in self._data_manager:
            raise ValueError(
                'Particle container \'{}\' already exists'.format(
                    container.name))
        else:
            self._data_manager.new_particles(container)
            
        #if container.data[CUBA.MATERIAL_TYPE] not in set(types) and len(types) > 0:
           #globals.MAX_NUMBER_TYPES += 1
            



    def get_dataset(self, name):
        """ Get the dataset

        The returned particle container can be used to query
        and change the related data inside LAMMPS.

        Parameters
        ----------
        name: str
            name of CUDS container to be retrieved.

        Returns
        -------
        container :
            A proxy of the dataset named ``name`` that is stored
            internally in the Engine.

        Raises
        ------
        ValueError:
            If there is no dataset with the given name

        """
        if name in self._data_manager:
            return self._data_manager[name]
        else:
            raise ValueError(
                'Particle container \'{}\` does not exist'.format(name))

    def get_dataset_names(self):
        """ Returns the names of all the datasets

        """
        # TODO  (simphony-common #218)
        return [name for name in self._data_manager]

    def remove_dataset(self, name):
        """ Remove a dataset

        Parameters
        ----------
        name: str
            name of CUDS container to be deleted

        Raises
        ------
        ValueError:
            If there is no dataset with the given name

        """
        if name in self._data_manager:
            del self._data_manager[name]
        else:
            raise ValueError(
                'Particles \'{}\' does not exist'.format(name))

    def iter_datasets(self, names=None):
        """ Returns an iterator over a subset or all of the containers.

        Parameters
        ----------
        names : sequence of str, optional
            names of specific containers to be iterated over. If names is not
            given, then all containers will be iterated over.

        """
        if names is None:
            for name in self._data_manager:
                yield self._data_manager[name]
        else:
            for name in names:
                if name in self._data_manager:
                    yield self._data_manager[name]
                else:
                    raise ValueError(
                        'Particle container \'{}\` does not exist'.format(
                            name))

    def run(self):
        """ Run lammps-engine based on configuration and data

        """

        if self._use_internal_interface:
         
            commands = ""
            
            if globals.INITIAL_RUN:
             
                for name in self._data_manager:
                  partcont = self.get_dataset(name)
             
                self.SP_extension[CUBAExtension.BOX_VECTORS] = partcont.data_extension[CUBAExtension.BOX_VECTORS]
                self.SP_extension[CUBAExtension.BOX_ORIGIN] = partcont.data_extension[CUBAExtension.BOX_ORIGIN]
                
                
                ScriptWriter.check_configuration_SP(_combine(self.SP, self.SP_extension))
                ScriptWriter.check_configuration_BC(_combine(self.BC, self.BC_extension))
                ScriptWriter.check_configuration_CM(_combine(self.CM, self.CM_extension))
                
                
                
                # Flush radius once to give lammps the required information for cutoff distances
                self._data_manager.flush_radius()

  
                commands = ""
                
                commands += ScriptWriter.get_ext_forces(self)
                
                #commands += "pair_style gran model hertz tangential history\n"
                commands += ScriptWriter.get_pair_style_liggghts(_combine(self.SP, self.SP_extension))
                
                commands += "pair_coeff      * *\n"
                
                commands += ScriptWriter.get_material_data(_combine(self.SP, self.SP_extension))
                
                commands += "run 0"
                
                for command in commands.splitlines():
                    #print command
                    self._lammps.command(command)
            

                # TODO this has to be rewritten as
                # we only want to send configuration commands
                # once (or after whenever they change) but we want
                # to send the the 'run' command each time
                
                #commands += ScriptWriter.get_pair_style(
                  #_combine(self.SP, self.SP_extension))
                
            
                commands = ""
                commands += ScriptWriter.get_boundary(_combine(self.BC,self.BC_extension),
                    change_existing_boundary=True)
                
                commands += "fix 1 all nve\n"

                commands += ScriptWriter.get_box_planes(_combine(self.SP, self.SP_extension), \
                    _combine(self.BC,self.BC_extension))
                
                commands += ScriptWriter.get_fixed_groups(_combine(self.BC,self.BC_extension))
                
                commands += "group group_1 type 1\n"
                commands += "dump 1 all custom %i test.traj id type x y z vx vy radius" % self.CM[CUBA.NUMBER_OF_TIME_STEPS]
                
                globals.INITIAL_RUN = 0
                
                for command in commands.splitlines():
                  #print command
                  self._lammps.command(command)

            #stop
            # before running, we flush any changes to lammps
            self._data_manager.flush()
            
            commands = ""
            commands += ScriptWriter.get_run(CM=_combine(self.CM,self.CM_extension))
            
            for command in commands.splitlines():
                #print command
                self._lammps.command(command)
  
            # after running, we read any changes from lammps
            # TODO rework
            self._data_manager.read()
            
        else:
         
            with _temp_directory() as temp_dir:
                input_data_filename = os.path.join(
                    temp_dir, "data_in.lammps")
                output_data_filename = os.path.join(
                    temp_dir, "data_out.lammps")

                # before running, we flush any changes to lammps
                self._data_manager.flush(input_data_filename)
                
                for name in self._data_manager:
                    partcont = self.get_dataset(name)
                    
                    #yield self._data_manager[name]
                self.SP_extension[CUBAExtension.BOX_VECTORS] = partcont.data_extension[CUBAExtension.BOX_VECTORS]
                self.SP_extension[CUBAExtension.BOX_ORIGIN] = partcont.data_extension[CUBAExtension.BOX_ORIGIN]

                #stop
                commands = self._script_writer.get_configuration(
                    input_data_file=input_data_filename,
                    output_data_file=output_data_filename,
                    BC=_combine(self.BC, self.BC_extension),
                    CM=_combine(self.CM, self.CM_extension),
                    SP=_combine(self.SP, self.SP_extension))
                process = LammpsProcess(lammps_name=self._executable_name,
                                        log_directory=temp_dir)
                process.run(commands)
                

                # after running, we read any changes from lammps
                self._data_manager.read(output_data_filename)


def _combine(data_container, data_container_extension):
    """ Combine a the approved CUBA with non-approved CUBA key-values

    Parameters
    ----------
    data_container : DataContainer
        data container with CUBA attributes
    data_container_extension : dict
        data container with non-approved CUBA attributes

    Returns
    ----------
    dict
        dictionary containing the approved adn non-approved
        CUBA key-values

    """
    result = dict(data_container_extension)
    result.update(data_container)
    return result
   
