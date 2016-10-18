import unittest
import shutil
import tempfile

from simliggghts.io.liggghts_process import LiggghtsProcess


class TestLiggghtsProcess(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.liggghts = LiggghtsProcess(log_directory=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_run_hello_world(self):
        command = "print \"hello world\""
        self.liggghts.run(command)

    def test_run_problem(self):
        command = "thisisnotaliggghtscommmand"
        with self.assertRaises(RuntimeError):
            self.liggghts.run(command)

    def test_cannot_find_liggghts(self):
        liggghts_name = "this_is_not_liggghts"
        with self.assertRaises(RuntimeError):
            self.liggghts = LiggghtsProcess(liggghts_name=liggghts_name)


if __name__ == '__main__':
    unittest.main()
