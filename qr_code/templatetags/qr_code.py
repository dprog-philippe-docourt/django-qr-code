"""Tags for Django template system that help generating QR codes."""
from collections.abc import Callable
from typing import Optional, Any

from django import template

from qr_code.qrcode.maker import make_qr_code_with_args, make_qr_code_url_with_args
from qr_code.qrcode.utils import (
    make_google_play_text,
    make_tel_text,
    make_sms_text,
    make_youtube_text,
    WifiConfig,
    ContactDetail,
    Coordinates,
    EpcData,
    VCard,
    Email,
    MeCard,
    VEvent,
)

register = template.Library()

# QR code options required by the EPC QR code specification.
_EPC_QR_CODE_ARGS = dict(error_correction="M", boost_error=False, micro=False, encoding="utf-8")


def _make_qr_code_or_url(
    data: Any,
    embedded: bool,
    qr_code_args: dict,
    force_text: bool = True,
    use_data_uri_for_svg: bool = False,
    alt_text: None | str = None,
    class_names: None | str = None,
) -> str:
    """Returns the markup of the embedded QR code, or the URL serving its image if `embedded` is False."""
    if embedded:
        return make_qr_code_with_args(
            data,
            qr_code_args=qr_code_args,
            force_text=force_text,
            use_data_uri_for_svg=use_data_uri_for_svg,
            alt_text=alt_text,
            class_names=class_names,
        )
    return make_qr_code_url_with_args(data, qr_code_args=qr_code_args, force_text=force_text)


def _make_app_qr_code_from_obj_or_kwargs(
    obj_or_kwargs,
    expected_cls,
    embedded: bool,
    qr_code_args: dict,
    extra_qr_code_args: Optional[dict] = None,
    force_text: bool = True,
    use_data_uri_for_svg: bool = False,
    alt_text: None | str = None,
    class_names: None | str = None,
) -> str:
    if isinstance(obj_or_kwargs, expected_cls):
        obj = obj_or_kwargs
    else:
        # For compatibility with existing views and templates, try to build from dict.
        obj = expected_cls(**obj_or_kwargs)
    final_args = {**qr_code_args}
    if extra_qr_code_args:
        final_args.update(extra_qr_code_args)
    return _make_qr_code_or_url(
        obj.make_qr_code_data(),
        embedded,
        qr_code_args=final_args,
        force_text=force_text,
        use_data_uri_for_svg=use_data_uri_for_svg,
        alt_text=alt_text,
        class_names=class_names,
    )


def _make_coordinates_qr_code(
    embedded: bool,
    coordinate_names: tuple[str, ...],
    make_text: Callable[[Coordinates], str],
    use_data_uri_for_svg: bool = False,
    alt_text: None | str = None,
    class_names: None | str = None,
    **kwargs,
) -> str:
    """Accepts a *'coordinates'* keyword argument, or one keyword argument for each of the `coordinate_names`."""
    if "coordinates" in kwargs:
        coordinates = kwargs.pop("coordinates")
    else:
        coordinates = Coordinates(*(kwargs.pop(name) for name in coordinate_names))
    return _make_qr_code_or_url(
        make_text(coordinates),
        embedded,
        qr_code_args=kwargs,
        use_data_uri_for_svg=use_data_uri_for_svg,
        alt_text=alt_text,
        class_names=class_names,
    )


def _make_geolocation_qr_code(embedded: bool, **kwargs) -> str:
    return _make_coordinates_qr_code(embedded, ("latitude", "longitude", "altitude"), Coordinates.make_geolocation_text, **kwargs)


def _make_google_maps_qr_code(embedded: bool, **kwargs) -> str:
    return _make_coordinates_qr_code(embedded, ("latitude", "longitude"), Coordinates.make_google_maps_text, **kwargs)


def _make_email(email: str | Email) -> Email:
    # Handle simple case where e-mail is simple the electronic address.
    return Email(to=email) if isinstance(email, str) else email


@register.simple_tag()
def qr_from_text(
    text: str, use_data_uri_for_svg: bool = False, alt_text: None | str = None, class_names: None | str = None, **kwargs
) -> str:
    return make_qr_code_with_args(
        data=text, qr_code_args=kwargs, use_data_uri_for_svg=use_data_uri_for_svg, alt_text=alt_text, class_names=class_names
    )


@register.simple_tag()
def qr_from_data(
    data: Any, use_data_uri_for_svg: bool = False, alt_text: None | str = None, class_names: None | str = None, **kwargs
) -> str:
    return make_qr_code_with_args(
        data=data,
        qr_code_args=kwargs,
        use_data_uri_for_svg=use_data_uri_for_svg,
        alt_text=alt_text,
        class_names=class_names,
        force_text=False,
    )


