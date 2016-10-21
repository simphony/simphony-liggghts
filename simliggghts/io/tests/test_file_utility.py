import unittest
import tempfile
import shutil
import os

from numpy.testing import assert_almost_equal

from simphony.core.cuba import CUBA
from simphony.core.cuds_item import CUDSItem
from simphony.core.keywords import KEYWORDS

from simliggghts.io.file_utility import (read_data_file,
                                         write_data_file)
from simliggghts.cuba_extension import CUBAExtension
from simliggghts.common.atom_style import AtomStyle
from simliggghts.common.atom_style_description import get_attributes


class TestFileUtility(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tear_down(self):
        shutil.rmtree(self.temp_dir)

    def _write_example_file(self, contents):
        filename = os.path.join(self.temp_dir, "test_data.txt")
        with open(filename, "w") as text_file:
            text_file.write(contents)
        return filename

    def test_read_sphere_style_data_file(self):
        # when
        particles_list = read_data_file(self._write_example_file(
            _explicit_sphere_style_file_contents))

        # then
        self.assertEqual(2, len(particles_list))

        particles1 = particles_list[0]
        particles2 = particles_list[1]
        self.assertEqual(2, particles1.count_of(CUDSItem.PARTICLE))
        self.assertEqual(1, particles2.count_of(CUDSItem.PARTICLE))
        self.assertEqual(str(particles1.data[CUBA.MATERIAL_TYPE]),
                         particles1.name)
        assert_almost_equal(
            particles1.data_extension[CUBAExtension.BOX_ORIGIN],
            (-10.0, -7.500, -0.500))
        box = [(25.0, 0.0, 0.0),
               (0.0, 15.0, 0.0),
               (0.0, 0.0, 1.0)]
        assert_almost_equal(
            particles1.data_extension[CUBAExtension.BOX_VECTORS],
            box)

        for p in particles1.iter_particles():
            assert_almost_equal(p.data[CUBA.ANGULAR_VELOCITY], [0.0, 0.0, 1.0])
            assert_almost_equal(p.data[CUBA.VELOCITY], [5.0, 0.0, 0.0])
            assert_almost_equal(p.data[CUBA.RADIUS], 0.5/2)
            assert_almost_equal(p.data[CUBA.DENSITY], 1.0)

    def test_write_file_sphere(self):
        # given
        original_particles_list = read_data_file(self._write_example_file(
            _explicit_sphere_style_file_contents))
        output_filename = os.path.join(self.temp_dir, "output.txt")

        # when
        write_data_file(filename=output_filename,
                        particles_list=original_particles_list,
                        atom_style=AtomStyle.GRANULAR)

        # then
        read_particles_list = read_data_file(output_filename)
        self.assertEqual(len(original_particles_list),
                         len(read_particles_list))

        _compare_list_of_named_particles(read_particles_list,
                                         original_particles_list,
                                         get_attributes(
                                             AtomStyle.GRANULAR),
                                         self)


def _compare_list_of_named_particles(read_particles_list,
                                     reference_particles_list,
                                     attributes_keys, testcase):
    for particles in read_particles_list:
        for reference in reference_particles_list:
            if reference.name == particles.name:
                _compare_particles_averages(particles,
                                            reference,
                                            attributes_keys,
                                            testcase)


def _compare_particles_averages(particles,
                                reference,
                                attributes_keys,
                                testcase):
    """  Compares average values (velocity, etc) of two Particles

    This comparison compares the average values of two Particles, which is
    useful when comparing two Particles who are representing the same thing but
    whose particle id's are different.

    """
    self = testcase

    len_particles = particles.count_of(CUDSItem.PARTICLE)
    len_reference = reference.count_of(CUDSItem.PARTICLE)
    self.assertEqual(len_particles, len_reference)
    for key in attributes_keys:
        average_particles = _get_average_value(particles, key)
        average_reference = _get_average_value(reference, key)
        assert_almost_equal(average_particles, average_reference)


def _get_average_value(particles, key):
    length = particles.count_of(CUDSItem.PARTICLE)

    keyword = KEYWORDS[CUBA(key).name]
    if keyword.shape == [1]:
        return sum(p.data[key] for p in particles.iter_particles())/length
    else:
        return tuple(map(lambda y: sum(y) / float(len(y)), zip(
            *[p.data[key] for p in particles.iter_particles()])))


_explicit_sphere_style_file_contents = """LIGGGHTS data file via write_data, version 28 Jun 2014, timestep = 25000

3 atoms
2 atom types

-10.0000000000000000e+00 15.0000000000000000e+00 xlo xhi
-7.5000000000000000e+00 7.5000000000000000e+00 ylo yhi
-5.0000000000000000e-01 5.0000000000000000e-01 zlo zhi

Atoms # granular

1 1 0.5 1.0000000000000000e+00 -5.0 0.0 0.0000000000000000e+00 0 0 0
2 2 0.5 1.0000000000000000e+00 10.0 0.0 0.0000000000000000e+00 0 0 0
3 1 0.5 1.0000000000000000e+00 10.43330 0.25000 0.0000000000000000e+00 0 0 0

Velocities

1 5.0 0.0 0.0 0.0 0.0 1.0
2 5.0 0.0 0.0 0.0 0.0 1.0
3 5.0 0.0 0.0 0.0 0.0 1.0
"""

if __name__ == '__main__':
    unittest.main()
