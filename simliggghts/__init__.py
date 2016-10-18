from .liggghts_wrapper import LiggghtsWrapper
from .cuba_extension import CUBAExtension
from .io.file_utility import read_data_file

__all__ = ["LiggghtsWrapper", "CUBAExtension", "read_data_file"]

from simphony.engine import ABCEngineExtension
from simphony.engine import EngineInterface
from simphony.engine.decorators import register

from .liggghts_wrapper import LiggghtsWrapper
from .cuba_extension import CUBAExtension
from .io.file_utility import read_data_file

__all__ = ["LiggghtsWrapper", "EngineType", "CUBAExtension", 'read_data_file']


@register
class SimliggghtsExtension(ABCEngineExtension):
    """Simphony-liggghts extension.

    This extension provides support for liggghts engines.
    """

    def get_supported_engines(self):
        """Get metadata about supported engines.

        Returns
        -------
        list: a list of EngineMetadata objects
        """
        # TODO: Add proper features as soon as the metadata classes are ready.
        # liggghts_features =\
        #     self.create_engine_metadata_feature(GranularDynamics(),
        #                                         [DEM()])
        liggghts_features = None
        liggghts = self.create_engine_metadata('LIGGGHTS',
                                               liggghts_features,
                                               [EngineInterface.FileIO])
        return [liggghts]

    def create_wrapper(self, cuds, engine_name, engine_interface):
        """Creates a wrapper to the requested engine.

        Parameters
        ----------
        cuds: CUDS
          CUDS computational model data
        engine_name: str
          name of the engine, must be supported by this extension
        engine_interface: EngineInterface
          the interface to interact with engine

        Returns
        -------
        ABCEngineExtension: A wrapper configured with cuds and ready to run
        """
        use_internal_interface = False
        if engine_interface == EngineInterface.Internal:
            use_internal_interface = True

        if engine_name != 'LIGGGHTS':
            raise Exception('Only LIGGGHTS engine is supported. '
                            'Unsupported eninge: %s', engine_name)

        return LiggghtsWrapper(cuds=cuds,
                       	       use_internal_interface=use_internal_interface)
