
from bson import SON, DBRef, ObjectId

from asyncmongoengine.base.common import get_document
from asyncmongoengine.base.errors import (FieldDoesNotExist,
                                          InvalidDocumentError,
                                          ValidationError)

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

    def __contains__(self, name):
        try:
            val = getattr(self, name)
            return val is not None
        except AttributeError:
            return False

    def __iter__(self):
        return iter(self._fields_ordered)
        
    def __getitem__(self, name):
        """Dictionary-style field access, return a field's value if present.
        """
        try:
            if name in self._fields_ordered:
                return getattr(self, name)
        except AttributeError:
            pass
        raise KeyError(name)

    def __setitem__(self, name, value):
        """Dictionary-style field access, set a field's value.
        """
        # Ensure that the field exists before settings its value
        if not self._dynamic and name not in self._fields:
            raise KeyError(name)
        return setattr(self, name, value)

    def __len__(self):
        return len(self._data)

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
                self._fields.get(name),
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

        for k, v in errors.items():
            print(k)
            print(v)

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

    def to_mongo(self, fields=None):
        fields = fields or []

        data = SON()
        data["_id"] = None
        data["_cls"] = self._class_name

        # only root fields ['test1.a', 'test2'] => ['test1', 'test2']
        root_fields = {f.split(".")[0] for f in fields}

        for field_name in self:
            if root_fields and field_name not in root_fields:
                continue

            value = self._data.get(field_name, None)
            field = self._fields.get(field_name)

            if value is not None:
                value = field.to_mongo(value)

            data[field.db_field] = value

        return data

    @classmethod
    def _get_collection_name(cls):
        """Return the collection name for this class. None for abstract
        class.
        """
        return cls._meta.get("collection", None)

    @classmethod
    def _from_son(cls, son, only_fields=None, created=False):
        """Create an instance of a Document (subclass) from a PyMongo SON."""
        if not only_fields:
            only_fields = []

        if son and not isinstance(son, dict):
            raise ValueError(
                "The source SON object needs to be of type 'dict' but a '%s' was found"
                % type(son)
            )

        # Get the class name from the document, falling back to the given
        # class if unavailable
        class_name = son.get("_cls", cls._class_name)

        # Convert SON to a data dict, making sure each key is a string and
        # corresponds to the right db field.
        data = {}
        for key, value in son.items():
            key = str(key)
            key = cls._db_field_map.get(key, key)
            data[key] = value

        # Return correct subclass for document type
        if class_name != cls._class_name:
            cls = get_document(class_name)

        errors_dict = {}

        fields = cls._fields

        for field_name, field in fields.items():
            if field.db_field in data:
                value = data[field.db_field]
                try:
                    data[field_name] = (
                        value if value is None else field.to_python(value)
                    )
                    if field_name != field.db_field:
                        del data[field.db_field]
                except (AttributeError, ValueError) as e:
                    errors_dict[field_name] = e

        if errors_dict:
            errors = "\n".join(
                ["Field '{}' - {}".format(k, v) for k, v in errors_dict.items()]
            )
            msg = "Invalid data to create a `{}` instance.\n{}".format(
                cls._class_name, errors,
            )
            raise InvalidDocumentError(msg)

        # In STRICT documents, remove any keys that aren't in cls._fields
        # if cls.STRICT:
        #    data = {k: v for k, v in data.items() if k in cls._fields}

        obj = cls(
            __auto_convert=False, _created=created, __only_fields=only_fields, **data
        )
        obj._changed_fields = []

        return obj
