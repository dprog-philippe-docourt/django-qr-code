import base64
import urllib.parse
from collections.abc import Mapping
from datetime import datetime
from typing import Optional, Union, Any

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.core.signing import Signer
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.encoding import force_str
from django.utils.safestring import mark_safe

from qr_code.qrcode import constants
from qr_code.qrcode.utils import QRCodeOptions


def _get_default_url_protection_options() -> dict:
    return {
        constants.TOKEN_LENGTH: 20,
        constants.SIGNING_KEY: settings.SECRET_KEY,
        constants.SIGNING_SALT: 'qr_code_url_protection_salt',
        constants.ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER: False
    }


def _get_url_protection_settings() -> Optional[Mapping]:
    if hasattr(settings, 'QR_CODE_URL_PROTECTION') and isinstance(settings.QR_CODE_URL_PROTECTION, Mapping):
        return settings.QR_CODE_URL_PROTECTION
    return None


def _options_allow_external_request(url_protection_options: Mapping, user: Union[User, AnonymousUser, None]) -> bool:
    # Evaluate the callable if required.
    if callable(url_protection_options[constants.ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER]):
        allows_external_request = url_protection_options[constants.ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER](user or AnonymousUser())
    elif url_protection_options[constants.ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER] is True:
        allows_external_request = user and user.pk and user.is_authenticated
    else:
        allows_external_request = False
    return allows_external_request


def requires_url_protection_token(user: Union[User, AnonymousUser, None] = None) -> bool:
    return not _options_allow_external_request(get_url_protection_options(), user)


def allows_external_request_from_user(user: Union[User, AnonymousUser, None] = None) -> bool:
    return _options_allow_external_request(get_url_protection_options(), user)


def get_url_protection_options() -> dict:
    options = _get_default_url_protection_options()
    settings_options = _get_url_protection_settings()
    if settings_options is not None:
        options.update(settings.QR_CODE_URL_PROTECTION)
    return options


def _make_random_token() -> str:
    url_protection_options = get_url_protection_options()
    return get_random_string(url_protection_options[constants.TOKEN_LENGTH])


_RANDOM_TOKEN = _make_random_token()


def get_qr_url_protection_signed_token(qr_code_options: QRCodeOptions):
    """Generate a signed token to handle view protection."""
    url_protection_options = get_url_protection_options()
    signer = Signer(key=url_protection_options[constants.SIGNING_KEY], salt=url_protection_options[constants.SIGNING_SALT])
    token = signer.sign(get_qr_url_protection_token(qr_code_options, _RANDOM_TOKEN))
    return token


def get_qr_url_protection_token(qr_code_options, random_token):
    """
    Generate a random token for the QR code image.

    The token contains image attributes so that a user cannot use a token provided somewhere on a website to
    generate bigger QR codes. The random_token part ensures that the signed token is not predictable.
    """
    return '.'.join(list(map(str, (qr_code_options.size, qr_code_options.border, qr_code_options.version or '', qr_code_options.image_format, qr_code_options.error_correction, random_token))))


def qr_code_etag(request) -> str:
    return '"%s:%s:version_%s"' % (request.path, request.GET.urlencode(), constants.QR_CODE_GENERATION_VERSION_DATE.isoformat())


def qr_code_last_modified(_request) -> datetime:
    return constants.QR_CODE_GENERATION_VERSION_DATE


def make_qr_code_url(data: Any, qr_code_options: Optional[QRCodeOptions] = None, force_text: bool = True, cache_enabled: Optional[bool] = None,
                     url_signature_enabled: Optional[bool] = None) -> str:
    """Build an URL to a view that handle serving QR code image from the given parameters.

    Any invalid argument related to the size or the format of the image is silently
    converted into the default value for that argument.

    :param str data: Data to encode into a QR code.
    :param QRCodeOptions qr_code_options: The rendering options for the QR code.
    :param bool force_text: Tells whether we want to force the `data` to be considered as text string and encoded in
        byte mode.
    :param bool cache_enabled: Allows to skip caching the QR code (when set to *False*) when caching has
        been enabled.
    :param bool url_signature_enabled: Tells whether the random token for protecting the URL against
        external requests is added to the returned URL. It defaults to *True*.
    """
    qr_code_options = QRCodeOptions() if qr_code_options is None else qr_code_options
    if url_signature_enabled is None:
        url_signature_enabled = constants.DEFAULT_URL_SIGNATURE_ENABLED
    if cache_enabled is None:
        cache_enabled = constants.DEFAULT_CACHE_ENABLED
    cache_enabled_arg = 1 if cache_enabled else 0
    if force_text:
        encoded_data = str(base64.b64encode(force_str(data).encode('utf-8')), encoding='utf-8')
        params = dict(text=encoded_data, cache_enabled=cache_enabled_arg)
    elif isinstance(data, int):
        params = dict(int=data, cache_enabled=cache_enabled_arg)
    else:
        if isinstance(data, str):
            b64data = base64.b64encode(force_str(data).encode('utf-8'))
        else:
            b64data = base64.b64encode(data)
        encoded_data = str(b64data, encoding='utf-8')
        params = dict(bytes=encoded_data, cache_enabled=cache_enabled_arg)
    # Only add non-default values to the params dict
    if qr_code_options.size != constants.DEFAULT_MODULE_SIZE:
        params['size'] = qr_code_options.size
    if qr_code_options.border != constants.DEFAULT_BORDER_SIZE:
        params['border'] = qr_code_options.border
    if qr_code_options.version != constants.DEFAULT_VERSION:
        params['version'] = qr_code_options.version
    if qr_code_options.image_format != constants.DEFAULT_IMAGE_FORMAT:
        params['image_format'] = qr_code_options.image_format
    if qr_code_options.error_correction != constants.DEFAULT_ERROR_CORRECTION:
        params['error_correction'] = qr_code_options.error_correction
    if qr_code_options.micro:
        params['micro'] = 1
    if qr_code_options.eci:
        params['eci'] = 1
    if qr_code_options.boost_error:
        params['boost_error'] = 1
    params['encoding'] = qr_code_options.encoding if qr_code_options.encoding else ''
    params.update(qr_code_options.color_mapping())
    path = reverse('qr_code:serve_qr_code_image')
    if url_signature_enabled:
        # Generate token to handle view protection. The token is added to the query arguments. It does not replace
        # existing plain data query arguments in order to allow usage of the URL as an API (without token since external
        # users cannot generate the signed token!).
        token = get_qr_url_protection_signed_token(qr_code_options)
        params['token'] = token
    url = '%s?%s' % (path, urllib.parse.urlencode(params))
    return mark_safe(url)
