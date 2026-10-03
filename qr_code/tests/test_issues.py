import subprocess
import sys
import textwrap

from django.test import SimpleTestCase

from qr_code.qrcode.maker import make_embedded_qr_code
from qr_code.qrcode.serve import make_qr_code_url
from qr_code.qrcode.utils import QRCodeOptions


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
