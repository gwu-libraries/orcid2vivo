#!/usr/bin/env python
# -*- coding: utf-8 -*-

from unittest import TestCase
import json
from orcid2vivo_app.bio import BioCrosswalk
import orcid2vivo_app.vivo_namespace as ns
from rdflib import Literal, Graph, RDF, RDFS
from orcid2vivo_app.vivo_namespace import D, VIVO, FOAF
from orcid2vivo_app.vivo_uri import HashIdentifierStrategy
from orcid2vivo import SimpleCreateEntitiesStrategy


class TestBio(TestCase):
    def setUp(self):
        self.graph = Graph(namespace_manager=ns.ns_manager)
        self.person_uri = ns.D["test"]
        self.create_strategy = SimpleCreateEntitiesStrategy(HashIdentifierStrategy(), person_uri=self.person_uri)
        self.crosswalker = BioCrosswalk(identifier_strategy=self.create_strategy,
                                        create_strategy=self.create_strategy)

    def test_no_external_identifiers(self):
        orcid_profile = json.loads("""
{
  "person": {
    "external-identifiers": {
      "last-modified-date": null,
      "external-identifier": [],
      "path": "/0000-0003-4507-4735/external-identifiers"
    },
    "path": "/0000-0003-4507-4735/person"
  }
}
""")
        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertEqual(0, len(self.graph))

    def test_external_identifiers(self):
        orcid_profile = json.loads("""
{
  "person": {
    "external-identifiers": {
      "last-modified-date": {
        "value": 1390435480189
      },
      "external-identifier": [
        {
          "created-date": {
            "value": 1379686803951
          },
          "last-modified-date": {
            "value": 1379686803951
          },
          "source": {
            "source-orcid": null,
            "source-client-id": {
              "uri": "http://orcid.org/client/0000-0002-5982-8983",
              "path": "0000-0002-5982-8983",
              "host": "orcid.org"
            },
            "source-name": {
              "value": "Scopus to ORCID"
            }
          },
          "external-id-type": "Scopus Author ID",
          "external-id-value": "6602258586",
          "external-id-url": {
            "value": "http://www.scopus.com/inward/authorDetails.url?authorID=6602258586&partnerID=MN8TOARS"
          },
          "external-id-relationship": "SELF",
          "visibility": "PUBLIC",
          "path": "/0000-0001-5109-3700/external-identifiers/142173",
          "put-code": 142173,
          "display-index": 0
        },
        {
          "created-date": {
            "value": 1379686803951
          },
          "last-modified-date": {
            "value": 1379686803951
          },
          "source": {
            "source-orcid": {
              "uri": "http://orcid.org/0000-0001-7707-4137",
              "path": "0000-0001-7707-4137",
              "host": "orcid.org"
            },
            "source-client-id": null,
            "source-name": {
              "value": "Clarivate Analytics"
            }
          },
          "external-id-type": "ResearcherID",
          "external-id-value": "C-4986-2008",
          "external-id-url": {
            "value": "http://www.researcherid.com/rid/C-4986-2008"
          },
          "external-id-relationship": "SELF",
          "visibility": "PUBLIC",
          "path": "/0000-0001-5109-3700/external-identifiers/38181",
          "put-code": 38181,
          "display-index": 0
        },
        {
          "created-date": {
            "value": 1390435480189
          },
          "last-modified-date": {
            "value": 1390435480189
          },
          "source": {
            "source-orcid": null,
            "source-client-id": {
              "uri": "http://orcid.org/client/0000-0003-0412-1857",
              "path": "0000-0003-0412-1857",
              "host": "orcid.org"
            },
            "source-name": {
              "value": "ISNI2ORCID search and link"
            }
          },
          "external-id-type": "ISNI",
          "external-id-value": "0000000138352317",
          "external-id-url": {
            "value": "http://isni.org/isni/0000000138352317"
          },
          "external-id-relationship": "SELF",
          "visibility": "PUBLIC",
          "path": "/0000-0001-5109-3700/external-identifiers/187639",
          "put-code": 187639,
          "display-index": 0
        }
      ],
      "path": "/0000-0001-5109-3700/external-identifiers"
    },
    "path": "/0000-0001-5109-3700/person"
  }
}
""")
        self.create_strategy.skip_person = True
        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertEqual(2, len(self.graph))
        # ScopusID is added.
        self.assertTrue(self.graph[D["test"]: VIVO["scopusId"]: Literal("6602258586")])
        # ResearcherId is added.
        self.assertTrue(self.graph[D["test"]: VIVO["researcherId"]: Literal("C-4986-2008")])

    def test_name(self):
        orcid_profile = json.loads(u"""
{
  "person": {
    "name": {
      "created-date": {
        "value": 1460753221409
      },
      "last-modified-date": {
        "value": 1460753221409
      },
      "given-names": {
        "value": "Laurel"
      },
      "family-name": {
        "value": "Haak"
      },
      "credit-name": {
        "value": "Laurel L Haak"
      },
      "source": null,
      "visibility": "PUBLIC",
      "path": "0000-0001-5109-3700"
    },
    "other-names": {
      "last-modified-date": {
        "value": 1461191605426
      },
      "other-name": [
        {
          "created-date": {
            "value": 1461191605416
          },
          "last-modified-date": {
            "value": 1461191605416
          },
          "source": {
            "source-orcid": {
              "uri": "http://orcid.org/0000-0001-5109-3700",
              "path": "0000-0001-5109-3700",
              "host": "orcid.org"
            },
            "source-client-id": null,
            "source-name": {
              "value": "Laurel L Haak"
            }
          },
          "content": " L. L. Haak",
          "visibility": "PUBLIC",
          "path": "/0000-0001-5109-3700/other-names/721941",
          "put-code": 721941,
          "display-index": 0
        },
        {
          "created-date": {
            "value": 1461191605425
          },
          "last-modified-date": {
            "value": 1461191605425
          },
          "source": {
            "source-orcid": {
              "uri": "http://orcid.org/0000-0001-5109-3700",
              "path": "0000-0001-5109-3700",
              "host": "orcid.org"
            },
            "source-client-id": null,
            "source-name": {
              "value": "Laurel L Haak"
            }
          },
          "content": "L Haak",
          "visibility": "PUBLIC",
          "path": "/0000-0001-5109-3700/other-names/721942",
          "put-code": 721942,
          "display-index": 0
        },
        {
          "created-date": {
            "value": 1461191605426
          },
          "last-modified-date": {
            "value": 1461191605426
          },
          "source": {
            "source-orcid": {
              "uri": "http://orcid.org/0000-0001-5109-3700",
              "path": "0000-0001-5109-3700",
              "host": "orcid.org"
            },
            "source-client-id": null,
            "source-name": {
              "value": "Laurel L Haak"
            }
          },
          "content": "Laure Haak",
          "visibility": "PUBLIC",
          "path": "/0000-0001-5109-3700/other-names/721943",
          "put-code": 721943,
          "display-index": 0
        },
        {
          "created-date": {
            "value": 1461191605426
          },
          "last-modified-date": {
            "value": 1461191605426
          },
          "source": {
            "source-orcid": {
              "uri": "http://orcid.org/0000-0001-5109-3700",
              "path": "0000-0001-5109-3700",
              "host": "orcid.org"
            },
            "source-client-id": null,
            "source-name": {
              "value": "Laurel L Haak"
            }
          },
          "content": "Laurela L Hāka",
          "visibility": "PUBLIC",
          "path": "/0000-0001-5109-3700/other-names/721944",
          "put-code": 721944,
          "display-index": 0
        }
      ],
      "path": "/0000-0001-5109-3700/other-names"
    }
  }
}
        """)
        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        # Laurel is a person
        self.assertTrue(self.graph[D["test"]: RDF.type: FOAF.Person])
        # with a label
        self.assertTrue(self.graph[D["test"]: RDFS.label: Literal("Laurel Haak")])

        # vcard test
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?vcn a vcard:Name .
                ?vcn vcard:familyName "Haak" .
                ?vcn vcard:givenName "Laurel" .
                ?vc obo:ARG_2000029 d:test .
                ?vc vcard:hasName ?vcn .
            }
        """)))

    def test_biography(self):
        orcid_profile = json.loads("""
{
  "person": {
    "biography": {
      "created-date": {
        "value": 1460753221411
      },
      "last-modified-date": {
        "value": 1487932762756
      },
      "content": "Laurel L. Haak, PhD, is the Executive Director of ORCID, an international and interdisciplinary non-profit organization dedicated to providing the technical infrastructure to generate and maintain unique and persistent identifiers for researchers and scholars.",
      "visibility": "PUBLIC",
      "path": "/0000-0001-5109-3700/biography"
    }
  }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)

        # Has a biography
        self.assertTrue(self.graph[D["test"]: VIVO["overview"]: Literal("Laurel L. Haak, PhD, is the Executive "
                                                                        "Director of ORCID, an international and "
                                                                        "interdisciplinary non-profit organization "
                                                                        "dedicated to providing the technical "
                                                                        "infrastructure to generate and maintain "
                                                                        "unique and persistent identifiers for "
                                                                        "researchers and scholars.")])

    def test_no_biography(self):
        orcid_profile = json.loads("""
{
  "person": {
    "biography": {
      "created-date": {
        "value": 1460766291133
      },
      "last-modified-date": {
        "value": 1460766291133
      },
      "content": null,
      "visibility": "PUBLIC",
      "path": "/0000-0003-4507-4735/biography"
    }
  }
}
""")

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)

        # Has a biography
        self.assertEqual(0, len(self.graph))

    def test_websites(self):
        orcid_profile = json.loads("""
{
 "person": {
    "researcher-urls": {
      "last-modified-date": {
        "value": 1463003428816
      },
      "researcher-url": [
        {
          "created-date": {
            "value": 1461191605427
          },
          "last-modified-date": {
            "value": 1463003428816
          },
          "source": {
            "source-orcid": {
              "uri": "http://orcid.org/0000-0001-5109-3700",
              "path": "0000-0001-5109-3700",
              "host": "orcid.org"
            },
            "source-client-id": null,
            "source-name": {
              "value": "Laurel L Haak"
            }
          },
          "url-name": "LinkedIn",
          "url": {
            "value": "http://www.linkedin.com/pub/laurel-haak/3/1b/4a3/"
          },
          "visibility": "PUBLIC",
          "path": "/0000-0001-5109-3700/researcher-urls/714700",
          "put-code": 714700,
          "display-index": 0
        },
        {
          "created-date": {
            "value": 1461191605427
          },
          "last-modified-date": {
            "value": 1463003428816
          },
          "source": {
            "source-orcid": {
              "uri": "http://orcid.org/0000-0001-5109-3700",
              "path": "0000-0001-5109-3700",
              "host": "orcid.org"
            },
            "source-client-id": null,
            "source-name": {
              "value": "Laurel L Haak"
            }
          },
          "url-name": null,
          "url": {
            "value": "https://www.researchgate.net/profile/Laurel_Haak"
          },
          "visibility": "PUBLIC",
          "path": "/0000-0001-5109-3700/researcher-urls/714701",
          "put-code": 714701,
          "display-index": 0
        }
      ],
      "path": "/0000-0001-5109-3700/researcher-urls"
    }
  }
}
""")
        # Set ResearchGate url-name to null.

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        # LinkedIn
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?vcw a vcard:URL .
                ?vcw vcard:url "http://www.linkedin.com/pub/laurel-haak/3/1b/4a3/"^^xsd:anyURI .
                ?vcw rdfs:label "LinkedIn" .
                ?vc a vcard:Individual .
                ?vc vcard:hasURL ?vcw .
            }
        """)))

        # ResearchGate
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?vcw a vcard:URL .
                ?vcw vcard:url "https://www.researchgate.net/profile/Laurel_Haak"^^xsd:anyURI .
                ?vc a vcard:Individual .
                ?vc vcard:hasURL ?vcw .
                filter not exists {
                    ?vcw rdfs:label ?label .
                }
            }
        """)))

    def test_no_websites(self):
        orcid_profile = json.loads("""
{
  "person": {
    "researcher-urls": {
      "last-modified-date": null,
      "researcher-url": [],
      "path": "/0000-0003-4507-4735/researcher-urls"
    }
  }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)

        # Has a biography
        self.assertEqual(0, len(self.graph))

    def test_no_keywords(self):
        orcid_profile = json.loads("""
{
  "person": {
    "keywords": {
      "last-modified-date": null,
      "keyword": [],
      "path": "/0000-0003-4507-4735/keywords"
    }
  }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)

        # Has a biography
        self.assertEqual(0, len(self.graph))

    def test_keywords(self):
        orcid_profile = json.loads("""
{
  "person": {
    "keywords": {
      "last-modified-date": {
        "value": 1464800983143
      },
      "keyword": [
        {
          "created-date": {
            "value": 1461191605415
          },
          "last-modified-date": {
            "value": 1464800983143
          },
          "source": {
            "source-orcid": {
              "uri": "http://orcid.org/0000-0001-5109-3700",
              "path": "0000-0001-5109-3700",
              "host": "orcid.org"
            },
            "source-client-id": null,
            "source-name": {
              "value": "Laurel L Haak"
            }
          },
          "content": "persistent identifiers, research policy, science workforce, program evaluation, neuroscience, calcium imaging, oligodendrocytes, circadian rhythms",
          "visibility": "PUBLIC",
          "path": "/0000-0001-5109-3700/keywords/419740",
          "put-code": 419740,
          "display-index": 0
        }
      ],
      "path": "/0000-0001-5109-3700/keywords"
    }
  }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertEqual(8, len(self.graph))

        self.assertTrue(bool(self.graph.query("""
            ask where {
                d:test vivo:freetextKeyword "persistent identifiers" .
                d:test vivo:freetextKeyword "research policy" .
                d:test vivo:freetextKeyword "science workforce" .
            }
        """)))
