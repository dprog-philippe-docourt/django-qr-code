"""Tests for qr_code application."""
import base64
import re

import os
from datetime import date
from itertools import product

from django.contrib.auth.models import AnonymousUser, User
from django.template import Template, Context
from django.test import SimpleTestCase, override_settings
from django.utils.safestring import mark_safe
from django.utils.html import escape

from qr_code.qrcode.image import SVG_FORMAT_NAME, PNG_FORMAT_NAME
from qr_code.qrcode.maker import make_embedded_qr_code
from qr_code.qrcode.constants import ERROR_CORRECTION_DICT, DEFAULT_IMAGE_FORMAT, DEFAULT_MODULE_SIZE, \
    DEFAULT_ERROR_CORRECTION, DEFAULT_VERSION
from qr_code.qrcode.serve import make_qr_code_url, allows_external_request_from_user
from qr_code.qrcode.utils import ContactDetail, WifiConfig, QRCodeOptions, Coordinates
from qr_code.templatetags.qr_code import qr_from_text, qr_url_from_text

# Set this flag to True for writing the new version of each reference image in tests/resources while running the tests.
REFRESH_REFERENCE_IMAGES = False

BASE64_PNG_IMAGE_TEMPLATE = '<img src="data:image/png;base64, %s" alt="Hello World!">'
IMAGE_TAG_BASE64_DATA_RE = re.compile(r'data:image/png;base64, (?P<data>[\w/+=]+)')
TEST_TEXT = 'Hello World!'
COMPLEX_TEST_TEXT = '/%+¼@#=<>àé'
TEST_CONTACT_DETAIL = dict(
            first_name='John',
            last_name='Doe',
            first_name_reading='jAAn',
            last_name_reading='dOH',
            tel='+41769998877',
            email='j.doe@company.com',
            url='http://www.company.com',
            birthday=date(year=1985, month=10, day=2),
            address='Cras des Fourches 987, 2800 Delémont, Jura, Switzerland',
            memo='Development Manager',
            org='Company Ltd',
        )
TEST_WIFI_CONFIG = dict(
            ssid='my-wifi',
            authentication=WifiConfig.AUTHENTICATION.WPA,
            password='wifi-password'
        )
OVERRIDE_CACHES_SETTING = {'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', },
                           'qr-code': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
                                       'LOCATION': 'qr-code-cache', 'TIMEOUT': 3600}}
SVG_REF_SUFFIX = '.ref.svg'
PNG_REF_SUFFIX = '.ref.png'


def get_urls_without_token_for_comparison(*urls):
    token_regex = re.compile(r"&?token=[^&]+")
    simplified_urls = list(map(lambda x: token_regex.sub('', x), urls))
    simplified_urls = list(map(lambda x: x.replace('?&', '?'), simplified_urls))
    return simplified_urls


def get_resources_path():
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    resources_dir = os.path.join(tests_dir, 'resources')
    return resources_dir


def _make_closing_path_tag(svg):
    return svg.replace(' /></svg>', '></path></svg>')


def _make_xml_header():
    return "<?xml version='1.0' encoding='UTF-8'?>"


class TestApps(SimpleTestCase):
    def test_apps_attributes(self):
        from qr_code.apps import QrCodeConfig
        self.assertEqual(QrCodeConfig.name, 'qr_code')
        self.assertEqual(QrCodeConfig.verbose_name, 'Django QR code')


class TestQRCodeOptions(SimpleTestCase):
    def test_qr_code_options(self):
        with self.assertRaises(ValueError):
            QRCodeOptions(foo='bar')
        options = QRCodeOptions()
        self.assertEqual(options.border, 4)
        self.assertEqual(options.size, DEFAULT_MODULE_SIZE)
        self.assertEqual(options.image_format, DEFAULT_IMAGE_FORMAT)
        self.assertEqual(options.version, DEFAULT_VERSION)
        self.assertEqual(options.error_correction, DEFAULT_ERROR_CORRECTION)
        options = QRCodeOptions(image_format='invalid-image-format')
        self.assertEqual(options.image_format, DEFAULT_IMAGE_FORMAT)


class TestContactDetail(SimpleTestCase):
    def test_make_qr_code_text(self):
        data = dict(**TEST_CONTACT_DETAIL)
        c1 = ContactDetail(**data)
        data['nickname'] = 'buddy'
        c2 = ContactDetail(**data)
        data['last_name'] = "O'Hara;,:"
        data['tel_av'] = 'n/a'
        c3 = ContactDetail(**data)
        del data['last_name']
        c4 = ContactDetail(**data)
        self.assertEqual(c1.make_qr_code_text(), r'MECARD:N:Doe,John;SOUND:dOH,jAAn;TEL:+41769998877;EMAIL:j.doe@company.com;NOTE:Development Manager;BDAY:19851002;ADR:Cras des Fourches 987, 2800 Delémont, Jura, Switzerland;URL:http\://www.company.com;ORG:Company Ltd;;')
        self.assertEqual(c2.make_qr_code_text(), r'MECARD:N:Doe,John;SOUND:dOH,jAAn;TEL:+41769998877;EMAIL:j.doe@company.com;NOTE:Development Manager;BDAY:19851002;ADR:Cras des Fourches 987, 2800 Delémont, Jura, Switzerland;URL:http\://www.company.com;NICKNAME:buddy;ORG:Company Ltd;;')
        self.assertEqual(c3.make_qr_code_text(),
                         r"MECARD:N:O'Hara\;\,\:,John;SOUND:dOH,jAAn;TEL:+41769998877;TEL-AV:n/a;EMAIL:j.doe@company.com;NOTE:Development Manager;BDAY:19851002;ADR:Cras des Fourches 987, 2800 Delémont, Jura, Switzerland;URL:http\://www.company.com;NICKNAME:buddy;ORG:Company Ltd;;")
        self.assertEqual(c4.make_qr_code_text(),
                         r"MECARD:N:John;SOUND:dOH,jAAn;TEL:+41769998877;TEL-AV:n/a;EMAIL:j.doe@company.com;NOTE:Development Manager;BDAY:19851002;ADR:Cras des Fourches 987, 2800 Delémont, Jura, Switzerland;URL:http\://www.company.com;NICKNAME:buddy;ORG:Company Ltd;;")


class TestWifiConfig(SimpleTestCase):
    def test_make_qr_code_text(self):
        wifi1 = WifiConfig(**TEST_WIFI_CONFIG)
        wifi2 = WifiConfig(hidden=True, **TEST_WIFI_CONFIG)
        self.assertEqual(wifi1.make_qr_code_text(), 'WIFI:S:my-wifi;T:WPA;P:wifi-password;;')
        self.assertEqual(wifi2.make_qr_code_text(), 'WIFI:S:my-wifi;T:WPA;P:wifi-password;H:true;;')


class TestCoordinates(SimpleTestCase):
    def test_coordinates(self):
        c1 = Coordinates(latitude=586000.32, longitude=250954.19)
        c2 = Coordinates(latitude=586000.32, longitude=250954.19, altitude=500)
        self.assertEqual(c1.__str__(), 'latitude: 586000.32, longitude: 250954.19')
        self.assertEqual(c2.__str__(), 'latitude: 586000.32, longitude: 250954.19, altitude: 500')


class TestQRUrlFromTextResult(SimpleTestCase):
    """
    Ensures that serving images representing QR codes works as expected (with or without caching, and with or without
    protection against external requests).
    """
    ref_base_file_name = 'qrfromtext_default'
    svg_result = None
    png_result = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        TestQRUrlFromTextResult.svg_result = get_svg_content_from_file_name(
            TestQRUrlFromTextResult.ref_base_file_name + SVG_REF_SUFFIX)
        TestQRUrlFromTextResult.png_result = get_png_content_from_file_name(
            TestQRUrlFromTextResult.ref_base_file_name + PNG_REF_SUFFIX)

    def test_svg_url(self):
        is_first = True
        users = [None, AnonymousUser(), User(username='test')]
        for url_options in product([True, False, None], [True, False, None], users):
            cache_enabled = url_options[0]
            url_signature_enabled = url_options[1]
            user = url_options[2]
            print("\t - cache_enabled=%s, url_signature_enabled=%s, user=%s" % (cache_enabled, url_signature_enabled, user))
            url_options_kwargs = dict()
            url0 = make_qr_code_url(TEST_TEXT, QRCodeOptions(size=1), **dict(**url_options_kwargs, cache_enabled=cache_enabled, url_signature_enabled=url_signature_enabled))
            if cache_enabled is not None:
                url_options_kwargs['cache_enabled'] = cache_enabled
            url1 = make_qr_code_url(TEST_TEXT, QRCodeOptions(size=1),  **dict(**url_options_kwargs, url_signature_enabled=url_signature_enabled))
            if url_signature_enabled is not None:
                url_options_kwargs['url_signature_enabled'] = url_signature_enabled
            url2 = qr_url_from_text(TEST_TEXT, size=1, **url_options_kwargs)
            url3 = qr_url_from_text(TEST_TEXT, image_format='svg', size=1, **url_options_kwargs)
            url4 = qr_url_from_text(TEST_TEXT, image_format='SVG', size=1, **url_options_kwargs)
            url5 = qr_url_from_text(TEST_TEXT, options=QRCodeOptions(image_format='SVG', size=1), **url_options_kwargs)
            # Using an invalid image format should fallback to SVG.
            url6 = qr_url_from_text(TEST_TEXT, image_format='invalid-format-name', size=1, **url_options_kwargs)
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
            image_data = response.content.decode('utf-8')
            if expected_status_code == 200:
                self.assertEqual(image_data, TestQRUrlFromTextResult.svg_result)
            if is_first and REFRESH_REFERENCE_IMAGES:
                write_svg_content_to_file(TestQRUrlFromTextResult.ref_base_file_name + SVG_REF_SUFFIX,
                                          image_data)
                is_first = False

    def test_png_url(self):
        is_first = True
        for url_options in product([True, False, None], [True, False, None]):
            cache_enabled = url_options[0]
            url_signature_enabled = url_options[1]
            url_options_kwargs = dict()
            if cache_enabled is not None:
                url_options_kwargs['cache_enabled'] = cache_enabled
            if url_signature_enabled is not None:
                url_options_kwargs['url_signature_enabled'] = url_signature_enabled
            url1 = make_qr_code_url(TEST_TEXT, QRCodeOptions(image_format='png', size=1), **url_options_kwargs)
            url2 = qr_url_from_text(TEST_TEXT, image_format='png', size=1, **url_options_kwargs)
            url3 = qr_url_from_text(TEST_TEXT, image_format='PNG', size=1, **url_options_kwargs)
            url4 = qr_url_from_text(TEST_TEXT, options=QRCodeOptions(image_format='PNG', size=1), **url_options_kwargs)
            url = url1
            if url_signature_enabled is not False:
                urls = get_urls_without_token_for_comparison(url1, url2, url3, url4)
            else:
                urls = [url1, url2, url3, url4]
            self.assertEqual(urls[0], urls[1])
            self.assertEqual(urls[0], urls[2])
            self.assertEqual(urls[0], urls[3])
            response = self.client.get(url)
            print("\t - cache_enabled=%s, url_signature_enabled=%s" % (cache_enabled, url_signature_enabled))
            expected_status_code = 200
            if url_signature_enabled is False and not allows_external_request_from_user(None):
                expected_status_code = 403
            self.assertEqual(response.status_code, expected_status_code)
            if expected_status_code == 200:
                self.assertEqual(response.content, TestQRUrlFromTextResult.png_result)
            if is_first and REFRESH_REFERENCE_IMAGES:
                write_png_content_to_file(TestQRUrlFromTextResult.ref_base_file_name + PNG_REF_SUFFIX,
                                          response.content)
                is_first = False

    @override_settings(CACHES=OVERRIDE_CACHES_SETTING, QR_CODE_CACHE_ALIAS=None)
    def test_svg_with_cache_but_no_alias(self):
        self.test_svg_url()

    @override_settings(CACHES=OVERRIDE_CACHES_SETTING)
    def test_png_with_cache(self):
        self.test_png_url()

    @override_settings(CACHES=OVERRIDE_CACHES_SETTING, QR_CODE_CACHE_ALIAS=None)
    def test_png_with_cache_but_no_alias(self):
        self.test_png_url()

    @override_settings(QR_CODE_URL_PROTECTION=dict(TOKEN_LENGTH=30, SIGNING_KEY='my-secret-signing-key',
                                                   SIGNING_SALT='my-signing-salt',
                                                   ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER=True))
    def test_with_url_protection_settings_1(self):
        self.test_svg_url()
        self.test_png_url()
        response = self.client.get(make_qr_code_url(TEST_TEXT, url_signature_enabled=False, cache_enabled=False))
        # Registered users can access the URL externally, but since we are not logged in, we must expect an HTTP 403.
        self.assertEqual(response.status_code, 403)

    @override_settings(QR_CODE_URL_PROTECTION=dict(ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER=False))
    def test_with_url_protection_settings_2(self):
        self.test_svg_url()
        self.test_png_url()
        response = self.client.get(make_qr_code_url(TEST_TEXT, url_signature_enabled=False, cache_enabled=False))
        self.assertEqual(response.status_code, 403)

    @override_settings(QR_CODE_URL_PROTECTION=dict(ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER=lambda user: False))
    def test_with_url_protection_settings_3(self):
        self.test_svg_url()
        self.test_png_url()
        response = self.client.get(make_qr_code_url(TEST_TEXT, url_signature_enabled=False, cache_enabled=False))
        self.assertEqual(response.status_code, 403)

    @override_settings(QR_CODE_URL_PROTECTION=dict(ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER=lambda user: True))
    def test_with_url_protection_settings_4(self):
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

    def test_svg_error_correction(self):
        base_file_name = 'qrfromtext_error_correction'
        for correction_level in ERROR_CORRECTION_DICT:
            print('Testing SVG URL with error correction: %s' % correction_level)
            url1 = make_qr_code_url(COMPLEX_TEST_TEXT, QRCodeOptions(error_correction=correction_level), cache_enabled=False)
            url2 = qr_url_from_text(COMPLEX_TEST_TEXT, error_correction=correction_level, cache_enabled=False)
            url3 = qr_url_from_text(COMPLEX_TEST_TEXT, error_correction=correction_level, image_format='svg', cache_enabled=False)
            url4 = qr_url_from_text(COMPLEX_TEST_TEXT, error_correction=correction_level, image_format='SVG', cache_enabled=False)
            url5 = qr_url_from_text(COMPLEX_TEST_TEXT, options=QRCodeOptions(error_correction=correction_level, image_format='SVG'), cache_enabled=False)
            # Using an invalid image format should fallback to SVG.
            url6 = qr_url_from_text(COMPLEX_TEST_TEXT, error_correction=correction_level, image_format='invalid-format-name', cache_enabled=False)
            url = url1
            urls = get_urls_without_token_for_comparison(url1, url2, url3, url4, url5, url6)
            self.assertEqual(urls[0], urls[1])
            self.assertEqual(urls[0], urls[2])
            self.assertEqual(urls[0], urls[3])
            self.assertEqual(urls[0], urls[4])
            self.assertEqual(urls[0], urls[5])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            source_image_data = response.content.decode('utf-8')
            # Skip header and adjust tag format.
            source_image_data = source_image_data[source_image_data.index('\n') + 1:]
            source_image_data = _make_closing_path_tag(source_image_data)
            ref_file_name = '%s_%s%s' % (base_file_name, correction_level.lower(), SVG_REF_SUFFIX)
            if REFRESH_REFERENCE_IMAGES:
                write_svg_content_to_file(ref_file_name, source_image_data)
            ref_image_data = get_svg_content_from_file_name(ref_file_name)
            self.assertEqual(source_image_data, ref_image_data)

    def test_png_error_correction(self):
        base_file_name = 'qrfromtext_error_correction'
        for correction_level in ERROR_CORRECTION_DICT:
            print('Testing PNG URL with error correction: %s' % correction_level)
            url1 = make_qr_code_url(COMPLEX_TEST_TEXT, QRCodeOptions(error_correction=correction_level, image_format='png'), cache_enabled=False)
            url2 = make_qr_code_url(COMPLEX_TEST_TEXT, QRCodeOptions(error_correction=correction_level, image_format='PNG'), cache_enabled=False)
            url3 = qr_url_from_text(COMPLEX_TEST_TEXT, error_correction=correction_level, image_format='png', cache_enabled=False)
            url4 = qr_url_from_text(COMPLEX_TEST_TEXT, error_correction=correction_level, image_format='PNG', cache_enabled=False)
            url5 = qr_url_from_text(COMPLEX_TEST_TEXT, options=QRCodeOptions(error_correction=correction_level, image_format='PNG'), cache_enabled=False)
            url = url1
            urls = get_urls_without_token_for_comparison(url1, url2, url3, url4, url5)
            self.assertEqual(urls[0], urls[1])
            self.assertEqual(urls[0], urls[2])
            self.assertEqual(urls[0], urls[3])
            self.assertEqual(urls[0], urls[4])
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            source_image_data = response.content
            ref_file_name = '%s_%s%s' % (base_file_name, correction_level.lower(), PNG_REF_SUFFIX)
            if REFRESH_REFERENCE_IMAGES:
                write_png_content_to_file(ref_file_name, source_image_data)
            ref_image_data = get_png_content_from_file_name(ref_file_name)
            self.assertEqual(source_image_data, ref_image_data)


