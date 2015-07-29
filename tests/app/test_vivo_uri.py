from unittest import TestCase
from app.vivo_uri import HashIdentifierStrategy
from app.vivo_namespace import VIVO, OBO


class TestHashIdentifierStrategy(TestCase):
    def setUp(self):
        self.strategy = HashIdentifierStrategy()

    def test_to_identifier(self):
        uri = "http://vivo.mydomain.edu/individual/grant-3c73b079585811b9cbb23c3253a0796a"
        self.assertEqual(uri, str(self.strategy.to_uri(VIVO.Grant, {"foo": "My Foo", "bar": "My Bar"})))
        #Switch order
        self.assertEqual(uri, str(self.strategy.to_uri(VIVO.Grant, {"bar": "My Bar", "foo": "My Foo"})))
        #Add a none
        self.assertEqual(uri, str(self.strategy.to_uri(VIVO.Grant,
                                                              {"foo": "My Foo", "bar": "My Bar", "foobar": None})))
        #General class trumps class
        self.assertEqual(uri, str(self.strategy.to_uri(VIVO.AnotherClazz,
                                                       {"foo": "My Foo", "bar": "My Bar", "foobar": None},
                                                       general_clazz=VIVO.Grant)))

        #Different class
        self.assertNotEqual(uri, str(self.strategy.to_uri(VIVO.NotAGrant, {"foo": "My Foo", "bar": "My Bar"})))
        #General class
        self.assertNotEqual(uri, str(self.strategy.to_uri(VIVO.Grant, {"foo": "My Foo", "bar": "My Bar"},
                                                          general_clazz=VIVO.AnotherClass)))
        #Changed attr
        self.assertNotEqual(uri, str(self.strategy.to_uri(VIVO.Grant, {"foo": "Not My Foo", "bar": "My Bar"})))
        #Additional attr
        self.assertNotEqual(uri, str(self.strategy.to_uri(VIVO.Grant,
                                                                 {"foo": "My Foo", "bar": "My Bar",
                                                                  "foobar": "My FooBar"})))

    def test_class_to_prefix(self):
        self.assertEqual("grant", HashIdentifierStrategy._class_to_prefix(VIVO.Grant))
        self.assertEqual("ro_0000052", HashIdentifierStrategy._class_to_prefix(OBO.RO_0000052))
        self.assertIsNone(HashIdentifierStrategy._class_to_prefix(None))
