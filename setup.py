"""
Install dependencies according to PEP 582 (draft)

[https://www.python.org/dev/peps/pep-0582/]
"""
import sys
import os
import subprocess


packagePath = '__pypackages__/'+str(sys.version_info[0])+'.'+str(sys.version_info[1])+'/lib'
if not os.path.exists(os.path.join(os.getcwd(),packagePath)):
    os.makedirs(os.getcwd()+"/"+packagePath)

virtualsmartcardRequiredPackages = ["readline","pycryptodome"]
WebSocketServerRequiredPackages = ["git+https://github.com/dpallot/simple-websocket-server.git"]
PaceRequiredPackages = ["pycryptodome","ecdsa","pytlv"]

for package in virtualsmartcardRequiredPackages+WebSocketServerRequiredPackages+PaceRequiredPackages:
    subprocess.call([sys.executable, "-m", "pip", "install", package, "--target=%s" % os.path.join(os.getcwd(),packagePath)])
    #implementation note: using import pip and calling pip.main directly does not seem to be supported anymore

try:
    from virtualsmartcard import SmartcardOS, Iso7816OS, VirtualICC # check if virtualsmartcard is properly installed
except ImportError:
    print("\n\nMANUAL INSTRUCTIONS:")
    print("(1) Download virtualsmartcard: https://github.com/frankmorgner/vsmartcard/tree/master/virtualsmartcard/src/vpicc/virtualsmartcard.")
    print("(2) Copy vsmartcard/virtualsmartcard/src/vpicc/virtualsmartcard to "+os.path.join(os.getcwd(),packagePath) + ".")
