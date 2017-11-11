"""Tags for Django template system that help generating QR codes."""

from django import template

from qr_code.qr_code import make_embedded_qr_code, make_contact_text, make_wifi_text, make_email_text, make_geo_text, make_mms_text, make_google_play_text, make_tel_text, make_sms_text, make_youtube_text, DEFAULT_MODULE_SIZE, DEFAULT_BORDER_SIZE, DEFAULT_VERSION, \
    DEFAULT_IMAGE_FORMAT, DEFAULT_CACHE_ENABLED, make_qr_code_url

register = template.Library()


@register.simple_tag()
def qr_from_text(text, size=DEFAULT_MODULE_SIZE, border=DEFAULT_BORDER_SIZE, version=DEFAULT_VERSION, image_format=DEFAULT_IMAGE_FORMAT):
    return make_embedded_qr_code(text, size=size, border=border, version=version, image_format=image_format)


@register.simple_tag()
def qr_for_email(email, size=DEFAULT_MODULE_SIZE, border=DEFAULT_BORDER_SIZE, version=DEFAULT_VERSION, image_format=DEFAULT_IMAGE_FORMAT):
    return make_embedded_qr_code(make_email_text(email), size=size, border=border, version=version, image_format=image_format)


@register.simple_tag()
def qr_for_tel(phone_number, size=DEFAULT_MODULE_SIZE, border=DEFAULT_BORDER_SIZE, version=DEFAULT_VERSION, image_format=DEFAULT_IMAGE_FORMAT):
    return make_embedded_qr_code(make_tel_text(phone_number), size=size, border=border, version=version, image_format=image_format)


@register.simple_tag()
def qr_for_sms(phone_number, size=DEFAULT_MODULE_SIZE, border=DEFAULT_BORDER_SIZE, version=DEFAULT_VERSION, image_format=DEFAULT_IMAGE_FORMAT):
    return make_embedded_qr_code(make_sms_text(phone_number), size=size, border=border, version=version, image_format=image_format)


@register.simple_tag()
def qr_for_mms(phone_number, size=DEFAULT_MODULE_SIZE, border=DEFAULT_BORDER_SIZE, version=DEFAULT_VERSION, image_format=DEFAULT_IMAGE_FORMAT):
    return make_embedded_qr_code(make_mms_text(phone_number), size=size, border=border, version=version, image_format=image_format)


@register.simple_tag()
def qr_for_geo(latitude, longitude, altitude, size=DEFAULT_MODULE_SIZE, border=DEFAULT_BORDER_SIZE, version=DEFAULT_VERSION, image_format=DEFAULT_IMAGE_FORMAT):
    return make_embedded_qr_code(make_geo_text(latitude=latitude, longitude=longitude, altitude=altitude), size=size, border=border, version=version, image_format=image_format)


@register.simple_tag()
def qr_for_youtube(video_id, size=DEFAULT_MODULE_SIZE, border=DEFAULT_BORDER_SIZE, version=DEFAULT_VERSION, image_format=DEFAULT_IMAGE_FORMAT):
    return make_embedded_qr_code(make_youtube_text(video_id), size=size, border=border, version=version, image_format=image_format)


@register.simple_tag()
def qr_for_google_play(package_id, size=DEFAULT_MODULE_SIZE, border=DEFAULT_BORDER_SIZE, version=DEFAULT_VERSION, image_format=DEFAULT_IMAGE_FORMAT):
    return make_embedded_qr_code(make_google_play_text(package_id), size=size, border=border, version=version, image_format=image_format)


@register.simple_tag()
def qr_for_contact(contact_dict, size=DEFAULT_MODULE_SIZE, border=DEFAULT_BORDER_SIZE, version=DEFAULT_VERSION, image_format=DEFAULT_IMAGE_FORMAT):
    contact_as_mecard = make_contact_text(contact_dict=contact_dict)
    return make_embedded_qr_code(contact_as_mecard, size=size, border=border, version=version, image_format=image_format)


@register.simple_tag()
def qr_for_wifi(wifi_dict, size=DEFAULT_MODULE_SIZE, border=DEFAULT_BORDER_SIZE, version=DEFAULT_VERSION, image_format=DEFAULT_IMAGE_FORMAT):
    wifi_config = make_wifi_text(wifi_dict=wifi_dict)
    return make_embedded_qr_code(wifi_config, size=size, border=border, version=version, image_format=image_format)


