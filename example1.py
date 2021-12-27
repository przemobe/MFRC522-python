#!/usr/bin/python3

import RPi.GPIO as GPIO
from time import sleep
from mfrc522 import EmvComMFRC522

READER = EmvComMFRC522()

def getApduCmdSelectByName(name):
    buf = [0x00, 0xA4, 0x04, 0x00]
    buf.append(len(name))
    buf.extend(ord(c) for c in name)
    buf.append(0x00)
    return buf


def getApduCmdSelectByAid(aid):
    buf = [0x00, 0xA4, 0x04, 0x00]
    buf.append(len(aid))
    buf.extend(aid)
    buf.append(0x00)
    return buf


def getApduCmdGetProcessingOptions(data=[0x83, 0x00]):
    # EMV Book 3, 6.5.8
    buf = [0x80, 0xA8, 0x00, 0x00]
    buf.append(len(data))
    buf.extend(data)
    buf.append(0x00)
    return buf


def getApduCmdReadRecord(sfi, recordNum):
    # EMV Book 3, 6.5.11
    buf = [0x00, 0xB2]
    buf.append(recordNum) # P1
    buf.append((sfi << 3) | 0x04) # P2
    buf.append(0x00) # LE
    return buf


def readEmv():
    cl_uid_sak = None
    while None == cl_uid_sak:
        cl_uid_sak = READER.MFRC522_TypeACollisionDetection()

    print('SAK: ', ' '.join('{:02X}'.format(x[1]) for x in cl_uid_sak))
    print('UID: ', ' '.join('{:02X}'.format(x) for x in READER.MFRC522_GetUID(cl_uid_sak)))

    if 0 == 0x20 & cl_uid_sak[0][1]:
        print('Not ISO 14443-4 Compilant!')
        return

    (status, backData) = READER.EmvCom_TransciveRats()
    if READER.MI_ERR == status:
        print('Read ATS ERROR!')
        return
    print('ATS: ', ':'.join('{:02X}'.format(x) for x in backData))

    cmd = getApduCmdSelectByName('2PAY.SYS.DDF01')
    (status, backData) = READER.EmvCom_TransciveApdu(cmd)
    if READER.MI_ERR == status:
        print('Read Select PSE Response ERROR!')
        return
    print('Select PSE Response: ', ':'.join('{:02X}'.format(x) for x in backData))


if __name__ == '__main__':
    try:
        while True:
            print('Hold a card near the reader')
            readEmv()
            print('=============================================')
            sleep(5)

    except KeyboardInterrupt:
        GPIO.cleanup()
        raise
