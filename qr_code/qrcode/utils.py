"""Utility classes and functions for configuring and setting up the content and the look of a QR code."""
import decimal
from collections import namedtuple
from django.utils.html import escape
from qr_code.qrcode.constants import DEFAULT_MODULE_SIZE, SIZE_DICT, \
    DEFAULT_ERROR_CORRECTION, DEFAULT_IMAGE_FORMAT


class QRCodeOptions:
    """
    Represents the options used to create and draw a QR code.
    """
    def __init__(self, *, size=DEFAULT_MODULE_SIZE, border=4, version=None,
                 image_format='svg', error_correction=DEFAULT_ERROR_CORRECTION,
                 micro=False, dark_color='#000', light_color='#fff',
                 finder_dark_color=False, finder_light_color=False,
                 data_dark_color=False, data_light_color=False,
                 version_dark_color=False, version_light_color=False,
                 format_dark_color=False, format_light_color=False,
                 alignment_dark_color=False, alignment_light_color=False,
                 timing_dark_color=False, timing_light_color=False,
                 separator_color=False, dark_module_color=False, 
                 quiet_zone_color=False):
        """
        :param size: The size of the QR code as an integer or a string.
                    Default is *'m'*.
        :type: str or int
        :param int border: The size of the border (blank space around the code).
        :param int version: The version of the QR code gives the size of the matrix.
                Default is *None* which mean automatic in order to avoid data overflow.
        :param str image_format: The graphics format used to render the QR code.
                It can be either *'svg'* or *'png'*. Default is *'svg'*.
        :param str error_correction: How much error correction that might be required
                to read the code. It can be either *'L'*, *'M'*, *'Q'*, or *'H'*. Default is *'M'*.
        :param bool micro: Indicates if a Micro QR Code should be created. Default: False
        :param dark_color: Color of the dark modules (default: black). The
                color can be provided as ``(R, G, B)`` tuple, as hexadecimal
                format (``#RGB``, ``#RRGGBB`` ``RRGGBBAA``), or web color
                name (i.e. ``red``).
        :param light_color: Color of the light modules (default: white).
                See `color` for valid values. If light is set to ``None`` the
                light modules will be transparent.
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

        The *size* parameter gives the size of each module of the QR code matrix. It can be either a positive integer or one of the following letters:
            * t or T: tiny (value: 6)
            * s or S: small (value: 12)
            * m or M: medium (value: 18)
            * l or L: large (value: 30)
            * h or H: huge (value: 48)

        For PNG image format the size unit is in pixels, while the unit is 0.1 mm for SVG format.

        The *border* parameter controls how many modules thick the border should be (blank space around the code).
        The default is 4, which is the minimum according to the specs.

        The *version* parameter is an integer from 1 to 40 that controls the size of the QR code matrix. Set to None to determine
        this automatically. The smallest, version 1, is a 21 x 21 matrix. The biggest, version 40, is 177 x 177 matrix.
        The size grows by 4 modules/side.

        There are 4 error correction levels used for QR codes, with each one adding different amounts of "backup" data
        depending on how much damage the QR code is expected to suffer in its intended environment, and hence how much
        error correction may be required. The correction level can be configured with the *error_correction* parameter as follow:
            * l or L: error correction level L – up to 7% damage
            * m or M: error correction level M – up to 15% damage
            * q or Q: error correction level Q – up to 25% damage
            * h or H: error correction level H – up to 30% damage
        :raises: TypeError in case an unknown argument is given.
        """
        self._size = size
        self._border = border
        if _can_be_cast_to_int(version):
            version = int(version)
            if not 1 <= version <= 40:
                version = None
        elif version in ('m1', 'm2', 'm3', 'm4', 'M1', 'M2', 'M3', 'M4'):
            version = version.lower()
            # Set / change the micro setting otherwise Segno complains about
            # conflicting parameters
            micro = True
        else:
            version = None
        self._version = version
        if not isinstance(micro, bool):
            micro = micro == 'True'
        self._micro = micro
        try:
            error = error_correction.lower()
            self._error_correction = error if error in ('l', 'm', 'q', 'h') else DEFAULT_ERROR_CORRECTION
        except AttributeError:
            self._error_correction = DEFAULT_ERROR_CORRECTION
        try:
            image_format = image_format.lower()
            self._image_format = image_format if image_format in ('svg', 'png') else DEFAULT_IMAGE_FORMAT
        except AttributeError:
            self._image_format = DEFAULT_IMAGE_FORMAT
        self._colors = dict(dark_color=dark_color, light_color=light_color,
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
                            quiet_zone_color=quiet_zone_color)

    def kw_make(self):
        """Internal method which returns a dict of parameters to create a QR code.

        :rtype: dict
        """
        return dict(version=self._version, error=self._error_correction,
                    micro=self._micro)

    def kw_save(self):
        """Internal method which returns a dict of parameters to save a QR code.

        :rtype: dict
        """
        image_format = self._image_format
        kw = dict(kind=image_format, scale=self._size_as_int())
        # Change the color mapping into the keywords Segno expects
        # (remove the "_color" suffix from the module names)
        kw.update({k[:-6]: v for k, v in self.color_mapping().items()})
        if image_format == 'svg':
            kw['unit'] = 'mm'
            scale = decimal.Decimal(kw['scale']) / 10
            kw['scale'] = scale
        return kw

    def color_mapping(self):
        """Internal method which returns the color mapping.

        Only non-default values are returned.

        :rtype: dict
        """
        colors = {k: v for k, v in self._colors.items() if v is not False}
        # Remove common default "dark" and "light" values
        if colors.get('dark_color') in ('#000', '#000000', 'black'):
            del colors['dark_color']
        if colors.get('light_color') in ('#fff', '#FFF', '#ffffff', '#FFFFFF', 'white'):
            del colors['light_color']
        return colors

    def _size_as_int(self):
        """Returns the size as integer value.

        :rtype: int
        """
        size = self._size
        if _can_be_cast_to_int(size):
            actual_size = int(size)
            if actual_size < 1:
                actual_size = SIZE_DICT[DEFAULT_MODULE_SIZE]
        elif isinstance(size, str):
            actual_size = SIZE_DICT.get(size.lower(), DEFAULT_MODULE_SIZE)
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
    def micro(self):
        return self._micro


