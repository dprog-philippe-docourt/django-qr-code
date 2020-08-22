"""Tools for generating QR codes. This module depends on the Segno library."""
import io
from django.utils.encoding import force_str
from django.utils.html import escape
from django.utils.safestring import mark_safe
import segno
from qr_code.qrcode.constants import DEFAULT_CACHE_ENABLED, \
    DEFAULT_URL_SIGNATURE_ENABLED
from qr_code.qrcode.serve import make_qr_code_url
from qr_code.qrcode.utils import QRCodeOptions


def make_qr(text, qr_code_options):
    """Creates a QR code

    :rtype: segno.QRCode
    """
    return segno.make(force_str(text), **qr_code_options.kw_make())


def make_qr_code_image(text, qr_code_options):
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


def make_embedded_qr_code(text, qr_code_options):
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


def make_qr_code_with_args(text, qr_code_args):
    options = _options_from_args(qr_code_args)
    return make_embedded_qr_code(text, options)


def make_qr_code_url_with_args(text, qr_code_args):
    cache_enabled = qr_code_args.pop('cache_enabled', DEFAULT_CACHE_ENABLED)
    url_signature_enabled = qr_code_args.pop('url_signature_enabled', DEFAULT_URL_SIGNATURE_ENABLED)
    options = _options_from_args(qr_code_args)
    return make_qr_code_url(text, options, cache_enabled=cache_enabled,
                            url_signature_enabled=url_signature_enabled)


def _options_from_args(args):
    """

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
