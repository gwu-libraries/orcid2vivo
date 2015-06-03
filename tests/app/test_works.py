from unittest import TestCase
import json
import app.works as works
import app.vivo_namespace as ns
from rdflib import Graph

class TestWorks(TestCase):

    def setUp(self):
        self.graph = Graph(namespace_manager=ns.ns_manager)
        self.person_uri = ns.D["test"]

    def test_no_actitivities(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-activities": null
    }
}
        """)
        works.crosswalk_works(orcid_profile, self.person_uri, self.graph)
        self.assertEqual(0, len(self.graph))

    def test_no_works(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-activities": {
            "orcid-works": null
        }
    }
}
        """)
        works.crosswalk_works(orcid_profile, self.person_uri, self.graph)
        self.assertEqual(0, len(self.graph))
