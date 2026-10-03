"""Tests for the view serving QR code images."""
from django.contrib.auth.models import AnonymousUser, User
from django.core.cache import caches
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, SimpleTestCase, override_settings

from qr_code.qrcode import constants
from qr_code.qrcode.serve import make_qr_code_url
from qr_code.qrcode.utils import QRCodeOptions
from qr_code.tests import OVERRIDE_CACHES_SETTING, TEST_TEXT
from qr_code.views import serve_qr_code_image


class TestServeQRCodeImage(SimpleTestCase):
    def assert_bad_request(self, url):
        with self.assertLogs("django.security.SuspiciousOperation", "ERROR"):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

    @override_settings(
        CACHES={
            "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
            "qr-code": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "qr-code-cache-without-timeout"},
        },
        QR_CODE_CACHE_ALIAS="qr-code",
    )
    def test_cache_without_timeout_setting(self):
        response = self.client.get(make_qr_code_url(TEST_TEXT))
        self.assertEqual(response.status_code, 200)
        # The default timeout of the cache applies.
        self.assertIn("max-age=300", response["Cache-Control"])

    def test_unknown_query_arguments_are_ignored(self):
        # E.g., tracking parameters added to the URL by a third party.
        url = make_qr_code_url(TEST_TEXT, cache_enabled=False)
        response = self.client.get(f"{url}&utm_source=newsletter&fbclid=abc")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, self.client.get(url).content)

    def test_invalid_boolean_query_arguments(self):
        url = make_qr_code_url(TEST_TEXT, cache_enabled=False)
        for name in ("cache_enabled", "micro", "eci", "boost_error"):
            for value in ("abc", ""):
                with self.subTest(name=name, value=value):
                    self.assert_bad_request(f"{url}&{name}={value}")

    def test_invalid_option_values(self):
        url = make_qr_code_url(TEST_TEXT, cache_enabled=False)
        for query in ("border=abc", "dark_color=not-a-color", "encoding=no-such-codec", "eci=1&encoding=no-such-codec"):
            with self.subTest(query=query):
                self.assert_bad_request(f"{url}&{query}")

    def test_options_that_cannot_be_applied_to_the_data(self):
        for data, options in (("x" * 500, QRCodeOptions(version=1)), ("1", QRCodeOptions(micro=True, error_correction="H"))):
            with self.subTest(options=options.kw_make()):
                self.assert_bad_request(make_qr_code_url(data, options, cache_enabled=False))

    @override_settings(
        CACHES=OVERRIDE_CACHES_SETTING,
        QR_CODE_CACHE_ALIAS="qr-code",
        QR_CODE_URL_PROTECTION={constants.ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER: True},
    )
    def test_cached_image_is_not_shared_between_users(self):
        caches["qr-code"].clear()
        url = make_qr_code_url(TEST_TEXT, url_signature_enabled=False)
        request = RequestFactory().get(url)
        request.user = User(pk=1, username="registered-user")
        self.assertEqual(serve_qr_code_image(request).status_code, 200)
        # The image is now cached for the registered user, but it must not be served to an anonymous user.
        request = RequestFactory().get(url)
        request.user = AnonymousUser()
        with self.assertRaises(PermissionDenied):
            serve_qr_code_image(request)
