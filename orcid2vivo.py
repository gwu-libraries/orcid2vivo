import requests
import json
from namespace import *
from rdflib import Literal, RDF, RDFS, XSD, Graph
from sparql import sparql_load
import bibtexparser
from bibtexparser.bparser import BibTexParser
import itertools
import re
from entity import PREFIX_DOCUMENT, PREFIX_JOURNAL, PREFIX_AWARDED_DEGREE, PREFIX_DEGREE, PREFIX_GRANT, PREFIX_PERSON, \
    Organization
from utility import to_hash_identifier, add_date, add_date_interval, join_if_not_empty

from bibtexparser.latexenc import unicode_to_latex, unicode_to_crappy_latex1, unicode_to_crappy_latex2


def fetch_profile(orchid):
    #curl -H "Accept: application/orcid+json" 'http://pub.orcid.org/v1.2/0000-0003-3441-946X/orcid-profile' -L -i
    r = requests.get('http://pub.orcid.org/v1.2/%s/orcid-profile' % orchid,
                     headers={"Accept": "application/orcid+json"})
    if r:
        return r.json()
    else:
        raise Exception("Request to fetch ORCID profile for %s returned %s" % (id, r.status_code))


def fetch_crossref_doi(doi):
    #curl 'http://api.crossref.org/works/10.1177/1049732304268657' -L -i
    r = requests.get('http://api.crossref.org/works/%s' % doi)
    if r.status_code == 404:
        print "%s not a crossref DOI." % doi
        return None
    if r:
        return r.json()["message"]
    else:
        raise Exception("Request to fetch DOI %s returned %s" % (doi, r.status_code))


def load_profile(p, vivo_id):
    #Create an RDFLib Graph
    g = Graph(namespace_manager=ns_manager)
    uri = D[vivo_id]

    #ORCID
    orcid = profile["orcid-profile"]["orcid-identifier"]["path"]
    g.add((uri, VIVO.orcidId, Literal(orcid)))

    #Other identifiers
    external_identifiers = p["orcid-profile"]["orcid-bio"]["external-identifiers"]["external-identifier"]
    for external_identifier in external_identifiers:
        if external_identifier["external-id-common-name"]["value"] == "Scopus Author ID":
            g.add((uri, VIVO.scopusId, Literal(external_identifier["external-id-reference"]["value"])))

    _load_works(profile, uri, g)
    _load_affiliations(profile, uri, g)
    _load_funding(p, uri, g)

    return g


