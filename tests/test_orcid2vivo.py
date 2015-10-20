from unittest import TestCase
from rdflib import Graph, URIRef, RDF, OWL
import orcid2vivo_app.vivo_namespace as ns
from orcid2vivo import PersonCrosswalk
from orcid2vivo_app.vivo_namespace import VIVO


class TestPersonCrosswalk(TestCase):
    def setUp(self):
        self.graph = Graph(namespace_manager=ns.ns_manager)
        self.person_uri = ns.D["test"]

    def test_add_orcid_id(self):
        orcid_id = "0000-0003-1527-0030"
        PersonCrosswalk._add_orcid_id(self.person_uri, orcid_id, self.graph)
        self.assertEqual(2, len(self.graph))
        orcid_id_uriref = URIRef("http://orcid.org/{}".format(orcid_id))
        self.assertTrue((self.person_uri, VIVO.orcidId, orcid_id_uriref) in self.graph)
        self.assertTrue((orcid_id_uriref, RDF.type, OWL.Thing) in self.graph)

