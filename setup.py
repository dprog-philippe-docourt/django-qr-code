from setuptools import setup

setup(
    name='django-qr-code',
    version='0.1.0',
    packages=['qr_code', 'qr_code.templatetags'],
    url='https://github.com/dprog-philippe-docourt/django-qr-code',
    license='BSD 3-clause',
    author='Philippe Docourt',
    author_email='philippe@docourt.ch',
    description='An application that provides tools for displaying QR codes on your Django site.',
    install_requires=['qrcode', 'django'],
    python_requires='>=3',
)
