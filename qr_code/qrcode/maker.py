"""Tools for generating QR codes. This module depends on the Segno library."""
import io
from typing import Mapping, Any

from django.utils.html import escape
from django.utils.safestring import mark_safe
import segno
from qr_code.qrcode.constants import DEFAULT_CACHE_ENABLED, \
    DEFAULT_URL_SIGNATURE_ENABLED
from qr_code.qrcode.serve import make_qr_code_url
from qr_code.qrcode.utils import QRCodeOptions


def make_qr(text: Any, qr_code_options: QRCodeOptions):
    """Creates a QR code

    :rtype: segno.QRCode
    """
    # WARNING: For compatibility reasons, we still allow to pass __proxy__ class (lazy string). Moreover, it would be OK to pass anything that has __str__
    # attribute (e. g. class instance that handles phone numbers).
    if isinstance(text, (bytes, int)):
        return segno.make(text, **qr_code_options.kw_make())
    else:
        return segno.make(str(text), **qr_code_options.kw_make())


def make_qr_code_image(text: Any, qr_code_options: QRCodeOptions) -> bytes:
    """
    Returns a bytes object representing a QR code image for the provided text.

    :param str text: The text to encode
    :param qr_code_options: Options to create and serialize the QR code.
    :rtype: bytes
    """
    qr = make_qr(text, qr_code_options)
    out = io.BytesIO()
    qr.save(out, **qr_code_options.kw_save())
    return out.getvalue()


def make_embedded_qr_code(text: Any, qr_code_options: QRCodeOptions) -> str:
    """
    Generates a <svg> or <img> tag representing the QR code for the given text.
    This tag can be embedded into an HTML document.
    """
    qr = make_qr(text, qr_code_options)
    kw = qr_code_options.kw_save()
    # Pop the image format from the keywords since qr.png_data_uri / qr.svg_inline
    # set it automatically
    kw.pop('kind')
    if qr_code_options.image_format == 'png':
        return mark_safe('<img src="{0}" alt="{1}">'
                         .format(qr.png_data_uri(**kw), escape(text)))
    return mark_safe(qr.svg_inline(**kw))


def make_qr_code_with_args(text: Any, qr_code_args: dict) -> str:
    options = _options_from_args(qr_code_args)
    return make_embedded_qr_code(text, options)


def make_qr_code_url_with_args(text: Any, qr_code_args: dict) -> str:
    cache_enabled = qr_code_args.pop('cache_enabled', DEFAULT_CACHE_ENABLED)
    if not isinstance(cache_enabled, bool):
        cache_enabled = not cache_enabled == 'False'
    url_signature_enabled = qr_code_args.pop('url_signature_enabled', DEFAULT_URL_SIGNATURE_ENABLED)
    if not isinstance(url_signature_enabled, bool):
        url_signature_enabled = not url_signature_enabled == 'False'
    options = _options_from_args(qr_code_args)
    return make_qr_code_url(text, options, cache_enabled=cache_enabled,
                            url_signature_enabled=url_signature_enabled)


def _options_from_args(args: Mapping) -> QRCodeOptions:
    """Returns a QRCodeOptions instance from the provided arguments.
    """
    options = args.get('options')
    if options:
        if not isinstance(options, QRCodeOptions):
            raise TypeError('The options argument must be of type QRCodeOptions.')
    else:
        # Convert the string "None" into None
        kw = {k: v if v != 'None' else None for k, v in args.items()}
        options = QRCodeOptions(**kw)
    return options
