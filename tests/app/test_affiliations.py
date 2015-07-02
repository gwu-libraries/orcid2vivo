from unittest import TestCase
import json
from app.affiliations import AffiliationsCrosswalk
import app.vivo_namespace as ns
from rdflib import Graph
from app.vivo_uri import HashIdentifierStrategy
from orcid2vivo import SimpleCreateEntitiesStrategy


class TestAffiliations(TestCase):

    def setUp(self):
        self.graph = Graph(namespace_manager=ns.ns_manager)
        self.person_uri = ns.D["test"]
        self.create_strategy = SimpleCreateEntitiesStrategy(person_uri=self.person_uri)
        self.crosswalker = AffiliationsCrosswalk(identifier_strategy=HashIdentifierStrategy(),
                                        create_strategy=self.create_strategy)

    def test_no_activities(self):
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

    def test_no_affiliations(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-activities": {
          "affiliations": null
        }
    }
}
        """)
        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertEqual(0, len(self.graph))

    def test_no_education(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-bio": {
            "orcid-activities": {
                "affiliations": {
                    "affiliation": [
                        {
                            "type": "EMPLOYMENT",
                            "department-name": "Gelman Library",
                            "role-title": "Science & Engineering Librarian",
                            "start-date": {
                                "year": {
                                    "value": "2013"
                                },
                                "month": {
                                    "value": "07"
                                },
                                "day": null
                            },
                            "end-date": null,
                            "organization": {
                                "name": "George Washington University",
                                "address": {
                                    "city": "Washington",
                                    "region": "DC",
                                    "country": "US"
                                },
                                "disambiguated-organization": {
                                    "disambiguated-organization-identifier": "8367",
                                    "disambiguation-source": "RINGGOLD"
                                }
                            },
                            "source": {
                                "source-orcid": {
                                    "value": null,
                                    "uri": "http://orcid.org/0000-0002-4192-3392",
                                    "path": "0000-0002-4192-3392",
                                    "host": "orcid.org"
                                },
                                "source-client-id": null,
                                "source-name": {
                                    "value": "Hope Lappen"
                                },
                                "source-date": {
                                    "value": 1386877638912
                                }
                            },
                            "created-date": {
                                "value": 1386877638912
                            },
                            "last-modified-date": {
                                "value": 1386877750045
                            },
                            "visibility": "PUBLIC",
                            "put-code": "25495"
                        }
                    ]
                }
            }
        }
    }
}
        """)
        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertEqual(0, len(self.graph))

    def test_education(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-activities": {
            "affiliations": {
                "affiliation": [
                    {
                        "type": "EDUCATION",
                        "department-name": "Neurosciences",
                        "role-title": "PhD",
                        "start-date": {
                            "year": {
                                "value": "1995"
                            },
                            "month" : {
                              "value" : "06"
                            },
                            "day" : {
                              "value" : "11"
                            }
                        },
                        "end-date": {
                            "year": {
                                "value": "1997"
                            },
                            "month" : {
                              "value" : "07"
                            },
                            "day" : {
                              "value" : "03"
                            }
                        },
                        "organization": {
                            "name": "Stanford University School of Medicine",
                            "address": {
                                "city": "Stanford",
                                "region": "California",
                                "country": "US"
                            },
                            "disambiguated-organization": null
                        },
                        "source": {
                            "source-orcid": {
                                "value": null,
                                "uri": "http://orcid.org/0000-0001-5109-3700",
                                "path": "0000-0001-5109-3700",
                                "host": "orcid.org"
                            },
                            "source-client-id": null,
                            "source-name": {
                                "value": "Laurel L Haak"
                            },
                            "source-date": {
                                "value": 1385568459467
                            }
                        },
                        "created-date": {
                            "value": 1385568459467
                        },
                        "last-modified-date": {
                            "value": 1406092743932
                        },
                        "visibility": "PUBLIC",
                        "put-code": "1006"
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
                ?awdgre a vivo:AwardedDegree .
                ?awdgre rdfs:label "PhD" .
                ?awdgre obo:RO_0002353 ?awdgreproc .
                ?awdgre vivo:assignedBy ?org .
                ?awdgre vivo:relates d:test, ?dgre .
                ?org a foaf:Organization .
                ?org rdfs:label "Stanford University School of Medicine" .
                ?org obo:RO_0001025 ?geo .
                ?geo rdfs:label "Stanford, California" .
                ?awdgreproc a vivo:EducationalProcess .
                ?awdgreproc obo:RO_0000057 ?org, d:test .
                ?awdgreproc vivo:dateTimeInterval ?awdgreprocint .
                ?awdgreproc vivo:departmentOrSchool "Neurosciences" .
                ?awdgreprocint a vivo:DateTimeInterval .
                ?awdgreprocint vivo:end ?awdgreprocintend .
                ?awdgreprocintend a vivo:DateTimeValue .
                ?awdgreprocintend rdfs:label "1997" .
                ?awdgreprocintend vivo:dateTime "1997-01-01T00:00:00"^^xsd:dateTime .
                ?awdgreprocintend vivo:dateTimePrecision vivo:yearPrecision .
                ?awdgreprocint vivo:start ?awdgreprocintstart .
                ?awdgreprocintstart a vivo:DateTimeValue .
                ?awdgreprocintstart rdfs:label "1995" .
                ?awdgreprocintstart vivo:dateTime "1995-01-01T00:00:00"^^xsd:dateTime .
                ?awdgreprocintstart vivo:dateTimePrecision vivo:yearPrecision .
            }
        """)))

    def test_education_minimal(self):
        orcid_profile = json.loads("""
{
    "message-version": "1.2",
    "orcid-profile": {
        "orcid-activities": {
            "affiliations": {
                "affiliation": [
                    {
                        "type": "EDUCATION",
                        "department-name": null,
                        "start-date": null,
                        "end-date": null,
                        "organization": {
                            "name": "Stanford University School of Medicine",
                            "address": {
                                "city": "Stanford",
                                "region": "California",
                                "country": "US"
                            },
                            "disambiguated-organization": null
                        },
                        "source": {
                            "source-orcid": {
                                "value": null,
                                "uri": "http://orcid.org/0000-0001-5109-3700",
                                "path": "0000-0001-5109-3700",
                                "host": "orcid.org"
                            },
                            "source-client-id": null,
                            "source-name": {
                                "value": "Laurel L Haak"
                            },
                            "source-date": {
                                "value": 1385568459467
                            }
                        },
                        "created-date": {
                            "value": 1385568459467
                        },
                        "last-modified-date": {
                            "value": 1406092743932
                        },
                        "visibility": "PUBLIC",
                        "put-code": "1006"
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
                ?org a foaf:Organization .
                ?org rdfs:label "Stanford University School of Medicine" .
                ?org obo:RO_0001025 ?geo .
                ?geo rdfs:label "Stanford, California" .
                ?awdgreproc a vivo:EducationalProcess .
                ?awdgreproc obo:RO_0000057 ?org, d:test .
            }
        """)))
