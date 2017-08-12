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

SvgPathImage = _SvgPathImage
PilImageOrFallback = _PilImageOrFallback
