# fork-reason

The goal is to extend the library to support EMV card reading.

First release is to add EMV Contactless Communication Protocol functions.

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

def apduCmdSelectByName(name):
    buf = [0x00, 0xA4, 0x04, 0x00]
    buf.append(len(name))
    buf.extend(ord(c) for c in name)
    buf.append(0x00)
    return READER.EmvCom_TransciveApdu(buf)


def readEmv():
    while True:
        (status, backBits) = READER.MFRC522_Request(READER.PICC_REQIDL)
        if READER.MI_OK != status:
            continue
        (status, uid) = READER.MFRC522_Anticoll()
        if READER.MI_OK != status:
            continue
        print('UID: ', ':'.join('{:02X}'.format(x) for x in uid))
        break

    sakByte0 = READER.MFRC522_SelectTag(uid)
    print('SAK[0]: 0x{:02X}'.format(sakByte0))

    if 0 == 0x20 & sakByte0:
        print('Not ISO 14443-4 Compilant!')
        return

    (status, backData) = READER.EmvCom_TransciveRats()
    if READER.MI_ERR == status:
        print('Read ATS ERROR!')
        return
    print('ATS: ', ':'.join('{:02X}'.format(x) for x in backData))

    (status, backData) = apduCmdSelectByName('2PAY.SYS.DDF01')
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


