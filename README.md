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
```htmldjango
{% load qr_code %}
```

The source code on [GitHub](https://github.com/dprog-philippe-docourt/django-qr-code) contains a simple demo app. Please check out the [templates folder](https://github.com/dprog-philippe-docourt/django-qr-code/tree/master/qr_code_demo/templates/qr_code_demo) for an example of template, and the [setting](https://github.com/dprog-philippe-docourt/django-qr-code/tree/master/demo_site/settings.py) and [urls](https://github.com/dprog-philippe-docourt/django-qr-code/tree/master/demo_site/urls.py) files for an example of configuration and integration.

### Example: Inline QR Code

Generate a simple QR code:

```htmldjango
{% qr_from_text "Hello World!" size="T" %}
```
### Example: URL QR Code

Generate a URL for a QR code image:

```htmldjango
<img src="{% qr_url_from_text "Hello World!" %}" alt="Hello World!">
```

### Advanced Usage of Tags

Refer to the [official documentation for tags](https://django-qr-code.readthedocs.io/latest/pages/template-tags.html) for more detailed information and advanced usage examples.

### Demo Application
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

## Generating Image Object Representing a QR Code

If you do not want to use Django tags for rendering QR code in a template, you can simply use the API in your code. For instance, `qr_code.qrcode.maker.make_qr_code_image` will return bytes representing an image according to the image_format passed in the `qr_code_options` parameter.

Refer to the [official API documentation](https://django-qr-code.readthedocs.io/latest/pages/api.html) for more detailed information.

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
