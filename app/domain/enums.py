from enum import StrEnum


class ProductCategory(StrEnum):
    GARMENT = "GARMENT"
    FABRIC_ROLL = "FABRIC_ROLL"


class PackagingRule(StrEnum):
    BOXED = "BOXED"
    DIRECT_LOAD = "DIRECT_LOAD"
    PALLETIZED = "PALLETIZED"
    BOXED_OR_DIRECT = "BOXED_OR_DIRECT"


class MatchType(StrEnum):
    EXACT = "EXACT"
    STARTS_WITH = "STARTS_WITH"
    CONTAINS = "CONTAINS"
    REGEX = "REGEX"


class PlanStatus(StrEnum):
    DRAFT = "DRAFT"
    VALID = "VALID"
    INVALID = "INVALID"
    EXPORTED = "EXPORTED"


class ConfidenceLevel(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