class TestQRFromTextSvgResult(SimpleTestCase):
    """
    Ensures that produced QR codes in SVG format coincide with verified references.

    The tests cover direct call to tag function, rendering of tag, and direct call to qr_code API.
    """

    def test_size(self):
        base_ref_file_name = 'qrfromtext_size_'
        sizes = ['t', 'T', 's', 'S', None, -1, 0, 'm', 'M', 'l', 'L', 'h', 'H', '6', 6, '8', 8, '10', 10]
        size_names = ['tiny'] * 2 + ['small'] * 2 + ['medium'] * 5 + ['large'] * 2 + ['huge'] * 2 + ['6'] * 2 + ['8'] * 2 + ['10'] * 2
        for i in range(len(sizes)):
            size = sizes[i]
            print('Testing SVG with size %s' % size)
            size_name = size_names[i]
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(size=size))
            qr2 = qr_from_text(TEST_TEXT, size=size)
            qr3 = qr_from_text(TEST_TEXT, size=size, image_format='svg')
            qr4 = qr_from_text(TEST_TEXT, options=QRCodeOptions(size=size, image_format='svg'))
            qr5 = qr_from_text(TEST_TEXT, size=size, image_format='invalid-format-name')
            result_file_name = '%s%s%s' % (base_ref_file_name, size_name, SVG_REF_SUFFIX)
            if REFRESH_REFERENCE_IMAGES:
                write_svg_content_to_file(result_file_name, _make_xml_header() + '\n' + qr1)
            result = get_svg_content_from_file_name(result_file_name, skip_header=True)
            self.assertEqual(qr1, qr2)
            self.assertEqual(qr1, qr3)
            self.assertEqual(qr1, qr4)
            self.assertEqual(qr1, qr5)
            self.assertEqual(qr1, result)

    def test_version(self):
        versions = [None, -1, 0, 41, '-1', '0', '41', 'blabla', 1, '1', 2, '2', 4, '4']
        default_result = """<svg height="52.2mm" version="1.1" viewBox="0 0 52.2 52.2" width="52.2mm" xmlns="http://www.w3.org/2000/svg"><path d="M 36 18 L 36 19.8 L 37.8 19.8 L 37.8 18 z M 32.4 37.8 L 32.4 39.6 L 34.2 39.6 L 34.2 37.8 z M 28.8 9 L 28.8 10.8 L 30.6 10.8 L 30.6 9 z M 25.2 37.8 L 25.2 39.6 L 27.0 39.6 L 27.0 37.8 z M 7.2 43.2 L 7.2 45.0 L 9.0 45.0 L 9.0 43.2 z M 36 23.4 L 36 25.2 L 37.8 25.2 L 37.8 23.4 z M 32.4 14.4 L 32.4 16.2 L 34.2 16.2 L 34.2 14.4 z M 39.6 14.4 L 39.6 16.2 L 41.4 16.2 L 41.4 14.4 z M 30.6 37.8 L 30.6 39.6 L 32.4 39.6 L 32.4 37.8 z M 9 18 L 9 19.8 L 10.8 19.8 L 10.8 18 z M 7.2 25.2 L 7.2 27.0 L 9.0 27.0 L 9.0 25.2 z M 39.6 41.4 L 39.6 43.2 L 41.4 43.2 L 41.4 41.4 z M 21.6 16.2 L 21.6 18.0 L 23.4 18.0 L 23.4 16.2 z M 16.2 21.6 L 16.2 23.4 L 18.0 23.4 L 18.0 21.6 z M 14.4 7.2 L 14.4 9.0 L 16.2 9.0 L 16.2 7.2 z M 25.2 21.6 L 25.2 23.4 L 27.0 23.4 L 27.0 21.6 z M 23.4 7.2 L 23.4 9.0 L 25.2 9.0 L 25.2 7.2 z M 25.2 19.8 L 25.2 21.6 L 27.0 21.6 L 27.0 19.8 z M 36 12.6 L 36 14.4 L 37.8 14.4 L 37.8 12.6 z M 18 25.2 L 18 27.0 L 19.8 27.0 L 19.8 25.2 z M 28.8 18 L 28.8 19.8 L 30.6 19.8 L 30.6 18 z M 41.4 32.4 L 41.4 34.2 L 43.2 34.2 L 43.2 32.4 z M 37.8 10.8 L 37.8 12.6 L 39.6 12.6 L 39.6 10.8 z M 7.2 37.8 L 7.2 39.6 L 9.0 39.6 L 9.0 37.8 z M 32.4 9 L 32.4 10.8 L 34.2 10.8 L 34.2 9 z M 43.2 23.4 L 43.2 25.2 L 45.0 25.2 L 45.0 23.4 z M 39.6 23.4 L 39.6 25.2 L 41.4 25.2 L 41.4 23.4 z M 7.2 14.4 L 7.2 16.2 L 9.0 16.2 L 9.0 14.4 z M 43.2 14.4 L 43.2 16.2 L 45.0 16.2 L 45.0 14.4 z M 21.6 34.2 L 21.6 36.0 L 23.4 36.0 L 23.4 34.2 z M 14.4 25.2 L 14.4 27.0 L 16.2 27.0 L 16.2 25.2 z M 12.6 10.8 L 12.6 12.6 L 14.4 12.6 L 14.4 10.8 z M 10.8 18 L 10.8 19.8 L 12.6 19.8 L 12.6 18 z M 23.4 32.4 L 23.4 34.2 L 25.2 34.2 L 25.2 32.4 z M 21.6 10.8 L 21.6 12.6 L 23.4 12.6 L 23.4 10.8 z M 18 7.2 L 18 9.0 L 19.8 9.0 L 19.8 7.2 z M 14.4 36 L 14.4 37.8 L 16.2 37.8 L 16.2 36 z M 27 7.2 L 27 9.0 L 28.8 9.0 L 28.8 7.2 z M 23.4 36 L 23.4 37.8 L 25.2 37.8 L 25.2 36 z M 36 7.2 L 36 9.0 L 37.8 9.0 L 37.8 7.2 z M 37.8 30.6 L 37.8 32.4 L 39.6 32.4 L 39.6 30.6 z M 36 41.4 L 36 43.2 L 37.8 43.2 L 37.8 41.4 z M 32.4 10.8 L 32.4 12.6 L 34.2 12.6 L 34.2 10.8 z M 30.6 25.2 L 30.6 27.0 L 32.4 27.0 L 32.4 25.2 z M 10.8 37.8 L 10.8 39.6 L 12.6 39.6 L 12.6 37.8 z M 39.6 25.2 L 39.6 27.0 L 41.4 27.0 L 41.4 25.2 z M 7.2 9 L 7.2 10.8 L 9.0 10.8 L 9.0 9 z M 9 28.8 L 9 30.6 L 10.8 30.6 L 10.8 28.8 z M 21.6 28.8 L 21.6 30.6 L 23.4 30.6 L 23.4 28.8 z M 16.2 32.4 L 16.2 34.2 L 18.0 34.2 L 18.0 32.4 z M 12.6 39.6 L 12.6 41.4 L 14.4 41.4 L 14.4 39.6 z M 21.6 39.6 L 21.6 41.4 L 23.4 41.4 L 23.4 39.6 z M 27 34.2 L 27 36.0 L 28.8 36.0 L 28.8 34.2 z M 23.4 41.4 L 23.4 43.2 L 25.2 43.2 L 25.2 41.4 z M 34.2 36 L 34.2 37.8 L 36.0 37.8 L 36.0 36 z M 32.4 21.6 L 32.4 23.4 L 34.2 23.4 L 34.2 21.6 z M 18 36 L 18 37.8 L 19.8 37.8 L 19.8 36 z M 28.8 21.6 L 28.8 23.4 L 30.6 23.4 L 30.6 21.6 z M 43.2 36 L 43.2 37.8 L 45.0 37.8 L 45.0 36 z M 39.6 7.2 L 39.6 9.0 L 41.4 9.0 L 41.4 7.2 z M 37.8 21.6 L 37.8 23.4 L 39.6 23.4 L 39.6 21.6 z M 43.2 12.6 L 43.2 14.4 L 45.0 14.4 L 45.0 12.6 z M 10.8 39.6 L 10.8 41.4 L 12.6 41.4 L 12.6 39.6 z M 39.6 34.2 L 39.6 36.0 L 41.4 36.0 L 41.4 34.2 z M 7.2 32.4 L 7.2 34.2 L 9.0 34.2 L 9.0 32.4 z M 10.8 28.8 L 10.8 30.6 L 12.6 30.6 L 12.6 28.8 z M 12.6 37.8 L 12.6 39.6 L 14.4 39.6 L 14.4 37.8 z M 18 32.4 L 18 34.2 L 19.8 34.2 L 19.8 32.4 z M 27 25.2 L 27 27.0 L 28.8 27.0 L 28.8 25.2 z M 37.8 18 L 37.8 19.8 L 39.6 19.8 L 39.6 18 z M 32.4 16.2 L 32.4 18.0 L 34.2 18.0 L 34.2 16.2 z M 28.8 30.6 L 28.8 32.4 L 30.6 32.4 L 30.6 30.6 z M 37.8 27 L 37.8 28.8 L 39.6 28.8 L 39.6 27 z M 34.2 7.2 L 34.2 9.0 L 36.0 9.0 L 36.0 7.2 z M 43.2 7.2 L 43.2 9.0 L 45.0 9.0 L 45.0 7.2 z M 7.2 27 L 7.2 28.8 L 9.0 28.8 L 9.0 27 z M 12.6 18 L 12.6 19.8 L 14.4 19.8 L 14.4 18 z M 10.8 10.8 L 10.8 12.6 L 12.6 12.6 L 12.6 10.8 z M 9 25.2 L 9 27.0 L 10.8 27.0 L 10.8 25.2 z M 21.6 18 L 21.6 19.8 L 23.4 19.8 L 23.4 18 z M 23.4 19.8 L 23.4 21.6 L 25.2 21.6 L 25.2 19.8 z M 18 14.4 L 18 16.2 L 19.8 16.2 L 19.8 14.4 z M 27 14.4 L 27 16.2 L 28.8 16.2 L 28.8 14.4 z M 25.2 14.4 L 25.2 16.2 L 27.0 16.2 L 27.0 14.4 z M 23.4 43.2 L 23.4 45.0 L 25.2 45.0 L 25.2 43.2 z M 36 14.4 L 36 16.2 L 37.8 16.2 L 37.8 14.4 z M 28.8 19.8 L 28.8 21.6 L 30.6 21.6 L 30.6 19.8 z M 7.2 39.6 L 7.2 41.4 L 9.0 41.4 L 9.0 39.6 z M 32.4 18 L 32.4 19.8 L 34.2 19.8 L 34.2 18 z M 28.8 39.6 L 28.8 41.4 L 30.6 41.4 L 30.6 39.6 z M 39.6 18 L 39.6 19.8 L 41.4 19.8 L 41.4 18 z M 7.2 16.2 L 7.2 18.0 L 9.0 18.0 L 9.0 16.2 z M 30.6 41.4 L 30.6 43.2 L 32.4 43.2 L 32.4 41.4 z M 43.2 16.2 L 43.2 18.0 L 45.0 18.0 L 45.0 16.2 z M 9 7.2 L 9 9.0 L 10.8 9.0 L 10.8 7.2 z M 7.2 21.6 L 7.2 23.4 L 9.0 23.4 L 9.0 21.6 z M 23.4 30.6 L 23.4 32.4 L 25.2 32.4 L 25.2 30.6 z M 21.6 12.6 L 21.6 14.4 L 23.4 14.4 L 23.4 12.6 z M 14.4 18 L 14.4 19.8 L 16.2 19.8 L 16.2 18 z M 18 9 L 18 10.8 L 19.8 10.8 L 19.8 9 z M 14.4 37.8 L 14.4 39.6 L 16.2 39.6 L 16.2 37.8 z M 32.4 28.8 L 32.4 30.6 L 34.2 30.6 L 34.2 28.8 z M 16.2 43.2 L 16.2 45.0 L 18.0 45.0 L 18.0 43.2 z M 28.8 14.4 L 28.8 16.2 L 30.6 16.2 L 30.6 14.4 z M 18 43.2 L 18 45.0 L 19.8 45.0 L 19.8 43.2 z M 25.2 43.2 L 25.2 45.0 L 27.0 45.0 L 27.0 43.2 z M 27 43.2 L 27 45.0 L 28.8 45.0 L 28.8 43.2 z M 34.2 23.4 L 34.2 25.2 L 36.0 25.2 L 36.0 23.4 z M 32.4 12.6 L 32.4 14.4 L 34.2 14.4 L 34.2 12.6 z M 30.6 23.4 L 30.6 25.2 L 32.4 25.2 L 32.4 23.4 z M 36 43.2 L 36 45.0 L 37.8 45.0 L 37.8 43.2 z M 39.6 27 L 39.6 28.8 L 41.4 28.8 L 41.4 27 z M 7.2 10.8 L 7.2 12.6 L 9.0 12.6 L 9.0 10.8 z M 37.8 37.8 L 37.8 39.6 L 39.6 39.6 L 39.6 37.8 z M 21.6 30.6 L 21.6 32.4 L 23.4 32.4 L 23.4 30.6 z M 14.4 21.6 L 14.4 23.4 L 16.2 23.4 L 16.2 21.6 z M 12.6 7.2 L 12.6 9.0 L 14.4 9.0 L 14.4 7.2 z M 10.8 21.6 L 10.8 23.4 L 12.6 23.4 L 12.6 21.6 z M 23.4 21.6 L 23.4 23.4 L 25.2 23.4 L 25.2 21.6 z M 25.2 34.2 L 25.2 36.0 L 27.0 36.0 L 27.0 34.2 z M 18 10.8 L 18 12.6 L 19.8 12.6 L 19.8 10.8 z M 23.4 39.6 L 23.4 41.4 L 25.2 41.4 L 25.2 39.6 z M 32.4 23.4 L 32.4 25.2 L 34.2 25.2 L 34.2 23.4 z M 18 37.8 L 18 39.6 L 19.8 39.6 L 19.8 37.8 z M 28.8 23.4 L 28.8 25.2 L 30.6 25.2 L 30.6 23.4 z M 9 43.2 L 9 45.0 L 10.8 45.0 L 10.8 43.2 z M 37.8 34.2 L 37.8 36.0 L 39.6 36.0 L 39.6 34.2 z M 36 37.8 L 36 39.6 L 37.8 39.6 L 37.8 37.8 z M 30.6 28.8 L 30.6 30.6 L 32.4 30.6 L 32.4 28.8 z M 43.2 28.8 L 43.2 30.6 L 45.0 30.6 L 45.0 28.8 z M 28.8 43.2 L 28.8 45.0 L 30.6 45.0 L 30.6 43.2 z M 7.2 34.2 L 7.2 36.0 L 9.0 36.0 L 9.0 34.2 z M 12.6 25.2 L 12.6 27.0 L 14.4 27.0 L 14.4 25.2 z M 9 32.4 L 9 34.2 L 10.8 34.2 L 10.8 32.4 z M 23.4 27 L 23.4 28.8 L 25.2 28.8 L 25.2 27 z M 16.2 7.2 L 16.2 9.0 L 18.0 9.0 L 18.0 7.2 z M 12.6 36 L 12.6 37.8 L 14.4 37.8 L 14.4 36 z M 25.2 7.2 L 25.2 9.0 L 27.0 9.0 L 27.0 7.2 z M 21.6 36 L 21.6 37.8 L 23.4 37.8 L 23.4 36 z M 18 34.2 L 18 36.0 L 19.8 36.0 L 19.8 34.2 z M 36 27 L 36 28.8 L 37.8 28.8 L 37.8 27 z M 32.4 25.2 L 32.4 27.0 L 34.2 27.0 L 34.2 25.2 z M 18 39.6 L 18 41.4 L 19.8 41.4 L 19.8 39.6 z M 28.8 32.4 L 28.8 34.2 L 30.6 34.2 L 30.6 32.4 z M 41.4 18 L 41.4 19.8 L 43.2 19.8 L 43.2 18 z M 39.6 10.8 L 39.6 12.6 L 41.4 12.6 L 41.4 10.8 z M 37.8 25.2 L 37.8 27.0 L 39.6 27.0 L 39.6 25.2 z M 30.6 34.2 L 30.6 36.0 L 32.4 36.0 L 32.4 34.2 z M 43.2 9 L 43.2 10.8 L 45.0 10.8 L 45.0 9 z M 10.8 43.2 L 10.8 45.0 L 12.6 45.0 L 12.6 43.2 z M 12.6 23.4 L 12.6 25.2 L 14.4 25.2 L 14.4 23.4 z M 10.8 12.6 L 10.8 14.4 L 12.6 14.4 L 12.6 12.6 z M 21.6 19.8 L 21.6 21.6 L 23.4 21.6 L 23.4 19.8 z M 14.4 10.8 L 14.4 12.6 L 16.2 12.6 L 16.2 10.8 z M 10.8 32.4 L 10.8 34.2 L 12.6 34.2 L 12.6 32.4 z M 18 16.2 L 18 18.0 L 19.8 18.0 L 19.8 16.2 z M 27 19.8 L 27 21.6 L 28.8 21.6 L 28.8 19.8 z M 25.2 16.2 L 25.2 18.0 L 27.0 18.0 L 27.0 16.2 z M 18 21.6 L 18 23.4 L 19.8 23.4 L 19.8 21.6 z M 32.4 36 L 32.4 37.8 L 34.2 37.8 L 34.2 36 z M 41.4 36 L 41.4 37.8 L 43.2 37.8 L 43.2 36 z M 37.8 7.2 L 37.8 9.0 L 39.6 9.0 L 39.6 7.2 z M 36 21.6 L 36 23.4 L 37.8 23.4 L 37.8 21.6 z M 7.2 41.4 L 7.2 43.2 L 9.0 43.2 L 9.0 41.4 z M 28.8 41.4 L 28.8 43.2 L 30.6 43.2 L 30.6 41.4 z M 7.2 18 L 7.2 19.8 L 9.0 19.8 L 9.0 18 z M 34.2 18 L 34.2 19.8 L 36.0 19.8 L 36.0 18 z M 43.2 18 L 43.2 19.8 L 45.0 19.8 L 45.0 18 z M 39.6 39.6 L 39.6 41.4 L 41.4 41.4 L 41.4 39.6 z M 12.6 14.4 L 12.6 16.2 L 14.4 16.2 L 14.4 14.4 z M 10.8 14.4 L 10.8 16.2 L 12.6 16.2 L 12.6 14.4 z M 23.4 28.8 L 23.4 30.6 L 25.2 30.6 L 25.2 28.8 z M 21.6 14.4 L 21.6 16.2 L 23.4 16.2 L 23.4 14.4 z M 25.2 27 L 25.2 28.8 L 27.0 28.8 L 27.0 27 z M 18 18 L 18 19.8 L 19.8 19.8 L 19.8 18 z M 16.2 18 L 16.2 19.8 L 18.0 19.8 L 18.0 18 z M 14.4 39.6 L 14.4 41.4 L 16.2 41.4 L 16.2 39.6 z M 27 10.8 L 27 12.6 L 28.8 12.6 L 28.8 10.8 z M 25.2 18 L 25.2 19.8 L 27.0 19.8 L 27.0 18 z M 36 10.8 L 36 12.6 L 37.8 12.6 L 37.8 10.8 z M 28.8 16.2 L 28.8 18.0 L 30.6 18.0 L 30.6 16.2 z M 37.8 12.6 L 37.8 14.4 L 39.6 14.4 L 39.6 12.6 z M 34.2 21.6 L 34.2 23.4 L 36.0 23.4 L 36.0 21.6 z M 32.4 7.2 L 32.4 9.0 L 34.2 9.0 L 34.2 7.2 z M 7.2 36 L 7.2 37.8 L 9.0 37.8 L 9.0 36 z M 28.8 36 L 28.8 37.8 L 30.6 37.8 L 30.6 36 z M 41.4 7.2 L 41.4 9.0 L 43.2 9.0 L 43.2 7.2 z M 39.6 21.6 L 39.6 23.4 L 41.4 23.4 L 41.4 21.6 z M 7.2 12.6 L 7.2 14.4 L 9.0 14.4 L 9.0 12.6 z M 12.6 32.4 L 12.6 34.2 L 14.4 34.2 L 14.4 32.4 z M 14.4 23.4 L 14.4 25.2 L 16.2 25.2 L 16.2 23.4 z M 12.6 12.6 L 12.6 14.4 L 14.4 14.4 L 14.4 12.6 z M 10.8 23.4 L 10.8 25.2 L 12.6 25.2 L 12.6 23.4 z M 23.4 34.2 L 23.4 36.0 L 25.2 36.0 L 25.2 34.2 z M 16.2 28.8 L 16.2 30.6 L 18.0 30.6 L 18.0 28.8 z M 14.4 14.4 L 14.4 16.2 L 16.2 16.2 L 16.2 14.4 z M 12.6 43.2 L 12.6 45.0 L 14.4 45.0 L 14.4 43.2 z M 25.2 28.8 L 25.2 30.6 L 27.0 30.6 L 27.0 28.8 z M 21.6 43.2 L 21.6 45.0 L 23.4 45.0 L 23.4 43.2 z M 18 12.6 L 18 14.4 L 19.8 14.4 L 19.8 12.6 z M 23.4 37.8 L 23.4 39.6 L 25.2 39.6 L 25.2 37.8 z M 34.2 39.6 L 34.2 41.4 L 36.0 41.4 L 36.0 39.6 z M 32.4 32.4 L 32.4 34.2 L 34.2 34.2 L 34.2 32.4 z M 41.4 25.2 L 41.4 27.0 L 43.2 27.0 L 43.2 25.2 z M 34.2 34.2 L 34.2 36.0 L 36.0 36.0 L 36.0 34.2 z M 30.6 27 L 30.6 28.8 L 32.4 28.8 L 32.4 27 z M 10.8 36 L 10.8 37.8 L 12.6 37.8 L 12.6 36 z M 7.2 7.2 L 7.2 9.0 L 9.0 9.0 L 9.0 7.2 z M 37.8 41.4 L 37.8 43.2 L 39.6 43.2 L 39.6 41.4 z M 14.4 32.4 L 14.4 34.2 L 16.2 34.2 L 16.2 32.4 z M 25.2 9 L 25.2 10.8 L 27.0 10.8 L 27.0 9 z M 21.6 37.8 L 21.6 39.6 L 23.4 39.6 L 23.4 37.8 z M 18 28.8 L 18 30.6 L 19.8 30.6 L 19.8 28.8 z M 32.4 43.2 L 32.4 45.0 L 34.2 45.0 L 34.2 43.2 z M 14.4 43.2 L 14.4 45.0 L 16.2 45.0 L 16.2 43.2 z M 27 28.8 L 27 30.6 L 28.8 30.6 L 28.8 28.8 z M 41.4 43.2 L 41.4 45.0 L 43.2 45.0 L 43.2 43.2 z M 37.8 14.4 L 37.8 16.2 L 39.6 16.2 L 39.6 14.4 z M 19.8 23.4 L 19.8 25.2 L 21.6 25.2 L 21.6 23.4 z M 34.2 37.8 L 34.2 39.6 L 36.0 39.6 L 36.0 37.8 z M 18 41.4 L 18 43.2 L 19.8 43.2 L 19.8 41.4 z M 28.8 34.2 L 28.8 36.0 L 30.6 36.0 L 30.6 34.2 z M 39.6 12.6 L 39.6 14.4 L 41.4 14.4 L 41.4 12.6 z M 37.8 23.4 L 37.8 25.2 L 39.6 25.2 L 39.6 23.4 z M 43.2 10.8 L 43.2 12.6 L 45.0 12.6 L 45.0 10.8 z M 39.6 32.4 L 39.6 34.2 L 41.4 34.2 L 41.4 32.4 z M 12.6 21.6 L 12.6 23.4 L 14.4 23.4 L 14.4 21.6 z M 10.8 7.2 L 10.8 9.0 L 12.6 9.0 L 12.6 7.2 z M 14.4 12.6 L 14.4 14.4 L 16.2 14.4 L 16.2 12.6 z M 23.4 16.2 L 23.4 18.0 L 25.2 18.0 L 25.2 16.2 z" id="qr-path" style="fill:#000000;fill-opacity:1;fill-rule:nonzero;stroke:none"></path></svg>"""
        result_version_2 = """<svg height="59.4mm" version="1.1" viewBox="0 0 59.4 59.4" width="59.4mm" xmlns="http://www.w3.org/2000/svg"><path d="M 36 18 L 36 19.8 L 37.8 19.8 L 37.8 18 z M 28.8 9 L 28.8 10.8 L 30.6 10.8 L 30.6 9 z M 27 27 L 27 28.8 L 28.8 28.8 L 28.8 27 z M 7.2 43.2 L 7.2 45.0 L 9.0 45.0 L 9.0 43.2 z M 36 23.4 L 36 25.2 L 37.8 25.2 L 37.8 23.4 z M 43.2 43.2 L 43.2 45.0 L 45.0 45.0 L 45.0 43.2 z M 39.6 14.4 L 39.6 16.2 L 41.4 16.2 L 41.4 14.4 z M 37.8 43.2 L 37.8 45.0 L 39.6 45.0 L 39.6 43.2 z M 34.2 9 L 34.2 10.8 L 36.0 10.8 L 36.0 9 z M 50.4 14.4 L 50.4 16.2 L 52.2 16.2 L 52.2 14.4 z M 45 23.4 L 45 25.2 L 46.8 25.2 L 46.8 23.4 z M 10.8 46.8 L 10.8 48.6 L 12.6 48.6 L 12.6 46.8 z M 9 18 L 9 19.8 L 10.8 19.8 L 10.8 18 z M 46.8 18 L 46.8 19.8 L 48.6 19.8 L 48.6 18 z M 45 18 L 45 19.8 L 46.8 19.8 L 46.8 18 z M 9 27 L 9 28.8 L 10.8 28.8 L 10.8 27 z M 21.6 16.2 L 21.6 18.0 L 23.4 18.0 L 23.4 16.2 z M 14.4 7.2 L 14.4 9.0 L 16.2 9.0 L 16.2 7.2 z M 12.6 50.4 L 12.6 52.2 L 14.4 52.2 L 14.4 50.4 z M 21.6 50.4 L 21.6 52.2 L 23.4 52.2 L 23.4 50.4 z M 25.2 19.8 L 25.2 21.6 L 27.0 21.6 L 27.0 19.8 z M 23.4 45 L 23.4 46.8 L 25.2 46.8 L 25.2 45 z M 36 12.6 L 36 14.4 L 37.8 14.4 L 37.8 12.6 z M 18 25.2 L 18 27.0 L 19.8 27.0 L 19.8 25.2 z M 16.2 39.6 L 16.2 41.4 L 18.0 41.4 L 18.0 39.6 z M 28.8 18 L 28.8 19.8 L 30.6 19.8 L 30.6 18 z M 32.4 39.6 L 32.4 41.4 L 34.2 41.4 L 34.2 39.6 z M 25.2 39.6 L 25.2 41.4 L 27.0 41.4 L 27.0 39.6 z M 27 46.8 L 27 48.6 L 28.8 48.6 L 28.8 46.8 z M 34.2 27 L 34.2 28.8 L 36.0 28.8 L 36.0 27 z M 50.4 32.4 L 50.4 34.2 L 52.2 34.2 L 52.2 32.4 z M 30.6 19.8 L 30.6 21.6 L 32.4 21.6 L 32.4 19.8 z M 28.8 37.8 L 28.8 39.6 L 30.6 39.6 L 30.6 37.8 z M 39.6 23.4 L 39.6 25.2 L 41.4 25.2 L 41.4 23.4 z M 7.2 14.4 L 7.2 16.2 L 9.0 16.2 L 9.0 14.4 z M 50.4 9 L 50.4 10.8 L 52.2 10.8 L 52.2 9 z M 34.2 14.4 L 34.2 16.2 L 36.0 16.2 L 36.0 14.4 z M 45 28.8 L 45 30.6 L 46.8 30.6 L 46.8 28.8 z M 43.2 14.4 L 43.2 16.2 L 45.0 16.2 L 45.0 14.4 z M 30.6 43.2 L 30.6 45.0 L 32.4 45.0 L 32.4 43.2 z M 39.6 43.2 L 39.6 45.0 L 41.4 45.0 L 41.4 43.2 z M 46.8 12.6 L 46.8 14.4 L 48.6 14.4 L 48.6 12.6 z M 12.6 10.8 L 12.6 12.6 L 14.4 12.6 L 14.4 10.8 z M 10.8 18 L 10.8 19.8 L 12.6 19.8 L 12.6 18 z M 21.6 10.8 L 21.6 12.6 L 23.4 12.6 L 23.4 10.8 z M 25.2 30.6 L 25.2 32.4 L 27.0 32.4 L 27.0 30.6 z M 23.4 12.6 L 23.4 14.4 L 25.2 14.4 L 25.2 12.6 z M 18 7.2 L 18 9.0 L 19.8 9.0 L 19.8 7.2 z M 16.2 50.4 L 16.2 52.2 L 18.0 52.2 L 18.0 50.4 z M 14.4 36 L 14.4 37.8 L 16.2 37.8 L 16.2 36 z M 25.2 50.4 L 25.2 52.2 L 27.0 52.2 L 27.0 50.4 z M 23.4 36 L 23.4 37.8 L 25.2 37.8 L 25.2 36 z M 50.4 50.4 L 50.4 52.2 L 52.2 52.2 L 52.2 50.4 z M 18 48.6 L 18 50.4 L 19.8 50.4 L 19.8 48.6 z M 43.2 41.4 L 43.2 43.2 L 45.0 43.2 L 45.0 41.4 z M 41.4 30.6 L 41.4 32.4 L 43.2 32.4 L 43.2 30.6 z M 25.2 48.6 L 25.2 50.4 L 27.0 50.4 L 27.0 48.6 z M 34.2 32.4 L 34.2 34.2 L 36.0 34.2 L 36.0 32.4 z M 45 36 L 45 37.8 L 46.8 37.8 L 46.8 36 z M 30.6 25.2 L 30.6 27.0 L 32.4 27.0 L 32.4 25.2 z M 36 41.4 L 36 43.2 L 37.8 43.2 L 37.8 41.4 z M 7.2 9 L 7.2 10.8 L 9.0 10.8 L 9.0 9 z M 45 34.2 L 45 36.0 L 46.8 36.0 L 46.8 34.2 z M 30.6 48.6 L 30.6 50.4 L 32.4 50.4 L 32.4 48.6 z M 9 28.8 L 9 30.6 L 10.8 30.6 L 10.8 28.8 z M 23.4 23.4 L 23.4 25.2 L 25.2 25.2 L 25.2 23.4 z M 12.6 39.6 L 12.6 41.4 L 14.4 41.4 L 14.4 39.6 z M 21.6 39.6 L 21.6 41.4 L 23.4 41.4 L 23.4 39.6 z M 32.4 45 L 32.4 46.8 L 34.2 46.8 L 34.2 45 z M 14.4 45 L 14.4 46.8 L 16.2 46.8 L 16.2 45 z M 41.4 48.6 L 41.4 50.4 L 43.2 50.4 L 43.2 48.6 z M 23.4 41.4 L 23.4 43.2 L 25.2 43.2 L 25.2 41.4 z M 19.8 21.6 L 19.8 23.4 L 21.6 23.4 L 21.6 21.6 z M 18 36 L 18 37.8 L 19.8 37.8 L 19.8 36 z M 30.6 7.2 L 30.6 9.0 L 32.4 9.0 L 32.4 7.2 z M 28.8 21.6 L 28.8 23.4 L 30.6 23.4 L 30.6 21.6 z M 41.4 21.6 L 41.4 23.4 L 43.2 23.4 L 43.2 21.6 z M 39.6 7.2 L 39.6 9.0 L 41.4 9.0 L 41.4 7.2 z M 27 36 L 27 37.8 L 28.8 37.8 L 28.8 36 z M 50.4 21.6 L 50.4 23.4 L 52.2 23.4 L 52.2 21.6 z M 34.2 36 L 34.2 37.8 L 36.0 37.8 L 36.0 36 z M 30.6 30.6 L 30.6 32.4 L 32.4 32.4 L 32.4 30.6 z M 43.2 12.6 L 43.2 14.4 L 45.0 14.4 L 45.0 12.6 z M 36 36 L 36 37.8 L 37.8 37.8 L 37.8 36 z M 43.2 36 L 43.2 37.8 L 45.0 37.8 L 45.0 36 z M 7.2 32.4 L 7.2 34.2 L 9.0 34.2 L 9.0 32.4 z M 10.8 39.6 L 10.8 41.4 L 12.6 41.4 L 12.6 39.6 z M 48.6 46.8 L 48.6 48.6 L 50.4 48.6 L 50.4 46.8 z M 45 10.8 L 45 12.6 L 46.8 12.6 L 46.8 10.8 z M 46.8 23.4 L 46.8 25.2 L 48.6 25.2 L 48.6 23.4 z M 10.8 28.8 L 10.8 30.6 L 12.6 30.6 L 12.6 28.8 z M 18 32.4 L 18 34.2 L 19.8 34.2 L 19.8 32.4 z M 28.8 10.8 L 28.8 12.6 L 30.6 12.6 L 30.6 10.8 z M 7.2 45 L 7.2 46.8 L 9.0 46.8 L 9.0 45 z M 36 25.2 L 36 27.0 L 37.8 27.0 L 37.8 25.2 z M 32.4 16.2 L 32.4 18.0 L 34.2 18.0 L 34.2 16.2 z M 19.8 34.2 L 19.8 36.0 L 21.6 36.0 L 21.6 34.2 z M 50.4 39.6 L 50.4 41.4 L 52.2 41.4 L 52.2 39.6 z M 43.2 45 L 43.2 46.8 L 45.0 46.8 L 45.0 45 z M 39.6 16.2 L 39.6 18.0 L 41.4 18.0 L 41.4 16.2 z M 9 36 L 9 37.8 L 10.8 37.8 L 10.8 36 z M 34.2 7.2 L 34.2 9.0 L 36.0 9.0 L 36.0 7.2 z M 50.4 16.2 L 50.4 18.0 L 52.2 18.0 L 52.2 16.2 z M 30.6 36 L 30.6 37.8 L 32.4 37.8 L 32.4 36 z M 43.2 7.2 L 43.2 9.0 L 45.0 9.0 L 45.0 7.2 z M 7.2 50.4 L 7.2 52.2 L 9.0 52.2 L 9.0 50.4 z M 39.6 36 L 39.6 37.8 L 41.4 37.8 L 41.4 36 z M 28.8 50.4 L 28.8 52.2 L 30.6 52.2 L 30.6 50.4 z M 12.6 18 L 12.6 19.8 L 14.4 19.8 L 14.4 18 z M 10.8 10.8 L 10.8 12.6 L 12.6 12.6 L 12.6 10.8 z M 9 25.2 L 9 27.0 L 10.8 27.0 L 10.8 25.2 z M 21.6 18 L 21.6 19.8 L 23.4 19.8 L 23.4 18 z M 48.6 18 L 48.6 19.8 L 50.4 19.8 L 50.4 18 z M 46.8 25.2 L 46.8 27.0 L 48.6 27.0 L 48.6 25.2 z M 18 14.4 L 18 16.2 L 19.8 16.2 L 19.8 14.4 z M 27 14.4 L 27 16.2 L 28.8 16.2 L 28.8 14.4 z M 25.2 14.4 L 25.2 16.2 L 27.0 16.2 L 27.0 14.4 z M 36 14.4 L 36 16.2 L 37.8 16.2 L 37.8 14.4 z M 32.4 41.4 L 32.4 43.2 L 34.2 43.2 L 34.2 41.4 z M 28.8 19.8 L 28.8 21.6 L 30.6 21.6 L 30.6 19.8 z M 27 23.4 L 27 25.2 L 28.8 25.2 L 28.8 23.4 z M 25.2 41.4 L 25.2 43.2 L 27.0 43.2 L 27.0 41.4 z M 7.2 39.6 L 7.2 41.4 L 9.0 41.4 L 9.0 39.6 z M 32.4 18 L 32.4 19.8 L 34.2 19.8 L 34.2 18 z M 28.8 39.6 L 28.8 41.4 L 30.6 41.4 L 30.6 39.6 z M 39.6 18 L 39.6 19.8 L 41.4 19.8 L 41.4 18 z M 7.2 16.2 L 7.2 18.0 L 9.0 18.0 L 9.0 16.2 z M 50.4 10.8 L 50.4 12.6 L 52.2 12.6 L 52.2 10.8 z M 37.8 46.8 L 37.8 48.6 L 39.6 48.6 L 39.6 46.8 z M 45 27 L 45 28.8 L 46.8 28.8 L 46.8 27 z M 10.8 50.4 L 10.8 52.2 L 12.6 52.2 L 12.6 50.4 z M 9 7.2 L 9 9.0 L 10.8 9.0 L 10.8 7.2 z M 7.2 21.6 L 7.2 23.4 L 9.0 23.4 L 9.0 21.6 z M 46.8 7.2 L 46.8 9.0 L 48.6 9.0 L 48.6 7.2 z M 14.4 18 L 14.4 19.8 L 16.2 19.8 L 16.2 18 z M 12.6 46.8 L 12.6 48.6 L 14.4 48.6 L 14.4 46.8 z M 21.6 46.8 L 21.6 48.6 L 23.4 48.6 L 23.4 46.8 z M 18 9 L 18 10.8 L 19.8 10.8 L 19.8 9 z M 27 12.6 L 27 14.4 L 28.8 14.4 L 28.8 12.6 z M 32.4 28.8 L 32.4 30.6 L 34.2 30.6 L 34.2 28.8 z M 18 43.2 L 18 45.0 L 19.8 45.0 L 19.8 43.2 z M 50.4 28.8 L 50.4 30.6 L 52.2 30.6 L 52.2 28.8 z M 36 43.2 L 36 45.0 L 37.8 45.0 L 37.8 43.2 z M 45 37.8 L 45 39.6 L 46.8 39.6 L 46.8 37.8 z M 43.2 34.2 L 43.2 36.0 L 45.0 36.0 L 45.0 34.2 z M 7.2 10.8 L 7.2 12.6 L 9.0 12.6 L 9.0 10.8 z M 45 32.4 L 45 34.2 L 46.8 34.2 L 46.8 32.4 z M 12.6 34.2 L 12.6 36.0 L 14.4 36.0 L 14.4 34.2 z M 21.6 30.6 L 21.6 32.4 L 23.4 32.4 L 23.4 30.6 z M 46.8 30.6 L 46.8 32.4 L 48.6 32.4 L 48.6 30.6 z M 12.6 7.2 L 12.6 9.0 L 14.4 9.0 L 14.4 7.2 z M 10.8 21.6 L 10.8 23.4 L 12.6 23.4 L 12.6 21.6 z M 23.4 21.6 L 23.4 23.4 L 25.2 23.4 L 25.2 21.6 z M 21.6 7.2 L 21.6 9.0 L 23.4 9.0 L 23.4 7.2 z M 16.2 30.6 L 16.2 32.4 L 18.0 32.4 L 18.0 30.6 z M 12.6 45 L 12.6 46.8 L 14.4 46.8 L 14.4 45 z M 25.2 34.2 L 25.2 36.0 L 27.0 36.0 L 27.0 34.2 z M 36 45 L 36 46.8 L 37.8 46.8 L 37.8 45 z M 18 10.8 L 18 12.6 L 19.8 12.6 L 19.8 10.8 z M 14.4 46.8 L 14.4 48.6 L 16.2 48.6 L 16.2 46.8 z M 27 32.4 L 27 34.2 L 28.8 34.2 L 28.8 32.4 z M 34.2 41.4 L 34.2 43.2 L 36.0 43.2 L 36.0 41.4 z M 50.4 46.8 L 50.4 48.6 L 52.2 48.6 L 52.2 46.8 z M 43.2 37.8 L 43.2 39.6 L 45.0 39.6 L 45.0 37.8 z M 27 41.4 L 27 43.2 L 28.8 43.2 L 28.8 41.4 z M 39.6 9 L 39.6 10.8 L 41.4 10.8 L 41.4 9 z M 50.4 23.4 L 50.4 25.2 L 52.2 25.2 L 52.2 23.4 z M 36 37.8 L 36 39.6 L 37.8 39.6 L 37.8 37.8 z M 30.6 28.8 L 30.6 30.6 L 32.4 30.6 L 32.4 28.8 z M 45 43.2 L 45 45.0 L 46.8 45.0 L 46.8 43.2 z M 39.6 28.8 L 39.6 30.6 L 41.4 30.6 L 41.4 28.8 z M 9 32.4 L 9 34.2 L 10.8 34.2 L 10.8 32.4 z M 46.8 32.4 L 46.8 34.2 L 48.6 34.2 L 48.6 32.4 z M 14.4 30.6 L 14.4 32.4 L 16.2 32.4 L 16.2 30.6 z M 10.8 30.6 L 10.8 32.4 L 12.6 32.4 L 12.6 30.6 z M 23.4 27 L 23.4 28.8 L 25.2 28.8 L 25.2 27 z M 16.2 7.2 L 16.2 9.0 L 18.0 9.0 L 18.0 7.2 z M 14.4 50.4 L 14.4 52.2 L 16.2 52.2 L 16.2 50.4 z M 23.4 50.4 L 23.4 52.2 L 25.2 52.2 L 25.2 50.4 z M 7.2 46.8 L 7.2 48.6 L 9.0 48.6 L 9.0 46.8 z M 36 27 L 36 28.8 L 37.8 28.8 L 37.8 27 z M 32.4 25.2 L 32.4 27.0 L 34.2 27.0 L 34.2 25.2 z M 30.6 10.8 L 30.6 12.6 L 32.4 12.6 L 32.4 10.8 z M 18 39.6 L 18 41.4 L 19.8 41.4 L 19.8 39.6 z M 41.4 18 L 41.4 19.8 L 43.2 19.8 L 43.2 18 z M 39.6 10.8 L 39.6 12.6 L 41.4 12.6 L 41.4 10.8 z M 43.2 46.8 L 43.2 48.6 L 45.0 48.6 L 45.0 46.8 z M 34.2 12.6 L 34.2 14.4 L 36.0 14.4 L 36.0 12.6 z M 50.4 18 L 50.4 19.8 L 52.2 19.8 L 52.2 18 z M 30.6 34.2 L 30.6 36.0 L 32.4 36.0 L 32.4 34.2 z M 46.8 37.8 L 46.8 39.6 L 48.6 39.6 L 48.6 37.8 z M 10.8 43.2 L 10.8 45.0 L 12.6 45.0 L 12.6 43.2 z M 45 48.6 L 45 50.4 L 46.8 50.4 L 46.8 48.6 z M 46.8 14.4 L 46.8 16.2 L 48.6 16.2 L 48.6 14.4 z M 45 14.4 L 45 16.2 L 46.8 16.2 L 46.8 14.4 z M 10.8 12.6 L 10.8 14.4 L 12.6 14.4 L 12.6 12.6 z M 9 23.4 L 9 25.2 L 10.8 25.2 L 10.8 23.4 z M 14.4 10.8 L 14.4 12.6 L 16.2 12.6 L 16.2 10.8 z M 18 16.2 L 18 18.0 L 19.8 18.0 L 19.8 16.2 z M 27 19.8 L 27 21.6 L 28.8 21.6 L 28.8 19.8 z M 36 16.2 L 36 18.0 L 37.8 18.0 L 37.8 16.2 z M 18 21.6 L 18 23.4 L 19.8 23.4 L 19.8 21.6 z M 16.2 36 L 16.2 37.8 L 18.0 37.8 L 18.0 36 z M 34.2 50.4 L 34.2 52.2 L 36.0 52.2 L 36.0 50.4 z M 27 21.6 L 27 23.4 L 28.8 23.4 L 28.8 21.6 z M 41.4 36 L 41.4 37.8 L 43.2 37.8 L 43.2 36 z M 7.2 41.4 L 7.2 43.2 L 9.0 43.2 L 9.0 41.4 z M 36 21.6 L 36 23.4 L 37.8 23.4 L 37.8 21.6 z M 18 50.4 L 18 52.2 L 19.8 52.2 L 19.8 50.4 z M 30.6 16.2 L 30.6 18.0 L 32.4 18.0 L 32.4 16.2 z M 28.8 41.4 L 28.8 43.2 L 30.6 43.2 L 30.6 41.4 z M 43.2 50.4 L 43.2 52.2 L 45.0 52.2 L 45.0 50.4 z M 9 39.6 L 9 41.4 L 10.8 41.4 L 10.8 39.6 z M 7.2 18 L 7.2 19.8 L 9.0 19.8 L 9.0 18 z M 50.4 12.6 L 50.4 14.4 L 52.2 14.4 L 52.2 12.6 z M 45 25.2 L 45 27.0 L 46.8 27.0 L 46.8 25.2 z M 43.2 18 L 43.2 19.8 L 45.0 19.8 L 45.0 18 z M 30.6 39.6 L 30.6 41.4 L 32.4 41.4 L 32.4 39.6 z M 39.6 39.6 L 39.6 41.4 L 41.4 41.4 L 41.4 39.6 z M 7.2 23.4 L 7.2 25.2 L 9.0 25.2 L 9.0 23.4 z M 12.6 14.4 L 12.6 16.2 L 14.4 16.2 L 14.4 14.4 z M 10.8 14.4 L 10.8 16.2 L 12.6 16.2 L 12.6 14.4 z M 16.2 23.4 L 16.2 25.2 L 18.0 25.2 L 18.0 23.4 z M 25.2 27 L 25.2 28.8 L 27.0 28.8 L 27.0 27 z M 18 18 L 18 19.8 L 19.8 19.8 L 19.8 18 z M 16.2 18 L 16.2 19.8 L 18.0 19.8 L 18.0 18 z M 14.4 39.6 L 14.4 41.4 L 16.2 41.4 L 16.2 39.6 z M 25.2 18 L 25.2 19.8 L 27.0 19.8 L 27.0 18 z M 23.4 46.8 L 23.4 48.6 L 25.2 48.6 L 25.2 46.8 z M 32.4 30.6 L 32.4 32.4 L 34.2 32.4 L 34.2 30.6 z M 18 45 L 18 46.8 L 19.8 46.8 L 19.8 45 z M 28.8 16.2 L 28.8 18.0 L 30.6 18.0 L 30.6 16.2 z M 41.4 34.2 L 41.4 36.0 L 43.2 36.0 L 43.2 34.2 z M 7.2 36 L 7.2 37.8 L 9.0 37.8 L 9.0 36 z M 34.2 21.6 L 34.2 23.4 L 36.0 23.4 L 36.0 21.6 z M 32.4 7.2 L 32.4 9.0 L 34.2 9.0 L 34.2 7.2 z M 30.6 21.6 L 30.6 23.4 L 32.4 23.4 L 32.4 21.6 z M 50.4 30.6 L 50.4 32.4 L 52.2 32.4 L 52.2 30.6 z M 41.4 7.2 L 41.4 9.0 L 43.2 9.0 L 43.2 7.2 z M 19.8 36 L 19.8 37.8 L 21.6 37.8 L 21.6 36 z M 7.2 12.6 L 7.2 14.4 L 9.0 14.4 L 9.0 12.6 z M 50.4 7.2 L 50.4 9.0 L 52.2 9.0 L 52.2 7.2 z M 28.8 36 L 28.8 37.8 L 30.6 37.8 L 30.6 36 z M 45 30.6 L 45 32.4 L 46.8 32.4 L 46.8 30.6 z M 12.6 32.4 L 12.6 34.2 L 14.4 34.2 L 14.4 32.4 z M 37.8 36 L 37.8 37.8 L 39.6 37.8 L 39.6 36 z M 30.6 45 L 30.6 46.8 L 32.4 46.8 L 32.4 45 z M 27 50.4 L 27 52.2 L 28.8 52.2 L 28.8 50.4 z M 36 50.4 L 36 52.2 L 37.8 52.2 L 37.8 50.4 z M 46.8 10.8 L 46.8 12.6 L 48.6 12.6 L 48.6 10.8 z M 14.4 23.4 L 14.4 25.2 L 16.2 25.2 L 16.2 23.4 z M 12.6 12.6 L 12.6 14.4 L 14.4 14.4 L 14.4 12.6 z M 10.8 23.4 L 10.8 25.2 L 12.6 25.2 L 12.6 23.4 z M 48.6 27 L 48.6 28.8 L 50.4 28.8 L 50.4 27 z M 16.2 28.8 L 16.2 30.6 L 18.0 30.6 L 18.0 28.8 z M 14.4 14.4 L 14.4 16.2 L 16.2 16.2 L 16.2 14.4 z M 12.6 43.2 L 12.6 45.0 L 14.4 45.0 L 14.4 43.2 z M 18 12.6 L 18 14.4 L 19.8 14.4 L 19.8 12.6 z M 27 9 L 27 10.8 L 28.8 10.8 L 28.8 9 z M 23.4 37.8 L 23.4 39.6 L 25.2 39.6 L 25.2 37.8 z M 34.2 39.6 L 34.2 41.4 L 36.0 41.4 L 36.0 39.6 z M 18 46.8 L 18 48.6 L 19.8 48.6 L 19.8 46.8 z M 43.2 39.6 L 43.2 41.4 L 45.0 41.4 L 45.0 39.6 z M 41.4 25.2 L 41.4 27.0 L 43.2 27.0 L 43.2 25.2 z M 50.4 25.2 L 50.4 27.0 L 52.2 27.0 L 52.2 25.2 z M 36 39.6 L 36 41.4 L 37.8 41.4 L 37.8 39.6 z M 10.8 36 L 10.8 37.8 L 12.6 37.8 L 12.6 36 z M 39.6 30.6 L 39.6 32.4 L 41.4 32.4 L 41.4 30.6 z M 7.2 7.2 L 7.2 9.0 L 9.0 9.0 L 9.0 7.2 z M 48.6 36 L 48.6 37.8 L 50.4 37.8 L 50.4 36 z M 9 50.4 L 9 52.2 L 10.8 52.2 L 10.8 50.4 z M 45 7.2 L 45 9.0 L 46.8 9.0 L 46.8 7.2 z M 30.6 50.4 L 30.6 52.2 L 32.4 52.2 L 32.4 50.4 z M 46.8 50.4 L 46.8 52.2 L 48.6 52.2 L 48.6 50.4 z M 39.6 50.4 L 39.6 52.2 L 41.4 52.2 L 41.4 50.4 z M 21.6 27 L 21.6 28.8 L 23.4 28.8 L 23.4 27 z M 16.2 34.2 L 16.2 36.0 L 18.0 36.0 L 18.0 34.2 z M 25.2 9 L 25.2 10.8 L 27.0 10.8 L 27.0 9 z M 21.6 37.8 L 21.6 39.6 L 23.4 39.6 L 23.4 37.8 z M 18 28.8 L 18 30.6 L 19.8 30.6 L 19.8 28.8 z M 32.4 43.2 L 32.4 45.0 L 34.2 45.0 L 34.2 43.2 z M 14.4 43.2 L 14.4 45.0 L 16.2 45.0 L 16.2 43.2 z M 27 28.8 L 27 30.6 L 28.8 30.6 L 28.8 28.8 z M 41.4 43.2 L 41.4 45.0 L 43.2 45.0 L 43.2 43.2 z M 7.2 48.6 L 7.2 50.4 L 9.0 50.4 L 9.0 48.6 z M 19.8 23.4 L 19.8 25.2 L 21.6 25.2 L 21.6 23.4 z M 32.4 27 L 32.4 28.8 L 34.2 28.8 L 34.2 27 z M 18 41.4 L 18 43.2 L 19.8 43.2 L 19.8 41.4 z M 43.2 48.6 L 43.2 50.4 L 45.0 50.4 L 45.0 48.6 z M 41.4 23.4 L 41.4 25.2 L 43.2 25.2 L 43.2 23.4 z M 39.6 12.6 L 39.6 14.4 L 41.4 14.4 L 41.4 12.6 z M 46.8 46.8 L 46.8 48.6 L 48.6 48.6 L 48.6 46.8 z M 45 46.8 L 45 48.6 L 46.8 48.6 L 46.8 46.8 z M 43.2 10.8 L 43.2 12.6 L 45.0 12.6 L 45.0 10.8 z M 10.8 45 L 10.8 46.8 L 12.6 46.8 L 12.6 45 z M 39.6 32.4 L 39.6 34.2 L 41.4 34.2 L 41.4 32.4 z M 45 12.6 L 45 14.4 L 46.8 14.4 L 46.8 12.6 z M 10.8 7.2 L 10.8 9.0 L 12.6 9.0 L 12.6 7.2 z M 48.6 7.2 L 48.6 9.0 L 50.4 9.0 L 50.4 7.2 z M 46.8 21.6 L 46.8 23.4 L 48.6 23.4 L 48.6 21.6 z M 14.4 12.6 L 14.4 14.4 L 16.2 14.4 L 16.2 12.6 z M 23.4 16.2 L 23.4 18.0 L 25.2 18.0 L 25.2 16.2 z" id="qr-path" style="fill:#000000;fill-opacity:1;fill-rule:nonzero;stroke:none"></path></svg>"""
        result_version_4 = """<svg height="73.8mm" version="1.1" viewBox="0 0 73.8 73.8" width="73.8mm" xmlns="http://www.w3.org/2000/svg"><path d="M 63 18 L 63 19.8 L 64.8 19.8 L 64.8 18 z M 43.2 52.2 L 43.2 54.0 L 45.0 54.0 L 45.0 52.2 z M 18 57.6 L 18 59.4 L 19.8 59.4 L 19.8 57.6 z M 41.4 14.4 L 41.4 16.2 L 43.2 16.2 L 43.2 14.4 z M 46.8 41.4 L 46.8 43.2 L 48.6 43.2 L 48.6 41.4 z M 21.6 16.2 L 21.6 18.0 L 23.4 18.0 L 23.4 16.2 z M 64.8 10.8 L 64.8 12.6 L 66.6 12.6 L 66.6 10.8 z M 30.6 64.8 L 30.6 66.6 L 32.4 66.6 L 32.4 64.8 z M 23.4 7.2 L 23.4 9.0 L 25.2 9.0 L 25.2 7.2 z M 32.4 63 L 32.4 64.8 L 34.2 64.8 L 34.2 63 z M 25.2 19.8 L 25.2 21.6 L 27.0 21.6 L 27.0 19.8 z M 7.2 37.8 L 7.2 39.6 L 9.0 39.6 L 9.0 37.8 z M 28.8 37.8 L 28.8 39.6 L 30.6 39.6 L 30.6 37.8 z M 52.2 34.2 L 52.2 36.0 L 54.0 36.0 L 54.0 34.2 z M 30.6 43.2 L 30.6 45.0 L 32.4 45.0 L 32.4 43.2 z M 59.4 37.8 L 59.4 39.6 L 61.2 39.6 L 61.2 37.8 z M 12.6 10.8 L 12.6 12.6 L 14.4 12.6 L 14.4 10.8 z M 43.2 64.8 L 43.2 66.6 L 45.0 66.6 L 45.0 64.8 z M 36 7.2 L 36 9.0 L 37.8 9.0 L 37.8 7.2 z M 61.2 36 L 61.2 37.8 L 63.0 37.8 L 63.0 36 z M 41.4 30.6 L 41.4 32.4 L 43.2 32.4 L 43.2 30.6 z M 57.6 64.8 L 57.6 66.6 L 59.4 66.6 L 59.4 64.8 z M 37.8 30.6 L 37.8 32.4 L 39.6 32.4 L 39.6 30.6 z M 19.8 46.8 L 19.8 48.6 L 21.6 48.6 L 21.6 46.8 z M 63 45 L 63 46.8 L 64.8 46.8 L 64.8 45 z M 48.6 41.4 L 48.6 43.2 L 50.4 43.2 L 50.4 41.4 z M 21.6 28.8 L 21.6 30.6 L 23.4 30.6 L 23.4 28.8 z M 64.8 52.2 L 64.8 54.0 L 66.6 54.0 L 66.6 52.2 z M 25.2 32.4 L 25.2 34.2 L 27.0 34.2 L 27.0 32.4 z M 23.4 41.4 L 23.4 43.2 L 25.2 43.2 L 25.2 41.4 z M 50.4 45 L 50.4 46.8 L 52.2 46.8 L 52.2 45 z M 32.4 21.6 L 32.4 23.4 L 34.2 23.4 L 34.2 21.6 z M 9 45 L 9 46.8 L 10.8 46.8 L 10.8 45 z M 10.8 39.6 L 10.8 41.4 L 12.6 41.4 L 12.6 39.6 z M 54 48.6 L 54 50.4 L 55.8 50.4 L 55.8 48.6 z M 55.8 18 L 55.8 19.8 L 57.6 19.8 L 57.6 18 z M 10.8 28.8 L 10.8 30.6 L 12.6 30.6 L 12.6 28.8 z M 59.4 14.4 L 59.4 16.2 L 61.2 16.2 L 61.2 14.4 z M 12.6 37.8 L 12.6 39.6 L 14.4 39.6 L 14.4 37.8 z M 36 19.8 L 36 21.6 L 37.8 21.6 L 37.8 19.8 z M 18 32.4 L 18 34.2 L 19.8 34.2 L 19.8 32.4 z M 41.4 39.6 L 41.4 41.4 L 43.2 41.4 L 43.2 39.6 z M 43.2 45 L 43.2 46.8 L 45.0 46.8 L 45.0 45 z M 39.6 16.2 L 39.6 18.0 L 41.4 18.0 L 41.4 16.2 z M 36 59.4 L 36 61.2 L 37.8 61.2 L 37.8 59.4 z M 18 64.8 L 18 66.6 L 19.8 66.6 L 19.8 64.8 z M 25.2 23.4 L 25.2 25.2 L 27.0 25.2 L 27.0 23.4 z M 21.6 52.2 L 21.6 54.0 L 23.4 54.0 L 23.4 52.2 z M 27 14.4 L 27 16.2 L 28.8 16.2 L 28.8 14.4 z M 50.4 57.6 L 50.4 59.4 L 52.2 59.4 L 52.2 57.6 z M 34.2 25.2 L 34.2 27.0 L 36.0 27.0 L 36.0 25.2 z M 27 54 L 27 55.8 L 28.8 55.8 L 28.8 54 z M 54 61.2 L 54 63.0 L 55.8 63.0 L 55.8 61.2 z M 7.2 16.2 L 7.2 18.0 L 9.0 18.0 L 9.0 16.2 z M 50.4 10.8 L 50.4 12.6 L 52.2 12.6 L 52.2 10.8 z M 9 7.2 L 9 9.0 L 10.8 9.0 L 10.8 7.2 z M 57.6 50.4 L 57.6 52.2 L 59.4 52.2 L 59.4 50.4 z M 18 9 L 18 10.8 L 19.8 10.8 L 19.8 9 z M 61.2 10.8 L 61.2 12.6 L 63.0 12.6 L 63.0 10.8 z M 14.4 37.8 L 14.4 39.6 L 16.2 39.6 L 16.2 37.8 z M 16.2 43.2 L 16.2 45.0 L 18.0 45.0 L 18.0 43.2 z M 43.2 57.6 L 43.2 59.4 L 45.0 59.4 L 45.0 57.6 z M 36 43.2 L 36 45.0 L 37.8 45.0 L 37.8 43.2 z M 18 55.8 L 18 57.6 L 19.8 57.6 L 19.8 55.8 z M 45 37.8 L 45 39.6 L 46.8 39.6 L 46.8 37.8 z M 37.8 37.8 L 37.8 39.6 L 39.6 39.6 L 39.6 37.8 z M 48.6 63 L 48.6 64.8 L 50.4 64.8 L 50.4 63 z M 21.6 7.2 L 21.6 9.0 L 23.4 9.0 L 23.4 7.2 z M 25.2 54 L 25.2 55.8 L 27.0 55.8 L 27.0 54 z M 27 41.4 L 27 43.2 L 28.8 43.2 L 28.8 41.4 z M 7.2 57.6 L 7.2 59.4 L 9.0 59.4 L 9.0 57.6 z M 50.4 23.4 L 50.4 25.2 L 52.2 25.2 L 52.2 23.4 z M 28.8 43.2 L 28.8 45.0 L 30.6 45.0 L 30.6 43.2 z M 10.8 61.2 L 10.8 63.0 L 12.6 63.0 L 12.6 61.2 z M 54 12.6 L 54 14.4 L 55.8 14.4 L 55.8 12.6 z M 59.4 46.8 L 59.4 48.6 L 61.2 48.6 L 61.2 46.8 z M 14.4 50.4 L 14.4 52.2 L 16.2 52.2 L 16.2 50.4 z M 63 7.2 L 63 9.0 L 64.8 9.0 L 64.8 7.2 z M 55.8 64.8 L 55.8 66.6 L 57.6 66.6 L 57.6 64.8 z M 36 27 L 36 28.8 L 37.8 28.8 L 37.8 27 z M 18 39.6 L 18 41.4 L 19.8 41.4 L 19.8 39.6 z M 45 54 L 45 55.8 L 46.8 55.8 L 46.8 54 z M 37.8 25.2 L 37.8 27.0 L 39.6 27.0 L 39.6 25.2 z M 43.2 9 L 43.2 10.8 L 45.0 10.8 L 45.0 9 z M 39.6 37.8 L 39.6 39.6 L 41.4 39.6 L 41.4 37.8 z M 21.6 19.8 L 21.6 21.6 L 23.4 21.6 L 23.4 19.8 z M 64.8 14.4 L 64.8 16.2 L 66.6 16.2 L 66.6 14.4 z M 27 21.6 L 27 23.4 L 28.8 23.4 L 28.8 21.6 z M 7.2 41.4 L 7.2 43.2 L 9.0 43.2 L 9.0 41.4 z M 50.4 36 L 50.4 37.8 L 52.2 37.8 L 52.2 36 z M 32.4 19.8 L 32.4 21.6 L 34.2 21.6 L 34.2 19.8 z M 52.2 30.6 L 52.2 32.4 L 54.0 32.4 L 54.0 30.6 z M 30.6 39.6 L 30.6 41.4 L 32.4 41.4 L 32.4 39.6 z M 54 25.2 L 54 27.0 L 55.8 27.0 L 55.8 25.2 z M 7.2 23.4 L 7.2 25.2 L 9.0 25.2 L 9.0 23.4 z M 12.6 14.4 L 12.6 16.2 L 14.4 16.2 L 14.4 14.4 z M 57.6 14.4 L 57.6 16.2 L 59.4 16.2 L 59.4 14.4 z M 63 23.4 L 63 25.2 L 64.8 25.2 L 64.8 23.4 z M 16.2 18 L 16.2 19.8 L 18.0 19.8 L 18.0 18 z M 59.4 23.4 L 59.4 25.2 L 61.2 25.2 L 61.2 23.4 z M 61.2 46.8 L 61.2 48.6 L 63.0 48.6 L 63.0 46.8 z M 41.4 34.2 L 41.4 36.0 L 43.2 36.0 L 43.2 34.2 z M 37.8 12.6 L 37.8 14.4 L 39.6 14.4 L 39.6 12.6 z M 16.2 64.8 L 16.2 66.6 L 18.0 66.6 L 18.0 64.8 z M 39.6 21.6 L 39.6 23.4 L 41.4 23.4 L 41.4 21.6 z M 36 50.4 L 36 52.2 L 37.8 52.2 L 37.8 50.4 z M 45 30.6 L 45 32.4 L 46.8 32.4 L 46.8 30.6 z M 21.6 32.4 L 21.6 34.2 L 23.4 34.2 L 23.4 32.4 z M 64.8 55.8 L 64.8 57.6 L 66.6 57.6 L 66.6 55.8 z M 46.8 10.8 L 46.8 12.6 L 48.6 12.6 L 48.6 10.8 z M 23.4 34.2 L 23.4 36.0 L 25.2 36.0 L 25.2 34.2 z M 48.6 27 L 48.6 28.8 L 50.4 28.8 L 50.4 27 z M 21.6 43.2 L 21.6 45.0 L 23.4 45.0 L 23.4 43.2 z M 27 9 L 27 10.8 L 28.8 10.8 L 28.8 9 z M 25.2 46.8 L 25.2 48.6 L 27.0 48.6 L 27.0 46.8 z M 10.8 36 L 10.8 37.8 L 12.6 37.8 L 12.6 36 z M 54 45 L 54 46.8 L 55.8 46.8 L 55.8 45 z M 7.2 7.2 L 7.2 9.0 L 9.0 9.0 L 9.0 7.2 z M 55.8 50.4 L 55.8 52.2 L 57.6 52.2 L 57.6 50.4 z M 57.6 12.6 L 57.6 14.4 L 59.4 14.4 L 59.4 12.6 z M 10.8 25.2 L 10.8 27.0 L 12.6 27.0 L 12.6 25.2 z M 16.2 34.2 L 16.2 36.0 L 18.0 36.0 L 18.0 34.2 z M 59.4 10.8 L 59.4 12.6 L 61.2 12.6 L 61.2 10.8 z M 12.6 41.4 L 12.6 43.2 L 14.4 43.2 L 14.4 41.4 z M 18 28.8 L 18 30.6 L 19.8 30.6 L 19.8 28.8 z M 14.4 43.2 L 14.4 45.0 L 16.2 45.0 L 16.2 43.2 z M 19.8 23.4 L 19.8 25.2 L 21.6 25.2 L 21.6 23.4 z M 39.6 12.6 L 39.6 14.4 L 41.4 14.4 L 41.4 12.6 z M 45 46.8 L 45 48.6 L 46.8 48.6 L 46.8 46.8 z M 64.8 21.6 L 64.8 23.4 L 66.6 23.4 L 66.6 21.6 z M 23.4 54 L 23.4 55.8 L 25.2 55.8 L 25.2 54 z M 50.4 61.2 L 50.4 63.0 L 52.2 63.0 L 52.2 61.2 z M 28.8 9 L 28.8 10.8 L 30.6 10.8 L 30.6 9 z M 52.2 63 L 52.2 64.8 L 54.0 64.8 L 54.0 63 z M 34.2 43.2 L 34.2 45.0 L 36.0 45.0 L 36.0 43.2 z M 30.6 14.4 L 30.6 16.2 L 32.4 16.2 L 32.4 14.4 z M 54 57.6 L 54 59.4 L 55.8 59.4 L 55.8 57.6 z M 50.4 14.4 L 50.4 16.2 L 52.2 16.2 L 52.2 14.4 z M 55.8 37.8 L 55.8 39.6 L 57.6 39.6 L 57.6 37.8 z M 9 18 L 9 19.8 L 10.8 19.8 L 10.8 18 z M 57.6 54 L 57.6 55.8 L 59.4 55.8 L 59.4 54 z M 54 18 L 54 19.8 L 55.8 19.8 L 55.8 18 z M 12.6 50.4 L 12.6 52.2 L 14.4 52.2 L 14.4 50.4 z M 61.2 7.2 L 61.2 9.0 L 63.0 9.0 L 63.0 7.2 z M 14.4 41.4 L 14.4 43.2 L 16.2 43.2 L 16.2 41.4 z M 41.4 59.4 L 41.4 61.2 L 43.2 61.2 L 43.2 59.4 z M 41.4 12.6 L 41.4 14.4 L 43.2 14.4 L 43.2 12.6 z M 37.8 48.6 L 37.8 50.4 L 39.6 50.4 L 39.6 48.6 z M 43.2 14.4 L 43.2 16.2 L 45.0 16.2 L 45.0 14.4 z M 23.4 12.6 L 23.4 14.4 L 25.2 14.4 L 25.2 12.6 z M 7.2 61.2 L 7.2 63.0 L 9.0 63.0 L 9.0 61.2 z M 55.8 46.8 L 55.8 48.6 L 57.6 48.6 L 57.6 46.8 z M 52.2 25.2 L 52.2 27.0 L 54.0 27.0 L 54.0 25.2 z M 30.6 48.6 L 30.6 50.4 L 32.4 50.4 L 32.4 48.6 z M 10.8 57.6 L 10.8 59.4 L 12.6 59.4 L 12.6 57.6 z M 54 9 L 54 10.8 L 55.8 10.8 L 55.8 9 z M 55.8 28.8 L 55.8 30.6 L 57.6 30.6 L 57.6 28.8 z M 14.4 54 L 14.4 55.8 L 16.2 55.8 L 16.2 54 z M 57.6 34.2 L 57.6 36.0 L 59.4 36.0 L 59.4 34.2 z M 36 30.6 L 36 32.4 L 37.8 32.4 L 37.8 30.6 z M 18 36 L 18 37.8 L 19.8 37.8 L 19.8 36 z M 14.4 64.8 L 14.4 66.6 L 16.2 66.6 L 16.2 64.8 z M 41.4 21.6 L 41.4 23.4 L 43.2 23.4 L 43.2 21.6 z M 64.8 64.8 L 64.8 66.6 L 66.6 66.6 L 66.6 64.8 z M 43.2 12.6 L 43.2 14.4 L 45.0 14.4 L 45.0 12.6 z M 48.6 46.8 L 48.6 48.6 L 50.4 48.6 L 50.4 46.8 z M 21.6 23.4 L 21.6 25.2 L 23.4 25.2 L 23.4 23.4 z M 64.8 18 L 64.8 19.8 L 66.6 19.8 L 66.6 18 z M 46.8 23.4 L 46.8 25.2 L 48.6 25.2 L 48.6 23.4 z M 34.2 54 L 34.2 55.8 L 36.0 55.8 L 36.0 54 z M 27 25.2 L 27 27.0 L 28.8 27.0 L 28.8 25.2 z M 7.2 45 L 7.2 46.8 L 9.0 46.8 L 9.0 45 z M 32.4 16.2 L 32.4 18.0 L 34.2 18.0 L 34.2 16.2 z M 28.8 30.6 L 28.8 32.4 L 30.6 32.4 L 30.6 30.6 z M 9 36 L 9 37.8 L 10.8 37.8 L 10.8 36 z M 52.2 41.4 L 52.2 43.2 L 54.0 43.2 L 54.0 41.4 z M 10.8 48.6 L 10.8 50.4 L 12.6 50.4 L 12.6 48.6 z M 54 21.6 L 54 23.4 L 55.8 23.4 L 55.8 21.6 z M 12.6 18 L 12.6 19.8 L 14.4 19.8 L 14.4 18 z M 57.6 18 L 57.6 19.8 L 59.4 19.8 L 59.4 18 z M 41.4 37.8 L 41.4 39.6 L 43.2 39.6 L 43.2 37.8 z M 37.8 9 L 37.8 10.8 L 39.6 10.8 L 39.6 9 z M 19.8 39.6 L 19.8 41.4 L 21.6 41.4 L 21.6 39.6 z M 43.2 25.2 L 43.2 27.0 L 45.0 27.0 L 45.0 25.2 z M 39.6 18 L 39.6 19.8 L 41.4 19.8 L 41.4 18 z M 45 27 L 45 28.8 L 46.8 28.8 L 46.8 27 z M 25.2 64.8 L 25.2 66.6 L 27.0 66.6 L 27.0 64.8 z M 37.8 55.8 L 37.8 57.6 L 39.6 57.6 L 39.6 55.8 z M 64.8 59.4 L 64.8 61.2 L 66.6 61.2 L 66.6 59.4 z M 23.4 30.6 L 23.4 32.4 L 25.2 32.4 L 25.2 30.6 z M 25.2 25.2 L 25.2 27.0 L 27.0 27.0 L 27.0 25.2 z M 27 12.6 L 27 14.4 L 28.8 14.4 L 28.8 12.6 z M 50.4 52.2 L 50.4 54.0 L 52.2 54.0 L 52.2 52.2 z M 32.4 28.8 L 32.4 30.6 L 34.2 30.6 L 34.2 28.8 z M 52.2 43.2 L 52.2 45.0 L 54.0 45.0 L 54.0 43.2 z M 30.6 23.4 L 30.6 25.2 L 32.4 25.2 L 32.4 23.4 z M 7.2 10.8 L 7.2 12.6 L 9.0 12.6 L 9.0 10.8 z M 12.6 34.2 L 12.6 36.0 L 14.4 36.0 L 14.4 34.2 z M 14.4 21.6 L 14.4 23.4 L 16.2 23.4 L 16.2 21.6 z M 57.6 59.4 L 57.6 61.2 L 59.4 61.2 L 59.4 59.4 z M 59.4 7.2 L 59.4 9.0 L 61.2 9.0 L 61.2 7.2 z M 12.6 45 L 12.6 46.8 L 14.4 46.8 L 14.4 45 z M 52.2 64.8 L 52.2 66.6 L 54.0 66.6 L 54.0 64.8 z M 18 10.8 L 18 12.6 L 19.8 12.6 L 19.8 10.8 z M 14.4 46.8 L 14.4 48.6 L 16.2 48.6 L 16.2 46.8 z M 16.2 48.6 L 16.2 50.4 L 18.0 50.4 L 18.0 48.6 z M 36 37.8 L 36 39.6 L 37.8 39.6 L 37.8 37.8 z M 64.8 43.2 L 64.8 45.0 L 66.6 45.0 L 66.6 43.2 z M 39.6 55.8 L 39.6 57.6 L 41.4 57.6 L 41.4 55.8 z M 64.8 25.2 L 64.8 27.0 L 66.6 27.0 L 66.6 25.2 z M 28.8 12.6 L 28.8 14.4 L 30.6 14.4 L 30.6 12.6 z M 34.2 46.8 L 34.2 48.6 L 36.0 48.6 L 36.0 46.8 z M 30.6 10.8 L 30.6 12.6 L 32.4 12.6 L 32.4 10.8 z M 27 61.2 L 27 63.0 L 28.8 63.0 L 28.8 61.2 z M 54 54 L 54 55.8 L 55.8 55.8 L 55.8 54 z M 50.4 18 L 50.4 19.8 L 52.2 19.8 L 52.2 18 z M 28.8 52.2 L 28.8 54.0 L 30.6 54.0 L 30.6 52.2 z M 55.8 41.4 L 55.8 43.2 L 57.6 43.2 L 57.6 41.4 z M 10.8 12.6 L 10.8 14.4 L 12.6 14.4 L 12.6 12.6 z M 54 14.4 L 54 16.2 L 55.8 16.2 L 55.8 14.4 z M 59.4 52.2 L 59.4 54.0 L 61.2 54.0 L 61.2 52.2 z M 12.6 54 L 12.6 55.8 L 14.4 55.8 L 14.4 54 z M 55.8 23.4 L 55.8 25.2 L 57.6 25.2 L 57.6 23.4 z M 18 16.2 L 18 18.0 L 19.8 18.0 L 19.8 16.2 z M 61.2 18 L 61.2 19.8 L 63.0 19.8 L 63.0 18 z M 14.4 59.4 L 14.4 61.2 L 16.2 61.2 L 16.2 59.4 z M 41.4 63 L 41.4 64.8 L 43.2 64.8 L 43.2 63 z M 12.6 64.8 L 12.6 66.6 L 14.4 66.6 L 14.4 64.8 z M 36 21.6 L 36 23.4 L 37.8 23.4 L 37.8 21.6 z M 18 63 L 18 64.8 L 19.8 64.8 L 19.8 63 z M 45 59.4 L 45 61.2 L 46.8 61.2 L 46.8 59.4 z M 41.4 16.2 L 41.4 18.0 L 43.2 18.0 L 43.2 16.2 z M 43.2 18 L 43.2 19.8 L 45.0 19.8 L 45.0 18 z M 39.6 39.6 L 39.6 41.4 L 41.4 41.4 L 41.4 39.6 z M 45 19.8 L 45 21.6 L 46.8 21.6 L 46.8 19.8 z M 21.6 14.4 L 21.6 16.2 L 23.4 16.2 L 23.4 14.4 z M 64.8 9 L 64.8 10.8 L 66.6 10.8 L 66.6 9 z M 25.2 18 L 25.2 19.8 L 27.0 19.8 L 27.0 18 z M 7.2 36 L 7.2 37.8 L 9.0 37.8 L 9.0 36 z M 32.4 7.2 L 32.4 9.0 L 34.2 9.0 L 34.2 7.2 z M 52.2 21.6 L 52.2 23.4 L 54.0 23.4 L 54.0 21.6 z M 57.6 41.4 L 57.6 43.2 L 59.4 43.2 L 59.4 41.4 z M 10.8 54 L 10.8 55.8 L 12.6 55.8 L 12.6 54 z M 54 34.2 L 54 36.0 L 55.8 36.0 L 55.8 34.2 z M 59.4 39.6 L 59.4 41.4 L 61.2 41.4 L 61.2 39.6 z M 12.6 12.6 L 12.6 14.4 L 14.4 14.4 L 14.4 12.6 z M 61.2 23.4 L 61.2 25.2 L 63.0 25.2 L 63.0 23.4 z M 14.4 14.4 L 14.4 16.2 L 16.2 16.2 L 16.2 14.4 z M 18 46.8 L 18 48.6 L 19.8 48.6 L 19.8 46.8 z M 23.4 64.8 L 23.4 66.6 L 25.2 66.6 L 25.2 64.8 z M 48.6 36 L 48.6 37.8 L 50.4 37.8 L 50.4 36 z M 45 7.2 L 45 9.0 L 46.8 9.0 L 46.8 7.2 z M 21.6 27 L 21.6 28.8 L 23.4 28.8 L 23.4 27 z M 46.8 34.2 L 46.8 36.0 L 48.6 36.0 L 48.6 34.2 z M 23.4 25.2 L 23.4 27.0 L 25.2 27.0 L 25.2 25.2 z M 27 28.8 L 27 30.6 L 28.8 30.6 L 28.8 28.8 z M 32.4 27 L 32.4 28.8 L 34.2 28.8 L 34.2 27 z M 28.8 34.2 L 28.8 36.0 L 30.6 36.0 L 30.6 34.2 z M 30.6 32.4 L 30.6 34.2 L 32.4 34.2 L 32.4 32.4 z M 7.2 30.6 L 7.2 32.4 L 9.0 32.4 L 9.0 30.6 z M 14.4 12.6 L 14.4 14.4 L 16.2 14.4 L 16.2 12.6 z M 57.6 7.2 L 57.6 9.0 L 59.4 9.0 L 59.4 7.2 z M 10.8 34.2 L 10.8 36.0 L 12.6 36.0 L 12.6 34.2 z M 36 18 L 36 19.8 L 37.8 19.8 L 37.8 18 z M 41.4 41.4 L 41.4 43.2 L 43.2 43.2 L 43.2 41.4 z M 37.8 19.8 L 37.8 21.6 L 39.6 21.6 L 39.6 19.8 z M 63 41.4 L 63 43.2 L 64.8 43.2 L 64.8 41.4 z M 39.6 14.4 L 39.6 16.2 L 41.4 16.2 L 41.4 14.4 z M 46.8 18 L 46.8 19.8 L 48.6 19.8 L 48.6 18 z M 39.6 61.2 L 39.6 63.0 L 41.4 63.0 L 41.4 61.2 z M 48.6 19.8 L 48.6 21.6 L 50.4 21.6 L 50.4 19.8 z M 27 16.2 L 27 18.0 L 28.8 18.0 L 28.8 16.2 z M 23.4 45 L 23.4 46.8 L 25.2 46.8 L 25.2 45 z M 50.4 55.8 L 50.4 57.6 L 52.2 57.6 L 52.2 55.8 z M 28.8 18 L 28.8 19.8 L 30.6 19.8 L 30.6 18 z M 34.2 27 L 34.2 28.8 L 36.0 28.8 L 36.0 27 z M 27 55.8 L 27 57.6 L 28.8 57.6 L 28.8 55.8 z M 7.2 14.4 L 7.2 16.2 L 9.0 16.2 L 9.0 14.4 z M 50.4 9 L 50.4 10.8 L 52.2 10.8 L 52.2 9 z M 55.8 57.6 L 55.8 59.4 L 57.6 59.4 L 57.6 57.6 z M 14.4 25.2 L 14.4 27.0 L 16.2 27.0 L 16.2 25.2 z M 10.8 18 L 10.8 19.8 L 12.6 19.8 L 12.6 18 z M 18 7.2 L 18 9.0 L 19.8 9.0 L 19.8 7.2 z M 61.2 59.4 L 61.2 61.2 L 63.0 61.2 L 63.0 59.4 z M 14.4 36 L 14.4 37.8 L 16.2 37.8 L 16.2 36 z M 41.4 50.4 L 41.4 52.2 L 43.2 52.2 L 43.2 50.4 z M 10.8 64.8 L 10.8 66.6 L 12.6 66.6 L 12.6 64.8 z M 43.2 41.4 L 43.2 43.2 L 45.0 43.2 L 45.0 41.4 z M 18 54 L 18 55.8 L 19.8 55.8 L 19.8 54 z M 46.8 52.2 L 46.8 54.0 L 48.6 54.0 L 48.6 52.2 z M 23.4 61.2 L 23.4 63.0 L 25.2 63.0 L 25.2 61.2 z M 32.4 45 L 32.4 46.8 L 34.2 46.8 L 34.2 45 z M 34.2 36 L 34.2 37.8 L 36.0 37.8 L 36.0 36 z M 54 50.4 L 54 52.2 L 55.8 52.2 L 55.8 50.4 z M 7.2 55.8 L 7.2 57.6 L 9.0 57.6 L 9.0 55.8 z M 50.4 21.6 L 50.4 23.4 L 52.2 23.4 L 52.2 21.6 z M 55.8 45 L 55.8 46.8 L 57.6 46.8 L 57.6 45 z M 9 54 L 9 55.8 L 10.8 55.8 L 10.8 54 z M 54 10.8 L 54 12.6 L 55.8 12.6 L 55.8 10.8 z M 12.6 57.6 L 12.6 59.4 L 14.4 59.4 L 14.4 57.6 z M 61.2 14.4 L 61.2 16.2 L 63.0 16.2 L 63.0 14.4 z M 43.2 54 L 43.2 55.8 L 45.0 55.8 L 45.0 54 z M 18 59.4 L 18 61.2 L 19.8 61.2 L 19.8 59.4 z M 45 55.8 L 45 57.6 L 46.8 57.6 L 46.8 55.8 z M 37.8 27 L 37.8 28.8 L 39.6 28.8 L 39.6 27 z M 19.8 50.4 L 19.8 52.2 L 21.6 52.2 L 21.6 50.4 z M 46.8 36 L 46.8 37.8 L 48.6 37.8 L 48.6 36 z M 21.6 64.8 L 21.6 66.6 L 23.4 66.6 L 23.4 64.8 z M 21.6 18 L 21.6 19.8 L 23.4 19.8 L 23.4 18 z M 64.8 12.6 L 64.8 14.4 L 66.6 14.4 L 66.6 12.6 z M 46.8 25.2 L 46.8 27.0 L 48.6 27.0 L 48.6 25.2 z M 27 23.4 L 27 25.2 L 28.8 25.2 L 28.8 23.4 z M 50.4 34.2 L 50.4 36.0 L 52.2 36.0 L 52.2 34.2 z M 32.4 18 L 32.4 19.8 L 34.2 19.8 L 34.2 18 z M 52.2 32.4 L 52.2 34.2 L 54.0 34.2 L 54.0 32.4 z M 34.2 19.8 L 34.2 21.6 L 36.0 21.6 L 36.0 19.8 z M 30.6 41.4 L 30.6 43.2 L 32.4 43.2 L 32.4 41.4 z M 54 30.6 L 54 32.4 L 55.8 32.4 L 55.8 30.6 z M 7.2 21.6 L 7.2 23.4 L 9.0 23.4 L 9.0 21.6 z M 59.4 36 L 59.4 37.8 L 61.2 37.8 L 61.2 36 z M 55.8 7.2 L 55.8 9.0 L 57.6 9.0 L 57.6 7.2 z M 14.4 18 L 14.4 19.8 L 16.2 19.8 L 16.2 18 z M 57.6 27 L 57.6 28.8 L 59.4 28.8 L 59.4 27 z M 63 32.4 L 63 34.2 L 64.8 34.2 L 64.8 32.4 z M 18 43.2 L 18 45.0 L 19.8 45.0 L 19.8 43.2 z M 41.4 28.8 L 41.4 30.6 L 43.2 30.6 L 43.2 28.8 z M 19.8 37.8 L 19.8 39.6 L 21.6 39.6 L 21.6 37.8 z M 63 43.2 L 63 45.0 L 64.8 45.0 L 64.8 43.2 z M 43.2 34.2 L 43.2 36.0 L 45.0 36.0 L 45.0 34.2 z M 39.6 27 L 39.6 28.8 L 41.4 28.8 L 41.4 27 z M 48.6 39.6 L 48.6 41.4 L 50.4 41.4 L 50.4 39.6 z M 21.6 30.6 L 21.6 32.4 L 23.4 32.4 L 23.4 30.6 z M 64.8 54 L 64.8 55.8 L 66.6 55.8 L 66.6 54 z M 46.8 30.6 L 46.8 32.4 L 48.6 32.4 L 48.6 30.6 z M 25.2 34.2 L 25.2 36.0 L 27.0 36.0 L 27.0 34.2 z M 21.6 41.4 L 21.6 43.2 L 23.4 43.2 L 23.4 41.4 z M 27 32.4 L 27 34.2 L 28.8 34.2 L 28.8 32.4 z M 23.4 39.6 L 23.4 41.4 L 25.2 41.4 L 25.2 39.6 z M 50.4 46.8 L 50.4 48.6 L 52.2 48.6 L 52.2 46.8 z M 28.8 23.4 L 28.8 25.2 L 30.6 25.2 L 30.6 23.4 z M 9 43.2 L 9 45.0 L 10.8 45.0 L 10.8 43.2 z M 30.6 28.8 L 30.6 30.6 L 32.4 30.6 L 32.4 28.8 z M 10.8 41.4 L 10.8 43.2 L 12.6 43.2 L 12.6 41.4 z M 54 43.2 L 54 45.0 L 55.8 45.0 L 55.8 43.2 z M 12.6 25.2 L 12.6 27.0 L 14.4 27.0 L 14.4 25.2 z M 57.6 10.8 L 57.6 12.6 L 59.4 12.6 L 59.4 10.8 z M 10.8 30.6 L 10.8 32.4 L 12.6 32.4 L 12.6 30.6 z M 16.2 7.2 L 16.2 9.0 L 18.0 9.0 L 18.0 7.2 z M 59.4 12.6 L 59.4 14.4 L 61.2 14.4 L 61.2 12.6 z M 12.6 36 L 12.6 37.8 L 14.4 37.8 L 14.4 36 z M 9 64.8 L 9 66.6 L 10.8 66.6 L 10.8 64.8 z M 61.2 50.4 L 61.2 52.2 L 63.0 52.2 L 63.0 50.4 z M 41.4 45 L 41.4 46.8 L 43.2 46.8 L 43.2 45 z M 19.8 32.4 L 19.8 34.2 L 21.6 34.2 L 21.6 32.4 z M 63 59.4 L 63 61.2 L 64.8 61.2 L 64.8 59.4 z M 43.2 46.8 L 43.2 48.6 L 45.0 48.6 L 45.0 46.8 z M 36 61.2 L 36 63.0 L 37.8 63.0 L 37.8 61.2 z M 45 48.6 L 45 50.4 L 46.8 50.4 L 46.8 48.6 z M 64.8 37.8 L 64.8 39.6 L 66.6 39.6 L 66.6 37.8 z M 39.6 57.6 L 39.6 59.4 L 41.4 59.4 L 41.4 57.6 z M 48.6 9 L 48.6 10.8 L 50.4 10.8 L 50.4 9 z M 21.6 54 L 21.6 55.8 L 23.4 55.8 L 23.4 54 z M 50.4 59.4 L 50.4 61.2 L 52.2 61.2 L 52.2 59.4 z M 32.4 36 L 32.4 37.8 L 34.2 37.8 L 34.2 36 z M 28.8 7.2 L 28.8 9.0 L 30.6 9.0 L 30.6 7.2 z M 52.2 50.4 L 52.2 52.2 L 54.0 52.2 L 54.0 50.4 z M 30.6 16.2 L 30.6 18.0 L 32.4 18.0 L 32.4 16.2 z M 27 59.4 L 27 61.2 L 28.8 61.2 L 28.8 59.4 z M 54 63 L 54 64.8 L 55.8 64.8 L 55.8 63 z M 7.2 18 L 7.2 19.8 L 9.0 19.8 L 9.0 18 z M 50.4 12.6 L 50.4 14.4 L 52.2 14.4 L 52.2 12.6 z M 28.8 61.2 L 28.8 63.0 L 30.6 63.0 L 30.6 61.2 z M 55.8 61.2 L 55.8 63.0 L 57.6 63.0 L 57.6 61.2 z M 30.6 63 L 30.6 64.8 L 32.4 64.8 L 32.4 63 z M 57.6 52.2 L 57.6 54.0 L 59.4 54.0 L 59.4 52.2 z M 10.8 14.4 L 10.8 16.2 L 12.6 16.2 L 12.6 14.4 z M 18 18 L 18 19.8 L 19.8 19.8 L 19.8 18 z M 61.2 12.6 L 61.2 14.4 L 63.0 14.4 L 63.0 12.6 z M 63 54 L 63 55.8 L 64.8 55.8 L 64.8 54 z M 16.2 41.4 L 16.2 43.2 L 18.0 43.2 L 18.0 41.4 z M 48.6 64.8 L 48.6 66.6 L 50.4 66.6 L 50.4 64.8 z M 18 50.4 L 18 52.2 L 19.8 52.2 L 19.8 50.4 z M 41.4 7.2 L 41.4 9.0 L 43.2 9.0 L 43.2 7.2 z M 46.8 63 L 46.8 64.8 L 48.6 64.8 L 48.6 63 z M 39.6 48.6 L 39.6 50.4 L 41.4 50.4 L 41.4 48.6 z M 32.4 55.8 L 32.4 57.6 L 34.2 57.6 L 34.2 55.8 z M 25.2 55.8 L 25.2 57.6 L 27.0 57.6 L 27.0 55.8 z M 7.2 59.4 L 7.2 61.2 L 9.0 61.2 L 9.0 59.4 z M 50.4 25.2 L 50.4 27.0 L 52.2 27.0 L 52.2 25.2 z M 28.8 45 L 28.8 46.8 L 30.6 46.8 L 30.6 45 z M 9 50.4 L 9 52.2 L 10.8 52.2 L 10.8 50.4 z M 30.6 50.4 L 30.6 52.2 L 32.4 52.2 L 32.4 50.4 z M 54 7.2 L 54 9.0 L 55.8 9.0 L 55.8 7.2 z M 59.4 45 L 59.4 46.8 L 61.2 46.8 L 61.2 45 z M 12.6 61.2 L 12.6 63.0 L 14.4 63.0 L 14.4 61.2 z M 57.6 32.4 L 57.6 34.2 L 59.4 34.2 L 59.4 32.4 z M 59.4 34.2 L 59.4 36.0 L 61.2 36.0 L 61.2 34.2 z M 41.4 23.4 L 41.4 25.2 L 43.2 25.2 L 43.2 23.4 z M 46.8 46.8 L 46.8 48.6 L 48.6 48.6 L 48.6 46.8 z M 43.2 10.8 L 43.2 12.6 L 45.0 12.6 L 45.0 10.8 z M 39.6 32.4 L 39.6 34.2 L 41.4 34.2 L 41.4 32.4 z M 48.6 48.6 L 48.6 50.4 L 50.4 50.4 L 50.4 48.6 z M 45 12.6 L 45 14.4 L 46.8 14.4 L 46.8 12.6 z M 21.6 21.6 L 21.6 23.4 L 23.4 23.4 L 23.4 21.6 z M 64.8 16.2 L 64.8 18.0 L 66.6 18.0 L 66.6 16.2 z M 23.4 16.2 L 23.4 18.0 L 25.2 18.0 L 25.2 16.2 z M 25.2 10.8 L 25.2 12.6 L 27.0 12.6 L 27.0 10.8 z M 34.2 55.8 L 34.2 57.6 L 36.0 57.6 L 36.0 55.8 z M 7.2 43.2 L 7.2 45.0 L 9.0 45.0 L 9.0 43.2 z M 50.4 37.8 L 50.4 39.6 L 52.2 39.6 L 52.2 37.8 z M 32.4 14.4 L 32.4 16.2 L 34.2 16.2 L 34.2 14.4 z M 34.2 9 L 34.2 10.8 L 36.0 10.8 L 36.0 9 z M 10.8 46.8 L 10.8 48.6 L 12.6 48.6 L 12.6 46.8 z M 54 27 L 54 28.8 L 55.8 28.8 L 55.8 27 z M 61.2 30.6 L 61.2 32.4 L 63.0 32.4 L 63.0 30.6 z M 14.4 7.2 L 14.4 9.0 L 16.2 9.0 L 16.2 7.2 z M 7.2 64.8 L 7.2 66.6 L 9.0 66.6 L 9.0 64.8 z M 59.4 21.6 L 59.4 23.4 L 61.2 23.4 L 61.2 21.6 z M 18 25.2 L 18 27.0 L 19.8 27.0 L 19.8 25.2 z M 61.2 48.6 L 61.2 50.4 L 63.0 50.4 L 63.0 48.6 z M 41.4 32.4 L 41.4 34.2 L 43.2 34.2 L 43.2 32.4 z M 63 46.8 L 63 48.6 L 64.8 48.6 L 64.8 46.8 z M 43.2 23.4 L 43.2 25.2 L 45.0 25.2 L 45.0 23.4 z M 21.6 34.2 L 21.6 36.0 L 23.4 36.0 L 23.4 34.2 z M 23.4 32.4 L 23.4 34.2 L 25.2 34.2 L 25.2 32.4 z M 48.6 25.2 L 48.6 27.0 L 50.4 27.0 L 50.4 25.2 z M 25.2 30.6 L 25.2 32.4 L 27.0 32.4 L 27.0 30.6 z M 27 7.2 L 27 9.0 L 28.8 9.0 L 28.8 7.2 z M 23.4 36 L 23.4 37.8 L 25.2 37.8 L 25.2 36 z M 50.4 50.4 L 50.4 52.2 L 52.2 52.2 L 52.2 50.4 z M 32.4 34.2 L 32.4 36.0 L 34.2 36.0 L 34.2 34.2 z M 25.2 48.6 L 25.2 50.4 L 27.0 50.4 L 27.0 48.6 z M 10.8 37.8 L 10.8 39.6 L 12.6 39.6 L 12.6 37.8 z M 7.2 9 L 7.2 10.8 L 9.0 10.8 L 9.0 9 z M 12.6 28.8 L 12.6 30.6 L 14.4 30.6 L 14.4 28.8 z M 9 28.8 L 9 30.6 L 10.8 30.6 L 10.8 28.8 z M 57.6 57.6 L 57.6 59.4 L 59.4 59.4 L 59.4 57.6 z M 10.8 27 L 10.8 28.8 L 12.6 28.8 L 12.6 27 z M 12.6 39.6 L 12.6 41.4 L 14.4 41.4 L 14.4 39.6 z M 14.4 45 L 14.4 46.8 L 16.2 46.8 L 16.2 45 z M 19.8 21.6 L 19.8 23.4 L 21.6 23.4 L 21.6 21.6 z M 46.8 64.8 L 46.8 66.6 L 48.6 66.6 L 48.6 64.8 z M 43.2 36 L 43.2 37.8 L 45.0 37.8 L 45.0 36 z M 39.6 7.2 L 39.6 9.0 L 41.4 9.0 L 41.4 7.2 z M 61.2 64.8 L 61.2 66.6 L 63.0 66.6 L 63.0 64.8 z M 37.8 59.4 L 37.8 61.2 L 39.6 61.2 L 39.6 59.4 z M 46.8 54 L 46.8 55.8 L 48.6 55.8 L 48.6 54 z M 21.6 57.6 L 21.6 59.4 L 23.4 59.4 L 23.4 57.6 z M 64.8 23.4 L 64.8 25.2 L 66.6 25.2 L 66.6 23.4 z M 28.8 10.8 L 28.8 12.6 L 30.6 12.6 L 30.6 10.8 z M 25.2 61.2 L 25.2 63.0 L 27.0 63.0 L 27.0 61.2 z M 34.2 48.6 L 34.2 50.4 L 36.0 50.4 L 36.0 48.6 z M 54 59.4 L 54 61.2 L 55.8 61.2 L 55.8 59.4 z M 7.2 50.4 L 7.2 52.2 L 9.0 52.2 L 9.0 50.4 z M 28.8 50.4 L 28.8 52.2 L 30.6 52.2 L 30.6 50.4 z M 55.8 36 L 55.8 37.8 L 57.6 37.8 L 57.6 36 z M 57.6 55.8 L 57.6 57.6 L 59.4 57.6 L 59.4 55.8 z M 10.8 10.8 L 10.8 12.6 L 12.6 12.6 L 12.6 10.8 z M 59.4 54 L 59.4 55.8 L 61.2 55.8 L 61.2 54 z M 18 14.4 L 18 16.2 L 19.8 16.2 L 19.8 14.4 z M 14.4 57.6 L 14.4 59.4 L 16.2 59.4 L 16.2 57.6 z M 41.4 57.6 L 41.4 59.4 L 43.2 59.4 L 43.2 57.6 z M 16.2 37.8 L 16.2 39.6 L 18.0 39.6 L 18.0 37.8 z M 43.2 63 L 43.2 64.8 L 45.0 64.8 L 45.0 63 z M 36 48.6 L 36 50.4 L 37.8 50.4 L 37.8 48.6 z M 18 61.2 L 18 63.0 L 19.8 63.0 L 19.8 61.2 z M 41.4 10.8 L 41.4 12.6 L 43.2 12.6 L 43.2 10.8 z M 37.8 46.8 L 37.8 48.6 L 39.6 48.6 L 39.6 46.8 z M 46.8 59.4 L 46.8 61.2 L 48.6 61.2 L 48.6 59.4 z M 39.6 45 L 39.6 46.8 L 41.4 46.8 L 41.4 45 z M 21.6 12.6 L 21.6 14.4 L 23.4 14.4 L 23.4 12.6 z M 64.8 7.2 L 64.8 9.0 L 66.6 9.0 L 66.6 7.2 z M 23.4 10.8 L 23.4 12.6 L 25.2 12.6 L 25.2 10.8 z M 32.4 52.2 L 32.4 54.0 L 34.2 54.0 L 34.2 52.2 z M 25.2 52.2 L 25.2 54.0 L 27.0 54.0 L 27.0 52.2 z M 7.2 63 L 7.2 64.8 L 9.0 64.8 L 9.0 63 z M 50.4 28.8 L 50.4 30.6 L 52.2 30.6 L 52.2 28.8 z M 32.4 12.6 L 32.4 14.4 L 34.2 14.4 L 34.2 12.6 z M 52.2 23.4 L 52.2 25.2 L 54.0 25.2 L 54.0 23.4 z M 57.6 39.6 L 57.6 41.4 L 59.4 41.4 L 59.4 39.6 z M 10.8 59.4 L 10.8 61.2 L 12.6 61.2 L 12.6 59.4 z M 54 32.4 L 54 34.2 L 55.8 34.2 L 55.8 32.4 z M 12.6 7.2 L 12.6 9.0 L 14.4 9.0 L 14.4 7.2 z M 55.8 34.2 L 55.8 36.0 L 57.6 36.0 L 57.6 34.2 z M 34.2 64.8 L 34.2 66.6 L 36.0 66.6 L 36.0 64.8 z M 57.6 21.6 L 57.6 23.4 L 59.4 23.4 L 59.4 21.6 z M 63 30.6 L 63 32.4 L 64.8 32.4 L 64.8 30.6 z M 16.2 54 L 16.2 55.8 L 18.0 55.8 L 18.0 54 z M 36 32.4 L 36 34.2 L 37.8 34.2 L 37.8 32.4 z M 46.8 43.2 L 46.8 45.0 L 48.6 45.0 L 48.6 43.2 z M 43.2 28.8 L 43.2 30.6 L 45.0 30.6 L 45.0 28.8 z M 39.6 28.8 L 39.6 30.6 L 41.4 30.6 L 41.4 28.8 z M 48.6 37.8 L 48.6 39.6 L 50.4 39.6 L 50.4 37.8 z M 45 9 L 45 10.8 L 46.8 10.8 L 46.8 9 z M 21.6 25.2 L 21.6 27.0 L 23.4 27.0 L 23.4 25.2 z M 25.2 7.2 L 25.2 9.0 L 27.0 9.0 L 27.0 7.2 z M 21.6 36 L 21.6 37.8 L 23.4 37.8 L 23.4 36 z M 27 30.6 L 27 32.4 L 28.8 32.4 L 28.8 30.6 z M 50.4 41.4 L 50.4 43.2 L 52.2 43.2 L 52.2 41.4 z M 30.6 34.2 L 30.6 36.0 L 32.4 36.0 L 32.4 34.2 z M 7.2 28.8 L 7.2 30.6 L 9.0 30.6 L 9.0 28.8 z M 12.6 23.4 L 12.6 25.2 L 14.4 25.2 L 14.4 23.4 z M 14.4 10.8 L 14.4 12.6 L 16.2 12.6 L 16.2 10.8 z M 10.8 32.4 L 10.8 34.2 L 12.6 34.2 L 12.6 32.4 z M 63 25.2 L 63 27.0 L 64.8 27.0 L 64.8 25.2 z M 59.4 18 L 59.4 19.8 L 61.2 19.8 L 61.2 18 z M 36 16.2 L 36 18.0 L 37.8 18.0 L 37.8 16.2 z M 18 21.6 L 18 23.4 L 19.8 23.4 L 19.8 21.6 z M 37.8 7.2 L 37.8 9.0 L 39.6 9.0 L 39.6 7.2 z M 63 36 L 63 37.8 L 64.8 37.8 L 64.8 36 z M 59.4 64.8 L 59.4 66.6 L 61.2 66.6 L 61.2 64.8 z M 39.6 19.8 L 39.6 21.6 L 41.4 21.6 L 41.4 19.8 z M 36 55.8 L 36 57.6 L 37.8 57.6 L 37.8 55.8 z M 45 25.2 L 45 27.0 L 46.8 27.0 L 46.8 25.2 z M 37.8 54 L 37.8 55.8 L 39.6 55.8 L 39.6 54 z M 46.8 9 L 46.8 10.8 L 48.6 10.8 L 48.6 9 z M 27 10.8 L 27 12.6 L 28.8 12.6 L 28.8 10.8 z M 50.4 54 L 50.4 55.8 L 52.2 55.8 L 52.2 54 z M 30.6 21.6 L 30.6 23.4 L 32.4 23.4 L 32.4 21.6 z M 27 50.4 L 27 52.2 L 28.8 52.2 L 28.8 50.4 z M 54 36 L 54 37.8 L 55.8 37.8 L 55.8 36 z M 7.2 12.6 L 7.2 14.4 L 9.0 14.4 L 9.0 12.6 z M 12.6 32.4 L 12.6 34.2 L 14.4 34.2 L 14.4 32.4 z M 57.6 61.2 L 57.6 63.0 L 59.4 63.0 L 59.4 61.2 z M 10.8 23.4 L 10.8 25.2 L 12.6 25.2 L 12.6 23.4 z M 16.2 28.8 L 16.2 30.6 L 18.0 30.6 L 18.0 28.8 z M 59.4 63 L 59.4 64.8 L 61.2 64.8 L 61.2 63 z M 12.6 43.2 L 12.6 45.0 L 14.4 45.0 L 14.4 43.2 z M 18 12.6 L 18 14.4 L 19.8 14.4 L 19.8 12.6 z M 14.4 48.6 L 14.4 50.4 L 16.2 50.4 L 16.2 48.6 z M 41.4 52.2 L 41.4 54.0 L 43.2 54.0 L 43.2 52.2 z M 63 52.2 L 63 54.0 L 64.8 54.0 L 64.8 52.2 z M 16.2 46.8 L 16.2 48.6 L 18.0 48.6 L 18.0 46.8 z M 36 39.6 L 36 41.4 L 37.8 41.4 L 37.8 39.6 z M 64.8 45 L 64.8 46.8 L 66.6 46.8 L 66.6 45 z M 39.6 50.4 L 39.6 52.2 L 41.4 52.2 L 41.4 50.4 z M 64.8 27 L 64.8 28.8 L 66.6 28.8 L 66.6 27 z M 23.4 63 L 23.4 64.8 L 25.2 64.8 L 25.2 63 z M 32.4 43.2 L 32.4 45.0 L 34.2 45.0 L 34.2 43.2 z M 52.2 57.6 L 52.2 59.4 L 54.0 59.4 L 54.0 57.6 z M 27 37.8 L 27 39.6 L 28.8 39.6 L 28.8 37.8 z M 7.2 54 L 7.2 55.8 L 9.0 55.8 L 9.0 54 z M 55.8 39.6 L 55.8 41.4 L 57.6 41.4 L 57.6 39.6 z M 30.6 55.8 L 30.6 57.6 L 32.4 57.6 L 32.4 55.8 z M 57.6 45 L 57.6 46.8 L 59.4 46.8 L 59.4 45 z M 10.8 7.2 L 10.8 9.0 L 12.6 9.0 L 12.6 7.2 z M 54 16.2 L 54 18.0 L 55.8 18.0 L 55.8 16.2 z M 32.4 64.8 L 32.4 66.6 L 34.2 66.6 L 34.2 64.8 z M 12.6 59.4 L 12.6 61.2 L 14.4 61.2 L 14.4 59.4 z M 55.8 21.6 L 55.8 23.4 L 57.6 23.4 L 57.6 21.6 z M 14.4 61.2 L 14.4 63.0 L 16.2 63.0 L 16.2 61.2 z M 41.4 61.2 L 41.4 63.0 L 43.2 63.0 L 43.2 61.2 z" id="qr-path" style="fill:#000000;fill-opacity:1;fill-rule:nonzero;stroke:none"></path></svg>"""
        results = [default_result] * 10 + [
            result_version_2,
            result_version_2,
            result_version_4,
            result_version_4
        ]
        for i in range(len(versions)):
            version = versions[i]
            print('Testing SVG with version %s' % version)
            result = results[i]
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(version=version))
            qr2 = qr_from_text(TEST_TEXT, version=version)
            qr3 = qr_from_text(TEST_TEXT, version=version, image_format='svg')
            qr4 = qr_from_text(TEST_TEXT, version=version, image_format='SVG')
            qr5 = qr_from_text(TEST_TEXT, options=QRCodeOptions(version=version, image_format='SVG'))
            qr6 = qr_from_text(TEST_TEXT, version=version, image_format='invalid-format-name')
            self.assertEqual(qr1, qr2)
            self.assertEqual(qr1, qr3)
            self.assertEqual(qr1, qr4)
            self.assertEqual(qr1, qr5)
            self.assertEqual(qr1, qr6)
            self.assertEqual(qr1, result)

    def test_error_correction(self):
        file_base_name = 'qrfromtext_error_correction'
        tests_data = []
        for correction_level in ERROR_CORRECTION_DICT.keys():
            ref_file_name = '%s_%s%s' % (file_base_name, correction_level, SVG_REF_SUFFIX)
            tests_data.append(dict(source='{% qr_from_text "' + COMPLEX_TEST_TEXT + '" image_format="svg" error_correction="' + correction_level + '" %}', ref_file_name=ref_file_name.lower()))

        for test_data in tests_data:
            print('Testing template: %s' % test_data['source'])
            html_source = mark_safe('{% load qr_code %}' + test_data['source'])
            template = Template(html_source)
            context = Context()
            source_image_data = template.render(context).strip()
            if REFRESH_REFERENCE_IMAGES:
                write_svg_content_to_file(test_data['ref_file_name'], source_image_data)
            ref_image_data = get_svg_content_from_file_name(test_data['ref_file_name'])
            self.assertEqual(source_image_data, ref_image_data)