def _load_works(p, person_uri, g):
    person_surname = p["orcid-profile"]["orcid-bio"]["personal-details"]["family-name"]["value"]

    #Publications
    works = p["orcid-profile"]["orcid-activities"]["orcid-works"]["orcid-work"]
    for work in works:
        ##Extract
        #Get external identifiers so that can get DOI
        external_identifiers = _get_work_identifiers(work)
        doi = external_identifiers.get("DOI")
        doi_record = fetch_crossref_doi(doi) if doi else None

        #Bibtex
        bibtex = _parse_bibtex(work)

        #Work Type
        work_type = work["work-type"]

        #Title
        title = work["work-title"]["title"]["value"]

        work_uri = D[to_hash_identifier(PREFIX_DOCUMENT, (title, work_type))]

        #Publication date
        (publication_year, publication_month, publication_day) = _get_doi_publication_date(doi_record) \
            if doi_record else _get_publication_date(work)

        #Subjects
        subjects = doi_record["subject"] if doi_record and "subject" in doi_record else None

        #Authors
        authors = _get_doi_authors(doi_record) if doi_record else None
        #TODO: Get from ORCID profile if no doi record

        #Publisher
        publisher = bibtex.get("publisher")

        ##Add triples
        #Title
        g.add((work_uri, RDFS.label, Literal(title)))
        #Person (via Authorship)
        authorship_uri = work_uri + "-auth"
        g.add((authorship_uri, RDF.type, VIVO.Authorship))
        g.add((authorship_uri, VIVO.relates, work_uri))
        g.add((authorship_uri, VIVO.relates, person_uri))
        #Other authors
        if authors:
            for (first_name, surname) in authors:
                if not person_surname.lower() == surname.lower():
                    author_uri = D[to_hash_identifier(PREFIX_PERSON, (first_name, surname))]
                    g.add((author_uri, RDF.type, FOAF.Person))
                    full_name = join_if_not_empty((first_name, surname))
                    g.add((author_uri, RDFS.label, Literal(full_name)))

                    authorship_uri = author_uri + "-auth"
                    g.add((authorship_uri, RDF.type, VIVO.Authorship))
                    g.add((authorship_uri, VIVO.relates, work_uri))
                    g.add((authorship_uri, VIVO.relates, author_uri))

        #Date
        date_uri = work_uri + "-date"
        g.add((work_uri, VIVO.dateTimeValue, date_uri))
        add_date(date_uri, publication_year, g, publication_month, publication_day)
        #Subjects
        if subjects:
            for subject in subjects:
                subject_uri = D[to_hash_identifier("sub", (subject,))]
                g.add((work_uri, VIVO.hasSubjectArea, subject_uri))
                g.add((subject_uri, RDF.type, SKOS.Concept))
                g.add((subject_uri, RDFS.label, Literal(subject)))
        #Identifier
        if doi:
            g.add((work_uri, BIBO.doi, Literal(doi)))
            #Also add as a website
            identifier_url = "http://dx.doi.org/%s" % doi
            vcard_uri = D[to_hash_identifier("vcard", (identifier_url,))]
            g.add((vcard_uri, RDF.type, VCARD.Kind))
            #Has contact info
            g.add((work_uri, OBO.ARG_2000028, vcard_uri))
            #Url vcard
            vcard_url_uri = vcard_uri + "-url"
            g.add((vcard_url_uri, RDF.type, VCARD.URL))
            g.add((vcard_uri, VCARD.hasURL, vcard_url_uri))
            g.add((vcard_url_uri, VCARD.url, Literal(identifier_url, datatype=XSD.anyURI)))


        #Publisher
        if publisher:
            p = Organization(publisher)
            g += p.to_graph()
            g.add((work_uri, VIVO.publisher, p.uri))

        if work_type == "JOURNAL_ARTICLE":
            ##Extract
            #Journal
            journal = bibtex.get("journal")
            #Volume
            volume = bibtex.get("volume")
            #Number
            number = bibtex.get("number")
            #Pages
            pages = bibtex.get("pages")
            start_page = None
            end_page = None
            if pages and "-" in pages:
                (start_page, end_page) = re.split(" *-+ *", pages, maxsplit=2)

            ##Add triples
            #Type
            g.add((work_uri, RDF.type, BIBO.AcademicArticle))
            #Journal
            if journal:
                journal_uri = D[to_hash_identifier(PREFIX_JOURNAL, (BIBO.Journal, journal))]
                g.add((journal_uri, RDF.type, BIBO.Journal))
                g.add((journal_uri, RDFS.label, Literal(journal)))
                g.add((work_uri, VIVO.hasPublicationVenue, journal_uri))

            #Volume
            if volume:
                g.add((work_uri, BIBO.volume, Literal(volume)))
            #Number
            if number:
                g.add((work_uri, BIBO.issue, Literal(number)))
            #Pages
            if start_page:
                g.add((work_uri, BIBO.pageStart, Literal(start_page)))
            if end_page:
                g.add((work_uri, BIBO.pageEnd, Literal(end_page)))

        elif work_type == "BOOK":
            ##Add triples
            #Type
            g.add((work_uri, RDF.type, BIBO.Book))
        elif work_type == "DATA_SET":
            ##Add triples
            #Type
            g.add((work_uri, RDF.type, VIVO.Dataset))


