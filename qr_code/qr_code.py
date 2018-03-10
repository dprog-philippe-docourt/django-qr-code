"""Utility classes and functions for generating QR code. This module depends on the qrcode python library."""

import base64
import urllib.parse
from collections import namedtuple
from datetime import datetime
from io import BytesIO

import xml.etree.ElementTree as ET

from django.conf import settings
from django.core.signing import Signer
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.html import escape
from django.utils.safestring import mark_safe

from qr_code.qrcode_image import SvgPathImage, PilImageOrFallback, get_supported_image_format, SVG_FORMAT_NAME, \
    PNG_FORMAT_NAME

QR_CODE_GENERATION_VERSION_DATE = datetime(year=2017, month=8, day=7, hour=0)

SIZE_DICT = {'t': 6, 's': 12, 'm': 18, 'l': 30, 'h': 48}

DEFAULT_MODULE_SIZE = 'M'
DEFAULT_BORDER_SIZE = 4
DEFAULT_VERSION = None
DEFAULT_IMAGE_FORMAT = SVG_FORMAT_NAME
DEFAULT_CACHE_ENABLED = True


class SvgEmbeddedInHtmlImage(SvgPathImage):
    def _write(self, stream):
        self._img.append(self.make_path())
        ET.ElementTree(self._img).write(stream, encoding="UTF-8", xml_declaration=False, default_namespace=None,
                                        method='html')


def _escape_mecard_special_chars_in_object_fields(obj, keys):
    for key in keys:
        if hasattr(obj, key):
            setattr(obj, 'escaped_%s' % key, _escape_mecard_special_chars(getattr(obj, key)))


class ContactDetail(object):
    """
    Represents the detail of a contact.
    """
    first_name = None
    last_name = None
    first_name_reading = None
    last_name_reading = None
    tel = None
    tel_av = None
    email = None
    memo = None
    birthday = None
    address = None
    url = None
    nickname = None
    org = None

    def __init__(self, **kwargs):
        """
        The contact details support the following fields.
        :param kwargs:
            The contact dictionary gives the following parameters:
            * first_name
            * last_name
            * first_name_reading: the sound of the first name.
            * last_name_reading: the sound of the last name.
            * tel: the phone number, it can appear multiple times.
            * tel-av: the video-phone number, it can appear multiple times.
            * email: the email address, it can appear multiple times.
            * memo: notes.
            * birthday: the birth date (Python date).
            * address: the fields divided by commas (,) denote PO box, room number, house number, city, prefecture, zip code and country, in order.
            * url: homepage URL.
            * nickname: display name.
            * org: organization or company name (non-standard,but often recognized, ORG field).
        """
        self.first_name = kwargs.get('first_name')
        self.last_name = kwargs.get('last_name')
        self.first_name_reading = kwargs.get('first_name_reading')
        self.last_name_reading = kwargs.get('last_name_reading')
        self.tel = kwargs.get('tel')
        self.tel_av = kwargs.get('tel_av')
        self.email = kwargs.get('email')
        self.memo = kwargs.get('memo')
        self.birthday = kwargs.get('birthday')
        self.address = kwargs.get('address')
        self.url = kwargs.get('url')
        self.nickname = kwargs.get('nickname')
        self.org = kwargs.get('org')

    def make_contact_text(self):
        """
        Make a text for configuring a contact in a phone book. The MeCARD format is used, with an optional, non-standard (but often recognized) ORG field.

        See this archive of the format specifications: https://web.archive.org/web/20160304025131/https://www.nttdocomo.co.jp/english/service/developer/make/content/barcode/function/application/addressbook/index.html

        The contact dictionary gives the following parameters:
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
        :return: the MeCARD contact description.
        """

        _escape_mecard_special_chars_in_object_fields(self, ('first_name', 'last_name', 'first_name_reading', 'last_name_reading', 'tel', 'tel_av', 'email', 'memo', 'nickname', 'org'))

        # See this for an archive of the format specifications:
        # https://web.archive.org/web/20160304025131/https://www.nttdocomo.co.jp/english/service/developer/make/content/barcode/function/application/addressbook/index.html
        contact_text = 'MECARD:'
        if self.first_name and self.last_name:
            name = '%s,%s' % (self.last_name, self.first_name)
        else:
            name = self.first_name if self.first_name else self.last_name
        if name:
            contact_text += 'N:%s;' % name
        if self.first_name_reading and self.last_name_reading:
            name_reading = '%s,%s' % (self.escaped_last_name_reading, self.escaped_first_name_reading)
        else:
            name_reading = self.escaped_first_name_reading if self.first_name_reading else self.escaped_last_name_reading
        if name_reading:
            contact_text += 'SOUND:%s;' % name_reading
        if self.tel:
            contact_text += 'TEL:%s;' % self.escaped_tel
        if self.tel_av:
            contact_text += 'TEL-AV:%s;' % self.escaped_tel_av
        if self.email:
            contact_text += 'EMAIL:%s;' % self.escaped_email
        if self.memo:
            contact_text += 'NOTE:%s;' % self.escaped_memo
        if self.birthday:
            # Format date to YYMMDD.
            contact_text += 'BDAY:%s;' % self.birthday.strftime('%Y%m%d')
        if self.address:
            contact_text += 'ADR:%s;' % self.address
        if self.url:
            contact_text += 'URL:%s;' % self.url
        if self.nickname:
            contact_text += 'NICKNAME:%s;' % self.escaped_nickname
        # Not standard, but recognized by several readers.
        if self.org:
            contact_text += 'ORG:%s;' % self.escaped_org
        contact_text += ';'
        return contact_text


