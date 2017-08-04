from setuptools import setup

setup(
    name='django-qr-code',
    version='0.2.0',
    packages=['qr_code', 'qr_code.templatetags'],
    url='https://github.com/dprog-philippe-docourt/django-qr-code',
    license='BSD 3-clause',
    author='Philippe Docourt',
    author_email='philippe@docourt.ch',
    description='An application that provides tools for displaying QR codes on your Django site.',
    install_requires=['qrcode', 'django'],
    python_requires='>=3',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3 :: Only',
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.11',
        'Natural Language :: English'
    ],
    keywords='qr code django',
)
