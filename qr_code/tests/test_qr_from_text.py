"""Tests for qr_code application."""
import base64
import hashlib
import re
from decimal import Decimal

from itertools import product

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.core.cache import caches
from django.template import Template, Context
from django.test import SimpleTestCase, override_settings
from django.utils.safestring import mark_safe
from django.utils.html import escape

from qr_code.qrcode.maker import make_embedded_qr_code
from qr_code.qrcode.constants import ERROR_CORRECTION_DICT
from qr_code.qrcode.serve import make_qr_code_url, allows_external_request_from_user
from qr_code.qrcode.utils import QRCodeOptions
from qr_code.templatetags.qr_code import qr_from_text, qr_url_from_text

from qr_code.tests import (
    REFRESH_REFERENCE_IMAGES,
    TEST_TEXT,
    OVERRIDE_CACHES_SETTING,
    COMPLEX_TEST_TEXT,
    get_base64_png_image_template,
    IMAGE_TAG_BASE64_DATA_RE,
)
from qr_code.tests.utils import (
    write_svg_content_to_file,
    write_png_content_to_file,
    get_svg_content_from_file_name,
    get_png_content_from_file_name,
    get_urls_without_token_for_comparison,
    minimal_svg,
)


class TestQRUrlFromTextResult(SimpleTestCase):
    """
    Ensures that serving images representing QR codes works as expected (with or without caching, and with or without
    protection against external requests).
    """

    default_ref_base_file_name = "qrfromtext_default"

    def setUp(self):
        self.maxDiff = None

    @staticmethod
    def _get_reference_result_for_default_svg():
        return get_svg_content_from_file_name(TestQRUrlFromTextResult.default_ref_base_file_name)

    @staticmethod
    def _get_reference_result_for_default_png():
        return get_png_content_from_file_name(TestQRUrlFromTextResult.default_ref_base_file_name)

    def test_svg_url(self):
        is_first = True
        users = [None, AnonymousUser(), User(username="test")]
        for url_options in product([True, False, None], [True, False, None], users):
            cache_enabled = url_options[0]
            url_signature_enabled = url_options[1]
            user = url_options[2]
            print(f"\t - cache_enabled={cache_enabled}, url_signature_enabled={url_signature_enabled}, user={user}")
            url_options_kwargs = dict()
            url0 = make_qr_code_url(
                TEST_TEXT,
                QRCodeOptions(size=1),
                **dict(**url_options_kwargs, cache_enabled=cache_enabled, url_signature_enabled=url_signature_enabled),
            )
            if cache_enabled is not None:
                url_options_kwargs["cache_enabled"] = cache_enabled
            url1 = make_qr_code_url(
                TEST_TEXT, QRCodeOptions(size=1), **dict(**url_options_kwargs, url_signature_enabled=url_signature_enabled)
            )
            if url_signature_enabled is not None:
                url_options_kwargs["url_signature_enabled"] = url_signature_enabled
            url2 = qr_url_from_text(TEST_TEXT, size=1, **url_options_kwargs)
            url3 = qr_url_from_text(TEST_TEXT, image_format="svg", size=1, **url_options_kwargs)
            url4 = qr_url_from_text(TEST_TEXT, image_format="SVG", size=1, **url_options_kwargs)
            url5 = qr_url_from_text(TEST_TEXT, options=QRCodeOptions(image_format="SVG", size=1), **url_options_kwargs)
            # Using an invalid image format should fall back to SVG.
            url6 = qr_url_from_text(TEST_TEXT, image_format="invalid-format-name", size=1, **url_options_kwargs)
            url = url1
            if url_signature_enabled is not False:
                urls = get_urls_without_token_for_comparison(url0, url1, url2, url3, url4, url5, url6)
            else:
                urls = [url0, url1, url2, url3, url4, url5, url6]
            self.assertEqual(urls[0], urls[1])
            self.assertEqual(urls[0], urls[2])
            self.assertEqual(urls[0], urls[3])
            self.assertEqual(urls[0], urls[4])
            self.assertEqual(urls[0], urls[5])
            response = self.client.get(url)
            expected_status_code = 200
            if url_signature_enabled is False and not allows_external_request_from_user(user):
                expected_status_code = 403
            self.assertEqual(response.status_code, expected_status_code)
            image_data = response.content.decode("utf-8")
            if expected_status_code == 200:
                if is_first and REFRESH_REFERENCE_IMAGES:
                    write_svg_content_to_file(TestQRUrlFromTextResult.default_ref_base_file_name, image_data)
                    is_first = False
                self.assertEqual(image_data, TestQRUrlFromTextResult._get_reference_result_for_default_svg())

    def test_png_url(self):
        is_first = True
        for url_options in product([True, False, None], [True, False, None]):
            cache_enabled = url_options[0]
            url_signature_enabled = url_options[1]
            url_options_kwargs = dict()
            if cache_enabled is not None:
                url_options_kwargs["cache_enabled"] = cache_enabled
            if url_signature_enabled is not None:
                url_options_kwargs["url_signature_enabled"] = url_signature_enabled
            url1 = make_qr_code_url(TEST_TEXT, QRCodeOptions(image_format="png", size=1), **url_options_kwargs)
            url2 = qr_url_from_text(TEST_TEXT, image_format="png", size=1, **url_options_kwargs)
            url3 = qr_url_from_text(TEST_TEXT, image_format="PNG", size=1, **url_options_kwargs)
            url4 = qr_url_from_text(TEST_TEXT, options=QRCodeOptions(image_format="PNG", size=1), **url_options_kwargs)
            url = url1
            if url_signature_enabled is not False:
                urls = get_urls_without_token_for_comparison(url1, url2, url3, url4)
            else:
                urls = [url1, url2, url3, url4]
            self.assertEqual(urls[0], urls[1])
            self.assertEqual(urls[0], urls[2])
            self.assertEqual(urls[0], urls[3])
            response = self.client.get(url)
            print(f"\t - cache_enabled={cache_enabled}, url_signature_enabled={url_signature_enabled}")
            expected_status_code = 200
            if url_signature_enabled is False and not allows_external_request_from_user(None):
                expected_status_code = 403
            self.assertEqual(response.status_code, expected_status_code)
            if expected_status_code == 200:
                if is_first and REFRESH_REFERENCE_IMAGES:
                    write_png_content_to_file(TestQRUrlFromTextResult.default_ref_base_file_name, response.content)
                    is_first = False
                self.assertEqual(response.content, TestQRUrlFromTextResult._get_reference_result_for_default_png())

    @override_settings(CACHES=OVERRIDE_CACHES_SETTING, QR_CODE_CACHE_ALIAS=None)
    def test_svg_with_cache_but_no_alias(self):
        self.test_svg_url()

    @override_settings(CACHES=OVERRIDE_CACHES_SETTING)
    def test_png_with_cache(self):
        self.test_png_url()

    @override_settings(CACHES=OVERRIDE_CACHES_SETTING, QR_CODE_CACHE_ALIAS=None)
    def test_png_with_cache_but_no_alias(self):
        self.test_png_url()

    @override_settings(
        QR_CODE_URL_PROTECTION=dict(
            TOKEN_LENGTH=30,
            SIGNING_KEY="my-secret-signing-key",
            SIGNING_SALT="my-signing-salt",
            ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER=True,
        )
    )
    def test_url_with_protection_settings_1(self):
        # We need to clear cache every time we change the QR_CODE_URL_PROTECTION to avoid incidence between tests.
        caches[settings.QR_CODE_CACHE_ALIAS].clear()
        self.test_svg_url()
        self.test_png_url()
        response = self.client.get(make_qr_code_url(TEST_TEXT, url_signature_enabled=False, cache_enabled=False))
        # Registered users can access the URL externally, but since we are not logged in, we must expect an HTTP 403.
        self.assertEqual(response.status_code, 403)

    @override_settings(QR_CODE_URL_PROTECTION=dict(ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER=False))
    def test_url_with_protection_settings_2(self):
        # We need to clear cache every time we change the QR_CODE_URL_PROTECTION to avoid incidence between tests.
        caches[settings.QR_CODE_CACHE_ALIAS].clear()
        self.test_svg_url()
        self.test_png_url()
        response = self.client.get(make_qr_code_url(TEST_TEXT, url_signature_enabled=False, cache_enabled=False))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(make_qr_code_url(TEST_TEXT, url_signature_enabled=True, cache_enabled=False))
        self.assertEqual(response.status_code, 200)

    @override_settings(QR_CODE_URL_PROTECTION=dict(ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER=lambda user: False))
    def test_url_with_protection_settings_3(self):
        # We need to clear cache every time we change the QR_CODE_URL_PROTECTION to avoid incidence between tests.
        caches[settings.QR_CODE_CACHE_ALIAS].clear()
        self.test_svg_url()
        self.test_png_url()
        response = self.client.get(make_qr_code_url(TEST_TEXT, url_signature_enabled=False, cache_enabled=False))
        self.assertEqual(response.status_code, 403)
        response = self.client.get(make_qr_code_url(TEST_TEXT, url_signature_enabled=True, cache_enabled=False))
        self.assertEqual(response.status_code, 200)

    @override_settings(QR_CODE_URL_PROTECTION=dict(ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER=lambda user: True))
    def test_url_with_protection_settings_4(self):
        # We need to clear cache every time we change the QR_CODE_URL_PROTECTION to avoid incidence between tests.
        caches[settings.QR_CODE_CACHE_ALIAS].clear()
        self.test_svg_url()
        self.test_png_url()
        # The callable for ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER always return True, even for anonymous user.
        # Therefore, we must expect an HTTP 200.
        # We test with different values of url_signature_enabled.
        response = self.client.get(make_qr_code_url(TEST_TEXT, cache_enabled=False))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(make_qr_code_url(TEST_TEXT, url_signature_enabled=True, cache_enabled=False))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(make_qr_code_url(TEST_TEXT, url_signature_enabled=False, cache_enabled=False))
        self.assertEqual(response.status_code, 200)

    def test_url_with_invalid_signature_token(self):
        valid_url_with_signature_token = make_qr_code_url(TEST_TEXT)
        url_with_invalid_signature_token = valid_url_with_signature_token.replace("token=", "token=some-front-padding")
        response = self.client.get(url_with_invalid_signature_token)
        self.assertEqual(response.status_code, 403)

    def test_url_with_wrong_signature_token(self):
        valid_url_with_signature_token_for_size_10 = make_qr_code_url(TEST_TEXT, QRCodeOptions(size=10))
        valid_url_with_signature_token_for_size_8 = make_qr_code_url(TEST_TEXT, QRCodeOptions(size=8))
        token_regex = re.compile(r"token=([^&]+)")
        match = token_regex.search(valid_url_with_signature_token_for_size_8)
        size_8_token_value = match.group(1)
        match = token_regex.search(valid_url_with_signature_token_for_size_10)
        size_10_token_value = match.group(1)
        url_with_invalid_signature_token = valid_url_with_signature_token_for_size_10.replace(size_10_token_value, size_8_token_value)
        response = self.client.get(url_with_invalid_signature_token)
        self.assertEqual(response.status_code, 403)

    def test_svg_error_correction(self):
        base_file_name = "qrfromtext_error_correction"
        for correction_level in ERROR_CORRECTION_DICT:
            print("Testing SVG URL with error correction: %s" % correction_level)
            url1 = make_qr_code_url(COMPLEX_TEST_TEXT, QRCodeOptions(error_correction=correction_level), cache_enabled=False)
            url2 = qr_url_from_text(COMPLEX_TEST_TEXT, error_correction=correction_level, cache_enabled=False)
            url3 = qr_url_from_text(COMPLEX_TEST_TEXT, error_correction=correction_level, image_format="svg", cache_enabled=False)
            url4 = qr_url_from_text(COMPLEX_TEST_TEXT, error_correction=correction_level, image_format="SVG", cache_enabled=False)
            url5 = qr_url_from_text(
                COMPLEX_TEST_TEXT, options=QRCodeOptions(error_correction=correction_level, image_format="SVG"), cache_enabled=False
            )
            # Using an invalid image format should fallback to SVG.
            url6 = qr_url_from_text(
                COMPLEX_TEST_TEXT, error_correction=correction_level, image_format="invalid-format-name", cache_enabled=False
            )
            url = url1
            urls = get_urls_without_token_for_comparison(url1, url2, url3, url4, url5, url6)
            self.assertEqual(urls[0], urls[1])
            self.assertEqual(urls[0], urls[2])
            self.assertEqual(urls[0], urls[3])
            self.assertEqual(urls[0], urls[4])
            self.assertEqual(urls[0], urls[5])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            source_image_data = response.content.decode("utf-8")
            ref_file_name = f"{base_file_name}_{correction_level.lower()}"
            if REFRESH_REFERENCE_IMAGES:
                write_svg_content_to_file(ref_file_name, source_image_data)
            ref_image_data = get_svg_content_from_file_name(ref_file_name)
            self.assertEqual(source_image_data, ref_image_data)

    def test_png_error_correction(self):
        base_file_name = "qrfromtext_error_correction"
        for correction_level in ERROR_CORRECTION_DICT:
            print("Testing PNG URL with error correction: %s" % correction_level)
            url1 = make_qr_code_url(
                COMPLEX_TEST_TEXT, QRCodeOptions(error_correction=correction_level, image_format="png"), cache_enabled=False
            )
            url2 = make_qr_code_url(
                COMPLEX_TEST_TEXT, QRCodeOptions(error_correction=correction_level, image_format="PNG"), cache_enabled=False
            )
            url3 = qr_url_from_text(COMPLEX_TEST_TEXT, error_correction=correction_level, image_format="png", cache_enabled=False)
            url4 = qr_url_from_text(COMPLEX_TEST_TEXT, error_correction=correction_level, image_format="PNG", cache_enabled=False)
            url5 = qr_url_from_text(
                COMPLEX_TEST_TEXT, options=QRCodeOptions(error_correction=correction_level, image_format="PNG"), cache_enabled=False
            )
            url = url1
            urls = get_urls_without_token_for_comparison(url1, url2, url3, url4, url5)
            self.assertEqual(urls[0], urls[1])
            self.assertEqual(urls[0], urls[2])
            self.assertEqual(urls[0], urls[3])
            self.assertEqual(urls[0], urls[4])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            source_image_data = response.content
            ref_file_name = f"{base_file_name}_{correction_level.lower()}"
            if REFRESH_REFERENCE_IMAGES:
                write_png_content_to_file(ref_file_name, source_image_data)
            ref_image_data = get_png_content_from_file_name(ref_file_name)
            self.assertEqual(source_image_data, ref_image_data)

    def test_svg_eci(self):
        base_file_name = "qrfromtext_eci"
        for eci in [False, True]:
            print("Testing SVG URL with ECI: %s" % eci)
            url1 = make_qr_code_url(COMPLEX_TEST_TEXT, QRCodeOptions(eci=eci), cache_enabled=False)
            url2 = qr_url_from_text(COMPLEX_TEST_TEXT, eci=eci, cache_enabled=False)
            url3 = qr_url_from_text(COMPLEX_TEST_TEXT, eci=eci, image_format="svg", cache_enabled=False)
            url4 = qr_url_from_text(COMPLEX_TEST_TEXT, eci=eci, image_format="SVG", cache_enabled=False)
            url5 = qr_url_from_text(COMPLEX_TEST_TEXT, options=QRCodeOptions(eci=eci, image_format="SVG"), cache_enabled=False)
            # Using an invalid image format should fallback to SVG.
            url6 = qr_url_from_text(COMPLEX_TEST_TEXT, eci=eci, image_format="invalid-format-name", cache_enabled=False)
            url = url1
            urls = get_urls_without_token_for_comparison(url1, url2, url3, url4, url5, url6)
            self.assertEqual(urls[0], urls[1])
            self.assertEqual(urls[0], urls[2])
            self.assertEqual(urls[0], urls[3])
            self.assertEqual(urls[0], urls[4])
            self.assertEqual(urls[0], urls[5])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            source_image_data = response.content.decode("utf-8")
            ref_file_name = f"{base_file_name}_{str(eci).lower()}"
            if REFRESH_REFERENCE_IMAGES:
                write_svg_content_to_file(ref_file_name, source_image_data)
            ref_image_data = get_svg_content_from_file_name(ref_file_name)
            self.assertEqual(source_image_data, ref_image_data)

    def test_png_eci(self):
        base_file_name = "qrfromtext_eci"
        for eci in [False, True]:
            print("Testing PNG URL with ECI: %s" % eci)
            url1 = make_qr_code_url(COMPLEX_TEST_TEXT, QRCodeOptions(eci=eci, image_format="png"), cache_enabled=False)
            url2 = make_qr_code_url(COMPLEX_TEST_TEXT, QRCodeOptions(eci=eci, image_format="PNG"), cache_enabled=False)
            url3 = qr_url_from_text(COMPLEX_TEST_TEXT, eci=eci, image_format="png", cache_enabled=False)
            url4 = qr_url_from_text(COMPLEX_TEST_TEXT, eci=eci, image_format="PNG", cache_enabled=False)
            url5 = qr_url_from_text(COMPLEX_TEST_TEXT, options=QRCodeOptions(eci=eci, image_format="PNG"), cache_enabled=False)
            url = url1
            urls = get_urls_without_token_for_comparison(url1, url2, url3, url4, url5)
            self.assertEqual(urls[0], urls[1])
            self.assertEqual(urls[0], urls[2])
            self.assertEqual(urls[0], urls[3])
            self.assertEqual(urls[0], urls[4])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            source_image_data = response.content
            ref_file_name = f"{base_file_name}_{str(eci).lower()}"
            if REFRESH_REFERENCE_IMAGES:
                write_png_content_to_file(ref_file_name, source_image_data)
            ref_image_data = get_png_content_from_file_name(ref_file_name)
            self.assertEqual(source_image_data, ref_image_data)

    def test_svg_micro(self):
        base_file_name = "qrfromtext_micro"
        for micro in [False, True]:
            print("Testing SVG URL with micro: %s" % micro)
            url1 = make_qr_code_url(COMPLEX_TEST_TEXT, QRCodeOptions(micro=micro, encoding="iso-8859-1"), cache_enabled=False)
            url2 = qr_url_from_text(COMPLEX_TEST_TEXT, micro=micro, encoding="iso-8859-1", cache_enabled=False)
            url3 = qr_url_from_text(COMPLEX_TEST_TEXT, micro=micro, encoding="iso-8859-1", image_format="svg", cache_enabled=False)
            url4 = qr_url_from_text(COMPLEX_TEST_TEXT, micro=micro, encoding="iso-8859-1", image_format="SVG", cache_enabled=False)
            url5 = qr_url_from_text(
                COMPLEX_TEST_TEXT, options=QRCodeOptions(micro=micro, encoding="iso-8859-1", image_format="SVG"), cache_enabled=False
            )
            # Using an invalid image format should fallback to SVG.
            url6 = qr_url_from_text(
                COMPLEX_TEST_TEXT, micro=micro, encoding="iso-8859-1", image_format="invalid-format-name", cache_enabled=False
            )
            url = url1
            urls = get_urls_without_token_for_comparison(url1, url2, url3, url4, url5, url6)
            self.assertEqual(urls[0], urls[1])
            self.assertEqual(urls[0], urls[2])
            self.assertEqual(urls[0], urls[3])
            self.assertEqual(urls[0], urls[4])
            self.assertEqual(urls[0], urls[5])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            source_image_data = response.content.decode("utf-8")
            ref_file_name = f"{base_file_name}_{str(micro).lower()}"
            if REFRESH_REFERENCE_IMAGES:
                write_svg_content_to_file(ref_file_name, source_image_data)
            ref_image_data = get_svg_content_from_file_name(ref_file_name)
            self.assertEqual(source_image_data, ref_image_data)

    def test_png_micro(self):
        base_file_name = "qrfromtext_micro"
        for micro in [False, True]:
            print("Testing PNG URL with micro: %s" % micro)
            url1 = make_qr_code_url(
                COMPLEX_TEST_TEXT, QRCodeOptions(micro=micro, encoding="iso-8859-1", image_format="png"), cache_enabled=False
            )
            url2 = make_qr_code_url(
                COMPLEX_TEST_TEXT, QRCodeOptions(micro=micro, encoding="iso-8859-1", image_format="PNG"), cache_enabled=False
            )
            url3 = qr_url_from_text(COMPLEX_TEST_TEXT, micro=micro, encoding="iso-8859-1", image_format="png", cache_enabled=False)
            url4 = qr_url_from_text(COMPLEX_TEST_TEXT, micro=micro, encoding="iso-8859-1", image_format="PNG", cache_enabled=False)
            url5 = qr_url_from_text(
                COMPLEX_TEST_TEXT, options=QRCodeOptions(micro=micro, encoding="iso-8859-1", image_format="PNG"), cache_enabled=False
            )
            url = url1
            urls = get_urls_without_token_for_comparison(url1, url2, url3, url4, url5)
            self.assertEqual(urls[0], urls[1])
            self.assertEqual(urls[0], urls[2])
            self.assertEqual(urls[0], urls[3])
            self.assertEqual(urls[0], urls[4])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            source_image_data = response.content
            ref_file_name = f"{base_file_name}_{str(micro).lower()}"
            if REFRESH_REFERENCE_IMAGES:
                write_png_content_to_file(ref_file_name, source_image_data)
            ref_image_data = get_png_content_from_file_name(ref_file_name)
            self.assertEqual(source_image_data, ref_image_data)

    def test_svg_boost_error(self):
        base_file_name = "qrfromtext_boost_error"
        for boost_error in [False, True]:
            print("Testing SVG URL with boost_error: %s" % boost_error)
            url1 = make_qr_code_url(COMPLEX_TEST_TEXT, QRCodeOptions(boost_error=boost_error), cache_enabled=False)
            url2 = qr_url_from_text(COMPLEX_TEST_TEXT, boost_error=boost_error, cache_enabled=False)
            url3 = qr_url_from_text(COMPLEX_TEST_TEXT, boost_error=boost_error, image_format="svg", cache_enabled=False)
            url4 = qr_url_from_text(COMPLEX_TEST_TEXT, boost_error=boost_error, image_format="SVG", cache_enabled=False)
            url5 = qr_url_from_text(
                COMPLEX_TEST_TEXT, options=QRCodeOptions(boost_error=boost_error, image_format="SVG"), cache_enabled=False
            )
            # Using an invalid image format should fallback to SVG.
            url6 = qr_url_from_text(COMPLEX_TEST_TEXT, boost_error=boost_error, image_format="invalid-format-name", cache_enabled=False)
            url = url1
            urls = get_urls_without_token_for_comparison(url1, url2, url3, url4, url5, url6)
            self.assertEqual(urls[0], urls[1])
            self.assertEqual(urls[0], urls[2])
            self.assertEqual(urls[0], urls[3])
            self.assertEqual(urls[0], urls[4])
            self.assertEqual(urls[0], urls[5])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            source_image_data = response.content.decode("utf-8")
            ref_file_name = f"{base_file_name}_{str(boost_error).lower()}"
            if REFRESH_REFERENCE_IMAGES:
                write_svg_content_to_file(ref_file_name, source_image_data)
            ref_image_data = get_svg_content_from_file_name(ref_file_name)
            self.assertEqual(source_image_data, ref_image_data)

    def test_png_boost_error(self):
        base_file_name = "qrfromtext_boost_error"
        for boost_error in [False, True]:
            print("Testing PNG URL with boost_error: %s" % boost_error)
            url1 = make_qr_code_url(COMPLEX_TEST_TEXT, QRCodeOptions(boost_error=boost_error, image_format="png"), cache_enabled=False)
            url2 = make_qr_code_url(COMPLEX_TEST_TEXT, QRCodeOptions(boost_error=boost_error, image_format="PNG"), cache_enabled=False)
            url3 = qr_url_from_text(COMPLEX_TEST_TEXT, boost_error=boost_error, image_format="png", cache_enabled=False)
            url4 = qr_url_from_text(COMPLEX_TEST_TEXT, boost_error=boost_error, image_format="PNG", cache_enabled=False)
            url5 = qr_url_from_text(
                COMPLEX_TEST_TEXT, options=QRCodeOptions(boost_error=boost_error, image_format="PNG"), cache_enabled=False
            )
            url = url1
            urls = get_urls_without_token_for_comparison(url1, url2, url3, url4, url5)
            self.assertEqual(urls[0], urls[1])
            self.assertEqual(urls[0], urls[2])
            self.assertEqual(urls[0], urls[3])
            self.assertEqual(urls[0], urls[4])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            source_image_data = response.content
            ref_file_name = f"{base_file_name}_{str(boost_error).lower()}"
            if REFRESH_REFERENCE_IMAGES:
                write_png_content_to_file(ref_file_name, source_image_data)
            ref_image_data = get_png_content_from_file_name(ref_file_name)
            self.assertEqual(source_image_data, ref_image_data)

    def test_svg_encoding(self):
        file_base_name = "qrfromtext_encoding"
        data_for_encoding = [
            (TEST_TEXT, "utf-8"),
            (TEST_TEXT, "iso-8859-1"),
            (TEST_TEXT, None),
            (COMPLEX_TEST_TEXT, "utf-8"),
            (COMPLEX_TEST_TEXT, "iso-8859-1"),
            (COMPLEX_TEST_TEXT, None),
            ("ABCD1234", "utf-8"),
            ("ABCD1234", "iso-8859-1"),
            ("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:", "utf-8"),
            ("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:", "iso-8859-1"),
            ("義務教育諸学校教科用図書検定基準", "utf-8"),
            ("義務教育諸学校教科用図書検定基準", "cp932"),
            ("ウェブサイトにおける文字コードの割合、UTF-8が90％超え。Shift_JISやEUC-JPは？", "utf-8"),
            ("ウェブサイトにおける文字コードの割合、UTF-8が90％超え。Shift_JISやEUC-JPは？", "shift-jis"),
        ]
        for text, encoding in data_for_encoding:
            text_id = hashlib.md5(text.encode("utf-8")).hexdigest()
            ref_file_name = f"{file_base_name}_{text_id}_{str(encoding).lower()}"

            print(f"Testing SVG URL with encoding {encoding}' for text '{text}' ({text_id})")
            url1 = make_qr_code_url(text, QRCodeOptions(encoding=encoding), cache_enabled=False)
            url2 = qr_url_from_text(text, encoding=encoding, cache_enabled=False)
            url3 = qr_url_from_text(text, encoding=encoding, image_format="svg", cache_enabled=False)
            url4 = qr_url_from_text(text, encoding=encoding, image_format="SVG", cache_enabled=False)
            url5 = qr_url_from_text(text, options=QRCodeOptions(encoding=encoding, image_format="SVG"), cache_enabled=False)
            # Using an invalid image format should fallback to SVG.
            url6 = qr_url_from_text(text, encoding=encoding, image_format="invalid-format-name", cache_enabled=False)
            url = url1
            urls = get_urls_without_token_for_comparison(url1, url2, url3, url4, url5, url6)
            self.assertEqual(urls[0], urls[1])
            self.assertEqual(urls[0], urls[2])
            self.assertEqual(urls[0], urls[3])
            self.assertEqual(urls[0], urls[4])
            self.assertEqual(urls[0], urls[5])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            source_image_data = response.content.decode("utf-8")
            if REFRESH_REFERENCE_IMAGES:
                write_svg_content_to_file(ref_file_name, source_image_data)
            ref_image_data = get_svg_content_from_file_name(ref_file_name)
            self.assertEqual(minimal_svg(source_image_data), minimal_svg(ref_image_data))

    def test_png_encoding(self):
        file_base_name = "qrfromtext_encoding"
        data_for_encoding = [
            (TEST_TEXT, "utf-8"),
            (TEST_TEXT, "iso-8859-1"),
            (TEST_TEXT, None),
            (COMPLEX_TEST_TEXT, "utf-8"),
            (COMPLEX_TEST_TEXT, "iso-8859-1"),
            (COMPLEX_TEST_TEXT, None),
            ("ABCD1234", "utf-8"),
            ("ABCD1234", "iso-8859-1"),
            ("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:", "utf-8"),
            ("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:", "iso-8859-1"),
            ("義務教育諸学校教科用図書検定基準", "utf-8"),
            ("義務教育諸学校教科用図書検定基準", "cp932"),
            ("ウェブサイトにおける文字コードの割合、UTF-8が90％超え。Shift_JISやEUC-JPは？", "utf-8"),
            ("ウェブサイトにおける文字コードの割合、UTF-8が90％超え。Shift_JISやEUC-JPは？", "shift-jis"),
        ]
        for text, encoding in data_for_encoding:
            text_id = hashlib.md5(text.encode("utf-8")).hexdigest()
            ref_file_name = f"{file_base_name}_{text_id}_{str(encoding).lower()}"

            print(f"Testing PNG URL with encoding {encoding}' for text '{text}' ({text_id})")
            url1 = make_qr_code_url(text, QRCodeOptions(encoding=encoding, image_format="png"), cache_enabled=False)
            url2 = make_qr_code_url(text, QRCodeOptions(encoding=encoding, image_format="PNG"), cache_enabled=False)
            url3 = qr_url_from_text(text, encoding=encoding, image_format="png", cache_enabled=False)
            url4 = qr_url_from_text(text, encoding=encoding, image_format="PNG", cache_enabled=False)
            url5 = qr_url_from_text(text, options=QRCodeOptions(encoding=encoding, image_format="PNG"), cache_enabled=False)
            url = url1
            urls = get_urls_without_token_for_comparison(url1, url2, url3, url4, url5)
            self.assertEqual(urls[0], urls[1])
            self.assertEqual(urls[0], urls[2])
            self.assertEqual(urls[0], urls[3])
            self.assertEqual(urls[0], urls[4])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            source_image_data = response.content
            if REFRESH_REFERENCE_IMAGES:
                write_png_content_to_file(ref_file_name, source_image_data)
            ref_image_data = get_png_content_from_file_name(ref_file_name)
            self.assertEqual(source_image_data, ref_image_data)