class WifiConfig(object):
    """
    Represents the configurion for a Wi-Fi connexion.
    """
    AUTHENTICATION = namedtuple('AUTHENTICATION', 'nopass WEP WPA')._make(range(3))
    AUTHENTICATION_CHOICES = ((AUTHENTICATION.nopass, 'nopass'), (AUTHENTICATION.WEP, 'WEP'), (AUTHENTICATION.WPA, 'WPA'))
    ssid = None
    authentication = AUTHENTICATION.nopass
    password = None
    hidden = False

    def __init__(self, **kwargs):
        """
        The wifi configuration recognizes the following parameters.
        :param kwargs:
            * ssid: the name of the SSID
            * authentication: the authentication type for the SSID; can be AUTHENTICATION.wep or AUTHENTICATION.wpa, or AUTHENTICATION.nopass for no password. Or, omit for no password.
            * password: the password, ignored if "authentsication" is 'nopass' (in which case it may be omitted).
            * hidden: tells whether the SSID is hidden or not; can be True or False.
        """
        self.ssid = kwargs.get('ssid')
        self.authentication = kwargs.get('authentication', WifiConfig.AUTHENTICATION.nopass)
        self.password = kwargs.get('password')
        self.hidden = kwargs.get('hidden')

    def make_wifi_text(self):
        """
        Make a text for configuring a Wi-Fi connexion. The syntax is inspired by the MeCARD format used for contacts.

        :return: the WIFI configuration text that can be translated to a QR code.
        """

        _escape_mecard_special_chars_in_object_fields(self, ('ssid', 'password'))

        wifi_config = 'WIFI:'
        if self.ssid:
            wifi_config += 'S:%s;' % self.escaped_ssid
        if self.authentication:
            wifi_config += 'T:%s;' % WifiConfig.AUTHENTICATION_CHOICES[self.authentication][1]
        if self.password:
            wifi_config += 'P:%s;' % self.escaped_password
        if self.hidden:
            wifi_config += 'H:%s;' % str(self.hidden).lower()
        return wifi_config


def get_url_protection_options(user=None):
    defaults = {
        'TOKEN_LENGTH': 20,
        'SIGNING_KEY': settings.SECRET_KEY,
        'SIGNING_SALT': 'qr_code_url_protection_salt',
        'ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER': False,
        'ALLOWS_EXTERNAL_REQUESTS': False
    }
    options = defaults
    if hasattr(settings, 'QR_CODE_URL_PROTECTION') and isinstance(settings.QR_CODE_URL_PROTECTION, dict):
        options.update(settings.QR_CODE_URL_PROTECTION)
        # Evaluate the callable if required.
        if callable(options['ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER']):
            options['ALLOWS_EXTERNAL_REQUESTS'] = user and options['ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER'](user)
        elif options['ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER'] and user:
            if callable(user.is_authenticated):
                # Django version < 1.10
                options['ALLOWS_EXTERNAL_REQUESTS'] = user.is_authenticated()
            else:
                # Django version >= 1.10
                options['ALLOWS_EXTERNAL_REQUESTS'] = user.is_authenticated
        else:
            options['ALLOWS_EXTERNAL_REQUESTS'] = False

    return options


