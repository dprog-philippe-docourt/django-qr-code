import re

from django.utils.html import escape


def get_base64_png_image_template(alt_text: None | str = None, class_names: None | str = None) -> str:
    if alt_text is None:
        alt_text = "Hello World!"
    template = f'<img src="data:image/png;base64,%s" alt="{escape(alt_text)}"'
    if class_names:
        template += f' class="{class_names}"'
    return template + ">"


def get_base64_svg_image_template(alt_text: None | str = None, class_names: None | str = None) -> str:
    if alt_text is None:
        alt_text = "Hello World!"
    template = f'<img src="data:image/svg+xml;base64,%s" alt="{escape(alt_text)}"'
    if class_names:
        template += f' class="{class_names}"'
    return template + ">"


IMAGE_TAG_BASE64_DATA_RE = re.compile(r"data:image/(png|svg\+xml);base64,(?P<data>[\w/+=]+)")
TEST_TEXT = "Hello World!"
COMPLEX_TEST_TEXT = "/%+¼@#=<>àé"

OVERRIDE_CACHES_SETTING = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
    "qr-code": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "qr-code-cache", "TIMEOUT": 3600},
}
SVG_REF_SUFFIX = ".ref.svg"
PNG_REF_SUFFIX = ".ref.png"

# Set this flag to True for writing the new version of each reference image in tests/resources while running the tests.
REFRESH_REFERENCE_IMAGES = True
