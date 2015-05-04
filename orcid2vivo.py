import requests
import argparse
import codecs
from rdflib import Literal, Graph
from rdflib.namespace import Namespace
from app.vivo_namespace import VIVO, FOAF
from app.affiliations import crosswalk_affiliations
from app.bio import crosswalk_bio
from app.fundings import crosswalk_funding
from app.works import crosswalk_works
from app.utility import sparql_insert
import app.vivo_namespace as ns


def crosswalk(orcid_id, vivo_person_id=None, person_class=None, skip_person=False, namespace=None):

    #Set default VIVO namespace
    if namespace:
        ns.D = Namespace(namespace)
        ns.ns_manager.bind('d', ns.D, replace=True)

    #Create an RDFLib Graph
    graph = Graph(namespace_manager=ns.ns_manager)

    #0000-0003-3441-946X
    orcid_profile = fetch_orcid_profile(orcid_id)

    #Determine the class to use for the person
    person_clazz = FOAF.Person
    if person_class:
        person_clazz = getattr(VIVO, person_class)

    #ORCID
    person_uri = ns.D[vivo_person_id or orcid_id]
    graph.add((person_uri, VIVO.orcidId, Literal("http://orcid.org/%s" % orcid_id)))

    crosswalk_bio(orcid_profile, person_uri, graph, person_class=person_clazz, skip_person=skip_person)
    crosswalk_works(orcid_profile, person_uri, graph)
    crosswalk_affiliations(orcid_profile, person_uri, graph)
    crosswalk_funding(orcid_profile, person_uri, graph)

    return graph, orcid_profile, person_uri


def fetch_orcid_profile(orcid_id):
    #curl -H "Accept: application/orcid+json" 'http://pub.orcid.org/v1.2/0000-0003-3441-946X/orcid-profile' -L -i
    r = requests.get('http://pub.orcid.org/v1.2/%s/orcid-profile' % orcid_id,
                     headers={"Accept": "application/orcid+json"})
    if r:
        return r.json()
    else:
        raise Exception("Request to fetch ORCID profile for %s returned %s" % (id, r.status_code))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("orcid_id")
    parser.add_argument("--format", default="turtle", choices=["xml", "n3", "turtle", "nt", "pretty-xml", "trix"],
                        help="The RDF format for serializing. Default is turtle.")
    parser.add_argument("--file", help="Filepath to which to serialize.")
    parser.add_argument("--endpoint", dest="endpoint",
                        help="Endpoint for SPARQL Update of VIVO instance,e.g., http://localhost/vivo/api/sparqlUpdate."
                             " Also provide --username and --password.")
    parser.add_argument("--username", dest="username", help="Username for VIVO root.")
    parser.add_argument("--password", dest="password",
                        help="Password for VIVO root.")
    parser.add_argument("--person-id", dest="person_id", help="Id for the person to use when constructing the person's "
                                                              "URI. If not provided, the orcid id will be used.")
    parser.add_argument("--namespace", default="http://vivo.mydomain.edu/individual/",
                        help="VIVO namespace. Default is http://vivo.mydomain.edu/individual/.")
    parser.add_argument("--person-class", dest="person_class",
                        choices=["FacultyMember", "FacultyMemberEmeritus", "Librarian", "LibrarianEmeritus",
                                 "NonAcademic", "NonFacultyAcademic", "ProfessorEmeritus", "Student"],
                        help="Class (in VIVO Core ontology) for a person. Default is a FOAF Person.")
    parser.add_argument("--skip-person", dest="skip_person", action="store_true",
                        help="Skip adding triples declaring the person and the person's name.")

    #Parse
    args = parser.parse_args()

    (g, p, per_uri) = crosswalk(args.orcid_id, vivo_person_id=args.person_id, person_class=args.person_class,
                                skip_person=args.skip_person, namespace=args.namespace)

    #Write to file
    if args.file:
        with codecs.open(args.file, "w") as out:
            g.serialize(format=args.format, destination=out)

    #Post to SPARQL Update
    if args.endpoint:
        if not args.username or not args.password:
            raise Exception("If an endpoint is specified, --username and --password must be provided.")
        sparql_insert(g, args.endpoint, args.username, args.password)

    #If not writing to file to posting to SPARQL Update then serialize to stdout
    if not args.file and not args.endpoint:
        print g.serialize(format=args.format)

    #TODO Add logging