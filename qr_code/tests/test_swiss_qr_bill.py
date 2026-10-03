"""Tests for the Swiss QR-bill data (SwissQrBill), its template tags and the Swiss cross."""
import base64
import io
from decimal import Decimal
from typing import Any

from django.test import SimpleTestCase
from PIL import Image

from qr_code.qrcode.maker import make_embedded_qr_code, make_qr, make_qr_code_image
from qr_code.qrcode.utils import (
    QRCodeOptions,
    SwissQrBill,
    SwissQrBillAddress,
    SWISS_QR_BILL_DO_NOT_USE_FOR_PAYMENT_MESSAGES,
    SWISS_QR_BILL_QR_CODE_ARGS,
    is_qr_iban,
    make_creditor_reference,
    make_qr_reference,
)
from qr_code.templatetags.qr_code import qr_for_swiss_qr_bill, qr_url_for_swiss_qr_bill

QR_IBAN = "CH4431999123000889012"
IBAN = "CH5800791123000889012"
QR_REFERENCE = "210000000003139471430009017"
CREDITOR_REFERENCE = "RF18539007547034"
BILLING_INFORMATION = "//S1/10/10201409/11/200701/20/140.000-53/30/102673831/31/200615/32/7.7/33/7.7:139.40/40/0:30"
CREDITOR = dict(name="Robert Schneider AG", street="Rue du Lac", building_number="1268", postal_code="2501", town="Biel")
DEBTOR = dict(name="Pia-Maria Rutschmann-Schnyder", street="Grosse Marktgasse", building_number="28", postal_code="9400", town="Rorschach")


def _make_bill(**kwargs) -> SwissQrBill:
    kw: dict[str, Any] = dict(account=QR_IBAN, creditor=CREDITOR, reference=QR_REFERENCE)
    kw.update(kwargs)
    return SwissQrBill(**kw)


class TestSwissQrBillReferences(SimpleTestCase):
    def test_make_qr_reference(self):
        self.assertEqual(make_qr_reference("21 00000 00003 13947 14300 0901"), QR_REFERENCE)
        self.assertEqual(make_qr_reference(1), "000000000000000000000000011")

    def test_make_qr_reference_with_invalid_base(self):
        for base in ["", "0", "000", "12A", "1" * 27, -1]:
            with self.subTest(base=base):
                self.assertRaises(ValueError, make_qr_reference, base)

    def test_make_creditor_reference(self):
        self.assertEqual(make_creditor_reference("5390 0754 7034"), CREDITOR_REFERENCE)
        self.assertEqual(make_creditor_reference("invoice42"), "RF72INVOICE42")
        # The creditor reference is valid according to the SwissQrBill validation.
        self.assertEqual(_make_bill(account=IBAN, reference=make_creditor_reference("invoice42")).reference_type, "SCOR")

    def test_make_creditor_reference_with_invalid_base(self):
        for base in ["", "invoice-42", "1" * 22]:
            with self.subTest(base=base):
                self.assertRaises(ValueError, make_creditor_reference, base)

    def test_is_qr_iban(self):
        self.assertTrue(is_qr_iban(QR_IBAN))
        self.assertTrue(is_qr_iban("ch44 3199 9123 0008 8901 2"))
        self.assertTrue(is_qr_iban("CH4430000123000889012"))
        self.assertFalse(is_qr_iban(IBAN))
        self.assertFalse(is_qr_iban("CH4432000123000889012"))
        self.assertFalse(is_qr_iban("CH"))


