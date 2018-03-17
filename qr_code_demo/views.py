from datetime import date
from django.shortcuts import render

from qr_code.qrcode.utils import ContactDetail, WifiConfig


def index(request):
    """
    Build the home page of this demo app.

    :param request:
    :return: HTTP response providing the home page of thisd emo app.
    """
    # Use a ContactDetail instance to encapsulate the detail of the contact.
    contact_detail = ContactDetail(
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
    # Use a WifiConfig instance to encapsulate the detail of the connexion.
    wifi_config = WifiConfig(
        ssid='my-wifi',
        authentication=WifiConfig.AUTHENTICATION.WPA,
        password='wifi-password'
    )
    # Build context for rendering QR codes.
    return render(request, 'qr_code_demo/index.html', context=dict(contact_detail=contact_detail, wifi_config=wifi_config))
