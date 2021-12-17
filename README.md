# fork-reason

The goal is to extend the library to support EMV card reading.

1) Add EMV Contactless Communication Protocol functions
2) Add support for double and triple size UID
3) Port to MicroPython v1.17 (RP2) (see micropython branch)

Branch micropython is to run a library on MicroPython v1.17 (RP2) without additional libraries.

# mfrc522

A python library to read/write RFID tags via the budget MFRC522 RFID module.

This code was published in relation to a [blog post](https://pimylifeup.com/raspberry-pi-rfid-rc522/) and you can find out more about how to hook up your MFRC reader to a Raspberry Pi there.

## Installation

Until the package is on PyPi, clone this repository and run `python setup.py install` in the top level directory.

# mfrc522/EmvComMFRC522

A python library implements EMV Contactless Communication Protocol.

## Example Code

The following code will read EMV card and print Select PSE Response: 

```python
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


def readEmv():
    while True:
        cl_uid_sak = READER.MFRC522_TypeACollisionDetection()
        if None == cl_uid_sak:
            continue
        break

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
```

Example output for a card:

```
Hold a card near the reader
UID:  EF:F6:A5:B2:0E
SAK[0]: 0x28
ATS:  13:78:80:82:02:80:31:80:66:B0:84:12:01:6E:01:83:00:90:00:DD:C7
Select PSE Response:  6F:2B:84:0E:32:50:41:59:2E:53:59:53:2E:44:44:46:30:31:A5:19:BF:0C:16:61:14:4F:07:A0:00:00:00:03:20:10:50:09:56:49:53:41:20:43:41:52:44:90:00
=============================================
```

The response can be decoded using [TLV decoder](https://emvlab.org/tlvutils/):

![obraz](https://user-images.githubusercontent.com/11823937/144728885-9c4fb121-578a-4b29-89df-3ad6a92c25fe.png)


