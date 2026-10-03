"""Tools for generating QR codes. This module depends on the Segno library."""
import base64
import hashlib
import io
import json
import re
from collections.abc import Mapping
from typing import Any

from django.conf import settings
from django.core.cache import caches
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.utils.html import escape
from django.utils.safestring import mark_safe
import segno
from pydantic import validate_call

from qr_code.qrcode import PYDANTIC_CONFIG
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
    return _serialize_qr(make_qr(data, qr_code_options, force_text=force_text), qr_code_options, data)


def _serialize_qr(qr: segno.QRCode, qr_code_options: QRCodeOptions, data: Any) -> bytes:
    """
    Serializes the QR code into an image (bytes), as specified by `qr_code_options`.

    The Swiss cross is drawn on the QR code if `data` is the data of a Swiss QR code.
    """
    is_swiss_qr_code = _is_swiss_qr_code_data(data)
    if is_swiss_qr_code and qr_code_options.image_format == "png":
        return _make_swiss_qr_code_png(qr, qr_code_options)
    out = io.BytesIO()
    qr.save(out, **qr_code_options.kw_save())
    image = out.getvalue()
    if is_swiss_qr_code:
        image = _add_swiss_cross_to_svg(image.decode("utf-8"), qr, qr_code_options).encode("utf-8")
    return image


# Header of the data of a Swiss QR code: QR type "SPC", version 2.x and coding type 1, separated by line breaks.
_SWISS_QR_CODE_HEADER_RE = re.compile(r"SPC\r?\n02[0-9]{2}\r?\n1\r?\n")


def _is_swiss_qr_code_data(data: Any) -> bool:
    """Tells whether the data to encode is the data of a Swiss QR code (see `SwissQrBill`), which requires a Swiss cross."""
    if isinstance(data, (bytes, bytearray)):
        header = bytes(data[:16]).decode("latin-1")
    else:
        header = str(data)[:16]
    return _SWISS_QR_CODE_HEADER_RE.match(header) is not None


def _swiss_cross_shapes(origin: float, symbol_size: float, whole_pixels: bool) -> list[tuple[float, float, float, float, str]]:
    """
    Returns the squares and rectangles of the Swiss cross in the middle of a Swiss QR code, as tuples (x, y, width, height, color).

    The Swiss cross measures 7 x 7 mm on a symbol of 46 x 46 mm (without the quiet zone). It is made of a black square with a white
    border of 0.5 mm, and of a white cross whose arms are 1/6 of the Swiss cross wide and 5/9 of it long altogether.

    :param origin: The position of the top left corner of the symbol, after the quiet zone.
    :param symbol_size: The size of the symbol, without the quiet zone.
    :param whole_pixels: Tells whether the sizes must be rounded so that the shapes are centered on whole pixels.
    """

    def size(ratio: float, reference: float) -> float:
        value = reference * ratio
        if whole_pixels:
            # Round to a size with the same parity as the reference, so that the shape is centered on whole pixels.
            value = reference + 2 * round((value - reference) / 2)
        return value

    cross_size = size(7 / 46, symbol_size)
    black_square_size = size(6 / 7, cross_size)
    arm_width = size(1 / 6, cross_size)
    arm_length = size(5 / 9, cross_size)
    center = origin + symbol_size / 2
    shapes = []
    for width, height, color in [
        (cross_size, cross_size, "white"),
        (black_square_size, black_square_size, "black"),
        (arm_length, arm_width, "white"),
        (arm_width, arm_length, "white"),
    ]:
        shapes.append((center - width / 2, center - height / 2, width, height, color))
    return shapes


def _make_swiss_qr_code_png(qr: segno.QRCode, qr_code_options: QRCodeOptions) -> bytes:
    """Serializes the Swiss QR code `qr` into a PNG image with the Swiss cross in the middle."""
    # Imported here so that only the processes drawing a Swiss cross on a PNG pay for the import of Pillow.
    from PIL import Image, ImageDraw

    # Segno does not compress the PNG, which Pillow compresses once the Swiss cross is drawn on it.
    png = io.BytesIO()
    qr.save(png, **qr_code_options.kw_save(), compresslevel=0)
    png.seek(0)
    image: Image.Image = Image.open(png)
    if "transparency" in image.info:
        # The Swiss cross must be opaque, even if the transparent color is white or black.
        image = image.convert("LA" if image.mode in ("1", "L") else "RGBA")
    # Otherwise, the mode of the image is kept: if a palette image with custom colors does not contain black and white, they are
    # added to its palette when drawing.
    modules = qr.symbol_size(scale=1, border=0)[0]
    module_size = image.width / (modules + 2 * qr_code_options.border)
    draw = ImageDraw.Draw(image)
    for x, y, width, height, color in _swiss_cross_shapes(
        round(qr_code_options.border * module_size), round(modules * module_size), whole_pixels=True
    ):
        draw.rectangle((x, y, x + width - 1, y + height - 1), fill=color)
    out = io.BytesIO()
    image.save(out, format="PNG", optimize=True)
    return out.getvalue()


