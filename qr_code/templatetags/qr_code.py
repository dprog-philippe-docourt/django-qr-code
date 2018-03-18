"""Tags for Django template system that help generating QR codes."""

from django import template

from qr_code.qrcode.maker import make_embedded_qr_code
from qr_code.qrcode.constants import DEFAULT_CACHE_ENABLED
from qr_code.qrcode.serve import make_qr_code_url
from qr_code.qrcode.utils import QRCodeOptions, make_email_text, make_google_play_text, make_tel_text, make_sms_text, \
    make_youtube_text, WifiConfig, ContactDetail, Coordinates

register = template.Library()


def _make_qr_code(text, qr_code_args, embedded):
    cache_enabled = DEFAULT_CACHE_ENABLED
    if 'cache_enabled' in qr_code_args:
        cache_enabled = qr_code_args.pop('cache_enabled')

    options = QRCodeOptions(**qr_code_args)
    if embedded:
        return make_embedded_qr_code(text, options)
    else:
        return make_qr_code_url(text, options, cache_enabled=cache_enabled)


def make_contact_or_wifi_qr_code(contact_or_wifi, expected_cls, embedded, qr_code_args):
    if not isinstance(contact_or_wifi, expected_cls):
        # For compatibility with existing views and templates, try to build from dict.
        contact_or_wifi = expected_cls(**contact_or_wifi)
    return _make_qr_code(contact_or_wifi.make_qr_code_text(), qr_code_args=qr_code_args, embedded=embedded)


def _make_google_maps_qr_code(embedded, **kwargs):
    if 'coordinates' in kwargs:
        coordinates = kwargs.pop('coordinates')
    else:
        coordinates = Coordinates(kwargs.pop('latitude'), kwargs.pop('longitude'))
    return _make_qr_code(coordinates.make_google_maps_text(), qr_code_args=kwargs, embedded=embedded)


def _make_geolocation_qr_code(embedded, **kwargs):
    if 'coordinates' in kwargs:
        coordinates = kwargs.pop('coordinates')
    else:
        coordinates = Coordinates(kwargs.pop('latitude'), kwargs.pop('longitude'), kwargs.pop('altitude'))
    return _make_qr_code(coordinates.make_geolocation_text(), qr_code_args=kwargs, embedded=embedded)


@register.simple_tag()
def qr_from_text(text, **kwargs):
    return _make_qr_code(text, qr_code_args=kwargs, embedded=True)


@register.simple_tag()
def qr_for_email(email, **kwargs):
    return _make_qr_code(make_email_text(email), qr_code_args=kwargs, embedded=True)


@register.simple_tag()
def qr_for_tel(phone_number, **kwargs):
    return _make_qr_code(make_tel_text(phone_number), qr_code_args=kwargs, embedded=True)


@register.simple_tag()
def qr_for_sms(phone_number, **kwargs):
    return _make_qr_code(make_sms_text(phone_number), qr_code_args=kwargs, embedded=True)


@register.simple_tag()
def qr_for_geolocation(**kwargs):
    """Accepts a *'coordinates'* keyword argument or a triplet *'latitude'*, *'longitude'*, and *'altitude'*."""
    return _make_geolocation_qr_code(embedded=True, **kwargs)


@register.simple_tag()
def qr_for_google_maps(**kwargs):
    """Accepts a *'coordinates'* keyword argument or a pair *'latitude'* and *'longitude'*."""
    return _make_google_maps_qr_code(embedded=True, **kwargs)


@register.simple_tag()
def qr_for_youtube(video_id, **kwargs):
    return _make_qr_code(make_youtube_text(video_id), qr_code_args=kwargs, embedded=True)


@register.simple_tag()
def qr_for_google_play(package_id, **kwargs):
    return _make_qr_code(make_google_play_text(package_id), qr_code_args=kwargs, embedded=True)


@register.simple_tag()
def qr_for_contact(contact_detail, **kwargs):
    return make_contact_or_wifi_qr_code(contact_detail, ContactDetail, qr_code_args=kwargs, embedded=True)


@register.simple_tag()
def qr_for_wifi(wifi_config, **kwargs):
    return make_contact_or_wifi_qr_code(wifi_config, WifiConfig, qr_code_args=kwargs, embedded=True)


@register.simple_tag()
def qr_url_from_text(text, **kwargs):
    return _make_qr_code(text, qr_code_args=kwargs, embedded=False)


@register.simple_tag()
def qr_url_for_email(email, **kwargs):
    return _make_qr_code(make_email_text(email), qr_code_args=kwargs, embedded=False)


@register.simple_tag()
def qr_url_for_tel(phone_number, **kwargs):
    return _make_qr_code(make_tel_text(phone_number), qr_code_args=kwargs, embedded=False)


@register.simple_tag()
def qr_url_for_sms(phone_number, **kwargs):
    return _make_qr_code(make_sms_text(phone_number), qr_code_args=kwargs, embedded=False)


@register.simple_tag()
def qr_url_for_geolocation(**kwargs):
    """Accepts a *'coordinates'* keyword argument or a triplet *'latitude'*, *'longitude'*, and *'altitude'*."""
    return _make_geolocation_qr_code(embedded=False, **kwargs)


@register.simple_tag()
def qr_url_for_google_maps(**kwargs):
    """Accepts a *'coordinates'* keyword argument or a pair *'latitude'* and *'longitude'*."""
    return _make_google_maps_qr_code(embedded=False, **kwargs)


@register.simple_tag()
def qr_url_for_youtube(video_id, **kwargs):
    return _make_qr_code(make_youtube_text(video_id), qr_code_args=kwargs, embedded=False)


@register.simple_tag()
def qr_url_for_google_play(package_id, **kwargs):
    return _make_qr_code(make_google_play_text(package_id), qr_code_args=kwargs, embedded=False)


@register.simple_tag()
def qr_url_for_contact(contact_detail, **kwargs):
    return make_contact_or_wifi_qr_code(contact_detail, ContactDetail, qr_code_args=kwargs, embedded=False)


@register.simple_tag()
def qr_url_for_wifi(wifi_config, **kwargs):
    return make_contact_or_wifi_qr_code(wifi_config, WifiConfig, qr_code_args=kwargs, embedded=False)
