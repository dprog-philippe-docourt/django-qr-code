"""Tests for qr_code application."""
import base64

from dataclasses import asdict
from datetime import date

from django.template import Template, Context
from django.test import SimpleTestCase, override_settings
from django.utils.safestring import mark_safe

from qr_code.qrcode.utils import ContactDetail, VCard, MeCard, WifiConfig, Coordinates, EpcData
from qr_code.tests import REFRESH_REFERENCE_IMAGES, IMAGE_TAG_BASE64_DATA_RE
from qr_code.tests.utils import (
    write_svg_content_to_file,
    get_svg_content_from_file_name,
    minimal_svg,
    get_png_content_from_file_name,
    write_png_content_to_file,
)


TEST_CONTACT_DETAIL = dict(
    first_name="Jérémy Sébastien Ninõ",
    last_name="Érard",
    first_name_reading="jAAn",
    last_name_reading="dOH",
    tel="+41769998877",
    email="j.doe@company.com",
    url="http://www.company.com",
    birthday=date(year=1985, month=10, day=2),
    address="Cras des Fourches 987, 2800 Delémont, Jura, Switzerland",
    memo="Development Manager",
    org="Company Ltd",
)
TEST_MECARD_CONTACT = MeCard(
    name="Ninõ,Jérémy Sébastien",
    phone="+41769998877",
    email="j.doe@company.com",
    url="http://www.company.com",
    birthday=date(year=1985, month=10, day=2),
    memo="Development Manager",
    org="Company Ltd",
)

TEST_VCARD_CONTACT = VCard(
    name="Ninõ;Jérémy Sébastien",
    phone="+41769998877",
    email="j.doe@company.com",
    url="http://www.company.com",
    birthday=date(year=1985, month=10, day=2),
    street="Cras des Fourches 987",
    city="Delémont",
    zipcode=2800,
    region="Jura",
    country="Switzerland",
    memo="Development Manager",
    org="Company Ltd",
)
TEST_WIFI_CONFIG = dict(ssid="my-wifi", authentication=WifiConfig.AUTHENTICATION.WPA, password="wifi-password")
TEST_EPC_QR_1 = dict(
    name="Wikimedia Foerdergesellschaft", iban="DE33100205000001194700", amount=20, text="To Wikipedia, From Gérard Boéchat"
)
TEST_EPC_QR_2 = dict(name="Wikimedia Foerdergesellschaft", iban="DE33100205000001194700", amount=50.0, reference="12983020")


class TestContactDetail(SimpleTestCase):
    def test_make_qr_code_text_with_contact_detail(self):
        data = dict(**TEST_CONTACT_DETAIL)
        c1 = ContactDetail(**data)
        data["nickname"] = "buddy"
        c2 = ContactDetail(**data)
        data["last_name"] = "O'Hara;,:"
        data["tel_av"] = "n/a"
        c3 = ContactDetail(**data)
        del data["last_name"]
        c4 = ContactDetail(**data)
        self.assertEqual(
            c1.make_qr_code_data(),
            r"MECARD:N:Érard,Jérémy Sébastien Ninõ;SOUND:dOH,jAAn;TEL:+41769998877;EMAIL:j.doe@company.com;NOTE:Development Manager;BDAY:19851002;ADR:Cras des Fourches 987, 2800 Delémont, Jura, Switzerland;URL:http\://www.company.com;ORG:Company Ltd;;",
        )
        self.assertEqual(
            c2.make_qr_code_data(),
            r"MECARD:N:Érard,Jérémy Sébastien Ninõ;SOUND:dOH,jAAn;TEL:+41769998877;EMAIL:j.doe@company.com;NOTE:Development Manager;BDAY:19851002;ADR:Cras des Fourches 987, 2800 Delémont, Jura, Switzerland;URL:http\://www.company.com;NICKNAME:buddy;ORG:Company Ltd;;",
        )
        self.assertEqual(
            c3.make_qr_code_data(),
            r"MECARD:N:O'Hara\;\,\:,Jérémy Sébastien Ninõ;SOUND:dOH,jAAn;TEL:+41769998877;TEL-AV:n/a;EMAIL:j.doe@company.com;NOTE:Development Manager;BDAY:19851002;ADR:Cras des Fourches 987, 2800 Delémont, Jura, Switzerland;URL:http\://www.company.com;NICKNAME:buddy;ORG:Company Ltd;;",
        )
        self.assertEqual(
            c4.make_qr_code_data(),
            r"MECARD:N:Jérémy Sébastien Ninõ;SOUND:dOH,jAAn;TEL:+41769998877;TEL-AV:n/a;EMAIL:j.doe@company.com;NOTE:Development Manager;BDAY:19851002;ADR:Cras des Fourches 987, 2800 Delémont, Jura, Switzerland;URL:http\://www.company.com;NICKNAME:buddy;ORG:Company Ltd;;",
        )

    def test_make_qr_code_text_with_mecard(self):
        data = asdict(TEST_MECARD_CONTACT)
        c1 = MeCard(**data)
        data["nickname"] = "buddy"
        c2 = MeCard(**data)
        self.assertEqual(
            c1.make_qr_code_data(),
            r"MECARD:N:Ninõ,Jérémy Sébastien;TEL:+41769998877;EMAIL:j.doe@company.com;BDAY:19851002;URL:http\://www.company.com;MEMO:Development Manager;;ORG:Company Ltd;",
        )
        self.assertEqual(
            c2.make_qr_code_data(),
            r"MECARD:N:Ninõ,Jérémy Sébastien;TEL:+41769998877;EMAIL:j.doe@company.com;NICKNAME:buddy;BDAY:19851002;URL:http\://www.company.com;MEMO:Development Manager;;ORG:Company Ltd;",
        )

    def test_make_qr_code_text_with_vcard(self):
        data = asdict(TEST_VCARD_CONTACT)
        c1 = VCard(**data)
        data["nickname"] = "buddy"
        c2 = VCard(**data)
        self.assertEqual(
            c1.make_qr_code_data(),
            """BEGIN:VCARD\r
VERSION:3.0\r
N:Ninõ;Jérémy Sébastien\r
FN:Ninõ Jérémy Sébastien\r
ORG:Company Ltd\r
EMAIL:j.doe@company.com\r
TEL:+41769998877\r
URL:http://www.company.com\r
ADR:;;Cras des Fourches 987;Delémont;Jura;2800;Switzerland\r
BDAY:1985-10-02\r
NOTE:Development Manager\r
END:VCARD\r
""",
        )
        self.assertEqual(
            c2.make_qr_code_data(),
            """BEGIN:VCARD\r
VERSION:3.0\r
N:Ninõ;Jérémy Sébastien\r
FN:Ninõ Jérémy Sébastien\r
ORG:Company Ltd\r
EMAIL:j.doe@company.com\r
TEL:+41769998877\r
URL:http://www.company.com\r
NICKNAME:buddy\r
ADR:;;Cras des Fourches 987;Delémont;Jura;2800;Switzerland\r
BDAY:1985-10-02\r
NOTE:Development Manager\r
END:VCARD\r
""",
        )


