[WebUSB] based Interface Device (IFD) handler for USB based Chip Card Interface Device(s) ([CCID]).

This is a proof-of-concept developed for my diploma thesis. I was supported by Humboldt-Universität zu Berlin (Humboldt University of Berlin) and Bundesdruckerei GmbH ("Federal Printing Office"), especially by my two advisors.

[WebUSB]: https://wicg.github.io/webusb/
[CCID]: http://www.usb.org/developers/docs/devclass_docs/DWG_Smart-Card_CCID_Rev110.pdf

### Run Demo ###
To run the demo, host a (simple) web server and access it with a WebUSB compatible Browser e.g. Chrome/Chromium >= 61.

```
                            +- Google Chrome ------------+      +--> WebSocketServer.py
                            |----------------------------|      |    (send GET CHALLENGE and
                            |                            |      |     output the cards result)
                            |     demo.html       +--WebSocket--+
                            |                     |      |      +--> WebSocketServerVICC.py
                            +---------------------|------+      |    (make card available via PC/SC
+-----+    +--------+       |                     v      |      |     on server in virtual reader)
|Smart|<-->|USB CCID| <--WebUSB--> ifd.js <--> ccid.js   |      |
|Card |    |Reader  |       |                            |      +--> WebSocketServerPACE.py
+-----+    +--------+       +----------------------------+           (Generate APDUs to
                                                                      Establish a PACE channel)
```
#### Quick Start ####

1. Start web server (`python3 HttpServer.py`)
2. open `http://localhost:8000/demo.html` in Chrome
3. Click "connect" and choose your USB CCID smart card reader

##### Roll the Dice #####

4. Insert smart card that accepts GET CHALLENGE (`00 84 00 00 00 00 01`)
5. Clicking the square sends GET CHALLENGE; the card's response is translated to the appropriate number of pips on the dice's face

##### GET CHALLENGE WebSocket #####

4. Insert smart card that accepts GET CHALLENGE (`00 84 00 00 00 00 01`)
5. `python3 WebSocketServer.py`
6. Clicking "Get challenge" connects to WebSocketServer.py, which sends a GET CHALLENGE; the response is shown in the log.

##### Relay from Browser to PC/SC #####

4. Insert smart card
5. `python3 WebSocketServerVICC.py`
6. Start virtual smart card reader on localhost:35963 (i.e. start PCSC-Lite or SCardSvr.exe with the vpcd driver)
7. Clicking "send" in the section "Remote nPA PACE" connects to WebSocketServerVICC.py, which relayes the card to the virtual smart card reader
8. Accessing the card in the virtual reader via PC/SC is relayed through the WebSocket and through the browser; the website's log shows the command and response APDUs.

##### Verify CAN with PACE #####

4. Insert smart card that is capable of performing PACE (e.g. German ID card)
5. `python3 WebSocketServerPACE.py`
6. In the section "Remote nPA PACE", enter the card's CAN and click "send". The browser connects to WebSocketServerPACE.py, which verifies the CAN with PACE; the responses are shown in the log.

#### Web Server ####
A simple, Python3.6 based web server, `HttpServer.py`, is included. For remote APDU forwarding a WebSocket server example, `WebSocketServer.py` is included. `WebSocketServerPACE` implements PACE protocol with german id token (nPA).

SSL/TLS encryption is left off for debugging. To enable it see comments in `HttpServer.py` or `WebSocket*.py`.

#### OS specific requirements ####
Making a CCID available to WebUSB, unless they come with a WebUSB compatible driver or device, requires operating system specific actions.
- For Windows [Zadig](http://zadig.akeo.ie/) is recommended to load the generic WinUSB driver for your CCID.
- For Linux, the user's browser needs write access to the usb device. This can be done by creating a custom udev rule. See the following example rule created in `/etc/udev/rules.d/50-Identiv-4700F.rules` and adding your user to the `plugdev` group in `etc/group`.
```
SUBSYSTEM=="usb", ATTR{idVendor}=="04e6", ATTR{idProduct}=="5720", MODE="0600", GROUP="plugdev"
```
Vendor Id and Product Id of your CCID can be identified using `lsusb` command.

### Usage in standalone applications based on electron ###
[electron] provides a Chromium based framework to build native applications for Linux, Mac and Windows. If Chromium >= 61 is used, it supports WebUSB. At time of testing, this was only the case with the beta version.

A working starting point can be the [quick-start example] installed using `npm install -D electron@beta`. Once started (`npm start`), `navigator.usb` is available in the included developer console (Ctrl+Shift+I).


[electron]: https://electronjs.org/
[quick-start example]: https://github.com/electron/electron-quick-start
