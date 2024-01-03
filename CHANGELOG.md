# Change Log

# 4.0.0 (2024-01-03)
* Upgrade dependencies, and drop support for Pydantic <2.5, Django<4.2
* Add support for Python 3.12
* Add support for Django 5.0.
* Introduce support for floating point size QR code modules.
* Introduce embedded Base64 SVG image.
* Behavior change: white background is no longer interpreted as transparent for SVG output (#41). If you want to avoid path fill of SVG to reduce the size of the SVG image, you have to explicitly set `light_color` to `None` in `QRCodeOptions`.

## 3.1.2 (2023-04-10)
* Fix bug in `WifiConfig` data class (#43).
* Fix typo in documentation (#45)
* Add support for Django 4.1 and Django 4.2.
* Add support for Python 3.11.

## 3.1.1 (2022-07-28)
* Fix regression in demo site due to improper runtime type validation on `QRCodeOptions`.
* Minor improvements to documentation.
* Modernize code syntax for Python >= 3.7.

## 3.1.0 (2022-06-26)
* Add support for more properties for vCard: cellphone (TEL;TYPE=CELL), homephone (TEL;TYPE=HOME), workphone (TEL;TYPE=WORK)
* Add support for simple iCalendar event (VEVENT). (#38)
* Add support for Django 4.0.
* BREAKING CHANGES:
  * Introduce type validation at runtime with pydantic. Existing code might need some type-related fixes.
  * Drop support for Django 2.2.

## 3.0.0 (2021-11-27)
* Add support for European Payments Council Quick Response Code (EPC QR Code) version 002.
* Add support for vCard v3 QR code.
* Revamp support for MeCARD QR code to provide a cleaner API (old API remains available for compatibility).
* Introduce `qr_from_data` and `qr_url_from_data` to allow optimized encoding of alphanumeric, numeric, and byte data (adopt appropriate encoding mode depending on data content).
* Introduce support for `boost_error` flag.
* Introduce support for `encoding` parameter.
* Several breaking changes in API and generated QR codes:
  * `text` parameters renamed to `data`;
  * class methods `make_qr_text` renamed to `make_qr_data`;
  * uses UTF-8 encoding by default for application and text QR codes (you must set the new `encoding` option or use the new `qr_from_data` and `qr_url_from_data` template tags to emulate old behavior);
  * encoded geolocations always contain a decimal separator.
* Improve API documentation.
* Add support for Python 3.10
* Drop support for Python 3.6.
* Drop support for Django 3.1.

## 2.3.0 (2021-11-07)
* Add support for `ECI mode` to control bytes encoding.
* Fix handling of `micro` QR code option when using URLs to serve image via `{% qr_url_from_text %}`.
* Fix handling of `cache_enabled` option when using URLs to serve image via `{% qr_url_from_text %}`.
* Fix handling of `url_signature_enabled` option when using URLs to serve image via `{% qr_url_from_text %}`.

## 2.2.0 (2021-06-03)
* Change encoding from URL-safe Base64 to standard Base64 for `text` query argument (used for serving QR code images).
* Fix #31 by passing the border parameter for segno.QRCode.save.
* Ensure compatibility with Django 3.2.
* Drop support for Django 3.0.

## 2.1.0 (2021-01-23)
* Change encoding from URL-safe Base64 to standard Base64 for `text` query argument (used for serving QR code images).
* Introduce setting `SERVE_QR_CODE_IMAGE_PATH` to configure the path under which QR Code images are served.
* Reorganize and improve documentation.
* Fix #23
* Introduce usage of type hints.

## 2.0.1 (2020-11-24)
* Update the install_requires after the move from qrcode to Segno.

## 2.0.0 (2020-11-22)
* Remove dependency to Pillow / qrcode
* Switch to [Segno](https://pypi.org/project/segno/) for generating QR Codes
* Add support for QR Codes with multiple colors
* Add support for Micro QR Codes
* Stable SVG format for QR code between 32-bit and 64-bit architecture (#19)
* Use hyphens in URLs (#16)
* Add support for Python 3.9

## 1.3.1 (2020-09-07)
* Fix local testing script.
* Fix date of release 1.3.0 in readme. 
* Code cleanup.

## 1.3.0 (2020-09-05)
* Drop support for Django 2.1.
* Ensure compatibility with Django 3.1.

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
* Add documentation about what a QR code can encode.

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
    * Add documentation for new features
    * Add tests for new features
    * Add examples to demo site
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
* Add support for PNG image format via an `img` tag.
* Add documentation for users and developers.
* Improve examples in demo app.

## 0.1.1 (2017-08-02)
First public release.
