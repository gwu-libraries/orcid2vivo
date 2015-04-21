import hashlib

#Prefixes
# PREFIX_APPOINTMENT = "apt"
# PREFIX_AWARD_RECEIPT = "awdrec"
PREFIX_AWARD = "awd"
PREFIX_AWARDED_DEGREE = "awdgre"
# PREFIX_EVENT = "evnt"
# PREFIX_COURSE = "crs"
PREFIX_DEGREE = "dgre"
PREFIX_DOCUMENT = "doc"
PREFIX_GRANT = "grant"
PREFIX_JOURNAL = "jrnl"
# PREFIX_MEMBERSHIP = "memb"
# PREFIX_NON_DEGREE = "nondgre"
PREFIX_ORGANIZATION = "org"
# PREFIX_PATENT = "pat"
PREFIX_PERSON = "per"
# PREFIX_PRESENTER = "presr"
# PREFIX_PRESENTATION = "pres"
# PREFIX_RESEARCH_AREA = "ra"
# PREFIX_REVIEWERSHIP = "rev"
# PREFIX_TEACHER = "tch"


def to_hash_identifier(prefix, parts):
    """
    Return an identifier composed of the prefix and hash of the parts.
    """
    hash_parts = hashlib.md5("".join([unicode(part) for part in parts if part]).encode("utf-8"))
    return "%s-%s" % (prefix, hash_parts.hexdigest())
