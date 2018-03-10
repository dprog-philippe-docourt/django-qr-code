"""Tags for Django template system that help generating QR codes."""

from django import template

from qr_code.qr_code import make_embedded_qr_code, make_email_text, \
    make_google_maps_text, make_geolocation_text, make_google_play_text, make_tel_text, make_sms_text, \
    make_youtube_text, DEFAULT_CACHE_ENABLED, make_qr_code_url, QRCodeOptions

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


@register.simple_tag()
def qr_from_text(text, **kwargs):
    """Wrapper for function :func:`~qr_code.qr_code._make_qr_code`"""
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
def qr_for_geolocation(latitude, longitude, altitude, **kwargs):
    return _make_qr_code(make_geolocation_text(latitude, longitude, altitude), qr_code_args=kwargs, embedded=True)


@register.simple_tag()
def qr_for_google_maps(latitude, longitude, **kwargs):
    return _make_qr_code(make_google_maps_text(latitude=latitude, longitude=longitude), qr_code_args=kwargs,
                         embedded=True)


@register.simple_tag()
def qr_for_youtube(video_id, **kwargs):
    return _make_qr_code(make_youtube_text(video_id), qr_code_args=kwargs, embedded=True)


@register.simple_tag()
def qr_for_google_play(package_id, **kwargs):
    return _make_qr_code(make_google_play_text(package_id), qr_code_args=kwargs, embedded=True)


@register.simple_tag()
def qr_for_contact(contact_detail, **kwargs):
    return _make_qr_code(contact_detail.make_contact_text(), qr_code_args=kwargs, embedded=True)


@register.simple_tag()
def qr_for_wifi(wifi_config, **kwargs):
    return _make_qr_code(wifi_config.make_wifi_text(), qr_code_args=kwargs, embedded=True)


@register.simple_tag()
def qr_url_from_text(text, **kwargs):
    """Wrapper for function :func:`~qr_code.qr_code.make_qr_code_url`"""
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
def qr_url_for_geolocation(latitude, longitude, altitude, **kwargs):
    return _make_qr_code(make_geolocation_text(latitude=latitude, longitude=longitude, altitude=altitude),
                         qr_code_args=kwargs, embedded=False)


@register.simple_tag()
def qr_url_for_google_maps(latitude, longitude, **kwargs):
    return _make_qr_code(make_google_maps_text(latitude=latitude, longitude=longitude), qr_code_args=kwargs,
                         embedded=False)


@register.simple_tag()
def qr_url_for_youtube(video_id, **kwargs):
    return _make_qr_code(make_youtube_text(video_id), qr_code_args=kwargs, embedded=False)


@register.simple_tag()
def qr_url_for_google_play(package_id, **kwargs):
    return _make_qr_code(make_google_play_text(package_id), qr_code_args=kwargs, embedded=False)


@register.simple_tag()
def qr_url_for_contact(contact_detail, **kwargs):
    return _make_qr_code(contact_detail.make_contact_text(), qr_code_args=kwargs, embedded=False)


@register.simple_tag()
def qr_url_for_wifi(wifi_config, **kwargs):
    return _make_qr_code(wifi_config.make_wifi_text(), qr_code_args=kwargs, embedded=False)
