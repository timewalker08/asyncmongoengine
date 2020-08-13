
from asyncmongoengine.base.errors import ValidationError

__all__ = ("BaseField", "ComplexBaseField", "ObjectIdField")


class BaseField(object):

    name = None
    creation_counter = 0
    auto_creation_counter = -1

    def __init__(
        self,
        db_field=None,
        required=False,
        default=None,
        unique=False,
        unique_with=None,
        validation=None,
        choices=None,
        null=False,
        sparse=False,
        **kwargs
    ):
        """
        :param db_field: The database field to store this field in
            (defaults to the name of the field)
        :param required: If the field is required. Whether it has to have a
            value or not. Defaults to False.
        :param default: (optional) The default value for this field if no value
            has been set (or if the value has been unset).  It can be a
            callable.
        :param unique: Is the field value unique or not.  Defaults to False.
        :param unique_with: (optional) The other field this field should be
            unique with.
        :param validation: (optional) A callable to validate the value of the
            field.  The callable takes the value as parameter and should raise
            a ValidationError if validation fails
        :param choices: (optional) The valid choices
        :param null: (optional) If the field value can be null. If no and there is a default value
            then the default value is set
        :param sparse: (optional) `sparse=True` combined with `unique=True` and `required=False`
            means that uniqueness won't be enforced for `None` values
        :param **kwargs: (optional) Arbitrary indirection-free metadata for
            this field can be supplied as additional keyword arguments and
            accessed as attributes of the field. Must not conflict with any
            existing attributes. Common metadata includes `verbose_name` and
            `help_text`.
        """
        self.db_field = db_field
        self.required = required
        self.default = default
        self.unique = bool(unique or unique_with)
        self.unique_with = unique_with
        self.validation = validation
        self.choices = choices
        self.null = null
        self.sparse = sparse
        self._owner_document = None

        if self.db_field is not None and not isinstance(self.db_field, str):
            raise TypeError("db_field should be a string.")

        if isinstance(self.db_field, str) and (
            "." in self.db_field
            or "\0" in self.db_field
            or self.db_field.startswith("$")
        ):
            raise ValueError(
                'field names cannot contain dots (".") or null characters '
                '("\\0"), and they must not start with a dollar sign ("$").'
            )

        self.__dict__.update(kwargs)

        # Adjust the appropriate creation counter, and save our local copy.
        if self.db_field == "_id":
            self.creation_counter = BaseField.auto_creation_counter
            BaseField.auto_creation_counter -= 1
        else:
            self.creation_counter = BaseField.creation_counter
            BaseField.creation_counter += 1

    def __get__(self, instance, owner):
        """Descriptor for retrieving a value from a field in a document.
        """
        if instance is None:
            # Document class being used rather than a document object
            return self

        # Get value from document instance if available
        return instance._data.get(self.name)

    def __set__(self, instance, value):
        if value is None:
            if self.null:
                value = None
            elif self.default is not None:
                value = self.default
                if callable(value):
                    value = value()

        instance._data[self.name] = value

    def to_python(self, value):
        """Convert a MongoDB-compatible type to a Python type."""
        return value

    def to_mongo(self, value):
        """Convert a Python type to a MongoDB-compatible type."""
        return self.to_python(value)

    def validate(self, value, clean=True):
        """Perform validation on a value."""
        pass
    
    def _validate(self, value, **kwargs):
        # Check the Choices Constraint
        #if self.choices:
        #    self._validate_choices(value)

        self.validate(value, **kwargs)

    def error(self, message="", errors=None, field_name=None):
        """Raise a ValidationError."""
        field_name = field_name if field_name else self.name
        raise ValidationError(message, errors=errors, field_name=field_name)


class ComplexBaseField(BaseField):
    """Handles complex fields, such as lists / dictionaries.

    Allows for nesting of embedded documents inside complex types.
    Handles the lazy dereferencing of a queryset by lazily dereferencing all
    items in a list / dict rather than one at a time.

    .. versionadded:: 0.5
    """

    field = None

    def __get__(self, instance, owner):
        """Descriptor to automatically dereference references."""
        if instance is None:
            # Document class being used rather than a document object
            return self

        value = super().__get__(instance, owner)

        # Convert lists / values so we can watch for any changes on them
        if isinstance(value, (list, tuple)):
            instance._data[self.name] = value
        elif isinstance(value, dict):
            instance._data[self.name] = value

        return value

    def to_python(self, value):
        """Convert a MongoDB-compatible type to a Python type."""
        pass

    def to_mongo(self, value, use_db_field=True, fields=None):
        """Convert a Python type to a MongoDB-compatible type."""
        pass

    def validate(self, value):
        """If field is provided ensure the value is valid."""
        errors = {}
        if self.field:
            if hasattr(value, "items"):
                sequence = value.items()
            else:
                sequence = enumerate(value)
            for k, v in sequence:
                try:
                    self.field._validate(v)
                except ValidationError as error:
                    errors[k] = error.errors or error
                except (ValueError, AssertionError) as error:
                    errors[k] = error

            if errors:
                field_class = self.field.__class__.__name__
                self.error(
                    "Invalid {} item ({})".format(field_class, value), errors=errors
                )
        # Don't allow empty values if required
        if self.required and not value:
            self.error("Field is required and cannot be empty")

    def prepare_query_value(self, op, value):
        return self.to_mongo(value)

    def lookup_member(self, member_name):
        if self.field:
            return self.field.lookup_member(member_name)
        return None

    def _set_owner_document(self, owner_document):
        if self.field:
            self.field.owner_document = owner_document
        self._owner_document = owner_document