@register.simple_tag()
def qr_for_email(
    email: str | Email, use_data_uri_for_svg: bool = False, alt_text: None | str = None, class_names: None | str = None, **kwargs
) -> str:
    return _make_app_qr_code_from_obj_or_kwargs(
        _make_email(email),
        Email,
        embedded=True,
        qr_code_args=kwargs,
        use_data_uri_for_svg=use_data_uri_for_svg,
        alt_text=alt_text,
        class_names=class_names,
    )


@register.simple_tag()
def qr_for_tel(
    phone_number: Any, use_data_uri_for_svg: bool = False, alt_text: None | str = None, class_names: None | str = None, **kwargs
) -> str:
    return make_qr_code_with_args(
        make_tel_text(phone_number),
        qr_code_args=kwargs,
        use_data_uri_for_svg=use_data_uri_for_svg,
        alt_text=alt_text,
        class_names=class_names,
    )


@register.simple_tag()
def qr_for_sms(
    phone_number: Any, use_data_uri_for_svg: bool = False, alt_text: None | str = None, class_names: None | str = None, **kwargs
) -> str:
    return make_qr_code_with_args(
        make_sms_text(phone_number),
        qr_code_args=kwargs,
        use_data_uri_for_svg=use_data_uri_for_svg,
        alt_text=alt_text,
        class_names=class_names,
    )


@register.simple_tag()
def qr_for_geolocation(**kwargs) -> str:
    """Accepts a *'coordinates'* keyword argument or a triplet *'latitude'*, *'longitude'*, and *'altitude'*."""
    return _make_geolocation_qr_code(embedded=True, **kwargs)


@register.simple_tag()
def qr_for_google_maps(**kwargs) -> str:
    """Accepts a *'coordinates'* keyword argument or a pair *'latitude'* and *'longitude'*."""
    return _make_google_maps_qr_code(embedded=True, **kwargs)


@register.simple_tag()
def qr_for_youtube(
    video_id: str, use_data_uri_for_svg: bool = False, alt_text: None | str = None, class_names: None | str = None, **kwargs
) -> str:
    return make_qr_code_with_args(
        make_youtube_text(video_id),
        qr_code_args=kwargs,
        use_data_uri_for_svg=use_data_uri_for_svg,
        alt_text=alt_text,
        class_names=class_names,
    )


@register.simple_tag()
def qr_for_google_play(
    package_id: str, use_data_uri_for_svg: bool = False, alt_text: None | str = None, class_names: None | str = None, **kwargs
) -> str:
    return make_qr_code_with_args(
        make_google_play_text(package_id),
        qr_code_args=kwargs,
        use_data_uri_for_svg=use_data_uri_for_svg,
        alt_text=alt_text,
        class_names=class_names,
    )


@register.simple_tag()
def qr_for_contact(
    contact_detail, use_data_uri_for_svg: bool = False, alt_text: None | str = None, class_names: None | str = None, **kwargs
) -> str:
    return _make_app_qr_code_from_obj_or_kwargs(
        contact_detail,
        ContactDetail,
        embedded=True,
        qr_code_args=kwargs,
        use_data_uri_for_svg=use_data_uri_for_svg,
        alt_text=alt_text,
        class_names=class_names,
    )


@register.simple_tag()
def qr_for_vcard(vcard, use_data_uri_for_svg: bool = False, alt_text: None | str = None, class_names: None | str = None, **kwargs) -> str:
    return _make_app_qr_code_from_obj_or_kwargs(
        vcard,
        VCard,
        embedded=True,
        qr_code_args=kwargs,
        use_data_uri_for_svg=use_data_uri_for_svg,
        alt_text=alt_text,
        class_names=class_names,
    )


@register.simple_tag()
def qr_for_mecard(mecard, use_data_uri_for_svg: bool = False, alt_text: None | str = None, class_names: None | str = None, **kwargs) -> str:
    return _make_app_qr_code_from_obj_or_kwargs(
        mecard,
        MeCard,
        embedded=True,
        qr_code_args=kwargs,
        use_data_uri_for_svg=use_data_uri_for_svg,
        alt_text=alt_text,
        class_names=class_names,
    )


@register.simple_tag()
def qr_for_wifi(
    wifi_config, use_data_uri_for_svg: bool = False, alt_text: None | str = None, class_names: None | str = None, **kwargs
) -> str:
    return _make_app_qr_code_from_obj_or_kwargs(
        wifi_config,
        WifiConfig,
        embedded=True,
        qr_code_args=kwargs,
        use_data_uri_for_svg=use_data_uri_for_svg,
        alt_text=alt_text,
        class_names=class_names,
    )


