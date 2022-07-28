import os
import re

from qr_code.tests import PNG_REF_SUFFIX, SVG_REF_SUFFIX


def get_urls_without_token_for_comparison(*urls):
    token_regex = re.compile(r"&?token=[^&]+")
    simplified_urls = list(map(lambda x: token_regex.sub("", x), urls))
    simplified_urls = list(map(lambda x: x.replace("?&", "?"), simplified_urls))
    return simplified_urls


def get_resources_path():
    tests_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(tests_dir, "resources")


def minimal_svg(s):
    """Returns the SVG document without the XML declaration and SVG namespace declaration

    :rtype: str
    """
    return s.replace('<?xml version="1.0" encoding="utf-8"?>\n', "").replace('xmlns="http://www.w3.org/2000/svg" ', "").strip()


def get_svg_content_from_file_name(base_file_name):
    with open(os.path.join(get_resources_path(), base_file_name + SVG_REF_SUFFIX), encoding="utf-8") as file:
        return file.read()


def get_png_content_from_file_name(base_file_name):
    with open(os.path.join(get_resources_path(), base_file_name + PNG_REF_SUFFIX), "rb") as file:
        return file.read()


def write_svg_content_to_file(base_file_name, image_content):
    with open(os.path.join(get_resources_path(), base_file_name + SVG_REF_SUFFIX), "wt", encoding="utf-8") as file:
        file.write(image_content)


def write_png_content_to_file(base_file_name, image_content):
    with open(os.path.join(get_resources_path(), base_file_name + PNG_REF_SUFFIX), "wb") as file:
        file.write(image_content)
