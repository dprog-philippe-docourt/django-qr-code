"""Tags for Django template system that help generating QR codes."""

from django import template

from qr_code.qr_code import make_qr_code, DEFAULT_MODULE_SIZE, DEFAULT_BORDER_SIZE, DEFAULT_VERSION, \
    DEFAULT_IMAGE_FORMAT, DEFAULT_CACHE_ENABLED, make_qr_code_url

register = template.Library()


@register.simple_tag()
def qr_from_text(text, size=DEFAULT_MODULE_SIZE, border=DEFAULT_BORDER_SIZE, version=DEFAULT_VERSION, image_format=DEFAULT_IMAGE_FORMAT):
    """Wrapper for function :func:`~qr_code.qr_code.make_qr_code`"""
    return make_qr_code(text, size=size, border=border, version=version, image_format=image_format)


@register.simple_tag()
def qr_url_from_text(text, size=DEFAULT_MODULE_SIZE, border=DEFAULT_BORDER_SIZE, version=DEFAULT_VERSION, image_format=DEFAULT_IMAGE_FORMAT, cache_enabled=DEFAULT_CACHE_ENABLED):
    """Wrapper for function :func:`~qr_code.qr_code.make_qr_code_url`"""
    return make_qr_code_url(text, size=size, border=border, version=version, image_format=image_format, cache_enabled=cache_enabled)
