from vivo_namespace import VIVO, OBO, FOAF, VCARD
from rdflib import RDF, RDFS, XSD, Literal
from utility import add_date, add_date_interval


class FundingCrosswalk():
    def __init__(self, identifier_strategy, create_strategy):
        self.identifier_strategy = identifier_strategy
        self.create_strategy = create_strategy

    def crosswalk(self, orcid_profile, person_uri, graph):
        if "funding-list" in orcid_profile["orcid-profile"]["orcid-activities"] \
                and orcid_profile["orcid-profile"]["orcid-activities"]["funding-list"] \
                and "funding" in orcid_profile["orcid-profile"]["orcid-activities"]["funding-list"]:
            #Funding
            fundings = orcid_profile["orcid-profile"]["orcid-activities"]["funding-list"]["funding"]
            for funding in fundings:
                if funding["funding-type"] == "GRANT":

                    title = funding["funding-title"]["title"]["value"]
                    grant_uri = self.identifier_strategy.to_uri(VIVO.Grant, {"title": title})
                    #Type
                    graph.add((grant_uri, RDF.type, VIVO.Grant))

                    #Person
                    graph.add((grant_uri, VIVO.relates, person_uri))

                    #Title
                    graph.add((grant_uri, RDFS.label, Literal(title)))

                    #Role
                    role_uri = self.identifier_strategy.to_uri(VIVO.PrincipalInvestigatorRole, {"grant_uri": grant_uri})
                    graph.add((role_uri, RDF.type, VIVO.PrincipalInvestigatorRole))
                    #Inheres in
                    graph.add((role_uri, OBO.RO_0000052, person_uri))
                    graph.add((role_uri, VIVO.relatedBy, grant_uri))

                    #Date interval
                    (start_year, start_month, start_day) = FundingCrosswalk._get_date_parts("start-date", funding)
                    (end_year, end_month, end_day) = FundingCrosswalk._get_date_parts("end-date", funding)

                    add_date_interval(grant_uri, graph, self.identifier_strategy,
                                      add_date(start_year, graph, self.identifier_strategy, start_month, start_day),
                                      add_date(end_year, graph, self.identifier_strategy, end_month, end_day))

                    #Award amount
                    funding_amount = funding.get("amount")
                    if funding_amount is not None:
                        value = funding_amount.get("value")
                        if value is not None:
                            award_amount = "${:,}".format(int(value))
                            graph.add((grant_uri, VIVO.totalAwardAmount, Literal(award_amount)))

                    #Awarded by
                    if "organization" in funding:
                        organization_name = funding["organization"]["name"]
                        organization_uri = self.identifier_strategy.to_uri(FOAF.Organization,
                                                                           {"name": organization_name})
                        graph.add((grant_uri, VIVO.assignedBy, organization_uri))
                        if self.create_strategy.should_create(FOAF.Organization, organization_uri):
                            graph.add((organization_uri, RDF.type, FOAF.Organization))
                            graph.add((organization_uri, RDFS.label, Literal(organization_name)))

                    #Identifiers
                    if "funding-external-identifiers" in funding:
                        for external_identifier in funding["funding-external-identifiers"]["funding-external-identifier"]:
                            if "funding-external-identifier-value" in external_identifier:
                                graph.add((grant_uri, VIVO.sponsorAwardId,
                                           Literal(external_identifier["funding-external-identifier-value"])))
                            identifier_url = (external_identifier.get("funding-external-identifier-url", {}) or {}).get("value")
                            if identifier_url:
                                vcard_uri = self.identifier_strategy.to_uri(VCARD.Kind, {"url": identifier_url})
                                graph.add((vcard_uri, RDF.type, VCARD.Kind))
                                #Has contact info
                                graph.add((grant_uri, OBO.ARG_2000028, vcard_uri))
                                #Url vcard
                                vcard_url_uri = self.identifier_strategy.to_uri(VCARD.URL, {"vcard_uri": vcard_uri})
                                graph.add((vcard_url_uri, RDF.type, VCARD.URL))
                                graph.add((vcard_uri, VCARD.hasURL, vcard_url_uri))
                                graph.add((vcard_url_uri, VCARD.url, Literal(identifier_url, datatype=XSD.anyURI)))

    @staticmethod
    def _get_date_parts(field_name, funding):
        date = funding.get(field_name, {}) or {}
        return (date.get("year", {}) or {}).get("value"), \
               (date.get("month", {}) or {}).get("value"), \
               (date.get("day", {}) or {}).get("value")
