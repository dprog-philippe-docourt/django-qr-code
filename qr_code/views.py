import base64
from io import BytesIO

from django.conf import settings
from django.core.signing import Signer, BadSignature
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.utils.decorators import available_attrs
from django.utils.six import wraps
from django.views.decorators.cache import cache_page
from django.views.decorators.http import condition

from qr_code.qrcode_image import SvgPathImage, PilImageOrFallback, SVG_FORMAT_NAME, PNG_FORMAT_NAME, \
    get_supported_image_format
from qr_code.qr_code import DEFAULT_MODULE_SIZE, DEFAULT_BORDER_SIZE, DEFAULT_VERSION, DEFAULT_IMAGE_FORMAT, \
    make_qr_code_image, QR_CODE_GENERATION_VERSION_DATE, get_url_protection_options, get_qr_url_protection_token


def cache_qr_code():
    """
    Decorator that caches the requested page if a settings named 'QR_CODE_CACHE_ALIAS' exists and is not empty or None.
    """
    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *view_args, **view_kwargs):
            cache_enabled = request.GET.get('cache_enabled', True)
            if cache_enabled and hasattr(settings, 'QR_CODE_CACHE_ALIAS') and settings.QR_CODE_CACHE_ALIAS:
                # We found a cache alias for storing the generate qr code and cache is enabled, use it to cache the
                # page.
                timeout = settings.CACHES[settings.QR_CODE_CACHE_ALIAS]['TIMEOUT']
                response = cache_page(timeout, cache=settings.QR_CODE_CACHE_ALIAS)(view_func)(request, *view_args, **view_kwargs)
            else:
                # No cache alias for storing the generated qr code, call the view as is.
                response = (view_func)(request, *view_args, **view_kwargs)
            return response
        return _wrapped_view
    return decorator


def qr_code_etag(request):
    return '%s:%s:version_%s' % (request.path, request.GET.urlencode(), QR_CODE_GENERATION_VERSION_DATE.isoformat())


def qr_code_last_modified(request):
    return QR_CODE_GENERATION_VERSION_DATE


@condition(etag_func=qr_code_etag, last_modified_func=qr_code_last_modified)
@cache_qr_code()
def serve_qr_code_image(request):
    """Serve an image that represents the requested QR code."""
    text = base64.urlsafe_b64decode(request.GET.get('text', ''))
    size = request.GET.get('size', DEFAULT_MODULE_SIZE)
    border = request.GET.get('border', DEFAULT_BORDER_SIZE)
    version = request.GET.get('version', DEFAULT_VERSION)
    image_format = request.GET.get('image_format', DEFAULT_IMAGE_FORMAT)
    image_format = get_supported_image_format(image_format)

    # Handle view protection (we do not allow external requests for anyone).
    url_protection_options = get_url_protection_options(request.user)
    if not url_protection_options['ALLOWS_EXTERNAL_REQUESTS']:
        token = request.GET.get('token', '')
        signer = Signer(key=url_protection_options['SIGNING_KEY'], salt=url_protection_options['SIGNING_SALT'])
        try:
            # Check signature.
            url_protection_string = signer.unsign(token)
            # Check that the given token matches the request parameters.
            random_token = url_protection_string.split('.')[-1]
            if get_qr_url_protection_token(size, border, version, image_format, random_token) != url_protection_string:
                raise PermissionDenied("Request query does not match protection token.")
        except BadSignature:
            raise PermissionDenied("Wrong token signature.")

    img = make_qr_code_image(text, image_factory=SvgPathImage if image_format == SVG_FORMAT_NAME else PilImageOrFallback, size=size,
                             border=border, version=version)

    # Warning: The largest QR codes, in version 40, with a border of 4 modules, and rendered in SVG format, are ~800
    # KB large. This can be handled in memory but could cause troubles if the server needs to generate thousands of
    # those QR codes within a short interval! Note that this would also be a problem for the CPU. Such QR codes needs
    # 0.7 second to be generated on a powerful machine (2017), and probably more than one second on a cheap hosting.
    stream = BytesIO()
    if image_format == SVG_FORMAT_NAME:
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
