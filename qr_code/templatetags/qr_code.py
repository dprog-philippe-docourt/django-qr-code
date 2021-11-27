"""Tags for Django template system that help generating QR codes."""
from typing import Optional, Any, Union

from django import template

from qr_code.qrcode.maker import make_qr_code_with_args, make_qr_code_url_with_args
from qr_code.qrcode.utils import make_google_play_text, make_tel_text, make_sms_text, \
    make_youtube_text, WifiConfig, ContactDetail, Coordinates, EpcData, VCard, Email, MeCard

register = template.Library()


def _make_app_qr_code_from_obj_or_kwargs(obj_or_kwargs, expected_cls, embedded: bool, qr_code_args: dict,
                                         extra_qr_code_args: Optional[dict] = None, force_text: bool = True) -> str:
    if isinstance(obj_or_kwargs, expected_cls):
        obj = obj_or_kwargs
    else:
        # For compatibility with existing views and templates, try to build from dict.
        obj = expected_cls(**obj_or_kwargs)
    final_args = {**qr_code_args}
    if extra_qr_code_args:
        final_args.update(extra_qr_code_args)
    if embedded:
        return make_qr_code_with_args(obj.make_qr_code_data(), qr_code_args=final_args, force_text=force_text)
    else:
        return make_qr_code_url_with_args(obj.make_qr_code_data(), qr_code_args=final_args, force_text=force_text)


def _make_google_maps_qr_code(embedded: bool, **kwargs) -> str:
    if 'coordinates' in kwargs:
        coordinates = kwargs.pop('coordinates')
    else:
        coordinates = Coordinates(kwargs.pop('latitude'), kwargs.pop('longitude'))
    if embedded:
        return make_qr_code_with_args(coordinates.make_google_maps_text(), qr_code_args=kwargs)
    else:
        return make_qr_code_url_with_args(coordinates.make_google_maps_text(), qr_code_args=kwargs)


def _make_geolocation_qr_code(embedded: bool, **kwargs) -> str:
    if 'coordinates' in kwargs:
        coordinates = kwargs.pop('coordinates')
    else:
        coordinates = Coordinates(kwargs.pop('latitude'), kwargs.pop('longitude'), kwargs.pop('altitude'))
    if embedded:
        return make_qr_code_with_args(coordinates.make_geolocation_text(), qr_code_args=kwargs)
    else:
        return make_qr_code_url_with_args(coordinates.make_geolocation_text(), qr_code_args=kwargs)


@register.simple_tag()
def qr_from_text(text: str, **kwargs) -> str:
    return make_qr_code_with_args(data=text, qr_code_args=kwargs)


@register.simple_tag()
def qr_from_data(data: Any, **kwargs) -> str:
    return make_qr_code_with_args(data=data, qr_code_args=kwargs, force_text=False)


@register.simple_tag()
def qr_for_email(email: Union[str, Email], **kwargs) -> str:
    if isinstance(email, str):
        # Handle simple case where e-mail is simple the electronic address.
        email = Email(to=email)
    return _make_app_qr_code_from_obj_or_kwargs(email, Email, embedded=True, qr_code_args=kwargs)


@register.simple_tag()
def qr_for_tel(phone_number: Any, **kwargs) -> str:
    return make_qr_code_with_args(make_tel_text(phone_number), qr_code_args=kwargs)


@register.simple_tag()
def qr_for_sms(phone_number: Any, **kwargs) -> str:
    return make_qr_code_with_args(make_sms_text(phone_number), qr_code_args=kwargs)


@register.simple_tag()
def qr_for_geolocation(**kwargs) -> str:
    """Accepts a *'coordinates'* keyword argument or a triplet *'latitude'*, *'longitude'*, and *'altitude'*."""
    return _make_geolocation_qr_code(embedded=True, **kwargs)


@register.simple_tag()
def qr_for_google_maps(**kwargs) -> str:
    """Accepts a *'coordinates'* keyword argument or a pair *'latitude'* and *'longitude'*."""
    return _make_google_maps_qr_code(embedded=True, **kwargs)


@register.simple_tag()
def qr_for_youtube(video_id: str, **kwargs) -> str:
    return make_qr_code_with_args(make_youtube_text(video_id), qr_code_args=kwargs)


@register.simple_tag()
def qr_for_google_play(package_id: str, **kwargs) -> str:
    return make_qr_code_with_args(make_google_play_text(package_id), qr_code_args=kwargs)


@register.simple_tag()
def qr_for_contact(contact_detail, **kwargs) -> str:
    return _make_app_qr_code_from_obj_or_kwargs(contact_detail, ContactDetail, embedded=True, qr_code_args=kwargs)