def _make_random_token():
    url_protection_options = get_url_protection_options()
    return get_random_string(url_protection_options['TOKEN_LENGTH'])


RANDOM_TOKEN = _make_random_token()


def make_qr_code_image(text, image_factory, size=DEFAULT_MODULE_SIZE, border=DEFAULT_BORDER_SIZE, version=DEFAULT_VERSION):
    """
    Generates an image object (from the qrcode library) representing the QR code for the given text.

    Any invalid argument is silently converted into the default value for that argument.

    See the function :func:`~qr_code.qr_code.make_embedded_qr_code` for behavior and details about parameters meaning.
    """

    if isinstance(version, int) or (isinstance(version, str) and version.isdigit()):
        actual_version = int(version)
        if actual_version < 1 or actual_version > 40:
            actual_version = 0
    else:
        actual_version = 0
    if isinstance(size, int) or (isinstance(size, str) and size.isdigit()):
        actual_size = int(size)
        if actual_size < 1:
            actual_size = SIZE_DICT['m']
    else:
        if not size or not size.lower() in SIZE_DICT:
            size = 'm'
        actual_size = SIZE_DICT[size.lower()]
    import qrcode
    qr = qrcode.QRCode(
        version=actual_version if actual_version != 0 else 1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=actual_size,
        border=border
    )
    qr.add_data(text)
    if actual_version == 0:
        qr.make(fit=True)
    return qr.make_image(image_factory=image_factory)


def make_email_text(email):
    return 'mailto:%s' % email


def make_tel_text(phone_number):
    return 'tel:%s' % phone_number


def make_sms_text(phone_number):
    return 'sms:%s' % phone_number


def make_geolocation_text(latitude, longitude, altitude):
    return 'geo:%s,%s,%s' % (escape(latitude), escape(longitude), escape(altitude))


def make_google_maps_text(latitude, longitude):
    return 'https://maps.google.com/local?q=%s,%s' % (escape(latitude), escape(longitude))


def make_youtube_text(video_id):
    return 'https://www.youtube.com/watch/?v=%s' % escape(video_id)


def make_google_play_text(package_id):
    return 'https://play.google.com/store/apps/details?id=%s' % escape(package_id)


def _escape_mecard_special_chars(string_to_escape):
    if not string_to_escape:
        return string_to_escape
    special_chars = ['\\', '"', ';', ',']
    for sc in special_chars:
        string_to_escape = string_to_escape.replace(sc, '\\%s' % sc)
    return string_to_escape


def make_qr_code(embedded, text, size=DEFAULT_MODULE_SIZE, border=DEFAULT_BORDER_SIZE, version=DEFAULT_VERSION, image_format=DEFAULT_IMAGE_FORMAT):
    if embedded is True:
        return make_embedded_qr_code(text, size=size, border=border, version=version, image_format=image_format)
    return make_qr_code_url(text, size=size, border=border, version=version, image_format=image_format)