@register.simple_tag()
def qr_url_from_text(text, size=DEFAULT_MODULE_SIZE, border=DEFAULT_BORDER_SIZE, version=DEFAULT_VERSION, image_format=DEFAULT_IMAGE_FORMAT, cache_enabled=DEFAULT_CACHE_ENABLED):
    """Wrapper for function :func:`~qr_code.qr_code.make_qr_code_url`"""
    return make_qr_code_url(text, size=size, border=border, version=version, image_format=image_format, cache_enabled=cache_enabled)


@register.simple_tag()
def qr_url_for_email(email, size=DEFAULT_MODULE_SIZE, border=DEFAULT_BORDER_SIZE, version=DEFAULT_VERSION, image_format=DEFAULT_IMAGE_FORMAT):
    return make_qr_code_url(make_email_text(email), size=size, border=border, version=version, image_format=image_format)


@register.simple_tag()
def qr_url_for_tel(phone_number, size=DEFAULT_MODULE_SIZE, border=DEFAULT_BORDER_SIZE, version=DEFAULT_VERSION, image_format=DEFAULT_IMAGE_FORMAT):
    return make_qr_code_url(make_tel_text(phone_number), size=size, border=border, version=version, image_format=image_format)


@register.simple_tag()
def qr_url_for_sms(phone_number, size=DEFAULT_MODULE_SIZE, border=DEFAULT_BORDER_SIZE, version=DEFAULT_VERSION, image_format=DEFAULT_IMAGE_FORMAT):
    return make_qr_code_url(make_sms_text(phone_number), size=size, border=border, version=version, image_format=image_format)


@register.simple_tag()
def qr_url_for_mms(phone_number, size=DEFAULT_MODULE_SIZE, border=DEFAULT_BORDER_SIZE, version=DEFAULT_VERSION, image_format=DEFAULT_IMAGE_FORMAT):
    return make_qr_code_url(make_mms_text(phone_number), size=size, border=border, version=version, image_format=image_format)


@register.simple_tag()
def qr_url_for_geo(latitude, longitude, altitude, size=DEFAULT_MODULE_SIZE, border=DEFAULT_BORDER_SIZE, version=DEFAULT_VERSION, image_format=DEFAULT_IMAGE_FORMAT):
    return make_qr_code_url(make_geo_text(latitude=latitude, longitude=longitude, altitude=altitude), size=size, border=border, version=version, image_format=image_format)


@register.simple_tag()
def qr_url_for_youtube(video_id, size=DEFAULT_MODULE_SIZE, border=DEFAULT_BORDER_SIZE, version=DEFAULT_VERSION, image_format=DEFAULT_IMAGE_FORMAT):
    return make_qr_code_url(make_youtube_text(video_id), size=size, border=border, version=version, image_format=image_format)


@register.simple_tag()
def qr_url_for_google_play(package_id, size=DEFAULT_MODULE_SIZE, border=DEFAULT_BORDER_SIZE, version=DEFAULT_VERSION, image_format=DEFAULT_IMAGE_FORMAT):
    return make_qr_code_url(make_google_play_text(package_id), size=size, border=border, version=version, image_format=image_format)


@register.simple_tag()
def qr_url_for_contact(contact_dict, size=DEFAULT_MODULE_SIZE, border=DEFAULT_BORDER_SIZE, version=DEFAULT_VERSION, image_format=DEFAULT_IMAGE_FORMAT):
    contact_as_mecard = make_contact_text(contact_dict=contact_dict)
    return make_qr_code_url(contact_as_mecard, size=size, border=border, version=version, image_format=image_format)


@register.simple_tag()
def qr_url_for_wifi(wifi_dict, size=DEFAULT_MODULE_SIZE, border=DEFAULT_BORDER_SIZE, version=DEFAULT_VERSION, image_format=DEFAULT_IMAGE_FORMAT):
    wifi_config = make_wifi_text(wifi_dict=wifi_dict)
    return make_qr_code_url(wifi_config, size=size, border=border, version=version, image_format=image_format)