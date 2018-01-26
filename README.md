[WebUSB] based Interface Device (IFD) handler for USB based Chip Card Interface Device(s) ([CCID]).

This is a proof-of-concept developed for my diploma thesis. I was supported by Humboldt-Universität zu Berlin (Humboldt University of Berlin) and Bundesdruckerei GmbH ("Federal Printing Office"), especially by my two advisors. They can not be held responsible for my work.

[WebUSB]: https://wicg.github.io/webusb/
[CCID]: http://www.usb.org/developers/docs/devclass_docs/DWG_Smart-Card_CCID_Rev110.pdf

### Run Demo ###
To run the demo, host a (simple) web server, or use included Python3.6 `HttpServer.py`. For remote APDU forwarding a WebSocket server example, `WebSocketServer.py` is included. `WebSocketServerPACE` implements PACE protocol with german id token (nPA) (don't forget to update password variable).

Making a CCID available to WebUSB, unless they come with a WebUSB compatible driver, requires operating system specific actions.
- For Windows [Zadig](http://zadig.akeo.ie/) is recommended to load the generic WinUSB driver for your CCID.
- For Linux, the user's browser needs write access to the usb device. This can be done by creating a custom udev rule. See the following example rule created in `/etc/udev/rules.d/50-Identiv-4700F.rules`.
```
SUBSYSTEM=="usb", ATTR{idVendor}=="04e6", ATTR{idProduct}=="5720", MODE="0664", GROUP="plugdev"
```
Vendor Id and Product Id of your CCID can be identified using `lsusb` command.

SSL/TLS encryption is left off for debugging. To enable it see comments in `HttpServer.py` or `WebSocket*.py`.