@register.simple_tag()
def qr_for_vcard(vcard, **kwargs) -> str:
    return _make_app_qr_code_from_obj_or_kwargs(vcard, VCard, embedded=True, qr_code_args=kwargs)


@register.simple_tag()
def qr_for_mecard(mecard, **kwargs) -> str:
    return _make_app_qr_code_from_obj_or_kwargs(mecard, MeCard, embedded=True, qr_code_args=kwargs)


@register.simple_tag()
def qr_for_wifi(wifi_config, **kwargs) -> str:
    return _make_app_qr_code_from_obj_or_kwargs(wifi_config, WifiConfig, embedded=True, qr_code_args=kwargs)


@register.simple_tag()
def qr_for_epc(epc_data, **kwargs) -> str:
    extra = dict(
        error_correction='M',
        boost_error=False,
        micro=False,
        encoding='utf-8',
    )
    return _make_app_qr_code_from_obj_or_kwargs(epc_data, EpcData, embedded=True, qr_code_args=kwargs,
                                                extra_qr_code_args=extra, force_text=False)


@register.simple_tag()
def qr_url_from_text(text: str, **kwargs) -> str:
    return make_qr_code_url_with_args(data=text, qr_code_args=kwargs)


@register.simple_tag()
def qr_url_from_data(data: Any, **kwargs) -> str:
    return make_qr_code_url_with_args(data=data, qr_code_args=kwargs, force_text=False)


@register.simple_tag()
def qr_url_for_email(email: Union[str, Email], **kwargs) -> str:
    if isinstance(email, str):
        # Handle simple case where e-mail is simple the electronic address.
        email = Email(to=email)
    return _make_app_qr_code_from_obj_or_kwargs(email, Email, embedded=False, qr_code_args=kwargs)


@register.simple_tag()
def qr_url_for_tel(phone_number: Any, **kwargs) -> str:
    return make_qr_code_url_with_args(make_tel_text(phone_number), qr_code_args=kwargs)


@register.simple_tag()
def qr_url_for_sms(phone_number: Any, **kwargs) -> str:
    return make_qr_code_url_with_args(make_sms_text(phone_number), qr_code_args=kwargs)


@register.simple_tag()
def qr_url_for_geolocation(**kwargs) -> str:
    """Accepts a *'coordinates'* keyword argument or a triplet *'latitude'*, *'longitude'*, and *'altitude'*."""
    return _make_geolocation_qr_code(embedded=False, **kwargs)


@register.simple_tag()
def qr_url_for_google_maps(**kwargs) -> str:
    """Accepts a *'coordinates'* keyword argument or a pair *'latitude'* and *'longitude'*."""
    return _make_google_maps_qr_code(embedded=False, **kwargs)


@register.simple_tag()
def qr_url_for_youtube(video_id: str, **kwargs) -> str:
    return make_qr_code_url_with_args(make_youtube_text(video_id), qr_code_args=kwargs)


@register.simple_tag()
def qr_url_for_google_play(package_id: str, **kwargs) -> str:
    return make_qr_code_url_with_args(make_google_play_text(package_id), qr_code_args=kwargs)


@register.simple_tag()
def qr_url_for_contact(contact_detail, **kwargs) -> str:
    return _make_app_qr_code_from_obj_or_kwargs(contact_detail, ContactDetail, embedded=False, qr_code_args=kwargs)


@register.simple_tag()
def qr_url_for_vcard(vcard, **kwargs) -> str:
    return _make_app_qr_code_from_obj_or_kwargs(vcard, VCard, embedded=False, qr_code_args=kwargs)


@register.simple_tag()
def qr_url_for_mecard(mecard, **kwargs) -> str:
    return _make_app_qr_code_from_obj_or_kwargs(mecard, MeCard, embedded=False, qr_code_args=kwargs)


@register.simple_tag()
def qr_url_for_wifi(wifi_config, **kwargs) -> str:
    return _make_app_qr_code_from_obj_or_kwargs(wifi_config, WifiConfig, embedded=False, qr_code_args=kwargs)


@register.simple_tag()
def qr_url_for_epc(epc_data, **kwargs) -> str:
    extra = dict(
        error_correction='M',
        boost_error=False,
        micro=False,
        encoding='utf-8',
    )
    return _make_app_qr_code_from_obj_or_kwargs(epc_data, EpcData, embedded=False, qr_code_args=kwargs,
                                                extra_qr_code_args=extra, force_text=False)
