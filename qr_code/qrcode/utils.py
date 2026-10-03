"""Utility classes and functions for configuring and setting up the content and the look of a QR code."""
import datetime
import re
from collections import namedtuple
from dataclasses import asdict
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Optional, Any, Union, Sequence, List, Tuple

from django.utils.html import escape
from pydantic import validate_call
from pydantic.dataclasses import dataclass as pydantic_dataclass
from qr_code.qrcode.constants import (
    DEFAULT_BOOST_ERROR,
    DEFAULT_BORDER_SIZE,
    DEFAULT_ECI,
    DEFAULT_ENCODING,
    DEFAULT_ERROR_CORRECTION,
    DEFAULT_IMAGE_FORMAT,
    DEFAULT_MODULE_SIZE,
    DEFAULT_VERSION,
    ERROR_CORRECTION_DICT,
    SIZE_DICT,
)

from segno import helpers


class QRCodeOptions:
    """
    Represents the options used to create and draw a QR code.
    """

    @validate_call
    def __init__(
        self,
        size: Union[int, float, str, Decimal, None] = DEFAULT_MODULE_SIZE,
        border: int = DEFAULT_BORDER_SIZE,
        version: Union[int, str, None] = DEFAULT_VERSION,
        image_format: str = DEFAULT_IMAGE_FORMAT,
        error_correction: str = DEFAULT_ERROR_CORRECTION,
        encoding: Optional[str] = DEFAULT_ENCODING,
        boost_error: bool = DEFAULT_BOOST_ERROR,
        micro: bool = False,
        eci: bool = DEFAULT_ECI,
        dark_color: Union[tuple, str, bool, None] = "black",
        light_color: Union[tuple, str, bool, None] = "white",
        finder_dark_color: Union[tuple, str, bool, None] = False,
        finder_light_color: Union[tuple, str, bool, None] = False,
        data_dark_color: Union[tuple, str, bool, None] = False,
        data_light_color: Union[tuple, str, bool, None] = False,
        version_dark_color: Union[tuple, str, bool, None] = False,
        version_light_color: Union[tuple, str, bool, None] = False,
        format_dark_color: Union[tuple, str, bool, None] = False,
        format_light_color: Union[tuple, str, bool, None] = False,
        alignment_dark_color: Union[tuple, str, bool, None] = False,
        alignment_light_color: Union[tuple, str, bool, None] = False,
        timing_dark_color: Union[tuple, str, bool, None] = False,
        timing_light_color: Union[tuple, str, bool, None] = False,
        separator_color: Union[tuple, str, bool, None] = False,
        dark_module_color: Union[tuple, str, bool, None] = False,
        quiet_zone_color: Union[tuple, str, bool, None] = False,
    ) -> None:
        """
        :param size: The size of the QR code as an integer, float, Decimal or a string. Default is *'m'*.
        :type: str, int, float or Decimal
        :param int border: The size of the border (blank space around the code).
        :param version: The version of the QR code gives the size of the matrix. Default is *None* which mean automatic
            in order to avoid data overflow.

        :param version: QR Code version. If the value is ``None`` (default), the minimal version which fits for the
            input data will be used. Valid values: "M1", "M2", "M3", "M4" (for Micro QR codes) or an integer between
            1 and 40 (for QR codes). The `version` parameter is case insensitive.

        :type version: int, str or None
        :param str image_format: The graphics format used to render the QR code. It can be either *'svg'* or *'png'*. Default is *'svg'*.
        :param str error_correction: How much error correction that might be required to read the code. It can be
            either *'L'*, *'M'*, *'Q'*, or *'H'*. Default is *'M'*.

        :param bool boost_error: Tells whether the QR code encoding engine tries to increase the error correction level
            if it does not affect the version. Error correction level is not increased when it impacts the version of the code.

        :param bool micro: Indicates if a Micro QR Code should be created. Default: False
        :param encoding: Indicates the encoding in mode "byte". By default `encoding` is ``UTF-8``. When set to
            ``None``, the implementation tries to use the standard conform ISO/IEC 8859-1 encoding and if it does not
            fit, it will use UTF-8. Note that no ECI mode indicator is inserted by default (see ``eci``). The `encoding`
            parameter is case-insensitive.

        :type encoding: str or None
        :param bool eci: Indicates if binary data which does not use the default encoding (ISO/IEC 8859-1) should
            enforce the ECI mode. Since a lot of QR code readers do not support the ECI mode, this feature is disabled
            by default and the data is encoded in the provided `encoding` using the usual "byte" mode. Set ``eci`` to
            ``True`` if an ECI header should be inserted into the QR Code. Note that the implementation may not know
            the ECI designator for the provided `encoding` and may raise an exception if the ECI designator cannot be
            found. The ECI mode is not supported by Micro QR Codes.

        :param dark_color: Color of the dark modules (default: black). The color can be provided as ``(R, G, B)`` tuple,
            as hexadecimal format (``#RGB``, ``#RRGGBB`` ``RRGGBBAA``), or web color name (i.e. ``red``). If alpha
            transparency is supported (i.e. PNG and SVG), hexadecimal values like #RRGGBBAA are accepted.

        :param light_color: Color of the light modules (default: transparent). See `color` for valid values. If light
            is set to ``None`` the light modules will be transparent.

        :param finder_dark_color: Color of the dark finder modules (default: same as ``dark_color``)
        :param finder_light_color: Color of the light finder modules (default: same as ``light_color``)
        :param data_dark_color: Color of the dark data modules (default: same as ``dark_color``)
        :param data_light_color: Color of the light data modules (default: same as ``light_color``)
        :param version_dark_color: Color of the dark version modules (default: same as ``dark_color``)
        :param version_light_color: Color of the light version modules (default: same as ``light_color``)
        :param format_dark_color: Color of the dark format modules (default: same as ``dark_color``)
        :param format_light_color: Color of the light format modules (default: same as ``light_color``)
        :param alignment_dark_color: Color of the dark alignment modules (default: same as ``dark_color``)
        :param alignment_light_color: Color of the light alignment modules (default: same as ``light_color``)
        :param timing_dark_color: Color of the dark timing pattern modules (default: same as ``dark_color``)
        :param timing_light_color: Color of the light timing pattern modules (default: same as ``light_color``)
        :param separator_color: Color of the separator (default: same as ``light_color``)
        :param dark_module_color: Color of the dark module (default: same as ``dark_color``)
        :param quiet_zone_color: Color of the quiet zone modules (default: same as ``light_color``)

        The *size* parameter gives the size of each module of the QR code matrix. It can be either a positive integer
        or one of the following letters:
        * t or T: tiny (value: 6)
        * s or S: small (value: 12)
        * m or M: medium (value: 18)
        * l or L: large (value: 30)
        * h or H: huge (value: 48)

        For PNG image format the size unit is in pixels, while the unit is 0.1 mm for SVG format.

        The *border* parameter controls how many modules thick the border should be (blank space around the code).
        The default is 4, which is the minimum according to the specs.

        The *version* parameter is an integer from 1 to 40 that controls the size of the QR code matrix. Set to None to
        determine this automatically. The smallest, version 1, is a 21 x 21 matrix. The biggest, version 40, is
        177 x 177 matrix.
        The size grows by 4 modules/side.
        For Micro QR codes, valid values are "M1", "M2", "M3", "M4".

        There are 4 error correction levels used for QR codes, with each one adding different amounts of "backup" data
        depending on how much damage the QR code is expected to suffer in its intended environment, and hence how much
        error correction may be required. The correction level can be configured with the *error_correction* parameter as follow:
        * l or L: error correction level L – up to 7% damage
        * m or M: error correction level M – up to 15% damage
        * q or Q: error correction level Q – up to 25% damage
        * h or H: error correction level H – up to 30% damage

        You may enforce the creation of a Micro QR Code with `micro=True`. The `micro` option defaults to `False`.

        The `encoding` option controls the text encoding used in mode "byte" (used for any general text content). By default `encoding` is ``UTF-8``. When set to ``None``, the implementation (based on Segno) tries to use the standard conform ISO/IEC 8859-1 encoding and if it does not fit, it will use UTF-8. Note that no ECI mode indicator is inserted by default (see `eci` option). The `encoding` parameter is case-insensitive.

        The `boost_error` indicates whether the QR code encoding engine (Segno) tries to increase the error correction level if it does not affect the version. Error correction level is not increased when it impacts the version of the code.

        The `eci` option indicates if binary data which does not use the default encoding (ISO/IEC 8859-1) should enforce the ECI mode. Since a lot of QR code readers do not support the ECI mode, this feature is disabled by default and the data is encoded in the provided encoding using the usual “byte” mode. Set eci to `True` if an ECI header should be inserted into the QR Code. Note that the implementation may not know the ECI designator for the provided encoding and may raise an exception if the ECI designator cannot be found. The ECI mode is not supported by Micro QR Codes.

        :raises: TypeError in case an unknown argument is given.
        """
        self._size = size
        self._border = border
        if _can_be_cast_to_int(version):
            version = int(version)  # type: ignore
            if not 1 <= version <= 40:
                version = None
        elif isinstance(version, str) and version.lower() in ("m1", "m2", "m3", "m4"):
            version = version.lower()
            # Set / change the micro setting otherwise Segno complains about
            # conflicting parameters
            micro = True
        else:
            version = None
        self._version = version
        self._micro = micro
        self._eci = eci
        self._error_correction = ERROR_CORRECTION_DICT.get(error_correction.upper(), DEFAULT_ERROR_CORRECTION)
        self._boost_error = boost_error
        self._encoding = encoding or None
        image_format = image_format.lower()
        self._image_format = image_format if image_format in ("svg", "png") else DEFAULT_IMAGE_FORMAT
        self._colors = dict(
            dark_color=dark_color,
            light_color=light_color,
            finder_dark_color=finder_dark_color,
            finder_light_color=finder_light_color,
            data_dark_color=data_dark_color,
            data_light_color=data_light_color,
            version_dark_color=version_dark_color,
            version_light_color=version_light_color,
            format_dark_color=format_dark_color,
            format_light_color=format_light_color,
            alignment_dark_color=alignment_dark_color,
            alignment_light_color=alignment_light_color,
            timing_dark_color=timing_dark_color,
            timing_light_color=timing_light_color,
            separator_color=separator_color,
            dark_module_color=dark_module_color,
            quiet_zone_color=quiet_zone_color,
        )

    def kw_make(self):
        """Internal method which returns a dict of parameters to create a QR code.

        :rtype: dict
        """
        return dict(
            version=self._version,
            error=self._error_correction,
            micro=self._micro,
            eci=self._eci,
            boost_error=self._boost_error,
            encoding=self._encoding,
        )

    def kw_save(self):
        """Internal method which returns a dict of parameters to save a QR code.

        :rtype: dict
        """
        image_format = self._image_format
        kw = dict(border=self.border, kind=image_format, scale=self._size_as_number())
        # Change the color mapping into the keywords Segno expects
        # (remove the "_color" suffix from the module names)
        kw.update({k.removesuffix("_color"): v for k, v in self.color_mapping().items()})
        if image_format == "svg":
            kw["unit"] = "mm"
            scale = Decimal(kw["scale"]) / 10
            kw["scale"] = scale
        return kw

    def color_mapping(self):
        """Internal method which returns the color mapping.

        Only non-default values are returned.

        :rtype: d
        """
        colors = {k: v for k, v in self._colors.items() if v is not False}
        return colors

    def _size_as_number(self) -> Union[int, float, Decimal]:
        """Returns the size as integer value.

        :rtype: int or float
        """
        size = self._size
        actual_size: Union[int, float, Decimal]
        if _can_be_cast_to_int(size):
            actual_size = int(size)  # type: ignore
            if actual_size < 1:
                actual_size = SIZE_DICT[DEFAULT_MODULE_SIZE]
        elif isinstance(size, (float, Decimal)):
            actual_size = size
            if actual_size < Decimal("0.01"):
                actual_size = SIZE_DICT[DEFAULT_MODULE_SIZE]
        elif isinstance(size, str):
            actual_size = SIZE_DICT.get(size.lower()) or _decimal_from_str(size) or SIZE_DICT[DEFAULT_MODULE_SIZE]
        else:
            actual_size = SIZE_DICT[DEFAULT_MODULE_SIZE]
        return actual_size

    @property
    def size(self):
        return self._size

    @property
    def border(self):
        return self._border

    @property
    def version(self):
        return self._version

    @property
    def image_format(self):
        return self._image_format

    @property
    def error_correction(self):
        return self._error_correction

    @property
    def boost_error(self):
        return self._boost_error

    @property
    def micro(self):
        return self._micro

    @property
    def encoding(self):
        return self._encoding

    @property
    def eci(self):
        return self._eci


