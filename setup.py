import re

from setuptools import setup

# Get version without importing
with open("qr_code/__init__.py", "rb") as f:
    VERSION = str(re.search('__version__ = "(.+?)"', f.read().decode("utf-8")).group(1))

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("LICENSE", "r", encoding="utf-8") as fh:
    license = fh.read()


setup(
    name="django-qr-code",
    version=VERSION,
    packages=["qr_code", "qr_code.qrcode", "qr_code.templatetags"],
    url="https://github.com/dprog-philippe-docourt/django-qr-code",
    license="BSD 3-clause",
    author="Philippe Docourt",
    author_email="philippe@docourt.ch",
    maintainer="Philippe Docourt",
    description="An application that provides tools for displaying QR codes on your Django site.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=["segno>=1.6", "django>=4.2", "pydantic>=2.7"],
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3 :: Only",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.2",
        "Natural Language :: English",
    ],
    keywords="qr code django",
)
