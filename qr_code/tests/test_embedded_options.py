import base64

from django.test import SimpleTestCase

from qr_code.qrcode.maker import make_embedded_qr_code
from qr_code.qrcode.utils import QRCodeOptions
from qr_code.templatetags.qr_code import qr_from_text
from qr_code.tests import TEST_TEXT, REFRESH_REFERENCE_IMAGES, IMAGE_TAG_BASE64_DATA_RE, get_base64_png_image_template, \
    get_base64_svg_image_template
from qr_code.tests.utils import write_png_content_to_file, get_png_content_from_file_name, write_svg_content_to_file, \
    get_svg_content_from_file_name

TEST_ALT_TEXTS = [None, "", "alternative text", "quotes test: ', \""]
TEST_ALT_TEXT_NAMES = ["none", "empty", "alternative-text", "quotes"]


class TestQREmbeddedImageResult(SimpleTestCase):
    """
    Ensures that produced QR codes in PNG format coincide with verified references.

    The tests cover direct call to tag function, rendering of tag, and direct call to qr_code API.
    """

    def setUp(self):
        self.maxDiff = None

    def test_embedded_alt_text_png(self):
        base_ref_file_name = "qrfromtext_embedded_alt_text"
        for i in range(len(TEST_ALT_TEXTS)):
            alt_text = TEST_ALT_TEXTS[i]
            alt_text_name = TEST_ALT_TEXT_NAMES[i]
            print("Testing PNG with alt text: %s" % alt_text_name)
            result_file_name = f"{base_ref_file_name}_{alt_text_name}"
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(image_format="png"), alt_text=alt_text)
            qr2 = qr_from_text(TEST_TEXT, image_format="png", alt_text=alt_text)
            qr3 = qr_from_text(TEST_TEXT, options=QRCodeOptions(image_format="png"), alt_text=alt_text)
            if REFRESH_REFERENCE_IMAGES:
                match = IMAGE_TAG_BASE64_DATA_RE.search(qr1)
                source_image_data = match.group("data")
                write_png_content_to_file(result_file_name, base64.b64decode(source_image_data))
            result = base64.b64encode(get_png_content_from_file_name(result_file_name)).decode("utf-8")
            self.assertEqual(qr1, qr2)
            self.assertEqual(qr1, qr3)
            self.assertEqual(qr1, get_base64_png_image_template(alt_text) % result)

    def test_embedded_alt_text_svg(self):
        base_ref_file_name = "qrfromtext_embedded_alt_text"
        for i in range(len(TEST_ALT_TEXTS)):
            alt_text = TEST_ALT_TEXTS[i]
            alt_text_name = TEST_ALT_TEXT_NAMES[i]
            print("Testing SVG with alt text: %s" % alt_text_name)
            result_file_name = f"{base_ref_file_name}_{alt_text_name}"
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(image_format="svg"), alt_text=alt_text, use_data_uri_for_svg=True)
            qr2 = qr_from_text(TEST_TEXT, image_format="svg", alt_text=alt_text, use_data_uri_for_svg=True)
            qr3 = qr_from_text(TEST_TEXT, options=QRCodeOptions(image_format="svg"), alt_text=alt_text, use_data_uri_for_svg=True)
            if REFRESH_REFERENCE_IMAGES:
                match = IMAGE_TAG_BASE64_DATA_RE.search(qr1)
                source_image_data = match.group("data")
                write_svg_content_to_file(result_file_name, base64.b64decode(source_image_data).decode("utf-8"))
            result = get_svg_content_from_file_name(result_file_name)
            self.assertEqual(qr1, qr2)
            self.assertEqual(qr1, qr3)
            self.assertEqual(qr1, get_base64_svg_image_template(alt_text) % base64.b64encode(result.encode("utf-8")).decode("utf-8"))
