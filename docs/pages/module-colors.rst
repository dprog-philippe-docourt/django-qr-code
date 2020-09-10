Module Colors
=============

By default the QR codes are rendered in black and white but this project
supports individual colors for each QR Code module type, i.e. the alignment
and finder patterns may use another color than the data modules.


The color values can be provided as tuple ``(R, G, B)``, as web color name
(like 'red') or as hexadecimal ``#RRGGBB`` value (i.e. '#085A75').

The value ``None`` is used to indicate transparency, i.e. ``light_color=None``
indicates that all light modules should be transparent.

.. code-block::

    {% qr_from_text "Yellow Submarine" dark_color="darkred" data_dark="darkorange" data_light="yellow" %}


.. image:: ../_static/colors/yellow-submarine.png
    :alt: Colorful 7-H QR code encoding "Yellow Submarine"


.. code-block::

    {% qr_from_text "Rain" dark_color="darkblue" data_dark="steelblue" micro=True %}

.. image:: ../_static/colors/rain.png
    :alt: Colorful M4-Q QR code encoding "RAIN"


Module names
------------

The following examples show the results of all supported module types.
The unaffected modules are rendered as grey or white modules, the red modules
show the result of the keyword.


dark_color
~~~~~~~~~~

Sets the (default) color of dark modules.

.. image:: ../_static/colors/dark.png
    :alt: Picture showing the dark modules

.. image:: ../_static/colors/mqr_dark.png
    :alt: Picture showing the dark modules of a Micro QR code


light_color
~~~~~~~~~~~

Sets the (default) color of light modules.

.. image:: ../_static/colors/light.png
    :alt: Picture showing the light modules

.. image:: ../_static/colors/mqr_light.png
    :alt: Picture showing the light modules of a Micro QR code


alignment_dark_color
~~~~~~~~~~~~~~~~~~~~

Sets the color of the dark alignment pattern modules.

Micro QR Codes don't have alignment patterns.

.. image:: ../_static/colors/alignment_dark.png
    :alt: Picture showing the dark alignment modules

.. image:: ../_static/colors/mqr_alignment_dark.png
    :alt: Picture showing the dark alignment modules of a Micro QR code (none)


alignment_light_color
~~~~~~~~~~~~~~~~~~~~~

Sets the color of the light alignment pattern modules.

Micro QR Codes don't have alignment patterns.

.. image:: ../_static/colors/alignment_light.png
    :alt: Picture showing the light alignment modules

.. image:: ../_static/colors/mqr_alignment_light.png
    :alt: Picture showing the light alignment modules of a Micro QR code (none)


dark_module_color
~~~~~~~~~~~~~~~~~

Sets the color of the dark module.

Micro QR Codes don't have a dark module.

.. image:: ../_static/colors/dark_module.png
    :alt: Picture showing the dark modules

.. image:: ../_static/colors/mqr_dark_module.png
    :alt: Picture showing the dark modules of a Micro QR code (none)


data_dark_color
~~~~~~~~~~~~~~~

Sets the color of the dark data modules.

.. image:: ../_static/colors/data_dark.png
    :alt: Picture showing the dark data modules

.. image:: ../_static/colors/mqr_data_dark.png
    :alt: Picture showing the dark data modules of a Micro QR code


data_light_color
~~~~~~~~~~~~~~~~

Sets the color of the light data modules.

.. image:: ../_static/colors/data_light.png
    :alt: Picture showing the light modules

.. image:: ../_static/colors/mqr_data_light.png
    :alt: Picture showing the light modules of a Micro QR code


finder_dark_color
~~~~~~~~~~~~~~~~~

Sets the color of the dark modules of the finder pattern.

.. image:: ../_static/colors/finder_dark.png
    :alt: Picture showing the dark finder modules

.. image:: ../_static/colors/mqr_finder_dark.png
    :alt: Picture showing the dark finder modules of a Micro QR code


finder_light_color
~~~~~~~~~~~~~~~~~~

Sets the color of the light modules of the finder pattern.

.. image:: ../_static/colors/finder_light.png
    :alt: Picture showing the light finder modules

.. image:: ../_static/colors/mqr_finder_light.png
    :alt: Picture showing the light finder modules of a Micro QR code


format_dark_color
~~~~~~~~~~~~~~~~~

Sets the color of the dark modules of the format information.

.. image:: ../_static/colors/format_dark.png
    :alt: Picture showing the dark format information modules

.. image:: ../_static/colors/mqr_format_dark.png
    :alt: Picture showing the dark format information modules of a Micro QR code (none)


format_light_color
~~~~~~~~~~~~~~~~~~

Sets the color of the light modules of the format information.

.. image:: ../_static/colors/format_light.png
    :alt: Picture showing the light format information modules

.. image:: ../_static/colors/mqr_format_light.png
    :alt: Picture showing the light format information modules of a Micro QR code (none)


quiet_zone_color
~~~~~~~~~~~~~~~~

Sets the color of the quiet zone.

.. image:: ../_static/colors/quiet_zone.png
    :alt: Picture showing the quiet zone

.. image:: ../_static/colors/mqr_quiet_zone.png
    :alt: Picture showing the quiet zone of a Micro QR code


separator_color
~~~~~~~~~~~~~~~

Sets the color of the separator.

.. image:: ../_static/colors/separator.png
    :alt: Picture showing the separator

.. image:: ../_static/colors/mqr_separator.png
    :alt: Picture showing the separator of a Micro QR code


timing_dark_color
~~~~~~~~~~~~~~~~~

Sets the color of the dark modules of the timing pattern.

.. image:: ../_static/colors/timing_dark.png
    :alt: Picture showing the dark timing pattern modules

.. image:: ../_static/colors/mqr_timing_dark.png
    :alt: Picture showing the dark timing pattern modules of a Micro QR code


timing_light_color
~~~~~~~~~~~~~~~~~~

Sets the color of the light modules of the timing pattern.

.. image:: ../_static/colors/timing_light.png
    :alt: Picture showing the light timing pattern modules

.. image:: ../_static/colors/mqr_timing_light.png
    :alt: Picture showing the light timing pattern modules of a Micro QR code


version_dark_color
~~~~~~~~~~~~~~~~~~

Sets the color of the dark modules of the version information.

Micro QR Codes and QR Codes lesser than version 7 don't carry any version information.

.. image:: ../_static/colors/version_dark.png
    :alt: Picture showing the dark version modules

.. image:: ../_static/colors/mqr_version_dark.png
    :alt: Picture showing the dark version modules of a Micro QR code (none)


version_light_color
~~~~~~~~~~~~~~~~~~~

Sets the color of the light modules of the version information.

Micro QR Codes and QR Codes lesser than version 7 don't carry any version information.

.. image:: ../_static/colors/version_light.png
    :alt: Picture showing the light version modules

.. image:: ../_static/colors/mqr_version_light.png
    :alt: Picture showing the light version modules of a Micro QR code (none)
