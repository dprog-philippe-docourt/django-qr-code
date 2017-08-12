"""
Import the required subclasses of :class:`~qrcode.image.base.BaseImage` from the qrcode library with a fallback to SVG
format when the Pillow library is not available.
"""

from qrcode.image.svg import SvgPathImage as _SvgPathImage
try:
    from qrcode.image.pil import PilImage as _PilImageOrFallback

except ImportError:
    print("WARNING: Pillow is not installed. No support available for PNG format. SVG will be used instead.")
    from qrcode.image.svg import SvgPathImage as _PilImageOrFallback

SVG_FORMAT_NAME = 'svg'
PNG_FORMAT_NAME = 'png'

SvgPathImage = _SvgPathImage
PilImageOrFallback = _PilImageOrFallback


def has_png_support():
    return PilImageOrFallback is not SvgPathImage


def get_supported_image_format(image_format):
    image_format = image_format.lower()
    if image_format not in [SVG_FORMAT_NAME, PNG_FORMAT_NAME] or not has_png_support():
        image_format = SVG_FORMAT_NAME
    return image_format
