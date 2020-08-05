
from asyncmongoengine.base.errors import FieldDoesNotExist, ValidationError

NON_FIELD_ERRORS = "__all__"


class BaseDocument(object):
    def __init__(self, *args, **values):
        """
        Initialise a document or an embedded document.

        :param values: A dictionary of keys and values for the document.
            It may contain additional reserved keywords, e.g. "__auto_convert".
        :param __auto_convert: If True, supplied values will be converted
            to Python-type values via each field's `to_python` method.
        :param __only_fields: A set of fields that have been loaded for
            this document. Empty if all fields have been loaded.
        :param _created: Indicates whether this is a brand new document
            or whether it's already been persisted before. Defaults to true.
        """
        self._initialised = False
        self._created = True

        if args:
            raise TypeError(
                "Instantiating a document with positional arguments is not "
                "supported. Please use `field_name=value` keyword arguments."
            )

        __auto_convert = values.pop("__auto_convert", True)
        _created = values.pop("_created", True)

        _undefined_fields = set(values.keys()) - set(
            list(self._fields.keys()) + ["id", "pk", "_cls", "_text_score"]
        )
        if _undefined_fields:
            msg = ('The fields "{}" do not exist on the document "{}"').format(
                _undefined_fields, self._class_name
            )
            raise FieldDoesNotExist(msg)

        self._data = {}

        for key, field in self._fields.items():
            value = getattr(self, key, None)
            setattr(self, key, value)

        if "_cls" not in values:
            self._cls = self._class_name

        for key, value in values.items():
            key = self._reverse_db_field_map.get(key, key)
            if key in self._fields or key in ("id", "pk", "_cls"):
                if __auto_convert and value is not None:
                    field = self._fields.get(key)
                    if field:
                        value = field.to_python(value)
                setattr(self, key, value)
            else:
                self._data[key] = value

        self._initialised = True
        self._created = _created


    def validate(self, clean=True):
        """Ensure that all fields' values are valid and that required fields
        are present.

        Raises :class:`ValidationError` if any of the fields' values are found
        to be invalid.
        """
        # Ensure that each field is matched to a valid value
        errors = {}
        if clean:
            try:
                self.clean()
            except ValidationError as error:
                errors[NON_FIELD_ERRORS] = error

        fields = [
            (
                self._fields.get(name, self._dynamic_fields.get(name)),
                self._data.get(name),
            )
            for name in self._fields_ordered
        ]

        for field, value in fields:
            if value is not None:
                try:
                    field._validate(value)
                except ValidationError as error:
                    errors[field.name] = error.errors or error
                except (ValueError, AttributeError, AssertionError) as error:
                    errors[field.name] = error
            elif field.required and not getattr(field, "_auto_gen", False):
                errors[field.name] = ValidationError(
                    "Field is required", field_name=field.name
                )

        if errors:
            pk = "None"
            if hasattr(self, "pk"):
                pk = self.pk
            elif self._instance and hasattr(self._instance, "pk"):
                pk = self._instance.pk
            message = "ValidationError ({}:{}) ".format(self._class_name, pk)
            raise ValidationError(message, errors=errors)


    def clean(self):
        """
        Hook for doing document level data cleaning before validation is run.

        Any ValidationError raised by this method will not be associated with
        a particular field; it will have a special-case association with the
        field defined by NON_FIELD_ERRORS.
        """
        pass
