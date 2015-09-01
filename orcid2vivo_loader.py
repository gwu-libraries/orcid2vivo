#!/usr/bin/env python

import argparse
import sqlite3
import os
import logging
import codecs
from datetime import datetime
from rdflib import Graph
from rdflib.compare import graph_diff
from orcid2vivo import default_execute
from orcid2vivo_app.vivo_namespace import ns_manager
from orcid2vivo_app.utility import sparql_insert, sparql_delete

log = logging.getLogger(__name__)

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class Store():
    def __init__(self, data_path):
        self.db_filepath = os.path.join(data_path, "orcid2vivo.db")
        log.debug("Db filepath is %s", self.db_filepath)
        create_db = not os.path.exists(self.db_filepath)
        self._conn = sqlite3.connect(self.db_filepath)
        if create_db:
            self._create_db()

    def _create_db(self):
        logging.info("Creating db")
        c = self._conn.cursor()

        # Creating a new table
        c.execute("""
            create table orcid_ids (orcid_id primary key, active, last_update, person_uri, person_id, person_class);
        """)

        self._conn.commit()

    def __contains__(self, orcid_id):
        """
        Returns True if there is a record for the orcid id and it is active.
        """

        c = self._conn.cursor()
        c.execute("""
            select orcid_id from orcid_ids where orcid_id=? and active=1
        """, (orcid_id,))
        if c.fetchone():
            return True
        return False

    def __getitem__(self, orcid_id):
        """
        Returns orcid_id, active, last_update, person_uri, person_id, person_class for orcid id.
        """
        c = self._conn.cursor()
        c.execute("""
            select orcid_id, active, last_update, person_uri, person_id, person_class from orcid_ids where orcid_id=?
        """, (orcid_id,))
        row = c.fetchone()
        if not row:
            raise IndexError
        return row

    def __delitem__(self, orcid_id):
        """
        Marks an orcid id as inactive.
        """
        c = self._conn.cursor()

        c.execute("""
            update orcid_ids set active=0 where orcid_id=?
        """, (orcid_id,))

        self._conn.commit()

    def add(self, orcid_id, person_uri=None, person_id=None, person_class=None):
        """
        Adds orcid id or updates existing orcid id and marks as active.
        """
        c = self._conn.cursor()

        if orcid_id not in self:
            #Add
            log.info("Adding %s", orcid_id)
            c.execute("""
                insert into orcid_ids (orcid_id, active, person_uri, person_id, person_class)
                values (?, 1, ?, ?, ?)
            """, (orcid_id, person_uri, person_id, person_class))
        else:
            #Make update
            log.info("Updating %s", orcid_id)
            c.execute("""
                update orcid_ids set active=1, person_uri=?, person_id=?, person_class=? where orcid_id=?
            """, (person_uri, person_id, person_class, orcid_id))

        self._conn.commit()

    def get_least_recent(self, limit=None, before_datetime=None):
        """
        Returns least recently updated active orcid ids as list of
        orcid_id, person_uri, person_id, person_class.
        """
        c = self._conn.cursor()
        sql = """
            select orcid_id, person_uri, person_id, person_class from orcid_ids where active=1
        """
        if before_datetime:
            sql += " and (last_update < '%s' or last_update is null)" % before_datetime.strftime(DATETIME_FORMAT)

        sql += " order by last_update asc"

        if limit:
            sql += " limit %s" % limit

        c.execute(sql)
        return c.fetchall()

    def touch(self, orcid_id):
        """
        Set last update for orcid id.
        """
        c = self._conn.cursor()

        c.execute("""
            update orcid_ids set last_update=CURRENT_TIMESTAMP where orcid_id=? and active=1
        """, (orcid_id,))

        self._conn.commit()

    def __iter__(self):
        c = self._conn.cursor()
        c.execute("""
            select orcid_id, active, last_update, person_uri, person_id, person_class from orcid_ids
        """)

        return iter(c.fetchall())

    def delete_all(self):
        c = self._conn.cursor()
        c.execute("""
            update orcid_ids set active=0
        """)
        self._conn.commit()

    #Methods to make this a Context Manager. This is necessary to make sure the connection is closed properly.
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._conn.close()


def load_single(orcid_id, person_uri, person_id, person_class, data_path, endpoint, username, password,
                namespace=None, skip_person=False):
    with Store(data_path) as store:
        #Crosswalk
        (graph, profile, person_uri) = default_execute(orcid_id, namespace=namespace, person_uri=person_uri,
                                                       person_id=person_id, skip_person=skip_person,
                                                       person_class=person_class)

        graph_filepath = os.path.join(data_path, "%s.ttl" % orcid_id.lower())
        previous_graph = Graph(namespace_manager=ns_manager)
        #Load last graph
        if os.path.exists(graph_filepath):
            log.debug("Loading previous graph %s", graph_filepath)
            previous_graph.parse(graph_filepath, format="turtle")

        #Diff against last graph
        (both_graph, delete_graph, add_graph) = graph_diff(previous_graph, graph)

        #SPARQL Update
        log.info("Adding %s, deleting %s triples for %s", len(add_graph), len(delete_graph), orcid_id)
        sparql_delete(delete_graph, endpoint, username, password)
        sparql_insert(add_graph, endpoint, username, password)

        #Save new last graph
        log.debug("Saving new graph %s", graph_filepath)
        with codecs.open(graph_filepath, "w") as out:
            graph.serialize(format="turtle", destination=out)

        #Touch
        store.touch(orcid_id)

        return graph, add_graph, delete_graph


