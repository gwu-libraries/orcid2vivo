from unittest import TestCase
import json
import app.works as works
import app.vivo_namespace as ns
from rdflib import Graph, Literal, RDFS

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

    def test_orcid_title_no_subtitle(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-activities" : {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-title": {
                            "title": {
                                "value": "Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?"
                            },
                            "subtitle": null,
                            "translated-title": null
                        },
                        "work-type": "JOURNAL_ARTICLE"
                    }
                ]
            }
        }
    }
}
        """)

        works.crosswalk_works(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(list(self.graph[: RDFS["label"]: Literal(
            "Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?")]))

    def test_orcid_title_and_subtitle(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-activities" : {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-title": {
                            "title" : {
                                "value" : "Substance use disorder among people with first-episode psychosis"
                            },
                            "subtitle" : {
                                "value" : "A systematic review of course and treatment"
                            },
                            "translated-title": null
                        },
                        "work-type": "JOURNAL_ARTICLE"
                    }
                ]
            }
        }
    }
}
        """)

        works.crosswalk_works(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(list(self.graph[: RDFS["label"]: Literal(
            "Substance use disorder among people with first-episode psychosis: A systematic review of course and treatment")]))

    def test_bibtex_title(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-activities" : {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-title": {
                            "title": {
                                "value": "Not the title"
                            },
                            "subtitle": null,
                            "translated-title": null
                        },
                        "work-type": "JOURNAL_ARTICLE",
                        "work-citation" : {
                            "work-citation-type" : "BIBTEX",
                            "citation" : "@article { haak2012,title = {Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?},journal = {Academic Medicine},year = {2012},volume = {87},number = {11},pages = {1516-1524},author = {Ginther, D.K. and Haak, L.L. and Schaffer, W.T. and Kington, R.}}"
                        }
                    }
                ]
            }
        }
    }
}
        """)

        works.crosswalk_works(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(list(self.graph[: RDFS["label"]: Literal(
            "Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?")]))

    def test_crossref_title(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-activities": {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-title": {
                            "title": {
                                "value": "Not the title"
                            },
                            "subtitle": null,
                            "translated-title": null
                        },
                        "work-type": "JOURNAL_ARTICLE",
                        "work-citation": {
                            "work-citation-type": "BIBTEX",
                            "citation": "@article { haak2012,title = {Not the title},journal = {Academic Medicine},year = {2012},volume = {87},number = {11},pages = {1516-1524},author = {Ginther, D.K. and Haak, L.L. and Schaffer, W.T. and Kington, R.}}"
                        },
                        "work-external-identifiers": {
                            "work-external-identifier": [
                                {
                                    "work-external-identifier-type": "DOI",
                                    "work-external-identifier-id": {
                                        "value": "10.1097/ACM.0b013e31826d726b"
                                    }
                                },
                                {
                                    "work-external-identifier-type": "EID",
                                    "work-external-identifier-id": {
                                        "value": "2-s2.0-84869886841"
                                    }
                                }
                            ],
                            "scope": null
                        }
                    }
                ]
            }
        }
    }
}
        """)

        works.fetch_crossref_doi = lambda doi: json.loads("""
{
    "title": [
        "Are Race, Ethnicity, and Medical School Affiliation Associated With NIH R01 Type 1 Award Probability for Physician Investigators?"
    ]
}
        """)

        works.crosswalk_works(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(list(self.graph[: RDFS["label"]: Literal(
            "Are Race, Ethnicity, and Medical School Affiliation Associated With NIH R01 Type 1 Award Probability for Physician Investigators?")]))
