import base64

from django.test import SimpleTestCase

from qr_code.qrcode.maker import make_embedded_qr_code
from qr_code.qrcode.utils import QRCodeOptions
from qr_code.templatetags.qr_code import qr_from_text, qr_for_email
from qr_code.tests import TEST_TEXT, REFRESH_REFERENCE_IMAGES, IMAGE_TAG_BASE64_DATA_RE, get_base64_png_image_template, \
    get_base64_svg_image_template
from qr_code.tests.utils import write_png_content_to_file, get_png_content_from_file_name, write_svg_content_to_file, \
    get_svg_content_from_file_name

TEST_ALT_TEXTS = [None, "", "alternative text", "quotes test: ', \""]
TEST_ALT_TEXT_NAMES = ["none", "empty", "alternative-text", "quotes"]
TEST_CLASS_NAMES = [None, "", "error", "ui fluid segment"]


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

    def test_embedded_classes_png(self):
        for i in range(len(TEST_CLASS_NAMES)):
            class_names = TEST_CLASS_NAMES[i]
            class_name = "none" if class_names is None else "empty" if class_names == "" else class_names.replace(" ", "_")
            print("Testing PNG with classes: %s" % class_name)
            base_ref_file_name = "qrfromtext_embedded_class"
            result_file_name = f"{base_ref_file_name}_{class_name}"
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(image_format="png"), class_names=class_names)
            qr2 = qr_from_text(TEST_TEXT, image_format="png", class_names=class_names)
            qr3 = qr_from_text(TEST_TEXT, options=QRCodeOptions(image_format="png"), class_names=class_names)
            if REFRESH_REFERENCE_IMAGES:
                match = IMAGE_TAG_BASE64_DATA_RE.search(qr1)
                source_image_data = match.group("data")
                write_png_content_to_file(result_file_name, base64.b64decode(source_image_data))
            result = base64.b64encode(get_png_content_from_file_name(result_file_name)).decode("utf-8")
            self.assertEqual(qr1, qr2)
            self.assertEqual(qr1, qr3)
            self.assertEqual(qr1, get_base64_png_image_template(class_names=class_names) % result)

            base_ref_file_name = "qrforemail_embedded_class"
            test_mail = "test@domain.com"
            result_file_name = f"{base_ref_file_name}_{class_name}"
            qr1 = make_embedded_qr_code(f"mailto:{test_mail}", QRCodeOptions(image_format="png"), class_names=class_names)
            qr2 = qr_for_email(test_mail, image_format="png", class_names=class_names)
            qr3 = qr_for_email(test_mail, options=QRCodeOptions(image_format="png"), class_names=class_names)
            if REFRESH_REFERENCE_IMAGES:
                match = IMAGE_TAG_BASE64_DATA_RE.search(qr1)
                source_image_data = match.group("data")
                write_png_content_to_file(result_file_name, base64.b64decode(source_image_data))
            result = base64.b64encode(get_png_content_from_file_name(result_file_name)).decode("utf-8")
            self.assertEqual(qr1, qr2)
            self.assertEqual(qr1, qr3)
            self.assertEqual(qr1, get_base64_png_image_template(class_names=class_names, alt_text="mailto:test@domain.com") % result)

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

    def test_embedded_classes_svg(self):
        base_ref_file_name = "qrfromtext_embedded_class"
        for i in range(len(TEST_CLASS_NAMES)):
            class_names = TEST_CLASS_NAMES[i]
            class_name = "none" if class_names is None else "empty" if class_names == "" else class_names.replace(" ", "_")
            print("Testing SVG with classes: %s" % class_name)
            result_file_name = f"{base_ref_file_name}_{class_name}"
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(image_format="svg"), class_names=class_names, use_data_uri_for_svg=True)
            qr2 = qr_from_text(TEST_TEXT, image_format="svg", class_names=class_names, use_data_uri_for_svg=True)
            qr3 = qr_from_text(TEST_TEXT, options=QRCodeOptions(image_format="svg"), class_names=class_names, use_data_uri_for_svg=True)
            if REFRESH_REFERENCE_IMAGES:
                match = IMAGE_TAG_BASE64_DATA_RE.search(qr1)
                source_image_data = match.group("data")
                write_svg_content_to_file(result_file_name, base64.b64decode(source_image_data).decode("utf-8"))
            result = get_svg_content_from_file_name(result_file_name)
            self.assertEqual(qr1, qr2)
            self.assertEqual(qr1, qr3)
            self.assertEqual(qr1, get_base64_svg_image_template(class_names=class_names) % base64.b64encode(result.encode("utf-8")).decode("utf-8"))

            base_ref_file_name = "qrforemail_embedded_class"
            test_mail = "test@domain.com"
            result_file_name = f"{base_ref_file_name}_{class_name}"
            qr1 = make_embedded_qr_code(f"mailto:{test_mail}", QRCodeOptions(image_format="png"),
                                        class_names=class_names)
            qr2 = qr_for_email(test_mail, image_format="png", class_names=class_names)
            qr3 = qr_for_email(test_mail, options=QRCodeOptions(image_format="png"), class_names=class_names)
            if REFRESH_REFERENCE_IMAGES:
                match = IMAGE_TAG_BASE64_DATA_RE.search(qr1)
                source_image_data = match.group("data")
                write_png_content_to_file(result_file_name, base64.b64decode(source_image_data))
            result = base64.b64encode(get_png_content_from_file_name(result_file_name)).decode("utf-8")
            self.assertEqual(qr1, qr2)
            self.assertEqual(qr1, qr3)
            self.assertEqual(qr1, get_base64_png_image_template(alt_text="mailto:test@domain.com", class_names=class_names) % result)

    def test_embedded_data_uri_svg(self):
        base_ref_file_name = "qrfromtext_embedded_data_uri"
        for use_data_uri_for_svg in [True, False]:
            alt_text_name = str(use_data_uri_for_svg).lower()
            print("Testing SVG with data URI: %s" % alt_text_name)
            result_file_name = f"{base_ref_file_name}_{alt_text_name}"
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(image_format="svg"), use_data_uri_for_svg=use_data_uri_for_svg)
            qr2 = qr_from_text(TEST_TEXT, image_format="svg", use_data_uri_for_svg=use_data_uri_for_svg)
            qr3 = qr_from_text(TEST_TEXT, options=QRCodeOptions(image_format="svg"), use_data_uri_for_svg=use_data_uri_for_svg)
            if REFRESH_REFERENCE_IMAGES:
                if use_data_uri_for_svg:
                    match = IMAGE_TAG_BASE64_DATA_RE.search(qr1)
                    source_image_data = match.group("data")
                    write_svg_content_to_file(result_file_name, base64.b64decode(source_image_data).decode("utf-8"))
                else:
                    write_svg_content_to_file(result_file_name, qr1)
            result = get_svg_content_from_file_name(result_file_name)
            self.assertEqual(qr1, qr2)
            self.assertEqual(qr1, qr3)
            if use_data_uri_for_svg:
                self.assertEqual(qr1, get_base64_svg_image_template() % base64.b64encode(result.encode("utf-8")).decode("utf-8"))
            else:
                self.assertEqual(qr1, result)