class TestQRFromTextPngResult(SimpleTestCase):
    """
    Ensures that produced QR codes in PNG format coincide with verified references.

    The tests cover direct call to tag function, rendering of tag, and direct call to qr_code API.
    """
    def test_size(self):
        base_ref_file_name = 'qrfromtext_size_'
        sizes = ['t', 'T', 's', 'S', None, -1, 0, 'm', 'M', 'l', 'L', 'h', 'H', '6', 6, '8', 8, '10', 10]
        size_names = ['tiny'] * 2 + ['small'] * 2 + ['medium'] * 5 + ['large'] * 2 + ['huge'] * 2 + ['6'] * 2 + [
            '8'] * 2 + ['10'] * 2
        for i in range(len(sizes)):
            size = sizes[i]
            print('Testing PNG with size %s' % size)
            size_name = size_names[i]
            result_file_name = '%s%s%s' % (base_ref_file_name, size_name, PNG_REF_SUFFIX)
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(size=size, image_format='png'))
            qr2 = qr_from_text(TEST_TEXT, size=size, image_format='png')
            qr3 = qr_from_text(TEST_TEXT, options=QRCodeOptions(size=size, image_format='png'))
            if REFRESH_REFERENCE_IMAGES:
                match = IMAGE_TAG_BASE64_DATA_RE.search(qr1)
                source_image_data = match.group('data')
                write_png_content_to_file(result_file_name, base64.b64decode(source_image_data))
            result =base64.b64encode(get_png_content_from_file_name(result_file_name)).decode('utf-8')
            self.assertEqual(qr1, qr2)
            self.assertEqual(qr1, qr3)
            self.assertEqual(qr1, BASE64_PNG_IMAGE_TEMPLATE % result)

    def test_version(self):
        versions = [None, -1, 0, 41, '-1', '0', '41', 'blabla', 1, '1', 2, '2', 4, '4']
        default_result = """iVBORw0KGgoAAAANSUhEUgAAAgoAAAIKAQAAAABqulr4AAACO0lEQVR4nO3cQW6kMBCF4VfjlmbJ3GCOAkeHo+QGsIwEqiyMwZA0MBM6tNR/rWiTfCo2likXNtc3o/n1XUGCgICAgICAgICAgICAgICAgID4X8KWcZOkJl5LUre6Xz0mCwgICIjjROlTtGmkVXCPc1SYb/s94oQsICAgII4T3WIdZVap8Hcz9zqNTMuwB2YBAQEBcT9uu38R9nojnuNBICAgICStV19XZQEBAQGRYrnWKlbrqsak0MvS7y+XXc/xIBAQEC9INPMO4Z84UqayvCQN2Q7iA7OAgICA2Ip5rfXVOqoxaYhT1HoZdmoWEBAQEP9OmFV5U9ZNiluHIfY5LG89LAsICAiInfA82jhWunuf3Vr9S3DPmrvq53gQCAiIlyPMzP56H3909jtNVkPq1wru8WLIOrjOzgICAgJiO/K3vbKeurPGKlZTzSOtNG4mhv7sLCAgICCORl6NH/scxskqNTwMJpfUWejnir2prE/MAgICAuJw+P2QpCJezFWsOJIFdS0ICIhriM9nPuTFK3Vx67D0N/q1ICAgLiTyjcLFmQ9htXVYxF3FWsvDH1hrQUBAXEl8/upwekN8S2st93fO14KAgLiM2DvzYSzCN/Gd0CQV7eoUiOd4EAgIiBch9matseGhdGm4zZuJJ2cBAQEBcTS2znxwNdV42VjRBteiCn9iFhAQEBCHY/OznSnKVJ9ff+xDNR4CAuJnia0zHxYjhU8j1LUgICAgICAgICAgICAgICAgIK4mPgAhWy686mP48AAAAABJRU5ErkJggg=="""
        result_version_2 = """iVBORw0KGgoAAAANSUhEUgAAAlIAAAJSAQAAAAAgpBbeAAADC0lEQVR4nO3dQZLbIBCF4deRqmYp3yBHkY9ujjI3sPZWdRaABPbYk6RsWSQ/K4+k+Qo2FDQNmOtZJfx4GiVhYWFhYWFhYWFhYWFhYWFhYWFhYbVjWV16yeyYX4b4UJKmqw+PX1jPrBcWFhZWW1Zf/B5Py8/pIMnzD2l0ac7fdpf1f+xF9cLCwsL6N6ypGoKaHTW4u0vBDup8zR1YxrTb1AsLCwurHat/8M4VbDjPvWJ/OveqxrQvrRcWFhZWq9ajflUafbKHH1Rlr23EwsLC2tKq+9Wh2iVg+UnsWztfo6lf7ibYaxuxsLCw3mWFdZH/EJ+M/hmDqKOf1+/mIhtgi3phYWFhtWSt49XbIWgKq5qkYIOnJ8Pdna97bSMWFhbWeyyzo6a8xD/FsWiwn74kVc05VWDOiax1jmsDbcTCwsLa1gpx+m9mZXcqyd39nPOsUt8bcqzg9fXCwsLCatNyP2nwS+xFP+3DPYZVu5i/umSrDlWX+/p6YWFhYbVl3cmzKtIAJLlGnw5z/ruLEdbhPFsVld1rG7GwsLDeZy1zfLM+Dlw9jk7Tfiv30xqDlTp34qtYWFhY962UTBW3r17yStaHXycAlOtWW9QLCwsLqyVr7RrjLoA0tZ+su6Ssqtnk8dyVPOvv7gRY99pGLCwsrC2tNNlfyuVqAeucp/9D9Y2k8om7u5/22kYsLCysLa16vLpsVk3HAoTj4Mty1XyzxrUcyfL8emFhYWG1al2PV8siKZ8TOOYn4/pKcSjLeBULCwvra+v2voDifIDqvoD0yvPa1mvrhYWFhdWW9fi+gGDpfIDxlC4OuD4fgDgAFhYW1lUpZv3LoVVjXq5a5/hSdV+AxLoVFhYW1l9Yt4cAjDed8O9af1awsLCwWrUe3RcQEwHmPuWvKt/MIkkKOU1gjR7stY1YWFhYW1qP7gtIGwRcUjim7rS4mDU9eU29sLCwsFq1yvhqVW6jqRepOOGq+EF8FQsLC2st398XsJR8jFV1cQD5AFhYWFhYWFhYWFhYWFhYWFhYWFj/q/ULXEmDCUnFmPAAAAAASUVORK5CYII="""
        result_version_4 = """iVBORw0KGgoAAAANSUhEUgAAAuIAAALiAQAAAAC0mI6SAAAEL0lEQVR4nO3dTW6jQBCG4a8GS7MkN8hRyM2iuZk5Sm4Ay5GMahYNTXeDM5EhcUzeWmF+HiE2peqfsrk+L9pfn4hL6Ojo6Ojo6Ojo6Ojo6Ojo6Ojo6Ojo6Ojo6N9JtzxO2ZkX9dkZqbWn6cm+ePTly98dHR0dHf2oeuMxOkkKh5dwsfa/Zu5n1e7uIVvFTFTNT/o1/XPfHR0dHR39qHpfFD5tKKBClVS5S413GszCQZVkolhtXdf3DnR0dHT0n6ebvagOdVPjb1OSitnqeSqpbtO3Bzo6Ojr6T9SbaXDvzzS7NJ5JDm7XtwY6Ojo6+jH1fBCuLnbitlZ36W9Tc5YkxfuWB2k88pdBR0dHR/8OejsvtXsKZxp/s9/uZq9plVRNayFOYdxPGpJVevd5d3R0dHT04+hz3fRO86JwaTBJrY1nWqt9MLmW1dYcj/xl0NHR0dHvr8fleXF9uDQuHX9nnV62sekpc77w3dHR0dHRj6v3ZtMmpst05pQs2IuX4piepPlSz5geOjo6OvoO4Wl04Vy5dyluwo17bwsk7r0dF5yPcX7kL4OOjo6O/l30yj2pm5q51UMsoHo7JQVUzGixQcT93h0dHR0d/Rj6XDclZ87SNLsUy6VYHHXhrpi24j3LoG5CR0dHR78lktw0DuWtdcZLCqi6yFbxIOvCR25CR0dHR785lvNNSXEU74nTTM0yAakssshN6Ojo6OibYi03ZQsequQgxDgV1ZWzS+EpchM6Ojo6+l56skHpdersqnTBwzCtD48pKW50EmvI0dHR0dH3i2K+aYx6Hp0rF+yNT2Vr+S7FuB91Ezo6Ojr6hnhnvimmm2vzTXn+YkwPHR0dHX1nPelZZPbsHhq6ah7K01pfiKwxbJfdrKN8GXR0dHT0r9Xz/U2xVVGy9M7XFpOH2qpcQ05fCHR0dHT0PWItN83JJR3Ku7r3tpusxeOP/GXQ0dHR0e+ll/NNZRu9LquJ1vrpNZ70jhD7m9DR0dHRN8d6bqoXA3f5cF/RT6/KbiY3oaOjo6NvivUxvW6+lK7BW/aFSKSy5RG5CR0dHR39tvDrkTR/aIrBvezSMrWRm9DR0dHRN8RaBSRpMfG0Nt9UZfmL3ISOjo6Ovrsec8qy6Wtrtv7/TVI2Esj/N6Gjo6Ojb49iBE/Scrwui3jPcr6pDOomdHR0dPSd9bAsPG31EFpGXCT3P6GSysql3sws9pf4j7490NHR0dF/op4M5Y3RTC3KG/d5VfmYv+qxXPqgvjXQ0dHR0Y+pn7JfdbkiQnUnSWpNqi5ySbUPJ5mac/8kyadLUmvjzXM88pdBR0dHR7+Xnuam1vJrJqm3aqqOBlNIXZUru7PuhvC7t+oiU3Oerjzyl0FHR0dHv5dui0ppx2gf+cugo6Ojo6Ojo6Ojo6Ojo6Ojo6Ojo6Ojo6OjfyT+AZQbXo3Rxei0AAAAAElFTkSuQmCC"""
        results = [default_result] * 10 + [
            result_version_2,
            result_version_2,
            result_version_4,
            result_version_4
        ]
        for i in range(len(versions)):
            version = versions[i]
            print('Testing PNG with version %s' % version)
            result = results[i]
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(version=version, image_format='png'))
            qr2 = qr_from_text(TEST_TEXT, version=version, image_format='png')
            qr3 = qr_from_text(TEST_TEXT, version=version, image_format='PNG')
            qr4 = qr_from_text(TEST_TEXT, options=QRCodeOptions(version=version, image_format='PNG'))
            self.assertEqual(qr1, qr2)
            self.assertEqual(qr1, qr3)
            self.assertEqual(qr1, qr4)
            self.assertEqual(qr1, BASE64_PNG_IMAGE_TEMPLATE % result)

    def test_error_correction(self):
        file_base_name = 'qrfromtext_error_correction'
        tests_data = []
        for correction_level in ERROR_CORRECTION_DICT.keys():
            ref_file_name = '%s_%s%s' % (file_base_name, correction_level, PNG_REF_SUFFIX)
            tests_data.append(dict(source='{% qr_from_text "' + COMPLEX_TEST_TEXT + '" image_format="png" error_correction="' + correction_level + '" %}', ref_file_name=ref_file_name.lower()))

        for test_data in tests_data:
            print('Testing template: %s' % test_data['source'])
            html_source = mark_safe('{% load qr_code %}' + test_data['source'])
            template = Template(html_source)
            context = Context()
            source_image = template.render(context).strip()
            source_image_data = source_image[33:-len('" alt="%s"' % escape(COMPLEX_TEST_TEXT))]
            source_image_data = base64.b64decode(source_image_data)
            if REFRESH_REFERENCE_IMAGES:
                write_png_content_to_file(test_data['ref_file_name'], source_image_data)
            ref_image_data = get_png_content_from_file_name(test_data['ref_file_name'])
            self.assertEqual(source_image_data, ref_image_data)


