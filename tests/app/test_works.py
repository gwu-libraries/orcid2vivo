#!/usr/bin/env python
# -*- coding: utf-8 -*-

from unittest import TestCase
import json
from orcid2vivo_app.works import WorksCrosswalk
import orcid2vivo_app.vivo_namespace as ns
from rdflib import Graph, Literal, RDFS
from orcid2vivo_app.vivo_uri import HashIdentifierStrategy
from orcid2vivo import SimpleCreateEntitiesStrategy

#Saving this because will be monkey patching
orig_fetch_crossref_doi = WorksCrosswalk._fetch_crossref_doi

class TestWorks(TestCase):

    def setUp(self):
        self.graph = Graph(namespace_manager=ns.ns_manager)
        self.person_uri = ns.D["test"]
        self.create_strategy = SimpleCreateEntitiesStrategy(person_uri=self.person_uri)
        WorksCrosswalk._fetch_crossref_doi = staticmethod(orig_fetch_crossref_doi)
        self.crosswalker = WorksCrosswalk(identifier_strategy=HashIdentifierStrategy(),
                                          create_strategy=self.create_strategy)


    def test_no_actitivities(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-activities": null
    }
}
        """)
        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
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
        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertEqual(0, len(self.graph))

    def test_only_handled_work_types(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-activities" : {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-type": "NOT_A_JOURNAL_ARTICLE"
                    }
                ]
            }
        }
    }
}
        """)
        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertEqual(0, len(self.graph))

    def test_orcid_title_no_subtitle(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Laurel"
                },
                "family-name": {
                    "value": "Haak"
                }
            }
        },
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

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(list(self.graph[: RDFS["label"]: Literal(
            "Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?")]))

    def test_orcid_title_and_subtitle(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Jennifer"
                },
                "family-name": {
                    "value": "Wisdom"
                }
            }
        },
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

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(list(self.graph[: RDFS["label"]: Literal(
            "Substance use disorder among people with first-episode psychosis: A systematic review of course and treatment")]))

    def test_bibtex_title(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Laurel"
                },
                "family-name": {
                    "value": "Haak"
                }
            }
        },
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

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(list(self.graph[: RDFS["label"]: Literal(
            "Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?")]))

    def test_crossref_title(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Laurel"
                },
                "family-name": {
                    "value": "Haak"
                }
            }
        },
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

        WorksCrosswalk._fetch_crossref_doi = staticmethod(lambda doi: json.loads("""
{
    "title": [
        "Are Race, Ethnicity, and Medical School Affiliation Associated With NIH R01 Type 1 Award Probability for Physician Investigators?"
    ]
}
        """))

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(list(self.graph[: RDFS["label"]: Literal(
            "Are Race, Ethnicity, and Medical School Affiliation Associated With NIH R01 Type 1 Award Probability for Physician Investigators?")]))

    def test_bibtex_publisher(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Heidi"
                },
                "family-name": {
                    "value": "Hardt"
                }
            }
        },
        "orcid-activities" : {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-type": "BOOK",
                        "work-citation" : {
                            "work-citation-type" : "BIBTEX",
                            "citation": "@book{Hardt_2014,doi = {10.1093/acprof:oso/9780199337118.001.0001},url = {http://dx.doi.org/10.1093/acprof:oso/9780199337118.001.0001},year = 2014,month = {Feb},publisher = {Oxford University Press},author = {Heidi Hardt},title = {Time to React}}"
                        }
                    }
                ]
            }
        }
    }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:Book .
                ?doc vivo:publisher ?pub .
                ?pub a foaf:Organization .
                ?pub rdfs:label "Oxford University Press" .
            }
        """)))

    def test_crossref_publisher(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Laurel"
                },
                "family-name": {
                    "value": "Haak"
                }
            }
        },
        "orcid-activities": {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-type": "JOURNAL_ARTICLE",
                        "work-citation": {
                            "work-citation-type": "BIBTEX",
                            "citation": "@article { haak2012,title = {Are Race, Ethnicity, and Medical School Affiliation Associated With NIH R01 Type 1 Award Probability for Physician Investigators?},publisher = {Not the publisher},journal = {Academic Medicine},year = {2012},volume = {87},number = {11},pages = {1516-1524},author = {Ginther, D.K. and Haak, L.L. and Schaffer, W.T. and Kington, R.}}"
                        },
                        "work-external-identifiers": {
                            "work-external-identifier": [
                                {
                                    "work-external-identifier-type": "DOI",
                                    "work-external-identifier-id": {
                                        "value": "10.1097/ACM.0b013e31826d726b"
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

        WorksCrosswalk._fetch_crossref_doi = staticmethod(lambda doi: json.loads("""
{
    "publisher": "Ovid Technologies (Wolters Kluwer Health)"
}
        """))

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:AcademicArticle .
                ?doc vivo:publisher ?pub .
                ?pub a foaf:Organization .
                ?pub rdfs:label "Ovid Technologies (Wolters Kluwer Health)" .
            }
        """)))

    def test_bibtex_volume_and_number_and_pages(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "F."
                },
                "family-name": {
                    "value": "Viladomat"
                }
            }
        },
        "orcid-activities" : {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-type": "BOOK",
                        "work-citation" : {
                            "work-citation-type" : "BIBTEX",
                            "citation": "@article { viladomat1997,title = {Narcissus alkaloids},journal = {Studies in Natural Products Chemistry},year = {1997},volume = {20},number = {PART F},pages = {323-405}}"
                        }
                    }
                ]
            }
        }
    }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(list(self.graph[: ns.BIBO["volume"]: Literal("20")]))
        self.assertTrue(list(self.graph[: ns.BIBO["issue"]: Literal("PART F")]))
        self.assertTrue(list(self.graph[: ns.BIBO["pageStart"]: Literal("323")]))
        self.assertTrue(list(self.graph[: ns.BIBO["pageEnd"]: Literal("405")]))

    def test_bibtex_volume_and_number_and_pages(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Laurel"
                },
                "family-name": {
                    "value": "Haak"
                }
            }
        },
        "orcid-activities": {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-type": "JOURNAL_ARTICLE",
                        "work-citation": {
                            "work-citation-type": "BIBTEX",
                            "citation": "@article { haak2012,title = {Are Race, Ethnicity, and Medical School Affiliation Associated With NIH R01 Type 1 Award Probability for Physician Investigators?},publisher = {Not the publisher},journal = {Academic Medicine},year = {2012},volume = {Not 87},number = {Not 11},pages = {1536-1554},author = {Ginther, D.K. and Haak, L.L. and Schaffer, W.T. and Kington, R.}}"
                        },
                        "work-external-identifiers": {
                            "work-external-identifier": [
                                {
                                    "work-external-identifier-type": "DOI",
                                    "work-external-identifier-id": {
                                        "value": "10.1097/ACM.0b013e31826d726b"
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

        WorksCrosswalk._fetch_crossref_doi = staticmethod(lambda doi: json.loads("""
{
    "page": "1516-1524",
    "issue": "87",
    "volume": "11"
}
        """))
        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(list(self.graph[: ns.BIBO["volume"]: Literal("11")]))
        self.assertTrue(list(self.graph[: ns.BIBO["issue"]: Literal("87")]))
        self.assertTrue(list(self.graph[: ns.BIBO["pageStart"]: Literal("1516")]))
        self.assertTrue(list(self.graph[: ns.BIBO["pageEnd"]: Literal("1524")]))

    def test_orcid_pubdate(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Laurel"
                },
                "family-name": {
                    "value": "Haak"
                }
            }
        },
        "orcid-activities" : {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-type": "JOURNAL_ARTICLE",
                        "work-title": {
                            "title": {
                                "value": "Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?"
                            },
                            "subtitle": null,
                            "translated-title": null
                        },
                        "publication-date" : {
                            "year" : {
                              "value" : "2013"
                            },
                            "month" : {
                              "value" : "11"
                            },
                            "day" : {
                              "value" : "01"
                            },
                            "media-type" : null
                        }
                    }
                ]
            }
        }
    }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:AcademicArticle .
                ?doc vivo:dateTimeValue ?dt .
                ?dt a vivo:DateTimeValue .
                ?dt rdfs:label "November 1, 2013" .
                ?dt vivo:dateTime "2013-11-01T00:00:00"^^xsd:dateTime .
                ?dt vivo:dateTimePrecision vivo:yearMonthDayPrecision .
            }
        """)))

    def test_orcid_pubdate_year_only(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Laurel"
                },
                "family-name": {
                    "value": "Haak"
                }
            }
        },
        "orcid-activities" : {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-type": "JOURNAL_ARTICLE",
                        "work-title": {
                            "title": {
                                "value": "Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?"
                            },
                            "subtitle": null,
                            "translated-title": null
                        },
                        "publication-date" : {
                            "year" : {
                              "value" : "2013"
                            },
                            "month" : null,
                            "day" : null,
                            "media-type" : null
                        }
                    }
                ]
            }
        }
    }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:AcademicArticle .
                ?doc vivo:dateTimeValue ?dt .
                ?dt a vivo:DateTimeValue .
                ?dt rdfs:label "2013" .
                ?dt vivo:dateTime "2013-01-01T00:00:00"^^xsd:dateTime .
                ?dt vivo:dateTimePrecision vivo:yearPrecision .
            }
        """)))

    def test_crossref_pubdate(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Laurel"
                },
                "family-name": {
                    "value": "Haak"
                }
            }
        },
        "orcid-activities" : {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-type": "JOURNAL_ARTICLE",
                        "work-title": {
                            "title": {
                                "value": "Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?"
                            },
                            "subtitle": null,
                            "translated-title": null
                        },
                        "publication-date" : {
                            "year" : {
                              "value" : "2013"
                            },
                            "month" : null,
                            "day" : null,
                            "media-type" : null
                        },
                        "work-external-identifiers": {
                            "work-external-identifier": [
                                {
                                    "work-external-identifier-type": "DOI",
                                    "work-external-identifier-id": {
                                        "value": "10.1097/ACM.0b013e31826d726b"
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

        WorksCrosswalk._fetch_crossref_doi = staticmethod(lambda doi: json.loads("""
{
    "issued":{"date-parts":[[2012,10,31]]}
}
        """))

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:AcademicArticle .
                ?doc vivo:dateTimeValue ?dt .
                ?dt a vivo:DateTimeValue .
                ?dt rdfs:label "October 31, 2012" .
                ?dt vivo:dateTime "2012-10-31T00:00:00"^^xsd:dateTime .
                ?dt vivo:dateTimePrecision vivo:yearMonthDayPrecision .
            }
        """)))

    def test_crossref_pubdate_year_only(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Laurel"
                },
                "family-name": {
                    "value": "Haak"
                }
            }
        },
        "orcid-activities" : {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-type": "JOURNAL_ARTICLE",
                        "work-title": {
                            "title": {
                                "value": "Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?"
                            },
                            "subtitle": null,
                            "translated-title": null
                        },
                        "publication-date" : {
                            "year" : {
                              "value" : "2013"
                            },
                            "month" : null,
                            "day" : null,
                            "media-type" : null
                        },
                        "work-external-identifiers": {
                            "work-external-identifier": [
                                {
                                    "work-external-identifier-type": "DOI",
                                    "work-external-identifier-id": {
                                        "value": "10.1097/ACM.0b013e31826d726b"
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

        WorksCrosswalk._fetch_crossref_doi = staticmethod(lambda doi: json.loads("""
{
    "issued":{"date-parts":[[2012]]}
}
        """))

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:AcademicArticle .
                ?doc vivo:dateTimeValue ?dt .
                ?dt a vivo:DateTimeValue .
                ?dt rdfs:label "2012" .
                ?dt vivo:dateTime "2012-01-01T00:00:00"^^xsd:dateTime .
                ?dt vivo:dateTimePrecision vivo:yearPrecision .
            }
        """)))

    def test_bibtex_pubdate(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "M."
                },
                "family-name": {
                    "value": "Chichorro"
                }
            }
        },
        "orcid-activities" : {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-type": "JOURNAL_ARTICLE",
                        "work-title": {
                          "title": {
                            "value": "Chronological link between deep-seated processes in magma chambers and eruptions: Permo-Carboniferous magmatism in the core of Pangaea (Southern Pyrenees)"
                          },
                          "subtitle": null
                        },
                        "work-citation": {
                          "work-citation-type": "BIBTEX",
                          "citation": "@article { chichorro2014,title = {Chronological link between deep-seated processes in magma chambers and eruptions: Permo-Carboniferous magmatism in the core of Pangaea (Southern Pyrenees)},journal = {Gondwana Research},year = {2014},volume = {25},number = {1},pages = {290-308}}"
                        }
                    }
                ]
            }
        }
    }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:AcademicArticle .
                ?doc vivo:dateTimeValue ?dt .
                ?dt a vivo:DateTimeValue .
                ?dt rdfs:label "2014" .
                ?dt vivo:dateTime "2014-01-01T00:00:00"^^xsd:dateTime .
                ?dt vivo:dateTimePrecision vivo:yearPrecision .
            }
        """)))

    def test_bibtex_pubdate_in_press(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "M."
                },
                "family-name": {
                    "value": "Chichorro"
                }
            }
        },
        "orcid-activities" : {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-type": "JOURNAL_ARTICLE",
                        "work-title": {
                          "title": {
                            "value": "Chronological link between deep-seated processes in magma chambers and eruptions: Permo-Carboniferous magmatism in the core of Pangaea (Southern Pyrenees)"
                          },
                          "subtitle": null
                        },
                        "work-citation": {
                          "work-citation-type": "BIBTEX",
                          "citation": "@article { chichorro2014,title = {Chronological link between deep-seated processes in magma chambers and eruptions: Permo-Carboniferous magmatism in the core of Pangaea (Southern Pyrenees)},journal = {Gondwana Research},year = {in press},volume = {25},number = {1},pages = {290-308}}"
                        }
                    }
                ]
            }
        }
    }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:AcademicArticle .
                filter not exists {
                    ?doc vivo:dateTimeValue ?dt .
                }
            }
        """)))

    def test_book_chapter(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "N.J."
                },
                "family-name": {
                    "value": "Ford"
                }
            }
        },
        "orcid-activities" : {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-title": {
                            "title": {
                                "value": "Numerical methods for multi-term fractional boundary value problems, Differential and Difference Equations with Applications"
                            },
                            "subtitle": null
                        },
                        "work-citation": {
                            "work-citation-type": "BIBTEX",
                            "citation": "@incollection{\\nyear={2013},\\nisbn={978-1-4614-7332-9},\\nbooktitle={Differential and Difference Equations with Applications},\\nvolume={47},\\nseries={Springer Proceedings in Mathematics & Statistics},\\neditor={Pinelas, Sandra and Chipot, Michel and Dosla, Zuzana},\\ndoi={10.1007/978-1-4614-7333-6_48},\\ntitle={Numerical Methods for Multi-term Fractional Boundary Value Problems},\\nurl={http://dx.doi.org/10.1007/978-1-4614-7333-6_48},\\npublisher={Springer New York},\\npages={535-542},\\nlanguage={English}\\n}\\n"
                        },
                        "work-type": "BOOK_CHAPTER"
                    }
                ]
            }
        }
    }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:Chapter .
                ?doc rdfs:label "Numerical Methods for Multi-term Fractional Boundary Value Problems" .
                ?doc bibo:pageStart "535" .
                ?doc bibo:pageEnd "542" .
                ?doc vivo:hasPublicationVenue ?pv .
                ?pv a bibo:Book .
                ?pv rdfs:label "Differential and Difference Equations with Applications" .
            }
        """)))

    def test_crossref_subject(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Jennifer"
                },
                "family-name": {
                    "value": "Wisdom"
                }
            }
        },
        "orcid-activities" : {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-type": "JOURNAL_ARTICLE",
                        "work-title" : {
                            "title" : {
                                "value" : "Substance abuse treatment programs' data management capacity: An exploratory study"
                            },
                            "subtitle" : null,
                            "translated-title" : null
                        },
                        "work-external-identifiers": {
                            "work-external-identifier": [
                                {
                                    "work-external-identifier-type": "DOI",
                                    "work-external-identifier-id": {
                                        "value": "10.1007/s11414-010-9221-z"
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

        WorksCrosswalk._fetch_crossref_doi = staticmethod(lambda doi: json.loads("""
{
    "subject":["Health(social science)","Public Health, Environmental and Occupational Health","Health Policy"]
}
        """))

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:AcademicArticle .
                ?doc vivo:hasSubjectArea ?sub1 .
                ?sub1 a skos:Concept .
                ?sub1 rdfs:label "Health(social science)" .
                ?doc vivo:hasSubjectArea ?sub2 .
                ?sub2 a skos:Concept .
                ?sub2 rdfs:label "Public Health, Environmental and Occupational Health" .
                ?doc vivo:hasSubjectArea ?sub3 .
                ?sub3 a skos:Concept .
                ?sub3 rdfs:label "Health Policy" .
            }
        """)))

    def test_crossref_authors(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio" : {
            "personal-details" : {
                "given-names" : {
                    "value" : "Laurel"
                },
                "family-name" : {
                    "value" : "Haak"
                }
            }
        },
        "orcid-activities" : {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-type": "JOURNAL_ARTICLE",
                        "work-title" : {
                            "title" : {
                                "value" : "Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?"
                            },
                            "subtitle" : null,
                            "translated-title" : null
                        },
                        "work-external-identifiers": {
                            "work-external-identifier": [
                                {
                                    "work-external-identifier-type": "DOI",
                                    "work-external-identifier-id": {
                                        "value": "10.1097/ACM.0b013e31826d726b"
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

        WorksCrosswalk._fetch_crossref_doi = staticmethod(lambda doi: json.loads("""
{
    "author":[{"affiliation":[],"family":"Ginther","given":"Donna K."},{"affiliation":[],"family":"Haak","given":"Laurel L."},{"affiliation":[],"family":"Schaffer","given":"Walter T."},{"affiliation":[],"family":"Kington","given":"Raynard"}]
}
        """))

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:AcademicArticle .
                ?auth1 a vivo:Authorship .
                ?auth1 vivo:relates ?doc, d:test.
                ?auth2 a vivo:Authorship .
                ?auth2 vivo:relates ?doc, ?per2 .
                ?per2 a foaf:Person .
                ?per2 rdfs:label "Walter T. Schaffer" .
                ?auth3 a vivo:Authorship .
                ?auth3 vivo:relates ?doc, ?per2 .
                ?per3 a foaf:Person .
                ?per3 rdfs:label "Donna K. Ginther" .
                ?auth4 a vivo:Authorship .
                ?auth4 vivo:relates ?doc, ?per2 .
                ?per4 a foaf:Person .
                ?per4 rdfs:label "Raynard Kington" .
            }
        """)))

    def test_orcid_authors_reversed(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Laurel"
                },
                "family-name": {
                    "value": "Haak"
                }
            }
        },
        "orcid-activities": {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-type": "JOURNAL_ARTICLE",
                        "work-title": {
                            "title": {
                                "value": "Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?"
                            },
                            "subtitle": null,
                            "translated-title": null
                        },
                        "work-contributors": {
                            "contributor": [
                                {
                                    "contributor-orcid": null,
                                    "credit-name": {
                                        "value": "Ginther, D.K.",
                                        "visibility": "PUBLIC"
                                    },
                                    "contributor-email": null,
                                    "contributor-attributes": null
                                },
                                {
                                    "contributor-orcid": null,
                                    "credit-name": {
                                        "value": "Haak, L.L.",
                                        "visibility": "PUBLIC"
                                    },
                                    "contributor-email": null,
                                    "contributor-attributes": null
                                },
                                {
                                    "contributor-orcid": null,
                                    "credit-name": {
                                        "value": "Schaffer, W.T.",
                                        "visibility": "PUBLIC"
                                    },
                                    "contributor-email": null,
                                    "contributor-attributes": null
                                },
                                {
                                    "contributor-orcid": null,
                                    "credit-name": {
                                        "value": "Kington, R.",
                                        "visibility": "PUBLIC"
                                    },
                                    "contributor-email": null,
                                    "contributor-attributes": null
                                }
                            ]
                        }
                    }
                ]
            }
        }
    }
}        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:AcademicArticle .
                ?auth1 a vivo:Authorship .
                ?auth1 vivo:relates ?doc, d:test.
                ?auth2 a vivo:Authorship .
                ?auth2 vivo:relates ?doc, ?per2 .
                ?per2 a foaf:Person .
                ?per2 rdfs:label "W.T. Schaffer" .
                ?auth3 a vivo:Authorship .
                ?auth3 vivo:relates ?doc, ?per2 .
                ?per3 a foaf:Person .
                ?per3 rdfs:label "D.K. Ginther" .
                ?auth4 a vivo:Authorship .
                ?auth4 vivo:relates ?doc, ?per2 .
                ?per4 a foaf:Person .
                ?per4 rdfs:label "R. Kington" .
            }
        """)))

    def test_no_orcid_authors(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Laurel"
                },
                "family-name": {
                    "value": "Haak"
                }
            }
        },
        "orcid-activities": {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-type": "JOURNAL_ARTICLE",
                        "work-title": {
                            "title": {
                                "value": "Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?"
                            },
                            "subtitle": null,
                            "translated-title": null
                        },
                        "work-contributors": null
                    }
                ]
            }
        }
    }
}        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:AcademicArticle .
                ?auth1 a vivo:Authorship .
                ?auth1 vivo:relates ?doc, d:test.
            }
        """)))

    def test_null_credit_name(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Laurel"
                },
                "family-name": {
                    "value": "Haak"
                }
            }
        },
        "orcid-activities": {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-type": "JOURNAL_ARTICLE",
                        "work-title": {
                            "title": {
                                "value": "Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?"
                            },
                            "subtitle": null,
                            "translated-title": null
                        },
                        "work-contributors": {
                            "contributor": [
                                {
                                    "contributor-orcid": null,
                                    "credit-name": null,
                                    "contributor-email": null,
                                    "contributor-attributes": {
                                        "contributor-sequence": null,
                                        "contributor-role": "SUPPORT_STAFF"
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }
    }
}        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:AcademicArticle .
                ?auth1 a vivo:Authorship .
                ?auth1 vivo:relates ?doc, d:test.
            }
        """)))

    def test_orcid_authors_not_reversed(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Laurel"
                },
                "family-name": {
                    "value": "Haak"
                }
            }
        },
        "orcid-activities": {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-type": "JOURNAL_ARTICLE",
                        "work-title": {
                            "title": {
                                "value": "Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?"
                            },
                            "subtitle": null,
                            "translated-title": null
                        },
                        "work-contributors": {
                            "contributor": [
                                {
                                    "contributor-orcid": null,
                                    "credit-name": {
                                        "value": "D.K. Ginther",
                                        "visibility": "PUBLIC"
                                    },
                                    "contributor-email": null,
                                    "contributor-attributes": null
                                },
                                {
                                    "contributor-orcid": null,
                                    "credit-name": {
                                        "value": "Haak, L.L.",
                                        "visibility": "PUBLIC"
                                    },
                                    "contributor-email": null,
                                    "contributor-attributes": null
                                },
                                {
                                    "contributor-orcid": null,
                                    "credit-name": {
                                        "value": " W.T. Schaffer",
                                        "visibility": "PUBLIC"
                                    },
                                    "contributor-email": null,
                                    "contributor-attributes": null
                                },
                                {
                                    "contributor-orcid": null,
                                    "credit-name": {
                                        "value": "R. Kington",
                                        "visibility": "PUBLIC"
                                    },
                                    "contributor-email": null,
                                    "contributor-attributes": null
                                }
                            ]
                        }
                    }
                ]
            }
        }
    }
}        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:AcademicArticle .
                ?auth1 a vivo:Authorship .
                ?auth1 vivo:relates ?doc, d:test.
                ?auth2 a vivo:Authorship .
                ?auth2 vivo:relates ?doc, ?per2 .
                ?per2 a foaf:Person .
                ?per2 rdfs:label "W. T. Schaffer" .
                ?auth3 a vivo:Authorship .
                ?auth3 vivo:relates ?doc, ?per2 .
                ?per3 a foaf:Person .
                ?per3 rdfs:label "D. K. Ginther" .
                ?auth4 a vivo:Authorship .
                ?auth4 vivo:relates ?doc, ?per2 .
                ?per4 a foaf:Person .
                ?per4 rdfs:label "R. Kington" .
            }
        """)))

    def test_bibtex_authors_reversed(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Laurel"
                },
                "family-name": {
                    "value": "Haak"
                }
            }
        },
        "orcid-activities": {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-type": "JOURNAL_ARTICLE",
                        "work-title": {
                            "title": {
                                "value": "Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?"
                            },
                            "subtitle": null,
                            "translated-title": null
                        },
                        "work-citation" : {
                            "work-citation-type" : "BIBTEX",
                            "citation" : "@article { haak2012,title = {Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?},journal = {Academic Medicine},year = {2012},volume = {87},number = {11},pages = {1516-1524},author = {Ginther, D.K. and Haak, L.L. and Schaffer, W.T. and Kington, R.}}"
                        }
                    }
                ]
            }
        }
    }
}        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:AcademicArticle .
                ?auth1 a vivo:Authorship .
                ?auth1 vivo:relates ?doc, d:test.
                ?auth2 a vivo:Authorship .
                ?auth2 vivo:relates ?doc, ?per2 .
                ?per2 a foaf:Person .
                ?per2 rdfs:label "W.T. Schaffer" .
                ?auth3 a vivo:Authorship .
                ?auth3 vivo:relates ?doc, ?per2 .
                ?per3 a foaf:Person .
                ?per3 rdfs:label "D.K. Ginther" .
                ?auth4 a vivo:Authorship .
                ?auth4 vivo:relates ?doc, ?per2 .
                ?per4 a foaf:Person .
                ?per4 rdfs:label "R. Kington" .
            }
        """)))

    def test_bibtex_authors_not_reversed(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Laurel"
                },
                "family-name": {
                    "value": "Haak"
                }
            }
        },
        "orcid-activities": {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-type": "JOURNAL_ARTICLE",
                        "work-title": {
                            "title": {
                                "value": "Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?"
                            },
                            "subtitle": null,
                            "translated-title": null
                        },
                        "work-citation" : {
                            "work-citation-type" : "BIBTEX",
                            "citation" : "@article { haak2012,title = {Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?},journal = {Academic Medicine},year = {2012},volume = {87},number = {11},pages = {1516-1524},author = {D.K. Ginther and L.L. Haak and W.T. Schaffer and R. Kington}}"
                        }
                    }
                ]
            }
        }
    }
}        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:AcademicArticle .
                ?auth1 a vivo:Authorship .
                ?auth1 vivo:relates ?doc, d:test.
                ?auth2 a vivo:Authorship .
                ?auth2 vivo:relates ?doc, ?per2 .
                ?per2 a foaf:Person .
                ?per2 rdfs:label "W. T. Schaffer" .
                ?auth3 a vivo:Authorship .
                ?auth3 vivo:relates ?doc, ?per2 .
                ?per3 a foaf:Person .
                ?per3 rdfs:label "D. K. Ginther" .
                ?auth4 a vivo:Authorship .
                ?auth4 vivo:relates ?doc, ?per2 .
                ?per4 a foaf:Person .
                ?per4 rdfs:label "R. Kington" .
            }
        """)))

    def test_bibtex_editor(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "N.J."
                },
                "family-name": {
                    "value": "Ford"
                }
            }
        },
        "orcid-activities" : {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-title": {
                            "title": {
                                "value": "Numerical methods for multi-term fractional boundary value problems, Differential and Difference Equations with Applications"
                            },
                            "subtitle": null
                        },
                        "work-citation": {
                            "work-citation-type": "BIBTEX",
                            "citation": "@incollection{\\nyear={2013},\\nisbn={978-1-4614-7332-9},\\nbooktitle={Differential and Difference Equations with Applications},\\nvolume={47},\\nseries={Springer Proceedings in Mathematics & Statistics},\\neditor={Pinelas, Sandra and Chipot, Michel and Dosla, Zuzana},\\ndoi={10.1007/978-1-4614-7333-6_48},\\ntitle={Numerical Methods for Multi-term Fractional Boundary Value Problems},\\nurl={http://dx.doi.org/10.1007/978-1-4614-7333-6_48},\\npublisher={Springer New York},\\npages={535-542},\\nlanguage={English}\\n}\\n"
                        },
                        "work-type": "BOOK_CHAPTER"
                    }
                ]
            }
        }
    }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:Chapter .
                ?edit1 a vivo:Editorship .
                ?edit1 vivo:relates ?doc, ?per1 .
                ?per1 a foaf:Person .
                ?per1 rdfs:label "Michel Chipot" .
                ?edit2 a vivo:Editorship .
                ?edit2 vivo:relates ?doc, ?per2 .
                ?per2 a foaf:Person .
                ?per2 rdfs:label "Zuzana Dosla" .
                ?edit3 a vivo:Editorship .
                ?edit3 vivo:relates ?doc, ?per3 .
                ?per3 a foaf:Person .
                ?per3 rdfs:label "Sandra Pinelas" .
            }
        """)))

    def test_orcid_editor(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Maria Clotilde"
                },
                "family-name": {
                    "value": "Almeida"
                }
            }
        },
        "orcid-activities" : {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-title": {
                            "title": {
                                "value": "Media and Sports/Media e Desporto"
                            },
                            "subtitle": null
                        },
                        "work-type": "BOOK",
                        "work-contributors": {
                            "contributor": [
                                {
                                    "contributor-attributes": {
                                        "contributor-sequence": "FIRST",
                                        "contributor-role": "EDITOR"
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }
    }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:Book .
                ?edit1 a vivo:Editorship .
                ?edit1 vivo:relates ?doc, d:test .
            }
        """)))

    def test_external_identifier(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Laurel"
                },
                "family-name": {
                    "value": "Haak"
                }
            }
        },
        "orcid-activities": {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-type": "JOURNAL_ARTICLE",
                        "work-title": {
                            "title": {
                                "value": "Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?"
                            },
                            "subtitle": null,
                            "translated-title": null
                        },
                        "work-external-identifiers": {
                            "work-external-identifier": [
                                {
                                    "work-external-identifier-type": "DOI",
                                    "work-external-identifier-id": {
                                        "value": "10.1097/ACM.0b013e31826d726b"
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

        WorksCrosswalk._fetch_crossref_doi = staticmethod(lambda doi: json.loads("""
{
}
        """))

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:AcademicArticle .
                ?doc bibo:doi "10.1097/ACM.0b013e31826d726b" .
                ?vc a vcard:Kind .
                ?doc obo:ARG_2000028 ?vc .
                ?vc vcard:hasURL ?vcurl .
                ?vcurl a vcard:URL .
                ?vcurl vcard:url "http://dx.doi.org/10.1097/ACM.0b013e31826d726b"^^xsd:anyURI .
            }
        """)))

    def test_isbn13(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.1",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Lara"
                },
                "family-name": {
                    "value": "Milesi"
                }
            }
        },
        "orcid-activities": {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-title": {
                            "title": {
                                "value": "Estrategias de frontera desde la interculturalidad."
                            },
                            "subtitle": {
                                "value": "El caso del we tripantü mapuche hoy"
                            }
                        },
                        "journal-title": {
                            "value": "Actas del XIII Congreso de Antropología de la Federación de Asociaciones de Antropología del Estado Español: Periferias, Fronteras y Diálogos. "
                        },
                        "work-type": "CONFERENCE_PAPER",
                        "work-external-identifiers": {
                            "work-external-identifier": [
                                {
                                    "work-external-identifier-type": "ISBN",
                                    "work-external-identifier-id": {
                                        "value": "978-84-697-0505-6"
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }
    }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(list(self.graph[: ns.BIBO["isbn13"]: Literal("978-84-697-0505-6")]))

    def test_isbn10(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.1",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Lara"
                },
                "family-name": {
                    "value": "Milesi"
                }
            }
        },
        "orcid-activities": {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-title": {
                            "title": {
                                "value": "Estrategias de frontera desde la interculturalidad."
                            },
                            "subtitle": {
                                "value": "El caso del we tripantü mapuche hoy"
                            }
                        },
                        "journal-title": {
                            "value": "Actas del XIII Congreso de Antropología de la Federación de Asociaciones de Antropología del Estado Español: Periferias, Fronteras y Diálogos. "
                        },
                        "work-type": "CONFERENCE_PAPER",
                        "work-external-identifiers": {
                            "work-external-identifier": [
                                {
                                    "work-external-identifier-type": "ISBN",
                                    "work-external-identifier-id": {
                                        "value": "978-84-697-05"
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }
    }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(list(self.graph[: ns.BIBO["isbn10"]: Literal("978-84-697-05")]))

    def test_bibtex_doi(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Heidi"
                },
                "family-name": {
                    "value": "Hardt"
                }
            }
        },
        "orcid-activities" : {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-type": "BOOK",
                        "work-citation" : {
                            "work-citation-type" : "BIBTEX",
                            "citation": "@book{Hardt_2014,doi = {10.1093/acprof:oso/9780199337118.001.0001},url = {http://dx.doi.org/10.1093/acprof:oso/9780199337118.001.0001},year = 2014,month = {Feb},publisher = {Oxford University Press},author = {Heidi Hardt},title = {Time to React}}"
                        }
                    }
                ]
            }
        }
    }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:Book .
                ?doc bibo:doi "10.1093/acprof:oso/9780199337118.001.0001" .
                ?vc a vcard:Kind .
                ?doc obo:ARG_2000028 ?vc .
                ?vc vcard:hasURL ?vcurl .
                ?vcurl a vcard:URL .
                ?vcurl vcard:url "http://dx.doi.org/10.1093/acprof:oso/9780199337118.001.0001"^^xsd:anyURI .
            }
        """)))

    def test_bibtex_isbn(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "N.J."
                },
                "family-name": {
                    "value": "Ford"
                }
            }
        },
        "orcid-activities" : {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-title": {
                            "title": {
                                "value": "Numerical methods for multi-term fractional boundary value problems, Differential and Difference Equations with Applications"
                            },
                            "subtitle": null
                        },
                        "work-citation": {
                            "work-citation-type": "BIBTEX",
                            "citation": "@incollection{\\nyear={2013},\\nisbn={978-1-4614-7332-9},\\nbooktitle={Differential and Difference Equations with Applications},\\nvolume={47},\\nseries={Springer Proceedings in Mathematics & Statistics},\\neditor={Pinelas, Sandra and Chipot, Michel and Dosla, Zuzana},\\ndoi={10.1007/978-1-4614-7333-6_48},\\ntitle={Numerical Methods for Multi-term Fractional Boundary Value Problems},\\nurl={http://dx.doi.org/10.1007/978-1-4614-7333-6_48},\\npublisher={Springer New York},\\npages={535-542},\\nlanguage={English}\\n}\\n"
                        },
                        "work-type": "BOOK_CHAPTER"
                    }
                ]
            }
        }
    }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(list(self.graph[: ns.BIBO["isbn13"]: Literal("978-1-4614-7332-9")]))

    def test_orcid_url(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.1",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Edwin"
                },
                "family-name": {
                    "value": "Seroussi"
                }
            }
        },
        "orcid-activities": {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-title": {
                            "title": {
                                "value": "Popular Music and Israeli National Culture"
                            },
                            "subtitle": null
                        },
                        "work-type": "BOOK",
                        "url": {
                            "value": "http://www.ucpress.edu/book.php?isbn=9780520236547"
                        }
                    }
                ]
            }
        }
    }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(list(self.graph[: ns.VCARD["url"]: ]))
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:Book .
                ?vc a vcard:Kind .
                ?doc obo:ARG_2000028 ?vc .
                ?vc vcard:hasURL ?vcurl .
                ?vcurl a vcard:URL .
                ?vcurl vcard:url "http://www.ucpress.edu/book.php?isbn=9780520236547"^^xsd:anyURI .
            }
        """)))



    def test_ignore_orcid_url(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Heidi"
                },
                "family-name": {
                    "value": "Hardt"
                }
            }
        },
        "orcid-activities" : {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-type": "BOOK",
                        "work-title": {
                            "title": {
                                "value": "Time to React"
                            },
                            "subtitle": null,
                            "translated-title": null
                        },
                        "url": {
                            "value": "http://dx.doi.org/10.1093/acprof:oso/9780199337118.001.0001"
                        }
                    }
                ]
            }
        }
    }
}
       """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertFalse(list(self.graph[: ns.VCARD["url"]: ]))

    def test_bibtex_url(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Heidi"
                },
                "family-name": {
                    "value": "Hardt"
                }
            }
        },
        "orcid-activities" : {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-type": "BOOK",
                        "work-citation" : {
                            "work-citation-type" : "BIBTEX",
                            "citation": "@book{Hardt_2014,url = {http://www.ucpress.edu/book.php?isbn=9780520236547},year = 2014,month = {Feb},publisher = {Oxford University Press},author = {Heidi Hardt},title = {Time to React}}"
                        }
                    }
                ]
            }
        }
    }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(list(self.graph[: ns.VCARD["url"]:]))
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:Book .
                ?vc a vcard:Kind .
                ?doc obo:ARG_2000028 ?vc .
                ?vc vcard:hasURL ?vcurl .
                ?vcurl a vcard:URL .
                ?vcurl vcard:url "http://www.ucpress.edu/book.php?isbn=9780520236547"^^xsd:anyURI .
            }
        """)))

    def test_ignore_bibtex_url(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Heidi"
                },
                "family-name": {
                    "value": "Hardt"
                }
            }
        },
        "orcid-activities" : {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-type": "BOOK",
                        "work-citation" : {
                            "work-citation-type" : "BIBTEX",
                            "citation": "@book{Hardt_2014,url = {http://dx.doi.org/10.1093/acprof:oso/9780199337118.001.0001},year = 2014,month = {Feb},publisher = {Oxford University Press},author = {Heidi Hardt},title = {Time to React}}"
                        }
                    }
                ]
            }
        }
    }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertFalse(list(self.graph[: ns.VCARD["url"]:]))

    def test_bibtex_journal(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Laurel"
                },
                "family-name": {
                    "value": "Haak"
                }
            }
        },
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
                            "citation" : "@article { haak2012,title = {Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?},journal = {Academic Medicine},issn = {1040-2446},year = {2012},volume = {87},number = {11},pages = {1516-1524},author = {Ginther, D.K. and Haak, L.L. and Schaffer, W.T. and Kington, R.}}"
                        }
                    }
                ]
            }
        }
    }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:AcademicArticle .
                ?doc vivo:hasPublicationVenue ?jrnl .
                ?jrnl a bibo:Journal .
                ?jrnl rdfs:label "Academic Medicine" .
                ?jrnl bibo:issn "1040-2446" .
            }
        """)))

    def test_crossref_journal(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Laurel"
                },
                "family-name": {
                    "value": "Haak"
                }
            }
        },
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
                            "citation" : "@article { haak2012,title = {Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?},journal = {Not Academic Medicine},issn = {Not 1040-2446},year = {2012},volume = {87},number = {11},pages = {1516-1524},author = {Ginther, D.K. and Haak, L.L. and Schaffer, W.T. and Kington, R.}}"
                        },
                        "work-external-identifiers": {
                            "work-external-identifier": [
                                {
                                    "work-external-identifier-type": "DOI",
                                    "work-external-identifier-id": {
                                        "value": "10.1097/ACM.0b013e31826d726b"
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

        WorksCrosswalk._fetch_crossref_doi = staticmethod(lambda doi: json.loads("""
{
    "container-title": ["Academic Medicine", "Acad. Med."],
    "ISSN": ["1040-2446", "1938-808X"]
}
        """))

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:AcademicArticle .
                ?doc vivo:hasPublicationVenue ?jrnl .
                ?jrnl a bibo:Journal .
                ?jrnl rdfs:label "Academic Medicine" .
                ?jrnl bibo:issn "1040-2446" .
                ?jrnl bibo:issn "1938-808X" .
            }
        """)))

    def test_orcid_journal(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Laurel"
                },
                "family-name": {
                    "value": "Haak"
                }
            }
        },
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
                        "journal-title": {
                            "value": "Academic Medicine"
                        }
                    }
                ]
            }
        }
    }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:AcademicArticle .
                ?doc vivo:hasPublicationVenue ?jrnl .
                ?jrnl a bibo:Journal .
                ?jrnl rdfs:label "Academic Medicine" .
            }
        """)))

    def test_journal_issue(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.1",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Andrew"
                },
                "family-name": {
                    "value": "Carlin"
                }
            }
        },
        "orcid-activities": {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-title": {
                            "title": {
                                "value": "Egon Bittner"
                            },
                            "subtitle": {
                                "value": "Phenomenology in Action"
                            }
                        },
                        "journal-title": {
                            "value": "Ethnographic Studies"
                        },
                        "short-description": "Special Memorial Issue",
                        "work-type": "JOURNAL_ISSUE",
                        "publication-date": {
                            "year": {
                                "value": "2013"
                            },
                            "month": {
                                "value": "07"
                            },
                            "day": {
                                "value": "01"
                            }
                        },
                        "work-external-identifiers": {
                            "work-external-identifier": [
                                {
                                    "work-external-identifier-type": "ISSN",
                                    "work-external-identifier-id": {
                                        "value": "1366-4964"
                                    }
                                }
                            ],
                            "scope": null
                        },
                        "url": {
                            "value": "http://www.zhbluzern.ch/index.php?id=2583"
                        },
                        "work-contributors": {
                            "contributor": [
                                {
                                    "credit-name": {
                                        "value": "Andrew Carlin",
                                        "visibility": "PUBLIC"
                                    },
                                    "contributor-attributes": {
                                        "contributor-sequence": "FIRST",
                                        "contributor-role": "EDITOR"
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }
    }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:Issue .
                ?doc rdfs:label "Egon Bittner: Phenomenology in Action" .
                ?doc vivo:dateTimeValue ?dtv .
                ?doc bibo:issn "1366-4964" .
                ?dtv a vivo:DateTimeValue .
                ?dtv rdfs:label "July 1, 2013" .
                ?doc obo:ARG_2000028 ?vcard .
                ?vcard vcard:hasURL ?vcardurl .
                ?vcardurl vcard:url "http://www.zhbluzern.ch/index.php?id=2583"^^xsd:anyURI .
                ?ed a vivo:Editorship .
                ?ed vivo:relates d:test, ?doc .
            }
        """)))

    def test_journal_issue(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.1",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Victor"
                },
                "family-name": {
                    "value": "Peinado"
                }
            }
        },
        "orcid-activities": {
            "orcid-works": {
                "orcid-work": [
                    {
                        "put-code": "13302713",
                        "work-title": {
                            "title": {
                                "value": "Software as a Communication Platform"
                            },
                            "subtitle": null
                        },
                        "journal-title": {
                            "value": "Kunststoffe international 2009/11"
                        },
                        "work-type": "MAGAZINE_ARTICLE"
                    }
                ]
            }
        }
    }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:Article .
                ?doc vivo:hasPublicationVenue ?jrnl .
                ?jrnl a bibo:Magazine .
                ?jrnl rdfs:label "Kunststoffe international 2009/11" .
            }
        """)))

    def test_translation_with_bibtex(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.1",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "andrea"
                },
                "family-name": {
                    "value": "sciandra"
                }
            }
        },
        "orcid-activities": {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-title": {
                            "title": {
                                "value": "Ambiguità nelle risposte al Position Generator"
                            },
                            "subtitle": null
                        },
                        "journal-title": {
                            "value": "SOCIOLOGIA E POLITICHE SOCIALI"
                        },
                        "work-citation": {
                            "work-citation-type": "BIBTEX",
                            "citation": "@article{sciandra2012, author= {SCIANDRA A.}, doi= {10.3280/SP2012-002006}, issn= {1591-2027}, journal= {SOCIOLOGIA E POLITICHE SOCIALI}, pages= {113--141}, title= {Ambiguita nelle risposte al Position Generator}, url= {http://dx.medra.org/10.3280/SP2012-002006}, volume= {15}, year= {2012}}"
                        },
                        "work-type": "TRANSLATION"
                    }
                ]
            }
        }
    }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:Article .
                ?doc rdfs:label "Ambiguita nelle risposte al Position Generator" .
                d:test bibo:translator ?doc .
                filter not exists {
                    ?contr a vivo:Authorship .
                    ?contr vivo:relates ?doc, d:test .
                }
            }
        """)))

    def test_translation(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.1",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Manuel"
                },
                "family-name": {
                    "value": "Alexandre Júnior"
                }
            }
        },
        "orcid-activities": {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-title": {
                            "title": {
                                "value": "Aristóteles, Retórica, Obras Completas de Aristóteles"
                            },
                            "subtitle": {
                                "value": "com a colaboração de Paulo Farmhouse Alberto e Abel Nascimento Pena."
                            }
                        },
                        "journal-title": {
                            "value": "São Paulo, WMF Martins Fontes, 2012."
                        },
                        "work-type": "TRANSLATION",
                        "work-contributors": {
                            "contributor": [
                                {
                                    "contributor-attributes": {
                                        "contributor-role": "CHAIR_OR_TRANSLATOR"
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }
    }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:Document .
                ?doc rdfs:label "Aristóteles, Retórica, Obras Completas de Aristóteles: com a colaboração de Paulo Farmhouse Alberto e Abel Nascimento Pena." .
                d:test bibo:translator ?doc .
                filter not exists {
                    ?contr a vivo:Authorship .
                    ?contr vivo:relates ?doc, d:test .
                }
            }
        """)))

    def test_conference_paper(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.1",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Alexander"
                },
                "family-name": {
                    "value": "Šatka"
                }
            }
        },
        "orcid-activities": {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-title": {
                            "title": {
                                "value": "Noise in the InAlN/GaN HEMT transistors"
                            },
                            "subtitle": null
                        },
                        "work-citation": {
                            "work-citation-type": "BIBTEX",
                            "citation": "@article { atka2010,title = {Noise in the InAlN/GaN HEMT transistors},journal = {Conference Proceedings - The 8th International Conference on Advanced Semiconductor Devices and Microsystems, ASDAM 2010},year = {2010},pages = {53-56},author = {Rendek, K. and Šatka, A. and Kováč, J. and Donoval, D.}}"
                        },
                        "work-type": "CONFERENCE_PAPER"
                    }
                ]
            }
        }
    }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a vivo:ConferencePaper .
                ?doc rdfs:label "Noise in the InAlN/GaN HEMT transistors" .
                ?doc vivo:hasPublicationVenue ?proc .
                ?proc a bibo:Proceedings .
                ?proc rdfs:label "Conference Proceedings - The 8th International Conference on Advanced Semiconductor Devices and Microsystems, ASDAM 2010" .
            }
        """)))

    def test_patent(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.1",
    "orcid-profile": {
        "orcid-bio": {
            "personal-details": {
                "given-names": {
                    "value": "Carlos C."
                },
                "family-name": {
                    "value": "Romão"
                }
            }
        },
        "orcid-activities": {
            "orcid-works": {
                "orcid-work": [
                    {
                        "work-title": {
                            "title": {
                                "value": "TREATMENT OF INFECTIONS BY CARBON MONOXIDE"
                            },
                            "subtitle": null
                        },
                        "work-type": "PATENT",
                        "work-external-identifiers": {
                            "work-external-identifier": [
                                {
                                    "work-external-identifier-type": "OTHER_ID",
                                    "work-external-identifier-id": {
                                        "value": "US2010196516 (A1)"
                                    }
                                }
                            ]
                        },
                        "url": {
                            "value": "http://worldwide.espacenet.com/publicationDetails/biblio?II=17&ND=3&adjacent=true&locale=en_EP&FT=D&date=20100805&CC=US&NR=2010196516A1&KC=A1"
                        },
                        "work-contributors": {
                            "contributor": [
                                {
                                    "contributor-attributes": {
                                        "contributor-role": "CO_INVENTOR"
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }
    }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:Patent .
                ?doc rdfs:label "TREATMENT OF INFECTIONS BY CARBON MONOXIDE" .
                d:test vivo:assigneeFor ?doc .
                ?doc vivo:patentNumber "US2010196516 (A1)" .
            }
        """)))
