# Django QR code
This is an application that provides tools for displaying QR codes on your Django site.

This application depends on the [qrcode](https://github.com/lincolnloop/python-qrcode) python library.

Only Python 3 is supported.

# Install
```bash
pip install django-qr-code
```

# Usage

The tag `qr_from_text` generates an embedded SVG tag within the HTML code of your template.

The following renders a tiny "hello world" QR code:
```djangotemplate
{% qr_from_text "Hello World!" size="T" %}
```
Here is a medium "hello world" QR code:
```djangotemplate
{% qr_from_text "Hello World!" size="m" %}
```

The size of the QR code can be either a positive integer or one of the following letters:
* t or T: tiny (value: 6)
* s or S: small (value: 12)
* m or M: medium (value: 18)
* l or L: large (value: 30)
* h or H: huge (value: 48)

Here is "hello world" QR code using the version 12:
```djangotemplate
{% qr_from_text "Hello World!" size=8 version=12 %}
```
The version parameter is an integer from 1 to 40 that controls the size of the QR Code. Set to None to determine this automatically. The smallest, version 1, is a 21 x 21 matrix. The biggest, version 40, is 177 x 177 matrix. The size grows by 4 boxes/side.

Here is "hello world" QR code using a border of 6 boxes:
```djangotemplate
{% qr_from_text "Hello World!" size=10 border=6 %}
```
The border parameter controls how many boxes thick the border should be (the default is 4, which is the minimum according to the specs).

The source code on [GitHub](https://github.com/dprog-philippe-docourt/django-qr-code) contains a simple demo app. Please check out the templates folder (in qr_code_demo/templates/qr_code_demo) for examples.
