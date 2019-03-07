/**
 * ISO 7816-4 command-response specific part
 *
 * Copyright (C) 2017, Jan Birkholz <jbirkholz@users.noreply.github.com >
 */

/**
 * Build Extended ISO 7816-4 (command) APDU.
 * - optionally create class with Uint8Array/ArrayBuffer containing apdu and prototype getter/setter for properties
 * @param  {Number} CLA            Class Byte.
 * @param  {Number} INS            Instruction Byte.
 * @param  {Number} P1             P1 Byte.
 * @param  {Number} P2             P2 Byte.
 * @param  {Uint8Array} commandData    Command Data Byte Array.
 * @param  {Number} responseLength Length of expectet answer.
 * @return {Uint8Array}                APDU Byte Array.
 */
function buildExtendedAPDU(CLA, INS, P1, P2, commandData, responseLength) { //always build extended APDU
  if(commandData.length>65535) throw new Error("command data must be <=65535 Bytes");
  if(responseLength>65536) throw new Error("Maximum response size must be <=65536");

  //determine length
  let hasCommandData = typeof commandData === Number && commandData > 0;
  let apduLength = 4;
  if(hasCommandData) apduLength+=commandData.length;
  if(responseLength>0) {
    if(hasCommandData) apduLength+=2;
    if(!hasCommandData) apduLength+=3;
  }

  /**
   * Encode Number as ByteArray of given length with Big/Little Endian.
   * @param  {Number}  number               Positive number to be encoded.
   * @param  {Number}  byteLength           Length in Bytes of Array
   * @param  {Boolean} [littleEndian=false] little endian
   * @return {Uint8Array}                   ArrayBuffer is accessible via buffer property.
   */
  let encodeNumber = (number,byteLength,littleEndian = false) => {
    if(number >= Math.pow(2,32)) throw new Error("Number is too large for conversion using >> operator.");
    if(number <0) throw new Error("Number has to be positive.");
    let numberByteArray = new Uint8Array(byteLength); //.buffer property contains ArrayBuffer read&write support
    //fill array according to endianess
    if(littleEndian) {
      for(let i =0;i<numberByteArray.length;i++) { //shifting gives big endian encoded number
        numberByteArray[i] = (number >>(8*i))&0xFF;
      }
    } else {
      for(let i =0;i<numberByteArray.length;i++) { //shifting gives big endian encoded number
        numberByteArray[numberByteArray.length-1-i] = (number >>(8*i))&0xFF; //only save last byte
      }
    }
    return numberByteArray;
  };

  //build APDU
  let apdu = new Uint8Array(apduLength);
  let i=0;
  apdu[i] = CLA;i++;
  apdu[i] = INS;i++;
  apdu[i] = P1;i++;
  apdu[i] = P2;i++;
  if(hasCommandData) {
    apdu[i] = 0x00;i++;
    let commandDataLength = encodeNumber(commandData.length,2,false);
    apdu.set(commandDataLength,i);i+=2;
    apdu.set(commandData,i);i+=commandData.length;
  }
  if(responseLength>0) {
    if(responseLength==65536) responseLength=0; //65536 is 0x0000
    if(hasCommandData ) { //2 Byte
      apdu.set(encodeNumber(responseLength,2,false),i);i+=2;
    }
    if(!hasCommandData) { //3 Byte
      apdu[i] = 0x00;i++;
      apdu.set(encodeNumber(responseLength,2,false),i);i+=2;
    }
  }

  return apdu;
}

let apdus = {
  GET_CHALLENGE: (length) => {
    return buildExtendedAPDU(0x00,0x84,0x00,0x00,0,1);
  },
};

export {buildExtendedAPDU, apdus};