class TestQRFromTextSvgResult(SimpleTestCase):
    """
    Ensures that produced QR codes in SVG format coincide with verified references.

    The tests cover direct call to tag function, rendering of tag, and direct call to qr_code API.
    """

    def setUp(self):
        self.maxDiff = None

    def test_size(self):
        base_ref_file_name = "qrfromtext_size"
        sizes = ["t", "T", "s", "S", None, -1, 0, "m", "M", "l", "L", "h", "H", "6", 6, "8", 8, "10", 10, 2.1, Decimal("1.2")]
        size_names = (
            ["tiny"] * 2
            + ["small"] * 2
            + ["medium"] * 5
            + ["large"] * 2
            + ["huge"] * 2
            + ["6"] * 2
            + ["8"] * 2
            + ["10"] * 2
            + ["2.1"]
            + ["1.2"]
        )
        for i in range(len(sizes)):
            size = sizes[i]
            print("Testing SVG with size %s" % size)
            size_name = size_names[i]
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(size=size))
            qr2 = qr_from_text(TEST_TEXT, size=size)
            qr3 = qr_from_text(TEST_TEXT, size=size, image_format="svg")
            qr4 = qr_from_text(TEST_TEXT, options=QRCodeOptions(size=size, image_format="svg"))
            qr5 = qr_from_text(TEST_TEXT, size=size, image_format="invalid-format-name")
            result_file_name = f"{base_ref_file_name}_{size_name}"
            if REFRESH_REFERENCE_IMAGES:
                write_svg_content_to_file(result_file_name, qr1)
            result = get_svg_content_from_file_name(result_file_name)
            self.assertEqual(qr1, qr2)
            self.assertEqual(qr1, qr3)
            self.assertEqual(qr1, qr4)
            self.assertEqual(qr1, qr5)
            self.assertEqual(qr1, result)

    def test_version(self):
        base_file_name = "qrfromtext_version"
        versions = [None, -1, 0, 41, "-1", "0", "41", "blabla", 1, "1", 2, "2", 4, "4"]
        version_names = ["default"] * 10 + ["2", "2", "4", "4"]
        for i in range(len(versions)):
            version = versions[i]
            print("Testing SVG with version %s" % version)
            version_name = version_names[i]
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(version=version))
            qr2 = qr_from_text(TEST_TEXT, version=version)
            qr3 = qr_from_text(TEST_TEXT, version=version, image_format="svg")
            qr4 = qr_from_text(TEST_TEXT, version=version, image_format="SVG")
            qr5 = qr_from_text(TEST_TEXT, options=QRCodeOptions(version=version, image_format="SVG"))
            qr6 = qr_from_text(TEST_TEXT, version=version, image_format="invalid-format-name")
            result_file_name = f"{base_file_name}_{version_name}"
            if REFRESH_REFERENCE_IMAGES:
                write_svg_content_to_file(result_file_name, qr1)
            result = get_svg_content_from_file_name(result_file_name)
            self.assertEqual(qr1, qr2)
            self.assertEqual(qr1, qr3)
            self.assertEqual(qr1, qr4)
            self.assertEqual(qr1, qr5)
            self.assertEqual(qr1, qr6)
            self.assertEqual(qr1, result)

    def test_error_correction(self):
        file_base_name = "qrfromtext_error_correction"
        tests_data = []
        for correction_level in ERROR_CORRECTION_DICT.keys():
            ref_file_name = f"{file_base_name}_{correction_level}"
            tests_data.append(
                dict(
                    source=f'{{% qr_from_text "{COMPLEX_TEST_TEXT}" image_format="svg" error_correction="{correction_level}" %}}',
                    ref_file_name=ref_file_name.lower(),
                )
            )

        for test_data in tests_data:
            print("Testing template: %s" % test_data["source"])
            html_source = mark_safe("{% load qr_code %}" + test_data["source"])
            template = Template(html_source)
            context = Context()
            source_image_data = template.render(context)
            if REFRESH_REFERENCE_IMAGES:
                write_svg_content_to_file(test_data["ref_file_name"], source_image_data)
            ref_image_data = get_svg_content_from_file_name(test_data["ref_file_name"])
            self.assertEqual(minimal_svg(source_image_data), minimal_svg(ref_image_data))

    def test_eci(self):
        file_base_name = "qrfromtext_eci"
        tests_data = []
        for eci in [False, True]:
            ref_file_name = f"{file_base_name}_{eci}"
            tests_data.append(
                dict(source=f'{{% qr_from_text "{COMPLEX_TEST_TEXT}" image_format="svg" eci={eci} %}}', ref_file_name=ref_file_name.lower())
            )
            # tests_data.append(dict(source=f'{{% qr_from_text "{COMPLEX_TEST_TEXT}" image_format="svg" eci="{eci}" %}}', ref_file_name=ref_file_name.lower()))

        for test_data in tests_data:
            print("Testing template: %s" % test_data["source"])
            html_source = mark_safe("{% load qr_code %}" + test_data["source"])
            template = Template(html_source)
            context = Context()
            source_image_data = template.render(context)
            if REFRESH_REFERENCE_IMAGES:
                write_svg_content_to_file(test_data["ref_file_name"], source_image_data)
            ref_image_data = get_svg_content_from_file_name(test_data["ref_file_name"])
            self.assertEqual(minimal_svg(source_image_data), minimal_svg(ref_image_data))

    def test_micro(self):
        file_base_name = "qrfromtext_micro"
        tests_data = []
        for micro in [False, True]:
            ref_file_name = f"{file_base_name}_{micro}"
            tests_data.append(
                dict(
                    source=f'{{% qr_from_text "{COMPLEX_TEST_TEXT}" image_format="svg" encoding="iso-8859-1" micro={micro} %}}',
                    ref_file_name=ref_file_name.lower(),
                )
            )
            # tests_data.append(dict(source=f'{{% qr_from_text "{COMPLEX_TEST_TEXT}" image_format="svg" micro="{micro}" %}}', ref_file_name=ref_file_name.lower()))

        for test_data in tests_data:
            print("Testing template: %s" % test_data["source"])
            html_source = mark_safe("{% load qr_code %}" + test_data["source"])
            template = Template(html_source)
            context = Context()
            source_image_data = template.render(context)
            if REFRESH_REFERENCE_IMAGES:
                write_svg_content_to_file(test_data["ref_file_name"], source_image_data)
            ref_image_data = get_svg_content_from_file_name(test_data["ref_file_name"])
            self.assertEqual(minimal_svg(source_image_data), minimal_svg(ref_image_data))

    def test_boost_error(self):
        file_base_name = "qrfromtext_boost_error"
        tests_data = []
        for boost_error in [False, True]:
            ref_file_name = f"{file_base_name}_{boost_error}"
            tests_data.append(
                dict(source=f'{{% qr_from_text data image_format="svg" boost_error={boost_error} %}}', ref_file_name=ref_file_name.lower())
            )

        for test_data in tests_data:
            print("Testing template: %s" % test_data["source"])
            html_source = mark_safe("{% load qr_code %}" + test_data["source"])
            template = Template(html_source)
            context = Context(dict(data=COMPLEX_TEST_TEXT))
            source_image_data = template.render(context)
            if REFRESH_REFERENCE_IMAGES:
                write_svg_content_to_file(test_data["ref_file_name"], source_image_data)
            ref_image_data = get_svg_content_from_file_name(test_data["ref_file_name"])
            self.assertEqual(minimal_svg(source_image_data), minimal_svg(ref_image_data))

    def test_encoding(self):
        file_base_name = "qrfromtext_encoding"
        tests_data = []
        data_for_encoding = [
            (TEST_TEXT, "utf-8"),
            (TEST_TEXT, "iso-8859-1"),
            (TEST_TEXT, None),
            (COMPLEX_TEST_TEXT, "utf-8"),
            (COMPLEX_TEST_TEXT, "iso-8859-1"),
            (COMPLEX_TEST_TEXT, None),
            ("ABCD1234", "utf-8"),
            ("ABCD1234", "iso-8859-1"),
            ("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:", "utf-8"),
            ("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:", "iso-8859-1"),
            ("義務教育諸学校教科用図書検定基準", "utf-8"),
            ("義務教育諸学校教科用図書検定基準", "cp932"),
            ("ウェブサイトにおける文字コードの割合、UTF-8が90％超え。Shift_JISやEUC-JPは？", "utf-8"),
            ("ウェブサイトにおける文字コードの割合、UTF-8が90％超え。Shift_JISやEUC-JPは？", "shift-jis"),
        ]
        for text, encoding in data_for_encoding:
            text_id = hashlib.md5(text.encode("utf-8")).hexdigest()
            ref_file_name = f"{file_base_name}_{text_id}_{str(encoding).lower()}"
            tests_data.append(
                dict(
                    source=f'{{% qr_from_text "{text}" image_format="svg" encoding="{encoding}" %}}',
                    text=text,
                    ref_file_name=ref_file_name.lower(),
                )
            )

        for test_data in tests_data:
            print("Testing template: %s" % test_data["source"])
            html_source = mark_safe("{% load qr_code %}" + test_data["source"])
            template = Template(html_source)
            context = Context()
            source_image_data = template.render(context)
            if REFRESH_REFERENCE_IMAGES:
                write_svg_content_to_file(test_data["ref_file_name"], source_image_data)
            ref_image_data = get_svg_content_from_file_name(test_data["ref_file_name"])
            self.assertEqual(minimal_svg(source_image_data), minimal_svg(ref_image_data))

    def test_colors(self):
        def run_tests():
            if REFRESH_REFERENCE_IMAGES:
                write_svg_content_to_file(result_file_name, qr1)
            self.assertEqual(minimal_svg(qr1), minimal_svg(qr2))
            self.assertEqual(minimal_svg(qr1), minimal_svg(qr3))
            ref_image_data = minimal_svg(get_svg_content_from_file_name(result_file_name))
            self.assertEqual(minimal_svg(qr1), ref_image_data)

        base_ref_file_name = "qrfromtext_color"
        colors = ["#000", "#000000", "black", "#fff", "#FFFFFF", "white", "red", "blue", None]
        color_names = ["black"] * 2 + ["black"] + ["white_hexa"] * 2 + ["white"] + ["red", "blue", "transparent"]
        for i in range(len(colors)):
            color = colors[i]
            color_name = color_names[i]
            print("Testing SVG with dark color %s" % color_name)
            result_file_name = f"{base_ref_file_name}_dark_{color_name}"
            # Set light color to pink  to avoid black on black or white on white.
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(dark_color=color, light_color="pink", image_format="svg"))
            qr2 = qr_from_text(TEST_TEXT, dark_color=color, light_color="pink", image_format="svg")
            qr3 = qr_from_text(TEST_TEXT, options=QRCodeOptions(dark_color=color, light_color="pink", image_format="svg"))
            run_tests()

            print("Testing SVG with light color %s" % color_name)
            result_file_name = f"{base_ref_file_name}_light_{color_name}"
            # Set dark color to pink  to avoid black on black or white on white.
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(light_color=color, dark_color="pink", image_format="svg"))
            qr2 = qr_from_text(TEST_TEXT, light_color=color, dark_color="pink", image_format="svg")
            qr3 = qr_from_text(TEST_TEXT, options=QRCodeOptions(light_color=color, dark_color="pink", image_format="svg"))
            run_tests()

            print("Testing SVG with data_dark color %s" % color_name)
            result_file_name = f"{base_ref_file_name}_data_dark_{color_name}"
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(data_dark_color=color, dark_color="pink", image_format="svg"))
            qr2 = qr_from_text(TEST_TEXT, data_dark_color=color, dark_color="pink", image_format="svg")
            qr3 = qr_from_text(TEST_TEXT, options=QRCodeOptions(data_dark_color=color, dark_color="pink", image_format="svg"))
            run_tests()

            print("Testing SVG with data light color %s" % color_name)
            result_file_name = f"{base_ref_file_name}_data_light_{color_name}"
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(data_light_color=color, dark_color="pink", image_format="svg"))
            qr2 = qr_from_text(TEST_TEXT, data_light_color=color, dark_color="pink", image_format="svg")
            qr3 = qr_from_text(TEST_TEXT, options=QRCodeOptions(data_light_color=color, dark_color="pink", image_format="svg"))
            run_tests()

            print("Testing SVG with finder dark color %s" % color_name)
            result_file_name = f"{base_ref_file_name}_finder_dark_{color_name}"
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(finder_dark_color=color, dark_color="pink", image_format="svg"))
            qr2 = qr_from_text(TEST_TEXT, finder_dark_color=color, dark_color="pink", image_format="svg")
            qr3 = qr_from_text(TEST_TEXT, options=QRCodeOptions(finder_dark_color=color, dark_color="pink", image_format="svg"))
            run_tests()

            print("Testing SVG with finder light color %s" % color_name)
            result_file_name = f"{base_ref_file_name}_finder_light_{color_name}"
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(finder_light_color=color, dark_color="pink", image_format="svg"))
            qr2 = qr_from_text(TEST_TEXT, finder_light_color=color, dark_color="pink", image_format="svg")
            qr3 = qr_from_text(TEST_TEXT, options=QRCodeOptions(finder_light_color=color, dark_color="pink", image_format="svg"))
            run_tests()

            print("Testing SVG with dark module color %s" % color_name)
            result_file_name = f"{base_ref_file_name}_dark_module_{color_name}"
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(dark_module_color=color, dark_color="pink", image_format="svg"))
            qr2 = qr_from_text(TEST_TEXT, dark_module_color=color, dark_color="pink", image_format="svg")
            qr3 = qr_from_text(TEST_TEXT, options=QRCodeOptions(dark_module_color=color, dark_color="pink", image_format="svg"))
            run_tests()

            print("Testing SVG with alignment dark color %s" % color_name)
            result_file_name = f"{base_ref_file_name}_alignment_dark_{color_name}"
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(alignment_dark_color=color, dark_color="pink", image_format="svg"))
            qr2 = qr_from_text(TEST_TEXT, alignment_dark_color=color, dark_color="pink", image_format="svg")
            qr3 = qr_from_text(TEST_TEXT, options=QRCodeOptions(alignment_dark_color=color, dark_color="pink", image_format="svg"))
            run_tests()

            print("Testing SVG with alignment light color %s" % color_name)
            result_file_name = f"{base_ref_file_name}_alignment_light_{color_name}"
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(alignment_light_color=color, dark_color="pink", image_format="svg"))
            qr2 = qr_from_text(TEST_TEXT, alignment_light_color=color, dark_color="pink", image_format="svg")
            qr3 = qr_from_text(TEST_TEXT, options=QRCodeOptions(alignment_light_color=color, dark_color="pink", image_format="svg"))
            run_tests()


