import base64
import urllib.parse
from collections import Mapping

from django.conf import settings
from django.core.signing import Signer
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.safestring import mark_safe

from qr_code.qrcode.constants import QR_CODE_GENERATION_VERSION_DATE, DEFAULT_CACHE_ENABLED, \
    ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER
from qr_code.qrcode.utils import QRCodeOptions


def _get_default_url_protection_options():
    return {
        'TOKEN_LENGTH': 20,
        'SIGNING_KEY': settings.SECRET_KEY,
        'SIGNING_SALT': 'qr_code_url_protection_salt',
        ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER: False,
        'ALLOWS_EXTERNAL_REQUESTS': False
    }


def _get_url_protection_settings():
    if hasattr(settings, 'QR_CODE_URL_PROTECTION') and isinstance(settings.QR_CODE_URL_PROTECTION, Mapping):
        return settings.QR_CODE_URL_PROTECTION
    return None


def _options_allow_external_request(url_protection_options, user):
    # Evaluate the callable if required.
    if callable(url_protection_options[ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER]):
        allows_external_request = user and url_protection_options[ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER](user)
    elif url_protection_options[ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER] is True and user:
        allows_external_request = user.is_authenticated
    else:
        allows_external_request = False
    return allows_external_request


def get_url_protection_options(user=None):
    options = _get_default_url_protection_options()
    settings_options = _get_url_protection_settings()
    if settings_options is not None:
        options.update(settings.QR_CODE_URL_PROTECTION)
        options['ALLOWS_EXTERNAL_REQUESTS'] = _options_allow_external_request(options, user)
    return options


def _make_random_token():
    url_protection_options = get_url_protection_options()
    return get_random_string(url_protection_options['TOKEN_LENGTH'])


_RANDOM_TOKEN = _make_random_token()


def get_qr_url_protection_signed_token(qr_code_options):
    """Generate a signed token to handle view protection."""
    url_protection_options = get_url_protection_options()
    signer = Signer(key=url_protection_options['SIGNING_KEY'], salt=url_protection_options['SIGNING_SALT'])
    token = signer.sign(get_qr_url_protection_token(qr_code_options, _RANDOM_TOKEN))
    return token


def get_qr_url_protection_token(qr_code_options, random_token):
    """
    Generate a random token for the QR code image.

    The token contains image attributes so that a user cannot use a token provided somewhere on a website to
    generate bigger QR codes. The random_token part ensures that the signed token is not predictable.
    """
    return '.'.join(list(map(str, (qr_code_options.size, qr_code_options.border, qr_code_options.version or '', qr_code_options.image_format, qr_code_options.error_correction, random_token))))


def qr_code_etag(request):
    return '"%s:%s:version_%s"' % (request.path, request.GET.urlencode(), QR_CODE_GENERATION_VERSION_DATE.isoformat())


def qr_code_last_modified(request):
    return QR_CODE_GENERATION_VERSION_DATE


def make_qr_code_url(text, qr_code_options=QRCodeOptions(), cache_enabled=DEFAULT_CACHE_ENABLED, include_url_protection_token=True):
    """
    Build an URL to a view that handle serving QR code image from the given parameters. Any invalid argument related
    to the size or the format of the image is silently converted into the default value for that argument.

    The parameter *cache_enabled (bool)* allows to skip caching the QR code (when set to *False*) when caching has
    been enabled.

    The parameter *include_url_protection_token (bool)* tells whether the random token for protecting the URL against
    external requests is added to the returned URL. It defaults to *True*.
    """
    encoded_text = str(base64.urlsafe_b64encode(bytes(text, encoding='utf-8')), encoding='utf-8')

    image_format = qr_code_options.image_format
    params = dict(text=encoded_text, size=qr_code_options.size, border=qr_code_options.border, version=qr_code_options.version or '', image_format=image_format, error_correction=qr_code_options.error_correction, cache_enabled=cache_enabled)
    path = reverse('qr_code:serve_qr_code_image')

    if include_url_protection_token:
        # Generate token to handle view protection. The token is added to the query arguments. It does not replace
        # existing plain text query arguments in order to allow usage of the URL as an API (without token since external
        # users cannot generate the signed token!).
        token = get_qr_url_protection_signed_token(qr_code_options)
        params['token'] = token

    url = '%s?%s' % (path, urllib.parse.urlencode(params))
    return mark_safe(url)
