class PlannerError(Exception):
    """Base exception for user-presentable application errors."""


class ExcelImportError(PlannerError):
    pass


class MissingRequiredColumnError(ExcelImportError):
    pass


class InvalidQuantityError(PlannerError):
    pass


class UnknownUnitError(PlannerError):
    pass


class ProductMatchingError(PlannerError):
    pass


class NoCompatibleBoxError(PlannerError):
    pass


class BoxWeightExceededError(PlannerError):
    pass


class VehicleCapacityExceededError(PlannerError):
    pass


class PlanValidationError(PlannerError):
    pass


class DatabaseError(PlannerError):
    pass


class ExportError(PlannerError):
    pass

