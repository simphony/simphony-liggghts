import unittest


class TestPluginIntegration(unittest.TestCase):

    def test_plugin_integration(self):

        from simphony.engine import liggghts

        self.assertTrue(hasattr(liggghts, 'LiggghtsWrapper'))


if __name__ == '__main__':
    unittest.main()
