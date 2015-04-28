from vivo_namespace import VIVO
from rdflib import RDFS, RDF, Literal
from utility import join_if_not_empty
from vivo_namespace import VCARD, OBO, FOAF


def crosswalk_bio(orcid_profile, person_uri, graph, skip_person=False, person_class=FOAF.Person):

    #If skip_person, then don't create person and add names
    if not skip_person:
        person_details = orcid_profile["orcid-profile"]["orcid-bio"]["personal-details"]
        given_names = person_details["given-names"]["value"] if "given-names" in person_details else None
        family_name = person_details["family-name"]["value"] if "family-name" in person_details else None
        full_name = join_if_not_empty((given_names, family_name))

        ##Person
        graph.add((person_uri, RDF.type, person_class))
        graph.add((person_uri, RDFS.label, Literal(full_name)))
        #Note that not assigning class here.

        ##vcard
        #Main vcard
        vcard_uri = person_uri + "-vcard"
        graph.add((vcard_uri, RDF.type, VCARD.Individual))
        #Contact info for
        graph.add((vcard_uri, OBO.ARG_2000029, person_uri))
        #Name vcard
        vcard_name_uri = person_uri + "-vcard-name"
        graph.add((vcard_name_uri, RDF.type, VCARD.Name))
        graph.add((vcard_uri, VCARD.hasName, vcard_name_uri))
        if given_names:
            graph.add((vcard_name_uri, VCARD.givenName, Literal(given_names)))
        if family_name:
            graph.add((vcard_name_uri, VCARD.familyName, Literal(family_name)))

    #Other identifiers
    if "external-identifiers" in orcid_profile["orcid-profile"]["orcid-bio"] \
            and orcid_profile["orcid-profile"]["orcid-bio"]["external-identifiers"] \
            and "external-identifier" in orcid_profile["orcid-profile"]["orcid-bio"]["external-identifiers"]:
        external_identifiers = orcid_profile["orcid-profile"]["orcid-bio"]["external-identifiers"]["external-identifier"]
        for external_identifier in external_identifiers:
            if external_identifier["external-id-common-name"]["value"] == "Scopus Author ID":
                graph.add((person_uri, VIVO.scopusId, Literal(external_identifier["external-id-reference"]["value"])))
