from unittest import TestCase
from orcid2vivo_app.utility import clean_orcid, is_valid_orcid


class TestUtility(TestCase):

    def test_clean_orcid(self):
        orcid = '0000-0003-1527-0030'

        # Test with orcid.org prefix.
        self.assertEqual(clean_orcid('orcid.org/' + orcid), orcid)

        # Test without prefix.
        self.assertEqual(clean_orcid(orcid), orcid)

    def test_is_valid_orcid(self):
        self.assertTrue(is_valid_orcid("0000-0003-1527-0030"))
        self.assertTrue(is_valid_orcid("0000-0003-1527-003X"))
        self.assertFalse(is_valid_orcid("0000-0003-1527-00301"))
        self.assertFalse(is_valid_orcid("0000-0003-1527-003"))