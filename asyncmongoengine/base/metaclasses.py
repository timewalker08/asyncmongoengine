
from asyncmongoengine.base.errors import InvalidDocumentError
from asyncmongoengine.base.fields import BaseField

__all__ = ("DocumentMetaclass", "TopLevelDocumentMetaclass")


class DocumentMetaclass(type):
    """Metaclass for all documents."""

    def __new__(mcs, name, bases, attrs):
        super_new = super().__new__

        # If a base class just call super
        metaclass = attrs.get("my_metaclass")
        if metaclass and issubclass(metaclass, DocumentMetaclass):
            return super_new(mcs, name, bases, attrs)

        doc_fields = {}
        field_names = {}
        for attr_name, attr_value in attrs.items():
            if not isinstance(attr_value, BaseField):
                continue
            attr_value.name = attr_name
            if not attr_value.db_field:
                attr_value.db_field = attr_name
            doc_fields[attr_name] = attr_value

            # Count names to ensure no db_field redefinitions
            field_names[attr_value.db_field] = (
                field_names.get(attr_value.db_field, 0) + 1
            )

        # Ensure no duplicate db_fields
        duplicate_db_fields = [k for k, v in field_names.items() if v > 1]
        if duplicate_db_fields:
            msg = "Multiple db_fields defined for: %s " % ", ".join(duplicate_db_fields)
            raise InvalidDocumentError(msg)

        # Set _fields and db_field maps
        attrs["_fields"] = doc_fields
        attrs["_db_field_map"] = {
            k: getattr(v, "db_field", k) for k, v in doc_fields.items()
        }
        attrs["_reverse_db_field_map"] = {
            v: k for k, v in attrs["_db_field_map"].items()
        }

        attrs["_fields_ordered"] = tuple(
            i[1]
            for i in sorted((v.creation_counter, v.name) for v in doc_fields.values())
        )

        attrs["_class_name"] = name

        # Create the new_class
        new_class = super_new(mcs, name, bases, attrs)

        return new_class


class TopLevelDocumentMetaclass(DocumentMetaclass):
    """Metaclass for top-level documents (i.e. documents that have their own
    collection in the database.
    """

    def __new__(mcs, name, bases, attrs):
        super_new = super().__new__

        if attrs.get("my_metaclass") == TopLevelDocumentMetaclass:
            # defaults
            attrs["_meta"] = {
                "abstract": True,
                "max_documents": None,
                "max_size": None,
                "ordering": [],  # default ordering applied at runtime
                "indexes": [],  # indexes to be ensured at runtime
                "id_field": None,
                "index_background": False,
                "index_opts": None,
                "delete_rules": None,
                # allow_inheritance can be True, False, and None. True means
                # "allow inheritance", False means "don't allow inheritance",
                # None means "do whatever your parent does, or don't allow
                # inheritance if you're a top-level class".
                "allow_inheritance": None,
            }
            attrs["_is_base_cls"] = True
            attrs["_meta"].update(attrs.get("meta", {}))
        else:
            attrs["_meta"] = attrs.get("meta", {})
            # Explicitly set abstract to false unless set
            attrs["_meta"]["abstract"] = attrs["_meta"].get("abstract", False)
            attrs["_is_base_cls"] = False

        # Set flag marking as document class - as opposed to an object mixin
        attrs["_is_document"] = True

        new_class = super_new(mcs, name, bases, attrs)

        return new_class



class MetaDict(dict):
    """Custom dictionary for meta classes.
    Handles the merging of set indexes
    """

    _merge_options = ("indexes",)

    def merge(self, new_options):
        for k, v in new_options.items():
            if k in self._merge_options:
                self[k] = self.get(k, []) + v
            else:
                self[k] = v