class TestQRFromTextPngResult(SimpleTestCase):
    """
    Ensures that produced QR codes in PNG format coincide with verified references.

    The tests cover direct call to tag function, rendering of tag, and direct call to qr_code API.
    """

    def setUp(self):
        self.maxDiff = None

    def test_size(self):
        base_ref_file_name = "qrfromtext_size"
        sizes = ["t", "T", "s", "S", None, -1, 0, "m", "M", "l", "L", "h", "H", "6", 6, "8", 8, "10", 10, 2.1]
        size_names = (
            ["tiny"] * 2 + ["small"] * 2 + ["medium"] * 5 + ["large"] * 2 + ["huge"] * 2 + ["6"] * 2 + ["8"] * 2 + ["10"] * 2 + ["2.1"]
        )
        for i in range(len(sizes)):
            size = sizes[i]
            print("Testing PNG with size %s" % size)
            size_name = size_names[i]
            result_file_name = f"{base_ref_file_name}_{size_name}"
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(size=size, image_format="png"))
            qr2 = qr_from_text(TEST_TEXT, size=size, image_format="png")
            qr3 = qr_from_text(TEST_TEXT, options=QRCodeOptions(size=size, image_format="png"))
            if REFRESH_REFERENCE_IMAGES:
                match = IMAGE_TAG_BASE64_DATA_RE.search(qr1)
                source_image_data = match.group("data")
                write_png_content_to_file(result_file_name, base64.b64decode(source_image_data))
            result = base64.b64encode(get_png_content_from_file_name(result_file_name)).decode("utf-8")
            self.assertEqual(qr1, qr2)
            self.assertEqual(qr1, qr3)
            self.assertEqual(qr1, get_base64_png_image_template() % result)

    def test_version(self):
        base_file_name = "qrfromtext_version"
        versions = [None, -1, 0, 41, "-1", "0", "41", "blabla", 1, "1", 2, "2", 4, "4"]
        version_names = ["default"] * 10 + ["2", "2", "4", "4"]
        for i in range(len(versions)):
            version = versions[i]
            print("Testing PNG with version %s" % version)
            version_name = version_names[i]
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(version=version, image_format="png"))
            qr2 = qr_from_text(TEST_TEXT, version=version, image_format="png")
            qr3 = qr_from_text(TEST_TEXT, version=version, image_format="PNG")
            qr4 = qr_from_text(TEST_TEXT, options=QRCodeOptions(version=version, image_format="PNG"))
            result_file_name = f"{base_file_name}_{version_name}"
            if REFRESH_REFERENCE_IMAGES:
                match = IMAGE_TAG_BASE64_DATA_RE.search(qr1)
                source_image_data = match.group("data")
                write_png_content_to_file(result_file_name, base64.b64decode(source_image_data))
            result = base64.b64encode(get_png_content_from_file_name(result_file_name)).decode("utf-8")
            self.assertEqual(qr1, qr2)
            self.assertEqual(qr1, qr3)
            self.assertEqual(qr1, qr4)
            self.assertEqual(qr1, get_base64_png_image_template() % result)

    def test_error_correction(self):
        file_base_name = "qrfromtext_error_correction"
        tests_data = []
        for correction_level in ERROR_CORRECTION_DICT.keys():
            ref_file_name = f"{file_base_name}_{correction_level}"
            tests_data.append(
                dict(
                    source=f'{{% qr_from_text "{COMPLEX_TEST_TEXT}" image_format="png" error_correction="{correction_level}" %}}',
                    ref_file_name=ref_file_name.lower(),
                )
            )

        for test_data in tests_data:
            print("Testing template: %s" % test_data["source"])
            html_source = mark_safe("{% load qr_code %}" + test_data["source"])
            template = Template(html_source)
            context = Context()
            source_image = template.render(context).strip()
            source_image_data = source_image[32 : -len('" alt="%s"' % escape(COMPLEX_TEST_TEXT))]
            source_image_data = base64.b64decode(source_image_data)
            if REFRESH_REFERENCE_IMAGES:
                write_png_content_to_file(test_data["ref_file_name"], source_image_data)
            ref_image_data = get_png_content_from_file_name(test_data["ref_file_name"])
            self.assertEqual(source_image_data, ref_image_data)

    def test_eci(self):
        file_base_name = "qrfromtext_eci"
        tests_data = []
        for eci in [False, True]:
            ref_file_name = f"{file_base_name}_{eci}"
            tests_data.append(
                dict(source=f'{{% qr_from_text "{COMPLEX_TEST_TEXT}" image_format="png" eci={eci} %}}', ref_file_name=ref_file_name.lower())
            )
            # tests_data.append(dict(source=f'{{% qr_from_text "{COMPLEX_TEST_TEXT}" image_format="png" eci="{eci}" %}}', ref_file_name=ref_file_name.lower()))

        for test_data in tests_data:
            print("Testing template: %s" % test_data["source"])
            html_source = mark_safe("{% load qr_code %}" + test_data["source"])
            template = Template(html_source)
            context = Context()
            source_image = template.render(context).strip()
            source_image_data = source_image[32 : -len('" alt="%s"' % escape(COMPLEX_TEST_TEXT))]
            source_image_data = base64.b64decode(source_image_data)
            if REFRESH_REFERENCE_IMAGES:
                write_png_content_to_file(test_data["ref_file_name"], source_image_data)
            ref_image_data = get_png_content_from_file_name(test_data["ref_file_name"])
            self.assertEqual(source_image_data, ref_image_data)

    def test_micro(self):
        file_base_name = "qrfromtext_micro"
        tests_data = []
        for micro in [False, True]:
            ref_file_name = f"{file_base_name}_{micro}"
            tests_data.append(
                dict(
                    source=f'{{% qr_from_text "{COMPLEX_TEST_TEXT}" image_format="png" encoding=None micro={micro}%}}',
                    ref_file_name=ref_file_name.lower(),
                )
            )
            tests_data.append(
                dict(
                    source=f'{{% qr_from_text "{COMPLEX_TEST_TEXT}" image_format="png" encoding="iso-8859-1" micro={micro}%}}',
                    ref_file_name=ref_file_name.lower(),
                )
            )
            # tests_data.append(dict(source=f'{{% qr_from_text "{COMPLEX_TEST_TEXT}" image_format="png" micro="{micro}"%}}', ref_file_name=ref_file_name.lower()))

        for test_data in tests_data:
            print("Testing template: %s" % test_data["source"])
            html_source = mark_safe("{% load qr_code %}" + test_data["source"])
            template = Template(html_source)
            context = Context()
            source_image = template.render(context).strip()
            source_image_data = source_image[32 : -len('" alt="%s"' % escape(COMPLEX_TEST_TEXT))]
            source_image_data = base64.b64decode(source_image_data)
            if REFRESH_REFERENCE_IMAGES:
                write_png_content_to_file(test_data["ref_file_name"], source_image_data)
            ref_image_data = get_png_content_from_file_name(test_data["ref_file_name"])
            self.assertEqual(source_image_data, ref_image_data)

    def test_boost_error(self):
        file_base_name = "qrfromtext_boost_error"
        tests_data = []
        for boost_error in [False, True]:
            ref_file_name = f"{file_base_name}_{boost_error}"
            tests_data.append(
                dict(source=f'{{% qr_from_text data image_format="png" boost_error={boost_error} %}}', ref_file_name=ref_file_name.lower())
            )

        for test_data in tests_data:
            print("Testing template: %s" % test_data["source"])
            html_source = mark_safe("{% load qr_code %}" + test_data["source"])
            template = Template(html_source)
            context = Context(dict(data=COMPLEX_TEST_TEXT))
            source_image = template.render(context).strip()

            # template = Template(html_source.replace('qr_from_text', 'qr_url_from_text'))
            # url = template.render(context).strip()
            # response = self.client.get(url)
            # new_image = base64.b64encode(response.content)

            source_image_data = source_image[32 : -len('" alt="%s"' % escape(COMPLEX_TEST_TEXT))]
            source_image_data = base64.b64decode(source_image_data)
            if REFRESH_REFERENCE_IMAGES:
                write_png_content_to_file(test_data["ref_file_name"], source_image_data)
            ref_image_data = get_png_content_from_file_name(test_data["ref_file_name"])
            self.assertEqual(source_image_data, ref_image_data)

    def test_encoding(self):
        file_base_name = "qrfromtext_encoding"
        tests_data = []
        data_for_encoding = [
            (TEST_TEXT, "utf-8"),
            (TEST_TEXT, "iso-8859-1"),
            (TEST_TEXT, None),
            (COMPLEX_TEST_TEXT, "utf-8"),
            (COMPLEX_TEST_TEXT, "iso-8859-1"),
            (COMPLEX_TEST_TEXT, None),
            ("ABCD1234", "utf-8"),
            ("ABCD1234", "iso-8859-1"),
            ("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:", "utf-8"),
            ("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:", "iso-8859-1"),
            ("義務教育諸学校教科用図書検定基準", "utf-8"),
            ("義務教育諸学校教科用図書検定基準", "cp932"),
            ("ウェブサイトにおける文字コードの割合、UTF-8が90％超え。Shift_JISやEUC-JPは？", "utf-8"),
            ("ウェブサイトにおける文字コードの割合、UTF-8が90％超え。Shift_JISやEUC-JPは？", "shift-jis"),
        ]
        for text, encoding in data_for_encoding:
            text_id = hashlib.md5(text.encode("utf-8")).hexdigest()
            ref_file_name = f"{file_base_name}_{text_id}_{str(encoding).lower()}"
            tests_data.append(
                dict(
                    source=f'{{% qr_from_text "{text}" image_format="png" encoding="{encoding}" %}}',
                    text=text,
                    ref_file_name=ref_file_name.lower(),
                )
            )

        for test_data in tests_data:
            print("Testing template: %s" % test_data["source"])
            text = test_data["text"]
            html_source = mark_safe("{% load qr_code %}" + test_data["source"])
            template = Template(html_source)
            context = Context()
            source_image = template.render(context).strip()
            source_image_data = source_image[32 : -len('" alt="%s"' % escape(text))]
            source_image_data = base64.b64decode(source_image_data)
            if REFRESH_REFERENCE_IMAGES:
                write_png_content_to_file(test_data["ref_file_name"], source_image_data)
            ref_image_data = get_png_content_from_file_name(test_data["ref_file_name"])
            self.assertEqual(source_image_data, ref_image_data)

    def test_colors(self):
        def run_tests():
            if REFRESH_REFERENCE_IMAGES:
                match = IMAGE_TAG_BASE64_DATA_RE.search(qr1)
                source_image_data = match.group("data")
                write_png_content_to_file(result_file_name, base64.b64decode(source_image_data))
            result = base64.b64encode(get_png_content_from_file_name(result_file_name)).decode("utf-8")
            self.assertEqual(qr1, qr2)
            self.assertEqual(qr1, qr3)
            self.assertEqual(qr1, get_base64_png_image_template() % result)

        base_ref_file_name = "qrfromtext_color"
        colors = ["#000", "#000000", "black", "#fff", "#FFFFFF", "white", "red", "blue", None]
        color_names = ["black"] * 2 + ["black"] + ["white_hexa"] * 2 + ["white"] + ["red", "blue", "transparent"]
        for i in range(len(colors)):
            color = colors[i]
            color_name = color_names[i]
            print("Testing PNG with dark color %s" % color_name)
            result_file_name = f"{base_ref_file_name}_dark_{color_name}"
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(dark_color=color, image_format="png"))
            qr2 = qr_from_text(TEST_TEXT, dark_color=color, image_format="png")
            qr3 = qr_from_text(TEST_TEXT, options=QRCodeOptions(dark_color=color, image_format="png"))
            run_tests()

            print("Testing PNG with light color %s" % color_name)
            result_file_name = f"{base_ref_file_name}_light_{color_name}"
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(light_color=color, image_format="png"))
            qr2 = qr_from_text(TEST_TEXT, light_color=color, image_format="png")
            qr3 = qr_from_text(TEST_TEXT, options=QRCodeOptions(light_color=color, image_format="png"))
            run_tests()

            print("Testing PNG with data_dark color %s" % color_name)
            result_file_name = f"{base_ref_file_name}_data_dark_{color_name}"
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(data_dark_color=color, image_format="png"))
            qr2 = qr_from_text(TEST_TEXT, data_dark_color=color, image_format="png")
            qr3 = qr_from_text(TEST_TEXT, options=QRCodeOptions(data_dark_color=color, image_format="png"))
            run_tests()

            print("Testing PNG with data light color %s" % color_name)
            result_file_name = f"{base_ref_file_name}_data_light_{color_name}"
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(data_light_color=color, image_format="png"))
            qr2 = qr_from_text(TEST_TEXT, data_light_color=color, image_format="png")
            qr3 = qr_from_text(TEST_TEXT, options=QRCodeOptions(data_light_color=color, image_format="png"))
            run_tests()

            print("Testing PNG with finder dark color %s" % color_name)
            result_file_name = f"{base_ref_file_name}_finder_dark_{color_name}"
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(finder_dark_color=color, image_format="png"))
            qr2 = qr_from_text(TEST_TEXT, finder_dark_color=color, image_format="png")
            qr3 = qr_from_text(TEST_TEXT, options=QRCodeOptions(finder_dark_color=color, image_format="png"))
            run_tests()

            print("Testing PNG with finder light color %s" % color_name)
            result_file_name = f"{base_ref_file_name}_finder_light_{color_name}"
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(finder_light_color=color, image_format="png"))
            qr2 = qr_from_text(TEST_TEXT, finder_light_color=color, image_format="png")
            qr3 = qr_from_text(TEST_TEXT, options=QRCodeOptions(finder_light_color=color, image_format="png"))
            run_tests()

            print("Testing PNG with dark module color %s" % color_name)
            result_file_name = f"{base_ref_file_name}_dark_module_{color_name}"
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(dark_module_color=color, image_format="png"))
            qr2 = qr_from_text(TEST_TEXT, dark_module_color=color, image_format="png")
            qr3 = qr_from_text(TEST_TEXT, options=QRCodeOptions(dark_module_color=color, image_format="png"))
            run_tests()

            print("Testing PNG with alignment dark color %s" % color_name)
            result_file_name = f"{base_ref_file_name}_alignment_dark_{color_name}"
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(alignment_dark_color=color, image_format="png"))
            qr2 = qr_from_text(TEST_TEXT, alignment_dark_color=color, image_format="png")
            qr3 = qr_from_text(TEST_TEXT, options=QRCodeOptions(alignment_dark_color=color, image_format="png"))
            run_tests()

            print("Testing PNG with alignment light color %s" % color_name)
            result_file_name = f"{base_ref_file_name}_alignment_light_{color_name}"
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(alignment_light_color=color, image_format="png"))
            qr2 = qr_from_text(TEST_TEXT, alignment_light_color=color, image_format="png")
            qr3 = qr_from_text(TEST_TEXT, options=QRCodeOptions(alignment_light_color=color, image_format="png"))
            run_tests()
