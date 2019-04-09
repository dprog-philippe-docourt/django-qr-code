"""Tags for Django template system that help generating QR codes."""

from django import template

from qr_code.qrcode.maker import make_qr_code_with_args, make_qr_code_url_with_args
from qr_code.qrcode.utils import make_email_text, make_google_play_text, make_tel_text, make_sms_text, \
    make_youtube_text, WifiConfig, ContactDetail, Coordinates

register = template.Library()


def _make_contact_or_wifi_qr_code(contact_or_wifi, expected_cls, embedded, qr_code_args):
    if not isinstance(contact_or_wifi, expected_cls):
        # For compatibility with existing views and templates, try to build from dict.
        contact_or_wifi = expected_cls(**contact_or_wifi)
    if embedded:
        return make_qr_code_with_args(contact_or_wifi.make_qr_code_text(), qr_code_args=qr_code_args)
    else:
        return make_qr_code_url_with_args(contact_or_wifi.make_qr_code_text(), qr_code_args=qr_code_args)


def _make_google_maps_qr_code(embedded, **kwargs):
    if 'coordinates' in kwargs:
        coordinates = kwargs.pop('coordinates')
    else:
        coordinates = Coordinates(kwargs.pop('latitude'), kwargs.pop('longitude'))
    if embedded:
        return make_qr_code_with_args(coordinates.make_google_maps_text(), qr_code_args=kwargs)
    else:
        return make_qr_code_url_with_args(coordinates.make_google_maps_text(), qr_code_args=kwargs)


def _make_geolocation_qr_code(embedded, **kwargs):
    if 'coordinates' in kwargs:
        coordinates = kwargs.pop('coordinates')
    else:
        coordinates = Coordinates(kwargs.pop('latitude'), kwargs.pop('longitude'), kwargs.pop('altitude'))
    if embedded:
        return make_qr_code_with_args(coordinates.make_geolocation_text(), qr_code_args=kwargs)
    else:
        return make_qr_code_url_with_args(coordinates.make_geolocation_text(), qr_code_args=kwargs)


@register.simple_tag()
def qr_from_text(text, **kwargs):
    return make_qr_code_with_args(text, qr_code_args=kwargs)


@register.simple_tag()
def qr_for_email(email, **kwargs):
    return make_qr_code_with_args(make_email_text(email), qr_code_args=kwargs)


@register.simple_tag()
def qr_for_tel(phone_number, **kwargs):
    return make_qr_code_with_args(make_tel_text(phone_number), qr_code_args=kwargs)


@register.simple_tag()
def qr_for_sms(phone_number, **kwargs):
    return make_qr_code_with_args(make_sms_text(phone_number), qr_code_args=kwargs)


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
    return make_qr_code_with_args(make_youtube_text(video_id), qr_code_args=kwargs)


@register.simple_tag()
def qr_for_google_play(package_id, **kwargs):
    return make_qr_code_with_args(make_google_play_text(package_id), qr_code_args=kwargs)


@register.simple_tag()
def qr_for_contact(contact_detail, **kwargs):
    return _make_contact_or_wifi_qr_code(contact_detail, ContactDetail, embedded=True, qr_code_args=kwargs)


@register.simple_tag()
def qr_for_wifi(wifi_config, **kwargs):
    return _make_contact_or_wifi_qr_code(wifi_config, WifiConfig, embedded=True, qr_code_args=kwargs)


@register.simple_tag()
def qr_url_from_text(text, **kwargs):
    return make_qr_code_url_with_args(text, qr_code_args=kwargs)


@register.simple_tag()
def qr_url_for_email(email, **kwargs):
    return make_qr_code_url_with_args(make_email_text(email), qr_code_args=kwargs)


@register.simple_tag()
def qr_url_for_tel(phone_number, **kwargs):
    return make_qr_code_url_with_args(make_tel_text(phone_number), qr_code_args=kwargs)


@register.simple_tag()
def qr_url_for_sms(phone_number, **kwargs):
    return make_qr_code_url_with_args(make_sms_text(phone_number), qr_code_args=kwargs)


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
    return make_qr_code_url_with_args(make_youtube_text(video_id), qr_code_args=kwargs)


@register.simple_tag()
def qr_url_for_google_play(package_id, **kwargs):
    return make_qr_code_url_with_args(make_google_play_text(package_id), qr_code_args=kwargs)


@register.simple_tag()
def qr_url_for_contact(contact_detail, **kwargs):
    return _make_contact_or_wifi_qr_code(contact_detail, ContactDetail, embedded=False, qr_code_args=kwargs)


@register.simple_tag()
def qr_url_for_wifi(wifi_config, **kwargs):
    return _make_contact_or_wifi_qr_code(wifi_config, WifiConfig, embedded=False, qr_code_args=kwargs)
