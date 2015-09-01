from unittest import TestCase
from orcid2vivo_app.utility import clean_orcid


class TestUtility(TestCase):

    def test_clean_orcid(self):
        orcid = '0000-0003-1527-0030'

        # Test with orcid.org prefix.
        self.assertEqual(clean_orcid('orcid.org/' + orcid), orcid)

        # Test without prefix.
        self.assertEqual(clean_orcid(orcid), orcid)
