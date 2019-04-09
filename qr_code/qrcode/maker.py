"""Tools for generating QR codes. This module depends on the qrcode python library."""

import base64
from io import BytesIO

import xml.etree.ElementTree as ET

from django.utils.encoding import force_text
from django.utils.html import escape
from django.utils.safestring import mark_safe

from qr_code.qrcode.constants import SIZE_DICT, ERROR_CORRECTION_DICT, DEFAULT_ERROR_CORRECTION, DEFAULT_MODULE_SIZE, \
    DEFAULT_CACHE_ENABLED, DEFAULT_URL_SIGNATURE_ENABLED
from qr_code.qrcode.image import SvgPathImage, PilImageOrFallback, SVG_FORMAT_NAME, PNG_FORMAT_NAME
from qr_code.qrcode.serve import make_qr_code_url
from qr_code.qrcode.utils import QRCodeOptions


class SvgEmbeddedInHtmlImage(SvgPathImage):
    def _write(self, stream):
        self._img.append(self.make_path())
        ET.ElementTree(self._img).write(stream, encoding="UTF-8", xml_declaration=False, default_namespace=None,
                                        method='html')


def make_qr_code_image(text, image_factory, qr_code_options=QRCodeOptions()):
    """
    Generates an image object (from the qrcode library) representing the QR code for the given text.

    Any invalid argument is silently converted into the default value for that argument.
    """

    valid_version = _get_valid_version_or_none(qr_code_options.version)
    valid_size = _get_valid_size_or_default(qr_code_options.size)
    valid_error_correction = _get_valid_error_correction_or_default(qr_code_options.error_correction)
    import qrcode
    qr = qrcode.QRCode(
        version=valid_version,
        error_correction=valid_error_correction,
        box_size=valid_size,
        border=qr_code_options.border
    )
    qr.add_data(force_text(text))
    if valid_version is None:
        qr.make(fit=True)
    return qr.make_image(image_factory=image_factory)


def _get_valid_error_correction_or_default(error_correction):
    return ERROR_CORRECTION_DICT.get(error_correction.upper(), ERROR_CORRECTION_DICT[
        DEFAULT_ERROR_CORRECTION])


def _get_valid_size_or_default(size):
    if _can_be_cast_to_int(size):
        actual_size = int(size)
        if actual_size < 1:
            actual_size = SIZE_DICT[DEFAULT_MODULE_SIZE.lower()]
    elif isinstance(size, str):
        actual_size = SIZE_DICT.get(size.lower(), DEFAULT_MODULE_SIZE)
    else:
        actual_size = SIZE_DICT[DEFAULT_MODULE_SIZE.lower()]
    return actual_size


def _get_valid_version_or_none(version):
    if _can_be_cast_to_int(version):
        actual_version = int(version)
        if actual_version < 1 or actual_version > 40:
            actual_version = None
    else:
        actual_version = None
    return actual_version


def _can_be_cast_to_int(value):
    return isinstance(value, int) or (isinstance(value, str) and value.isdigit())


def make_embedded_qr_code(text, qr_code_options=QRCodeOptions()):
    """
    Generates a <svg> or <img> tag representing the QR code for the given text. This tag can be embedded into an
    HTML document.
    """
    image_format = qr_code_options.image_format
    img = make_qr_code_image(text, SvgEmbeddedInHtmlImage if image_format == SVG_FORMAT_NAME else PilImageOrFallback, qr_code_options=qr_code_options)
    stream = BytesIO()
    if image_format == SVG_FORMAT_NAME:
        img.save(stream, kind=SVG_FORMAT_NAME.upper())
        html_fragment = (str(stream.getvalue(), 'utf-8'))
    else:
        img.save(stream, format=PNG_FORMAT_NAME.upper())
        html_fragment = '<img src="data:image/png;base64, %s" alt="%s">' % (str(base64.b64encode(stream.getvalue()), encoding='ascii'), escape(text))
    return mark_safe(html_fragment)


def make_qr_code_with_args(text, qr_code_args):
    options = qr_code_args.get('options')
    if options:
        if not isinstance(options, QRCodeOptions):
            raise TypeError('The options argument must be of type QRCodeOptions.')
    else:
        options = QRCodeOptions(**qr_code_args)
    return make_embedded_qr_code(text, options)


def make_qr_code_url_with_args(text, qr_code_args):
    cache_enabled = DEFAULT_CACHE_ENABLED
    if 'cache_enabled' in qr_code_args:
        cache_enabled = qr_code_args.pop('cache_enabled')
    url_signature_enabled = DEFAULT_URL_SIGNATURE_ENABLED
    if 'url_signature_enabled' in qr_code_args:
        url_signature_enabled = qr_code_args.pop('url_signature_enabled')
    options = qr_code_args.get('options')
    if options:
        if not isinstance(options, QRCodeOptions):
            raise TypeError('The options argument must be of type QRCodeOptions.')
    else:
        options = QRCodeOptions(**qr_code_args)
    return make_qr_code_url(text, options, cache_enabled=cache_enabled, url_signature_enabled=url_signature_enabled)