class TestQRForApplications(SimpleTestCase):

    @staticmethod
    def _make_test_data(tag_pattern, ref_file_name, tag_args, template_context=dict()):
        tag_content = tag_pattern
        for key, value in tag_args.items():
            if isinstance(value, str):
                tag_content += ' %s="%s"' % (key, value)
            else:
                tag_content += ' %s=%s' % (key, value)
        return dict(source='{% ' + tag_content + ' %}', ref_file_name=ref_file_name, template_context=template_context)

    @staticmethod
    def _make_tests_data(embedded=True, image_format=SVG_FORMAT_NAME):
        contact_detail1 = dict(**TEST_CONTACT_DETAIL)
        contact_detail2 = ContactDetail(
            **contact_detail1
        )
        wifi_config1 = dict(**TEST_WIFI_CONFIG)
        wifi_config2 = WifiConfig(
            **wifi_config1
        )
        google_maps_coordinates = Coordinates(latitude=586000.32, longitude=250954.19)
        geolocation_coordinates = Coordinates(latitude=586000.32, longitude=250954.19, altitude=500)
        if image_format == SVG_FORMAT_NAME:
            ref_suffix = SVG_REF_SUFFIX
        else:
            ref_suffix = PNG_REF_SUFFIX
        tag_prefix = 'qr_for_' if embedded else 'qr_url_for_'
        tag_args = dict(image_format=image_format)
        if image_format == PNG_FORMAT_NAME:
            tag_args['size'] = 't'
        if not embedded:
            # Deactivate cache for URL.
            tag_args['cache_enabled'] = False
        raw_data = (
            ('email', '"john.doe@domain.com"', None),
            ('tel', ' "+41769998877"', None),
            ('sms', ' "+41769998877"', None),
            ('geolocation', 'latitude=586000.32 longitude=250954.19 altitude=500', None),
            ('geolocation', 'coordinates=coordinates', {'coordinates': geolocation_coordinates}),
            ('google_maps', 'latitude=586000.32 longitude=250954.19', None),
            ('google_maps', 'coordinates=coordinates', {'coordinates': google_maps_coordinates}),
            ('wifi', 'wifi_config', {'wifi_config': wifi_config1}),
            ('wifi', 'wifi_config', {'wifi_config': wifi_config2}),
            ('wifi', 'wifi_config=wifi_config', {'wifi_config': wifi_config2}),
            ('contact', 'contact_detail', {'contact_detail': contact_detail1}),
            ('contact', 'contact_detail', {'contact_detail': contact_detail2}),
            ('contact', 'contact_detail=contact_detail', {'contact_detail': contact_detail2}),
            ('youtube', '"J9go2nj6b3M"', None),
            ('youtube', 'video_id', {'video_id': "J9go2nj6b3M"}),
            ('google_play', '"ch.admin.meteoswiss"', None),
        )
        tests_data = []
        for tag_base_name, tag_data, template_context in raw_data:
            test_data = TestQRForApplications._make_test_data(tag_pattern='%s%s %s' % (tag_prefix, tag_base_name, tag_data),
                                                              ref_file_name='qr_for_%s%s' % (tag_base_name, ref_suffix),
                                                              tag_args=tag_args,
                                                              template_context=template_context)
            tests_data.append(test_data)
        return tests_data

    @staticmethod
    def _get_rendered_template(template_source, template_context):
        html_source = mark_safe('{% load qr_code %}' + template_source)
        template = Template(html_source)
        context = Context()
        if template_context:
            context.update(template_context)
        return template.render(context).strip()

    def test_demo_samples_embedded_in_svg_format(self):
        tests_data = self._make_tests_data(embedded=True)
        for test_data in tests_data:
            print('Testing template: %s' % test_data['source'])
            source_image_data = TestQRForApplications._get_rendered_template(test_data['source'], test_data.get('template_context'))
            source_image_data = _make_xml_header() + '\n' + source_image_data
            if REFRESH_REFERENCE_IMAGES:
                write_svg_content_to_file(test_data['ref_file_name'], source_image_data)
            ref_image_data = get_svg_content_from_file_name(test_data['ref_file_name'])
            self.assertEqual(source_image_data, ref_image_data)

    def test_demo_samples_embedded_in_png_format(self):
        tests_data = self._make_tests_data(embedded=True, image_format=PNG_FORMAT_NAME)
        for test_data in tests_data:
            print('Testing template: %s' % test_data['source'])
            source_image_data = TestQRForApplications._get_rendered_template(test_data['source'], test_data.get('template_context'))
            match = IMAGE_TAG_BASE64_DATA_RE.search(source_image_data)
            source_image_data = match.group('data')
            source_image_data = base64.b64decode(source_image_data)
            if REFRESH_REFERENCE_IMAGES:
                write_png_content_to_file(test_data['ref_file_name'], source_image_data)
            ref_image_data = get_png_content_from_file_name(test_data['ref_file_name'])
            self.assertEqual(source_image_data, ref_image_data)

    def test_demo_sample_urls_in_svg_format(self):
        tests_data = self._make_tests_data(embedded=False)
        for test_data in tests_data:
            source_image_data = self._check_url_for_test_data(test_data).content.decode('utf-8')
            source_image_data = _make_closing_path_tag(source_image_data)
            if REFRESH_REFERENCE_IMAGES:
                write_svg_content_to_file(test_data['ref_file_name'], source_image_data)
            ref_image_data = get_svg_content_from_file_name(test_data['ref_file_name'])
            self.assertEqual(source_image_data, ref_image_data)

    def test_demo_sample_urls_in_png_format(self):
        tests_data = self._make_tests_data(embedded=False, image_format=PNG_FORMAT_NAME)
        for test_data in tests_data:
            source_image_data = self._check_url_for_test_data(test_data).content
            if REFRESH_REFERENCE_IMAGES:
                write_png_content_to_file(test_data['ref_file_name'], source_image_data)
            ref_image_data = get_png_content_from_file_name(test_data['ref_file_name'])
            self.assertEqual(source_image_data, ref_image_data)

    def _check_url_for_test_data(self, test_data):
        print('Testing template: %s' % test_data['source'])
        source_image_url = TestQRForApplications._get_rendered_template(test_data['source'],
                                                                        test_data.get('template_context'))
        response = self.client.get(source_image_url)
        self.assertEqual(response.status_code, 200)
        return response


