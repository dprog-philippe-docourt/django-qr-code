"""Utility classes and functions for generating QR code. This module depends on the qrcode python library."""

import base64
from io import BytesIO

import xml.etree.ElementTree as ET

from django.utils.html import escape
from django.utils.safestring import mark_safe
from qrcode.image.pil import PilImage
from qrcode.image.svg import SvgPathImage


class SvgEmbeddedInHtmlImage(SvgPathImage):
    def _write(self, stream):
        self._img.append(self.make_path())
        ET.ElementTree(self._img).write(stream, encoding="UTF-8", xml_declaration=False, default_namespace=None,
                                        method='html')


def make_qr_code(text, size='M', border=4, version=None, image_format='svg'):
    """Generate a <svg> or <img> tag representing the QR code for the given text. This tag can be embedded into an
    HTML document. """

    image_format = image_format.lower()
    if image_format not in ['svg', 'png']:
        image_format = 'svg'
    if isinstance(version, int) or (isinstance(version, str) and version.isdigit()):
        actual_version = int(version)
    else:
        actual_version = 0
    if isinstance(size, int) or (isinstance(size, str) and size.isdigit()):
        actual_size = int(size)
    else:
        sizes_dict = {'t': 6, 's': 12, 'm': 18, 'l': 30, 'h': 48}
        if not size or not size.lower() in sizes_dict:
            size = 'm'
        actual_size = sizes_dict[size.lower()]
    import qrcode
    qr = qrcode.QRCode(
        version=actual_version if 0 < actual_version <= 40 else 1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=actual_size,
        border=border,
        image_factory=SvgEmbeddedInHtmlImage if image_format == 'svg' else PilImage
    )
    qr.add_data(text)
    if actual_version == 0:
        qr.make(fit=True)
    img = qr.make_image()
    stream = BytesIO()
    if image_format == 'svg':
        img.save(stream, kind='SVG')
        html_fragment = (str(stream.getvalue(), 'utf-8'))
    else:
        img.save(stream, format='PNG')
        html_fragment = '<img src="data:image/png;base64, %s" alt="%s"' % (
        str(base64.b64encode(stream.getvalue()), encoding='ascii'), escape(text))
    return mark_safe(html_fragment)
