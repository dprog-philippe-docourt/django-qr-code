from django import template

from qr_code.qr_code import make_qr_code


register = template.Library()


@register.simple_tag()
def qr_from_text(text, size='M', border=4, version=None):
    return make_qr_code(text, size=size, border=border, version=version)
