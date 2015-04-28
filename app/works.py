import requests
from vivo_uri import to_hash_identifier, PREFIX_DOCUMENT, PREFIX_PERSON, PREFIX_ORGANIZATION, PREFIX_JOURNAL
from rdflib import RDFS, RDF, XSD, Literal
from vivo_namespace import VIVO, VCARD, OBO, BIBO, FOAF, SKOS
import app.vivo_namespace as ns
from utility import join_if_not_empty
import re
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.latexenc import unicode_to_latex, unicode_to_crappy_latex1, unicode_to_crappy_latex2
import itertools
from utility import add_date


def crosswalk_works(orcid_profile, person_uri, graph):
    person_surname = orcid_profile["orcid-profile"]["orcid-bio"]["personal-details"]["family-name"]["value"]

    #Publications
    if "orcid-works" in orcid_profile["orcid-profile"]["orcid-activities"] \
            and orcid_profile["orcid-profile"]["orcid-activities"]["orcid-works"] \
            and "orcid-work" in orcid_profile["orcid-profile"]["orcid-activities"]["orcid-works"]:
        works = orcid_profile["orcid-profile"]["orcid-activities"]["orcid-works"]["orcid-work"]
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

            work_uri = ns.D[to_hash_identifier(PREFIX_DOCUMENT, (title, work_type))]

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
            graph.add((work_uri, RDFS.label, Literal(title)))
            #Person (via Authorship)
            authorship_uri = work_uri + "-auth"
            graph.add((authorship_uri, RDF.type, VIVO.Authorship))
            graph.add((authorship_uri, VIVO.relates, work_uri))
            graph.add((authorship_uri, VIVO.relates, person_uri))
            #Other authors
            if authors:
                for (first_name, surname) in authors:
                    if not person_surname.lower() == surname.lower():
                        author_uri = ns.D[to_hash_identifier(PREFIX_PERSON, (first_name, surname))]
                        graph.add((author_uri, RDF.type, FOAF.Person))
                        full_name = join_if_not_empty((first_name, surname))
                        graph.add((author_uri, RDFS.label, Literal(full_name)))

                        authorship_uri = author_uri + "-auth"
                        graph.add((authorship_uri, RDF.type, VIVO.Authorship))
                        graph.add((authorship_uri, VIVO.relates, work_uri))
                        graph.add((authorship_uri, VIVO.relates, author_uri))

            #Date
            date_uri = work_uri + "-date"
            graph.add((work_uri, VIVO.dateTimeValue, date_uri))
            add_date(date_uri, publication_year, graph, publication_month, publication_day)
            #Subjects
            if subjects:
                for subject in subjects:
                    subject_uri = ns.D[to_hash_identifier("sub", (subject,))]
                    graph.add((work_uri, VIVO.hasSubjectArea, subject_uri))
                    graph.add((subject_uri, RDF.type, SKOS.Concept))
                    graph.add((subject_uri, RDFS.label, Literal(subject)))
            #Identifier
            if doi:
                graph.add((work_uri, BIBO.doi, Literal(doi)))
                #Also add as a website
                identifier_url = "http://dx.doi.org/%s" % doi
                vcard_uri = ns.D[to_hash_identifier("vcard", (identifier_url,))]
                graph.add((vcard_uri, RDF.type, VCARD.Kind))
                #Has contact info
                graph.add((work_uri, OBO.ARG_2000028, vcard_uri))
                #Url vcard
                vcard_url_uri = vcard_uri + "-url"
                graph.add((vcard_url_uri, RDF.type, VCARD.URL))
                graph.add((vcard_uri, VCARD.hasURL, vcard_url_uri))
                graph.add((vcard_url_uri, VCARD.url, Literal(identifier_url, datatype=XSD.anyURI)))

            #Publisher
            if publisher:
                publisher_uri = ns.D[to_hash_identifier(PREFIX_ORGANIZATION, (publisher,))]
                graph.add((publisher_uri, RDF.type, FOAF.Organization))
                graph.add((publisher_uri, RDFS.label, Literal(publisher)))
                graph.add((work_uri, VIVO.publisher, publisher_uri))

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
                graph.add((work_uri, RDF.type, BIBO.AcademicArticle))
                #Journal
                if journal:
                    journal_uri = ns.D[to_hash_identifier(PREFIX_JOURNAL, (BIBO.Journal, journal))]
                    graph.add((journal_uri, RDF.type, BIBO.Journal))
                    graph.add((journal_uri, RDFS.label, Literal(journal)))
                    graph.add((work_uri, VIVO.hasPublicationVenue, journal_uri))

                #Volume
                if volume:
                    graph.add((work_uri, BIBO.volume, Literal(volume)))
                #Number
                if number:
                    graph.add((work_uri, BIBO.issue, Literal(number)))
                #Pages
                if start_page:
                    graph.add((work_uri, BIBO.pageStart, Literal(start_page)))
                if end_page:
                    graph.add((work_uri, BIBO.pageEnd, Literal(end_page)))

            elif work_type == "BOOK":
                ##Add triples
                #Type
                graph.add((work_uri, RDF.type, BIBO.Book))
            elif work_type == "DATA_SET":
                ##Add triples
                #Type
                graph.add((work_uri, RDF.type, VIVO.Dataset))


def fetch_crossref_doi(doi):
    #curl 'http://api.crossref.org/works/10.1177/1049732304268657' -L -i
    r = requests.get('http://api.crossref.org/works/%s' % doi)
    if r.status_code == 404:
        #Not a crossref DOI.
        return None
    if r:
        return r.json()["message"]
    else:
        raise Exception("Request to fetch DOI %s returned %s" % (doi, r.status_code))


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
        day = publication_date["day"]["value"] if publication_date.get("day") else None
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
