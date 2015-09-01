import requests
from rdflib import RDFS, RDF, XSD, Literal
from vivo_namespace import VIVO, VCARD, OBO, BIBO, FOAF, SKOS
from utility import join_if_not_empty
import re
import bibtexparser
from bibtexparser.bparser import BibTexParser
from bibtexparser.latexenc import unicode_to_latex, unicode_to_crappy_latex1, unicode_to_crappy_latex2
import itertools
from utility import add_date

work_type_map = {
    "BOOK": BIBO["Book"],
    "BOOK_CHAPTER": BIBO["Chapter"],
    "BOOK_REVIEW": BIBO["Review"],
    "DICTIONARY_ENTRY": BIBO["DocumentPart"],
    "DISSERTATION": BIBO["Thesis"],
    "ENCYCLOPEDIA_ENTRY": BIBO["DocumentPart"],
    "EDITED_BOOK": BIBO["EditedBook"],
    "JOURNAL_ARTICLE": BIBO["AcademicArticle"],
    "JOURNAL_ISSUE": BIBO["Issue"],
    "MAGAZINE_ARTICLE": BIBO["Article"],
    "MANUAL": BIBO["Manual"],
    "ONLINE_RESOURCE": BIBO["Website"],
    "NEWSLETTER_ARTICLE": BIBO["Article"],
    "NEWSPAPER_ARTICLE": BIBO["Article"],
    "REPORT": BIBO["Report"],
    "RESEARCH_TOOL": BIBO["Document"],
    "SUPERVISED_STUDENT_PUBLICATION": BIBO["Article"],
    # test not mapped
    "TRANSLATION": BIBO["Document"],
    "WEBSITE": BIBO["Website"],
    "WORKING_PAPER": VIVO["WorkingPaper"],
    "CONFERENCE_ABSTRACT": VIVO["Abstract"],
    "CONFERENCE_PAPER": VIVO["ConferencePaper"],
    "CONFERENCE_POSTER": VIVO["ConferencePoster"],
    # disclosure not mapped
    # license not mapped
    "PATENT": BIBO["Patent"],
    # registered-copyright not mapped
    "ARTISTIC_PERFORMANCE": BIBO["Performance"],
    "DATA_SET": VIVO["Dataset"],
    # invention not mapped
    "LECTURE_SPEECH": VIVO["Speech"],
    "RESEARCH_TECHNIQUE": OBO["OBI_0000272"],
    # spin-off-company not mapped
    "STANDARDS_AND_POLICY": BIBO["Standard"],
    "OTHER": BIBO["Document"]
}

identifier_map = {
    "DOI": (BIBO.doi, "http://dx.doi.org/%s"),
    "ASIN": (BIBO.asin, "http://www.amazon.com/dp/%s"),
    "OCLC": (BIBO.oclcnum, "http://www.worldcat.org/oclc/%s"),
    "LCCN": (BIBO.lccn, None),
    "PMC": (VIVO.pmcid, "http://www.ncbi.nlm.nih.gov/pmc/articles/%s/"),
    "PMID": (BIBO.pmid, "http://www.ncbi.nlm.nih.gov/pubmed/%s"),
    "ISSN": (BIBO.issn, None)
}

journal_map = {
    "JOURNAL_ARTICLE": BIBO.Journal,
    "MAGAZINE_ARTICLE": BIBO.Magazine,
    "NEWSLETTER_ARTICLE": VIVO.Newsletter,
    "NEWSPAPER_ARTICLE": BIBO.Newspaper,
    "SUPERVISED_STUDENT_PUBLICATION": BIBO.Journal
}

contributor_map = {
    "EDITOR": VIVO.Editorship,
    "CHAIR_OR_TRANSLATOR": "TRANSLATOR"
}

bibtex_type_map = {
    "article": BIBO["Article"],
    "book": BIBO["Book"],
    "conference": VIVO["ConferencePaper"],
    "manual": BIBO["Manual"],
    "mastersthesis": BIBO["Thesis"],
    "phdthesis": BIBO["Thesis"],
    "proceedings": VIVO["ConferencePaper"],
    "techreport": BIBO["Report"]
}


