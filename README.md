# Django QR Code
[![Latest PyPI version](https://badge.fury.io/py/django-qr-code.svg)](https://badge.fury.io/py/django-qr-code)
[![Downloads](https://img.shields.io/pypi/dm/django-qr-code.svg)](https://pypi.python.org/pypi/django-qr-code)
[![Documentation Status](https://readthedocs.org/projects/django-qr-code/badge/?version=latest)](http://django-qr-code.readthedocs.io/en/latest/)
[![Build Status](https://travis-ci.com/dprog-philippe-docourt/django-qr-code.svg?branch=master)](https://app.travis-ci.com/github/dprog-philippe-docourt/django-qr-code)
[![Maintainability](https://api.codeclimate.com/v1/badges/c47e79bf51f6a2bb8264/maintainability)](https://codeclimate.com/github/dprog-philippe-docourt/django-qr-code/maintainability)
[![Coverage Status](https://coveralls.io/repos/github/dprog-philippe-docourt/django-qr-code/badge.svg?branch=master)](https://coveralls.io/github/dprog-philippe-docourt/django-qr-code?branch=master)

This is an application that provides tools for displaying QR codes on your [Django](https://www.djangoproject.com/) site.

This application depends on the [Segno QR Code generator](https://pypi.org/project/segno/) library.

This app makes no usage of the Django models and therefore do not use any database.

Only Python >= 3.9 is supported.

## Features

* Generate QR codes as embedded SVG or PNG images in HTML templates.
* Customize QR codes with various parameters (size, error correction, border, etc.).
* Generate URLs for QR code images.
* Support for specific application QR codes (e.g., contact info, Wi-Fi config).
* Cache QR code images for performance.
* Secure QR code image serving with URL protection and user authentication.

## Installation

### Binary Package from PyPi
In order to use this app in a Django project, the simplest way is to install it from [PyPi](https://pypi.python.org/pypi/django-qr-code):
```bash
pip install django-qr-code
```

### From the Source Code
In order to modify or test this app you may want to install it from the source code.

Clone the [GitHub repository](https://github.com/dprog-philippe-docourt/django-qr-code) and install dependencies:
```bash
git clone https://github.com/dprog-philippe-docourt/django-qr-code
pip install -r requirements.txt -r requirements-dev.txt
python manage.py collectstatic --no-input
```

## Usage
Start by adding `qr_code` to your `INSTALLED_APPS` setting like this:
```python
INSTALLED_APPS = (
    # ...,
    'qr_code',
)
```

You need to load the tags provided by this app in your template with:
```djangotemplate
{% load qr_code %}
```

The source code on [GitHub](https://github.com/dprog-philippe-docourt/django-qr-code) contains a simple demo app. Please check out the [templates folder](https://github.com/dprog-philippe-docourt/django-qr-code/tree/master/qr_code_demo/templates/qr_code_demo) for an example of template, and the [setting](https://github.com/dprog-philippe-docourt/django-qr-code/tree/master/demo_site/settings.py) and [urls](https://github.com/dprog-philippe-docourt/django-qr-code/tree/master/demo_site/urls.py) files for an example of configuration and integration.

### Example: Inline QR Code

Generate a simple QR code:

```djangotemplate
{% qr_from_text "Hello World!" size="T" %}
```
### Example: URL QR Code

Generate a URL for a QR code image:

```djangotemplate
<img src="{% qr_url_from_text "Hello World!" %}" alt="Hello World!">
```

### Generating Inline QR Code in your HTML (qr_from_text)
The tag **`qr_from_text`** generates an embedded `<svg>` or `<img>` tag within the HTML code produced by your template.

The following renders a tiny "hello world" QR code in SVG format with an inline `<svg>` tag:
```djangotemplate
{% qr_from_text "Hello World!" size="T" %}
```

Here is a medium "hello world" QR code in PNG format:
```djangotemplate
{% qr_from_text "Hello World!" size="m" image_format="png" error_correction="L" %}
```
This will output an `<img>` tag with data URI: `<img src="data:image/png;base64,[...]">`

#### Customizing the HTML Output

You can customize `alt` and `class` attributes can be customized through `alt_text` and `class_names` arguments of `qr_from_text`:
```djangotemplate
{% qr_from_text "Hello World!" alt_text="My Hello World image" class_names="ui centered image" %}
```
The `alt_text` argument indicates the value of the alternative text embedded in the `alt` attribute of the returned 
    image tag. When set to `None`, the alternative text is set to the string representation of data. The alternative 
    text is automatically escaped. You may use an empty string to explicitly set an empty alternative text.

The `class_names` argument indicates the value of the `class` attribute of the returned
    image tag. When set to `None` or empty, the class attribute is not set.

By default, when SVG format is specified, the generated tag is an inline SVG path: `<svg>`. To change that, you can p
ass `use_data_uri_for_svg=True` to the `qr_from_text` tag:
```djangotemplate
{% qr_from_text "Hello World!" use_data_uri_for_svg=True %}
```
This will output an `<img>` tag with a data URI similar to what you get by default for the PNG format: 
`<img src="data:image/svg+xml;base64,[...]">`. This also allows you to define the `class` and `alt` HTML attributes 
of the `<img>` tag as shown above. When `use_data_uri_for_svg` is not set or is set to `False`, the `alt_text` 
and `class_names` arguments are ignored.

### QR Code Rendering Options

#### Customization options overview

* `size`: Size of each module (e.g., T, S, M, L, H or specific integer). Default is 'M'
* `image_format`: Format of the image (e.g., 'svg', 'png'). Default is 'svg'.
* `border`: Border size in modules. Default is 4.
* `error_correction`: Error correction level ('L', 'M', 'Q', 'H'). Default is 'M'.
* `use_data_uri_for_svg`: Generate a data URI for SVG images. Default is `False`.
* `encoding`: Text encoding . Default is 'UTF-8'.
* `micro`: enforce the creation of a Micro QR Code. Default is `False`.
* `boost_error` indicates whether the QR code encoding engine (Segno) tries to increase the error correction level if it does not affect the version. Default is `False`.
* `eci` indicates if binary data which does not use the default encoding (ISO/IEC 8859-1). Default is `False`.
* `options`: Use an instance of QRCodeOptions to encapsulate multiple settings.

#### Examples of Rendering Options

The `size` parameter gives the size of each module of the QR code matrix. It can be either a positive integer or one of the following letters:

* t or T: tiny (value: 6)
* s or S: small (value: 12)
* m or M: medium (value: 18)
* l or L: large (value: 30)
* h or H: huge (value: 48)

For PNG image format the size unit is in pixels, while the unit is 1 mm for SVG format.

Here is a "hello world" QR code using the version 12:
```djangotemplate
{% qr_from_text "Hello World!" size=8 version=12 %}
```
The `version` parameter is an integer from 1 to 40 that controls the size of the QR code matrix. Set to None to determine this automatically. The smallest, version 1, is a 21 x 21 matrix. The biggest, version 40, is 177 x 177 matrix. The size grows by 4 modules/side.

Here is a "hello world" QR code using a border of 6 modules:
```djangotemplate
{% qr_from_text "Hello World!" size=10 border=6 %}
```
The `border` parameter controls how many modules thick the border should be (the default is 4, which is the minimum according to the specs).

There are 4 error correction levels used for QR codes, with each one adding different amounts of "backup" data
depending on how much damage the QR code is expected to suffer in its intended environment, and hence how much
error correction may be required. The correction level can be configured with the `error_correction` parameter as follows:
* l or L: error correction level L – up to 7% damage
* m or M: error correction level M – up to 15% damage
* q or Q: error correction level Q – up to 25% damage
* h or H: error correction level H – up to 30% damage

You may enforce the creation of a Micro QR Code with `micro=True`. The `micro` option defaults to `False`.

The `encoding` option controls the text encoding used in mode "byte" (used for any general text content). By default `encoding` is ``UTF-8``. When set to ``None``, the implementation (based on Segno) tries to use the standard conform ISO/IEC 8859-1 encoding and if it does not fit, it will use UTF-8. Note that no ECI mode indicator is inserted by default (see `eci` option). The `encoding` parameter is case-insensitive.

The `boost_error` indicates whether the QR code encoding engine (Segno) tries to increase the error correction level if it does not affect the version. Error correction level is not increased when it impacts the version of the code.

The `eci` option indicates if binary data which does not use the default encoding (ISO/IEC 8859-1) should enforce the ECI mode. Since a lot of QR code readers do not support the ECI mode, this feature is disabled by default and the data is encoded in the provided encoding using the usual “byte” mode. Set eci to `True` if an ECI header should be inserted into the QR Code. Note that the implementation may not know the ECI designator for the provided encoding and may raise an exception if the ECI designator cannot be found. The ECI mode is not supported by Micro QR Codes.

Alternatively, you may use the `options` keyword argument with an instance of `QRCodeOptions` as value instead of listing every requested options. Here is an example of view: 
```python
from django.shortcuts import render
from qr_code.qrcode.utils import QRCodeOptions

def my_view(request):
    # Build context for rendering QR codes.
    context = dict(
        my_options=QRCodeOptions(size='t', border=6, error_correction='L'),
    )

    # Render the view.
    return render(request, 'my_app/my_view.html', context=context)
```

and an example of template for the view above:
```djangotemplate
{% qr_from_text "Hello World!" options=my_options %}
```

### Generating URLs to QR Code Images (qr_url_from_text)
The **`qr_url_from_text`** tag generates an url to an image representing the QR code. It comes with the same options as `qr_from_text` to customize the image format (SVG or PNG), the size, the border, and the matrix size. It also has an additional option **`cache_enabled`** to disable caching of served image.

Here is a medium "hello world" QR code that uses a URL to serve the image in SVG format:

```djangotemplate
<img src="{% qr_url_from_text "Hello World!" %}" alt="Hello World!">
```

Here is a "hello world" QR code in version 10 that uses a URL to serve the image in PNG format:

```djangotemplate
<img src="{% qr_url_from_text "Hello World!" size=8 version=10 image_format='png' %}" alt="Hello World!">
```

The image targeted by the generated URL is served by a view provided in `qr_code.urls`. Therefore, you need to include the URLs provided by `qr_code.urls` in your app in order to make this tag work. This can be achieved with something like this:

```python
from django.conf.urls import include
from django.urls import path

urlpatterns = [
    path('qr_code/', include('qr_code.urls', namespace="qr_code")),
]
```

The QR code images are served via a URL named **`qr_code:serve_qr_code_image`**. You can customize the path under which the images are served (i.e. the path bound to the URL named `qr_code:serve_qr_code_image`) with the optional setting **`SERVE_QR_CODE_IMAGE_PATH`** which defaults to `images/serve-qr-code-image/`. Note that the trailing slash is mandatory and that defining this setting to an empty string leads to using the default value. The example below will serve any QR code image from `<base URL or your application>/qr-code-image/`:

```python
# In urls.py
from django.conf.urls import include
from django.urls import path

urlpatterns = [
    path('', include('qr_code.urls', namespace='qr_code')),
]

# In your settings
SERVE_QR_CODE_IMAGE_PATH = 'qr-code-image/'
```

### Generating Image Object Representing a QR Code

If you do not want to use Django tags for rendering QR code in a template, you can simply use the API in your code. For instance, `qr_code.qrcode.maker.make_qr_code_image` will return bytes representing an image according to the image_format passed in the `qr_code_options` parameter.

### Special encoding modes with qr_from_data and qr_url_from_data
The tags **`qr_from_data`** and  **`qr_url_from_data`** produce results similar to those of `qr_from_text` and `qr_url_from_text`, but they avoid converting everything to text (UTF-8 encoded by default, or any supported charset depending on `encoding` option).

The ISO/IEC 18004 standard defines four modes in order to encode the data as efficiently as possible.

#### Numeric mode
The numeric mode is the most efficient way to encode digits. This mode does not cover negative numbers because it does not support the minus sign (or plus sign).

The numeric mode is supported by QR Codes and Micro QR Codes. The encoding engine detects (Segno) the numeric mode if the data is provided as string (e.g. '54') or integer (e.g. 54) to `qr_from_data` or `qr_url_from_data`.

#### Alphanumeric mode
The alphanumeric mode extends the numeric mode by various characters. Namely, about the upper case letters ABCDEFGHIJKLMNOPQRSTUVWXYZ, a space character " " and other letters $%*+-./:.

#### Kanji mode
Kanji can be encoded compactly and efficiently and requires significantly less space than encoding the characters in UTF-8.

#### Byte mode
The byte mode covers all data which cannot be represented by the other modes. When the `encoding` option is set to `None`, the encoding engine (Segno) detects, according to ISO/IEC 18004, to encode the data with ISO 8859-1. In case the data cannot be represented by ISO 8859-1, UTF-8 is used as fallback.

NOTE: When using `qr_from_text` or `qr_url_from_text`, the byte mode with UTF-8 encoding is forced by default . You may use the `encoding` option to change this behavior. It appears to be one of the most portable way of encoding text for proper decoding among the readers.

#### Examples
The following renders a tiny numeric QR code containing the value `2021` with a `svg` tag:
```djangotemplate
{% qr_from_data 2021 size="T" %}
```

Here is a micro QR code with an `img` tag containing the value `2021`:
```djangotemplate
{% qr_from_data 2021 micro=True image_format="png" %}
```

### Caching Served Images

A large QR code (version 40) requires 0.2 second to be generated on a powerful machine (in 2018), and probably more than half a second on a really cheap hosting.

The image served by the *qr_code* app can be cached to improve performances and reduce CPU usage required to generate the QR codes. In order to activate caching, you simply need to declare a cache alias with the setting **`QR_CODE_CACHE_ALIAS`** to indicate in which cache to store the generated QR codes.

For instance, you may declare an additional cache for your QR codes like this in your Django settings:
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
    'qr-code': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'qr-code-cache',
        'TIMEOUT': 3600
    }
}

QR_CODE_CACHE_ALIAS = 'qr-code'
```

The `QR_CODE_CACHE_ALIAS = 'qr-code'` tells the *qr_code* app to use that cache for storing the generated QR codes. All QR codes will be cached with the specified *TIMEOUT* when a non-empty value is set to `QR_CODE_CACHE_ALIAS`.

If you want to activate the cache for QR codes, but skip the caching for some specific codes, you can use the keyword argument `cache_enabled=False` when using `qr_url_from_text`.

Here is a "hello world" QR code in version 20 with an error correction level Q (25% of redundant data) that uses a URL to serve the image in SVG format, and disable caching for served image:
```djangotemplate
<img src="{% qr_url_from_text "Hello World!" size=8 version=20 error_correction="Q" cache_enabled=False %}" alt="Hello World!">
```

### Protecting Access to QR Code Images

The default settings protect the URLs that serve QR code images against external requests, and thus against possibly easy (D)DoS attacks.

Here are the available settings to manage the protection for served images:
```python
from qr_code.qrcode import constants

QR_CODE_URL_PROTECTION = {
    constants.TOKEN_LENGTH: 30,                         # Optional random token length for URL protection. Defaults to 20.
    constants.SIGNING_KEY: 'my-secret-signing-key',     # Optional signing key for URL token. Uses SECRET_KEY if not defined.
    constants.SIGNING_SALT: 'my-signing-salt',          # Optional signing salt for URL token.
    constants.ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER: True  # Tells whether a registered user can request the QR code URLs from outside a site that uses this app. It can be a boolean value used for any user or a callable that takes a user as parameter. Defaults to False (nobody can access the URL without the signature token).
}
```

#### Signing Request URLs

By default, the application only serves QR code images for authenticated URLs (requests generated from your application and addressed to your application). The authentication uses a HMAC to sign the request query arguments. The authentication code is passed as a query argument named **`token`** which is automatically generated by `qr_url_from_text`  or `qr_url_from_data`. Whenever the signature is invalid, the application returns a *HTTP 403 Permission denied* response when processing the request for serving a QR code image.

This mechanism ensures that, by default, nobody can send external requests to your application to obtain custom QR codes for free. This is especially useful if you display QR code URLs on public pages (no user authentication).

The `token` query argument is not mandatory and, when a request reaches the `qr_code:serve_qr_code_image` URL without that token, the protection mechanism falls back to the user authentication mechanism (see chapter below).

It is possible to explicitly remove the  signature token that protects a specific URL with the parameter **`url_signature_enabled=False`**. Here is a "hello world" QR code that uses a URL to serve the image in SVG format without the `token` query argument :

```djangotemplate
<img src="{% qr_url_from_text "Hello World!" url_signature_enabled=False %}" alt="Hello World!">
```

The `token` parameter will not be part of the query string of the generated URL, making possible to build a simpler, predictable URL. However, this will trigger the user authentication mechanism (see chapter below).

#### Handling User Authentication when Serving QR Code Images

If you are interested in providing the QR code images as a service, there is a setting named **`ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER`** to grant access to some controlled users. This setting tells who can bypass the url signature token (see chapter above). It can be a boolean value used for any authenticated user, or a callable that takes a user as only parameter.

Setting the `ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER` option to `True` tells the application to serve QR code images to authenticated users only. Hence, to grant access to any authenticated user to generated images, you can use this in your settings:

```python
from qr_code.qrcode import constants

QR_CODE_URL_PROTECTION = {
    constants.ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER: True
}
```

Setting the option `ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER` to a callable that always returns `True` (even for anonymous users) will allow anyone to access QR code image generation from outside your Django app. The following settings will grant access to anonymous users to generated images:

```python
from qr_code.qrcode import constants

QR_CODE_URL_PROTECTION = {
    constants.ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER: lambda u: True
}
```

Please note that, if your service is available on the Internet, allowing anyone to generate any kind of QR code via your Django application - as shown above - might generate a very heavy load on your server.

### QR Codes for Apps

Aside from generating a QR code from a given text, you can also generate codes for specific application purposes, that a reader can interpret as an action to take: open a mail client to send an e-mail to a given address, add a contact to your phone book, connect to a Wi-Fi, start a SMS, etc.  See [this documentation](https://github.com/zxing/zxing/wiki/Barcode-Contents) about what a QR code can encode.

Django QR Code proposes several utility tags to ease the generation of such codes, without having to build the appropriate text representation for each action you need. This remove the hassle of reading the specifications and handling all the required escaping for reserved chars.

Please note that some commands are common patterns, rather than formal specifications. Therefore, there is no guarantee that all QR code readers will handle them properly.

The following tags targeting apps are available:
* `qr_for_email` and `qr_url_for_email`
* `qr_for_tel` and `qr_url_for_tel`
* `qr_for_sms` and `qr_url_for_sms`
* `qr_for_geolocation` and `qr_url_for_geolocation`
* `qr_for_google_maps` and `qr_url_for_google_maps`
* `qr_for_youtube` and `qr_url_for_youtube`
* `qr_for_google_play` and `qr_url_for_google_play`
* `qr_for_mecard` and `qr_url_for_mecard`
* `qr_for_vcard` and `qr_url_for_vcard`
* `qr_for_wifi` and `qr_url_for_wifi`
* `qr_for_epc` and `qr_url_for_epc`
* `qr_for_event` and `qr_url_for_event`
* `qr_for_contact` and `qr_url_for_contact` (legacy, do not use in new projects)

You could write a view like this:

```python
import datetime
from datetime import date
from django.shortcuts import render
from qr_code.qrcode.utils import MeCard, VCard, EpcData, VEvent, EventClass, EventTransparency, EventStatus, WifiConfig, Coordinates, QRCodeOptions


def application_qr_code_demo(request):
    # Use a MeCard instance to encapsulate the detail of the contact.
    mecard_contact = MeCard(
        name='Doe, John',
        phone='+41769998877',
        email='j.doe@company.com',
        url='http://www.company.com',
        birthday=date(year=1985, month=10, day=2),
        memo='Development Manager',
        org='Company Ltd'
    )

    # Use a VCard instance to encapsulate the detail of the contact.
    vcard_contact = VCard(
        name='Doe; John',
        phone='+41769998877',
        email='j.doe@company.com',
        url='http://www.company.com',
        birthday=date(year=1985, month=10, day=2),
        street='Cras des Fourches 987',
        city='Delémont',
        zipcode=2800,
        region='Jura',
        country='Switzerland',
        memo='Development Manager',
        org='Company Ltd'
    )

    # Use a WifiConfig instance to encapsulate the configuration of the connexion.
    wifi_config = WifiConfig(
        ssid='my-wifi',
        authentication=WifiConfig.AUTHENTICATION.WPA,
        password='wifi-password'
    )

    # Use a EpcData instance to encapsulate the data of the European Payments Council Quick Response Code.
    epc_data = EpcData(
        name='Wikimedia Foerdergesellschaft',
        iban='DE33100205000001194700',
        amount=50.0,
        text='To Wikipedia'
    )

    # Build coordinates instances.
    google_maps_coordinates = Coordinates(latitude=586000.32, longitude=250954.19)
    geolocation_coordinates = Coordinates(latitude=586000.32, longitude=250954.19, altitude=500)

    # Build event data (VEVENT properties)
    # NB for start and end of event:
    #   - Naive date and time is rendered as floating time.
    #   - Aware date and time is rendered as UTC converted time.
    event = VEvent(
        uid="some-event-id",
        summary="Vacations",
        start=datetime.datetime(2022, 8, 6, hour=8, minute=30),
        end=datetime.datetime(2022, 8, 17, hour=12),
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

RSVP to team leader."""
    )
    
    # Build context for rendering QR codes.
    context = dict(
        mecard_contact=mecard_contact,
        vcard_contact=vcard_contact,
        wifi_config=wifi_config,
        epc_data=epc_data,
        event=event,
        video_id='J9go2nj6b3M',
        google_maps_coordinates=google_maps_coordinates,
        geolocation_coordinates=geolocation_coordinates,
        options_example=QRCodeOptions(size='t', border=6, error_correction='L'),
    )

    # Render the index page.
    return render(request, 'my_app/application_qr_code_demo.html', context=context)
```

Then, in your template, you can render the appropriate QR codes for the given context:
```djangotemplate
<h3>Add contact '{{ mecard_contact.name }}' to phone book</h3>
{% qr_for_mecard mecard=mecard_contact size='S' %}
<p>or:</p>
{% qr_for_contact mecard_contact size='S' %}
<p>or:</p>
{% qr_for_contact mecard_contact options=options_example %}

<h3>Add contact '{{ vcard_contact.name }}' to phone book</h3>
{% qr_for_vcard vcard=vcard_contact size='S' %}
<p>or:</p>
{% qr_for_contact vcard_contact size='S' %}
<p>or:</p>
{% qr_for_contact vcard_contact options=options_example %}

<h3>Configure Wi-Fi connexion to '{{ wifi_config.ssid }}'</h3>
<img src="{% qr_url_for_wifi wifi_config=wifi_config size='T' error_correction='Q' %}">
<p>or:</p>
<img src="{% qr_url_for_wifi wifi_config size='T' error_correction='Q' %}">
<p>or:</p>
<img src="{% qr_url_for_wifi wifi_config options=options_example %}">

<h3>EPC QR Code'</h3>
<img src="{% qr_url_for_epc epc_data=epc_data %}">
<p>or:</p>
<img src="{% qr_url_for_epc epc_data size='H' %}">

<h3>Event QR Code'</h3>
<img src="{% qr_url_for_event event=event %}">
<p>or:</p>
{% qr_for_event event=event %}

<h3>Watch YouTube video '{{ video_id }}'</h3>
{% qr_for_youtube video_id image_format='png' size='T' %}
<p>or:</p>
{% qr_for_youtube video_id options=options_example %}

<h3>Open map at location: ({{ geolocation_coordinates }})</h3>
<img src="{% qr_url_for_geolocation coordinates=geolocation_coordinates %}">
<p>or:</p>
<img src="{% qr_url_for_geolocation latitude=geolocation_coordinates.latitude longitude=geolocation_coordinates.longitude altitude=geolocation_coordinates.altitude %}">
<p>or:</p>
<img src="{% qr_url_for_geolocation latitude=geolocation_coordinates.latitude longitude=geolocation_coordinates.longitude altitude=geolocation_coordinates.altitude options=options_example %}">

<h3>Open Google Maps App at location: ({{ google_maps_coordinates }})</h3>
{% qr_for_google_maps coordinates=google_maps_coordinates %}
<p>or:</p>
{% qr_for_google_maps latitude=google_maps_coordinates.latitude longitude=google_maps_coordinates.longitude %}
<p>or:</p>
{% qr_for_google_maps latitude=google_maps_coordinates.latitude longitude=google_maps_coordinates.longitude options=options_example %}
```

Please check out the [demo application](#demo-application) to see more examples.

## Notes

### Image Formats
The SVG is the default image format. It is a vector image format, so it can be scaled up and down without quality loss. However, it has two drawbacks. The size is not given in pixel, which can be problematic if the design of your website relies on a fixed width (in pixels). The format is less compact than PNG and results in a larger HTML content. Note that a base64 PNG is less compressible than a SVG tag, so it might not matter that much of you use HTML compression on your web server.

SVG has [broad support](http://caniuse.com/#feat=svg) now, and it will work properly on any modern web browser.

### qr_from_text vs qr_url_from_text
The tag `qr_url_from_text` has several advantages over `qr_from_text`, despite the fact that it requires a bit more of writing:
* the generated HTML code does not contain heavy inline image data (lighter and cleaner content)
* the generated images can be cached (served with a separate HTML request)
* the HTML tag used to render the QR code is always an `<img>` tag, which may simplify CSS handling.
* the HTML tag embedding the image is not generated for you, which allows for customization of attributes (*height*, *width*)
* the page can be loaded asynchronously, which improves responsiveness
* you can provide links to QR codes instead of displaying them, which is not possible with `qr_from_text`

One disadvantage of `qr_url_from_text` is that it increases the number of requests to the server: one request to serve the page containing the URL and another to request the image.

Be aware that serving image files (which are generated on the fly) from a URL can be abused and lead to (D)DoS attack pretty easily, for instance by requesting very large QR codes from outside your application. This is the reason why the associated setting `ALLOWS_EXTERNAL_REQUESTS_FOR_REGISTERED_USER` in `QR_CODE_URL_PROTECTION` defaults to completely forbid external access to the API. Be careful when opening external access.

### QR Codes Caching
Caching QR codes reduces CPU usage, but the usage of `qr_url_from_text` (which caching depends on) increases the number of requests to the server (one request to serve the page containing the URL and another to request the image).

Moreover, be aware that the largest QR codes, in version 40 with a border of 4 modules and rendered in SVG format, have a size of ~800 KB.
Be sure that your cache options are reasonable and can be supported by your server(s), especially for in-memory caching.

Note that even without caching the generated QR codes, the app will return an *HTTP 304 Not Modified* status code whenever the same QR code is requested again. The URL named **`qr_code:serve_qr_code_image`** adds the `ETag` and `Last-Modified` headers to the response if the headers aren't already set, enabling  *HTTP 304 Not Modified* response upon following requests.

## Demo Application
If you want to try this app, you may want to use the demo application shipped alongside the source code.

Get the source code from [GitHub](https://github.com/dprog-philippe-docourt/django-qr-code), follow the [installation instructions](#from-the-source-code) above, and run the `runserver` command of Django:
```bash
python manage.py runserver
```
The demo application should be running at <http://127.0.0.1:8000/qr-code-demo/>.

If you have [Docker Compose](https://docs.docker.com/compose/) installed, you can simply run the following from a terminal (this will save you the burden of setting up a proper python environment):
```bash
cd scripts
./run-demo-app.sh
```
The demo application should be running at <http://127.0.0.1:8910/qr-code-demo/>.

## Testing
Get the source code from [GitHub](https://github.com/dprog-philippe-docourt/django-qr-code), follow the [installation instructions](#from-the-source-code) above, and run the `test` command of Django:
```bash
python manage.py test
```
This will run the test suite with the locally installed version of Python and Django.

If you have [Docker Compose](https://docs.docker.com/compose/) installed, you can simply run the following from a terminal (this will save you the burden of setting up a proper python environment):
```bash
cd scripts
./run-tests.sh
```
This will run the test suite with all supported versions of Python and Django. The test results are stored within `tests_result` folder.

## Projects Using this App

This app is used in the following projects:
* [MyGym Web](https://mygym-web.ch/): a web platform for managing sports clubs. The QR codes are used for importing members' contact information in a phone book.
* [Gymna-Score](https://gymna-score.acjg.ch/): a web platform for entering scores during gymnastics competitions organized by the Association Cantonale Jurassienne de Gymnastique (ACJG). The QR codes are used to provide an easy way for the public to follow an ongoing competition. They are also used to authenticate judges that need to enter scores.
* [AC-Ju](https://www.ac-ju.ch/): a website that generates digital vouchers that can be redeemed at affiliate merchants.
