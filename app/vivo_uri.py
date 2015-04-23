import hashlib

#Prefixes
PREFIX_AWARD = "awd"
PREFIX_AWARDED_DEGREE = "awdgre"
PREFIX_DEGREE = "dgre"
PREFIX_DOCUMENT = "doc"
PREFIX_GRANT = "grant"
PREFIX_JOURNAL = "jrnl"
PREFIX_ORGANIZATION = "org"
PREFIX_PERSON = "per"


def to_hash_identifier(prefix, parts):
    """
    Return an identifier composed of the prefix and hash of the parts.
    """
    hash_parts = hashlib.md5("".join([unicode(part) for part in parts if part]).encode("utf-8"))
    return "%s-%s" % (prefix, hash_parts.hexdigest())