def load(data_path, endpoint, username, password, limit=None, before_datetime=None, namespace=None, skip_person=False):
    orcid_ids = []
    with Store(data_path) as store:
        #Get the orcid ids to update
        results = store.get_least_recent(limit=limit, before_datetime=before_datetime)
        for (orcid_id, person_uri, person_id, person_class) in results:
            load_single(orcid_id, person_uri, person_id, person_class, data_path, endpoint, username, password,
                        namespace, skip_person)
            orcid_ids.append(orcid_id)
    return orcid_ids

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--debug", action="store_true")

    orcid_id_parent_parser = argparse.ArgumentParser(add_help=False)
    orcid_id_parent_parser.add_argument("orcid_id")
    data_path_parent_parser = argparse.ArgumentParser(add_help=False)
    data_path_parent_parser.add_argument("--data-path", dest="data_path", help="Path where db and ttl files will be "
                                                                               "stored. Default is ./data.",
                                         default="./data")

    subparsers = parser.add_subparsers(dest="command")

    add_parser = subparsers.add_parser("add", help="Adds or updates orcid id record. If inactive, marks active.",
                                       parents=[orcid_id_parent_parser, data_path_parent_parser])
    add_parser.add_argument("--person-id", dest="person_id", help="Id for the person to use when constructing the "
                                                                  "person's URI. If not provided, the orcid id will be "
                                                                  "used.")
    add_parser.add_argument("--person-uri", dest="person_uri", help="A URI for the person. If not provided, one will "
                                                                    "be created from the orcid id or person id.")
    add_parser.add_argument("--person-class", dest="person_class",
                            choices=["FacultyMember", "FacultyMemberEmeritus", "Librarian", "LibrarianEmeritus",
                                     "NonAcademic", "NonFacultyAcademic", "ProfessorEmeritus", "Student"],
                            help="Class (in VIVO Core ontology) for a person. Default is a FOAF Person.")

    delete_parser = subparsers.add_parser("delete", help="Marks an orcid id record as inactive so that it will not be "
                                                         "loaded.",
                                          parents=[orcid_id_parent_parser, data_path_parent_parser])

    delete_all_parser = subparsers.add_parser("delete-all", help="Marks all orcid id records as inactive.",
                                              parents=[data_path_parent_parser])

    load_parser = subparsers.add_parser("load", help="Fetches orcid profiles, crosswalks to VIVO-ISF, loads to VIVO "
                                                     "instance, and updates orcid id record. If loading multiple "
                                                     "orcid ids, loads in least recent order.",
                                        parents=[data_path_parent_parser])
    load_parser.add_argument("endpoint", help="Endpoint for SPARQL Update of VIVO instance, e.g., "
                                              "http://localhost/vivo/api/sparqlUpdate.")
    load_parser.add_argument("username", help="Username for VIVO root.")
    load_parser.add_argument("namespace", help="VIVO namespace. Default is http://vivo.mydomain.edu/individual/.")
    load_parser.add_argument("--password", help="Password for VIVO root. Alternatively, provide in "
                                                "environment variable VIVO_ROOT_PASSWORD.")
    load_parser.add_argument("--orcid_id", help="Orcid id of person to load.")
    load_parser.add_argument("--limit", type=int, help="Maximimum number of orcid ids to load.")
    load_parser.add_argument("--before", help="Orcid ids that were loaded before this date or never loaded. Format is "
                                              "YYYY-MM-DD HH:MM:SS in UTC.")
    load_parser.add_argument("--skip-person", dest="skip_person", action="store_true",
                             help="Skip adding triples declaring the person and the person's name.")

    list_parser = subparsers.add_parser("list", help="Lists orcid_id records in the db.",
                                        parents=[data_path_parent_parser])

    #Parse
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    if not os.path.exists(args.data_path):
        raise IOError("%s does not exists" % args.data_path)

    with Store(args.data_path) as main_store:
        if args.command == "add":
            print "Adding %s" % args.orcid_id
            main_store.add(args.orcid_id, person_uri=args.person_uri, person_id=args.person_id,
                           person_class=args.person_class)
        elif args.command == "delete":
            print "Deleting %s" % args.orcid_id
            del main_store[args.orcid_id]
        elif args.command == "delete-all":
            print "Deleting all"
            main_store.delete_all()
        elif args.command == "list":
            for main_orcid_id, main_active, main_last_update, main_person_uri, \
                    main_person_id, main_person_class in main_store:
                print "%s [active=%s; last_update=%s; person_uri=%s; person_id=%s, person_class=%s]" % (
                    main_orcid_id,
                    "true" if main_active else "false",
                    main_last_update,
                    main_person_uri,
                    main_person_id,
                    main_person_class
                )

    if args.command == "load":
            main_password = args.password or os.environ["VIVO_ROOT_PASSWORD"]
            if args.orcid_id:
                with Store(args.data_path) as main_store:
                    if args.orcid_id not in main_store:
                        raise ValueError("%s not in db. Add person to db first." % args.orcid_id)
                    main_orcid_id, main_active, main_last_update, main_person_uri, main_person_id, \
                        main_person_class = main_store[args.orcid_id]
                    print "Loading %s to %s" % (args.orcid_id, args.endpoint)
                    load_single(main_orcid_id, main_person_uri, main_person_id, main_person_class, args.data_path,
                                args.endpoint, args.username, main_password,
                                namespace=args.namespace, skip_person=args.skip_person)
            else:
                main_before_datetime = datetime.strptime(args.before, DATETIME_FORMAT) if args.before else None
                print "Loading to %s" % args.endpoint
                main_orcid_ids = load(args.data_path, args.endpoint, args.username, main_password, limit=args.limit,
                                      before_datetime=main_before_datetime, namespace=args.namespace,
                                      skip_person=args.skip_person)
                print "Loaded: %s" % ", ".join(main_orcid_ids)

    print "Done"