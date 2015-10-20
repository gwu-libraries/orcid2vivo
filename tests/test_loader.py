from __future__ import absolute_import
import tempfile
import shutil
from orcid2vivo_loader import Store, load_single
import os
import tests
import time
import datetime
import vcr
from mock import patch, call
from rdflib.compare import to_isomorphic

my_vcr = vcr.VCR(
    cassette_library_dir=tests.FIXTURE_PATH,
)


class TestStore(tests.TestCase):
    def setUp(self):
        self.data_path = tempfile.mkdtemp()
        self.db_filepath = os.path.join(self.data_path, "orcid2vivo.db")

    def tearDown(self):
        shutil.rmtree(self.data_path, ignore_errors=True)

    def test_persist(self):
        self.assertFalse(os.path.exists(self.db_filepath))
        with Store(self.data_path) as store:
            self.assertEqual(self.db_filepath, store.db_filepath)
            #Created
            self.assertTrue(os.path.exists(self.db_filepath))
            #Add
            store.add("0000-0003-1527-0030")

        #Still exists after close
        self.assertTrue(os.path.exists(self.db_filepath))
        with Store(self.data_path) as store:
            self.assertTrue("0000-0003-1527-0030" in store)

    def test_contains(self):
        with Store(self.data_path) as store:
            #Add
            store.add("0000-0003-1527-0030")
            self.assertTrue("0000-0003-1527-0030" in store)
            self.assertFalse("X000-0003-1527-0030" in store)
            self.assertTrue(store.contains("0000-0003-1527-0030"))
            self.assertTrue(store.contains("0000-0003-1527-0030", True))
            self.assertFalse(store.contains("0000-0003-1527-0030", False))

    def test_add_item(self):
        with Store(self.data_path) as store:
            #Insert
            store.add("0000-0003-1527-0030")
            (orcid_id, active, last_update, person_uri, person_id, person_class) = store["0000-0003-1527-0030"]
            self.assertTrue(active)
            self.assertIsNone(person_uri)
            self.assertIsNone(person_id)
            self.assertIsNone(person_class)
            self.assertIsNone(last_update)
            #Update
            store.add("0000-0003-1527-0030", person_uri="http://me", person_id="me", person_class="Librarian")
            (orcid_id, active, last_update, person_uri, person_id, person_class) = store["0000-0003-1527-0030"]
            self.assertTrue(active)
            self.assertEqual("http://me", person_uri)
            self.assertEqual("me", person_id)
            self.assertEqual("Librarian", person_class)
            self.assertIsNone(last_update)

    def test_add_deleted_item(self):
        with Store(self.data_path) as store:
            #Insert
            store.add("0000-0003-1527-0030")
            (orcid_id, active, last_update, person_uri, person_id, person_class) = store["0000-0003-1527-0030"]
            self.assertTrue(active)
            self.assertIsNone(person_uri)
            self.assertIsNone(person_id)
            self.assertIsNone(person_class)
            self.assertIsNone(last_update)
            #Delete
            del store["0000-0003-1527-0030"]
            #Add again
            store.add("0000-0003-1527-0030")
            (orcid_id, active, last_update, person_uri, person_id, person_class) = store["0000-0003-1527-0030"]
            self.assertTrue(active)
            self.assertIsNone(person_uri)
            self.assertIsNone(person_id)
            self.assertIsNone(person_class)
            self.assertIsNone(last_update)


    def test_del(self):
        with Store(self.data_path) as store:
            store.add("0000-0003-1527-0030")
            self.assertTrue("0000-0003-1527-0030" in store)
            del store["0000-0003-1527-0030"]
            self.assertFalse("0000-0003-1527-0030" in store)

    def test_touch(self):
        with Store(self.data_path) as store:
            store.add("0000-0003-1527-0030")
            (orcid_id, active, last_update, person_uri, person_id, person_class) = store["0000-0003-1527-0030"]
            time.sleep(1)
            store.touch("0000-0003-1527-0030")
            (orcid_id, active, new_last_update, person_uri, person_id, person_class) = store["0000-0003-1527-0030"]
            self.assertNotEqual(last_update, new_last_update)

    def test_get_least_recent(self):
        with Store(self.data_path) as store:
            store.add("0000-0003-1527-0030")
            store.add("0000-0003-1527-0031")
            store.add("0000-0003-1527-0032")
            #Deactivate one to make sure not returned.
            del store["0000-0003-1527-0032"]
            #Touch first
            time.sleep(1)
            t = datetime.datetime.utcnow()
            time.sleep(1)
            store.touch("0000-0003-1527-0030")
            results = list(store.get_least_recent())
            self.assertEqual(2, len(results))
            self.assertEqual("0000-0003-1527-0031", results[0][0])
            self.assertEqual("0000-0003-1527-0030", results[1][0])

            #With limit
            results = list(store.get_least_recent(limit=1))
            self.assertEqual(1, len(results))
            self.assertEqual("0000-0003-1527-0031", results[0][0])

            #Before
            results = list(store.get_least_recent(before_datetime=t))
            self.assertEqual(1, len(results))
            self.assertEqual("0000-0003-1527-0031", results[0][0])

    def test_iter(self):
        with Store(self.data_path) as store:
            store.add("0000-0003-1527-0030")
            store.add("0000-0003-1527-0031")
            for orcid_id, active, new_last_update, person_uri, person_id, person_class in store:
                self.assertTrue(orcid_id in ("0000-0003-1527-0030", "0000-0003-1527-0031"))
            self.assertEqual(2, len(list(store)))

    def test_delete_all(self):
        with Store(self.data_path) as store:
            store.add("0000-0003-1527-0030")
            store.add("0000-0003-1527-0031")
            self.assertTrue("0000-0003-1527-0030" in store)
            self.assertTrue("0000-0003-1527-0031" in store)
            store.delete_all()
            self.assertFalse("0000-0003-1527-0030" in store)
            self.assertFalse("0000-0003-1527-0031" in store)


