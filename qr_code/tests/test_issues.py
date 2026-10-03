import subprocess
import sys
import textwrap

from decimal import Decimal

from django.template import Context, Template
from django.test import SimpleTestCase

from qr_code.qrcode.maker import make_embedded_qr_code, make_qr_code_image
from qr_code.qrcode.serve import make_qr_code_url
from qr_code.qrcode.utils import QRCodeOptions, VCard


class TestIssues(SimpleTestCase):
    def test_reverse_lazy_url(self):
        from django.urls import reverse, reverse_lazy

        options = QRCodeOptions(image_format="svg", size=1)
        url1 = make_qr_code_url(reverse("qr_code:serve_qr_code_image"), options)
        url2 = make_qr_code_url(reverse_lazy("qr_code:serve_qr_code_image"), options)
        self.assertEqual(url1, url2)

        svg1 = make_embedded_qr_code(reverse("qr_code:serve_qr_code_image"), options)
        svg2 = make_embedded_qr_code(reverse_lazy("qr_code:serve_qr_code_image"), options)
        self.assertEqual(svg1, svg2)

    def test_import_without_secret_key(self):
        # Importing the app modules must not access the settings, e.g., for running management commands such as
        # collectstatic in an environment where SECRET_KEY is not set.
        script = textwrap.dedent(
            """
            import django
            from django.conf import settings

            settings.configure(INSTALLED_APPS=["django.contrib.auth", "django.contrib.contenttypes", "qr_code"])
            django.setup()

            import qr_code.qrcode.serve
            import qr_code.qrcode.maker
            import qr_code.templatetags.qr_code
            import qr_code.views
            import qr_code.urls
            """
        )
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_url_token_is_stable(self):
        # The random part of the token must be stable so that identical QR codes get identical URLs, which is required
        # for the server-side cache and the HTTP caching (ETag) to be effective.
        options = QRCodeOptions(image_format="png", size=1)
        self.assertEqual(make_qr_code_url("Stable token", options), make_qr_code_url("Stable token", options))

    def test_unknown_size_letter_falls_back_to_default_size(self):
        self.assertEqual(make_embedded_qr_code("Unknown size", QRCodeOptions(size="xyz")), make_embedded_qr_code("Unknown size", QRCodeOptions()))
        self.assertEqual(
            make_qr_code_image("Unknown size", QRCodeOptions(size="xyz", image_format="png")),
            make_qr_code_image("Unknown size", QRCodeOptions(image_format="png")),
        )

    def test_vcard_without_zipcode(self):
        self.assertNotIn("ADR:", VCard(name="John Doe").make_qr_code_data())
        self.assertIn("ADR:;;;;;0;", VCard(name="John Doe", zipcode=0).make_qr_code_data())
        self.assertIn("ADR:;;;;;1234;", VCard(name="John Doe", zipcode=1234).make_qr_code_data())

    def test_alt_text_for_bytes_with_any_encoding(self):
        for encoding in ("UTF-8", "Latin-1", "cp1252", "unknown-encoding"):
            with self.subTest(encoding=encoding):
                data = "été".encode("utf-8" if encoding == "UTF-8" else "latin-1")
                options = QRCodeOptions(image_format="png", encoding=encoding)
                self.assertIn('alt="été"', make_embedded_qr_code(data, options, force_text=False))

    def test_decimal_size_given_as_string(self):
        self.assertEqual(QRCodeOptions(size="2.5")._size_as_number(), Decimal("2.5"))
        self.assertEqual(
            Template('{% load qr_code %}{% qr_from_text "Decimal size" size="2.5" %}').render(Context()),
            make_embedded_qr_code("Decimal size", QRCodeOptions(size=Decimal("2.5"))),
        )
        # Invalid sizes fall back to the default size.
        for size in ("0.001", "-2.5", "NaN", "Infinity", "2.5.1"):
            with self.subTest(size=size):
                self.assertEqual(QRCodeOptions(size=size)._size_as_number(), 18)
