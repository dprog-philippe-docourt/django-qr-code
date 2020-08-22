# Change Log

## x.y.z (yyyy-mm-dd)
* Removed dependency on Pillow / qrcode
* Switched to [Segno](https://pypi.org/project/segno/) for generating QR Codes
* Added support for QR Codes with multiple colors
* Added support for Micro QR Codes

## 1.2.0 (2020-04-26)
* Ensure compatibility with Django 3.0.
* Upgrade Pillow requirement to 7.1.
* Drop support for Python 3.5.
* Drop support for Django <2.2.
* More modern build environment and configuration for ReadTheDocs.

## 1.1.0 (2019-11-16)
* Ensure compatibility with Django 2.1.
* Ensure compatibility with Django 2.2.
* Upgrade qr_code library from 5.3 to 6.1 (several fixes).
* Drop support for Python 3.4.
* Fixed error when generating qr code from lazy text. (#1)
* Add support for customizing usage of URL signature token via template tags (allows to generate URLs for serving QR code images that do not include a signature token). (#4)
* The caching of QR codes images could allow to bypass checking the user when external access is active.
* Upgrade Pillow requirement to 6.2.0 (CVE-2019-16865).
* Adopt a dedicated logger, and move message "Pillow is not installed. No support available for PNG format." from info to debug. (#6)

## 1.0.0 (2018-03-23)
* BREAKING CHANGES:
    * QR code options have been factorized and now use the `QRCodeOptions` class.
    * The context for rendering a QR code encoding a Wi-Fi configuration uses the dedicated `WifiConfig` class.
    * The context for rendering a QR code encoding a contact detail uses the dedicated `ContactDetail` class.
    * `qr_for_contact` and `qr_url_for_contact` keyword arg has been renamed from `contact_dict` to `contact_detail`.
    * `qr_for_wifi` and `qr_url_for_wifi` keyword arg has been renamed from `wifi_dict` to `wifi_config`.
    * Reorganize code and split qr_code.py into several modules.

The changes mentioned above might break the compatibility with code using qr_code.py's API directly, but template tags are not impacted, except for `qr_for_contact`, `qr_url_for_contact`, `qr_for_wifi`, and `qr_url_for_wifi` if they were using a keyword argument.
* Other changes:
    * Added support for `error_correction` parameter when generating a QR code.
    * Added support for `coordinates` keyword argument to `qr_for_geolocation`, `qr_for_google_maps`, `qr_url_for_geolocation`, and `qr_url_for_google_maps`.
    * Additions to documentation.
    * Added ability to use a `QRCodeOptions` instance with `options` keyword argument in all tags.
* Bug fixes:
    * Fixed non-closed <img> tag when generating embedded PNG image.
    * Escape colon char (':') if it appears within a contact detail or a wifi configuration.
    * Add a second terminal semi-colon at the end of the text representing a wifi configuration, as recommended in some sources.

## 0.4.1 (2018-03-10)
* Fixed unescaped chars when generating QR code for a contact.
* Simplify handling of default values for QR code options.
* Added documentation about what a QR code can encode.

## 0.4.0 (2018-03-09)
* Added support for multiple new tags:
    * `qr_for_email` and `qr_url_for_email`
    * `qr_for_tel` and `qr_url_for_tel`
    * `qr_for_sms` and `qr_url_for_sms`
    * `qr_for_geolocation` and `qr_url_for_geolocation`
    * `qr_for_google_maps` and `qr_url_for_google_maps`
    * `qr_for_youtube` and `qr_url_for_youtube`
    * `qr_for_google_play` and `qr_url_for_google_play`
    * `qr_for_contact` and `qr_url_for_contact`
    * `qr_for_wifi` and `qr_url_for_wifi`
* Reformat documentation on the demo site for better readability.
* Drop support for Django <1.11.

## 0.3.3 (2017-08-16)
* Added `app_name` namespace to `qr_code.urls` (better compatibility with `include()` function provided with Django >= 1.9).
* Update documentation regarding the inclusion of `qr_code.urls` for distinct versions of Django.
* Minor improvements to the documentation.

## 0.3.2 (2017-08-13)
* Allows optional installation of Pillow (PNG format unavailable, fallback to SVG).
* Fixed caching of images (not working due protection against external queries).
* Fixed conditional view processing (HTTP 304) for rendered QR codes (not working due protection against external queries).

## 0.3.1 (2017-08-12)
* Added a mention about Pillow library requirement in documentation.
* Minor improvements to the documentation and the demo application.

## 0.3.0 (2017-08-12)
* Added new tag qr_url_from_text:
    * Separate image from the page displaying the image
    * Handle caching of images
    * Conditional view processing (HTTP 304) for rendered QR codes
    * Protection against external requests
    * Settings to configure URLs accesses as a service for generating QR code images
    * Added documentation for new features
    * Added tests for new features
    * Added examples to demo site
* More robust testing of make_embedded_qr_code's arguments.
* Improved documentation.
* Demo site is compatible with Django 1.8.
* Added support for Docker Compose for running the demo application and running the tests.

## 0.2.1 (2017-08-05)
* Added support for Django 1.8.
* Fixed version specifiers for Django requirement so that it wont force the installation of Django 1.11.
* Added badges for PyPi, Read the Docs and Travis CI to readme file.
* Several additions to the documentation.

## 0.2.0 (2017-08-04)
* Added support for PNG image format via an `img` tag.
* Added documentation for users and developers.
* Improved examples in demo app.

## 0.1.1 (2017-08-02)
First public release.