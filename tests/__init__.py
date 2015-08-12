import logging
import unittest
import os

FIXTURE_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'fixtures'
)


class TestCase(unittest.TestCase):
    logging.basicConfig(level=logging.DEBUG)