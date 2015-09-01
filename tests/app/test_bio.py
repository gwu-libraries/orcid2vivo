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
        self.create_strategy = SimpleCreateEntitiesStrategy(person_uri=self.person_uri)
        self.crosswalker = BioCrosswalk(identifier_strategy=HashIdentifierStrategy(),
                                        create_strategy=self.create_strategy)

    def test_no_external_identifiers(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "external-identifiers": null
        }
    }
}
        """)
        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertEqual(0, len(self.graph))

    def test_external_identifiers(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "external-identifiers": {
                "external-identifier": [
                    {
                        "orcid": null,
                        "external-id-orcid": null,
                        "external-id-common-name": {
                            "value": "ISNI"
                        },
                        "external-id-reference": {
                            "value": "0000000138352317"
                        },
                        "external-id-url": {
                            "value": "http://isni.org/isni/0000000138352317"
                        },
                        "external-id-source": null,
                        "source": {
                            "source-orcid": {
                                "value": null,
                                "uri": "http://orcid.org/0000-0003-0412-1857",
                                "path": "0000-0003-0412-1857",
                                "host": "orcid.org"
                            },
                            "source-client-id": null,
                            "source-name": null,
                            "source-date": null
                        }
                    },
                    {
                        "orcid": null,
                        "external-id-orcid": null,
                        "external-id-common-name": {
                            "value": "ResearcherID"
                        },
                        "external-id-reference": {
                            "value": "C-4986-2008"
                        },
                        "external-id-url": {
                            "value": "http://www.researcherid.com/rid/C-4986-2008"
                        },
                        "external-id-source": null,
                        "source": {
                            "source-orcid": {
                                "value": null,
                                "uri": "http://orcid.org/0000-0001-7707-4137",
                                "path": "0000-0001-7707-4137",
                                "host": "orcid.org"
                            },
                            "source-client-id": null,
                            "source-name": null,
                            "source-date": null
                        }
                    },
                    {
                        "orcid": null,
                        "external-id-orcid": null,
                        "external-id-common-name": {
                            "value": "Scopus Author ID"
                        },
                        "external-id-reference": {
                            "value": "6602258586"
                        },
                        "external-id-url": {
                            "value": "http://www.scopus.com/inward/authorDetails.url?authorID=6602258586&partnerID=MN8TOARS"
                        },
                        "external-id-source": null,
                        "source": {
                            "source-orcid": {
                                "value": null,
                                "uri": "http://orcid.org/0000-0002-5982-8983",
                                "path": "0000-0002-5982-8983",
                                "host": "orcid.org"
                            },
                            "source-client-id": null,
                            "source-name": null,
                            "source-date": null
                        }
                    }
                ],
                "visibility": "PUBLIC"
            }
        }
    }
}
        """)
        self.create_strategy.skip_person = True
        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertEqual(2, len(self.graph))
        #ScopusID is added.
        self.assertTrue(self.graph[D["test"]: VIVO["scopusId"] : Literal("6602258586")])
        #ResearcherId is added.
        self.assertTrue(self.graph[D["test"]: VIVO["researcherId"] : Literal("C-4986-2008")])

    def test_name(self):
        orcid_profile = json.loads(u"""
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
                },
                "credit-name": {
                    "value": "Laurel L Haak",
                    "visibility": "PUBLIC"
                },
                "other-names": {
                    "other-name": [
                        {
                            "value": " L. L. Haak"
                        },
                        {
                            "value": "L Haak"
                        },
                        {
                            "value": "Laure Haak"
                        },
                        {
                            "value": "Laurela L Hāka"
                        }
                    ],
                    "visibility": "PUBLIC"
                }
            },
            "external-identifiers": null
        }
    }
}
        """)
        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        #Laurel is a person
        self.assertTrue(self.graph[D["test"]: RDF.type: FOAF.Person])
        #with a label
        self.assertTrue(self.graph[D["test"]: RDFS.label: Literal("Laurel Haak")])

        #vcard test
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
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "biography": {
                "value": "Laurel L. Haak, PhD, is the Executive Director of ORCID.",
                "visibility": "PUBLIC"
            }
        }
    }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)

        #Has a biography
        self.assertTrue(self.graph[D["test"]: VIVO["overview"]:
            Literal("Laurel L. Haak, PhD, is the Executive Director of ORCID.")])

    def test_no_biography(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "biography": null
        }
    }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)

        #Has a biography
        self.assertEqual(0, len(self.graph))

    def test_websites(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "researcher-urls": {
                "researcher-url": [
                    {
                        "url-name": {
                            "value": "LinkedIn"
                        },
                        "url": {
                            "value": "http://www.linkedin.com/pub/laurel-haak/3/1b/4a3/"
                        }
                    },
                    {
                        "url-name": null,
                        "url": {
                            "value": "https://www.researchgate.net/profile/Laurel_Haak"
                        }
                    }
                ],
                "visibility": "PUBLIC"
            },
            "contact-details": {
                "email": [],
                "address": {
                    "country": {
                        "value": "US",
                        "visibility": "PUBLIC"
                    }
                }
            }
        }
    }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        #LinkedIn
        self.assertTrue(bool(self.graph.query("""
            ask where {
                ?vcw a vcard:URL .
                ?vcw vcard:url "http://www.linkedin.com/pub/laurel-haak/3/1b/4a3/"^^xsd:anyURI .
                ?vcw rdfs:label "LinkedIn" .
                ?vc a vcard:Individual .
                ?vc vcard:hasURL ?vcw .
            }
        """)))

        #ResearchGate
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
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "researcher-urls": {
                "researcher-url": [],
                "visibility": "PUBLIC"
            }
        }
    }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)

        #Has a biography
        self.assertEqual(0, len(self.graph))

    def test_no_keywords(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "keywords": null
        }
    }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)

        #Has a biography
        self.assertEqual(0, len(self.graph))

    def test_keywords(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "keywords": {
                "keyword": [
                    {
                        "value": "persistent identifiers"
                    },
                    {
                        "value": "research policy"
                    },
                    {
                        "value": "science workforce"
                    }
                ],
                "visibility": "PUBLIC"
            }
        }
    }
}
        """)

        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertEqual(3, len(self.graph))

        self.assertTrue(bool(self.graph.query("""
            ask where {
                d:test vivo:freetextKeyword "persistent identifiers" .
                d:test vivo:freetextKeyword "research policy" .
                d:test vivo:freetextKeyword "science workforce" .
            }
        """)))