from contextlib import contextmanager

from pymongo.read_concern import ReadConcern
from pymongo.write_concern import WriteConcern


@contextmanager
def set_write_concern(collection, write_concerns):
    combined_concerns = dict(collection.write_concern.document.items())
    combined_concerns.update(write_concerns)
    yield collection.with_options(write_concern=WriteConcern(**combined_concerns))
