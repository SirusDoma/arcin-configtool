arcin configtool
=====
This repository contains config tool to configure arcin v1.1, a custom game controller board with support for 11 buttons, 2 analog or quadrature encoders, 2 always-on LEDs, and WS2812B LED lighting via the B9 connector.

The original code by zyp can be found at: https://paste.jvnv.net/view/HtEgg

Pre-Built Images
----------------
Latest config tool can be downloaded [here](https://github.com/SirusDoma/arcin-configtool/releases)

Setup
-----
1. Clone the branch you want to work with.
2. `pip3 install PyQt5` make sure to install everything that required by PyQt5 beforehand.
3. `git submodule update` to retrieve `pyhidapi` submodule, note that this custom made repo that already customized for arcin, not ordinary `pyhidapi`.

Building and Testing
--------------------
Run main.py with python3 with `python3 main.py`

Packaging
---------
1. `pip3 install pyinstaller`
2. `pyinstaller --onefile --windowed main.py`
