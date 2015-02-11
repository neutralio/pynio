import unittest
from pynio.block import Block
from unittest.mock import MagicMock

class TestBlock(unittest.TestCase):

        def test_block(self):
            b = Block('name', 'type')
            self.assertEqual(b.name, 'name')
            self.assertEqual(b.type, 'type')

        def test_save(self):
            b = Block('name', 'type')
            b._config = {'key': 'val'}
            b._instance = MagicMock()
            b._put = MagicMock()
            b.save()
            self.assertEqual(b._put.call_args[0][0], 'blocks/name')
            self.assertDictEqual(b._put.call_args[0][1],
                                 {'name': 'name',
                                  'type': 'type',
                                  'key': 'val'})
