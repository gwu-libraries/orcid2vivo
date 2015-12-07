from unittest import TestCase
from tests import FIXTURE_PATH
from orcid2vivo_app.fundings import FundingCrosswalk
import orcid2vivo
import orcid2vivo_app.vivo_namespace as ns
from orcid2vivo_app.vivo_uri import HashIdentifierStrategy
from orcid2vivo import SimpleCreateEntitiesStrategy

from rdflib import Graph, RDFS
import vcr

my_vcr = vcr.VCR(
    cassette_library_dir=FIXTURE_PATH,
)


class TestFundings(TestCase):

    def setUp(self):
        self.graph = Graph(namespace_manager=ns.ns_manager)
        self.person_uri = ns.D["test"]
        self.create_strategy = SimpleCreateEntitiesStrategy(HashIdentifierStrategy(), person_uri=self.person_uri)
        self.crosswalker = FundingCrosswalk(identifier_strategy=self.create_strategy,
                                        create_strategy=self.create_strategy)


    @my_vcr.use_cassette('fundings/no.yaml')
    def test_no_funding(self):
        profile = orcid2vivo.fetch_orcid_profile('0000-0003-1527-0030')
        self.crosswalker.crosswalk(profile, self.person_uri, self.graph)
        # Assert no triples in graph
        self.assertTrue(len(self.graph) == 0)


    @my_vcr.use_cassette('fundings/null.yaml')
    def test_no_funding(self):
        profile = orcid2vivo.fetch_orcid_profile('0000-0002-7843-9422')
        self.crosswalker.crosswalk(profile, self.person_uri, self.graph)
        # Assert no triples in graph
        self.assertTrue(len(self.graph) == 0)


    @my_vcr.use_cassette('fundings/with_funding.yaml')
    def test_with_funding(self):
        profile = orcid2vivo.fetch_orcid_profile('0000-0001-5109-3700')
        self.crosswalker.crosswalk(profile, self.person_uri, self.graph)
        # Verify a grant exists.
        grant_uri = ns.D['grant-9ea22d7c992375778b4a3066f5142624']
        self.assertEqual(
            self.graph.value(grant_uri, RDFS.label).toPython(),
            u"Policy Implications of International Graduate Students and Postdocs in the United States"
        )
        # Verify three PI roles related to grants for this person uri.
        pi_roles = [guri for guri in self.graph.subjects(predicate=ns.OBO['RO_0000052'], object=self.person_uri)]
        self.assertEqual(len(pi_roles), 3)

    @my_vcr.use_cassette('fundings/null_external_identifier_funding.yaml')
    def test_with_funding(self):
        profile = orcid2vivo.fetch_orcid_profile('0000-0003-3844-5120')
        self.crosswalker.crosswalk(profile, self.person_uri, self.graph)
        # Verify a grant exists.
        grant_uri = ns.D['grant-742228eecfbdacf092bf482f84151082']
        self.assertEqual(
            self.graph.value(grant_uri, RDFS.label).toPython(),
            u"The Utility of Ultra High Performance Supercritical Fluid Chromatography for the Analysis of Seized Drugs:"
            u"  Application to Synthetic Cannabinoids and Bath Salts "
        )
        self.assertEqual(0, len(list(self.graph[grant_uri : ns.VIVO.sponsorAwardId : ])))
