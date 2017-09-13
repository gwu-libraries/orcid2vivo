from unittest import TestCase
import json
from orcid2vivo_app.affiliations import AffiliationsCrosswalk
import orcid2vivo_app.vivo_namespace as ns
from rdflib import Graph
from orcid2vivo_app.vivo_uri import HashIdentifierStrategy
from orcid2vivo import SimpleCreateEntitiesStrategy


class TestAffiliations(TestCase):

    def setUp(self):
        self.graph = Graph(namespace_manager=ns.ns_manager)
        self.person_uri = ns.D["test"]
        self.create_strategy = SimpleCreateEntitiesStrategy(HashIdentifierStrategy(), person_uri=self.person_uri)
        self.crosswalker = AffiliationsCrosswalk(identifier_strategy=self.create_strategy,
                                                 create_strategy=self.create_strategy)

    def test_no_affiliations(self):
        orcid_profile = json.loads("""
{
  "activities-summary": {
  }
}
        """)
        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertEqual(0, len(self.graph))

    def test_no_education(self):
        orcid_profile = json.loads("""
{
  "activities-summary": {
    "educations": {
        "education-summary": []
    }
  }
}
""")
        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        self.assertEqual(0, len(self.graph))

    def test_education(self):
        orcid_profile = json.loads("""
{
  "activities-summary": {
    "educations": {
      "last-modified-date": {
        "value": 1486085029078
      },
      "education-summary": [
        {
          "created-date": {
            "value": 1385568459467
          },
          "last-modified-date": {
            "value": 1486085026897
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
          "department-name": "Neurosciences",
          "role-title": "PhD",
          "start-date": {
            "year": {
              "value": "1995"
            },
            "month": null,
            "day": null
          },
          "end-date": {
            "year": {
              "value": "1997"
            },
            "month": null,
            "day": null
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
          "visibility": "PUBLIC",
          "put-code": 1006,
          "path": "/0000-0001-5109-3700/education/1006"
        }
      ],
      "path": "/0000-0001-5109-3700/educations"
    }
  }  
}
        """)
        # Changed start date to 1995
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
  "activities-summary": {
    "educations": {
      "last-modified-date": {
        "value": 1486085029078
      },
      "education-summary": [
        {
          "created-date": {
            "value": 1385568459467
          },
          "last-modified-date": {
            "value": 1486085026897
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
          "department-name": null,
          "role-title": "PhD",
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
          "visibility": "PUBLIC",
          "put-code": 1006,
          "path": "/0000-0001-5109-3700/education/1006"
        }
      ],
      "path": "/0000-0001-5109-3700/educations"
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
                filter not exists {
                    ?awdgreproc vivo:departmentOrSchool ?awdgredept .
                }
            }
        """)))
