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