def _add_swiss_cross_to_svg(svg: str, qr: segno.QRCode, qr_code_options: QRCodeOptions) -> str:
    def number(value: float) -> str:
        return f"{value:.3f}".rstrip("0").rstrip(".")

    modules = qr.symbol_size(scale=1, border=0)[0]
    paths = "".join(
        f'<path fill="{"#fff" if color == "white" else "#000"}" d="M{number(x)} {number(y)}h{number(width)}v{number(height)}h-{number(width)}z"/>'
        for x, y, width, height, color in _swiss_cross_shapes(qr_code_options.border, modules, whole_pixels=False)
    )
    # The shapes are drawn in modules, like the QR code, and then scaled like the QR code.
    scale = number(float(qr_code_options.kw_save()["scale"]))
    end = svg.rindex("</svg>")
    return f'{svg[:end]}<g transform="scale({scale})">{paths}</g>{svg[end:]}'


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
    if alt_text is None and (use_data_uri_for_svg or qr_code_options.image_format == "png"):
        if isinstance(data, bytes):
            alt_text = ""
            # Try the encoding of the QR code first (any codec name or spelling supported by Python), then the defaults.
            encodings = ["utf-8", "iso-8859-1", "shift-jis"]
            if qr_code_options.encoding:
                encodings.insert(0, qr_code_options.encoding)
            for e in encodings:
                try:
                    alt_text = data.decode(e)
                    break
                except (UnicodeDecodeError, LookupError):
                    pass
        else:
            alt_text = str(data)

    if class_names:
        class_attr = f' class="{escape(class_names)}"'
    else:
        class_attr = ""

    if qr_code_options.image_format == "png":
        png_b64_data = base64.b64encode(_serialize_qr(qr, qr_code_options, data)).decode("utf-8")
        return mark_safe(f'<img src="data:image/png;base64,{png_b64_data}" alt="{escape(alt_text)}"{class_attr}>')

    if use_data_uri_for_svg:
        svg_b64_data = base64.b64encode(_serialize_qr(qr, qr_code_options, data)).decode("utf-8")
        return mark_safe(f'<img src="data:image/svg+xml;base64,{svg_b64_data}" alt="{escape(alt_text)}"{class_attr}>')
    kw = qr_code_options.kw_save()
    # Pop the image format from the keywords since qr.svg_inline sets it automatically.
    kw.pop("kind")
    svg = qr.svg_inline(**kw)
    if _is_swiss_qr_code_data(data):
        svg = _add_swiss_cross_to_svg(svg, qr, qr_code_options)
    return mark_safe(svg)


def get_or_make_cached_embedded_qr_code(
        data,
        qr_code_options,
        force_text: bool = True,
        use_data_uri_for_svg: bool = False,
        alt_text: None | str = None,
        class_names: None | str = None,
        cache_timeout: None | float = DEFAULT_TIMEOUT):
    """
    Same as `make_embedded_qr_code` but caches the result the first time is it called for a given set of args and returned the cached result. It raises an exception when the `QR_CODE_CACHE_ALIAS` setting is not set.

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
        raise RuntimeError("QR_CODE_CACHE_ALIAS must be set in settings.")

    url = make_qr_code_url(data=data, qr_code_options=qr_code_options, force_text=force_text, cache_enabled=True, url_signature_enabled=False)
    # To simplify the logic, use the QR URL without a signature as the base for the cache key, and append the
    # arguments that affect the generated markup but are not encoded in the URL (data URI for SVG, alt text and CSS
    # classes). JSON serialization keeps these values unambiguous (e.g., None vs. empty string). Ensure that the resulting
    # key remains reasonably sized and contains only characters compatible with all relevant cache backends by using MD5 hash.
    key_source = json.dumps(["qr", url, use_data_uri_for_svg, alt_text, class_names])
    key = hashlib.md5(key_source.encode()).hexdigest()
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
    # The boolean arguments may be strings (e.g., "False", "false", "0" or "no"), which make_qr_code_url converts.
    cache_enabled = _from_tag_arg(qr_code_args.pop("cache_enabled", None))
    url_signature_enabled = _from_tag_arg(qr_code_args.pop("url_signature_enabled", None))
    options = _options_from_args(qr_code_args)
    return make_qr_code_url(data, options, force_text=force_text, cache_enabled=cache_enabled, url_signature_enabled=url_signature_enabled)


def _from_tag_arg(value: Any) -> Any:
    """Converts the string "None", which a template tag argument may be, into None."""
    return None if value == "None" else value


def _options_from_args(args: Mapping) -> QRCodeOptions:
    """Returns a QRCodeOptions instance from the provided arguments."""
    options = args.get("options")
    if options:
        if not isinstance(options, QRCodeOptions):
            raise TypeError("The options argument must be of type QRCodeOptions.")
    else:
        kw: dict[str, Any] = {k: _from_tag_arg(v) for k, v in args.items()}
        options = QRCodeOptions(**kw)
    return options
