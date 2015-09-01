#!/usr/bin/env python

import requests
import argparse
import codecs
from rdflib import Literal, Graph, URIRef
from rdflib.namespace import Namespace
from orcid2vivo_app.vivo_uri import HashIdentifierStrategy
from orcid2vivo_app.vivo_namespace import VIVO, FOAF
from orcid2vivo_app.affiliations import AffiliationsCrosswalk
from orcid2vivo_app.bio import BioCrosswalk
from orcid2vivo_app.fundings import FundingCrosswalk
from orcid2vivo_app.works import WorksCrosswalk
from orcid2vivo_app.utility import sparql_insert, clean_orcid
import orcid2vivo_app.vivo_namespace as ns


class SimpleCreateEntitiesStrategy():
    """
    A minimally configurable strategy for determining if ancillary entities
    should be created.

    Except for a few configurable options, entities are always created.

    Other implementations must implement should_create().
    """
    def __init__(self, skip_person=False, person_uri=None):
        self.skip_person = skip_person
        self.person_uri = person_uri

    def should_create(self, clazz, uri):
        """
        Determine whether an entity should be created.
        :param clazz: Class of the entity.
        :param uri: URI of the entity.
        :return: True if the entity should be created.
        """
        if self.skip_person and self.person_uri == uri:
            return False
        return True


class PersonCrosswalk():
    def __init__(self, identifier_strategy=HashIdentifierStrategy(), create_strategy=SimpleCreateEntitiesStrategy()):
        self.identifier_strategy = identifier_strategy
        self.create_strategy = create_strategy
        self.bio_crosswalker = BioCrosswalk(identifier_strategy, create_strategy)
        self.affiliations_crosswalker = AffiliationsCrosswalk(identifier_strategy, create_strategy)
        self.funding_crosswalker = FundingCrosswalk(identifier_strategy, create_strategy)
        self.works_crosswalker = WorksCrosswalk(identifier_strategy, create_strategy)

    def crosswalk(self, orcid_id, person_uri, person_class=None):

        #Create an RDFLib Graph
        graph = Graph(namespace_manager=ns.ns_manager)

        #0000-0003-3441-946X
        orcid = clean_orcid(orcid_id)
        orcid_profile = fetch_orcid_profile(orcid)

        #Determine the class to use for the person
        person_clazz = FOAF.Person
        if person_class:
            person_clazz = getattr(VIVO, person_class)

        #ORCID
        graph.add((person_uri, VIVO.orcidId, Literal("http://orcid.org/%s" % orcid)))

        self.bio_crosswalker.crosswalk(orcid_profile, person_uri, graph, person_class=person_clazz)
        self.works_crosswalker.crosswalk(orcid_profile, person_uri, graph)
        self.affiliations_crosswalker.crosswalk(orcid_profile, person_uri, graph)
        self.funding_crosswalker.crosswalk(orcid_profile, person_uri, graph)

        return graph, orcid_profile, person_uri


def fetch_orcid_profile(orcid_id):
    orcid = clean_orcid(orcid_id)
    #curl -H "Accept: application/orcid+json" 'http://pub.orcid.org/v1.2/0000-0003-3441-946X/orcid-profile' -L -i
    r = requests.get('http://pub.orcid.org/v1.2/%s/orcid-profile' % orcid,
                     headers={"Accept": "application/orcid+json"})
    if r:
        return r.json()
    else:
        raise Exception("Request to fetch ORCID profile for %s returned %s" % (id, r.status_code))


def set_namespace(namespace=None):
    #Set default VIVO namespace
    if namespace:
        ns.D = Namespace(namespace)
        ns.ns_manager.bind('d', ns.D, replace=True)


def default_execute(orcid_id, namespace=None, person_uri=None, person_id=None, skip_person=False, person_class=None):
    #Set namespace
    set_namespace(namespace)

    this_identifier_strategy = HashIdentifierStrategy()
    this_person_uri = URIRef(person_uri) if person_uri \
        else this_identifier_strategy.to_uri(FOAF.Person, {"id": person_id or orcid_id})

    this_create_strategy = SimpleCreateEntitiesStrategy(skip_person=skip_person, person_uri=this_person_uri)

    crosswalker = PersonCrosswalk(create_strategy=this_create_strategy, identifier_strategy=this_identifier_strategy)
    return crosswalker.crosswalk(orcid_id, this_person_uri, person_class=person_class)


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
    parser.add_argument("--person-uri", dest="person_uri", help="A URI for the person. If not provided, one will be "
                                                                "created from the orcid id or person id.")
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

    #Excute with default strategies
    (g, p, per_uri) = default_execute(args.orcid_id, namespace=args.namespace, person_uri=args.person_uri,
                                      person_id=args.person_id, skip_person=args.skip_person,
                                      person_class=args.person_class)

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
