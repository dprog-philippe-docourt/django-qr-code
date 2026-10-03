import base64
import functools
import urllib.parse
from collections.abc import Mapping
from datetime import datetime
from typing import Optional, Any

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.core.signing import Signer
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.encoding import force_str
from django.utils.safestring import mark_safe
from pydantic import validate_call

from qr_code.qrcode import constants, PYDANTIC_CONFIG
from qr_code.qrcode.utils import QRCodeOptions


def _get_default_url_protection_options() -> dict:
    return {
        constants.TOKEN_LENGTH: 20,
        constants.SIGNING_KEY: settings.SECRET_KEY,
        constants.SIGNING_SALT: "qr_code_url_protection_salt",
        constants.ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER: False,
    }


def _options_allow_external_request(url_protection_options: Mapping, user: User | AnonymousUser | None) -> bool:
    allows_external_requests = url_protection_options[constants.ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER]
    # Evaluate the callable if required.
    if callable(allows_external_requests):
        return allows_external_requests(user or AnonymousUser())
    if allows_external_requests is True:
        return bool(user and user.pk and user.is_authenticated)
    return False


def requires_url_protection_token(user: User | AnonymousUser | None = None) -> bool:
    return not _options_allow_external_request(get_url_protection_options(), user)


def allows_external_request_from_user(user: User | AnonymousUser | None = None) -> bool:
    return _options_allow_external_request(get_url_protection_options(), user)


def get_url_protection_options() -> dict:
    options = _get_default_url_protection_options()
    settings_options = getattr(settings, "QR_CODE_URL_PROTECTION", None)
    if isinstance(settings_options, Mapping):
        options.update(settings_options)
    return options


@functools.cache
def _get_random_token() -> str:
    """
    Return the random part of the URL protection token.

    It is generated once per process, on first use rather than at import time, so that importing this module does not
    require the settings (e.g., SECRET_KEY) to be available. Keeping it stable produces identical URLs for identical
    QR codes, which is required for the server-side cache and the ETag-based HTTP caching to be effective.
    """
    url_protection_options = get_url_protection_options()
    return get_random_string(url_protection_options[constants.TOKEN_LENGTH])


def get_qr_url_protection_signed_token(qr_code_options: QRCodeOptions):
    """Generate a signed token to handle view protection."""
    url_protection_options = get_url_protection_options()
    signer = Signer(key=url_protection_options[constants.SIGNING_KEY], salt=url_protection_options[constants.SIGNING_SALT])
    return signer.sign(get_qr_url_protection_token(qr_code_options, _get_random_token()))


def get_qr_url_protection_token(qr_code_options, random_token):
    """
    Generate a random token for the QR code image.

    The token contains image attributes so that a user cannot use a token provided somewhere on a website to
    generate bigger QR codes. The random_token part ensures that the signed token is not predictable.
    """
    o = qr_code_options
    return f"{o.size}.{o.border}.{o.version or ''}.{o.image_format}.{o.error_correction}.{random_token}"


def qr_code_etag(request) -> str:
    return f'"{request.path}:{request.GET.urlencode()}:version_{constants.QR_CODE_GENERATION_VERSION_DATE.isoformat()}"'


def qr_code_last_modified(_request) -> datetime:
    return constants.QR_CODE_GENERATION_VERSION_DATE


@validate_call(config=PYDANTIC_CONFIG)
def make_qr_code_url(
    data: Any,
    qr_code_options: Optional[QRCodeOptions] = None,
    force_text: bool = True,
    cache_enabled: Optional[bool] = None,
    url_signature_enabled: Optional[bool] = None,
) -> str:
    """Build a URL to a view that handle serving QR code image from the given parameters.

    Any invalid argument related to the size or the format of the image is silently
    converted into the default value for that argument.

    :param str data: Data to encode into a QR code.
    :param QRCodeOptions qr_code_options: The rendering options for the QR code.
    :param bool force_text: Tells whether we want to force the `data` to be considered as text string and encoded in
        byte mode.
    :param bool cache_enabled: Allows skipping caching the QR code (when set to *False*) when caching has
        been enabled.
    :param bool url_signature_enabled: Tells whether the random token for protecting the URL against
        external requests is added to the returned URL. It defaults to *True*.
    """
    qr_code_options = QRCodeOptions() if qr_code_options is None else qr_code_options
    if url_signature_enabled is None:
        url_signature_enabled = constants.DEFAULT_URL_SIGNATURE_ENABLED
    if cache_enabled is None:
        cache_enabled = constants.DEFAULT_CACHE_ENABLED
    data_value: str | int
    if force_text:
        data_key, data_value = "text", base64.b64encode(force_str(data).encode("utf-8")).decode("utf-8")
    elif isinstance(data, int):
        data_key, data_value = "int", data
    else:
        raw_data = data.encode("utf-8") if isinstance(data, str) else data
        data_key, data_value = "bytes", base64.b64encode(raw_data).decode("utf-8")
    params = {data_key: data_value, "cache_enabled": 1 if cache_enabled else 0}
    # Only add non-default values to the params dict
    if qr_code_options.size != constants.DEFAULT_MODULE_SIZE:
        params["size"] = qr_code_options.size
    if qr_code_options.border != constants.DEFAULT_BORDER_SIZE:
        params["border"] = qr_code_options.border
    if qr_code_options.version != constants.DEFAULT_VERSION:
        params["version"] = qr_code_options.version
    if qr_code_options.image_format != constants.DEFAULT_IMAGE_FORMAT:
        params["image_format"] = qr_code_options.image_format
    if qr_code_options.error_correction != constants.DEFAULT_ERROR_CORRECTION:
        params["error_correction"] = qr_code_options.error_correction
    if qr_code_options.micro:
        params["micro"] = 1
    if qr_code_options.eci:
        params["eci"] = 1
    if qr_code_options.boost_error:
        params["boost_error"] = 1
    params["encoding"] = qr_code_options.encoding or ""
    params.update(qr_code_options.color_mapping())
    path = reverse("qr_code:serve_qr_code_image")
    if url_signature_enabled:
        # Generate token to handle view protection. The token is added to the query arguments. It does not replace
        # existing plain data query arguments to allow usage of the URL as an API (without a token since external
        # users cannot generate the signed token!).
        params["token"] = get_qr_url_protection_signed_token(qr_code_options)
    url = f"{path}?{urllib.parse.urlencode(params)}"
    return mark_safe(url)
