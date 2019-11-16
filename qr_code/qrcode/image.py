"""
Import the required subclasses of :class:`~qrcode.image.base.BaseImage` from the qrcode library with a fallback to SVG
format when the Pillow library is not available.
"""
import logging
from qrcode.image.svg import SvgPathImage as _SvgPathImage

logger = logging.getLogger('django-qr-code')
try:
    from qrcode.image.pil import PilImage as _PilImageOrFallback
except ImportError:  # pragma: no cover
    logger.debug("Pillow is not installed. No support available for PNG format.")
    from qrcode.image.svg import SvgPathImage as _PilImageOrFallback

SVG_FORMAT_NAME = 'svg'
PNG_FORMAT_NAME = 'png'

SvgPathImage = _SvgPathImage
PilImageOrFallback = _PilImageOrFallback


def has_png_support():
    return PilImageOrFallback is not SvgPathImage


def get_supported_image_format(image_format):
    image_format = image_format.lower()
    if image_format not in [SVG_FORMAT_NAME, PNG_FORMAT_NAME]:
        logger.warning('Unknown image format: %s' % image_format)
        image_format = SVG_FORMAT_NAME
    elif image_format == PNG_FORMAT_NAME and not has_png_support():  # pragma: no cover
        logger.warning(
            "No support available for PNG format, SVG will be used instead. Please install Pillow for PNG support.")
        image_format = SVG_FORMAT_NAME
    return image_format
