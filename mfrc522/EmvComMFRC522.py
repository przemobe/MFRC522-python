#!/usr/bin/env python
# -*- coding: utf8 -*-

#    Copyright 2021 Przemyslaw Bereski https://github.com/przemobe/

#    This is version for MicroPython v1.17

from . import MFRC522

class EmvComMFRC522(MFRC522):
    '''This class extends MFRC522 to provide functions for EMV Contactless Communication Protocol'''

    EmvComRxDebug = False
    EmvComTxDebug = False
    EmvComMaxRetx = 32

    EMVCOM_PCD_CMD_RATS = 0xE0
    EMVCOM_PICC_PCB_IBLOCK = 0x02
    EMVCOM_PICC_PCB_RBLOCK = 0xA2
    EMVCOM_PICC_PCB_SBLOCK = 0xC0

    EMVCOM_PCB_BLOK_TYPE_IBLOCK = 0
    EMVCOM_PCB_BLOK_TYPE_RBLOCK = 2
    EMVCOM_PCB_BLOK_TYPE_SBLOCK = 3
    EMVCOM_PCB_BLOK_NAMES = ['IBlock','<01>','RBlock','SBlock']

    EMVCOM_FSDI2BYTES = [16, 24, 32, 40, 48, 64, 96, 128, 256]

    def __init__(self, spi, cs, debugLevel='WARNING'):
        MFRC522.__init__(self, spi, cs, debugLevel)
        self.MAX_LEN = 64 # max supported by MRFC522

    def EmvCom_TxRATS(self, param = 0x50):
        # https://www.emvco.com/wp-content/uploads/2017/04/D_EMV_Contactless_Communication_Protocol_v2.6_20160301114325655.pdf
        # Chapter 5.7
        # Request for Answer to Select (RATS)
        # PCD Command: RATS
        # PICC Response: ATS
        # Table 5.14:  FSDI to FSD Conversion
        # FSDI -> FSD (Bytes)
        # 0x00 -> 16 B
        # 0x10 -> 24 B
        # 0x20 -> 32 B
        # 0x30 -> 40 B
        # 0x40 -> 48 B
        # 0x50 -> 64 B (max supported by MRFC522)
        # 0x60 -> 96 B
        # 0x70 -> 128 B
        # 0x80 -> 256 B
        buf = []
        buf.append(self.EMVCOM_PCD_CMD_RATS)
        buf.append(param)
        crc = self.CalulateCRC(buf)
        buf.extend(crc)

        # initialize PICC data
        self.txIBlockNum = 0
        self.piccFsdMax = 64

        if self.EmvComTxDebug: print('TxRATS: ', ":".join("{:02x}".format(ord(chr(c))) for c in buf))

        (status, backData, backLen) = self.MFRC522_ToCard(self.PCD_TRANSCEIVE, buf)
        return (status, backData)

    def EmvCom_StoreATS(self, ats):
        if len(ats) < 3:
            return
        tc1Flag = 0 != 0x40 & ats[1]
        tb1Flag = 0 != 0x20 & ats[1]
        ta1Flag = 0 != 0x10 & ats[1]
        fsci = 0x0F & ats[1]
        # TODO
        self.piccFsdMax = self.EMVCOM_FSDI2BYTES[fsci]
        if self.EmvComRxDebug: print('ATS len={}, T0=0x{:02X}, TA(1)={}, TB(1)={}, TC(1)={} FSCI={}({} Bytes)'.format(ats[0], ats[1], ta1Flag, tb1Flag, tc1Flag, fsci, self.piccFsdMax))
        return

    def EmvCom_TransciveRats(self):
        (status, backData) = self.EmvCom_TxRATS()
        if (self.MI_ERR == status):
            return (self.MI_ERR, [])
        if self.EmvComRxDebug: print('RxATS: ', ":".join("{:02x}".format(ord(chr(c))) for c in backData))
        self.EmvCom_StoreATS(backData)
        return (status, backData)

    def EmvCom_TxIBlock(self, data, chaining=False):
        # https://www.emvco.com/wp-content/uploads/2017/04/D_EMV_Contactless_Communication_Protocol_v2.6_20160301114325655.pdf
        # Chapter 10 Half-Duplex Block Transmission Protocol
        buf = []
        buf.append(self.EMVCOM_PICC_PCB_IBLOCK | (0x01 & self.txIBlockNum) | (0x10 if chaining else 0))
        buf.extend(data)
        crc = self.CalulateCRC(buf)
        buf.extend(crc)

        self.txIBlockNum += 1

        if self.EmvComTxDebug: print('TxIBlock: ', ":".join("{:02x}".format(ord(chr(c))) for c in buf))

        (status, backData, backLen) = self.MFRC522_ToCard(self.PCD_TRANSCEIVE, buf)
        return (status, backData)

    def EmvCom_TxRBlock(self, nak=0):
        # https://www.emvco.com/wp-content/uploads/2017/04/D_EMV_Contactless_Communication_Protocol_v2.6_20160301114325655.pdf
        # Chapter 10 Half-Duplex Block Transmission Protocol
        buf = []
        buf.append(self.EMVCOM_PICC_PCB_RBLOCK | ((0x01 & nak) << 4) | (0x01 & self.txIBlockNum))
        crc = self.CalulateCRC(buf)
        buf.extend(crc)

        self.txIBlockNum += 1

        if self.EmvComTxDebug: print('TxRBlock: ', ":".join("{:02x}".format(ord(chr(c))) for c in buf))

        (status, backData, backLen) = self.MFRC522_ToCard(self.PCD_TRANSCEIVE, buf)
        return (status, backData)

    def EmvCom_TxSBlock_Wtx(self, wtxm):
        # https://www.emvco.com/wp-content/uploads/2017/04/D_EMV_Contactless_Communication_Protocol_v2.6_20160301114325655.pdf
        # Chapter 10 Half-Duplex Block Transmission Protocol
        buf = []
        buf.append(self.EMVCOM_PICC_PCB_SBLOCK | 0x32)
        buf.append(wtxm)
        crc = self.CalulateCRC(buf)
        buf.extend(crc)

        if self.EmvComTxDebug: print('TxSBlock: ', ":".join("{:02x}".format(ord(chr(c))) for c in buf))

        (status, backData, backLen) = self.MFRC522_ToCard(self.PCD_TRANSCEIVE, buf)
        return (status, backData)

    def EmvCom_TransciveApdu(self, apdu):
        # https://www.emvco.com/wp-content/uploads/2017/04/D_EMV_Contactless_Communication_Protocol_v2.6_20160301114325655.pdf
        # Chapter 10.3
        rxData = []
        retx = 0

        maxTxBlkLen = 61 #TODO: min(PCD_MAX(64), PICC_FSD_MAX(rx in RATS (todo)) - 3)
        startBlkIdx = 0
        endBlkIdx = maxTxBlkLen
        notLastBlkFlag = endBlkIdx < len(apdu)

        while startBlkIdx < len(apdu):
            (status, backData) = self.EmvCom_TxIBlock(apdu[startBlkIdx:endBlkIdx], notLastBlkFlag)
            if (self.MI_ERR == status):
                return (status, [])
            if notLastBlkFlag:
                blockDisc = (backData[0] >> 6) & 0x03
                blockName = self.EMVCOM_PCB_BLOK_NAMES[blockDisc]
                if self.EmvComRxDebug: print('Rx{}: '.format(blockName), ":".join("{:02x}".format(ord(chr(c))) for c in backData))
                if self.EMVCOM_PCB_BLOK_TYPE_RBLOCK == blockDisc:
                    if 0x10 & backData[0]:
                        print('RxRBlock(NAK)')
                        return (self.MI_ERR, [])
                else:
                    # TODO: add handler for WTX
                    print('Rx unsupported block type: ', ":".join("{:02x}".format(ord(chr(c))) for c in backData))
                    return (self.MI_ERR, [])

            startBlkIdx += maxTxBlkLen
            endBlkIdx += maxTxBlkLen
            notLastBlkFlag = endBlkIdx < len(apdu)

        while True:
            blockDisc = (backData[0] >> 6) & 0x03
            blockName = self.EMVCOM_PCB_BLOK_NAMES[blockDisc]
            if self.EmvComRxDebug: print('Rx{}: '.format(blockName), ":".join("{:02x}".format(ord(chr(c))) for c in backData))

            if self.EMVCOM_PCB_BLOK_TYPE_IBLOCK == blockDisc:
                rxData.extend(backData[1:-2]) # skip 1B header and cut 2B CRC
                chaining = (0 != 0x10 & backData[0])
                rxBlockNum = 0x01 & backData[0]
                retx = 0
                if chaining:
                    (status, backData) = self.EmvCom_TxRBlock()
                    if (self.MI_ERR == status):
                        return (status, [])
                else:
                    break
            elif self.EMVCOM_PCB_BLOK_TYPE_SBLOCK == blockDisc:
                sblockType = (0x30 & backData[0]) >> 4
                print('RxSBlock type({}) [0=DESELECT, 3=WTX] : '.format(sblockType), ":".join("{:02x}".format(ord(chr(c))) for c in backData))
                if (3 == sblockType):
                    # WTX
                    wtxm = 0x3F & backData[1]
                    (status, backData) = self.EmvCom_TxSBlock_Wtx(wtxm)
                    if (self.MI_ERR == status):
                        return (status, [])
                    retx += 1
                    if (self.EmvComMaxRetx <= retx):
                        return (self.MI_ERR, [])
                else:
                    # TODO
                    print('Rx unsupported SBlock type({}): '.format(sblockType), ":".join("{:02x}".format(ord(chr(c))) for c in backData))
                    return (self.MI_ERR, [])
            else:
                print('Rx unsupported block type: ', ":".join("{:02x}".format(ord(chr(c))) for c in backData))
                return (self.MI_ERR, [])

        return (status, rxData)