class TestSwissQrBill(SimpleTestCase):
    def test_make_qr_code_data_with_qr_reference(self):
        bill = _make_bill(
            amount=Decimal("1949.75"),
            debtor=DEBTOR,
            unstructured_message="Order of 15 June 2020",
            billing_information=BILLING_INFORMATION,
        )
        expected = [
            "SPC", "0200", "1", QR_IBAN,
            "S", "Robert Schneider AG", "Rue du Lac", "1268", "2501", "Biel", "CH",
            "", "", "", "", "", "", "",
            "1949.75", "CHF",
            "S", "Pia-Maria Rutschmann-Schnyder", "Grosse Marktgasse", "28", "9400", "Rorschach", "CH",
            "QRR", QR_REFERENCE, "Order of 15 June 2020", "EPD",
            BILLING_INFORMATION,
        ]  # fmt: skip
        self.assertEqual(bill.reference_type, "QRR")
        self.assertEqual(bill.make_qr_code_data(), "\n".join(expected))

    def test_make_qr_code_data_with_creditor_reference(self):
        bill = _make_bill(
            account=IBAN,
            creditor=dict(name="Salvation Army Foundation Switzerland", postal_code=3000, town="Bern", country="ch"),
            currency="EUR",
            reference="RF18 5390 0754 7034",
            alternative_schemes=["Name AV1: UV;UltraPay005;12345"],
        )
        expected = [
            "SPC", "0200", "1", IBAN,
            "S", "Salvation Army Foundation Switzerland", "", "", "3000", "Bern", "CH",
            "", "", "", "", "", "", "",
            "", "EUR",
            "", "", "", "", "", "", "",
            "SCOR", CREDITOR_REFERENCE, "", "EPD",
            "",
            "Name AV1: UV;UltraPay005;12345",
        ]  # fmt: skip
        self.assertEqual(bill.reference_type, "SCOR")
        self.assertEqual(bill.make_qr_code_data(), "\n".join(expected))

    def test_make_qr_code_data_without_reference(self):
        bill = _make_bill(account=IBAN, reference=None, amount=20, unstructured_message="Donation")
        data = bill.make_qr_code_data()
        self.assertEqual(bill.reference_type, "NON")
        self.assertTrue(data.endswith("\n20.00\nCHF\n\n\n\n\n\n\n\nNON\n\nDonation\nEPD"))

    def test_normalization(self):
        bill = _make_bill(
            account="ch44 3199 9123 0008 8901 2",
            creditor=SwissQrBillAddress(name=" Club ", postal_code=2900, town="Porrentruy ", building_number=12, country="li"),
            reference=make_qr_reference(123).lstrip("0"),
            amount=20.5,
            currency="chf",
        )
        self.assertEqual(bill.account, QR_IBAN)
        self.assertEqual(bill.reference, make_qr_reference(123))
        self.assertEqual(bill.currency, "CHF")
        self.assertEqual(bill.amount, Decimal("20.5"))
        self.assertEqual(bill.creditor, SwissQrBillAddress(name="Club", postal_code="2900", town="Porrentruy", building_number="12", country="LI"))
        self.assertIn("\n20.50\n", bill.make_qr_code_data())

    def test_amount_limits(self):
        self.assertIn("\n0.01\nCHF\n", _make_bill(amount="0.01").make_qr_code_data())
        self.assertIn("\n999999999.99\nCHF\n", _make_bill(amount="999999999.99").make_qr_code_data())

    def test_notification_with_zero_amount(self):
        # An amount of 0.00 is only allowed for a notification that must not be paid.
        for language, message in SWISS_QR_BILL_DO_NOT_USE_FOR_PAYMENT_MESSAGES.items():
            for amount in [0, "0.00", "-0"]:
                with self.subTest(language=language, amount=amount):
                    data = _make_bill(amount=amount, unstructured_message=message).make_qr_code_data()
                    self.assertTrue(data.endswith(f"\n0.00\nCHF\n\n\n\n\n\n\n\nQRR\n{QR_REFERENCE}\n{message}\nEPD"))
        for message in [None, "Contribution 2026", "Ne pas utiliser pour le paiement"]:
            with self.subTest(message=message):
                self.assertRaises(ValueError, _make_bill, amount=0, unstructured_message=message)

    def test_invalid_data(self):
        too_long_address = dict(CREDITOR, name="N" * 71)
        invalid_kwargs = [
            dict(account="DE33100205000001194700"),
            dict(account="CH4431999123000889013"),
            dict(account="CH443199912300088901"),
            dict(reference=None),
            dict(reference=CREDITOR_REFERENCE),
            dict(account=IBAN),
            dict(reference="210000000003139471430009018"),
            dict(reference="ABC"),
            dict(account=IBAN, reference="RF19539007547034"),
            dict(amount=-1),
            dict(amount="-0.01"),
            dict(amount="1000000000"),
            dict(amount="10.005"),
            dict(currency="USD"),
            dict(currency="EUR"),
            dict(reference="0" * 27),
            dict(creditor=too_long_address),
            dict(debtor=too_long_address),
            dict(creditor=dict(CREDITOR, name=" ")),
            dict(creditor=dict(CREDITOR, name="Robert\nSchneider AG")),
            dict(creditor=dict(CREDITOR, street="S" * 71)),
            dict(creditor=dict(CREDITOR, building_number="1" * 17)),
            dict(creditor=dict(CREDITOR, postal_code="")),
            dict(creditor=dict(CREDITOR, postal_code="1" * 17)),
            dict(creditor=dict(CREDITOR, town="T" * 36)),
            dict(creditor=dict(CREDITOR, country="CHE")),
            dict(unstructured_message="M" * 141),
            dict(unstructured_message="Line 1\r\nLine 2"),
            dict(billing_information="S1/10/10201409"),
            dict(unstructured_message="M" * 100, billing_information="//" + "B" * 39),
            dict(alternative_schemes=["A", "B", "C"]),
            dict(alternative_schemes=["A" * 101]),
            dict(alternative_schemes=[""]),
        ]
        for kwargs in invalid_kwargs:
            with self.subTest(kwargs=kwargs):
                self.assertRaises(ValueError, _make_bill, **kwargs)

    def test_data_too_large(self):
        address = dict(name="é" * 70, street="é" * 70, building_number="é" * 16, postal_code="é" * 16, town="é" * 35)
        bill = _make_bill(creditor=address, debtor=address, unstructured_message="é" * 140)
        self.assertRaises(ValueError, bill.make_qr_code_data)


