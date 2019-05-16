"""
Install dependencies according to PEP 582 (draft) in __pypackages__

[https://www.python.org/dev/peps/pep-0582/]
"""

def install_pip_packages():
    import sys
    import os
    import subprocess

    # eg __pypackages__/3.7/lib
    packagePath = '__pypackages__/'+str(sys.version_info[0])+'.'+str(sys.version_info[1])+'/lib'
    absolutePackagePath = os.path.join(os.getcwd(),packagePath)
    if not os.path.exists(absolutePackagePath):
        os.makedirs(absolutePackagePath)

    # define dependencies
    virtualsmartcardRequiredPackages = ["readline","pycryptodome"] #pyreadline is used in Windows instead of readline
    WebSocketServerRequiredPackages = ["git+https://github.com/dpallot/simple-websocket-server.git"]
    PaceRequiredPackages = ["pycryptodome","ecdsa","pytlv"]

    # install dependencies
    for package in virtualsmartcardRequiredPackages+WebSocketServerRequiredPackages+PaceRequiredPackages:
        subprocess.call([sys.executable, "-m", "pip", "install", package, "--target=%s" % absolutePackagePath])
        #implementation note: using import pip and calling pip.main directly does not seem to be supported anymore

def install_virtualsmartcard():
    # support PEP 582 (draft) packages
    import sys, os
    packagePath = '__pypackages__/'+str(sys.version_info[0])+'.'+str(sys.version_info[1])+'/lib'
    sys.path.insert(1,os.path.join(os.getcwd(),packagePath))

    # check virtualsmartcard install
    try:
        from virtualsmartcard.VirtualSmartcard import SmartcardOS, Iso7816OS, VirtualICC
    except ImportError:
        # download and install (not an elegant solution, but works)
        try:
            print("Downloading virtualsmartcard...")
            import urllib.request, ssl, zipfile, tempfile # download and unzip
            import os, sys, shutil # file handling

            # create ssl context to download file in
            sslContext = ssl.create_default_context()
            sslContext.load_default_certs(purpose=ssl.Purpose.SERVER_AUTH) # sslContext.get_ca_certs() ist still empty on my system
            knownVerifyLocations = [ # see https://serverfault.com/questions/62496/ssl-certificate-location-on-unix-linux
                "/etc/ssl/certs/ca-certificates.crt",                # Debian/Ubuntu/Gentoo etc.
                "/etc/pki/tls/certs/ca-bundle.crt",                  # Fedora/RHEL 6
                "/etc/ssl/ca-bundle.pem",                            # OpenSUSE
                "/etc/pki/tls/cacert.pem",                           # OpenELEC
                "/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem", # CentOS/RHEL 7
                "/etc/ssl/certs",                                    # SLES10/SLES11, https://golang.org/issue/12139
                "/system/etc/security/cacerts",                      # Android
                "/usr/local/share/certs",                            # FreeBSD
                "/etc/pki/tls/certs",                                # Fedora/RHEL
                "/etc/openssl/certs",                                # NetBSD
                ]
            for verifyLocation in knownVerifyLocations:
                sslContext.load_verify_locations(cafile=verifyLocation)
                if len(sslContext.get_ca_certs()) > 0:
                    break

            # download current vsmartcard master as zip file
            vsmartcardZipData = urllib.request.urlopen("https://github.com/frankmorgner/vsmartcard/archive/master.zip",context=sslContext).read()

            # save download to tempdir
            tempDir = tempfile.TemporaryDirectory() #tempDir.name
            vsmartcardFile = open(os.path.join(tempDir.name,"vsmartcard-master.zip"),"wb") # vsmartcardFile.name
            vsmartcardFile.write(vsmartcardZipData)
            vsmartcardFile.close()

            # unzip
            vsmartcardZipFile = zipfile.ZipFile(os.path.join(tempDir.name,"vsmartcard-master.zip"))
            virtualsmartcardFiles = list(filter(lambda x: x.startswith("vsmartcard-master/virtualsmartcard/src/vpicc/virtualsmartcard"),vsmartcardZipFile.namelist()))
            extracted = vsmartcardZipFile.extractall(tempDir.name,members=virtualsmartcardFiles)
            vsmartcardZipFile.close()

            # move virtualsmartcard
            packagePath = '__pypackages__/'+str(sys.version_info[0])+'.'+str(sys.version_info[1])+'/lib'
            absolutePackagePath = os.path.join(os.getcwd(),packagePath)
            if not os.path.exists(absolutePackagePath):
                os.makedirs(absolutePackagePath)

            shutil.move(os.path.join(tempDir.name,"vsmartcard-master/virtualsmartcard/src/vpicc/virtualsmartcard"),absolutePackagePath)
        except:
            # instruct user to download and install manually
            print("\n\nMANUAL INSTRUCTIONS:")
            print("(1) Download virtualsmartcard: https://github.com/frankmorgner/vsmartcard/tree/master/virtualsmartcard/src/vpicc/virtualsmartcard.")
            print("(2) Copy vsmartcard/virtualsmartcard/src/vpicc/virtualsmartcard to "+absolutePackagePath + ".")

# run
install_pip_packages()
install_virtualsmartcard()