class TestIssues(SimpleTestCase):
    def test_reverse_lazy_url(self):
        from django.urls import reverse, reverse_lazy
        options = QRCodeOptions(image_format='svg', size=1)
        url1 = make_qr_code_url(reverse('qr_code:serve_qr_code_image'), options)
        url2 = make_qr_code_url(reverse_lazy('qr_code:serve_qr_code_image'), options)
        self.assertEqual(url1, url2)

        svg1 = make_embedded_qr_code(reverse('qr_code:serve_qr_code_image'), options)
        svg2 = make_embedded_qr_code(reverse_lazy('qr_code:serve_qr_code_image'), options)
        self.assertEqual(svg1, svg2)


def get_svg_content_from_file_name(file_name, skip_header=False):
    with open(os.path.join(get_resources_path(), file_name), 'r', encoding='utf-8') as file:
        if skip_header:
            file.readline()
        image_data = file.read().strip()
        return image_data


def get_png_content_from_file_name(file_name):
    with open(os.path.join(get_resources_path(), file_name), 'rb') as file:
        image_data = file.read()
        return image_data


# Uncomment in order to renew some of the reference files.
def write_png_content_to_file(file_name, image_content):
    with open(os.path.join(get_resources_path(), file_name), 'wb') as file:
        file.write(image_content)


def write_svg_content_to_file(file_name, image_content):
    with open(os.path.join(get_resources_path(), file_name), 'wt', encoding='utf-8') as file:
        file.write(image_content)
