from datetime import date
from django.shortcuts import render

from qr_code.qrcode.utils import ContactDetail, WifiConfig, Coordinates, QRCodeOptions

# Use a ContactDetail instance to encapsulate the detail of the contact.
DEMO_CONTACT = ContactDetail(
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

# Use a WifiConfig instance to encapsulate the configuration of the connexion.
DEMO_WIFI = WifiConfig(
        ssid='my-wifi',
        authentication=WifiConfig.AUTHENTICATION.WPA,
        password='wifi-password'
    )

DEMO_COORDINATES = Coordinates(latitude=586000.32, longitude=250954.19, altitude=500)

DEMO_OPTIONS = QRCodeOptions(size='t', border=6, error_correction='L')


def index(request):
    """
    Build the home page of this demo app.

    :param request:
    :return: HTTP response providing the home page of this demo app.
    """

    # Build context for rendering QR codes.
    context = dict(
        contact_detail=DEMO_CONTACT,
        wifi_config=DEMO_WIFI,
        video_id='J9go2nj6b3M',
        google_maps_coordinates=DEMO_COORDINATES,
        geolocation_coordinates=DEMO_COORDINATES,
        options_example=DEMO_OPTIONS
    )

    # Render the index page.
    return render(request, 'qr_code_demo/index.html', context=context)
