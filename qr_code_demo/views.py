from datetime import date
from django.shortcuts import render


def index(request):
    contact_dict = dict(
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
    wifi_dict = dict(
        ssid='my-wifi',
        authentication='WPA',
        password='wifi-password'
    )
    return render(request, 'qr_code_demo/index.html', context=dict(contact_dict=contact_dict, wifi_dict=wifi_dict))
