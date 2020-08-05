
from asyncmongoengine.base.document import BaseDocument
from asyncmongoengine.base.metaclasses import (DocumentMetaclass,
                                               TopLevelDocumentMetaclass)


class EmbeddedDocument(BaseDocument, metaclass=DocumentMetaclass):

    __slots__ = ("_instance",)

    my_metaclass = DocumentMetaclass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._instance = None
        self._changed_fields = []

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._data == other._data
        return False

    def __ne__(self, other):
        return not self.__eq__(other)

    
class Document(BaseDocument, metaclass=TopLevelDocumentMetaclass):

    my_metaclass = TopLevelDocumentMetaclass

    __slots__ = ("__objects",)

    async def save_async(
        self,
        force_insert=False,
        validate=True,
        clean=True,
        write_concern=None,
        cascade=None,
        cascade_kwargs=None,
        _refs=None,
        save_condition=None,
        signal_kwargs=None,
        **kwargs
    ):
        if validate:
            self.validate(clean=clean)