def make_embedded_qr_code(text, size=DEFAULT_MODULE_SIZE, border=DEFAULT_BORDER_SIZE, version=DEFAULT_VERSION, image_format=DEFAULT_IMAGE_FORMAT):
    """
    Generates a <svg> or <img> tag representing the QR code for the given text. This tag can be embedded into an
    HTML document.

    Any invalid argument is silently converted into the default value for that argument.

    The size parameter gives the size of each module of the QR code matrix. It can be either a positive integer or one of the following letters:
        * t or T: tiny (value: 6)
        * s or S: small (value: 12)
        * m or M: medium (value: 18)
        * l or L: large (value: 30)
        * h or H: huge (value: 48)

    For PNG image format the size unit is in pixels, while the unit is 0.1 mm for SVG format.

    The version parameter is an integer from 1 to 40 that controls the size of the QR code matrix. Set to None to determine
    this automatically. The smallest, version 1, is a 21 x 21 matrix. The biggest, version 40, is 177 x 177 matrix.
    The size grows by 4 modules/side.

    Keyword arguments:
        * text (str): the text to render as a QR code
        * size (int, str): the size of the QR code as an integer or a string. Default is *'m'*.
        * version (int): the version of the QR code gives the size of the matrix. Default is *1*.
        * image_format (str): the graphics format used to render the QR code. It can be either *'svg'* or *'png'*. Default is *'svg'*.
    """
    image_format = get_supported_image_format(image_format)
    img = make_qr_code_image(text, SvgEmbeddedInHtmlImage if image_format == SVG_FORMAT_NAME else PilImageOrFallback, size=size, border=border, version=version)
    stream = BytesIO()
    if image_format == SVG_FORMAT_NAME:
        img.save(stream, kind=SVG_FORMAT_NAME.upper())
        html_fragment = (str(stream.getvalue(), 'utf-8'))
    else:
        img.save(stream, format=PNG_FORMAT_NAME.upper())
        html_fragment = '<img src="data:image/png;base64, %s" alt="%s"' % (
        str(base64.b64encode(stream.getvalue()), encoding='ascii'), escape(text))
    return mark_safe(html_fragment)


def make_qr_code_url(text, size=DEFAULT_MODULE_SIZE, border=DEFAULT_BORDER_SIZE, version=DEFAULT_VERSION, image_format=DEFAULT_IMAGE_FORMAT, cache_enabled=DEFAULT_CACHE_ENABLED, include_url_protection_token=True):
    """
    Build an URL to a view that handle serving QR code image from the given parameters.
    Any invalid argument related to the size or the format of the image is silently converted into the default value for that argument.

    See the function :func:`~qr_code.qr_code.make_embedded_qr_code` for behavior and details about parameters meaning.

    The parameter *cache_enabled (bool)* allows to skip caching the QR code (when set to *False*) when caching has been enabled.

    The parameter *include_url_protection_token (bool)* tells whether the random token for protecting the URL against external requests is added to the returned URL. It defaults to *True*.
    """
    encoded_text = str(base64.urlsafe_b64encode(bytes(text, encoding='utf-8')), encoding='utf-8')

    image_format = get_supported_image_format(image_format)
    params = dict(text=encoded_text, size=size, border=border, version=version, image_format=image_format, cache_enabled=cache_enabled)
    path = reverse('qr_code:serve_qr_code_image')

    if include_url_protection_token:
        # Generate token to handle view protection. The token is added to the query arguments. It does not replace
        # existing plain text query arguments in order to allow usage of the URL as an API (without token since external
        # users cannot generate the signed token!).
        token = get_qr_url_protection_signed_token(size, border, version, image_format)
        params['token'] = token

    url = '%s?%s' % (path, urllib.parse.urlencode(params))
    return mark_safe(url)


def get_qr_url_protection_signed_token(size, border, version, image_format):
    """Generate a signed token to handle view protection."""
    url_protection_options = get_url_protection_options()
    signer = Signer(key=url_protection_options['SIGNING_KEY'], salt=url_protection_options['SIGNING_SALT'])
    token = signer.sign(get_qr_url_protection_token(size, border, version, image_format, RANDOM_TOKEN))
    return token


def get_qr_url_protection_token(size, border, version, image_format, random_token):
    """
    Generate a random token for the QR code image.

    The token contains image attributes so that a user cannot use a token provided somewhere on a website to
    generate bigger QR codes. The random_token part ensures that the signed token is not predictable.
    """
    return '.'.join(list(map(str, (size, border, version, image_format, random_token))))


def qr_code_etag(request):
    return '"%s:%s:version_%s"' % (request.path, request.GET.urlencode(), QR_CODE_GENERATION_VERSION_DATE.isoformat())


def qr_code_last_modified(request):
    return QR_CODE_GENERATION_VERSION_DATE
