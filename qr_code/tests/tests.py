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
    default_ref_base_file_name = 'qrfromtext_default'

    @staticmethod
    def _get_reference_result_for_default_svg():
        return get_svg_content_from_file_name(TestQRUrlFromTextResult.default_ref_base_file_name + SVG_REF_SUFFIX)

    @staticmethod
    def _get_reference_result_for_default_png():
        return get_png_content_from_file_name(TestQRUrlFromTextResult.default_ref_base_file_name + PNG_REF_SUFFIX)

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
                if is_first and REFRESH_REFERENCE_IMAGES:
                    write_svg_content_to_file(TestQRUrlFromTextResult.default_ref_base_file_name + SVG_REF_SUFFIX,
                                              image_data)
                    is_first = False
                self.assertEqual(image_data, TestQRUrlFromTextResult._get_reference_result_for_default_svg())

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
                if is_first and REFRESH_REFERENCE_IMAGES:
                    write_png_content_to_file(TestQRUrlFromTextResult.default_ref_base_file_name + PNG_REF_SUFFIX,
                                              response.content)
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
        base_file_name = "qrfromtext_version"
        versions = [None, -1, 0, 41, '-1', '0', '41', 'blabla', 1, '1', 2, '2', 4, '4']
        version_names = ['default'] * 10 + [
            '2',
            '2',
            '4',
            '4'
        ]
        for i in range(len(versions)):
            version = versions[i]
            print('Testing SVG with version %s' % version)
            version_name = version_names[i]
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(version=version))
            qr2 = qr_from_text(TEST_TEXT, version=version)
            qr3 = qr_from_text(TEST_TEXT, version=version, image_format='svg')
            qr4 = qr_from_text(TEST_TEXT, version=version, image_format='SVG')
            qr5 = qr_from_text(TEST_TEXT, options=QRCodeOptions(version=version, image_format='SVG'))
            qr6 = qr_from_text(TEST_TEXT, version=version, image_format='invalid-format-name')
            result_file_name = '%s_%s%s' % (base_file_name, version_name, SVG_REF_SUFFIX)
            if REFRESH_REFERENCE_IMAGES:
                write_svg_content_to_file(result_file_name, _make_xml_header() + '\n' + qr1)
            result = get_svg_content_from_file_name(result_file_name, skip_header=True)
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
        base_file_name = "qrfromtext_version"
        versions = [None, -1, 0, 41, '-1', '0', '41', 'blabla', 1, '1', 2, '2', 4, '4']
        version_names = ['default'] * 10 + [
            '2',
            '2',
            '4',
            '4'
        ]
        for i in range(len(versions)):
            version = versions[i]
            print('Testing PNG with version %s' % version)
            version_name = version_names[i]
            qr1 = make_embedded_qr_code(TEST_TEXT, QRCodeOptions(version=version, image_format='png'))
            qr2 = qr_from_text(TEST_TEXT, version=version, image_format='png')
            qr3 = qr_from_text(TEST_TEXT, version=version, image_format='PNG')
            qr4 = qr_from_text(TEST_TEXT, options=QRCodeOptions(version=version, image_format='PNG'))
            result_file_name = '%s_%s%s' % (base_file_name, version_name, PNG_REF_SUFFIX)
            if REFRESH_REFERENCE_IMAGES:
                match = IMAGE_TAG_BASE64_DATA_RE.search(qr1)
                source_image_data = match.group('data')
                write_png_content_to_file(result_file_name, base64.b64decode(source_image_data))
            result =base64.b64encode(get_png_content_from_file_name(result_file_name)).decode('utf-8')
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