def _load_affiliations(p, person_uri, g):
    #Education
    affiliations = p["orcid-profile"]["orcid-activities"]["affiliations"]["affiliation"]
    for affiliation in affiliations:
        if affiliation["type"] == "EDUCATION":
            u = Organization(affiliation["organization"]["name"])
            g += u.to_graph()
            if "address" in affiliation["organization"]:
                city = affiliation["organization"]["address"]["city"]
                state = affiliation["organization"]["address"]["region"]
            address_uri = D[to_hash_identifier("geo", (city, state))]
            g.add((address_uri, RDF.type, VIVO.GeographicLocation))
            g.add((u.uri, OBO.RO_0001025, address_uri))
            g.add((address_uri, RDFS.label, Literal("%s, %s" % (city, state))))

            degree_name = affiliation["role-title"]

            #Awarded degree
            awarded_degree_uri = D[to_hash_identifier(PREFIX_AWARDED_DEGREE, (person_uri, u.uri, degree_name))]
            g.add((awarded_degree_uri, RDF.type, VIVO.AwardedDegree))
            g.add((awarded_degree_uri, RDFS.label, Literal(degree_name)))

            #Assigned by organization
            g.add((awarded_degree_uri, VIVO.assignedBy, u.uri))

            #Relates to degree
            degree_uri = D[to_hash_identifier(PREFIX_DEGREE, (degree_name,))]
            g.add((degree_uri, RDF.type, VIVO.AcademicDegree))
            g.add((degree_uri, RDFS.label, Literal(degree_name)))
            g.add((awarded_degree_uri, VIVO.relates, degree_uri))

            #Relates to person
            g.add((awarded_degree_uri, VIVO.relates, person_uri))

            #Output of educational process
            educational_process_uri = awarded_degree_uri + "-process"
            g.add((educational_process_uri, RDF.type, VIVO.EducationalProcess))
            g.add((awarded_degree_uri, OBO.RO_0002353, educational_process_uri))
            #Has participants
            g.add((educational_process_uri, OBO.RO_0000057, u.uri))
            g.add((educational_process_uri, OBO.RO_0000057, person_uri))
            #Department
            department_name = affiliation["department-name"]
            if department_name:
                g.add((educational_process_uri, VIVO.departmentOrSchool, Literal(department_name)))

            #Interval
            interval_uri = educational_process_uri + "-interval"
            interval_end_uri = interval_uri + "-end"
            end_date_year = affiliation["end-date"]["year"]["value"] if "end-date" in affiliation else None
            add_date_interval(interval_uri, educational_process_uri, g,
                              None,
                              interval_end_uri if add_date(interval_end_uri, end_date_year, g) else None)


def _load_funding(p, person_uri, g):
    #Funding
    fundings = p["orcid-profile"]["orcid-activities"]["funding-list"]["funding"]
    for funding in fundings:
        if funding["funding-type"] == "GRANT":
            print json.dumps(funding, indent=4)

            title = funding["funding-title"]["title"]["value"]
            grant_uri = D[to_hash_identifier(PREFIX_GRANT, (title,))]
            #Type
            g.add((grant_uri, RDF.type, VIVO.Grant))

            #Person
            g.add((grant_uri, VIVO.relates, person_uri))

            #Title
            g.add((grant_uri, RDFS.label, Literal(title)))

            #Role
            role_uri = grant_uri + "-role"
            g.add((role_uri, RDF.type, VIVO.PrincipalInvestigatorRole))
            #Inheres in
            g.add((role_uri, OBO.RO_0000052, person_uri))
            g.add((role_uri, VIVO.relatedBy, grant_uri))

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

            add_date_interval(interval_uri, grant_uri, g,
                              interval_start_uri if add_date(interval_start_uri,
                                                             start_year,
                                                             g,
                                                             start_month,
                                                             start_day) else None,
                              interval_end_uri if add_date(interval_end_uri,
                                                           end_year,
                                                           g,
                                                           end_month,
                                                           end_day) else None)

            #Award amount
            if "amount" in funding:
                award_amount = "${:,}".format(int(funding["amount"]["value"]))
                g.add((grant_uri, VIVO.totalAwardAmount, Literal(award_amount)))

            #Awarded by
            if "organization" in funding:
                o = Organization(funding["organization"]["name"])
                g += o.to_graph()
                g.add((grant_uri, VIVO.assignedBy, o.uri))

            #Identifiers
            if "funding-external-identifiers" in funding:
                for external_identifier in funding["funding-external-identifiers"]["funding-external-identifier"]:
                    if "funding-external-identifier-value" in external_identifier:
                        g.add((grant_uri,
                               VIVO.sponsorAwardId, Literal(external_identifier["funding-external-identifier-value"])))
                    if "funding-external-identifier-url" in external_identifier:
                        identifier_url = external_identifier["funding-external-identifier-url"]["value"]
                        vcard_uri = D[to_hash_identifier("vcard", (identifier_url,))]
                        g.add((vcard_uri, RDF.type, VCARD.Kind))
                        #Has contact info
                        g.add((grant_uri, OBO.ARG_2000028, vcard_uri))
                        #Url vcard
                        vcard_url_uri = vcard_uri + "-url"
                        g.add((vcard_url_uri, RDF.type, VCARD.URL))
                        g.add((vcard_uri, VCARD.hasURL, vcard_url_uri))
                        g.add((vcard_url_uri, VCARD.url, Literal(identifier_url, datatype=XSD.anyURI)))


