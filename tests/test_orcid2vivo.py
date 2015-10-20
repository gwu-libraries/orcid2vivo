from unittest import TestCase
from rdflib import Graph, URIRef, RDF, OWL
import orcid2vivo_app.vivo_namespace as ns
from orcid2vivo import PersonCrosswalk
from orcid2vivo_app.vivo_namespace import VIVO


class TestPersonCrosswalk(TestCase):
    def setUp(self):
        self.graph = Graph(namespace_manager=ns.ns_manager)
        self.person_uri = ns.D["test"]
        self.orcid_id = "0000-0003-1527-0030"
        self.orcid_id_uriref = URIRef("http://orcid.org/{}".format(self.orcid_id))

    def test_add_orcid_id(self):
        PersonCrosswalk._add_orcid_id(self.person_uri, self.orcid_id, self.graph, False)
        self.assertEqual(2, len(self.graph))

        self.assertTrue((self.person_uri, VIVO.orcidId, self.orcid_id_uriref) in self.graph)
        self.assertTrue((self.orcid_id_uriref, RDF.type, OWL.Thing) in self.graph)

    def test_add_orcid_id_confirmed(self):
        PersonCrosswalk._add_orcid_id(self.person_uri, self.orcid_id, self.graph, True)
        self.assertEqual(3, len(self.graph))

        self.assertTrue((self.orcid_id_uriref, VIVO.confirmedOrcidId, self.person_uri) in self.graph)
