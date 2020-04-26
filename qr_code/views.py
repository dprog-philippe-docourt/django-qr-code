import base64
import binascii
import functools
from io import BytesIO

from django.conf import settings
from django.core.exceptions import PermissionDenied, SuspiciousOperation
from django.core.signing import BadSignature, Signer
from django.http import HttpResponse
from django.views.decorators.cache import cache_page
from django.views.decorators.http import condition

from qr_code.qrcode import constants
from qr_code.qrcode.maker import make_qr_code_image
from qr_code.qrcode.utils import QRCodeOptions
from qr_code.qrcode.serve import get_url_protection_options, get_qr_url_protection_token, qr_code_etag, \
    qr_code_last_modified, allows_external_request_from_user
from qr_code.qrcode.image import PNG_FORMAT_NAME, PilImageOrFallback, SVG_FORMAT_NAME, SvgPathImage


def cache_qr_code():
    """
    Decorator that caches the requested page if a settings named 'QR_CODE_CACHE_ALIAS' exists and is not empty or None.
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def _wrapped_view(request, *view_args, **view_kwargs):
            cache_enabled = request.GET.get('cache_enabled', True)
            if cache_enabled and hasattr(settings, 'QR_CODE_CACHE_ALIAS') and settings.QR_CODE_CACHE_ALIAS:
                # We found a cache alias for storing the generate qr code and cache is enabled, use it to cache the
                # page.
                timeout = settings.CACHES[settings.QR_CODE_CACHE_ALIAS]['TIMEOUT']
                key_prefix = 'token=%s.user_pk=%s' % (request.GET.get('url_signature_enabled') or constants.DEFAULT_URL_SIGNATURE_ENABLED, request.user.pk)
                response = cache_page(timeout, cache=settings.QR_CODE_CACHE_ALIAS, key_prefix=key_prefix)(view_func)(request, *view_args, **view_kwargs)
            else:
                # No cache alias for storing the generated qr code, call the view as is.
                response = (view_func)(request, *view_args, **view_kwargs)
            return response
        return _wrapped_view
    return decorator


@condition(etag_func=qr_code_etag, last_modified_func=qr_code_last_modified)
@cache_qr_code()
def serve_qr_code_image(request):
    """Serve an image that represents the requested QR code."""
    qr_code_options = get_qr_code_option_from_request(request)

    # Handle image access protection (we do not allow external requests for anyone).
    check_image_access_permission(request, qr_code_options)

    try:
        text = base64.urlsafe_b64decode(request.GET.get('text', ''))
    except binascii.Error:
        raise SuspiciousOperation("Invalid base64 encoded string.")
    img = make_qr_code_image(text, image_factory=SvgPathImage if qr_code_options.image_format == SVG_FORMAT_NAME else PilImageOrFallback, qr_code_options=qr_code_options)

    # Warning: The largest QR codes, in version 40, with a border of 4 modules, and rendered in SVG format, are ~800
    # KB large. This can be handled in memory but could cause troubles if the server needs to generate thousands of
    # those QR codes within a short interval! Note that this would also be a problem for the CPU. Such QR codes needs
    # 0.7 second to be generated on a powerful machine (2017), and probably more than one second on a cheap hosting.
    stream = BytesIO()
    if qr_code_options.image_format == SVG_FORMAT_NAME:
        img.save(stream, kind=SVG_FORMAT_NAME.upper())
        mime_type = 'image/svg+xml'
    else:
        img.save(stream, format=PNG_FORMAT_NAME.upper())
        mime_type = 'image/png'

    # Go to the beginning of the stream.
    stream.seek(0)

    # Build the response.
    response = HttpResponse(content=stream, content_type=mime_type)
    return response


def get_qr_code_option_from_request(request):
    request_query = request.GET.dict()
    for key in ('text', 'token', 'cache_enabled'):
        if key in request_query:
            request_query.pop(key)
    qr_code_options = QRCodeOptions(**request_query)
    return qr_code_options


def check_image_access_permission(request, qr_code_options):
    """Handle image access protection (we do not allow external requests for anyone)."""
    token = request.GET.get('token', '')
    if token:
        check_url_signature_token(qr_code_options, token)
    else:
        if not allows_external_request_from_user(request.user):
            raise PermissionDenied("You are not allowed to access this QR code.")


def check_url_signature_token(qr_code_options, token):
    url_protection_options = get_url_protection_options()
    signer = Signer(key=url_protection_options[constants.SIGNING_KEY],
                    salt=url_protection_options[constants.SIGNING_SALT])
    try:
        # Check signature.
        url_protection_string = signer.unsign(token)
        # Check that the given token matches the request parameters.
        random_token = url_protection_string.split('.')[-1]
        if get_qr_url_protection_token(qr_code_options, random_token) != url_protection_string:
            raise PermissionDenied("Request query does not match protection token.")
    except BadSignature:
        raise PermissionDenied("Wrong token signature.")