def _decimal_from_str(value: str) -> Optional[Decimal]:
    """Returns the size given as a decimal number string (e.g., "2.5"), or None if it is not a valid size."""
    try:
        size = Decimal(value)
    except InvalidOperation:
        return None
    return size if size.is_finite() and size >= Decimal("0.01") else None


def _can_be_cast_to_int(value: Any) -> bool:
    return isinstance(value, int) or (isinstance(value, str) and value.isdigit())


class EventClass(Enum):
    PUBLIC = 1
    PRIVATE = 2
    CONFIDENTIAL = 3


class EventStatus(Enum):
    TENTATIVE = 1
    CONFIRMED = 2
    CANCELLED = 3


class EventTransparency(Enum):
    OPAQUE = 1
    TRANSPARENT = 2


@pydantic_dataclass
class VEvent:
    """
    Data for representing VEVENT for iCalendar (.ics) event.

    Only a subset of https://icalendar.org/iCalendar-RFC-5545/3-6-1-event-component.html is supported.

    Fields meaning:
        * uid: Event identifier
        * summary: This property defines a short summary or subject for the calendar event.
        * start: Start of event
        * end: End of event
        * dtstamp: The property indicates the date/time that the instance of the iCalendar object was created. Defaults to current time in UTC.
        * description: This property provides a more complete description of the calendar component, than that provided by the "SUMMARY" property.
        * organizer: E-mail of organizer
        * status: Status of event
        * location: Location of event
        * geo: This property specifies information related to the global position of event. The property value specifies latitude and longitude, in that order. Whole degrees of latitude shall be represented by a two-digit decimal number ranging from -90 through 90. The longitude represents the location east or west of the prime meridian as a positive or negative real number, respectively (a decimal number ranging from -180 through 180).
        * event_class: Either PUBLIC, PRIVATE or CONFIDENTIAL (see `utils.EventClass`).
        * categories: This property defines the categories for calendar event.
        * transparency: Tell whether the event can have its Time Transparency set to "TRANSPARENT" in order to prevent blocking of the event in searches for busy time.
        * url: This property defines a Uniform Resource Locator (URL) associated with the iCalendar object.
    """

    uid: str
    summary: str
    start: datetime.datetime
    end: datetime.datetime
    dtstamp: Optional[datetime.datetime] = None
    description: Optional[str] = None
    organizer: Optional[str] = None
    status: Optional[EventStatus] = None
    location: Optional[str] = None
    geo: Optional[Tuple[float, float]] = None
    event_class: Optional[EventClass] = None
    categories: Optional[List[str]] = None
    transparency: Optional[EventTransparency] = None
    url: Optional[str] = None

    def make_qr_code_data(self) -> str:
        """\
        Creates a string encoding the event information.

        Only a subset of https://icalendar.org/iCalendar-RFC-5545/3-6-1-event-component.html is supported.
        """

        # Inspired form icalendar: https://github.com/collective/icalendar/
        def fold_icalendar_line(text, limit=75, fold_sep="\r\n "):
            """Make a string folded as defined in RFC5545
            Lines of text SHOULD NOT be longer than 75 octets, excluding the line
            break.  Long content lines SHOULD be split into a multiple line
            representations using a line "folding" technique.  That is, a long
            line can be split between any two characters by inserting a CRLF
            immediately followed by a single linear white-space character (i.e.,
            SPACE or HTAB).
            """
            new_text = ""
            for line in text.split("\n"):
                # Use a fast and simple variant for the common case that line is all ASCII.
                if line.isascii():
                    new_text += fold_sep.join(line[i : i + limit - 1] for i in range(0, len(line), limit - 1))
                else:
                    ret_chars = []
                    byte_count = 0
                    for char in line:
                        char_byte_len = len(char.encode("utf-8"))
                        byte_count += char_byte_len
                        if byte_count >= limit:
                            ret_chars.append(fold_sep)
                            byte_count = char_byte_len
                        ret_chars.append(char)
                    new_text += "".join(ret_chars)
            return new_text

        # Source form icalendar: https://github.com/collective/icalendar/
        def escape_char(text):
            """Format value according to iCalendar TEXT escaping rules."""
            # NOTE: ORDER MATTERS!
            return (
                text.replace(r"\N", "\n")
                .replace("\\", "\\\\")
                .replace(";", r"\;")
                .replace(",", r"\,")
                .replace("\r\n", r"\n")
                .replace("\n", r"\n")
            )

        def is_naive_datetime(t) -> bool:
            return t.tzinfo is None or t.tzinfo.utcoffset(t) is None

        def get_utc_datetime_str(t) -> str:
            return t.astimezone(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")

        def get_datetime_str(t) -> str:
            if is_naive_datetime(t):
                return t.strftime("%Y%m%dT%H%M%S")
            return get_utc_datetime_str(t)

        event_str = f"""BEGIN:VCALENDAR
PRODID:Django QR Code
VERSION:2.0
BEGIN:VEVENT
DTSTAMP:{get_utc_datetime_str(self.dtstamp or datetime.datetime.now(datetime.timezone.utc))}
UID:{self.uid}
DTSTART:{get_datetime_str(self.start)}
DTEND:{get_datetime_str(self.end)}
SUMMARY:{escape_char(self.summary)}"""
        if self.event_class:
            event_str += f"\nCLASS:{self.event_class.name}"
        if self.categories:
            event_str += "\n" + fold_icalendar_line(f"CATEGORIES:{','.join(map(escape_char, self.categories))}")
        if self.transparency:
            event_str += f"\nTRANSP:{self.transparency.name}"
        if self.description:
            event_str += "\n" + fold_icalendar_line(f"DESCRIPTION:{escape_char(self.description)}")
        if self.organizer:
            event_str += f"\nORGANIZER:MAILTO:{self.organizer}"
        if self.status:
            event_str += f"\nSTATUS:{self.status.name}"
        if self.location:
            event_str += "\n" + fold_icalendar_line(f"LOCATION:{escape_char(self.location)}")
        if self.geo:
            event_str += f"\nGEO:{self.geo[0]};{self.geo[1]}"
        if self.url:
            event_str += f"\nURL:{self.url}"
        event_str += "\nEND:VEVENT\nEND:VCALENDAR"
        return event_str


# QR code options required by the EPC QR code specification.
EPC_QR_CODE_ARGS: dict = dict(error_correction="M", boost_error=False, micro=False, encoding="utf-8")


@pydantic_dataclass
class EpcData:
    """
    Data for representing an European Payments Council Quick Response Code (EPC QR Code) version 002.

    You must always use the error correction level "M" (see ``EPC_QR_CODE_ARGS``) and utilizes max. version 13 to fulfill the
        constraints of the EPC QR Code standard.

        .. note::

            Either the ``text`` or ``reference`` must be provided but not both

        .. note::

            Neither the IBAN, BIC, nor remittance reference number or any other
            information is validated (aside from checks regarding the allowed string
            lengths).

    Fields meaning:
        * name: Name of the recipient.
        * iban: International Bank Account Number (IBAN)
        * amount: The amount to transfer. The currency is always Euro, no other currencies are supported.
        * text: Remittance Information (unstructured)
        * reference: Remittance Information (structured)
        * bic: Bank Identifier Code (BIC). Optional, only required for non-EEA countries.
        * purpose: SEPA purpose code.
    """

    name: str
    iban: str
    amount: Union[int, float, Decimal]
    text: Optional[str] = None
    reference: Optional[str] = None
    bic: Optional[str] = None
    purpose: Optional[str] = None

    def make_qr_code_data(self) -> bytes:
        """
        Validates the input and creates the data for an European Payments Council Quick Response Code
        (EPC QR Code) version 002, encoded in UTF-8.

        This is a wrapper for :py:func:`segno.helpers._make_epc_qr_data` with no choice for encoding.

        :rtype: bytes
        """
        return helpers._make_epc_qr_data(**asdict(self), encoding=1)  # type: ignore


# QR code options required by the Swiss QR-bill specification: error correction level "M" and byte mode in UTF-8 without ECI header (the
# coding type of the data gives its encoding), so that the data always fits in a QR code of version 25 (see _SWISS_QR_BILL_MAX_DATA_SIZE).
SWISS_QR_BILL_QR_CODE_ARGS: dict = dict(error_correction="M", boost_error=False, micro=False, encoding="utf-8", eci=False)
# Maximum size of the data of a Swiss QR code, which must fit in a QR code of version 25 with error correction level "M".
_SWISS_QR_BILL_MAX_DATA_SIZE = 997
# IBAN of Switzerland or Liechtenstein: country code, check digits, institution identification (IID) and account number.
_SWISS_IBAN_RE = re.compile(r"(CH|LI)[0-9]{7}[0-9A-Z]{12}")
# A QR-IBAN is identified by an institution identification (QR-IID) in this range.
_QR_IID_RANGE = range(30000, 32000)
_QR_REFERENCE_RE = re.compile(r"[0-9]{1,27}")
_CREDITOR_REFERENCE_RE = re.compile(r"RF[0-9]{2}[0-9A-Z]{1,21}")
_QR_REFERENCE_CHECK_DIGIT_TABLE = (0, 9, 4, 6, 8, 2, 7, 1, 3, 5)
# Unstructured message of a notification Swiss QR-bill that must not be paid, by language, the only one allowed to have an amount of 0.00.
SWISS_QR_BILL_DO_NOT_USE_FOR_PAYMENT_MESSAGES: dict[str, str] = {
    "de": "NICHT ZUR ZAHLUNG VERWENDEN",
    "fr": "NE PAS UTILISER POUR LE PAIEMENT",
    "it": "NON UTILIZZARE PER IL PAGAMENTO",
    "en": "DO NOT USE FOR PAYMENT",
    "rm": "BETG DUVRAR PER IL PAJAMENT",
}


def _normalize_identifier(value: Any) -> str:
    """Removes the spaces of an identifier (e.g., IBAN or payment reference), which are often used for readability, and upper cases it."""
    return str(value).replace(" ", "").upper()


def _mod97(value: str) -> int:
    """Returns the ISO 7064 MOD 97-10 remainder of an alphanumeric value, after converting its letters into numbers (A = 10, ..., Z = 35)."""
    return int("".join(str(int(c, 36)) for c in value)) % 97


def _qr_reference_check_digit(digits: str) -> str:
    """Returns the check digit of a QR reference, computed with the recursive modulo 10 algorithm."""
    carry = 0
    for digit in digits:
        carry = _QR_REFERENCE_CHECK_DIGIT_TABLE[(carry + int(digit)) % 10]
    return str((10 - carry) % 10)


def _check_text(field_name: str, value: Optional[str], max_length: int, required: bool = False) -> None:
    """Checks that a text field of a Swiss QR-bill has a valid length and no line break, since line breaks separate the fields."""
    if not value:
        if required:
            raise ValueError(f"The {field_name} is required.")
        return
    if len(value) > max_length:
        raise ValueError(f"The {field_name} cannot have more than {max_length} characters, got {len(value)}.")
    if "\n" in value or "\r" in value:
        raise ValueError(f"The {field_name} cannot contain line breaks.")


def is_qr_iban(iban: str) -> bool:
    """
    Tells whether the given Swiss or Liechtenstein IBAN is a QR-IBAN, which requires a QR reference (see :py:func:`make_qr_reference`).

    The IBAN itself is not validated, but spaces are ignored.

    :rtype: bool
    """
    iid = _normalize_identifier(iban)[4:9]
    # Not only isdigit(), which accepts non-ASCII digits (e.g., superscripts) that int() rejects.
    return iid.isascii() and iid.isdigit() and int(iid) in _QR_IID_RANGE


def make_qr_reference(base: Union[int, str]) -> str:
    """
    Makes a QR reference (QRR) for a Swiss QR-bill from up to 26 digits, by padding them with leading zeros and appending the check digit
    computed with the recursive modulo 10 algorithm.

    A QR reference can only be used with a QR-IBAN, for a payment in CHF.

    :param base: The digits of the reference (spaces are ignored), which cannot all be zeros.
    :return: The 27 digits of the QR reference.
    :rtype: str
    """
    digits = _normalize_identifier(base)
    if not re.fullmatch(r"[0-9]{1,26}", digits) or not digits.strip("0"):
        raise ValueError(f'The base of a QR reference must be made of 1 to 26 digits, which cannot all be zeros, got "{base}".')
    digits = digits.rjust(26, "0")
    return digits + _qr_reference_check_digit(digits)


def make_creditor_reference(base: str) -> str:
    """
    Makes an ISO 11649 creditor reference (SCOR), e.g., "RF18539007547034", from up to 21 letters or digits.

    Unlike a QR reference, a creditor reference can be used with a regular IBAN in a Swiss QR-bill.

    :param base: The letters and digits of the reference (spaces are ignored).
    :return: The creditor reference, starting with "RF" and its two check digits.
    :rtype: str
    """
    normalized_base = _normalize_identifier(base)
    if not re.fullmatch(r"[0-9A-Z]{1,21}", normalized_base):
        raise ValueError(f'The base of a creditor reference must be made of 1 to 21 letters or digits, got "{base}".')
    check_digits = 98 - _mod97(normalized_base + "RF00")
    return f"RF{check_digits:02d}{normalized_base}"


@pydantic_dataclass
class SwissQrBillAddress:
    """
    Structured address of the creditor or of the debtor of a Swiss QR-bill (see :py:class:`SwissQrBill`).

    The fields are validated according to the Swiss QR-bill specification: a ``ValueError`` is raised when a field is too long, which
    lets you decide how to shorten it. Leading and trailing spaces are removed.

    Fields meaning:
        * name: Name of the person or company, up to 70 characters.
        * street: Street name, up to 70 characters. Optional.
        * building_number: Building number, up to 16 characters. Optional.
        * postal_code: Postal code, up to 16 characters.
        * town: Town, up to 35 characters.
        * country: Two-letter country code (ISO 3166-1 alpha-2). Defaults to "CH".
    """

    name: str
    postal_code: Union[int, str]
    town: str
    street: Optional[str] = None
    building_number: Union[int, str, None] = None
    country: str = "CH"

    def __post_init__(self):
        self.name = self.name.strip()
        self.postal_code = str(self.postal_code).strip()
        self.town = self.town.strip()
        self.street = self.street.strip() if self.street else None
        self.building_number = str(self.building_number).strip() if self.building_number not in (None, "") else None
        self.country = self.country.strip().upper()
        _check_text("name", self.name, 70, required=True)
        _check_text("street", self.street, 70)
        _check_text("building number", self.building_number, 16)
        _check_text("postal code", self.postal_code, 16, required=True)
        _check_text("town", self.town, 35, required=True)
        if not re.fullmatch(r"[A-Z]{2}", self.country):
            raise ValueError(f'The country must be a two-letter country code (ISO 3166-1 alpha-2), got "{self.country}".')

    def _make_qr_code_data_fields(self) -> list[str]:
        return ["S", self.name, self.street or "", str(self.building_number or ""), str(self.postal_code), self.town, self.country]


@pydantic_dataclass
class SwissQrBill:
    """
    Data for representing the Swiss QR code of a Swiss QR-bill (version 2.4 of the Swiss Implementation Guidelines for the QR-bill, which
    is also compliant with version 2.3).

    The fields are validated according to the specification, and a ``ValueError`` is raised when they are not valid (e.g., invalid IBAN,
    wrong reference check digits, text too long, etc.). The allowed character set is not checked. The QR code must be generated with the
    error correction level "M" and without ECI header (see ``SWISS_QR_BILL_QR_CODE_ARGS``), which is what the ``qr_for_swiss_qr_bill``
    and ``qr_url_for_swiss_qr_bill`` template tags do. The Swiss cross required by the specification is drawn in the middle of any QR code
    whose data is the data of a Swiss QR code.

    The type of reference is inferred from the reference and the IBAN:

        * QRR: a QR reference (27 digits, see :py:func:`make_qr_reference`), which is required with a QR-IBAN and only allowed with a
          QR-IBAN, for a payment in CHF.
        * SCOR: an ISO 11649 creditor reference starting with "RF" (see :py:func:`make_creditor_reference`).
        * NON: no reference.

    Fields meaning:
        * account: IBAN or QR-IBAN of the creditor, from Switzerland or Liechtenstein. Spaces are ignored.
        * creditor: Address of the creditor.
        * amount: Amount of the payment, between 0.01 and 999999999.99 with at most two decimal places. Leave it empty to let the
          debtor enter the amount. An amount of 0.00 is only allowed for a notification that must not be paid, whose unstructured
          message must be "DO NOT USE FOR PAYMENT" in one of the languages of the specification (see
          ``SWISS_QR_BILL_DO_NOT_USE_FOR_PAYMENT_MESSAGES``).
        * currency: Currency of the payment, either "CHF" (default) or "EUR".
        * debtor: Address of the debtor. Optional.
        * reference: QR reference or creditor reference. Optional, spaces are ignored.
        * unstructured_message: Additional information for the debtor, up to 140 characters (together with the billing information).
          Optional.
        * billing_information: Coded billing information for automated processing, starting with "//". Optional.
        * alternative_schemes: Parameters of up to two alternative payment schemes, up to 100 characters each. Optional.
    """

    account: str
    creditor: SwissQrBillAddress
    amount: Optional[Decimal] = None
    currency: str = "CHF"
    debtor: Optional[SwissQrBillAddress] = None
    reference: Optional[str] = None
    unstructured_message: Optional[str] = None
    billing_information: Optional[str] = None
    alternative_schemes: Tuple[str, ...] = ()

    def __post_init__(self):
        self.account = _normalize_identifier(self.account)
        if not _SWISS_IBAN_RE.fullmatch(self.account):
            raise ValueError(f'The account must be a Swiss or Liechtenstein IBAN made of 21 characters, got "{self.account}".')
        if _mod97(self.account[4:] + self.account[:4]) != 1:
            raise ValueError(f'The account "{self.account}" is not a valid IBAN (wrong check digits).')

        if self.amount is not None:
            if not Decimal("0") <= self.amount <= Decimal("999999999.99"):
                raise ValueError(f"The amount must be between 0.00 and 999999999.99, got {self.amount}.")
            if self.amount != self.amount.quantize(Decimal("0.01")):
                raise ValueError(f"The amount cannot have more than two decimal places, got {self.amount}.")
            # Turn a negative zero into zero, which would otherwise be written as "-0.00".
            self.amount = abs(self.amount)
            if self.amount == 0 and self.unstructured_message not in SWISS_QR_BILL_DO_NOT_USE_FOR_PAYMENT_MESSAGES.values():
                raise ValueError(
                    'An amount of 0.00 is only allowed for a notification that must not be paid, whose unstructured message must be "DO NOT '
                    f'USE FOR PAYMENT" in one of the languages of the specification: {", ".join(SWISS_QR_BILL_DO_NOT_USE_FOR_PAYMENT_MESSAGES.values())}.'
                )

        self.currency = self.currency.strip().upper()
        if self.currency not in ("CHF", "EUR"):
            raise ValueError(f'The currency must be either "CHF" or "EUR", got "{self.currency}".')

        self.reference = _normalize_identifier(self.reference) if self.reference else None
        if self.reference:
            if self.reference.startswith("RF"):
                if not _CREDITOR_REFERENCE_RE.fullmatch(self.reference) or _mod97(self.reference[4:] + self.reference[:4]) != 1:
                    raise ValueError(f'The reference "{self.reference}" is not a valid creditor reference (ISO 11649).')
            else:
                if not _QR_REFERENCE_RE.fullmatch(self.reference):
                    raise ValueError(f'The reference "{self.reference}" is neither a QR reference nor a creditor reference.')
                self.reference = self.reference.rjust(27, "0")
                if not self.reference.strip("0"):
                    raise ValueError("A QR reference cannot be made of zeros only.")
                if _qr_reference_check_digit(self.reference[:-1]) != self.reference[-1]:
                    raise ValueError(f'The reference "{self.reference}" is not a valid QR reference (wrong check digit).')
        if is_qr_iban(self.account) and self.reference_type != "QRR":
            raise ValueError("A QR-IBAN requires a QR reference.")
        if not is_qr_iban(self.account) and self.reference_type == "QRR":
            raise ValueError("A QR reference requires a QR-IBAN.")
        if self.reference_type == "QRR" and self.currency != "CHF":
            raise ValueError("A QR-IBAN and a QR reference can only be used for a payment in CHF.")

        _check_text("unstructured message", self.unstructured_message, 140)
        _check_text("billing information", self.billing_information, 140)
        if self.billing_information and not self.billing_information.startswith("//"):
            raise ValueError('The billing information must start with "//".')
        if len(self.unstructured_message or "") + len(self.billing_information or "") > 140:
            raise ValueError("The unstructured message and the billing information cannot have more than 140 characters altogether.")
        if len(self.alternative_schemes) > 2:
            raise ValueError("There cannot be more than two alternative schemes.")
        for alternative_scheme in self.alternative_schemes:
            _check_text("alternative scheme", alternative_scheme, 100, required=True)

    @property
    def reference_type(self) -> str:
        """The type of reference: "QRR" (QR reference), "SCOR" (creditor reference) or "NON" (no reference)."""
        if not self.reference:
            return "NON"
        return "SCOR" if self.reference.startswith("RF") else "QRR"

    def make_qr_code_data(self) -> str:
        """
        Creates the data of the Swiss QR code of a Swiss QR-bill.

        :rtype: str
        """
        fields = [
            "SPC",  # QR type: Swiss Payments Code.
            "0200",  # Version 2.
            "1",  # Coding type: UTF-8 restricted to the Latin character set.
            self.account,
            *self.creditor._make_qr_code_data_fields(),
            *[""] * 7,  # Ultimate creditor: reserved for future use.
            f"{self.amount:.2f}" if self.amount is not None else "",
            self.currency,
            *(self.debtor._make_qr_code_data_fields() if self.debtor else [""] * 7),
            self.reference_type,
            self.reference or "",
            self.unstructured_message or "",
            "EPD",  # Trailer: end of payment data.
        ]
        # The trailing optional fields are omitted when they are empty.
        if self.billing_information or self.alternative_schemes:
            fields.append(self.billing_information or "")
        fields.extend(self.alternative_schemes)
        data = "\n".join(fields)
        if len(data.encode("utf-8")) > _SWISS_QR_BILL_MAX_DATA_SIZE:
            raise ValueError(f"The data of a Swiss QR code cannot exceed {_SWISS_QR_BILL_MAX_DATA_SIZE} bytes.")
        return data


class ContactDetail:
    """
    Represents the detail of a contact for MeCARD encoding.

    .. note::
        This is a legacy class. Please use :py:class:`MeCard` instead for new projects.

    Fields meaning:
        * first_name
        * last_name
        * first_name_reading: the sound of the first name.
        * last_name_reading: the sound of the last name.
        * tel: the phone number, it can appear multiple times.
        * tel_av: the video-phone number, it can appear multiple times.
        * email: the email address, it can appear multiple times.
        * memo: notes.
        * birthday: the birth date (Python date).
        * address: the fields divided by commas (,) denote PO box, room number, house number, city, prefecture, zip code and country, in order.
        * url: homepage URL.
        * nickname: display name.
        * org: organization or company name (non-standard,but often recognized, ORG field).
    """

    @validate_call
    def __init__(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        first_name_reading: Optional[str] = None,
        last_name_reading: Optional[str] = None,
        tel: Optional[str] = None,
        tel_av: Optional[str] = None,
        email: Optional[str] = None,
        memo: Optional[str] = None,
        birthday: Optional[datetime.date] = None,
        address: Optional[str] = None,
        url: Optional[str] = None,
        nickname: Optional[str] = None,
        org: Optional[str] = None,
    ):
        self.first_name = first_name
        self.last_name = last_name
        self.first_name_reading = first_name_reading
        self.last_name_reading = last_name_reading
        self.tel = tel
        self.tel_av = tel_av
        self.email = email
        self.memo = memo
        self.birthday = birthday
        self.address = address
        self.url = url
        self.nickname = nickname
        self.org = org

    def make_qr_code_data(self) -> str:
        """
        Make a text for configuring a contact in a phone book. The MeCARD format is used, with an optional, non-standard (but often recognized) ORG field.

        See this archive of the format specifications: https://web.archive.org/web/20160304025131/https://www.nttdocomo.co.jp/english/service/developer/make/content/barcode/function/application/addressbook/index.html

        :return: the MeCARD contact description.
        """

        # See this for an archive of the format specifications:
        # https://web.archive.org/web/20160304025131/https://www.nttdocomo.co.jp/english/service/developer/make/content/barcode/function/application/addressbook/index.html
        contact_text = "MECARD:"
        for template, name_components in (
            ("N:%s;", (self.last_name, self.first_name)),
            ("SOUND:%s;", (self.last_name_reading, self.first_name_reading)),
        ):
            if name := ",".join(filter(None, map(_escape_mecard_special_chars, name_components))):
                contact_text += template % name
        if self.tel:
            contact_text += "TEL:%s;" % _escape_mecard_special_chars(self.tel)
        if self.tel_av:
            contact_text += "TEL-AV:%s;" % _escape_mecard_special_chars(self.tel_av)
        if self.email:
            contact_text += "EMAIL:%s;" % _escape_mecard_special_chars(self.email)
        if self.memo:
            contact_text += "NOTE:%s;" % _escape_mecard_special_chars(self.memo)
        if self.birthday:
            # Format date to YYMMDD.
            contact_text += "BDAY:%s;" % self.birthday.strftime("%Y%m%d")
        if self.address:
            contact_text += "ADR:%s;" % self.address
        if self.url:
            contact_text += "URL:%s;" % _escape_mecard_special_chars(self.url)
        if self.nickname:
            contact_text += "NICKNAME:%s;" % _escape_mecard_special_chars(self.nickname)
        # Not standard, but recognized by several readers.
        if self.org:
            contact_text += "ORG:%s;" % _escape_mecard_special_chars(self.org)
        contact_text += ";"
        return contact_text

    def escaped_value(self, field_name: str):
        return _escape_mecard_special_chars(getattr(self, field_name))


@pydantic_dataclass
class MeCard:
    """Represents the detail of a contact for MeCARD encoding.

    Fields meaning:
        * name: Name. If it contains a comma, the first part is treated as lastname and the second part is treated as forename.
        * reading: Designates a text string to be set as the kana name in the phonebook
        * email: E-mail address. Multiple values are allowed.
        * phone: Phone number. Multiple values are allowed.
        * videophone: Phone number for video calls. Multiple values are allowed.
        * memo: A notice for the contact.
        * nickname: Nickname.
        * birthday: Birthday. If a string is provided, it should encode the date as YYYYMMDD value.
        * url: Homepage. Multiple values are allowed.
        * pobox: P.O. box (address information).
        * roomno: Room number (address information).
        * houseno: House number (address information).
        * city: City (address information).
        * prefecture: Prefecture (address information).
        * zipcode: Zip code (address information).
        * country: Country (address information).
        * org: organization or company name (ORG field, non-standard,but often recognized by readers).
    """

    name: str
    reading: Optional[str] = None
    email: Union[str, Sequence[str], None] = None
    phone: Union[str, Sequence[str], None] = None
    videophone: Union[str, Sequence[str], None] = None
    memo: Optional[str] = None
    nickname: Optional[str] = None
    birthday: Union[str, datetime.date, None] = None
    url: Union[str, Sequence[str], None] = None
    pobox: Optional[str] = None
    roomno: Optional[str] = None
    houseno: Optional[str] = None
    city: Optional[str] = None
    prefecture: Optional[str] = None
    zipcode: Union[int, str, None] = None
    country: Optional[str] = None
    org: Optional[str] = None

    def make_qr_code_data(self) -> str:
        """\
        Creates a string encoding the contact information as MeCARD.

        :rtype: str
        """
        kw = asdict(self)
        if self.zipcode is not None and self.zipcode != "":
            kw["zipcode"] = str(self.zipcode)
        org = kw.pop("org")
        contact_text = helpers.make_mecard_data(**kw)
        # Not standard, but recognized by several readers.
        if org:
            contact_text += f"ORG:{_escape_mecard_special_chars(org)};"
        return contact_text


@pydantic_dataclass
class VCard:
    """Represents the detail of a contact for vCard encoding.

    Creates a QR code which encodes a `vCard <https://en.wikipedia.org/wiki/VCard>`_
    version 3.0.

    Only a subset of available `vCard 3.0 properties <https://tools.ietf.org/html/rfc2426>`
    is supported.

    Fields meaning:
    name: The name. If it contains a semicolon, the first part is treated as lastname and the second part is treated as forename.
    displayname: Common name.
    email: E-mail address. Multiple values are allowed.
    phone: Phone number. Multiple values are allowed.
    fax: Fax number. Multiple values are allowed.
    videophone: Phone number for video calls. Multiple values are allowed.
    memo: A notice for the contact.
    nickname: Nickname.
    birthday: Birthday. If a string is provided, it should encode the date as ``YYYY-MM-DD`` value.
    url: Homepage. Multiple values are allowed.
    pobox: P.O. box (address information).
    street: Street address.
    city: City (address information).
    region: Region (address information).
    zipcode: Zip code (address information).
    country: Country (address information).
    org: Company / organization name.
    lat: Latitude.
    lng: Longitude.
    source: URL where to obtain the vCard.
    rev: Revision of the vCard / last modification date.
    title: Job Title. Multiple values are allowed.
    photo_uri: Photo URI. Multiple values are allowed.
    cellphone: Cell phone number. Multiple values are allowed.
    homephone: Home phone number. Multiple values are allowed.
    workphone: Work phone number. Multiple values are allowed.
    """

    name: str
    displayname: Optional[str] = None
    email: Union[str, Sequence[str], None] = None
    phone: Union[str, Sequence[str], None] = None
    fax: Union[str, Sequence[str], None] = None
    videophone: Union[str, Sequence[str], None] = None
    memo: Optional[str] = None
    nickname: Optional[str] = None
    birthday: Union[str, datetime.date, None] = None
    url: Union[str, Sequence[str], None] = None
    pobox: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    region: Optional[str] = None
    zipcode: Union[int, str, None] = None
    country: Optional[str] = None
    org: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    source: Optional[str] = None
    rev: Union[str, datetime.date, None] = None
    title: Union[str, Sequence[str], None] = None
    photo_uri: Union[str, Sequence[str], None] = None
    cellphone: Union[str, Sequence[str], None] = None
    homephone: Union[str, Sequence[str], None] = None
    workphone: Union[str, Sequence[str], None] = None

    def __post_init__(self):
        if self.displayname is None:
            self.displayname = self.name.replace(" ; ", " ").replace("; ", " ").replace(";", " ")

    def make_qr_code_data(self) -> str:
        """\
        Creates a string encoding the contact information as vCard 3.0.

        Only a subset of available `vCard 3.0 properties <https://tools.ietf.org/html/rfc2426>`
        is supported.

        :rtype: str
        """
        kw = asdict(self)
        if self.zipcode is not None and self.zipcode != "":
            kw["zipcode"] = str(self.zipcode)
        return helpers.make_vcard_data(**kw)


@pydantic_dataclass
class WifiConfig:
    """\
    Represents a WI-FI configuration.

    Fields meaning:
        * ssid: the name of the SSID
        * authentication: the authentication type for the SSID; can be AUTHENTICATION.wep or AUTHENTICATION.wpa, or AUTHENTICATION.nopass for no password. Or, omit for no password.
        * password: the password, ignored if "authentication" is 'nopass' (in which case it may be omitted).
        * hidden: tells whether the SSID is hidden or not; can be True or False.
    """

    AUTHENTICATION = namedtuple("AUTHENTICATION", "nopass WEP WPA")._make(range(3))  # type: ignore
    AUTHENTICATION_CHOICES = ((AUTHENTICATION.nopass, "nopass"), (AUTHENTICATION.WEP, "WEP"), (AUTHENTICATION.WPA, "WPA"))

    ssid: str = ""
    authentication: int = AUTHENTICATION.nopass
    password: str = ""
    hidden: bool = False

    def make_qr_code_data(self) -> str:
        """
        Make a text for configuring a Wi-Fi connexion. The syntax is inspired by the MeCARD format used for contacts.

        :return: the WI-FI configuration text that can be translated to a QR code.
        :rtype: str
        """

        wifi_config = "WIFI:"
        if self.ssid:
            wifi_config += "S:%s;" % _escape_mecard_special_chars(self.ssid)
        if self.authentication:
            wifi_config += "T:%s;" % WifiConfig.AUTHENTICATION_CHOICES[self.authentication][1]
        if self.password:
            wifi_config += "P:%s;" % _escape_mecard_special_chars(self.password)
        if self.hidden:
            wifi_config += "H:true;"
        wifi_config += ";"
        return wifi_config


@pydantic_dataclass
class Coordinates:
    """\
    Represents a set of coordinates with an optional altitude.

    Fields meaning:
        * latitude: The latitude.
        * longitude: The longitude.
        * altitude: The optional altitude.
    """

    latitude: float
    longitude: float
    altitude: Optional[Union[int, float]] = None

    def __str__(self) -> str:
        if self.altitude:
            return f"latitude: {self.latitude}, longitude: {self.longitude}, altitude: {self.altitude}"
        return f"latitude: {self.latitude}, longitude: {self.longitude}"

    def float_to_str(self, f):
        return f"{f:.8f}".rstrip("0")

    def _coordinates_text(self) -> str:
        coordinates = [self.latitude, self.longitude] + ([self.altitude] if self.altitude else [])
        return ",".join(map(self.float_to_str, coordinates))

    def make_geolocation_text(self) -> str:
        return f"geo:{self._coordinates_text()}"

    def make_google_maps_text(self) -> str:
        return f"https://maps.google.com/local?q={self._coordinates_text()}"


def make_tel_text(phone_number: Any) -> str:
    return "tel:%s" % phone_number


def make_sms_text(phone_number: Any) -> str:
    return "sms:%s" % phone_number


def make_youtube_text(video_id: str) -> str:
    return f"https://www.youtube.com/watch/?v={escape(video_id)}"


def make_google_play_text(package_id: str) -> str:
    return f"https://play.google.com/store/apps/details?id={escape(package_id)}"


@pydantic_dataclass
class Email:
    """Represents the data of an e-mail.

    Fields meaning:
        * to: The email address (recipient). Multiple values are allowed.
        * cc: The carbon copy recipient. Multiple values are allowed.
        * bcc: The blind carbon copy recipient. Multiple values are allowed.
        * subject: The subject.
        * body: The message body.
    """

    to: Union[str, Sequence[str]]
    cc: Union[str, Sequence[str], None] = None
    bcc: Union[str, Sequence[str], None] = None
    subject: Optional[str] = None
    body: Optional[str] = None

    def make_qr_code_data(self) -> str:
        """\
        Creates either a simple "mailto:" URL or complete e-mail message with
        (blind) carbon copies and a subject and a body.

        :rtype: str
        """
        return helpers.make_make_email_data(**asdict(self))


@validate_call
def _escape_mecard_special_chars(string_to_escape: Optional[str]) -> Optional[str]:
    if not string_to_escape:
        return string_to_escape
    special_chars = ["\\", '"', ";", ",", ":"]
    for sc in special_chars:
        string_to_escape = string_to_escape.replace(sc, "\\%s" % sc)
    return string_to_escape