class TestLoad(tests.TestCase):
    def setUp(self):
        self.data_path = tempfile.mkdtemp()

    @my_vcr.use_cassette('loader/load_single.yaml')
    @patch("orcid2vivo_loader.sparql_insert")
    @patch("orcid2vivo_loader.sparql_delete")
    def test_load_single(self, mock_sparql_delete, mock_sparql_insert):
        with Store(self.data_path) as store:
            store.add("0000-0003-1527-0030")
            (orcid_id, active, last_update, person_uri, person_id, person_class) = store["0000-0003-1527-0030"]
            self.assertIsNone(last_update)

        graph1, add_graph1, delete_graph1 = load_single("0000-0003-1527-0030", None, None, None, self.data_path,
                                                        "http://vivo.mydomain.edu/sparql", "vivo@mydomain.edu",
                                                        "password")

        self.assertEqual(232, len(add_graph1))
        self.assertEqual(0, len(delete_graph1))

        self.assertEqual(to_isomorphic(graph1), to_isomorphic(add_graph1))

        with Store(self.data_path) as store:
            #Last update now set
            (orcid_id, active, last_update, person_uri, person_id, person_class) = store["0000-0003-1527-0030"]
            self.assertIsNotNone(last_update)

        #Make sure turtle file created
        self.assertTrue(os.path.exists(os.path.join(self.data_path, "0000-0003-1527-0030.ttl")))

        #Now change a fact and run again. Changed fact is provided by vcr recording.
        #Changed year of Amherst degree.
        graph2, add_graph2, delete_graph2 = load_single("0000-0003-1527-0030", None, None, None,
                                                        self.data_path, "http://vivo.mydomain.edu/sparql",
                                                        "vivo@mydomain.edu", "password")

        self.assertEqual(232, len(graph2))
        self.assertEqual(17, len(add_graph2))
        self.assertEqual(17, len(delete_graph2))

        mock_sparql_insert.assert_has_calls([
            call(add_graph1, "http://vivo.mydomain.edu/sparql", "vivo@mydomain.edu", "password"),
            call(add_graph2, "http://vivo.mydomain.edu/sparql", "vivo@mydomain.edu", "password")])
        mock_sparql_delete.assert_has_calls([
            call(delete_graph1, "http://vivo.mydomain.edu/sparql", "vivo@mydomain.edu", "password"),
            call(delete_graph2, "http://vivo.mydomain.edu/sparql", "vivo@mydomain.edu", "password")])
