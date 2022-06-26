"""Tests for qr_code application."""
import os

from django.test import SimpleTestCase
from pydantic import ValidationError

from qr_code.qrcode.constants import (
    DEFAULT_IMAGE_FORMAT,
    DEFAULT_MODULE_SIZE,
    DEFAULT_ERROR_CORRECTION,
    DEFAULT_VERSION,
    DEFAULT_ECI,
    DEFAULT_BOOST_ERROR,
    DEFAULT_ENCODING,
)
from qr_code.qrcode.serve import make_qr_code_url
from qr_code.qrcode.utils import QRCodeOptions
from qr_code.tests import TEST_TEXT, PNG_REF_SUFFIX, SVG_REF_SUFFIX

from qr_code.tests.utils import write_svg_content_to_file, get_resources_path, write_png_content_to_file


class TestApps(SimpleTestCase):
    def test_apps_attributes(self):
        from qr_code.apps import QrCodeConfig

        self.assertEqual(QrCodeConfig.name, "qr_code")
        self.assertEqual(QrCodeConfig.verbose_name, "Django QR Code")


class TestQRCodeOptions(SimpleTestCase):
    def test_qr_code_options(self):
        with self.assertRaises((TypeError, ValidationError)):
            QRCodeOptions(foo="bar")
        options = QRCodeOptions()
        self.assertEqual(options.border, 4)
        self.assertEqual(options.size, DEFAULT_MODULE_SIZE)
        self.assertEqual(options.image_format, DEFAULT_IMAGE_FORMAT)
        self.assertEqual(options.version, DEFAULT_VERSION)
        self.assertEqual(options.error_correction, DEFAULT_ERROR_CORRECTION)
        self.assertEqual(options.eci, DEFAULT_ECI)
        self.assertEqual(options.boost_error, DEFAULT_BOOST_ERROR)
        self.assertEqual(options.encoding.lower(), DEFAULT_ENCODING)
        options = QRCodeOptions(image_format="invalid-image-format")
        self.assertEqual(options.image_format, DEFAULT_IMAGE_FORMAT)

    def test_kw_save(self):
        options = QRCodeOptions(border=0, image_format="png", size=13)
        self.assertDictEqual(options.kw_save(), {"border": 0, "kind": "png", "scale": 13})


class TestWriteResourceData(SimpleTestCase):
    resource_file_base_name = "TestWriteResourceData"

    def test_write_svg(self):
        response = self.client.get(make_qr_code_url(TEST_TEXT))
        image_data = response.content.decode("utf-8")
        write_svg_content_to_file(TestWriteResourceData.resource_file_base_name, image_data)
        file_path_to_remove = os.path.join(get_resources_path(), TestWriteResourceData.resource_file_base_name + SVG_REF_SUFFIX)
        os.remove(file_path_to_remove)

    def test_write_png(self):
        response = self.client.get(make_qr_code_url(TEST_TEXT))
        image_data = response.content
        write_png_content_to_file(TestWriteResourceData.resource_file_base_name, image_data)
        file_path_to_remove = os.path.join(get_resources_path(), TestWriteResourceData.resource_file_base_name + PNG_REF_SUFFIX)
        os.remove(file_path_to_remove)
