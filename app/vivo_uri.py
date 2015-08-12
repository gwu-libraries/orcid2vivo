import vivo_namespace as ns
import hashlib
import re
import collections


def to_hash_identifier(prefix, parts):
    """
    Return an identifier composed of the prefix and hash of the parts.
    """
    hash_parts = hashlib.md5("".join([unicode(part) for part in parts if part]).encode("utf-8"))
    return "%s-%s" % (prefix, hash_parts.hexdigest())


class HashIdentifierStrategy():
    """
    A strategy for constructing an identifier by creating a prefix from the
    class or general class and a body from a hash of the attributes.

    Other identifier strategies must implement to_uri().
    """
    pattern = re.compile("^.+/(.+?)(#(.+))?$")

    def __init__(self):
        pass

    def to_uri(self, clazz, attrs, general_clazz=None):
        """
        Given an RDF class and a set of attributes for an entity, produce a URI.
        :param clazz: the class of the entity.
        :param attrs: a map of identifying attributes for an entity.
        :param general_clazz: a superclass of the entity that can be used to group like entities.
        :return: URI for the entity.
        """
        return ns.D["%s-%s" % (self._class_to_prefix(general_clazz) or self._class_to_prefix(clazz),
                    self._attrs_to_hash(attrs))]

    @staticmethod
    def _class_to_prefix(clazz):
        if clazz:
            match = HashIdentifierStrategy.pattern.search(clazz)
            assert match
            return (match.group(3) or match.group(1)).lower()
        return None

    @staticmethod
    def _attrs_to_hash(attrs):
        sorted_attrs = collections.OrderedDict(sorted(attrs.items()))
        hash_parts = hashlib.md5("".join([unicode(part) for part in sorted_attrs.values() if part]).encode("utf-8"))
        return hash_parts.hexdigest()