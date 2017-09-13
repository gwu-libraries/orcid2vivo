#!/usr/bin/env python
# -*- coding: utf-8 -*-

from unittest import TestCase
import json
from orcid2vivo_app.works import WorksCrosswalk
import orcid2vivo_app.vivo_namespace as ns
from rdflib import Graph, Literal, RDFS, RDF
from orcid2vivo_app.vivo_namespace import VIVO
from orcid2vivo_app.vivo_uri import HashIdentifierStrategy
from orcid2vivo import SimpleCreateEntitiesStrategy

# Saving this because will be monkey patching
orig_fetch_crossref_doi = WorksCrosswalk._fetch_crossref_doi

# curl -H "Accept: application/json" https://pub.orcid.org/v2.0/0000-0003-3441-946X/work/15628639 | jq '.' | pbcopy


class TestWorks(TestCase):

    def setUp(self):
        self.graph = Graph(namespace_manager=ns.ns_manager)
        self.person_uri = ns.D["test"]
        self.create_strategy = SimpleCreateEntitiesStrategy(HashIdentifierStrategy(), person_uri=self.person_uri)
        WorksCrosswalk._fetch_crossref_doi = staticmethod(orig_fetch_crossref_doi)
        self.crosswalker = WorksCrosswalk(identifier_strategy=self.create_strategy,
                                          create_strategy=self.create_strategy)

    def test_no_works(self):
        orcid_profile = json.loads("""
{
  "activities-summary": {
    "works": {
      "group": []
    }
  }
}
        """)
        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertEqual(0, len(self.graph))

    def test_only_handled_work_types(self):
        work_profile = json.loads("""
{
  "type": "NOT_A_BOOK_CHAPTER"
}
        """)
        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "nobody", self.graph)
        self.assertEqual(0, len(self.graph))

    def test_authorship(self):
        work_profile = json.loads("""
{
  "path": "/0000-0001-5109-3700/work/15643392",
  "title": {
    "title": {
      "value": "Persistent identifiers can improve provenance and attribution and encourage sharing of research results"
    },
    "subtitle": null,
    "translated-title": null
  },
  "type": "JOURNAL_ARTICLE"
}
        
        """)
        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Haak", self.graph)
        self.assertEqual(1, len(list(self.graph[: RDF["type"]: VIVO["Authorship"]])))
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:AcademicArticle .
                ?doc rdfs:label "Persistent identifiers can improve provenance and attribution and encourage sharing of research results" .
                ?auth a vivo:Authorship .
                ?auth vivo:relates ?doc, d:test .
            }
        """)))

    def test_orcid_title_no_subtitle(self):
        work_profile = json.loads("""
{
  "path": "/0000-0001-5109-3700/work/15643384",
  "title": {
    "title": {
      "value": "Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?"
    },
    "subtitle": null,
    "translated-title": null
  },
  "type": "JOURNAL_ARTICLE"
}
        
        """)
        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Haak", self.graph)
        self.assertTrue(list(self.graph[: RDFS["label"]: Literal(
            "Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for "
            "physician investigators?")]))

    def test_orcid_title_and_subtitle(self):
        work_profile = json.loads("""
{
  "path": "/0000-0003-3441-946X/work/15628639",
  "title": {
    "title": {
      "value": "Substance use disorder among people with first-episode psychosis"
    },
    "subtitle": {
      "value": "A systematic review of course and treatment"
    },
    "translated-title": null
  },
  "type": "JOURNAL_ARTICLE"
}
        
        """)
        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Wisdom", self.graph)
        self.assertTrue(list(self.graph[: RDFS["label"]: Literal(
            "Substance use disorder among people with first-episode psychosis: A systematic review of course and "
            "treatment")]))

    def test_bibtex_title(self):
        work_profile = json.loads("""
{
  "path": "/0000-0001-5109-3700/work/15643384",
  "title": {
    "title": {
      "value": "Not the title"
    },
    "subtitle": null,
    "translated-title": null
  },
  "citation": {
    "citation-type": "BIBTEX",
    "citation-value": "@article{Haak2012,title = {Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?},journal = {Academic Medicine},year = {2012},volume = {87},number = {11},pages = {1516-1524},author = {Ginther, D.K. and Haak, L.L. and Schaffer, W.T. and Kington, R.}}"
  },
  "type": "JOURNAL_ARTICLE"
}
        
        """)
        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Haak", self.graph)
        self.assertTrue(list(self.graph[: RDFS["label"]: Literal(
            "Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for "
            "physician investigators?")]))

    def test_crossref_title(self):
        work_profile = json.loads("""
{
  "path": "/0000-0001-5109-3700/work/15643384",
  "title": {
    "title": {
      "value": "Not the title"
    },
    "subtitle": null,
    "translated-title": null
  },
  "citation": {
    "citation-type": "BIBTEX",
    "citation-value": "@article{Haak2012,title = {Not the title},journal = {Academic Medicine},year = {2012},volume = {87},number = {11},pages = {1516-1524},author = {Ginther, D.K. and Haak, L.L. and Schaffer, W.T. and Kington, R.}}"
  },
  "type": "JOURNAL_ARTICLE",
  "external-ids": {
    "external-id": [
      {
        "external-id-type": "doi",
        "external-id-value": "10.1097/ACM.0b013e31826d726b",
        "external-id-url": null,
        "external-id-relationship": "SELF"
      },
      {
        "external-id-type": "eid",
        "external-id-value": "2-s2.0-84869886841",
        "external-id-url": null,
        "external-id-relationship": "SELF"
      }
    ]
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

        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Haak", self.graph)
        self.assertTrue(list(self.graph[: RDFS["label"]: Literal(
            "Are Race, Ethnicity, and Medical School Affiliation Associated With NIH R01 Type 1 Award Probability for "
            "Physician Investigators?")]))

    def test_bibtex_publisher(self):
        work_profile = json.loads("""
{
  "path": "/0000-0001-5014-4975/work/13266925",
  "short-description": null,
  "citation": {
    "citation-type": "BIBTEX",
    "citation-value": "@book{Hardt_2014,doi = {10.1093/acprof:oso/9780199337118.001.0001},url = {http://dx.doi.org/10.1093/acprof:oso/9780199337118.001.0001},year = 2014,month = {Feb},publisher = {Oxford University Press},author = {Heidi Hardt},title = {Time to React}}"
  },
  "type": "BOOK"
}
        
        """)
        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Hardt", self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:Book .
                ?doc vivo:publisher ?pub .
                ?pub a foaf:Organization .
                ?pub rdfs:label "Oxford University Press" .
            }
        """)))

    def test_crossref_publisher(self):
        work_profile = json.loads("""
{
  "path": "/0000-0001-5109-3700/work/15643382",
  "citation": {
    "citation-type": "BIBTEX",
    "citation-value": "@article{Haak2012,title = {Standards and infrastructure for innovation data exchange},journal = {Science},year = {2012},volume = {338},number = {6104},pages = {196-197},author = {Haak, L.L. and Baker, D. and Ginther, D.K. and Gordon, G.J. and Probus, M.A. and Kannankutty, N. and Weinberg, B.A.}}"
  },
  "type": "JOURNAL_ARTICLE",
  "external-ids": {
    "external-id": [
      {
        "external-id-type": "doi",
        "external-id-value": "10.1126/science.1221840",
        "external-id-url": null,
        "external-id-relationship": "SELF"
      },
      {
        "external-id-type": "eid",
        "external-id-value": "2-s2.0-84867318319",
        "external-id-url": null,
        "external-id-relationship": "SELF"
      }
    ]
  }
}
        
        """)

        WorksCrosswalk._fetch_crossref_doi = staticmethod(lambda doi: json.loads("""
{
    "publisher": "Ovid Technologies (Wolters Kluwer Health)"
}
        """))

        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Haak", self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:AcademicArticle .
                ?doc vivo:publisher ?pub .
                ?pub a foaf:Organization .
                ?pub rdfs:label "Ovid Technologies (Wolters Kluwer Health)" .
            }
        """)))

    def test_bibtex_volume_and_number_and_pages(self):
        work_profile = json.loads("""
{
  "path": "/0000-0001-5003-0230/work/13540323",
  "type": "BOOK",
  "citation": {
    "citation-type": "BIBTEX",
    "citation-value": "@article { viladomat1997,title = {Narcissus alkaloids},journal = {Studies in Natural Products Chemistry},year = {1997},volume = {20},number = {PART F},pages = {323-405},author = {Bastida, J. and Viladomat, F. and Codina, C.}}"
  }
}
        
        """)

        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Viladomat", self.graph)
        self.assertTrue(list(self.graph[: ns.BIBO["volume"]: Literal("20")]))
        self.assertTrue(list(self.graph[: ns.BIBO["issue"]: Literal("PART F")]))
        self.assertTrue(list(self.graph[: ns.BIBO["pageStart"]: Literal("323")]))
        self.assertTrue(list(self.graph[: ns.BIBO["pageEnd"]: Literal("405")]))

    def test_crossref_volume_and_number_and_pages(self):
        work_profile = json.loads("""

{
  "path": "/0000-0001-5109-3700/work/8289794",
  "type": "JOURNAL_ARTICLE",
  "title": {
    "title": {
      "value": "Are Race, Ethnicity, and Medical School Affiliation Associated With NIH R01 Type 1 Award Probability for Physician Investigators?"
    },
    "subtitle": null,
    "translated-title": null
  },
  "external-ids": {
    "external-id": [
      {
        "external-id-type": "doi",
        "external-id-value": "10.1097/acm.0b013e31826d726b",
        "external-id-url": null,
        "external-id-relationship": "SELF"
      }
    ]
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
        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Haak", self.graph)
        self.assertTrue(list(self.graph[: ns.BIBO["volume"]: Literal("11")]))
        self.assertTrue(list(self.graph[: ns.BIBO["issue"]: Literal("87")]))
        self.assertTrue(list(self.graph[: ns.BIBO["pageStart"]: Literal("1516")]))
        self.assertTrue(list(self.graph[: ns.BIBO["pageEnd"]: Literal("1524")]))

    def test_orcid_pubdate(self):
        work_profile = json.loads("""
{
  "path": "/0000-0001-5109-3700/work/8289794",
  "type": "JOURNAL_ARTICLE",
  "title": {
    "title": {
      "value": "Are Race, Ethnicity, and Medical School Affiliation Associated With NIH R01 Type 1 Award Probability for Physician Investigators?"
    },
    "subtitle": null,
    "translated-title": null
  },
  "publication-date": {
    "year": {
      "value": "2013"
    },
    "month": {
      "value": "11"
    },
    "day": {
      "value": "01"    
    },
    "media-type": null
  }
}
        
        """)
        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Haak", self.graph)
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
        work_profile = json.loads("""
{
  "path": "/0000-0001-5109-3700/work/8289794",
  "type": "JOURNAL_ARTICLE",
  "title": {
    "title": {
      "value": "Are Race, Ethnicity, and Medical School Affiliation Associated With NIH R01 Type 1 Award Probability for Physician Investigators?"
    },
    "subtitle": null,
    "translated-title": null
  },
  "publication-date": {
    "year": {
      "value": "2013"
    },
    "month": null,
    "day": null,
    "media-type": null
  }
}

        """)
        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Haak", self.graph)
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
        work_profile = json.loads("""
{
  "path": "/0000-0001-5109-3700/work/8289794",
  "type": "JOURNAL_ARTICLE",
  "title": {
    "title": {
      "value": "Are Race, Ethnicity, and Medical School Affiliation Associated With NIH R01 Type 1 Award Probability for Physician Investigators?"
    },
    "subtitle": null,
    "translated-title": null
  },
  "publication-date": {
    "year": {
      "value": "2013"
    },
    "month": null,
    "day": null,
    "media-type": null
  },
  "external-ids": {
    "external-id": [
      {
        "external-id-type": "doi",
        "external-id-value": "10.1097/acm.0b013e31826d726b",
        "external-id-url": null,
        "external-id-relationship": "SELF"
      }
    ]
  }
}
""")

        WorksCrosswalk._fetch_crossref_doi = staticmethod(lambda doi: json.loads("""
{
    "issued":{"date-parts":[[2012,10,31]]}
}
        """))

        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Haak", self.graph)
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
        work_profile = json.loads("""
        {
          "path": "/0000-0001-5109-3700/work/8289794",
          "type": "JOURNAL_ARTICLE",
          "title": {
            "title": {
              "value": "Are Race, Ethnicity, and Medical School Affiliation Associated With NIH R01 Type 1 Award Probability for Physician Investigators?"
            },
            "subtitle": null,
            "translated-title": null
          },
          "publication-date": {
            "year": {
              "value": "2013"
            },
            "month": null,
            "day": null,
            "media-type": null
          },
          "external-ids": {
            "external-id": [
              {
                "external-id-type": "doi",
                "external-id-value": "10.1097/acm.0b013e31826d726b",
                "external-id-url": null,
                "external-id-relationship": "SELF"
              }
            ]
          }
        }
        """)

        WorksCrosswalk._fetch_crossref_doi = staticmethod(lambda doi: json.loads("""
{
    "issued":{"date-parts":[[2012]]}
}
        """))

        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Haak", self.graph)
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
        work_profile = json.loads("""
{
  "path": "/0000-0001-5000-0736/work/11557873",
  "citation": {
    "citation-type": "BIBTEX",
    "citation-value": "@article { chichorro2014,title = {Chronological link between deep-seated processes in magma chambers and eruptions: Permo-Carboniferous magmatism in the core of Pangaea (Southern Pyrenees)},journal = {Gondwana Research},year = {2014},volume = {25},number = {1},pages = {290-308},author = {Pereira, M.F. and Castro, A. and Chichorro, M. and Fernández, C. and Díaz-Alvarado, J. and Martí, J. and Rodríguez, C.}}"
  },
  "type": "JOURNAL_ARTICLE"
}
        
        """)
        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Chichorro", self.graph)
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
        work_profile = json.loads("""
{
  "path": "/0000-0001-5000-0736/work/11557873",
  "citation": {
    "citation-type": "BIBTEX",
    "citation-value": "@article { chichorro2014,title = {Chronological link between deep-seated processes in magma chambers and eruptions: Permo-Carboniferous magmatism in the core of Pangaea (Southern Pyrenees)},journal = {Gondwana Research},year = {in press},volume = {25},number = {1},pages = {290-308}}"
  },
  "type": "JOURNAL_ARTICLE"
}
        
        """)
        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Chichorro", self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:AcademicArticle .
                filter not exists {
                    ?doc vivo:dateTimeValue ?dt .
                }
            }
        """)))

    def test_book_chapter(self):
        work_profile = json.loads("""
{
  "path": "/0000-0002-9446-437X/work/35153466",
  "title": {
    "title": {
      "value": "Numerical Methods for Multi-term Fractional Boundary Value Problems"
    },
    "subtitle": null,
    "translated-title": null
  },
  "citation": {
    "citation-type": "BIBTEX",
    "citation-value": "@incollection{\\nyear={2013},\\nisbn={978-1-4614-7332-9},\\nbooktitle={Differential and Difference Equations with Applications},\\nvolume={47},\\nseries={Springer Proceedings in Mathematics & Statistics},\\neditor={Pinelas, Sandra and Chipot, Michel and Dosla, Zuzana},\\ndoi={10.1007/978-1-4614-7333-6_48},\\ntitle={Numerical Methods for Multi-term Fractional Boundary Value Problems},\\nurl={http://dx.doi.org/10.1007/978-1-4614-7333-6_48},\\npublisher={Springer New York},\\npages={535-542},\\nlanguage={English}\\n}\\n"
  },
  "type": "BOOK_CHAPTER"
}        
        """)
        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Ford", self.graph)
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
        work_profile = json.loads("""
{
  "path": "/0000-0003-3441-946X/work/15628641",
  "title": {
    "title": {
      "value": "Substance abuse treatment programs' data management capacity: An exploratory study"
    },
    "subtitle": null,
    "translated-title": null
  },
  "type": "JOURNAL_ARTICLE",
  "external-ids": {
    "external-id": [
      {
        "external-id-type": "doi",
        "external-id-value": "10.1007/s11414-010-9221-z",
        "external-id-url": {
          "value": ""
        },
        "external-id-relationship": "SELF"
      },
      {
        "external-id-type": "eid",
        "external-id-value": "2-s2.0-79955719929",
        "external-id-url": {
          "value": ""
        },
        "external-id-relationship": "SELF"
      }
    ]
  }
}
        
        """)
        WorksCrosswalk._fetch_crossref_doi = staticmethod(lambda doi: json.loads("""
{
    "subject":["Health(social science)","Public Health, Environmental and Occupational Health","Health Policy"]
}
        """))

        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Wisdom", self.graph)
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
        work_profile = json.loads("""
                {
                  "path": "/0000-0001-5109-3700/work/8289794",
                  "type": "JOURNAL_ARTICLE",
                  "title": {
                    "title": {
                      "value": "Are Race, Ethnicity, and Medical School Affiliation Associated With NIH R01 Type 1 Award Probability for Physician Investigators?"
                    },
                    "subtitle": null,
                    "translated-title": null
                  },
                  "publication-date": {
                    "year": {
                      "value": "2013"
                    },
                    "month": null,
                    "day": null,
                    "media-type": null
                  },
                  "external-ids": {
                    "external-id": [
                      {
                        "external-id-type": "doi",
                        "external-id-value": "10.1097/acm.0b013e31826d726b",
                        "external-id-url": null,
                        "external-id-relationship": "SELF"
                      }
                    ]
                  }
                }
                """)

        WorksCrosswalk._fetch_crossref_doi = staticmethod(lambda doi: json.loads("""
        {
            "author":[{"affiliation":[],"family":"Ginther","given":"Donna K."},{"affiliation":[],"family":"Haak","given":"Laurel L."},{"affiliation":[],"family":"Schaffer","given":"Walter T."},{"affiliation":[],"family":"Kington","given":"Raynard"}]
        }
                """))

        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Haak", self.graph)
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
        work_profile = json.loads("""
{
  "path": "/0000-0001-5109-3700/work/15643384",
  "title": {
    "title": {
      "value": "Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?"
    },
    "subtitle": null,
    "translated-title": null
  },
  "type": "JOURNAL_ARTICLE",
  "contributors": {
    "contributor": [
      {
        "contributor-orcid": null,
        "credit-name": {
          "value": "Ginther, D.K."
        },
        "contributor-email": null,
        "contributor-attributes": null
      },
      {
        "contributor-orcid": null,
        "credit-name": {
          "value": "Haak, L.L."
        },
        "contributor-email": null,
        "contributor-attributes": null
      },
      {
        "contributor-orcid": null,
        "credit-name": {
          "value": "Schaffer, W.T."
        },
        "contributor-email": null,
        "contributor-attributes": null
      },
      {
        "contributor-orcid": null,
        "credit-name": {
          "value": "Kington, R."
        },
        "contributor-email": null,
        "contributor-attributes": null
      }
    ]
  }
}
        
        """)

        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Haak", self.graph)
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
        work_profile = json.loads("""
        {
          "path": "/0000-0001-5109-3700/work/15643384",
          "title": {
            "title": {
              "value": "Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?"
            },
            "subtitle": null,
            "translated-title": null
          },
          "type": "JOURNAL_ARTICLE",
          "contributors": {
            "contributor": []
          }
        }

                """)

        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Haak", self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:AcademicArticle .
                ?auth1 a vivo:Authorship .
                ?auth1 vivo:relates ?doc, d:test.
            }
        """)))

    def test_null_credit_name(self):
        work_profile = json.loads("""
        {
          "path": "/0000-0001-5109-3700/work/15643384",
          "title": {
            "title": {
              "value": "Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?"
            },
            "subtitle": null,
            "translated-title": null
          },
          "type": "JOURNAL_ARTICLE",
          "contributors": {
            "contributor": [
              {
                "contributor-orcid": null,
                "credit-name": null,
                "contributor-email": null,
                "contributor-attributes": null
              }
            ]
          }
        }

                """)

        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Haak", self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:AcademicArticle .
                ?auth1 a vivo:Authorship .
                ?auth1 vivo:relates ?doc, d:test.
            }
        """)))

    def test_orcid_authors_not_reversed(self):
        work_profile = json.loads("""
        {
          "path": "/0000-0001-5109-3700/work/15643384",
          "title": {
            "title": {
              "value": "Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?"
            },
            "subtitle": null,
            "translated-title": null
          },
          "type": "JOURNAL_ARTICLE",
          "contributors": {
            "contributor": [
              {
                "contributor-orcid": null,
                "credit-name": {
                  "value": "D.K. Ginther"
                },
                "contributor-email": null,
                "contributor-attributes": null
              },
              {
                "contributor-orcid": null,
                "credit-name": {
                  "value": "L.L. Haak"
                },
                "contributor-email": null,
                "contributor-attributes": null
              },
              {
                "contributor-orcid": null,
                "credit-name": {
                  "value": "W.T. Schaffer"
                },
                "contributor-email": null,
                "contributor-attributes": null
              },
              {
                "contributor-orcid": null,
                "credit-name": {
                  "value": "R. Kington"
                },
                "contributor-email": null,
                "contributor-attributes": null
              }
            ]
          }
        }
                """)

        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Haak", self.graph)
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
        work_profile = json.loads("""
{
  "path": "/0000-0001-5109-3700/work/15643384",
  "title": {
    "title": {
      "value": "Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?"
    },
    "subtitle": null,
    "translated-title": null
  },
  "citation": {
    "citation-type": "BIBTEX",
    "citation-value": "@article{Haak2012,title = {Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?},journal = {Academic Medicine},year = {2012},volume = {87},number = {11},pages = {1516-1524},author = {Ginther, D.K. and Haak, L.L. and Schaffer, W.T. and Kington, R.}}"
  },
  "type": "JOURNAL_ARTICLE"
}
        
        """)
        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Haak", self.graph)
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
        work_profile = json.loads("""
        {
          "path": "/0000-0001-5109-3700/work/15643384",
          "title": {
            "title": {
              "value": "Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?"
            },
            "subtitle": null,
            "translated-title": null
          },
          "citation": {
            "citation-type": "BIBTEX",
            "citation-value": "@article{Haak2012,title = {Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?},journal = {Academic Medicine},year = {2012},volume = {87},number = {11},pages = {1516-1524},author = {D.K. Ginther and L.L. Haak and W.T. Schaffer and R. Kington}}"
          },
          "type": "JOURNAL_ARTICLE"
        }

                """)
        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Haak", self.graph)
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
        work_profile = json.loads("""
{
  "path": "/0000-0002-9446-437X/work/35153466",
  "title": {
    "title": {
      "value": "Numerical Methods for Multi-term Fractional Boundary Value Problems"
    },
    "subtitle": null,
    "translated-title": null
  },
  "citation": {
    "citation-type": "BIBTEX",
    "citation-value": "@incollection{\\nyear={2013},\\nisbn={978-1-4614-7332-9},\\nbooktitle={Differential and Difference Equations with Applications},\\nvolume={47},\\nseries={Springer Proceedings in Mathematics & Statistics},\\neditor={Pinelas, Sandra and Chipot, Michel and Dosla, Zuzana},\\ndoi={10.1007/978-1-4614-7333-6_48},\\ntitle={Numerical Methods for Multi-term Fractional Boundary Value Problems},\\nurl={http://dx.doi.org/10.1007/978-1-4614-7333-6_48},\\npublisher={Springer New York},\\npages={535-542},\\nlanguage={English}\\n}\\n"
  },
  "type": "BOOK_CHAPTER"
}
        
        """)

        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Ford", self.graph)
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
        work_profile = json.loads("""
{
  "path": "/0000-0001-5014-7658/work/11269935",
  "title": {
    "title": {
      "value": "Media and Sports/Media e Desporto"
    },
    "subtitle": null,
    "translated-title": null
  },
  "type": "BOOK",
  "contributors": {
    "contributor": [
      {
        "contributor-orcid": null,
        "credit-name": null,
        "contributor-email": null,
        "contributor-attributes": {
          "contributor-sequence": "FIRST",
          "contributor-role": "EDITOR"
        }
      }
    ]
  }
}
        
        """)
        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Almeida", self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:Book .
                ?edit1 a vivo:Editorship .
                ?edit1 vivo:relates ?doc, d:test .
            }
        """)))

    def test_external_identifier(self):
        work_profile = json.loads("""
{
  "path": "/0000-0001-5109-3700/work/15643384",
  "title": {
    "title": {
      "value": "Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?"
    },
    "subtitle": null,
    "translated-title": null
  },
  "type": "JOURNAL_ARTICLE",
  "external-ids": {
    "external-id": [
      {
        "external-id-type": "doi",
        "external-id-value": "10.1097/ACM.0b013e31826d726b",
        "external-id-url": null,
        "external-id-relationship": "SELF"
      },
      {
        "external-id-type": "eid",
        "external-id-value": "2-s2.0-84869886841",
        "external-id-url": null,
        "external-id-relationship": "SELF"
      }
    ]
  }
}
        
        """)

        WorksCrosswalk._fetch_crossref_doi = staticmethod(lambda doi: json.loads("""
{
}
        """))

        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Haak", self.graph)
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
        work_profile = json.loads("""
{
  "path": "/0000-0001-9002-015X/work/13926662",
  "title": {
    "title": {
      "value": "Estrategias de frontera desde la interculturalidad."
    },
    "subtitle": {
      "value": "El caso del we tripantü mapuche hoy"
    },
    "translated-title": null
  },
  "journal-title": {
    "value": "Actas del XIII Congreso de Antropología de la Federación de Asociaciones de Antropología del Estado Español: Periferias, Fronteras y Diálogos. "
  },
  "type": "CONFERENCE_PAPER",
  "external-ids": {
    "external-id": [
      {
        "external-id-type": "isbn",
        "external-id-value": "978-84-697-0505-6",
        "external-id-url": {
          "value": ""
        },
        "external-id-relationship": "PART_OF"
      }
    ]
  }
}
        
        """)
        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Milesi", self.graph)
        self.assertTrue(list(self.graph[: ns.BIBO["isbn13"]: Literal("978-84-697-0505-6")]))

    def test_isbn10(self):
        work_profile = json.loads("""
        {
          "path": "/0000-0001-9002-015X/work/13926662",
          "title": {
            "title": {
              "value": "Estrategias de frontera desde la interculturalidad."
            },
            "subtitle": {
              "value": "El caso del we tripantü mapuche hoy"
            },
            "translated-title": null
          },
          "journal-title": {
            "value": "Actas del XIII Congreso de Antropología de la Federación de Asociaciones de Antropología del Estado Español: Periferias, Fronteras y Diálogos. "
          },
          "type": "CONFERENCE_PAPER",
          "external-ids": {
            "external-id": [
              {
                "external-id-type": "isbn",
                "external-id-value": "978-84-697-05",
                "external-id-url": {
                  "value": ""
                },
                "external-id-relationship": "PART_OF"
              }
            ]
          }
        }

                """)
        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Milesi", self.graph)
        self.assertTrue(list(self.graph[: ns.BIBO["isbn10"]: Literal("978-84-697-05")]))

    def test_bibtex_doi(self):
        work_profile = json.loads("""
{
  "path": "/0000-0001-5014-4975/work/13266925",
  "title": {
    "title": {
      "value": "Time to React"
    },
    "subtitle": {
      "value": "The Efficiency of International Organizations in Crisis Response"
    },
    "translated-title": null
  },
  "citation": {
    "citation-type": "BIBTEX",
    "citation-value": "@book{Hardt_2014,doi = {10.1093/acprof:oso/9780199337118.001.0001},url = {http://dx.doi.org/10.1093/acprof:oso/9780199337118.001.0001},year = 2014,month = {Feb},publisher = {Oxford University Press},author = {Heidi Hardt},title = {Time to React}}"
  },
  "type": "BOOK"
}
        """)
        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Hardt", self.graph)
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
        work_profile = json.loads("""
{
  "title": {
    "title": {
      "value": "Numerical methods for multi-term fractional boundary value problems, Differential and Difference Equations with Applications"
    },
    "subtitle": null,
    "translated-title": null
  },
  "citation": {
    "citation-type": "BIBTEX",
    "citation-value": "@incollection{\\nyear={2013},\\nisbn={978-1-4614-7332-9},\\nbooktitle={Differential and Difference Equations with Applications},\\nvolume={47},\\nseries={Springer Proceedings in Mathematics & Statistics},\\neditor={Pinelas, Sandra and Chipot, Michel and Dosla, Zuzana},\\ndoi={10.1007/978-1-4614-7333-6_48},\\ntitle={Numerical Methods for Multi-term Fractional Boundary Value Problems},\\nurl={http://dx.doi.org/10.1007/978-1-4614-7333-6_48},\\npublisher={Springer New York},\\npages={535-542},\\nlanguage={English}\\n}\\n"
  },
  "type": "BOOK_CHAPTER"
}
        
        """)

        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Ford", self.graph)
        self.assertTrue(list(self.graph[: ns.BIBO["isbn13"]: Literal("978-1-4614-7332-9")]))

    def test_orcid_url(self):
        work_profile = json.loads("""
{
  "path": "/0000-0001-5006-1520/work/13637092",
  "title": {
    "title": {
      "value": "Popular Music and Israeli National Culture"
    },
    "subtitle": null,
    "translated-title": null
  },
  "type": "BOOK",
  "url": {
    "value": "http://www.ucpress.edu/book.php?isbn=9780520236547"
  }
}
        
        """)

        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Seroussi", self.graph)
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
        work_profile = json.loads("""
{
  "path": "/0000-0001-5014-4975/work/13266925",
  "title": {
    "title": {
      "value": "Time to React"
    },
    "subtitle": {
      "value": "The Efficiency of International Organizations in Crisis Response"
    },
    "translated-title": null
  },
  "type": "BOOK",
  "url": {
    "value": "http://dx.doi.org/10.1093/acprof:oso/9780199337118.001.0001"
  }
}
        
        """)
        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Hardt", self.graph)
        self.assertFalse(list(self.graph[: ns.VCARD["url"]: ]))

    def test_bibtex_url(self):
        work_profile = json.loads("""
{
  "path": "/0000-0001-5014-4975/work/13266925",
  "title": {
    "title": {
      "value": "Time to React"
    },
    "subtitle": {
      "value": "The Efficiency of International Organizations in Crisis Response"
    },
    "translated-title": null
  },
  "citation": {
    "citation-type": "BIBTEX",
    "citation-value": "@book{Hardt_2014,doi = {10.1093/acprof:oso/9780199337118.001.0001},url = {http://www.ucpress.edu/book.php?isbn=9780520236547},year = 2014,month = {Feb},publisher = {Oxford University Press},author = {Heidi Hardt},title = {Time to React}}"
  },
  "type": "BOOK"
}
        
        """)
        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Hardt", self.graph)
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
        work_profile = json.loads("""
        {
          "path": "/0000-0001-5014-4975/work/13266925",
          "title": {
            "title": {
              "value": "Time to React"
            },
            "subtitle": {
              "value": "The Efficiency of International Organizations in Crisis Response"
            },
            "translated-title": null
          },
          "citation": {
            "citation-type": "BIBTEX",
            "citation-value": "@book{Hardt_2014,url = {http://dx.doi.org/10.1093/acprof:oso/9780199337118.001.0001},year = 2014,month = {Feb},publisher = {Oxford University Press},author = {Heidi Hardt},title = {Time to React}}"
          },
          "type": "BOOK"
        }

                """)

        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Hardt", self.graph)
        self.assertFalse(list(self.graph[: ns.VCARD["url"]:]))

    def test_bibtex_journal(self):
        work_profile = json.loads("""
        {
          "path": "/0000-0001-5109-3700/work/15643384",
          "title": {
            "title": {
              "value": "Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?"
            },
            "subtitle": null,
            "translated-title": null
          },
          "citation": {
            "citation-type": "BIBTEX",
            "citation-value": "@article { haak2012,title = {Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?},journal = {Academic Medicine},issn = {1040-2446},year = {2012},volume = {87},number = {11},pages = {1516-1524},author = {Ginther, D.K. and Haak, L.L. and Schaffer, W.T. and Kington, R.}}"
          },
          "type": "JOURNAL_ARTICLE"
        }

        """)
        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Haak", self.graph)
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
        work_profile = json.loads("""
        {
          "path": "/0000-0001-5109-3700/work/15643384",
          "title": {
            "title": {
              "value": "Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?"
            },
            "subtitle": null,
            "translated-title": null
          },
          "type": "JOURNAL_ARTICLE",
          "external-ids": {
            "external-id": [
              {
                "external-id-type": "doi",
                "external-id-value": "10.1097/ACM.0b013e31826d726b",
                "external-id-url": null,
                "external-id-relationship": "SELF"
              },
              {
                "external-id-type": "eid",
                "external-id-value": "2-s2.0-84869886841",
                "external-id-url": null,
                "external-id-relationship": "SELF"
              }
            ]
          }
        }

                """)

        WorksCrosswalk._fetch_crossref_doi = staticmethod(lambda doi: json.loads("""
        {
            "container-title": ["Academic Medicine", "Acad. Med."],
            "ISSN": ["1040-2446", "1938-808X"]
        }
                """))

        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Haak", self.graph)
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
        work_profile = json.loads("""
{
  "path": "/0000-0001-5109-3700/work/15643384",
  "title": {
    "title": {
      "value": "Are race, ethnicity, and medical school affiliation associated with NIH R01 type 1 award probability for physician investigators?"
    },
    "subtitle": null,
    "translated-title": null
  },
  "journal-title": {
    "value": "Academic Medicine"
  },
  "type": "JOURNAL_ARTICLE"
}
        
        """)

        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Haak", self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:AcademicArticle .
                ?doc vivo:hasPublicationVenue ?jrnl .
                ?jrnl a bibo:Journal .
                ?jrnl rdfs:label "Academic Medicine" .
            }
        """)))

    def test_journal_issue(self):
        work_profile = json.loads("""
{
  "path": "/0000-0001-5138-9384/work/10341578",
  "title": {
    "title": {
      "value": "Egon Bittner"
    },
    "subtitle": {
      "value": "Phenomenology in Action"
    },
    "translated-title": null
  },
  "journal-title": {
    "value": "Ethnographic Studies"
  },
  "short-description": "Special Memorial Issue",
  "type": "JOURNAL_ISSUE",
  "publication-date": {
    "year": {
      "value": "2013"
    },
    "month": {
      "value": "07"
    },
    "day": {
      "value": "01"
    },
    "media-type": null
  },
  "external-ids": {
    "external-id": [
      {
        "external-id-type": "issn",
        "external-id-value": "1366-4964",
        "external-id-url": null,
        "external-id-relationship": "SELF"
      }
    ]
  },
  "url": {
    "value": "http://www.zhbluzern.ch/index.php?id=2583"
  },
  "contributors": {
    "contributor": [
      {
        "contributor-orcid": {
          "uri": null,
          "path": null,
          "host": null
        },
        "credit-name": {
          "value": "Andrew Carlin"
        },
        "contributor-email": null,
        "contributor-attributes": {
          "contributor-sequence": "FIRST",
          "contributor-role": "EDITOR"
        }
      }
    ]
  }
}
        
        """)
        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Carlin", self.graph)
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

    def test_magazine(self):
        work_profile = json.loads("""
{
  "path": "/0000-0001-5019-3929/work/13302713",
  "title": {
    "title": {
      "value": "Software as a Communication Platform"
    },
    "subtitle": {
      "value": ""
    },
    "translated-title": null
  },
  "journal-title": {
    "value": "Kunststoffe international 2009/11"
  },
  "type": "MAGAZINE_ARTICLE"
}
        
        """)
        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Peinado", self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:Article .
                ?doc vivo:hasPublicationVenue ?jrnl .
                ?jrnl a bibo:Magazine .
                ?jrnl rdfs:label "Kunststoffe international 2009/11" .
            }
        """)))

    def test_translation_with_bibtex(self):
        work_profile = json.loads("""
{

  "path": "/0000-0001-5621-5463/work/14402996",
  "title": {
    "title": {
      "value": "Ambiguità nelle risposte al Position Generator"
    },
    "subtitle": null,
    "translated-title": null
  },
  "journal-title": {
    "value": "SOCIOLOGIA E POLITICHE SOCIALI"
  },
  "citation": {
    "citation-type": "BIBTEX",
    "citation-value": "@article{sciandra2012, author= {SCIANDRA A.}, doi= {10.3280/SP2012-002006}, issn= {1591-2027}, journal= {SOCIOLOGIA E POLITICHE SOCIALI}, pages= {113--141}, title= {Ambiguita nelle risposte al Position Generator}, url= {http://dx.medra.org/10.3280/SP2012-002006}, volume= {15}, year= {2012}}"
  },
  "type": "TRANSLATION"
}
        
        """)
        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Sciandra", self.graph)
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
        work_profile = json.loads("""
{
  "path": "/0000-0001-5785-6342/work/11161159",
  "title": {
    "title": {
      "value": "Aristóteles, Retórica, Obras Completas de Aristóteles"
    },
    "subtitle": {
      "value": "com a colaboração de Paulo Farmhouse Alberto e Abel Nascimento Pena."
    },
    "translated-title": null
  },
  "journal-title": {
    "value": "São Paulo, WMF Martins Fontes, 2012."
  },
  "type": "TRANSLATION",
  "contributors": {
    "contributor": [
      {
        "contributor-orcid": null,
        "credit-name": null,
        "contributor-email": null,
        "contributor-attributes": {
          "contributor-sequence": null,
          "contributor-role": "CHAIR_OR_TRANSLATOR"
        }
      }
    ]
  }
}
        
        """)

        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Manuel", self.graph)
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
        work_profile = json.loads("""
{
  "path": "/0000-0001-5004-4536/work/14890522",
  "title": {
    "title": {
      "value": "Noise in the InAlN/GaN HEMT transistors"
    },
    "subtitle": null,
    "translated-title": null
  },
  "citation": {
    "citation-type": "BIBTEX",
    "citation-value": "@article { atka2010,title = {Noise in the InAlN/GaN HEMT transistors},journal = {Conference Proceedings - The 8th International Conference on Advanced Semiconductor Devices and Microsystems, ASDAM 2010},year = {2010},pages = {53-56},author = {Rendek, K. and Šatka, A. and Kováč, J. and Donoval, D.}}"
  },
  "type": "CONFERENCE_PAPER"
}        
""")
        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Sitka", self.graph)
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
        work_profile = json.loads("""
{
  "path": "/0000-0001-5061-3743/work/11259988",
  "title": {
    "title": {
      "value": "TREATMENT OF INFECTIONS BY CARBON MONOXIDE"
    },
    "subtitle": null,
    "translated-title": null
  },
  "type": "PATENT",
  "external-ids": {
    "external-id": [
      {
        "external-id-type": "other-id",
        "external-id-value": "US2010196516 (A1)",
        "external-id-url": {
          "value": ""
        },
        "external-id-relationship": "SELF"
      }
    ]
  },
  "url": {
    "value": "http://worldwide.espacenet.com/publicationDetails/biblio?II=5&ND=3&adjacent=true&locale=en_EP&FT=D&date=20100805&CC=US&NR=2010196516A1&KC=A1"
  },
  "contributors": {
    "contributor": [
      {
        "contributor-orcid": null,
        "credit-name": null,
        "contributor-email": null,
        "contributor-attributes": {
          "contributor-sequence": null,
          "contributor-role": "CO_INVENTOR"
        }
      }
    ]
  }
}
        
        """)
        self.crosswalker.crosswalk_work(work_profile, self.person_uri, "Romão", self.graph)
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?doc a bibo:Patent .
                ?doc rdfs:label "TREATMENT OF INFECTIONS BY CARBON MONOXIDE" .
                d:test vivo:assigneeFor ?doc .
                ?doc vivo:patentNumber "US2010196516 (A1)" .
            }
        """)))
