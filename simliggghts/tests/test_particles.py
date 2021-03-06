import unittest

from simphony.cuds.particles import Particles
from simphony.core.cuba import CUBA
from simphony.testing.abc_check_particles import (
    CheckAddingParticles, CheckManipulatingParticles)
from simphony.testing.utils import create_particles_with_id

from simliggghts.liggghts_wrapper import LiggghtsWrapper
from simliggghts.testing.md_example_configurator import MDExampleConfigurator

# list of CUBA that is supported/needed by particles in LIGGGHTS
_SUPPORTED_CUBA =\
    [CUBA.VELOCITY,
     CUBA.ANGULAR_VELOCITY,
     CUBA.DENSITY,
     CUBA.RADIUS,
     CUBA.EXTERNAL_APPLIED_FORCE]
#     CUBA.MASS]


class TestFileIoParticlesAddParticles(
        CheckAddingParticles, unittest.TestCase):

    def supported_cuba(self):
        return _SUPPORTED_CUBA

    def container_factory(self, name):
        return self.pc

    def setUp(self):
        self.wrapper = LiggghtsWrapper(use_internal_interface=False)
        MDExampleConfigurator.configure_wrapper(self.wrapper)
        pcs = [pc for pc in self.wrapper.iter_datasets()]
        self.pc = pcs[0]
        CheckAddingParticles.setUp(self)

    # TODO workaround for simphony issue #202 ( simphony/simphony-common#202 )
    def test_add_multiple_particles_with_id(self):
        # given
        container = self.container
        particles = create_particles_with_id(restrict=self.supported_cuba())

        # when
        uids = container.add(particles)

        # then
        for particle in particles:
            uid = particle.uid
            self.assertIn(uid, uids)
            self.assertTrue(container.has(uid))
            self.assertEqual(container.get(uid), particle)


class TestInternalParticlesAddParticles(
        CheckAddingParticles, unittest.TestCase):

    def supported_cuba(self):
        return _SUPPORTED_CUBA

    def container_factory(self, name):
        return self.pc

    def setUp(self):
        self.wrapper = LiggghtsWrapper(use_internal_interface=True)
        MDExampleConfigurator.configure_wrapper(self.wrapper)
        pcs = [pc for pc in self.wrapper.iter_datasets()]
        self.pc = pcs[0]
        CheckAddingParticles.setUp(self)

    # TODO workaround for simphony issue #202 ( simphony/simphony-common#202 )
    def test_add_multiple_particles_with_id(self):
        # given
        container = self.container
        particles = create_particles_with_id(restrict=self.supported_cuba())

        # when
        uids = container.add(particles)

        # then
        for particle in particles:
            uid = particle.uid
            self.assertIn(uid, uids)
            self.assertTrue(container.has(uid))
            self.assertEqual(container.get(uid), particle)


class TestFileIoParticlesManipulatingParticles(
        CheckManipulatingParticles, unittest.TestCase):

    def supported_cuba(self):
        return _SUPPORTED_CUBA

    def container_factory(self, name):
        p = Particles(name="foo")
        pc_w = MDExampleConfigurator.add_configure_particles(self.wrapper,
                                                             p)
        return pc_w

    def setUp(self):
        self.wrapper = LiggghtsWrapper(use_internal_interface=False)
        MDExampleConfigurator.configure_wrapper(self.wrapper)
        CheckManipulatingParticles.setUp(self)


class TestInternalParticlesManipulatingParticles(
        CheckManipulatingParticles, unittest.TestCase):

    def supported_cuba(self):
        return _SUPPORTED_CUBA

    def container_factory(self, name):
        p = Particles(name="foo")
        pc_w = MDExampleConfigurator.add_configure_particles(self.wrapper,
                                                             p)
        return pc_w

    def setUp(self):
        self.wrapper = LiggghtsWrapper(use_internal_interface=True)
        MDExampleConfigurator.configure_wrapper(self.wrapper)
        CheckManipulatingParticles.setUp(self)


if __name__ == '__main__':
    unittest.main()
