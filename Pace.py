"""
Tobias Senger's implementation of the PACE protocol [pypace]

Updated to work with my WebSocket server, which forwards APDUs. I changed
bytestring encode/decode, logging, added input/result checks and included a
helper function.

[pypace]: https://github.com/tsenger/pypace
"""

# needs pycryptodome (pip install pycryptodomex)
from Crypto.Cipher import AES
from Crypto.Hash import CMAC, SHA
from Crypto.Random import get_random_bytes

from binascii import unhexlify, hexlify
#pip install ecdsa
from ecdsa.ellipticcurve import Point, CurveFp
from ecdsa.curves import Curve

#pip install pytlv
from pytlv.TLV import *

import binascii
import logging


class Pace:

    def __init__(self, connection):
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
        self.__load_brainpool()
        self.connection = connection

    def __long_to_bytearray (self, val, endianness='big'):
        """
        Use :ref:`string formatting` and :func:`~binascii.unhexlify` to
        convert ``val``, a :func:`long`, to a byte :func:`str`.

        :param long val: The value to pack

        :param str endianness: The endianness of the result. ``'big'`` for
          big-endian, ``'little'`` for little-endian.
        """

        # one (1) hex digit per four (4) bits
        width = val.bit_length()

        # unhexlify wants an even multiple of eight (8) bits, but we don't
        # want more digits than we need (hence the ternary-ish 'or')
        width += 8 - ((width % 8) or 8)

        # format width specifier: four (4) bits per hex digit
        fmt = '%%0%dx' % (width // 4)

        # prepend zero (0) to the width, to zero-pad the output
        s = unhexlify(fmt % val)

        if endianness == 'little':
            # see http://stackoverflow.com/a/931095/309233
            s = s[::-1]

        return bytearray(s)


    def __hex_to_int(self, b):
        return int(hexlify(b), 16)


    def __transceiveAPDU(self, command):
        logging.debug("CAPDU: " + toHexString(command))
        data, sw1, sw2 = self.connection.transmit( command )
        logging.debug("RAPDU Data: " + toHexString(data))
        logging.debug("RAPDU SW: %02x %02x" % (sw1, sw2))
        return bytearray(data)


    def __kdf(self, password, c):
        intarray = [0, 0, 0 , c]
        mergedData = list(bytearray(password)) + intarray
        sha = SHA.new()
        sha.update(bytearray(mergedData))
        return bytearray(sha.digest())[0:16]


    def __decryptNonce(self, encryptedNonce, password):
        derivatedPassword = self.__kdf(password, 3)
        aes = AES.new(bytes(derivatedPassword), AES.MODE_ECB)
        return bytearray(aes.decrypt(bytes(encryptedNonce)))


    def __getX1(self):
        self.__PCD_SK_x1 = self.__hex_to_int(bytearray(get_random_bytes(32)))
        PCD_PK_X1 = self.pointG * self.__PCD_SK_x1
        return bytearray(bytearray([0x04])+self.__long_to_bytearray(PCD_PK_X1.x())+ self.__long_to_bytearray(PCD_PK_X1.y()))


    def __getX2(self, PICC_PK, decryptedNonce):
        x = PICC_PK[1:33]
        y = PICC_PK[33:]

        pointY1 = Point( self.curve_brainpoolp256r1, self.__hex_to_int(x), self.__hex_to_int(y), self._q)
        sharedSecret_P = pointY1 * self.__PCD_SK_x1
        pointG_strich = (self.pointG * self.__hex_to_int(decryptedNonce)) + sharedSecret_P

        self.__PCD_SK_x2 = self.__hex_to_int(bytearray(get_random_bytes(32)))
        PCD_PK_X2 = pointG_strich * self.__PCD_SK_x2
        return bytearray(bytearray([0x04])+self.__long_to_bytearray(PCD_PK_X2.x())+ self.__long_to_bytearray(PCD_PK_X2.y()))


    def __sendMSESetAt(self, pace_oid, pw_ref, chat = None):
        if (chat is None):
            apdu_mse = [0x00, 0x22, 0xc1, 0xa4, len(pace_oid)+5, 0x80, len(pace_oid)] + pace_oid + [0x83, 0x01, pw_ref]
        else:
            apdu_mse = [0x00, 0x22, 0xc1, 0xa4, len(pace_oid)+8+len(chat), 0x80, len(pace_oid)] + pace_oid + [0x83, 0x01, pw_ref] + [0x7F, 0x4C, len(chat)] + chat
        self.__transceiveAPDU(apdu_mse)


    def __sendGA1(self):
        apdu_ga1 = [0x10, 0x86, 0x00, 0x00, 0x02, 0x7c, 0x00, 0x00]
        return self.__transceiveAPDU(apdu_ga1)[4:20]


    def __sendGA2(self, PCD_PK):
        header = bytearray([0x10, 0x86, 0, 0, len(PCD_PK)+4, 0x7c, len(PCD_PK)+2, 0x81, len(PCD_PK)])
        response = self.__transceiveAPDU(list(header + PCD_PK)+[0])
        return response[4:]


    def __sendGA3(self, PCD_PK):
        header = bytearray([0x10, 0x86, 0, 0, len(PCD_PK)+4, 0x7c, len(PCD_PK)+2, 0x83, len(PCD_PK)])
        response = self.__transceiveAPDU(list(header + PCD_PK)+[0])
        return bytearray(response[4:])


    def __sendGA4(self, authToken):
        header = bytearray([0x00, 0x86, 0, 0, len(authToken)+4, 0x7c, len(authToken)+2, 0x85, len(authToken)])
        response = self.__transceiveAPDU(list(header + authToken)+[0])

        tlv = TLV(['86', '87', '88'])
        collection = tlv.parse(binascii.hexlify(response[2:]).decode('ascii'))
        tpicc = collection.get('86') if collection.get('86')!=None else ""
        car1 = collection.get('87') if collection.get('87')!=None else ""
        car2 = collection.get('88') if collection.get('88')!=None else ""

        return bytearray.fromhex(tpicc), bytearray.fromhex(car1), bytearray.fromhex(car2)

    def __getSharedSecret(self, PICC_PK):
        x = PICC_PK[1:33]
        y = PICC_PK[33:]
        pointY2 = Point( self.curve_brainpoolp256r1, self.__hex_to_int(x), self.__hex_to_int(y), self._q)
        K = pointY2 * self.__PCD_SK_x2
        return self.__long_to_bytearray(K.x())


    def __calcAuthToken(self, kmac, algorithm_oid, Y2):
        oid_input = [0x06, len(algorithm_oid)] +algorithm_oid
        mac_input = [0x7f, 0x49, len(oid_input)+len(Y2)+2] + oid_input + [0x86, len(Y2)] + list(Y2)
        logging.debug("Mac input: " + toHexString(mac_input))
        return bytearray(self.__getCMAC(kmac, bytearray(mac_input)))[:8]


    def __getCMAC(self, key, data):
        cmac = CMAC.new(bytes(key), ciphermod=AES)
        cmac.update(bytes(data))
        return bytearray(cmac.digest())


    def __load_brainpool(self):
        # Brainpool P-256-r1
        _a = 0x7D5A0975FC2C3057EEF67530417AFFE7FB8055C126DC5C6CE94A4B44F330B5D9
        _b = 0x26DC5C6CE94A4B44F330B5D9BBD77CBF958416295CF7E1CE6BCCDC18FF8C07B6
        _p = 0xA9FB57DBA1EEA9BC3E660A909D838D726E3BF623D52620282013481D1F6E5377
        _Gx = 0x8BD2AEB9CB7E57CB2C4B482FFC81B7AFB9DE27E1E3BD23C23A4453BD9ACE3262
        _Gy = 0x547EF835C3DAC4FD97F8461A14611DC9C27745132DED8E545C1D54C72F046997
        self._q = 0xA9FB57DBA1EEA9BC3E660A909D838D718C397AA3B561A6F7901E0E82974856A7

        self.curve_brainpoolp256r1 = CurveFp( _p, _a, _b)
        self.pointG = Point(self.curve_brainpoolp256r1, _Gx, _Gy, self._q)

    #we are server/terminal
    def performPACE(self, algorithm_oid, password, pw_ref, chat = None):
        if not isinstance(password,bytes): raise Exception("Password has to be an array of bytes with ASCII encoded characters.")
        self.__sendMSESetAt(algorithm_oid, pw_ref, chat)

        encryptedNonce = self.__sendGA1() #receive nonce
        logging.info("PACE encrypted nonce: " + toHexString(list(encryptedNonce)))
        decryptedNonce = self.__decryptNonce(encryptedNonce, password) #ICC nonce
        logging.info("PACE decrypted nonce: " + toHexString(list(decryptedNonce)))

        #1st DH key agreement
        PCD_PK_X1 = self.__getX1() #terminal (temp) pubkey. SK=SecureKey/privKey
        logging.info("PACE PCD_PK_X1: "+toHexString(list(PCD_PK_X1)))
        PICC_PK_Y1 = self.__sendGA2(PCD_PK_X1) #icc (temp) pubkey
        logging.info("PACE PICC_PK_Y1: "+toHexString(list(PICC_PK_Y1)))

        PCD_PK_X2 = self.__getX2(PICC_PK_Y1, decryptedNonce) #2nd key agreement(ownSK,otherPK,D)
        logging.info("PACE PCD_PK_X2: "+toHexString(list(PCD_PK_X2)))
        PICC_PK_Y2 = self.__sendGA3(PCD_PK_X2)
        logging.info("PACE PICC_PK_Y2: "+toHexString(list(PICC_PK_Y2)))

        sharedSecretK = self.__getSharedSecret(PICC_PK_Y2) #sharedKey
        logging.info("PACE Shared Secret K: "+toHexString(list(sharedSecretK)))

        kenc = self.__kdf(sharedSecretK, 1)
        logging.info("PACE K_enc: "+toHexString(list(kenc)))

        kmac = self.__kdf(sharedSecretK, 2)
        logging.info("PACE K_mac: "+toHexString(list(kmac)))

        tpcd = self.__calcAuthToken(kmac, algorithm_oid, PICC_PK_Y2)
        logging.info("PACE tpcd: "+toHexString(list(tpcd)))

        tpicc, car1, car2 = self.__sendGA4(tpcd)
        logging.info("PACE tpicc: "+toHexString(list(tpicc)))
        logging.info("CAR1: "+ car1.decode('ascii') +", CAR2: " + car2.decode('ascii'))

        tpicc_strich = self.__calcAuthToken(kmac, algorithm_oid, PCD_PK_X2);

        if tpicc == tpicc_strich:
            logging.info("PACE established!")
            return 0
        else:
             logging.info("PACE failed!");
             return -1

#simple version of pyscard's smartcard.util.toHexString to reduce dependencies
def toHexString(bytes):
    return ''.join('%02x ' % byte for byte in bytes)
