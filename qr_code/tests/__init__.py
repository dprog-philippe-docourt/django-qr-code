import re

BASE64_PNG_IMAGE_TEMPLATE = '<img src="data:image/png;base64,%s" alt="Hello World!">'
IMAGE_TAG_BASE64_DATA_RE = re.compile(r"data:image/png;base64,(?P<data>[\w/+=]+)")
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
