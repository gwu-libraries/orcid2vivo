from vivo_namespace import D, VIVO, OBO, FOAF, VCARD
from vivo_uri import to_hash_identifier, PREFIX_GRANT, PREFIX_ORGANIZATION
from rdflib import RDF, RDFS, XSD, Literal
from utility import add_date, add_date_interval


def crosswalk_funding(orcid_profile, person_uri, graph):
    #Funding
    fundings = orcid_profile["orcid-profile"]["orcid-activities"]["funding-list"]["funding"]
    for funding in fundings:
        if funding["funding-type"] == "GRANT":

            title = funding["funding-title"]["title"]["value"]
            grant_uri = D[to_hash_identifier(PREFIX_GRANT, (title,))]
            #Type
            graph.add((grant_uri, RDF.type, VIVO.Grant))

            #Person
            graph.add((grant_uri, VIVO.relates, person_uri))

            #Title
            graph.add((grant_uri, RDFS.label, Literal(title)))

            #Role
            role_uri = grant_uri + "-role"
            graph.add((role_uri, RDF.type, VIVO.PrincipalInvestigatorRole))
            #Inheres in
            graph.add((role_uri, OBO.RO_0000052, person_uri))
            graph.add((role_uri, VIVO.relatedBy, grant_uri))

            #Date interval
            interval_uri = grant_uri + "-interval"
            interval_start_uri = interval_uri + "-start"
            interval_end_uri = interval_uri + "-end"
            start_year = funding["start-date"]["year"]["value"] \
                if "start-date" in funding and "year" in funding["start-date"] else None
            start_month = funding["start-date"]["month"]["value"] \
                if "start-date" in funding and "month" in funding["start-date"] else None
            start_day = funding["start-date"]["day"]["value"] \
                if "start-date" in funding and "day" in funding["start-date"] else None
            end_year = funding["end-date"]["year"]["value"] \
                if "end-date" in funding and "year" in funding["start-date"] else None
            end_month = funding["end-date"]["month"]["value"] \
                if "end-date" in funding and "month" in funding["start-date"] else None
            end_day = funding["end-date"]["day"]["value"] \
                if "end-date" in funding and "day" in funding["start-date"] else None

            add_date_interval(interval_uri, grant_uri, graph,
                              interval_start_uri if add_date(interval_start_uri,
                                                             start_year,
                                                             graph,
                                                             start_month,
                                                             start_day) else None,
                              interval_end_uri if add_date(interval_end_uri,
                                                           end_year,
                                                           graph,
                                                           end_month,
                                                           end_day) else None)

            #Award amount
            if "amount" in funding:
                award_amount = "${:,}".format(int(funding["amount"]["value"]))
                graph.add((grant_uri, VIVO.totalAwardAmount, Literal(award_amount)))

            #Awarded by
            if "organization" in funding:
                organization_name = funding["organization"]["name"]
                organization_uri = D[to_hash_identifier(PREFIX_ORGANIZATION, (organization_name,))]
                graph.add((organization_uri, RDF.type, FOAF.Organization))
                graph.add((organization_uri, RDFS.label, Literal(organization_name)))
                graph.add((grant_uri, VIVO.assignedBy, organization_uri))

            #Identifiers
            if "funding-external-identifiers" in funding:
                for external_identifier in funding["funding-external-identifiers"]["funding-external-identifier"]:
                    if "funding-external-identifier-value" in external_identifier:
                        graph.add((grant_uri,
                               VIVO.sponsorAwardId, Literal(external_identifier["funding-external-identifier-value"])))
                    if "funding-external-identifier-url" in external_identifier:
                        identifier_url = external_identifier["funding-external-identifier-url"]["value"]
                        vcard_uri = D[to_hash_identifier("vcard", (identifier_url,))]
                        graph.add((vcard_uri, RDF.type, VCARD.Kind))
                        #Has contact info
                        graph.add((grant_uri, OBO.ARG_2000028, vcard_uri))
                        #Url vcard
                        vcard_url_uri = vcard_uri + "-url"
                        graph.add((vcard_url_uri, RDF.type, VCARD.URL))
                        graph.add((vcard_uri, VCARD.hasURL, vcard_url_uri))
                        graph.add((vcard_url_uri, VCARD.url, Literal(identifier_url, datatype=XSD.anyURI)))
