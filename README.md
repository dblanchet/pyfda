`pyfda` is a collection of command-line and GUI tools for [Flydream
Altimeter](http://www.fd-rc.com/Showcpzs.asp?id=893) flight data
extraction and visualization.

I wrote `pyfda` because the altimeter came with a Windows-only software.

Currently tested on:

* Mac OS X 10.9.1 with Python 2.7
* Linux Ubuntu 13.10 with Python 2.7 and Python 3.3

Screenshot
----------

![screenshot](gui_screenshot.png)

Dependencies
------------

Data extraction relies on `pyserial` library and SILabs
USB to UART driver:

* http://pyserial.sourceforge.net/
* http://www.silabs.com/products/mcu/pages/usbtouartbridgevcpdrivers.aspx

PySerial is embedded in Mac OS X bundle installer.

ToDo
----

`pyfda` is a work in progress.

In no particular order, I would like to:

* Write a user manual for CLI tool
* Test on Mac with Python 3, Test on Windows with both Python 2 and 3
* Add missing features in GUI
* Publish on PyPI?

License
-------

This code is published under the BSD license:

   ````
   Copyright (c) 2014, David Blanchet
   All rights reserved.

   Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice, this
      list of conditions and the following disclaimer.

   2. Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer in the documentation
      and/or other materials provided with the distribution.

   3. Neither the name of the copyright holder nor the names of its contributors
      may be used to endorse or promote products derived from this software
      without specific prior written permission.

   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
   ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
   WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
   DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
   FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
   DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
   SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
   CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
   OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
   ````
