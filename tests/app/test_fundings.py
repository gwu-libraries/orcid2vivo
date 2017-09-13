#!/usr/bin/env python
# -*- coding: utf-8 -*-

from unittest import TestCase
from orcid2vivo_app.fundings import FundingCrosswalk
import orcid2vivo_app.vivo_namespace as ns
from orcid2vivo_app.vivo_uri import HashIdentifierStrategy
from orcid2vivo import SimpleCreateEntitiesStrategy

from rdflib import Graph, RDFS
import json


class TestFundings(TestCase):

    def setUp(self):
        self.graph = Graph(namespace_manager=ns.ns_manager)
        self.person_uri = ns.D["test"]
        self.create_strategy = SimpleCreateEntitiesStrategy(HashIdentifierStrategy(), person_uri=self.person_uri)
        self.crosswalker = FundingCrosswalk(identifier_strategy=self.create_strategy,
                                            create_strategy=self.create_strategy)

    def test_no_funding(self):
        orcid_profile = json.loads("""
{
  "activities-summary": {
    "fundings": {
      "group": []
    }
  }
}
        """)
        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        # Assert no triples in graph
        self.assertTrue(len(self.graph) == 0)

    def test_with_funding(self):
        orcid_profile = json.loads("""
{
  "activities-summary": {
"fundings": {
      "last-modified-date": {
        "value": 1444208097475
      },
      "group": [
        {
          "last-modified-date": {
            "value": 1437078970386
          },
          "external-ids": {
            "external-id": [
              {
                "external-id-type": "grant_number",
                "external-id-value": "0536999",
                "external-id-url": {
                  "value": "http://www.nsf.gov/awardsearch/showAward?AWD_ID=0536999&HistoricalAwards=false"
                },
                "external-id-relationship": "SELF"
              }
            ]
          },
          "funding-summary": [
            {
              "created-date": {
                "value": 1427825460988
              },
              "last-modified-date": {
                "value": 1437078970386
              },
              "source": {
                "source-orcid": null,
                "source-client-id": {
                  "uri": "http://orcid.org/client/0000-0003-2174-0924",
                  "path": "0000-0003-2174-0924",
                  "host": "orcid.org"
                },
                "source-name": {
                  "value": "ÜberWizard for ORCID"
                }
              },
              "title": {
                "title": {
                  "value": "ADVANCE Leadership Award: Women in Science and Engineering: A Guide to Maximizing their Potential"
                },
                "translated-title": null
              },
              "external-ids": {
                "external-id": [
                  {
                    "external-id-type": "grant_number",
                    "external-id-value": "0536999",
                    "external-id-url": {
                      "value": "http://www.nsf.gov/awardsearch/showAward?AWD_ID=0536999&HistoricalAwards=false"
                    },
                    "external-id-relationship": "SELF"
                  },
                  {
                    "external-id-type": "grant_number",
                    "external-id-value": "0536999",
                    "external-id-url": {
                      "value": "http://grants.uberresearch.com/100000081/0536999/ADVANCE-Leadership-Award-Women-in-Science-and-Engineering-A-Guide-to-Maximizing-their-Potential"
                    },
                    "external-id-relationship": "SELF"
                  }
                ]
              },
              "type": "GRANT",
              "start-date": {
                "year": {
                  "value": "2006"
                },
                "month": {
                  "value": "04"
                },
                "day": {
                  "value": "01"
                }
              },
              "end-date": {
                "year": {
                  "value": "2007"
                },
                "month": {
                  "value": "03"
                },
                "day": {
                  "value": "31"
                }
              },
              "organization": {
                "name": "National Science Foundation - Directorate for Education and Human Resources",
                "address": {
                  "city": "n/a",
                  "region": null,
                  "country": "US"
                },
                "disambiguated-organization": null
              },
              "visibility": "PUBLIC",
              "put-code": 74458,
              "path": "/0000-0001-5109-3700/funding/74458",
              "display-index": "0"
            }
          ]
        },
        {
          "last-modified-date": {
            "value": 1440583684368
          },
          "external-ids": {
            "external-id": [
              {
                "external-id-type": "grant_number",
                "external-id-value": "0305602",
                "external-id-url": {
                  "value": "http://www.nsf.gov/awardsearch/showAward?AWD_ID=0305602&HistoricalAwards=false"
                },
                "external-id-relationship": "SELF"
              }
            ]
          },
          "funding-summary": [
            {
              "created-date": {
                "value": 1440583684368
              },
              "last-modified-date": {
                "value": 1440583684368
              },
              "source": {
                "source-orcid": null,
                "source-client-id": {
                  "uri": "http://orcid.org/client/0000-0003-2174-0924",
                  "path": "0000-0003-2174-0924",
                  "host": "orcid.org"
                },
                "source-name": {
                  "value": "ÜberWizard for ORCID"
                }
              },
              "title": {
                "title": {
                  "value": "Postdoc Network Annual Policy Meeting; Berkeley, CA, March 15-17, 2003"
                },
                "translated-title": null
              },
              "external-ids": {
                "external-id": [
                  {
                    "external-id-type": "grant_number",
                    "external-id-value": "0305602",
                    "external-id-url": {
                      "value": "http://www.nsf.gov/awardsearch/showAward?AWD_ID=0305602&HistoricalAwards=false"
                    },
                    "external-id-relationship": "SELF"
                  },
                  {
                    "external-id-type": "grant_number",
                    "external-id-value": "0305602",
                    "external-id-url": {
                      "value": "http://grants.uberresearch.com/100000076/0305602/Postdoc-Network-Annual-Policy-Meeting-Berkeley-CA-March-15-17-2003"
                    },
                    "external-id-relationship": "SELF"
                  }
                ]
              },
              "type": "GRANT",
              "start-date": {
                "year": {
                  "value": "2003"
                },
                "month": {
                  "value": "03"
                },
                "day": {
                  "value": "01"
                }
              },
              "end-date": {
                "year": {
                  "value": "2004"
                },
                "month": {
                  "value": "02"
                },
                "day": {
                  "value": "29"
                }
              },
              "organization": {
                "name": "National Science Foundation - Directorate for Biological Sciences",
                "address": {
                  "city": "n/a",
                  "region": null,
                  "country": "US"
                },
                "disambiguated-organization": null
              },
              "visibility": "PUBLIC",
              "put-code": 105986,
              "path": "/0000-0001-5109-3700/funding/105986",
              "display-index": "0"
            }
          ]
        },
        {
          "last-modified-date": {
            "value": 1440583684380
          },
          "external-ids": {
            "external-id": [
              {
                "external-id-type": "grant_number",
                "external-id-value": "0342159",
                "external-id-url": {
                  "value": "http://www.nsf.gov/awardsearch/showAward?AWD_ID=0342159&HistoricalAwards=false"
                },
                "external-id-relationship": "SELF"
              }
            ]
          },
          "funding-summary": [
            {
              "created-date": {
                "value": 1440583684380
              },
              "last-modified-date": {
                "value": 1440583684380
              },
              "source": {
                "source-orcid": null,
                "source-client-id": {
                  "uri": "http://orcid.org/client/0000-0003-2174-0924",
                  "path": "0000-0003-2174-0924",
                  "host": "orcid.org"
                },
                "source-name": {
                  "value": "ÜberWizard for ORCID"
                }
              },
              "title": {
                "title": {
                  "value": "Policy Implications of International Graduate Students and Postdocs in the United States"
                },
                "translated-title": null
              },
              "external-ids": {
                "external-id": [
                  {
                    "external-id-type": "grant_number",
                    "external-id-value": "0342159",
                    "external-id-url": {
                      "value": "http://www.nsf.gov/awardsearch/showAward?AWD_ID=0342159&HistoricalAwards=false"
                    },
                    "external-id-relationship": "SELF"
                  },
                  {
                    "external-id-type": "grant_number",
                    "external-id-value": "0342159",
                    "external-id-url": {
                      "value": "http://grants.uberresearch.com/100000179/0342159/Policy-Implications-of-International-Graduate-Students-and-Postdocs-in-the-United-States"
                    },
                    "external-id-relationship": "SELF"
                  }
                ]
              },
              "type": "GRANT",
              "start-date": {
                "year": {
                  "value": "2004"
                },
                "month": {
                  "value": "03"
                },
                "day": {
                  "value": "01"
                }
              },
              "end-date": {
                "year": {
                  "value": "2006"
                },
                "month": {
                  "value": "02"
                },
                "day": {
                  "value": "28"
                }
              },
              "organization": {
                "name": "National Science Foundation - Office of the Director",
                "address": {
                  "city": "n/a",
                  "region": null,
                  "country": "US"
                },
                "disambiguated-organization": null
              },
              "visibility": "PUBLIC",
              "put-code": 105988,
              "path": "/0000-0001-5109-3700/funding/105988",
              "display-index": "0"
            }
          ]
        },
        {
          "last-modified-date": {
            "value": 1444208097475
          },
          "external-ids": {
            "external-id": [
              {
                "external-id-type": "grant_number",
                "external-id-value": "5F31MH010500-03",
                "external-id-url": {
                  "value": "http://projectreporter.nih.gov/project_info_description.cfm?aid=2241697"
                },
                "external-id-relationship": "SELF"
              }
            ]
          },
          "funding-summary": [
            {
              "created-date": {
                "value": 1444208097475
              },
              "last-modified-date": {
                "value": 1444208097475
              },
              "source": {
                "source-orcid": null,
                "source-client-id": {
                  "uri": "http://orcid.org/client/0000-0003-2174-0924",
                  "path": "0000-0003-2174-0924",
                  "host": "orcid.org"
                },
                "source-name": {
                  "value": "ÜberWizard for ORCID"
                }
              },
              "title": {
                "title": {
                  "value": "CELLULAR BASIS OF CIRCADIAN CLOCK IN SCN"
                },
                "translated-title": null
              },
              "external-ids": {
                "external-id": [
                  {
                    "external-id-type": "grant_number",
                    "external-id-value": "5F31MH010500-03",
                    "external-id-url": {
                      "value": "http://projectreporter.nih.gov/project_info_description.cfm?aid=2241697"
                    },
                    "external-id-relationship": "SELF"
                  },
                  {
                    "external-id-type": "grant_number",
                    "external-id-value": "5F31MH010500-03",
                    "external-id-url": {
                      "value": "http://grants.uberresearch.com/100000025/F31MH010500/CELLULAR-BASIS-OF-CIRCADIAN-CLOCK-IN-SCN"
                    },
                    "external-id-relationship": "SELF"
                  }
                ]
              },
              "type": "GRANT",
              "start-date": {
                "year": {
                  "value": "1994"
                },
                "month": {
                  "value": "10"
                },
                "day": {
                  "value": "01"
                }
              },
              "end-date": null,
              "organization": {
                "name": "National Institute of Mental Health",
                "address": {
                  "city": "Bethesda",
                  "region": null,
                  "country": "US"
                },
                "disambiguated-organization": null
              },
              "visibility": "PUBLIC",
              "put-code": 116401,
              "path": "/0000-0001-5109-3700/funding/116401",
              "display-index": "0"
            }
          ]
        }
      ],
      "path": "/0000-0001-5109-3700/fundings"
    }
  }
}
                """)
        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        # Verify a grant exists.
        grant_uri = ns.D['grant-9ea22d7c992375778b4a3066f5142624']
        self.assertEqual(
            self.graph.value(grant_uri, RDFS.label).toPython(),
            u"Policy Implications of International Graduate Students and Postdocs in the United States"
        )
        # Verify three PI roles related to grants for this person uri.
        pi_roles = [guri for guri in self.graph.subjects(predicate=ns.OBO['RO_0000052'], object=self.person_uri)]
        self.assertEqual(len(pi_roles), 4)

    def test_with_funding(self):
        orcid_profile = json.loads("""
{
  "activities-summary": {
    "fundings": {
      "last-modified-date": {
        "value": 1449261003455
      },
      "group": [
        {
          "last-modified-date": {
            "value": 1449261003455
          },
          "external-ids": {
            "external-id": []
          },
          "funding-summary": [
            {
              "created-date": {
                "value": 1449261003455
              },
              "last-modified-date": {
                "value": 1449261003455
              },
              "source": {
                "source-orcid": {
                  "uri": "http://orcid.org/0000-0003-3844-5120",
                  "path": "0000-0003-3844-5120",
                  "host": "orcid.org"
                },
                "source-client-id": null,
                "source-name": {
                  "value": "Ira Lurie"
                }
              },
              "title": {
                "title": {
                  "value": "The Utility of Ultra High Performance Supercritical Fluid Chromatography for the Analysis of Seized Drugs:  Application to Synthetic Cannabinoids and Bath Salts "
                },
                "translated-title": null
              },
              "external-ids": null,
              "type": "GRANT",
              "start-date": {
                "year": {
                  "value": "2015"
                },
                "month": {
                  "value": "01"
                },
                "day": null
              },
              "end-date": {
                "year": {
                  "value": "2016"
                },
                "month": {
                  "value": "12"
                },
                "day": null
              },
              "organization": {
                "name": "National Institute of Justice",
                "address": {
                  "city": "DC",
                  "region": "DC",
                  "country": "US"
                },
                "disambiguated-organization": {
                  "disambiguated-organization-identifier": "http://dx.doi.org/10.13039/100005289",
                  "disambiguation-source": "FUNDREF"
                }
              },
              "visibility": "PUBLIC",
              "put-code": 132761,
              "path": "/0000-0003-3844-5120/funding/132761",
              "display-index": "0"
            }
          ]
        }
      ],
      "path": "/0000-0003-3844-5120/fundings"
    }
  }
}
                """)
        self.crosswalker.crosswalk(orcid_profile, self.person_uri, self.graph)
        # Verify a grant exists.
        grant_uri = ns.D['grant-742228eecfbdacf092bf482f84151082']
        self.assertEqual(
            self.graph.value(grant_uri, RDFS.label).toPython(),
            u"The Utility of Ultra High Performance Supercritical Fluid Chromatography for the Analysis of Seized "
            u"Drugs:  Application to Synthetic Cannabinoids and Bath Salts "
        )
        self.assertEqual(0, len(list(self.graph[grant_uri : ns.VIVO.sponsorAwardId : ])))
