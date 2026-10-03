# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`django-qr-code` is a reusable Django app (package `qr_code`) that renders QR codes in templates, built on the Segno library, with Pydantic for runtime argument validation. It uses no models/database. Supported: Python >= 3.10, Django >= 5.2 (LTS). The version lives in `qr_code/__init__.py` (`__version__`) and is read by `setup.py` without importing.

The repo root is also a runnable Django project used for tests and the demo: `demo_site/` (settings, URLs) + `qr_code_demo/` (demo app and template). `manage.py` uses `demo_site.settings`.

## Commands

```bash
pip install -r requirements.txt -r requirements-dev.txt
python manage.py collectstatic --no-input      # needed before running tests

python manage.py test                                              # full suite
python manage.py test qr_code.tests.test_qr_from_text              # one module
python manage.py test qr_code.tests.tests.TestQRCodeOptions        # one class
python manage.py test qr_code.tests.tests.TestQRCodeOptions.test_qr_code_options  # one test

mypy qr_code                                   # type checking (run in CI)
python manage.py runserver                     # demo at http://127.0.0.1:8000/qr-code-demo/
```

- `scripts/run-tests.sh` (what CI runs) uses Docker Compose to run the suite (`python -Wd manage.py test`) plus `mypy qr_code` across the Python 3.10–3.13 × Django 5.2 matrix; logs go to `tests_result/`.
- `scripts/run-demo-app.sh` serves the demo via Docker/gunicorn on port 8910.
- `scripts/generate-pypi-release.sh` builds and uploads to PyPI — do not run without being asked.
- Docs: Sphinx in `docs/` (`cd docs && make html`); `docs/conf.py` calls `django.setup()` with demo settings and symlinks root `README.md` / `CHANGELOG.md` into `docs/pages/`.

Language: everything written to this repo — code, identifiers, comments, docstrings, documentation and commit messages — must be in English, even when the conversation with the user is in another language.

Style: 4-space indent (2 for HTML) per `.editorconfig`; long lines (~140 chars) are common in the existing code.

## Architecture

Layered, from template tag down to Segno:

1. **`qr_code/templatetags/qr_code.py`** — every public tag comes in two flavours: `qr_*` (embedded `<svg>`/`<img>` markup) and `qr_url_*` (URL to the serving view). Application-specific tags (`qr_for_email`, `qr_for_contact`, `qr_for_wifi`, `qr_for_event`, …) accept either a data object or kwargs to build one (`_make_app_qr_code_from_obj_or_kwargs`), convert it to a string via the object's `make_qr_code_data()`, then delegate to the maker. Adding a new app-specific QR type means adding both a `qr_for_*` and a `qr_url_for_*` tag.
2. **`qr_code/qrcode/utils.py`** — `QRCodeOptions` (all rendering options, validated with `@validate_call`; also builds the Segno kwargs and color mapping) and the payload dataclasses (`VCard`, `MeCard`, `ContactDetail`, `WifiConfig`, `EpcData`, `VEvent`, `Email`, `Coordinates`, plus `make_*_text` helpers). Template tag kwargs arrive as strings, so `maker._options_from_args` converts `"None"` → `None`, and tags accept an `options=QRCodeOptions(...)` object as an alternative to individual kwargs.
3. **`qr_code/qrcode/maker.py`** — public Python API: `make_qr`, `make_qr_code_image` (raw bytes), `make_embedded_qr_code` (HTML markup), `get_or_make_cached_embedded_qr_code` (requires `QR_CODE_CACHE_ALIAS`), and the `*_with_args` adapters used by tags.
4. **`qr_code/qrcode/serve.py` + `qr_code/views.py` + `qr_code/urls.py`** — URL-based serving. `make_qr_code_url` encodes data as base64 `text`/`bytes` or `int` query params, only adds non-default options, and appends an HMAC-signed `token` (URL protection). `serve_qr_code_image` decodes the request back into `QRCodeOptions`, enforces the token / `QR_CODE_URL_PROTECTION` rules (incl. external requests for authenticated users), and is wrapped by ETag/Last-Modified handling and optional per-user page caching. Booleans in the query string are `1`/`0`.

Relevant Django settings (see `demo_site/settings.py` for an example): `QR_CODE_CACHE_ALIAS`, `QR_CODE_URL_PROTECTION`, `SERVE_QR_CODE_IMAGE_PATH`.

**`constants.QR_CODE_GENERATION_VERSION_DATE`** feeds the ETag and Last-Modified of served images; bump it whenever the generated output changes so clients/caches invalidate.

## Tests

Tests in `qr_code/tests/` are `SimpleTestCase`s that compare generated output against reference images in `qr_code/tests/resources/*.ref.svg` / `*.ref.png`. When output legitimately changes, set `REFRESH_REFERENCE_IMAGES = True` in `qr_code/tests/__init__.py`, run the suite once to rewrite the references, then set it back to `False`. Tests that exercise caching use `override_settings(CACHES=OVERRIDE_CACHES_SETTING)` from the same module.

User-visible changes are recorded in `CHANGELOG.md`.
