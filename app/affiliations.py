from vivo_namespace import VIVO, OBO
from rdflib import RDFS, RDF, Literal
from vivo_namespace import FOAF
from vivo_uri import to_hash_identifier, PREFIX_ORGANIZATION, PREFIX_DEGREE, \
    PREFIX_EDUCATIONAL_PROCESS
from utility import add_date, add_date_interval
import app.vivo_namespace as ns


def crosswalk_affiliations(orcid_profile, person_uri, graph):
    #Education
    for affiliation in (orcid_profile["orcid-profile"].get("orcid-activities") or {}).get("affiliations", {})\
            .get("affiliation", []):
        if affiliation["type"] == "EDUCATION":
            #Gather some values
            degree_name = affiliation.get("role-title")
            organization_name=affiliation["organization"]["name"]
            start_date_year = (affiliation["start-date"] or {}).get("year", {}).get("value")
            end_date_year = (affiliation["end-date"] or {}).get("year", {}).get("value")

            #Organization
            organization_uri = ns.D[to_hash_identifier(PREFIX_ORGANIZATION, (organization_name,))]
            graph.add((organization_uri, RDF.type, FOAF.Organization))
            graph.add((organization_uri, RDFS.label, Literal(organization_name)))
            if "address" in affiliation["organization"]:
                city = affiliation["organization"]["address"]["city"]
                state = affiliation["organization"]["address"]["region"]
            address_uri = ns.D[to_hash_identifier("geo", (city, state))]
            graph.add((address_uri, RDF.type, VIVO.GeographicLocation))
            graph.add((organization_uri, OBO.RO_0001025, address_uri))
            graph.add((address_uri, RDFS.label, Literal("%s, %s" % (city, state))))

            #Output of educational process
            educational_process_uri = ns.D[to_hash_identifier(PREFIX_EDUCATIONAL_PROCESS, (organization_name,
                                                                                           degree_name,
                                                                                           start_date_year,
                                                                                           end_date_year))]
            graph.add((educational_process_uri, RDF.type, VIVO.EducationalProcess))
            #Has participants
            graph.add((educational_process_uri, OBO.RO_0000057, organization_uri))
            graph.add((educational_process_uri, OBO.RO_0000057, person_uri))
            #Department
            if "department-name" in affiliation:
                graph.add((educational_process_uri, VIVO.departmentOrSchool,
                           Literal(affiliation["department-name"])))

            #Interval
            interval_uri = educational_process_uri + "-interval"
            interval_start_uri = interval_uri + "-start"
            # start_date_year = affiliation["start-date"]["year"]["value"] if "start-date" in affiliation else None
            interval_end_uri = interval_uri + "-end"
            # end_date_year = affiliation["end-date"]["year"]["value"] if "end-date" in affiliation else None
            add_date_interval(interval_uri, educational_process_uri, graph,
                              interval_start_uri if add_date(interval_start_uri, start_date_year, graph) else None,
                              interval_end_uri if add_date(interval_end_uri, end_date_year, graph) else None)

            if "role-title" in affiliation:
                degree_name = affiliation["role-title"]

                #Awarded degree
                awarded_degree_uri = educational_process_uri + "-dgre"
                graph.add((awarded_degree_uri, RDF.type, VIVO.AwardedDegree))
                graph.add((awarded_degree_uri, RDFS.label, Literal(degree_name)))

                #Assigned by organization
                graph.add((awarded_degree_uri, VIVO.assignedBy, organization_uri))

                #Related to educational process
                graph.add((awarded_degree_uri, OBO.RO_0002353, educational_process_uri))

                #Relates to degree
                degree_uri = ns.D[to_hash_identifier(PREFIX_DEGREE, (degree_name,))]
                graph.add((degree_uri, RDF.type, VIVO.AcademicDegree))
                graph.add((degree_uri, RDFS.label, Literal(degree_name)))
                graph.add((awarded_degree_uri, VIVO.relates, degree_uri))

                #Relates to person
                graph.add((awarded_degree_uri, VIVO.relates, person_uri))