def _can_be_cast_to_int(value):
    return isinstance(value, int) or (isinstance(value, str) and value.isdigit())


class ContactDetail:
    """
    Represents the detail of a contact.

    The following fields are provided:
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

    def make_qr_code_text(self):
        """
        Make a text for configuring a contact in a phone book. The MeCARD format is used, with an optional, non-standard (but often recognized) ORG field.

        See this archive of the format specifications: https://web.archive.org/web/20160304025131/https://www.nttdocomo.co.jp/english/service/developer/make/content/barcode/function/application/addressbook/index.html

        :return: the MeCARD contact description.
        """

        _escape_mecard_special_chars_in_object_fields(self, ('first_name', 'last_name', 'first_name_reading', 'last_name_reading', 'tel', 'tel_av', 'email', 'memo', 'url', 'nickname', 'org'))

        # See this for an archive of the format specifications:
        # https://web.archive.org/web/20160304025131/https://www.nttdocomo.co.jp/english/service/developer/make/content/barcode/function/application/addressbook/index.html
        contact_text = 'MECARD:'
        for name_components_pair in (('N:%s;', (self.escaped_last_name, self.escaped_first_name)), ('SOUND:%s;', (self.escaped_last_name_reading, self.escaped_first_name_reading))):
            if name_components_pair[1][0] and name_components_pair[1][1]:
                name = '%s,%s' % name_components_pair[1]
            else:
                name = name_components_pair[1][0] if name_components_pair[1][0] else name_components_pair[1][1]
            if name:
                contact_text += name_components_pair[0] % name
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
            contact_text += 'URL:%s;' % self.escaped_url
        if self.nickname:
            contact_text += 'NICKNAME:%s;' % self.escaped_nickname
        # Not standard, but recognized by several readers.
        if self.org:
            contact_text += 'ORG:%s;' % self.escaped_org
        contact_text += ';'
        return contact_text


class WifiConfig(object):
    """
    Represents the configuration of a Wi-Fi connexion.

    The following fields are provided:
        * ssid: the name of the SSID
        * authentication: the authentication type for the SSID; can be AUTHENTICATION.wep or AUTHENTICATION.wpa, or AUTHENTICATION.nopass for no password. Or, omit for no password.
        * password: the password, ignored if "authentsication" is 'nopass' (in which case it may be omitted).
        * hidden: tells whether the SSID is hidden or not; can be True or False.
    """
    AUTHENTICATION = namedtuple('AUTHENTICATION', 'nopass WEP WPA')._make(range(3))
    AUTHENTICATION_CHOICES = ((AUTHENTICATION.nopass, 'nopass'), (AUTHENTICATION.WEP, 'WEP'), (AUTHENTICATION.WPA, 'WPA'))
    ssid = None
    authentication = AUTHENTICATION.nopass
    password = None
    hidden = False

    def __init__(self, **kwargs):
        self.ssid = kwargs.get('ssid')
        self.authentication = kwargs.get('authentication', WifiConfig.AUTHENTICATION.nopass)
        self.password = kwargs.get('password')
        self.hidden = kwargs.get('hidden')

    def make_qr_code_text(self):
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
        wifi_config += ';'
        return wifi_config


class Coordinates:
    def __init__(self, latitude, longitude, altitude=None):
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude

    def __str__(self):
        if self.altitude:
            return 'latitude: %s, longitude: %s, altitude: %s' % (self.latitude, self.longitude, self.altitude)
        return 'latitude: %s, longitude: %s' % (self.latitude, self.longitude)

    def make_geolocation_text(coordinates):
        return 'geo:%s,%s,%s' % (
            escape(coordinates.latitude), escape(coordinates.longitude), escape(coordinates.altitude))

    def make_google_maps_text(coordinates):
        return 'https://maps.google.com/local?q=%s,%s' % (
            escape(coordinates.latitude), escape(coordinates.longitude))


def make_email_text(email):
    return 'mailto:%s' % email


def make_tel_text(phone_number):
    return 'tel:%s' % phone_number


def make_sms_text(phone_number):
    return 'sms:%s' % phone_number


def make_youtube_text(video_id):
    return 'https://www.youtube.com/watch/?v=%s' % escape(video_id)


def make_google_play_text(package_id):
    return 'https://play.google.com/store/apps/details?id=%s' % escape(package_id)


def _escape_mecard_special_chars(string_to_escape):
    if not string_to_escape:
        return string_to_escape
    special_chars = ['\\', '"', ';', ',', ':']
    for sc in special_chars:
        string_to_escape = string_to_escape.replace(sc, '\\%s' % sc)
    return string_to_escape


def _escape_mecard_special_chars_in_object_fields(obj, keys):
    for key in keys:
        if hasattr(obj, key):
            setattr(obj, 'escaped_%s' % key, _escape_mecard_special_chars(getattr(obj, key)))
