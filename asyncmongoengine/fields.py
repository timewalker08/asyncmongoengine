
import datetime
import decimal
import re
import time

from bson.int64 import Int64

from asyncmongoengine.base.errors import InvalidQueryError
from asyncmongoengine.base.fields import BaseField
from asyncmongoengine.document import EmbeddedDocument

try:
    import dateutil
except ImportError:
    dateutil = None
else:
    import dateutil.parser


class StringField(BaseField):
    """A unicode string field."""

    def __init__(self, regex=None, max_length=None, min_length=None, **kwargs):
        self.regex = re.compile(regex) if regex else None
        self.max_length = max_length
        self.min_length = min_length
        super().__init__(**kwargs)

    def to_python(self, value):
        if isinstance(value, str):
            return value
        try:
            value = value.decode("utf-8")
        except Exception:
            pass
        return value

    def validate(self, value):
        if not isinstance(value, str):
            self.error("StringField only accepts string values")

        if self.max_length is not None and len(value) > self.max_length:
            self.error("String value is too long")

        if self.min_length is not None and len(value) < self.min_length:
            self.error("String value is too short")

        if self.regex is not None and self.regex.match(value) is None:
            self.error("String value did not match validation regex")



class IntField(BaseField):
    """32-bit integer field."""

    def __init__(self, min_value=None, max_value=None, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        super().__init__(**kwargs)

    def to_python(self, value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            pass
        return value

    def validate(self, value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            self.error("%s could not be converted to int" % value)

        if self.min_value is not None and value < self.min_value:
            self.error("Integer value is too small")

        if self.max_value is not None and value > self.max_value:
            self.error("Integer value is too large")


class LongField(BaseField):
    """64-bit integer field. (Equivalent to IntField since the support to Python2 was dropped)"""

    def __init__(self, min_value=None, max_value=None, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        super().__init__(**kwargs)

    def to_python(self, value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            pass
        return value

    def to_mongo(self, value):
        return Int64(value)

    def validate(self, value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            self.error("%s could not be converted to long" % value)

        if self.min_value is not None and value < self.min_value:
            self.error("Long value is too small")

        if self.max_value is not None and value > self.max_value:
            self.error("Long value is too large")

    def prepare_query_value(self, op, value):
        if value is None:
            return value

        return super().prepare_query_value(op, int(value))


class FloatField(BaseField):
    """Floating point number field."""

    def __init__(self, min_value=None, max_value=None, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        super().__init__(**kwargs)

    def to_python(self, value):
        try:
            value = float(value)
        except ValueError:
            pass
        return value

    def validate(self, value):
        if isinstance(value, int):
            try:
                value = float(value)
            except OverflowError:
                self.error("The value is too large to be converted to float")

        if not isinstance(value, float):
            self.error("FloatField only accepts float and integer values")

        if self.min_value is not None and value < self.min_value:
            self.error("Float value is too small")

        if self.max_value is not None and value > self.max_value:
            self.error("Float value is too large")

    def prepare_query_value(self, op, value):
        if value is None:
            return value

        return super().prepare_query_value(op, float(value))


class DecimalField(BaseField):
    """Fixed-point decimal number field. Stores the value as a float by default unless `force_string` is used.
    If using floats, beware of Decimal to float conversion (potential precision loss)

    .. versionchanged:: 0.8
    .. versionadded:: 0.3
    """

    def __init__(
        self,
        min_value=None,
        max_value=None,
        force_string=False,
        precision=2,
        rounding=decimal.ROUND_HALF_UP,
        **kwargs
    ):
        """
        :param min_value: Validation rule for the minimum acceptable value.
        :param max_value: Validation rule for the maximum acceptable value.
        :param force_string: Store the value as a string (instead of a float).
         Be aware that this affects query sorting and operation like lte, gte (as string comparison is applied)
         and some query operator won't work (e.g: inc, dec)
        :param precision: Number of decimal places to store.
        :param rounding: The rounding rule from the python decimal library:

            - decimal.ROUND_CEILING (towards Infinity)
            - decimal.ROUND_DOWN (towards zero)
            - decimal.ROUND_FLOOR (towards -Infinity)
            - decimal.ROUND_HALF_DOWN (to nearest with ties going towards zero)
            - decimal.ROUND_HALF_EVEN (to nearest with ties going to nearest even integer)
            - decimal.ROUND_HALF_UP (to nearest with ties going away from zero)
            - decimal.ROUND_UP (away from zero)
            - decimal.ROUND_05UP (away from zero if last digit after rounding towards zero would have been 0 or 5; otherwise towards zero)

            Defaults to: ``decimal.ROUND_HALF_UP``

        """
        self.min_value = min_value
        self.max_value = max_value
        self.force_string = force_string
        self.precision = precision
        self.rounding = rounding

        super().__init__(**kwargs)

    def to_python(self, value):
        if value is None:
            return value

        # Convert to string for python 2.6 before casting to Decimal
        try:
            value = decimal.Decimal(value)
        except (TypeError, ValueError, decimal.InvalidOperation):
            return value
        return value.quantize(
            decimal.Decimal(".%s" % ("0" * self.precision)), rounding=self.rounding
        )

    def to_mongo(self, value):
        if value is None:
            return value
        if self.force_string:
            return str(self.to_python(value))
        return float(self.to_python(value))

    def validate(self, value):
        if not isinstance(value, decimal.Decimal):
            if not isinstance(value, str):
                value = str(value)
            try:
                value = decimal.Decimal(value)
            except (TypeError, ValueError, decimal.InvalidOperation) as exc:
                self.error("Could not convert value to decimal: %s" % exc)

        if self.min_value is not None and value < self.min_value:
            self.error("Decimal value is too small")

        if self.max_value is not None and value > self.max_value:
            self.error("Decimal value is too large")

    def prepare_query_value(self, op, value):
        return super().prepare_query_value(op, self.to_mongo(value))


class BooleanField(BaseField):
    """Boolean field type.

    .. versionadded:: 0.1.2
    """

    def to_python(self, value):
        try:
            value = bool(value)
        except ValueError:
            pass
        return value

    def validate(self, value):
        if not isinstance(value, bool):
            self.error("BooleanField only accepts boolean values")


class DateTimeField(BaseField):
    """Datetime field.

    Uses the python-dateutil library if available alternatively use time.strptime
    to parse the dates.  Note: python-dateutil's parser is fully featured and when
    installed you can utilise it to convert varying types of date formats into valid
    python datetime objects.

    Note: To default the field to the current datetime, use: DateTimeField(default=datetime.utcnow)

    Note: Microseconds are rounded to the nearest millisecond.
      Pre UTC microsecond support is effectively broken.
      Use :class:`~mongoengine.fields.ComplexDateTimeField` if you
      need accurate microsecond support.
    """

    def validate(self, value):
        new_value = self.to_mongo(value)
        if not isinstance(new_value, (datetime.datetime, datetime.date)):
            self.error('cannot parse date "%s"' % value)

    def to_mongo(self, value):
        if value is None:
            return value
        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, datetime.date):
            return datetime.datetime(value.year, value.month, value.day)
        if callable(value):
            return value()

        if not isinstance(value, str):
            return None

        return self._parse_datetime(value)

    def _parse_datetime(self, value):
        # Attempt to parse a datetime from a string
        value = value.strip()
        if not value:
            return None

        if dateutil:
            try:
                return dateutil.parser.parse(value)
            except (TypeError, ValueError, OverflowError):
                return None

        # split usecs, because they are not recognized by strptime.
        if "." in value:
            try:
                value, usecs = value.split(".")
                usecs = int(usecs)
            except ValueError:
                return None
        else:
            usecs = 0
        kwargs = {"microsecond": usecs}
        try:  # Seconds are optional, so try converting seconds first.
            return datetime.datetime(
                *time.strptime(value, "%Y-%m-%d %H:%M:%S")[:6], **kwargs
            )
        except ValueError:
            try:  # Try without seconds.
                return datetime.datetime(
                    *time.strptime(value, "%Y-%m-%d %H:%M")[:5], **kwargs
                )
            except ValueError:  # Try without hour/minutes/seconds.
                try:
                    return datetime.datetime(
                        *time.strptime(value, "%Y-%m-%d")[:3], **kwargs
                    )
                except ValueError:
                    return None

    def prepare_query_value(self, op, value):
        return super().prepare_query_value(op, self.to_mongo(value))


class DateField(DateTimeField):
    def to_mongo(self, value):
        value = super().to_mongo(value)
        # drop hours, minutes, seconds
        if isinstance(value, datetime.datetime):
            value = datetime.datetime(value.year, value.month, value.day)
        return value

    def to_python(self, value):
        value = super().to_python(value)
        # convert datetime to date
        if isinstance(value, datetime.datetime):
            value = datetime.date(value.year, value.month, value.day)
        return value


class EmbeddedDocumentField(BaseField):
    """An embedded document field - with a declared document_type.
    Only valid values are subclasses of :class:`~mongoengine.EmbeddedDocument`.
    """

    def __init__(self, document_type, **kwargs):
        # XXX ValidationError raised outside of the "validate" method.
        if not issubclass(document_type, EmbeddedDocument):
            self.error(
                "Invalid embedded document class provided to an "
                "EmbeddedDocumentField"
            )

        self.document_type_obj = document_type
        super().__init__(**kwargs)

    @property
    def document_type(self):
        return self.document_type_obj

    def to_python(self, value):
        if not isinstance(value, self.document_type):
            return self.document_type._from_son(
                value, _auto_dereference=self._auto_dereference
            )
        return value

    def to_mongo(self, value, fields=None):
        if not isinstance(value, self.document_type):
            return value
        return self.document_type.to_mongo(value, fields)

    def validate(self, value, clean=True):
        """Make sure that the document instance is an instance of the
        EmbeddedDocument subclass provided when the document was defined.
        """
        # Using isinstance also works for subclasses of self.document
        if not isinstance(value, self.document_type):
            self.error(
                "Invalid embedded document instance provided to an "
                "EmbeddedDocumentField"
            )
        self.document_type.validate(value, clean)

    def lookup_member(self, member_name):
        doc_and_subclasses = [self.document_type] + self.document_type.__subclasses__()
        for doc_type in doc_and_subclasses:
            field = doc_type._fields.get(member_name)
            if field:
                return field

    def prepare_query_value(self, op, value):
        if value is not None and not isinstance(value, self.document_type):
            try:
                value = self.document_type._from_son(value)
            except ValueError:
                raise InvalidQueryError(
                    "Querying the embedded document '%s' failed, due to an invalid query value"
                    % (self.document_type._class_name,)
                )
        super().prepare_query_value(op, value)
        return self.to_mongo(value)


class ListField(BaseField):
    def __init__(self, field=None, max_length=None, **kwargs):
        self.field = field
        self.max_length = max_length
        kwargs.setdefault("default", lambda: [])
        super().__init__(**kwargs)

    def __get__(self, instance, owner):
        if instance is None:
            # Document class being used rather than a document object
            return self

        value = instance._data.get(self.name)

        return value

    def to_mongo(self, value, fields=None):
        if isinstance(self.field, EmbeddedDocumentField):
            return [item.to_mongo() for item in value]

        return value

