from io import BytesIO

import xml.etree.ElementTree as ET

from django.utils.safestring import mark_safe
from qrcode.image.svg import SvgPathImage


class SvgEmbeddedInHtmlImage(SvgPathImage):
    def _write(self, stream):
        self._img.append(self.make_path())
        ET.ElementTree(self._img).write(stream, encoding="UTF-8", xml_declaration=False, default_namespace=None, method='html')


def make_qr_code(text, size='M', border=0, version=None):
    if isinstance(version, int) or (isinstance(version, str) and version.isdigit()):
        actual_version = version
    else:
        actual_version = 0
    if isinstance(size, int) or (isinstance(size, str) and size.isdigit()):
        actual_size = size
    else:
        sizes_dict = {'t': 6, 's': 12, 'm': 18, 'l': 30, 'h': 48}
        if not size.lower() in sizes_dict:
            size = 'm'
        actual_size = sizes_dict[size.lower()]
    import qrcode
    qr = qrcode.QRCode(
        version=actual_version if 0 < actual_version <= 40 else 1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=actual_size,
        border=border,
        image_factory=SvgEmbeddedInHtmlImage
    )
    qr.add_data(text)
    if actual_version == 0:
        qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    stream = BytesIO()
    img.save(stream, kind='SVG')
    html_fragment = (str(stream.getvalue(), 'utf-8'))
    return mark_safe(html_fragment)