class TestWifiConfig(SimpleTestCase):
    def test_make_qr_code_text(self):
        wifi1 = WifiConfig(**TEST_WIFI_CONFIG)
        wifi2 = WifiConfig(hidden=True, **TEST_WIFI_CONFIG)
        self.assertEqual(wifi1.make_qr_code_data(), "WIFI:S:my-wifi;T:WPA;P:wifi-password;;")
        self.assertEqual(wifi2.make_qr_code_data(), "WIFI:S:my-wifi;T:WPA;P:wifi-password;H:true;;")


class TestCoordinates(SimpleTestCase):
    def test_coordinates(self):
        c1 = Coordinates(latitude=586000.32, longitude=250954.19)
        c2 = Coordinates(latitude=586000.32, longitude=250954.19, altitude=500)
        self.assertEqual(c1.__str__(), "latitude: 586000.32, longitude: 250954.19")
        self.assertEqual(c2.__str__(), "latitude: 586000.32, longitude: 250954.19, altitude: 500")


class TestQRForApplications(SimpleTestCase):
    @staticmethod
    def _make_test_data(tag_pattern, ref_file_name, tag_args, template_context=dict()):
        tag_content = tag_pattern
        for key, value in tag_args.items():
            if isinstance(value, str):
                tag_content += ' %s="%s"' % (key, value)
            else:
                tag_content += " %s=%s" % (key, value)
        return dict(source="{% " + tag_content + " %}", ref_file_name=ref_file_name, template_context=template_context)

    @staticmethod
    def _make_tests_data(embedded=True, image_format="svg"):
        contact_detail1 = dict(**TEST_CONTACT_DETAIL)
        contact_detail2 = ContactDetail(**contact_detail1)
        wifi_config1 = dict(**TEST_WIFI_CONFIG)
        wifi_config2 = WifiConfig(**wifi_config1)
        epc_data1 = dict(**TEST_EPC_QR_1)
        epc_data2 = EpcData(**epc_data1)
        epc_data3 = dict(**TEST_EPC_QR_2)
        google_maps_coordinates = Coordinates(latitude=586000.32, longitude=250954.19)
        geolocation_coordinates = Coordinates(latitude=586000.32, longitude=250954.19, altitude=500)
        tag_prefix = "qr_for_" if embedded else "qr_url_for_"
        tag_args = dict(image_format=image_format)
        if image_format == "png":
            tag_args["size"] = "t"
        if not embedded:
            # Deactivate cache for URL.
            tag_args["cache_enabled"] = False
        raw_data = (
            ("email", '"john.doe@domain.com"', None, None),
            ("tel", ' "+41769998877"', None, None),
            ("sms", ' "+41769998877"', None, None),
            ("geolocation", "latitude=586000.32 longitude=250954.19 altitude=500", None, None),
            ("geolocation", "coordinates=coordinates", {"coordinates": geolocation_coordinates}, None),
            ("google_maps", "latitude=586000.32 longitude=250954.19", None, None),
            ("google_maps", "coordinates=coordinates", {"coordinates": google_maps_coordinates}, None),
            ("wifi", "wifi_config", {"wifi_config": wifi_config1}, None),
            ("wifi", "wifi_config", {"wifi_config": wifi_config2}, None),
            ("wifi", "wifi_config=wifi_config", {"wifi_config": wifi_config2}, None),
            ("epc", "epc_data", {"epc_data": epc_data1}, 1),
            ("epc", "epc_data", {"epc_data": epc_data2}, 1),
            ("epc", "epc_data=epc_data", {"epc_data": epc_data2}, 1),
            ("epc", "epc_data", {"epc_data": epc_data3}, 2),
            ("contact", "contact_detail", {"contact_detail": contact_detail1}, None),
            ("contact", "contact_detail", {"contact_detail": contact_detail2}, None),
            ("contact", "contact_detail=contact_detail", {"contact_detail": contact_detail2}, None),
            ("mecard", "mecard=mecard", {"mecard": TEST_MECARD_CONTACT}, None),
            ("mecard", "mecard", {"mecard": TEST_MECARD_CONTACT}, None),
            ("vcard", "vcard=vcard", {"vcard": TEST_VCARD_CONTACT}, None),
            ("vcard", "vcard", {"vcard": TEST_VCARD_CONTACT}, None),
            ("youtube", '"J9go2nj6b3M"', None, None),
            ("youtube", "video_id", {"video_id": "J9go2nj6b3M"}, None),
            ("google_play", '"ch.admin.meteoswiss"', None, None),
        )
        tests_data = []
        for tag_base_name, tag_data, template_context, number in raw_data:
            ref_file_name = "qr_for_%s" % tag_base_name
            if number is not None:
                ref_file_name = f"{ref_file_name}_{number}"
            test_data = TestQRForApplications._make_test_data(
                tag_pattern="%s%s %s" % (tag_prefix, tag_base_name, tag_data),
                ref_file_name=ref_file_name,
                tag_args=tag_args,
                template_context=template_context,
            )
            tests_data.append(test_data)
        return tests_data

    @staticmethod
    def _get_rendered_template(template_source, template_context):
        html_source = mark_safe("{% load qr_code %}" + template_source)
        template = Template(html_source)
        context = Context()
        if template_context:
            context.update(template_context)
        return template.render(context).strip()

    def test_demo_samples_embedded_in_svg_format(self):
        tests_data = self._make_tests_data(embedded=True)
        for test_data in tests_data:
            print("Testing template: %s" % test_data["source"])
            source_image_data = TestQRForApplications._get_rendered_template(test_data["source"], test_data.get("template_context"))
            if REFRESH_REFERENCE_IMAGES:
                write_svg_content_to_file(test_data["ref_file_name"], source_image_data)
            ref_image_data = get_svg_content_from_file_name(test_data["ref_file_name"])
            self.assertEqual(source_image_data, ref_image_data)

    def test_demo_samples_embedded_in_png_format(self):
        tests_data = self._make_tests_data(embedded=True, image_format="png")
        for test_data in tests_data:
            print("Testing template: %s" % test_data["source"])
            source_image_data = TestQRForApplications._get_rendered_template(test_data["source"], test_data.get("template_context"))
            match = IMAGE_TAG_BASE64_DATA_RE.search(source_image_data)
            source_image_data = match.group("data")
            source_image_data = base64.b64decode(source_image_data)
            if REFRESH_REFERENCE_IMAGES:
                write_png_content_to_file(test_data["ref_file_name"], source_image_data)
            ref_image_data = get_png_content_from_file_name(test_data["ref_file_name"])
            self.assertEqual(source_image_data, ref_image_data)

    def test_demo_sample_urls_in_svg_format(self):
        tests_data = self._make_tests_data(embedded=False)
        for test_data in tests_data:
            source_image_data = self._check_url_for_test_data(test_data).content.decode("utf-8")
            if REFRESH_REFERENCE_IMAGES:
                write_svg_content_to_file(test_data["ref_file_name"], source_image_data)
            ref_image_data = get_svg_content_from_file_name(test_data["ref_file_name"])
            self.assertEqual(minimal_svg(source_image_data), minimal_svg(ref_image_data))

    def test_demo_sample_urls_in_png_format(self):
        tests_data = self._make_tests_data(embedded=False, image_format="png")
        for test_data in tests_data:
            source_image_data = self._check_url_for_test_data(test_data).content
            if REFRESH_REFERENCE_IMAGES:
                write_png_content_to_file(test_data["ref_file_name"], source_image_data)
            ref_image_data = get_png_content_from_file_name(test_data["ref_file_name"])
            self.assertEqual(source_image_data, ref_image_data)

    def _check_url_for_test_data(self, test_data):
        print("Testing template: %s" % test_data["source"])
        source_image_url = TestQRForApplications._get_rendered_template(test_data["source"], test_data.get("template_context"))
        response = self.client.get(source_image_url)
        self.assertEqual(response.status_code, 200)
        return response
