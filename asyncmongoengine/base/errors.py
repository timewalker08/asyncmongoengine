
class InvalidDocumentError(Exception):
    pass

class OperationError(Exception):
    pass

class NotUniqueError(OperationError):
    pass

class InvalidQueryError(Exception):
    pass

class NotRegistered(Exception):
    pass

class FieldDoesNotExist(Exception):
    """Raised when trying to set a field
    not declared in a :class:`~mongoengine.Document`
    or an :class:`~mongoengine.EmbeddedDocument`.

    To avoid this behavior on data loading,
    you should set the :attr:`strict` to ``False``
    in the :attr:`meta` dictionary.
    """


class ValidationError(AssertionError):
    """Validation exception.

    May represent an error validating a field or a
    document containing fields with validation errors.

    :ivar errors: A dictionary of errors for fields within this
        document or list, or None if the error is for an
        individual field.
    """

    errors = {}

    def __init__(self, message="", **kwargs):
        super().__init__(message)
        self.errors = kwargs.get("errors", {})
        self.field_name = kwargs.get("field_name")
        self.message = message

    def __str__(self):
        return str(self.message)

    def __repr__(self):
        return "{}({},)".format(self.__class__.__name__, self.message)