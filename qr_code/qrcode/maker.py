"""Tools for generating QR codes. This module depends on the Segno library."""
import base64
import hashlib
import io
from typing import Mapping, Any

from django.conf import settings
from django.core.cache import caches
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.utils.html import escape
from django.utils.safestring import mark_safe
import segno
from pydantic import validate_call

from qr_code.qrcode import PYDANTIC_CONFIG
from qr_code.qrcode.constants import DEFAULT_CACHE_ENABLED, DEFAULT_URL_SIGNATURE_ENABLED
from qr_code.qrcode.serve import make_qr_code_url
from qr_code.qrcode.utils import QRCodeOptions


@validate_call(config=PYDANTIC_CONFIG)
def make_qr(data: Any, qr_code_options: QRCodeOptions, force_text: bool = True):
    """Creates a QR code that encodes the given `data` with the given `qr_code_options`.

    :param str data: The data to encode
    :param qr_code_options: Options to create and serialize the QR code.
    :param bool force_text: Tells whether we want to force the `data` to be considered as text string and encoded in byte mode.
    :rtype: segno.QRCode
    """
    # WARNING: For compatibility reasons, we still allow to pass __proxy__ class (lazy string). Moreover, it would be
    # OK to pass anything that has __str__ attribute (e.g. class instance that handles phone numbers).
    if force_text:
        return segno.make(str(data), **qr_code_options.kw_make(), mode="byte")
    return segno.make(data, **qr_code_options.kw_make())


@validate_call(config=PYDANTIC_CONFIG)
def make_qr_code_image(data: Any, qr_code_options: QRCodeOptions, force_text: bool = True) -> bytes:
    """
    Creates a bytes object representing a QR code image for the provided `data`.

    :param str data: The data to encode
    :param qr_code_options: Options to create and serialize the QR code.
    :param bool force_text: Tells whether we want to force the `data` to be considered as text string and encoded in byte mode.
    :rtype: bytes
    """
    qr = make_qr(data, qr_code_options, force_text=force_text)
    out = io.BytesIO()
    qr.save(out, **qr_code_options.kw_save())
    return out.getvalue()


@validate_call(config=PYDANTIC_CONFIG)
def make_embedded_qr_code(
    data: Any,
    qr_code_options: QRCodeOptions,
    force_text: bool = True,
    use_data_uri_for_svg: bool = False,
    alt_text: None | str = None,
    class_names: None | str = None,
) -> str:
    """
    Generate an HTML `<svg>` or `<img>` element that renders *data* as a QR code.

    If `image_format == "svg"` **and** `use_data_uri_for_svg` is `True`, the function returns an
    `<img>` tag whose `src` is a base-64-encoded SVG data-URI.
    Otherwise, it returns inline `<svg>` markup.

    ### Accessibility

    * `alt_text` populates the `alt` attribute.
      * `None` (default) → uses `str(data)`
      * `""` → explicit empty `alt`
      The value is automatically HTML-escaped.

    ### Styling

    * `class_names` populates the `class` attribute.
      If `None` or an empty string, the attribute is omitted.

    Parameters
    ----------
    data : Any
        Payload to encode in the QR code.
    qr_code_options : QRCodeOptions
        Rendering and encoding options.
    force_text : bool
        If `True`, convert *data* to `str` before encoding; otherwise raw bytes,
        integers, etc. are accepted.
    use_data_uri_for_svg : bool
        When generating SVG, return a data-URI `<img>` instead of inline SVG.
    alt_text : str | None
        Alternative text for screen readers.
    class_names : str | None
        Space-separated CSS classes for the generated element.

    Returns
    -------
    str
        Markup for an HTML `<svg>` or `<img>` element containing the QR code.

    Notes
    -----
    * The returned fragment is ready to insert into any HTML document.
    * All text is HTML-escaped to prevent injection.
"""

    qr = make_qr(data, qr_code_options, force_text=force_text)
    kw = qr_code_options.kw_save()
    # Pop the image format from the keywords since qr.png_data_uri / qr.svg_inline
    # set it automatically
    kw.pop("kind")
    if alt_text is None and (use_data_uri_for_svg or qr_code_options.image_format == "png"):
        if isinstance(data, bytes):
            alt_text = ""
            encodings = ["utf-8", "iso-8859-1", "shift-jis"]
            if qr_code_options.encoding:
                ei = encodings.index(qr_code_options.encoding)
                if ei > 0:
                    encodings[ei] = encodings[0]
                    encodings[0] = qr_code_options.encoding
            for e in encodings:
                try:
                    alt_text = data.decode(e)
                    break
                except UnicodeDecodeError:
                    pass
        elif not isinstance(data, str):
            alt_text = str(data)
        else:
            alt_text = data

    if class_names:
        class_attr = f' class="{class_names}"'
    else:
        class_attr = ""

    if qr_code_options.image_format == "png":
        return mark_safe(f'<img src="{qr.png_data_uri(**kw)}" alt="{escape(alt_text)}"{class_attr}>')

    if use_data_uri_for_svg:
        out = io.BytesIO()
        qr.save(out, **qr_code_options.kw_save())
        svg_path = out.getvalue()
        svg_b64_data = base64.b64encode(svg_path).decode("utf-8")
        html = f'<img src="data:image/svg+xml;base64,{svg_b64_data}" alt="{escape(alt_text)}"{class_attr}>'
        return mark_safe(html)
    else:
        return mark_safe(qr.svg_inline(**kw))