def _parse_bibtex(work):
    bibtex = {}
    if "work-citation" in work and work["work-citation"]["work-citation-type"] == "BIBTEX":
        citation = work["work-citation"]["citation"]
        #Need to add \n for bibtexparser to work
        curly_level = 0
        new_citation = ""
        for c in citation:
            if c == "{":
                curly_level += 1
            elif c == "}":
                curly_level -= 1
            new_citation += c
            if (curly_level == 1 and c == ",") or (curly_level == 0 and c == "}"):
                new_citation += "\n"
        parser = BibTexParser()
        parser.customization = bibtex_convert_to_unicode
        bibtex = bibtexparser.loads(new_citation, parser=parser).entries[0]
    return bibtex


def _get_publication_date(work):
    year = None
    month = None
    day = None
    publication_date = work.get("publication-date")
    if publication_date:
        year = publication_date["year"]["value"] if publication_date.get("year") else None
        month = publication_date["month"]["value"] if publication_date.get("month") else None
        day = publication_date["day"]["value"] if publication_date.get("day") in publication_date else None
    return year, month, day


def _get_doi_publication_date(doi_record):
    date_parts = doi_record["issued"]["date-parts"][0]
    return date_parts[0], date_parts[1] if len(date_parts) > 1 else None, date_parts[2] if len(date_parts) > 2 else None


def _get_work_identifiers(work):
    ids = {}
    external_identifiers = work.get("work-external-identifiers")
    if external_identifiers:
        for external_identifier in external_identifiers["work-external-identifier"]:
            ids[external_identifier["work-external-identifier-type"]] = \
                external_identifier["work-external-identifier-id"]["value"]
    return ids


def _get_doi_authors(doi_record):
    authors = []
    for author in doi_record["author"]:
        authors.append((author["given"], author["family"]))
    return authors


def bibtex_convert_to_unicode(record):
    for val in record:
        if '\\' in record[val] or '{' in record[val]:
            for k, v in itertools.chain(unicode_to_crappy_latex1, unicode_to_latex):
                if v in record[val]:
                    record[val] = record[val].replace(v, k)
                #Try without space
                elif v.rstrip() in record[val]:
                    record[val] = record[val].replace(v.rstrip(), k)

        # If there is still very crappy items
        if '\\' in record[val]:
            for k, v in unicode_to_crappy_latex2:
                if v in record[val]:
                    parts = record[val].split(str(v))
                    for key, record[val] in enumerate(parts):
                        if key+1 < len(parts) and len(parts[key+1]) > 0:
                            # Change order to display accents
                            parts[key] = parts[key] + parts[key+1][0]
                            parts[key+1] = parts[key+1][1:]
                    record[val] = k.join(parts)

        #Also replace {\\&}
        if '{\\&}' in record[val]:
            record[val] = record[val].replace('{\\&}', '&')
    return record


if __name__ == '__main__':
    profile = fetch_profile('0000-0003-3441-946X')
    #print json.dumps(profile, indent=4)
    graph = load_profile(profile, "per-7896ae72b37a8eb0dc5faad32da0eefe")

    print "To add %s triples:\n%s" % (len(graph), graph.serialize(format="turtle"))

    sparql_load(graph, "/usr/local/apache2/htdocs")
