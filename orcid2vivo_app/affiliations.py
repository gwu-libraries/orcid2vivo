from vivo_namespace import VIVO, OBO
from rdflib import RDFS, RDF, Literal
from vivo_namespace import FOAF
from vivo_uri import to_hash_identifier
from utility import add_date, add_date_interval
import orcid2vivo_app.vivo_namespace as ns


class AffiliationsCrosswalk():
    def __init__(self, identifier_strategy, create_strategy):
        self.identifier_strategy = identifier_strategy
        self.create_strategy = create_strategy

    def crosswalk(self, orcid_profile, person_uri, graph):
        #Education
        for affiliation in ((orcid_profile["orcid-profile"].get("orcid-activities") or {})
                            .get("affiliations", {}) or {}).get("affiliation", []):
            if affiliation["type"] == "EDUCATION":
                #Gather some values
                degree_name = affiliation.get("role-title")
                organization_name=affiliation["organization"]["name"]
                start_date_year = (affiliation["start-date"] or {}).get("year", {}).get("value")
                end_date_year = (affiliation["end-date"] or {}).get("year", {}).get("value")

                #Organization
                organization_uri = self.identifier_strategy.to_uri(FOAF.Organization, {"name": organization_name})
                if self.create_strategy.should_create(FOAF.Organization, organization_uri):
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
                educational_process_uri = self.identifier_strategy.to_uri(VIVO.EducationalProcess,
                                                                          {"organization_name": organization_name,
                                                                           "degree_name": degree_name,
                                                                           "start_year": start_date_year,
                                                                           "end_year": end_date_year})
                graph.add((educational_process_uri, RDF.type, VIVO.EducationalProcess))
                #Has participants
                graph.add((educational_process_uri, OBO.RO_0000057, organization_uri))
                graph.add((educational_process_uri, OBO.RO_0000057, person_uri))
                #Department
                if "department-name" in affiliation:
                    graph.add((educational_process_uri, VIVO.departmentOrSchool,
                               Literal(affiliation["department-name"])))

                #Interval
                add_date_interval(educational_process_uri, graph, self.identifier_strategy,
                                  add_date(start_date_year, graph, self.identifier_strategy),
                                  add_date(end_date_year, graph, self.identifier_strategy))

                if "role-title" in affiliation:
                    degree_name = affiliation["role-title"]

                    #Awarded degree
                    awarded_degree_uri = self.identifier_strategy.to_uri(VIVO.AwardedDegree,
                                                                         {"educational_process_uri":
                                                                          educational_process_uri})
                    graph.add((awarded_degree_uri, RDF.type, VIVO.AwardedDegree))
                    graph.add((awarded_degree_uri, RDFS.label, Literal(degree_name)))

                    #Assigned by organization
                    graph.add((awarded_degree_uri, VIVO.assignedBy, organization_uri))

                    #Related to educational process
                    graph.add((awarded_degree_uri, OBO.RO_0002353, educational_process_uri))

                    #Relates to degree
                    degree_uri = self.identifier_strategy.to_uri(VIVO.AcademicDegree, {"name": degree_name})
                    graph.add((awarded_degree_uri, VIVO.relates, degree_uri))
                    if self.create_strategy.should_create(VIVO.AcademicDegree, degree_uri):
                        graph.add((degree_uri, RDF.type, VIVO.AcademicDegree))
                        graph.add((degree_uri, RDFS.label, Literal(degree_name)))

                    #Relates to person
                    graph.add((awarded_degree_uri, VIVO.relates, person_uri))

