import base64
import binascii
import functools

from django.conf import settings
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.core.signing import BadSignature, Signer
from django.http import HttpResponse
from django.views.decorators.cache import cache_page
from django.views.decorators.http import condition

from qr_code.qrcode import constants
from qr_code.qrcode.maker import make_qr_code_image
from qr_code.qrcode.utils import QRCodeOptions
from qr_code.qrcode.serve import (
    get_url_protection_options,
    get_qr_url_protection_token,
    qr_code_etag,
    qr_code_last_modified,
    allows_external_request_from_user,
)


def cache_qr_code():
    """
    Decorator that caches the requested page if a settings named 'QR_CODE_CACHE_ALIAS' exists and is not empty or None.
    """

    def decorator(view_func):
        @functools.wraps(view_func)
        def _wrapped_view(request, *view_args, **view_kwargs):
            cache_enabled = int(request.GET.get("cache_enabled", 1)) == 1
            if cache_enabled and hasattr(settings, "QR_CODE_CACHE_ALIAS") and settings.QR_CODE_CACHE_ALIAS:
                # We found a cache alias for storing the generate qr code and cache is enabled, use it to cache the
                # page.
                timeout = settings.CACHES[settings.QR_CODE_CACHE_ALIAS]["TIMEOUT"]
                key_prefix = "token={}.user_pk={}".format(
                    request.GET.get("url_signature_enabled") or constants.DEFAULT_URL_SIGNATURE_ENABLED,
                    request.user.pk,
                )
                response = cache_page(timeout, cache=settings.QR_CODE_CACHE_ALIAS, key_prefix=key_prefix)(view_func)(
                    request, *view_args, **view_kwargs
                )
            else:
                # No cache alias for storing the generated qr code, call the view as is.
                response = (view_func)(request, *view_args, **view_kwargs)
            return response

        return _wrapped_view

    return decorator


@condition(etag_func=qr_code_etag, last_modified_func=qr_code_last_modified)
@cache_qr_code()
def serve_qr_code_image(request) -> HttpResponse:
    """Serve an image that represents the requested QR code.

    IMPORTANT NOTE: Each boolean option mentioned below (value True/False) must be passed as `<option name>=1` for
    `True`, respectively `<option name>=0` for `False`.

    You may pass any argument available for :py:func:`qr_code.qrcode.utils.QRCodeOptions.__init__` to adjust the
    appearance of the returned QR code. The arguments must be passed as query
    string arguments in the URL. Additionally, the following arguments are available:
    * cache_enabled: boolean – Tells the generator to work around the caching mechanism if it is empty (default: True/undefined).
    * token: str – By default, the application only serves QR code images for authenticated URLs (requests generated
    from your application and addressed to your application). The authentication uses a HMAC to sign the request query
    arguments. The authentication code is passed as a query argument named `token` which is automatically generated
    by `qr_url_from_text` or `qr_url_from_data`.
    """
    qr_code_options = get_qr_code_option_from_request(request)
    # Handle image access protection (we do not allow external requests for anyone).
    check_image_access_permission(request, qr_code_options)
    force_text = False
    if "bytes" in request.GET:
        try:
            data = base64.b64decode(request.GET.get("bytes", b""))
        except binascii.Error:
            raise SuspiciousOperation("Invalid base64 encoded data.")
    elif "int" in request.GET:
        try:
            data = int(request.GET.get("int", None))  # type: ignore
        except (ValueError, TypeError):
            raise SuspiciousOperation("Invalid integer value.")
    else:
        try:
            data = base64.b64decode(request.GET.get("text", "")).decode("utf-8")  # type: ignore
            force_text = True
        except binascii.Error:
            raise SuspiciousOperation("Invalid base64 encoded text.")
        except UnicodeDecodeError:
            raise SuspiciousOperation("Invalid UTF-8 encoded text.")
    img = make_qr_code_image(data, qr_code_options=qr_code_options, force_text=force_text)
    return HttpResponse(content=img, content_type="image/svg+xml" if qr_code_options.image_format == "svg" else "image/png")


def get_qr_code_option_from_request(request) -> QRCodeOptions:
    request_query = request.GET.dict()
    for key in ("bytes", "text", "int", "token", "cache_enabled"):
        request_query.pop(key, None)
    # Force typing for booleans.
    request_query["micro"] = int(request_query.get("micro", 0)) == 1
    request_query["eci"] = int(request_query.get("eci", 0)) == 1
    request_query["boost_error"] = int(request_query.get("boost_error", 0)) == 1
    return QRCodeOptions(**request_query)


def check_image_access_permission(request, qr_code_options) -> None:
    """Handle image access protection (we do not allow external requests for anyone)."""
    token = request.GET.get("token", "")
    if token:
        check_url_signature_token(qr_code_options, token)
    else:
        if not allows_external_request_from_user(request.user):
            raise PermissionDenied("You are not allowed to access this QR code.")


def check_url_signature_token(qr_code_options, token) -> None:
    url_protection_options = get_url_protection_options()
    signer = Signer(key=url_protection_options[constants.SIGNING_KEY], salt=url_protection_options[constants.SIGNING_SALT])
    try:
        # Check signature.
        url_protection_string = signer.unsign(token)
        # Check that the given token matches the request parameters.
        random_token = url_protection_string.split(".")[-1]
        if get_qr_url_protection_token(qr_code_options, random_token) != url_protection_string:
            raise PermissionDenied("Request query does not match protection token.")
    except BadSignature:
        raise PermissionDenied("Wrong token signature.")
