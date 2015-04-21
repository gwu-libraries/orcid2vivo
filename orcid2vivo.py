import requests
from orcid2vivo.vivo_namespace import *
from rdflib import Literal, Graph
from orcid2vivo.affiliations import crosswalk_affiliations
from orcid2vivo.bio import crosswalk_bio
from orcid2vivo.fundings import crosswalk_funding
from orcid2vivo.works import crosswalk_works


def crosswalk_orcid_profile(orcid_profile, vivo_person_id, graph):
    person_uri = D[vivo_person_id]

    #ORCID
    orcid = orcid_profile["orcid-profile"]["orcid-identifier"]["path"]
    graph.add((person_uri, VIVO.orcidId, Literal(orcid)))

    crosswalk_bio(orcid_profile, person_uri, graph)
    crosswalk_works(orcid_profile, person_uri, graph)
    crosswalk_affiliations(orcid_profile, person_uri, graph)
    crosswalk_funding(orcid_profile, person_uri, graph)


def fetch_orcid_profile(orcid_id):
    #curl -H "Accept: application/orcid+json" 'http://pub.orcid.org/v1.2/0000-0003-3441-946X/orcid-profile' -L -i
    r = requests.get('http://pub.orcid.org/v1.2/%s/orcid-profile' % orcid_id,
                     headers={"Accept": "application/orcid+json"})
    if r:
        return r.json()
    else:
        raise Exception("Request to fetch ORCID profile for %s returned %s" % (id, r.status_code))


if __name__ == '__main__':
    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)

    p = fetch_orcid_profile('0000-0003-3441-946X')
    #print json.dumps(profile, indent=4)
    crosswalk_orcid_profile(p, "per-7896ae72b37a8eb0dc5faad32da0eefe", g)

    # print "To add %s triples:\n%s" % (len(g), g.serialize(format="turtle"))
    print g.serialize(format="turtle")

    #sparql_load(graph, "/usr/local/apache2/htdocs")
