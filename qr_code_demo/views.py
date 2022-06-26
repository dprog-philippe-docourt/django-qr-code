from datetime import date, datetime
from django.shortcuts import render

from qr_code.qrcode.utils import (
    MeCard,
    VCard,
    WifiConfig,
    Coordinates,
    QRCodeOptions,
    Email,
    EpcData,
    VEvent,
    EventClass,
    EventStatus,
    EventTransparency,
)

# Use a ContactDetail instance to encapsulate the detail of the contact.
DEMO_MECARD_CONTACT = MeCard(
    name="Doe, John",
    phone="+41769998877",
    email="j.doe@company.com",
    url="http://www.company.com",
    birthday=date(year=1985, month=10, day=2),
    memo="Development Manager",
    org="Company Ltd",
)

DEMO_VCARD_CONTACT = VCard(
    name="Doe; John",
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

DEMO_EVENT = VEvent(
    uid="some-event-id",
    summary="Vacations",
    start=datetime(2022, 8, 6, hour=8, minute=30),
    end=datetime(2022, 8, 17, hour=12),
    location="New-York, Statue de la Liberté",
    geo=(40.69216097988203, -74.04460073403436),
    categories=["PERSO", "holidays"],
    status=EventStatus.CONFIRMED,
    event_class=EventClass.PRIVATE,
    transparency=EventTransparency.OPAQUE,
    organizer="foo@bar.com",
    url="https://bar.com",
    description="""Fake description. Meeting to provide technical review for "Phoenix" design. Happy Face Conference Room.

Phoenix design team MUST attend this meeting.

RSVP to team leader.""",
)

# Use a WifiConfig instance to encapsulate the configuration of the connexion.
DEMO_WIFI = WifiConfig(ssid="my-wifi", authentication=WifiConfig.AUTHENTICATION.WPA, password="wifi-password")

DEMO_COORDINATES = Coordinates(latitude=586000.32, longitude=250954.19, altitude=500)

DEMO_OPTIONS = QRCodeOptions(size="t", border=6, error_correction="L")


def index(request):
    """
    Build the home page of this demo app.

    :param request:
    :return: HTTP response providing the home page of this demo app.
    """

    # Build context for rendering QR codes.
    context = dict(
        mecard_contact=DEMO_MECARD_CONTACT,
        vcard_contact=DEMO_VCARD_CONTACT,
        wifi_config=DEMO_WIFI,
        video_id="J9go2nj6b3M",
        google_maps_coordinates=DEMO_COORDINATES,
        geolocation_coordinates=DEMO_COORDINATES,
        email=Email(
            to="john.doe@domain.com",
            cc=("bob.doe@domain.com", "alice.doe@domain.com"),
            bcc="secret@domain.com",
            subject="Important message",
            body="This is a very important message!",
        ),
        epc_data=EpcData(
            name="Wikimedia Foerdergesellschaft", iban="DE33100205000001194700", amount=20, text="To Wikipedia, From Gérard Boéchat"
        ),
        event=DEMO_EVENT,
        shift_js_encoded="ウェブサイトにおける文字コードの割合、UTF-8が90％超え。Shift_JISやEUC-JPは？".encode("shift-jis"),
        kanji_encoded="義務教育諸学校教科用図書検定基準".encode("cp932"),
        options_example=DEMO_OPTIONS,
    )

    # Render the index page.
    return render(request, "qr_code_demo/index.html", context=context)