def get_or_make_cached_embedded_qr_code(
        data,
        qr_code_options,
        force_text: bool = True,
        use_data_uri_for_svg: bool = False,
        alt_text: None | str = None,
        class_names: None | str = None,
        cache_timeout: None | int | object = DEFAULT_TIMEOUT):
    """
    Same as `make_embedded_qr_code`but caches the result the first time is it called for a given set of args and returned the cached result. It raises an exception when the `QR_CODE_CACHE_ALIAS` setting is not set.

    :param data: See `make_embedded_qr_code`.
    :param qr_code_options: See `make_embedded_qr_code`.
    :param force_text: See `make_embedded_qr_code`.
    :param use_data_uri_for_svg: See `make_embedded_qr_code`.
    :param alt_text: See `make_embedded_qr_code`.
    :param class_names: See `make_embedded_qr_code`.
    :param cache_timeout: Cache timeout in seconds. Passing in `None` for timeout will cache the value forever. A timeout of 0 won’t cache the value.
    :return: See `make_embedded_qr_code`.
    """
    cache_name = getattr(settings, "QR_CODE_CACHE_ALIAS", None)
    if not cache_name:
        raise RuntimeError(f"QR_CODE_CACHE_ALIAS must be set in settings.")

    url = make_qr_code_url(data=data, qr_code_options=qr_code_options, force_text=force_text, cache_enabled=True, url_signature_enabled=False)
    # To simplify the logic, use the QR URL without a signature as the base for the cache key, and append the
    # data_uri_for_svg value separately, since it is not encoded in the URL. Ensure that the resulting key remains
    # reasonably sized and contains only characters compatible with all relevant cache backends by using MD5 hash.
    key = hashlib.md5(f"qr.{url}&data_uri_for_svg={use_data_uri_for_svg}".encode()).hexdigest()
    cache = caches[cache_name]
    qr_code = cache.get(key)
    if qr_code is None:
        qr_code = make_embedded_qr_code(data=data, qr_code_options=qr_code_options, force_text=force_text,
                                        use_data_uri_for_svg=use_data_uri_for_svg, alt_text=alt_text,
                                        class_names=class_names)
        cache.set(key, qr_code, timeout=cache_timeout)
    return qr_code


def make_qr_code_with_args(
    data: Any,
    qr_code_args: dict,
    force_text: bool = True,
    use_data_uri_for_svg: bool = False,
    alt_text: None | str = None,
    class_names: None | str = None,
) -> str:
    options = _options_from_args(qr_code_args)
    return make_embedded_qr_code(
        data, options, force_text=force_text, use_data_uri_for_svg=use_data_uri_for_svg, alt_text=alt_text, class_names=class_names
    )


def make_qr_code_url_with_args(data: Any, qr_code_args: dict, force_text: bool = True) -> str:
    cache_enabled = qr_code_args.pop("cache_enabled", DEFAULT_CACHE_ENABLED)
    if not isinstance(cache_enabled, bool):
        cache_enabled = not cache_enabled == "False"
    url_signature_enabled = qr_code_args.pop("url_signature_enabled", DEFAULT_URL_SIGNATURE_ENABLED)
    if not isinstance(url_signature_enabled, bool):
        url_signature_enabled = not url_signature_enabled == "False"
    options = _options_from_args(qr_code_args)
    return make_qr_code_url(data, options, force_text=force_text, cache_enabled=cache_enabled, url_signature_enabled=url_signature_enabled)


def _options_from_args(args: Mapping) -> QRCodeOptions:
    """Returns a QRCodeOptions instance from the provided arguments."""
    options = args.get("options")
    if options:
        if not isinstance(options, QRCodeOptions):
            raise TypeError("The options argument must be of type QRCodeOptions.")
    else:
        # Convert the string "None" into None
        kw = {k: v if v != "None" else None for k, v in args.items()}
        options = QRCodeOptions(**kw)
    return options