class TestSwissQrBillTemplateTags(SimpleTestCase):
    def test_qr_code_options(self):
        bill = _make_bill(debtor=DEBTOR)
        self.assertEqual(make_qr(bill.make_qr_code_data(), QRCodeOptions(**SWISS_QR_BILL_QR_CODE_ARGS)).error, "M")
        # The QR code options required by the specification take precedence over the template tag arguments.
        self.assertEqual(qr_for_swiss_qr_bill(bill, error_correction="H"), qr_for_swiss_qr_bill(bill))
        self.assertEqual(qr_url_for_swiss_qr_bill(bill, error_correction="H"), qr_url_for_swiss_qr_bill(bill))

    def test_from_object_or_dict(self):
        kwargs = dict(account=QR_IBAN, creditor=CREDITOR, debtor=DEBTOR, reference=QR_REFERENCE)
        self.assertEqual(qr_for_swiss_qr_bill(kwargs), qr_for_swiss_qr_bill(SwissQrBill(**kwargs)))
        self.assertEqual(qr_url_for_swiss_qr_bill(kwargs), qr_url_for_swiss_qr_bill(SwissQrBill(**kwargs)))


class TestSwissCross(SimpleTestCase):
    """The Swiss cross is drawn in the middle of any QR code that encodes the data of a Swiss QR code."""

    data = _make_bill(debtor=DEBTOR).make_qr_code_data()

    def _check_png_cross(self, png: bytes, border: int):
        image = Image.open(io.BytesIO(png)).convert("RGB")
        center = image.width // 2
        # The size of the Swiss cross is 7/46 of the symbol size, without the quiet zone (the border).
        modules = make_qr(self.data, QRCodeOptions(**SWISS_QR_BILL_QR_CODE_ARGS)).symbol_size(scale=1, border=0)[0]
        cross_size = image.width * modules / (modules + 2 * border) * 7 / 46
        white, black = (255, 255, 255), (0, 0, 0)
        # Center of the white cross, black square around the cross, white border of the black square.
        for offset, color in [(0, white), (0.3 * cross_size, black), (0.47 * cross_size, white)]:
            with self.subTest(offset=offset):
                self.assertEqual(image.getpixel((round(center + offset), round(center + offset))), color)

    def test_png(self):
        for options in [dict(size=10), dict(size=10, border=6, dark_color="darkblue", light_color=None)]:
            with self.subTest(options=options):
                qr_code_options = QRCodeOptions(**SWISS_QR_BILL_QR_CODE_ARGS, image_format="png", **options)
                self._check_png_cross(make_qr_code_image(self.data, qr_code_options), qr_code_options.border)
                # The data may also be passed as bytes, with any line separator.
                crlf_data = self.data.replace("\n", "\r\n").encode("utf-8")
                self._check_png_cross(make_qr_code_image(crlf_data, qr_code_options, force_text=False), qr_code_options.border)
                html = make_embedded_qr_code(self.data, qr_code_options)
                png = base64.b64decode(html.split("base64,")[1].split('"')[0])
                self._check_png_cross(png, qr_code_options.border)

    def test_svg(self):
        cross_path = '<path fill="#000" d="M'
        options = QRCodeOptions(**SWISS_QR_BILL_QR_CODE_ARGS, image_format="svg")
        svg = make_qr_code_image(self.data, options).decode("utf-8")
        self.assertIn(cross_path, svg)
        self.assertTrue(svg.endswith("</g></svg>\n") or svg.endswith("</g></svg>"))
        self.assertIn(cross_path, make_embedded_qr_code(self.data, options))
        html = make_embedded_qr_code(self.data, options, use_data_uri_for_svg=True)
        self.assertIn(cross_path, base64.b64decode(html.split("base64,")[1].split('"')[0]).decode("utf-8"))

    def test_no_cross_for_other_data(self):
        for data in ["Hello", "SPC", "SPC\n0100\n1\n", "SPC-like text", 12345]:
            with self.subTest(data=data):
                svg_options = QRCodeOptions(image_format="svg")
                png_options = QRCodeOptions(image_format="png")
                self.assertNotIn('<path fill="#000" d="M', make_embedded_qr_code(data, svg_options))
                self.assertEqual(make_qr_code_image(data, png_options), _png_without_cross(data, png_options))


def _png_without_cross(data, options: QRCodeOptions) -> bytes:
    out = io.BytesIO()
    make_qr(data, options).save(out, **options.kw_save())
    return out.getvalue()
