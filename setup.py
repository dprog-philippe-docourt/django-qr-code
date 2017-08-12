from setuptools import setup

setup(
    name='django-qr-code',
    version='0.3.2',
    packages=['qr_code', 'qr_code.templatetags'],
    url='https://github.com/dprog-philippe-docourt/django-qr-code',
    license='BSD 3-clause',
    author='Philippe Docourt',
    author_email='philippe@docourt.ch',
    maintainer='Philippe Docourt',
    description='An application that provides tools for displaying QR codes on your Django site.',
    long_description="""This application provides tools for displaying QR codes on your `Django <https://www.djangoproject.com/>`_ site.

This application depends on the `qrcode <https://github.com/lincolnloop/python-qrcode>`_ python library which requires the `Pillow <https://github.com/python-pillow/Pillow>`_ library in order to support PNG image format. The Pillow library needs to be installed manually if you want to generate QR codes in PNG format; otherwise, only SVG is format is supported.

This app makes no usage of the Django models and therefore do not use any database.
k
Only Python >= 3.4 is supported.""",
    install_requires=['qrcode', 'django'],
    python_requires='>=3',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3 :: Only',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.11',
        'Natural Language :: English'
    ],
    keywords='qr code django',
)