class WorksCrosswalk():
    def __init__(self, identifier_strategy, create_strategy):
        self.identifier_strategy = identifier_strategy
        self.create_strategy = create_strategy

    def crosswalk(self, orcid_profile, person_uri, graph):
        # Work metadata may be available from the orcid profile, bibtex contained in the orcid profile, and/or crossref
        # record. The preferred order (in general) for getting metadata is crossref, bibtex, orcid.

        # Note that datacite records were considered, but not found to have additional/better metadata.

        #Publications
        for work in ((orcid_profile["orcid-profile"].get("orcid-activities") or {}).get("orcid-works") or {})\
                .get("orcid-work", []):
            #Work Type
            work_type = work["work-type"]
            if work_type in work_type_map:
                ##Extract
                #Get external identifiers so that can get DOI
                external_identifiers = WorksCrosswalk._get_work_identifiers(work)
                doi = external_identifiers.get("DOI")
                crossref_record = WorksCrosswalk._fetch_crossref_doi(doi) if doi else {}

                #Bibtex
                bibtex = WorksCrosswalk._parse_bibtex(work)
                #Get title so that can construct work uri
                title = WorksCrosswalk._get_crossref_title(crossref_record) \
                    or bibtex.get("title") \
                    or WorksCrosswalk._get_orcid_title(work)

                #Work-type
                work_class = work_type_map[work_type]
                if work_type == "TRANSLATION" and bibtex and bibtex["ENTRYTYPE"] in bibtex_type_map:
                    work_class = bibtex_type_map[bibtex["ENTRYTYPE"]]

                #Construct work uri
                work_uri = self.identifier_strategy.to_uri(work_class, {"name": title})

                graph.add((work_uri, RDF.type, work_class))

                #Title
                graph.add((work_uri, RDFS.label, Literal(title)))

                #Publication date
                (publication_year, publication_month, publication_day) = \
                    WorksCrosswalk._get_crossref_publication_date(crossref_record) \
                    or WorksCrosswalk._get_orcid_publication_date(work) \
                    or WorksCrosswalk._get_bibtext_publication_date(bibtex) or (None, None, None)
                date_uri = add_date(publication_year, graph, self.identifier_strategy,
                                    publication_month, publication_day)
                if date_uri:
                    graph.add((work_uri, VIVO.dateTimeValue, date_uri))

                #Subjects
                subjects = crossref_record["subject"] if crossref_record and "subject" in crossref_record else None
                if subjects:
                    for subject in subjects:
                        subject_uri = self.identifier_strategy.to_uri(SKOS.Concept, {"name": subject})
                        graph.add((work_uri, VIVO.hasSubjectArea, subject_uri))
                        if self.create_strategy.should_create(SKOS.Concept, subject_uri):
                            graph.add((subject_uri, RDF.type, SKOS.Concept))
                            graph.add((subject_uri, RDFS.label, Literal(subject)))

                #Contributors (an array of (first_name, surname, VIVO type, e.g., VIVO.Authorship))
                bibtex_contributors = []
                bibtex_contributors.extend(WorksCrosswalk._get_bibtex_authors(bibtex))
                bibtex_contributors.extend(WorksCrosswalk._get_bibtex_editors(bibtex))
                #Orcid is better for translations because has translator role
                if work_type == "TRANSLATION":
                    contributors = WorksCrosswalk._get_orcid_contributors(work)
                else:
                    contributors = WorksCrosswalk._get_crossref_authors(crossref_record) or bibtex_contributors \
                        or WorksCrosswalk._get_orcid_contributors(work)
                person_surname = orcid_profile["orcid-profile"]["orcid-bio"]["personal-details"]["family-name"]["value"]
                if not contributors:
                    #Add person as author or editor.
                    #None, None means this person.
                    if work_type in ("EDITED_BOOK",):
                        contributors.append((None, None, VIVO.Editorship))
                    elif work_type == "TRANSLATION":
                        #Translator is a predicate, not a -ship class.
                        contributors.append((None, None, "TRANSLATOR"))
                    else:
                        contributors.append((None, None, VIVO.Authorship))

                for (first_name, surname, vivo_type) in contributors:
                    if not surname or person_surname.lower() == surname.lower():
                        contributor_uri = person_uri
                    else:
                        contributor_uri = self.identifier_strategy.to_uri(FOAF.Person, {"first_name": first_name,
                                                                                        "surname": surname})
                        if self.create_strategy.should_create(FOAF.Person, contributor_uri):
                            graph.add((contributor_uri, RDF.type, FOAF.Person))
                            full_name = join_if_not_empty((first_name, surname))
                            graph.add((contributor_uri, RDFS.label, Literal(full_name)))

                    #Translation is a special case
                    if vivo_type == "TRANSLATOR":
                        graph.add((contributor_uri, BIBO.translator, work_uri))
                    #So is patent assignee
                    elif work_type == "PATENT":
                        graph.add((contributor_uri, VIVO.assigneeFor, work_uri))
                    else:
                        contributorship_uri = self.identifier_strategy.to_uri(vivo_type,
                                                                              {"contributor_uri": contributor_uri})
                        graph.add((contributorship_uri, RDF.type, vivo_type))
                        graph.add((contributorship_uri, VIVO.relates, work_uri))
                        graph.add((contributorship_uri, VIVO.relates, contributor_uri))

                #Publisher
                publisher = crossref_record.get("publisher") or bibtex.get("publisher")
                if publisher:
                    publisher_uri = self.identifier_strategy.to_uri(FOAF.Organization, {"name": publisher})
                    graph.add((work_uri, VIVO.publisher, publisher_uri))
                    if self.create_strategy.should_create(FOAF.Organization, publisher_uri):
                        graph.add((publisher_uri, RDF.type, FOAF.Organization))
                        graph.add((publisher_uri, RDFS.label, Literal(publisher)))

                #Volume
                volume = crossref_record.get("volume") or bibtex.get("volume")
                if volume:
                    graph.add((work_uri, BIBO.volume, Literal(volume)))

                #Issue
                issue = crossref_record.get("issue") or bibtex.get("number")
                if issue:
                    graph.add((work_uri, BIBO.issue, Literal(issue)))

                #Pages
                pages = crossref_record.get("page") or bibtex.get("pages")
                start_page = None
                end_page = None
                if pages and "-" in pages:
                    (start_page, end_page) = re.split(" *-+ *", pages, maxsplit=2)
                if start_page:
                    graph.add((work_uri, BIBO.pageStart, Literal(start_page)))
                if end_page:
                    graph.add((work_uri, BIBO.pageEnd, Literal(end_page)))

                #Identifiers
                #Add doi in bibtex, but not orcid profile
                if bibtex and "doi" in bibtex and "DOI" not in external_identifiers:
                    external_identifiers["DOI"] = bibtex["doi"]
                #Add isbn in bibtex, but not orcid profile
                if bibtex and "isbn" in bibtex and "ISBN" not in external_identifiers:
                    external_identifiers["ISBN"] = bibtex["isbn"]

                for identifier_type, identifier in external_identifiers.iteritems():
                    identifier_url = None

                    if identifier_type in ("PAT", "OTHER_ID") and work_type == "PATENT":
                        identifier_predicate = VIVO.patentNumber
                    elif identifier_type == "ISBN":
                        clean_isbn = identifier.replace("-", "")
                        if len(clean_isbn) <= 10:
                            identifier_predicate = BIBO.isbn10
                        else:
                            identifier_predicate = BIBO.isbn13
                    else:
                        (identifier_predicate, url_template) = identifier_map.get(identifier_type, (None, None))
                        if url_template:
                            identifier_url = url_template % identifier

                    if identifier_predicate:
                        graph.add((work_uri, identifier_predicate, Literal(identifier)))
                    if identifier_url:
                        self._add_work_url(identifier_url, work_uri, graph)

                orcid_url = (work.get("url", {}) or {}).get("value")
                if orcid_url and WorksCrosswalk._use_url(orcid_url):
                    self._add_work_url(orcid_url, work_uri, graph)
                bibtex_url = bibtex.get("link")
                if bibtex_url and WorksCrosswalk._use_url(bibtex_url) and orcid_url != bibtex_url:
                    self._add_work_url(bibtex_url, work_uri, graph)

                #Series
                series = bibtex.get("series")
                #TODO: Figure out how to model series in VIVO-ISF.

                #Journal
                #If Crossref has a journal use it
                journal = WorksCrosswalk._get_crossref_journal(crossref_record)
                if journal:
                    issns = crossref_record.get("ISSN", [])
                #Otherwise, only use for some work types.
                elif work_type in journal_map:
                    issns = []
                    journal = bibtex.get("journal")
                    if journal:
                        if "issn" in bibtex:
                            issns = [bibtex["issn"]]
                    else:
                        journal = (work.get("journal-title", {}) or {}).get("value")

                if journal:
                    journal_class = journal_map.get(work_type, BIBO.Journal)
                    journal_uri = self.identifier_strategy.to_uri(journal_class, {"name": journal})
                    graph.add((work_uri, VIVO.hasPublicationVenue, journal_uri))
                    if self.create_strategy.should_create(journal_class, journal_uri):
                        graph.add((journal_uri, RDF.type, journal_class))
                        graph.add((journal_uri, RDFS.label, Literal(journal)))
                        for issn in issns:
                            graph.add((journal_uri, BIBO.issn, Literal(issn)))

                if work_type in ("BOOK_CHAPTER",):
                    book_title = bibtex.get("booktitle")
                    if book_title:
                        book_uri = self.identifier_strategy.to_uri(BIBO.Book, {"name": book_title})
                        graph.add((work_uri, VIVO.hasPublicationVenue, book_uri))
                        if self.create_strategy.should_create(BIBO.Book, book_uri):
                            graph.add((book_uri, RDF.type, BIBO.Book))
                            graph.add((book_uri, RDFS.label, Literal(book_title)))

                if work_type in ("CONFERENCE_PAPER",):
                    proceeding = bibtex.get("journal") or (work.get("journal-title", {}) or {}).get("value")
                    if proceeding:
                        proceeding_uri = self.identifier_strategy.to_uri(BIBO.Proceedings, {"name": proceeding})
                        graph.add((work_uri, VIVO.hasPublicationVenue, proceeding_uri))
                        if self.create_strategy.should_create(BIBO.Proceedings, proceeding_uri):
                            graph.add((proceeding_uri, RDF.type, BIBO.Proceedings))
                            graph.add((proceeding_uri, RDFS.label, Literal(proceeding)))

    @staticmethod
    def _fetch_crossref_doi(doi):
        #curl 'http://api.crossref.org/works/10.1177/1049732304268657' -L -i
        r = requests.get('http://api.crossref.org/works/%s' % doi)
        if r.status_code == 404:
            #Not a crossref DOI.
            return {}
        if r:
            return r.json()["message"]
        else:
            raise Exception("Request to fetch DOI %s returned %s" % (doi, r.status_code))

    @staticmethod
    def _parse_bibtex(work):
        bibtex = {}
        if work and (work.get("work-citation", {}) or {}).get("work-citation-type") == "BIBTEX":
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
            parser.customization = WorksCrosswalk._bibtex_customizations
            bibtex = bibtexparser.loads(new_citation, parser=parser).entries[0]
        return bibtex

    @staticmethod
    def _get_crossref_title(crossref_record):
        if "title" in crossref_record and crossref_record["title"]:
            return crossref_record["title"][0]
        return None

    @staticmethod
    def _get_orcid_title(work):
        return join_if_not_empty((work["work-title"]["title"]["value"],
                                (work["work-title"].get("subtitle") or {}).get("value")), ": ")

    @staticmethod
    def _get_orcid_publication_date(work):
        year = None
        month = None
        day = None
        publication_date = work.get("publication-date")
        if publication_date:
            year = publication_date["year"]["value"] if publication_date.get("year") else None
            month = publication_date["month"]["value"] if publication_date.get("month") else None
            day = publication_date["day"]["value"] if publication_date.get("day") else None
        if not year and not month and not day:
            return None
        return year, month, day

    @staticmethod
    def _get_bibtext_publication_date(bibtex):
        year = bibtex.get("year")
        if year and not re.match("\d{4}", year):
            year = None
        #Not going to try to parse month and day
        if not year:
            return None
        return year, None, None

    @staticmethod
    def _get_crossref_publication_date(doi_record):
        if "issued" in doi_record and "date-parts" in doi_record["issued"]:
            date_parts = doi_record["issued"]["date-parts"][0]
            return date_parts[0], \
                date_parts[1] if len(date_parts) > 1 else None, date_parts[2] if len(date_parts) > 2 else None
        return None

    @staticmethod
    def _get_work_identifiers(work):
        ids = {}
        external_identifiers = work.get("work-external-identifiers")
        if external_identifiers:
            for external_identifier in external_identifiers["work-external-identifier"]:
                ids[external_identifier["work-external-identifier-type"]] = \
                    external_identifier["work-external-identifier-id"]["value"]
        return ids

    @staticmethod
    def _get_crossref_authors(doi_record):
        authors = []
        for author in doi_record.get("author", []):
            authors.append((author["given"], author["family"], VIVO.Authorship))
        return authors

    @staticmethod
    def _get_orcid_contributors(work):
        contributors = []
        for contributor in (work.get("work-contributors") or {}).get("contributor", []):
            #Last name, first name
            credit_name = (contributor.get("credit-name") or {}).get("value")
            #Some entries will not have a credit name, meaning the entry is for the person.
            #Using None, None to indicate the person.
            first_name = None
            surname = None
            if credit_name:
                #Normalize with BibtexParser's getnames()
                clean_name = bibtexparser.customization.getnames([credit_name])[0]
                (first_name, surname) = WorksCrosswalk._parse_reversed_name(clean_name)
            role = (contributor.get("contributor-attributes", {}) or {}).get("contributor-role")
            contributors.append((first_name, surname, contributor_map.get(role, VIVO.Authorship)))
        return contributors

    @staticmethod
    def _get_bibtex_authors(bibtex):
        authors = []
        for name in bibtex.get("author", []):
            (first_name, surname) = WorksCrosswalk._parse_reversed_name(name)
            authors.append((first_name, surname, VIVO.Authorship))
        return authors

    @staticmethod
    def _get_bibtex_editors(bibtex):
        editors = []
        for editor in bibtex.get("editor", {}):
            (first_name, surname) = WorksCrosswalk._parse_reversed_name(editor["name"])
            editors.append((first_name, surname, VIVO.Editorship))
        return editors

    @staticmethod
    def _parse_reversed_name(name):
        if name:
            split_name = name.split(", ", 2)
            if len(split_name) == 2:
                return split_name[1], split_name[0]
            else:
                return None, name

    @staticmethod
    def _bibtex_customizations(record):
        record = WorksCrosswalk._bibtex_convert_to_unicode(record)
        record = bibtexparser.customization.author(record)
        record = bibtexparser.customization.editor(record)
        return record

    @staticmethod
    def _bibtex_convert_to_unicode(record):
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

    def _add_work_url(self, url, work_uri, graph):
        vcard_uri = self.identifier_strategy.to_uri(VCARD.Kind, {"url": url})
        graph.add((vcard_uri, RDF.type, VCARD.Kind))
        #Has contact info
        graph.add((work_uri, OBO.ARG_2000028, vcard_uri))
        #Url vcard
        vcard_url_uri = self.identifier_strategy.to_uri(VCARD.URL, {"vcard_uri": vcard_uri})
        graph.add((vcard_url_uri, RDF.type, VCARD.URL))
        graph.add((vcard_uri, VCARD.hasURL, vcard_url_uri))
        graph.add((vcard_url_uri, VCARD.url, Literal(url, datatype=XSD.anyURI)))

    @staticmethod
    def _use_url(url):
        #Use url if it does not match one of the patterns in identifier_map
        for (identifier_predicate, url_template) in identifier_map.itervalues():
            if url_template:
                base_url = url_template[:url_template.index("%s")]
                if url.startswith(base_url):
                    return False
        return True

    @staticmethod
    def _get_crossref_journal(crossref_record):
        journal = None
        #May be multiple container titles. Take the longest.
        for j in crossref_record.get("container-title", []):
            if not journal or len(j) > len(journal):
                journal = j
        return journal