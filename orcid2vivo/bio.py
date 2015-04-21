from vivo_namespace import VIVO
from rdflib import Literal


def crosswalk_bio(orcid_profile, person_uri, graph):
    #Other identifiers
    external_identifiers = orcid_profile["orcid-profile"]["orcid-bio"]["external-identifiers"]["external-identifier"]
    for external_identifier in external_identifiers:
        if external_identifier["external-id-common-name"]["value"] == "Scopus Author ID":
            graph.add((person_uri, VIVO.scopusId, Literal(external_identifier["external-id-reference"]["value"])))
