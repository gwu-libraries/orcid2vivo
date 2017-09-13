from vivo_namespace import VIVO
from rdflib import RDFS, RDF, Literal, XSD
from utility import join_if_not_empty
from vivo_namespace import VCARD, OBO, FOAF


class BioCrosswalk:
    def __init__(self, identifier_strategy, create_strategy):
        self.identifier_strategy = identifier_strategy
        self.create_strategy = create_strategy

    def crosswalk(self, orcid_profile, person_uri, graph, person_class=FOAF.Person):

        # Get names (for person and name vcard)
        given_names = None
        family_name = None
        if "name" in orcid_profile["person"]:
            person_details = orcid_profile["person"]["name"]
            given_names = person_details.get("given-names", {}).get("value")
            family_name = person_details.get("family-name", {}).get("value")
            full_name = join_if_not_empty((given_names, family_name))

            # Following is non-vcard bio information

            # If skip_person, then don't create person and add names
            if full_name and self.create_strategy.should_create(person_class, person_uri):
                # Add person
                graph.add((person_uri, RDF.type, person_class))
                graph.add((person_uri, RDFS.label, Literal(full_name)))

        # Biography
        if "biography" in orcid_profile["person"]:
            biography = orcid_profile["person"]["biography"]["content"]
            if biography:
                graph.add((person_uri, VIVO.overview, Literal(biography)))

        # Other identifiers
        # Default VIVO-ISF only supports a limited number of identifier types.
        if "external-identifiers" in orcid_profile["person"]:
            external_identifiers = orcid_profile["person"]["external-identifiers"]["external-identifier"]
            for external_identifier in external_identifiers:
                # Scopus ID
                if external_identifier["external-id-type"] == "Scopus Author ID":
                    graph.add((person_uri, VIVO.scopusId, Literal(external_identifier["external-id-value"])))

                # ISI Research ID
                if external_identifier["external-id-type"] == "ResearcherID":
                    graph.add((person_uri, VIVO.researcherId, Literal(external_identifier["external-id-value"])))

        # Keywords
        if "keywords" in orcid_profile["person"]:
            keywords = orcid_profile["person"]["keywords"]["keyword"]
            for keyword in keywords:
                keywords_content = keyword["content"]
                if keywords_content:
                    for keyword_content in keywords_content.split(", "):
                        graph.add((person_uri, VIVO.freetextKeyword, Literal(keyword_content)))

        # Following is vcard bio information

        # Add main vcard
        vcard_uri = self.identifier_strategy.to_uri(VCARD.Individual, {"person_uri": person_uri})
        # Will only add vcard if there is a child vcard
        add_main_vcard = False

        # Name vcard
        vcard_name_uri = self.identifier_strategy.to_uri(VCARD.Name, {"person_uri": person_uri})
        if (given_names or family_name) and self.create_strategy.should_create(VCARD.Name, vcard_name_uri):
            graph.add((vcard_name_uri, RDF.type, VCARD.Name))
            graph.add((vcard_uri, VCARD.hasName, vcard_name_uri))
            if given_names:
                graph.add((vcard_name_uri, VCARD.givenName, Literal(given_names)))
            if family_name:
                graph.add((vcard_name_uri, VCARD.familyName, Literal(family_name)))
            add_main_vcard = True

        # Websites
        if "researcher-urls" in orcid_profile["person"]:
            researcher_urls = orcid_profile["person"]["researcher-urls"]["researcher-url"]
            for researcher_url in researcher_urls:
                url = researcher_url["url"]["value"]
                url_name = researcher_url["url-name"]
                vcard_website_uri = self.identifier_strategy.to_uri(VCARD.URL, {"url": url})
                graph.add((vcard_website_uri, RDF.type, VCARD.URL))
                graph.add((vcard_uri, VCARD.hasURL, vcard_website_uri))
                graph.add((vcard_website_uri, VCARD.url, Literal(url, datatype=XSD.anyURI)))
                if url_name:
                    graph.add((vcard_website_uri, RDFS.label, Literal(url_name)))
                add_main_vcard = True

        if add_main_vcard and self.create_strategy.should_create(VCARD.Individual, vcard_uri):
            graph.add((vcard_uri, RDF.type, VCARD.Individual))
            # Contact info for
            graph.add((vcard_uri, OBO.ARG_2000029, person_uri))