@register.simple_tag()
def qr_for_epc(epc_data, use_data_uri_for_svg: bool = False, alt_text: None | str = None, class_names: None | str = None, **kwargs) -> str:
    return _make_app_qr_code_from_obj_or_kwargs(
        epc_data,
        EpcData,
        embedded=True,
        qr_code_args=kwargs,
        use_data_uri_for_svg=use_data_uri_for_svg,
        alt_text=alt_text,
        class_names=class_names,
        extra_qr_code_args=_EPC_QR_CODE_ARGS,
        force_text=False,
    )


@register.simple_tag()
def qr_for_event(event, use_data_uri_for_svg: bool = False, alt_text: None | str = None, class_names: None | str = None, **kwargs) -> str:
    return _make_app_qr_code_from_obj_or_kwargs(
        event,
        VEvent,
        embedded=True,
        qr_code_args=kwargs,
        use_data_uri_for_svg=use_data_uri_for_svg,
        alt_text=alt_text,
        class_names=class_names,
    )


@register.simple_tag()
def qr_url_from_text(
    text: str, **kwargs
) -> str:
    return make_qr_code_url_with_args(
        data=text, qr_code_args=kwargs,
    )


@register.simple_tag()
def qr_url_from_data(
    data: Any, **kwargs
) -> str:
    return make_qr_code_url_with_args(
        data=data,
        qr_code_args=kwargs,
        force_text=False,
    )


@register.simple_tag()
def qr_url_for_email(
    email: str | Email, **kwargs
) -> str:
    return _make_app_qr_code_from_obj_or_kwargs(
        _make_email(email),
        Email,
        embedded=False,
        qr_code_args=kwargs,
    )


@register.simple_tag()
def qr_url_for_tel(
    phone_number: Any, **kwargs
) -> str:
    return make_qr_code_url_with_args(
        make_tel_text(phone_number),
        qr_code_args=kwargs,
    )


@register.simple_tag()
def qr_url_for_sms(
    phone_number: Any, **kwargs
) -> str:
    return make_qr_code_url_with_args(
        make_sms_text(phone_number),
        qr_code_args=kwargs,
    )


@register.simple_tag()
def qr_url_for_geolocation(**kwargs) -> str:
    """Accepts a *'coordinates'* keyword argument or a triplet *'latitude'*, *'longitude'*, and *'altitude'*."""
    return _make_geolocation_qr_code(embedded=False, **kwargs)


@register.simple_tag()
def qr_url_for_google_maps(**kwargs) -> str:
    """Accepts a *'coordinates'* keyword argument or a pair *'latitude'* and *'longitude'*."""
    return _make_google_maps_qr_code(embedded=False, **kwargs)


@register.simple_tag()
def qr_url_for_youtube(
    video_id: str, **kwargs
) -> str:
    return make_qr_code_url_with_args(
        make_youtube_text(video_id),
        qr_code_args=kwargs,
    )


@register.simple_tag()
def qr_url_for_google_play(
    package_id: str, **kwargs
) -> str:
    return make_qr_code_url_with_args(
        make_google_play_text(package_id),
        qr_code_args=kwargs,
    )


@register.simple_tag()
def qr_url_for_contact(
    contact_detail, **kwargs
) -> str:
    return _make_app_qr_code_from_obj_or_kwargs(
        contact_detail,
        ContactDetail,
        embedded=False,
        qr_code_args=kwargs,
    )


@register.simple_tag()
def qr_url_for_vcard(
    vcard, **kwargs
) -> str:
    return _make_app_qr_code_from_obj_or_kwargs(
        vcard,
        VCard,
        embedded=False,
        qr_code_args=kwargs,
    )


@register.simple_tag()
def qr_url_for_mecard(
    mecard, **kwargs
) -> str:
    return _make_app_qr_code_from_obj_or_kwargs(
        mecard,
        MeCard,
        embedded=False,
        qr_code_args=kwargs,
    )


@register.simple_tag()
def qr_url_for_wifi(
    wifi_config, **kwargs
) -> str:
    return _make_app_qr_code_from_obj_or_kwargs(
        wifi_config,
        WifiConfig,
        embedded=False,
        qr_code_args=kwargs,
    )


@register.simple_tag()
def qr_url_for_epc(
    epc_data, **kwargs
) -> str:
    return _make_app_qr_code_from_obj_or_kwargs(
        epc_data,
        EpcData,
        embedded=False,
        qr_code_args=kwargs,
        extra_qr_code_args=_EPC_QR_CODE_ARGS,
        force_text=False,
    )


@register.simple_tag()
def qr_url_for_event(
    event, **kwargs
) -> str:
    return _make_app_qr_code_from_obj_or_kwargs(
        event,
        VEvent,
        embedded=False,
        qr_code_args=kwargs,
    )
