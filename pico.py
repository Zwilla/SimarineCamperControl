#!/usr/bin/env python3

import os
import time
import socket
import sys
from typing import Dict, Any

import dictdiffer as dictdiffer
import select
import requests
import json
import brainsmoke
import copy

responses = [''] * 200
sensors = ['']


def debug(string):
    if "DEBUG" in os.environ:
        if os.environ['DEBUG'] == 'picoCC':
            print(string)
            sys.stdout.flush()


def empty_socket_has_exit(sock, terminator):
    """remove the data present on the socket"""
    inputSi = [sock]
    while 1:
        inputready, o, e = select.select(inputSi, [], [], 0.0)
        if len(inputready) == 0:
            break

        for s in inputready:
            s.recv(2048)

    print("Regular exit:" + terminator)

    exit(0)


def striplist(siList):
    return [x.strip() for x in siList]


def hexdump(b):
    hexSi = ' '.join(["%02x" % b])
    if len(hexSi) == 3:
        hexSi = "0" + hexSi
    if len(hexSi) == 2:
        hexSi = "00" + hexSi
    return hexSi[0:2] + " " + hexSi[2:4]


def HexToByte(hexStr):
    """
    Convert a string hexSi byte values into a byte string. The Hex Byte values may
    or may not be space separated.
    """
    bytesSi = []
    hexStr = ''.join(hexStr.split(" "))
    for i in range(0, len(hexStr), 2):
        bytesSi.append(chr(int(hexStr[i:i + 2], 16)))
    return ''.join(bytesSi)


def ByteToHex(byteStr):
    """
    Convert a byte string to it's hexSi string representation e.g. for output.
    """
    return ''.join(["%02X " % ord(x) for x in byteStr]).strip()


def HexToInt(hexSi, lastBytes):
    return int(hexSi.replace(' ', '')[-lastBytes:], 16)


def IntToDecimal(integer):
    return integer / float(10)


def BinToHex(message_bth):
    response_bth = ''
    for x in message_bth:
        hexy = format(x, '02x')
        response_bth = response_bth + hexy + ' '
    return response_bth


def parse(message_p):
    values = message_p.split(' ff')
    values = striplist(values)
    return values


def getNextField(response_gnf, position):
    field_nr = int(response_gnf[0:2], 16)
    ftc = int(response_gnf[3:6])
    debug("field_type: " + response_gnf[3:6])
    field_type = int(response_gnf[3:5], 16)
    c = position
    device = 'SC287981'

    # SOURCE 1
    # 01. position 01 - 30 = SC287981           (Type = 10) 2.nd data
    # 02. position 02 - 09 =                    (Type = 07) 2.nd data
    # 03. position 03 - 12 = Sensor 1           (Type = 04) 2.nd data
    # 04. position 04 - 15 = Barometer          (Type = 00) 2.nd data
    # 05. position 07 - 14 = PICO INTERNAL      (Type = 01) 2.nd data
    # 06. position 08 - 23 = SCC8               (Type = 00) 2.nd data

    # 07. position 12 - 24 = SPU62 [2880] 1     (Type = 02) 2.nd data
    # 08. position 13 - 25 = SPU62 [2880] 2     (Type = 02) 2.nd data
    # 09. position 14 - 26 = SPU62 [2880] 3     (Type = 02) 2.nd data
    # 10. position 15 - 27 = SPU62 [2880] 4     (Type = 02) 2.nd data

    # 11. position 16 - 23 = SPU62 [2880] 1     (Type = 01) 2.nd data
    # 12. position 17 - 24 = SPU62 [2880] 2     (Type = 01) 2.nd data
    # 13. position 18 - 25 = SPU62 [2880] 3     (Type = 01) 2.nd data
    # 14. position 19 - 26 = SPU62 [2880] 4     (Type = 01) 2.nd data

    # 15. position 20 - 28 = SPU62 [2880] 1     (Type = 06) 2.nd data
    # 16. position 21 - 29 = SPU62 [2880] 2     (Type = 06) 2.nd data
    # 17. position 22 - 30 = SPU62 [2880] 3     (Type = 06) 2.nd data
    # 18. position 23 - 31 = SPU62 [2880] 4     (Type = 06) 2.nd data

    # 19. position 24 - 42 = SPU62 [2880]       (Type = 25) 2.nd data
    # 20. position 27 - 38 =                    (Type = 13) 2.nd data
    # 21. position 28 - 39 =                    (Type = 13) 2.nd data
    # 22. position 29 - 46 = BATTERY 1          (Type = 09) 2.nd data
    # 23. position 30 - 52 = FRISCHWASSER       (Type = 08) 2.nd data
    # 24. position 31 - 48 = STARTERBAT         (Type = 09) 2.nd data
    # 25. position 32 - 44 = BAT1.TEMP          (Type = 03) 2.nd data
    # 26. position 33 - 45 = BAT2.TEMP          (Type = 03) 2.nd data
    # 27. position 34 - 46 = STARTERBAT.TEMP    (Type = 03) 2.nd data
    # 28. position 35 - 47 = HEIZUNG OUT        (Type = 03) 2.nd data
    # 29. position 36 - 53 = BATPICO            (Type = 09) 2.nd data
    # 30. position 37 - 54 = STARTEREINGANG     (Type = 09) 2.nd data
    # 31. position 38 - 50 = SC303 [5450]       (Type = 02) 2.nd data

    # 32. position 39 - 46 = SC303 [5450] 1     (Type = 01) 2.nd data
    # 34. position 40 - 47 = SC303 [5450] 2     (Type = 01) 2.nd data

    # 35. position 41 - 49 = SC303 [5450] 1     (Type = 06) 2.nd data
    # 36. position 42 - 50 = SC303 [5450] 2     (Type = 06) 2.nd data
    # 38. position 43 - 51 = SC303 [5450] 3     (Type = 06) 2.nd data

    # 39. position 44 - 56 = SC303.TEMP         (Type = 03) 2.nd data
    # 40. position 45 - 67 = GRAUWASSER         (Type = 08) 2.nd data

    # SOURCE 2

    if field_type == 1:
        debug(response_gnf)
        fta = response_gnf[6:11].replace(' ', '')
        ftb = response_gnf[12:17].replace(' ', '')
        debug("field_type1 a: " + response_gnf[6:11].replace(' ', ''))
        debug("field_type1 b: " + response_gnf[12:17].replace(' ', ''))
        data = response_gnf[6:17]
        debug("field_type1 data: " + data)
        response_gnf = response_gnf[21:]
        # if (data[0:11] == '7f ff ff ff'):
        # return field_nr, '', response_pr
        # else:
        a = int(data[0:5].replace(' ', ''), 16)
        b = int(data[6:11].replace(' ', ''), 16)
        # field_data = [a, b, data]
        field_data = [a, b, c, field_type]

        return field_nr, field_data, response_gnf

    if field_type == 3:
        debug(response_gnf)
        debug("field_type3 a: " + response_gnf[21:27].replace(' ', ''))
        debug("field_type3 b: " + response_gnf[27:32].replace(' ', ''))
        data = response_gnf[21:32]
        debug("field_type3 data: " + data)
        response_gnf = response_gnf[36:]
        if data[0:11] == '7f ff ff ff':
            return field_nr, '', response_gnf
        else:
            a = int(data[0:5].replace(' ', ''), 16)
            b = int(data[6:11].replace(' ', ''), 16)
            # field_data = [a, b, data]
            field_data = [a, b, c, field_type]
            return field_nr, field_data, response_gnf

    if field_type == 4:  # device string
        # Strip first part
        response_gnf = response_gnf[21:]
        nextHex = response_gnf[0:2]
        word = ''
        while nextHex != '00':
            word += nextHex
            response_gnf = response_gnf[3:]
            nextHex = response_gnf[0:2]
        word = HexToByte(word)
        print("field_type4 Word: " + word)
        response_gnf = response_gnf[6:]  # Strip seperator
        return field_nr, word, response_gnf

    print("Unknown field type " + str(field_type))


def getNextFieldS2(response_gnf, position):
    field_nr = position
    field_nrData = int(response_gnf[0:2], 16)
    debug(response_gnf)
    fta = response_gnf[6:11].replace(' ', '')
    ftb = response_gnf[12:17].replace(' ', '')
    debug("field_type1 a: " + response_gnf[6:11].replace(' ', ''))
    debug("field_type1 b: " + response_gnf[12:17].replace(' ', ''))
    data = response_gnf[6:17]
    debug("field_type1 data: " + data)
    response_gnf = response_gnf[21:]
    a = int(data[0:5].replace(' ', ''), 16)
    b = int(data[6:11].replace(' ', ''), 16)
    field_data = [a, b, field_nrData, position]
    return field_nrData, field_data, response_gnf


def parseResponse(response_pr, position):
    dictSi = {}
    # strip header
    response_pr = response_pr[42:]

    while len(response_pr) > 6:
        a = len(response_pr)
        position = position + 1
        field_nr, field_data, response_pr = getNextField(response_pr, position)
        # debug(str(field_nr) + " " + field_data)
        print('field_nr:' + str(field_nr))
        print(' data:' + str(field_data))
        debug(response_pr + " " + str(len(response_pr)))
        debug(str(field_data))
        dictSi[field_nr] = field_data

    return dictSi


def parseResponseS2(response_pr, position):
    dictSi = {}
    # strip header
    response_pr = response_pr[42:]

    while len(response_pr) > 6:
        a = len(response_pr)
        position = position + 1
        field_nr, field_data, response_pr = getNextFieldS2(response_pr, position)
        # debug(str(field_nr) + " " + field_data)
        print('field_nr:' + str(field_nr))
        print(' data:' + str(field_data))
        debug(response_pr + " " + str(len(response_pr)))
        debug(str(field_data))
        dictSi[field_nr] = field_data

    return dictSi


def add_crc(messageSi):
    fields = messageSi.split()
    message_int = [int(x, 16) for x in fields[1:]]
    crc_int = brainsmoke.calc_rev_crc16(message_int[0:-1])
    return messageSi + " " + hexdump(crc_int)


def send_receive(messageSi):
    bytesSi = messageSi.count(' ') + 1
    debug(("Sending : " + messageSi + " (" + str(bytesSi) + " bytesSi)"))
    messageSi = bytearray.fromhex(messageSi)
    response_sr = ''
    hexSi = ''

    try:
        s.sendall(messageSi)
        for x in s.recv(2048):
            hexSi = format(x, '02x')
            response_sr = response_sr + hexSi + ' '
            debug('Response: ' + response_sr)
    except BlockingIOError:
        sys.stdout.flush()
        time.sleep(0.9)
        empty_socket_has_exit(client, 'send_receive')
    finally:
        debug("The 'try except' is finished - send_receive")

    return response_sr


def open_tcp(picoIp_ot):
    try:
        # Create a TCP stream socket with address family of IPv4 (INET)
        serverport = 5001
        # Connect to the server at given IP and port
        s.connect((picoIp_ot, serverport))
        return
    except BrokenPipeError:
        debug("Connection to " + str(picoIp_ot) + ":5001 failed. Retrying in 1 sec.")
        time.sleep(5)
        # try again
        return open_tcp(picoIp_ot)
    finally:
        debug("The show must go on")


def get_pico_config(pico_ip_get):
    config_SimarineSystem = {}
    open_tcp(pico_ip_get)
    response_list = []
    messageSi = '00 00 00 00 00 ff 02 04 8c 55 4b 00 03 ff'
    messageSi = add_crc(messageSi)

    req_count = int(0 + 1)
    # Response: 00 00 00 00 00 ff 02 04 8c 55 4b 00 11 ff 01 01 00 00 00 1e ff 02 01 00 00 00 30 ff 32 cf
    try:
        response_gpc = send_receive(messageSi)
        req_count = int(response_gpc.split()[19], 16) + 1
        debug("req_count: " + str(req_count))
        for pos in range(req_count):
            messageSi = (
                    '00 00 00 00 00 ff 41 04 8c 55 4b 00 16 ff 00 01 00 00 00 ' + "%02x" % pos + ' ff 01 03 00 00 00 00 ff 00 00 00 00 ff')
            messageSi = add_crc(messageSi)
            response_gpc = send_receive(messageSi)
            device_Simarine = parseResponse(response_gpc, pos)
            config_SimarineSystem[pos] = device_Simarine

    except KeyError:
        sys.stdout.flush()
        time.sleep(0.9)
        empty_socket_has_exit(client, 'get_pico_config')
    finally:
        # Close tcp connection
        s.close()

    return config_SimarineSystem


def toTemperature(temp):
    # Unsigned to signed
    if temp > 32768:
        temp = temp - 65536
    temp2 = float(("%.2f" % round(temp / float(10) + 273.15, 2))) / 10
    return temp2


def toTemperaturePriority(temp):
    priority = 'dummy'
    if temp > 0:
        priority = 'high'
    if temp > 1:
        priority = 'medium'
    if temp > 2:
        priority = 'low'
    if temp > 3:
        priority = 'hide'

    return priority


def createSensorList(config_csl):
    sensorListSi = {}
    fluid = ['dummy', 'freshWater', 'fuel', 'wasteWater']
    fluid_type = ['dummy', 'fresh water', 'diesel', 'blackwater']
    battery_type = ['dummy', 'wet low maintenance', 'wet maintenance free', 'AGM', 'Deep Cycle', 'Gel', 'LiFePo4']
    ntc_type = ['dummy', '10k', '5k']
    elementPos = 0

    for entry in config_csl.keys():
        debug(config_csl[entry])
        # Set id_csl
        id_csl = config_csl[entry][0][1]
        # Set type_cls
        type_csl = config_csl[entry][1][1]
        # Default elementsize
        elementSize = 1
        sensorListSi[id_csl] = {}

        if type_csl == 10:
            type_csl = '10 System'

            elementSize = 0
            elementPos = elementPos + elementSize
            sensorListSi[id_csl].update({'pos': elementPos})
            sensorListSi[id_csl].update({'type_csl': type_csl})
            sensorListSi[id_csl].update({'name': config_csl[entry][10]})
            sensorListSi[id_csl].update({'name2': config_csl[entry][15]})
            sensorListSi[id_csl].update({'val 3.0': config_csl[entry][3][0]})
            sensorListSi[id_csl].update({'val 3.1': config_csl[entry][3][1]})
            sensorListSi[id_csl].update({'val 11.0': config_csl[entry][11][0]})
            sensorListSi[id_csl].update({'val 11.1': config_csl[entry][11][1]})
            sensorListSi[id_csl].update({'Port': config_csl[entry][12][1]})
            sensorListSi[id_csl].update({'val 13.0': config_csl[entry][13][0]})
            sensorListSi[id_csl].update({'val 13.1': config_csl[entry][13][1]})
            sensorListSi[id_csl].update({'val 14.0': config_csl[entry][14][0]})
            sensorListSi[id_csl].update({'client port': config_csl[entry][14][1]})
            sensorListSi[id_csl].update({'val 29.0': config_csl[entry][29][0]})
            sensorListSi[id_csl].update({'val 29.1': config_csl[entry][29][1]})

        if type_csl == 7:
            type_csl = 'Battery Loader'

            elementSize = 0
            elementPos = elementPos + elementSize
            sensorListSi[id_csl].update({'pos': elementPos})
            sensorListSi[id_csl].update({'type_csl': type_csl})
            sensorListSi[id_csl].update({'name': config_csl[entry][3][0]})
            sensorListSi[id_csl].update({'val 2': config_csl[entry][3][1]})
            sensorListSi[id_csl].update({'val 7200': config_csl[entry][4][1]})
            sensorListSi[id_csl].update({'val 5': config_csl[entry][3][0]})
            sensorListSi[id_csl].update({'val 3': config_csl[entry][7][0]})
            sensorListSi[id_csl].update({'val 4': config_csl[entry][7][1]})

        if type_csl == 4:
            type_csl = 'SolarPower'
            elementSize = 1
            elementPos = elementPos + elementSize
            sensorListSi[id_csl].update({'pos': elementPos})
            sensorListSi[id_csl].update({'type_csl': type_csl})

            sensorListSi[id_csl].update({'name': config_csl[entry][3]})
            sensorListSi[id_csl].update({'val.4.0': config_csl[entry][4][0]})
            sensorListSi[id_csl].update({'val.4.1': config_csl[entry][4][1]})
            sensorListSi[id_csl].update({'Amp Input': config_csl[entry][8][1]})
            if config_csl[entry][8][1] == 255:
                sensorListSi[id_csl].update({'Amp Input': 'no Input'})
            sensorListSi[id_csl].update({'val.9.0': config_csl[entry][9][0]})
            sensorListSi[id_csl].update({'val.9.1': config_csl[entry][9][1]})

        if type_csl == 0:
            type_csl = 'reserved 0.0'
            elementSize = 0
            elementPos = elementPos + elementSize
            sensorListSi[id_csl].update({'pos': elementPos})
            sensorListSi[id_csl].update({'name': 'reserved'})
            sensorListSi[id_csl].update({'type_csl': type_csl})

        if type_csl == 5:
            type_csl = 'barometer'
            elementSize = 1
            elementPos = elementPos + elementSize
            sensorListSi[id_csl].update({'pos': elementPos})
            sensorListSi[id_csl].update({'type_csl': type_csl})
            sensorListSi[id_csl].update({'name': config_csl[entry][3]})
            sensorListSi[id_csl].update({'high.min': config_csl[entry][4][0]})
            sensorListSi[id_csl].update({'high.max': config_csl[entry][4][1]})
            sensorListSi[id_csl].update({'high over zero': config_csl[entry][5][1]})
            sensorListSi[id_csl].update({'low.min': config_csl[entry][9][0]})
            sensorListSi[id_csl].update({'low.max': config_csl[entry][9][1]})

        if type_csl == 1:
            type_csl = 'volt'
            if config_csl[entry][3] == 'PICO INTERNAL':
                elementSize = 1
            if 'SPU52' in str(config_csl[entry][3]):
                elementSize = 1
            if 'SPU62' in str(config_csl[entry][3]):
                elementSize = 1
            if 'SC303' in str(config_csl[entry][3]):
                elementSize = 1  # U1 and U2
            if 'SC503' in str(config_csl[entry][3]):
                elementSize = 1  # U1 and U2
            if 'SC301' in str(config_csl[entry][3]):
                elementSize = 1  # U1 and U2
            if 'SCQ25' in str(config_csl[entry][3]):
                elementSize = 1
            if 'SCQ25T' in str(config_csl[entry][3]):
                elementSize = 1
            if 'SCQ50' in str(config_csl[entry][3]):
                elementSize = 1

            elementPos = elementPos + elementSize
            sensorListSi[id_csl].update({'pos': elementPos})
            sensorListSi[id_csl].update({'type_csl': type_csl})
            sensorListSi[id_csl].update({'name': config_csl[entry][3]})
            sensorListSi[id_csl].update({'is 10351 18046': config_csl[entry][4][0]})
            sensorListSi[id_csl].update({'is 32314 224': config_csl[entry][4][1]})
            sensorListSi[id_csl].update({'is 1 2 3 4': config_csl[entry][5][1]})
            sensorListSi[id_csl].update({'is 28 255 36 30': config_csl[entry][6][1]})  # 28 or 255
            sensorListSi[id_csl].update({'current': 'calc'})
            sensorListSi[id_csl].update({'stateOfCharge': 'calc'})
            sensorListSi[id_csl].update({'capacity.C20.Ah': config_csl[entry][5][1]})
            sensorListSi[id_csl].update({'capacity.timeRemaining': 'calc'})
            sensorListSi[id_csl].update({'volt 1506 1547 28066': config_csl[entry][7][0]})
            sensorListSi[id_csl].update({'volt 60868 47887 25761': config_csl[entry][7][1]})
            sensorListSi[id_csl].update({'volt': config_csl[entry][7][1]})

        if type_csl == 22:
            type_csl = '22 SCC8 CamperControl'

            elementSize = 0
            elementPos = elementPos + elementSize
            sensorListSi[id_csl].update({'pos': elementPos})
            sensorListSi[id_csl].update({'type_csl': type_csl})
            sensorListSi[id_csl].update({'name': config_csl[entry][3]})
            sensorListSi[id_csl].update({'val a': config_csl[entry][4][0]})
            sensorListSi[id_csl].update({'val b': config_csl[entry][4][1]})
            sensorListSi[id_csl].update({'Switch.1.on.off': config_csl[entry][5][0]})
            sensorListSi[id_csl].update({'Switch.2.on.off': config_csl[entry][6][0]})
            sensorListSi[id_csl].update({'Switch.3.on.off': config_csl[entry][7][0]})
            sensorListSi[id_csl].update({'Switch.4.on.off': config_csl[entry][8][0]})
            sensorListSi[id_csl].update({'Switch.5.on.off': config_csl[entry][9][0]})
            sensorListSi[id_csl].update({'Switch.6.on.off': config_csl[entry][10][0]})
            sensorListSi[id_csl].update({'Switch.7.on.off': config_csl[entry][11][0]})
            sensorListSi[id_csl].update({'Switch.Main.on.off': config_csl[entry][12][0]})

        if type_csl == 2:
            type_csl = 'current'
            if 'SPU52' in str(config_csl[entry][3]):
                elementSize = 1
            if 'SPU62' in str(config_csl[entry][3]):
                elementSize = 1
            if 'SC303' in str(config_csl[entry][3]):
                elementSize = 1
            if 'SC503' in str(config_csl[entry][3]):
                elementSize = 1  #
            if 'SC301' in str(config_csl[entry][3]):
                elementSize = 1
            if 'SCQ25' in str(config_csl[entry][3]):
                elementSize = 1
            if 'SCQ25T' in str(config_csl[entry][3]):
                elementSize = 1
            if 'SCQ50' in str(config_csl[entry][3]):
                elementSize = 1

            elementPos = elementPos + elementSize
            sensorListSi[id_csl].update({'pos': elementPos})
            sensorListSi[id_csl].update({'type_csl': type_csl})
            sensorListSi[id_csl].update({'name': config_csl[entry][3]})
            sensorListSi[id_csl].update({'current': 'calc'})
            sensorListSi[id_csl].update({'set a': config_csl[entry][4][0]})
            sensorListSi[id_csl].update({'set b': config_csl[entry][4][1]})
            sensorListSi[id_csl].update({'Max Aamp': config_csl[entry][6][1]})
            sensorListSi[id_csl].update({'connected to device': config_csl[entry][10][1]})
            if config_csl[entry][10][1] == 255:
                sensorListSi[id_csl].update({'connected to device': 'not connected'})

        if type_csl == 6:
            type_csl = 'ohm'
            if 'SPU52' in str(config_csl[entry][3]):
                elementSize = 1
            if 'SPU62' in str(config_csl[entry][3]):
                elementSize = 1
            if 'SC303' in str(config_csl[entry][3]):
                elementSize = 1
            if 'SC503' in str(config_csl[entry][3]):
                elementSize = 1
            if 'SC301' in str(config_csl[entry][3]):
                elementSize = 1
            if 'SCQ25' in str(config_csl[entry][3]):
                elementSize = 1
            if 'SCQ25T' in str(config_csl[entry][3]):
                elementSize = 1
            if 'SCQ50' in str(config_csl[entry][3]):
                elementSize = 1

            elementPos = elementPos + elementSize
            sensorListSi[id_csl].update({'pos': elementPos})
            sensorListSi[id_csl].update({'type_csl': type_csl})
            sensorListSi[id_csl].update({'name': config_csl[entry][3]})
            sensorListSi[id_csl].update({'is 18046': config_csl[entry][4][0]})
            sensorListSi[id_csl].update({'is 224': config_csl[entry][4][1]})
            sensorListSi[id_csl].update({'val.8.0': config_csl[entry][8][0]})
            sensorListSi[id_csl].update({'ohm': config_csl[entry][8][1]})

        if type_csl == 25:
            type_csl = '25 reserved'
            elementSize = 0
            elementPos = elementPos + elementSize
            sensorListSi[id_csl].update({'pos': elementPos})
            sensorListSi[id_csl].update({'type_csl': type_csl})
            sensorListSi[id_csl].update({'name': 'unused'})

        if type_csl == 23:
            type_csl = '23 SPU'

            elementSize = 0
            elementPos = elementPos + elementSize
            sensorListSi[id_csl].update({'pos': elementPos})
            sensorListSi[id_csl].update({'type_csl': type_csl})
            sensorListSi[id_csl].update({'name': config_csl[entry][3]})
            sensorListSi[id_csl].update({'val.4.0': config_csl[entry][4][0]})
            sensorListSi[id_csl].update({'val.4.1': config_csl[entry][4][1]})

        if type_csl == 13:
            type_csl = '13 Nick Roll'

            elementSize = 1
            elementPos = elementPos + elementSize
            sensorListSi[id_csl].update({'pos': elementPos})
            sensorListSi[id_csl].update({'type_csl': type_csl})
            sensorListSi[id_csl].update({'name': 'Nick Roll'})

            if config_csl[entry][7][1] == 1:
                sensorListSi[id_csl].update({'Ino Type': 'Boat'})
            if config_csl[entry][7][1] == 2:
                sensorListSi[id_csl].update({'Ino Type': 'Caravan'})

            sensorListSi[id_csl].update({'Calibration min 0': config_csl[entry][8][0]})
            sensorListSi[id_csl].update({'Calibration max 2500': config_csl[entry][8][1]})
            sensorListSi[id_csl].update({'val a': config_csl[entry][11][0]})
            sensorListSi[id_csl].update({'val b': config_csl[entry][11][1]})

        if type_csl == 9:
            type_csl = 'battery'
            elementSize = 1
            elementPos = elementPos + elementSize
            sensorListSi[id_csl].update({'pos': elementPos})
            sensorListSi[id_csl].update({'type_csl': type_csl})

            try:
                sensorListSi[id_csl].update({'name': config_csl[entry][3]})
                sensorListSi[id_csl].update({'capacity.nominal': config_csl[entry][5][1] * 36 * 12})  # In Joule
                sensorListSi[id_csl].update({'capacity.C20.Joule': 'calc'})
                sensorListSi[id_csl].update({'capacity.C20.Ah': 'calc'})
                sensorListSi[id_csl].update({'capacity.C10.Joule': 'calc'})
                sensorListSi[id_csl].update({'capacity.C10.Ah': 'calc'})
                sensorListSi[id_csl].update({'capacity.C05.Joule': 'calc'})
                sensorListSi[id_csl].update({'capacity.C05.Ah': 'calc'})
                sensorListSi[id_csl].update({'battery_type': battery_type[config_csl[entry][8][1]]})
                sensorListSi[id_csl].update({'TempSensor is': config_csl[entry][10][1]})
                sensorListSi[id_csl].update({'stateOfCharge': 'calc'})
                sensorListSi[id_csl].update({'capacity.remaining': 'calc'})
                sensorListSi[id_csl].update({'capacity.timeRemaining': 'calc'})
                sensorListSi[id_csl].update({'TTG.avg': config_csl[entry][13][1]})
                sensorListSi[id_csl].update({'TTG.SOC': (config_csl[entry][14][1] / 10)})
                sensorListSi[id_csl].update({'CEF': (config_csl[entry][15][1] / 10)})
                sensorListSi[id_csl].update({'is.charging': config_csl[entry][16][1]})

            except KeyError:
                print("Something went wrong - battery")
            finally:
                debug("The 'try except' is finished - battery" + str(config_csl[entry][3]))

        if type_csl == 8:
            type_csl = 'tank'
            if 'SCQ25' in str(config_csl[entry][3]):
                elementSize = 1
            if 'SCQ25T' in str(config_csl[entry][3]):
                elementSize = 1
            if 'SCQ50' in str(config_csl[entry][3]):
                elementSize = 1

            elementPos = elementPos + elementSize
            sensorListSi[id_csl].update({'pos': elementPos})
            sensorListSi[id_csl].update({'type_csl': type_csl})

            try:
                sensorListSi[id_csl].update({'name': config_csl[entry][3]})
                sensorListSi[id_csl].update({'currentLevel': 'calc'})
                sensorListSi[id_csl].update({'currentVolume': 'calc'})
                sensorListSi[id_csl].update({'capacity': config_csl[entry][7][1] / 10})
                sensorListSi[id_csl].update({'fluid_type': fluid_type[config_csl[entry][6][1]]})
                sensorListSi[id_csl].update({'fluid': fluid[config_csl[entry][6][1]]})
                sensorListSi[id_csl].update({'ohm.empty': config_csl[entry][8][1]})
                sensorListSi[id_csl].update({'ohm.5% capacity': config_csl[entry][9][0] / 10})
                sensorListSi[id_csl].update({'ohm.5%': config_csl[entry][9][1]})
                sensorListSi[id_csl].update({'ohm.25%.capacity': config_csl[entry][10][0] / 10})
                sensorListSi[id_csl].update({'ohm.25%': config_csl[entry][10][1]})
                sensorListSi[id_csl].update({'ohm.50%.capacity': config_csl[entry][11][0] / 10})
                sensorListSi[id_csl].update({'ohm.50%': config_csl[entry][11][1]})
                sensorListSi[id_csl].update({'ohm.75%.capacity': config_csl[entry][12][0] / 10})
                sensorListSi[id_csl].update({'ohm.75%': config_csl[entry][12][1]})
                sensorListSi[id_csl].update({'ohm.100%.capacity': config_csl[entry][13][0] / 10})
                sensorListSi[id_csl].update({'ohm.100%': config_csl[entry][13][1]})
            except KeyError:
                print("Something went wrong tank:" + config_csl[entry][3])
            finally:
                debug("The 'try except' is finished - tank")

        if type_csl == 3:
            type_csl = 'thermometer'
            if 'SPU52' in str(config_csl[entry][3]):
                elementSize = 1
            if 'SPU62' in str(config_csl[entry][3]):
                elementSize = 1
            if 'SC303' in str(config_csl[entry][3]):
                elementSize = 1
            if 'SC503' in str(config_csl[entry][3]):
                elementSize = 1  # NTC 1
            if 'SC301' in str(config_csl[entry][3]):
                elementSize = 1  # NTC 1
            if 'SCQ25' in str(config_csl[entry][3]):
                elementSize = 1
            if 'SCQ25T' in str(config_csl[entry][3]):
                elementSize = 1
            if 'SCQ50' in str(config_csl[entry][3]):
                elementSize = 1

            elementPos = elementPos + elementSize
            sensorListSi[id_csl].update({'pos': elementPos})
            sensorListSi[id_csl].update({'type_csl': type_csl})

            sensorListSi[id_csl].update({'name': config_csl[entry][3]})
            sensorListSi[id_csl].update({'ntc_type': '' + ntc_type[config_csl[entry][6][1]]})
            sensorListSi[id_csl].update({'Temperature.Calibration': config_csl[entry][7][1] / 100})
            sensorListSi[id_csl].update({'Temperature.Priority': toTemperaturePriority(config_csl[entry][9][1])})
            sensorListSi[id_csl].update({'temperature': 'calc'})
            sensorListSi[id_csl].update({'temperature2': toTemperature(config_csl[entry][10][1])})
            sensorListSi[id_csl].update({'temperature3': toTemperature(config_csl[entry][12][0])})
            sensorListSi[id_csl].update({'temperature4': toTemperature(config_csl[entry][12][1])})
            sensorListSi[id_csl].update({'Temperature.MaxTemp': config_csl[entry][11][1] / 10})

    return sensorListSi


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
debug("Start TCP listener")
# Setup UDP broadcasting listener
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
client.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
client.bind(("", 43210))

# Assign pico address
try:
    message, addr = client.recvfrom(2048)
    picoIp = addr[0]
except KeyboardInterrupt:
    debug("See Pico at KeyboardInterrupt")
finally:
    debug("See Pico at f KeyboardInterrupt")

# picoIp = "192.168.8.146"
debug("See Pico/CC at " + str(picoIp))

global_config: dict[int, dict[Any, Any]] = get_pico_config(picoIp)
debug("CONFIG:")
debug(global_config)

# global_sensorList = {}
global_sensorList = createSensorList(global_config)
debug("SensorList:")
debug(global_sensorList)
print(json.dumps(global_sensorList))

responseB = [''] * 50
responseC = []

old_element = {}


def readVolt(sensorId, elementId, SensorName):
    print("SensorName:" + SensorName)
    elementgo = 19
    if elementId == 8:
        elementgo = 19
    if elementId == 3:
        elementgo = 5
    if elementId == 9:
        elementgo = 20
    if elementId == 10:
        elementgo = 21
    voltage = real_data_element[elementgo][1] / float(1000)
    sensorListTmp[sensorId].update({'voltage': voltage})


def readCurrent(sensorId, elementId, SensorName):
    elementgo = 28
    if elementId == 27:
        elementgo = 28
    if elementId == 4:
        elementgo = 11  # = sensorId
    if elementId == 5:
        elementgo = 12  # = sensorId
    if elementId == 6:
        elementgo = 13  # = sensorId
    if elementId == 7:
        elementgo = 14  # = sensorId
    if elementId == 13:
        elementgo = 15  # = sensorId
    if elementId == 14:
        elementgo = 16  # = sensorId
    print("SensorName:" + SensorName)
    current = real_data_element[elementgo][1]
    if current > 25000:
        current = (65535 - current) / float(100)
    else:
        current = current / float(100) * -1
    sensorListTmp[sensorId].update({'current': current})


def readBaro(sensorId, elementId, SensorName):
    print("SensorName:" + SensorName)
    elementgo = 3
    if elementId == 2:
        elementgo = 3  # = sensorId
    pressure = float((real_data_element[elementgo][1] + 65536) / 100)
    sensorListTmp[sensorId].update({'pressure': pressure})

def readTemp(sensorId, elementId, SensorName):
    print("SensorName:" + SensorName)
    elementgo = 1
    if elementId == 21:
        elementgo = 44   # 15.2
    if elementId == 22:
        elementgo = 45   # 15.2
    if elementId == 23:
        elementgo = 46   # 19.6
    if elementId == 24:
        elementgo = 47   # 17.6
    if elementId == 26:
        elementgo = 44   # 15.2
    if elementId == 46:
        elementgo = 47   # 15.2
    if elementId == 44:
        elementgo = 46   # 19.6
    if elementId == 33:
        elementgo = 65   # 18.6

    print("elementId:" + str(elementgo))
    calibration = sensorListTmp[sensorId]['Temperature.Calibration']
    tempval2calc = real_data_element[elementgo][1]
    # temperature = toTemperature(tempval2calc) - calibration
    temperature = float(real_data_element[elementgo][1] / 10)
    sensorListTmp[sensorId].update({'temperature': temperature})


def readTank(sensorId, elementId, SensorName):
    print("SensorName:" + SensorName)
    # is 32 and 33
    elementgo = 35
    if elementId == 34:
        elementgo = 34
    if elementId == 29:
        elementgo = 35
    currentLevel = real_data_element[elementgo][0] / float(10)
    currentVolume = real_data_element[elementgo][1] / float(10)
    sensorListTmp[sensorId].update({'currentLevel': currentLevel})
    sensorListTmp[sensorId].update({'currentVolume': currentVolume})


def readOhm(sensorId, elementId, SensorName):
    print("SensorName:" + SensorName)
    elementgo = 1
    if elementId == 12:
        elementgo = 23
    if elementId == 13:
        elementgo = 24
    if elementId == 14:
        elementgo = 25
    if elementId == 15:
        elementgo = 26
    if elementId == 30:
        elementgo = 62
    if elementId == 31:
        elementgo = 63
    if elementId == 32:
        elementgo = 64
    ohm = real_data_element[elementgo][1]
    sensorListTmp[sensorId].update({'ohm': ohm})

def readSolarPower(sensorId, elementId, SensorName):
    print("SensorName:" + SensorName)
    elementgo = 22
    if elementId == 1:
        elementgo = 22

    sensorListTmp[sensorId].update({'currentAmp': real_data_element[elementgo][0] / float(1000)})
    sensorListTmp[sensorId].update({'currentVolt': real_data_element[elementgo][1] / float(10000)})


# above ok for my individual setup


def readBatt(sensorId, elementId, SensorName):
    print("SensorName:" + SensorName)
    elementgo = 18
    if elementId == 20:
        elementgo = 18
    if elementId == 25:
        elementgo = 3

    stateOfCharge = float("%.2f" % (real_data_element[elementgo][0] / 16000.0))
    sensorListTmp[sensorId].update({'stateOfCharge': stateOfCharge})
    sensorListTmp[sensorId].update({'capacity.remaining': real_data_element[elementgo][1] * stateOfCharge})
    sensorListTmp[sensorId].update({'voltage': real_data_element[elementgo + 2][1] / float(1000)})
    current = real_data_element[elementgo + 1][1]
    if current > 25000:
        current = (65535 - current) / float(100)
    else:
        current = current / float(100) * -1
    sensorListTmp[sensorId].update({'current': current})
    stateOfCharge = float("%.2f" % (real_data_element[elementgo][0] / 16000.0))
    if real_data_element[elementgo][0] != 65535:
        timeRemaining = round(
            (global_sensorList[sensorId]['capacity.nominal']) / 12 / ((current * stateOfCharge) + 0.001))
        if timeRemaining < 0:
            timeRemaining = 60 * 60 * 24 * 7  # One week
        sensorListTmp[sensorId].update({'capacity.timeRemaining': timeRemaining})


while True:
    updates = []
    sensorListTmp: dict[Any, dict[Any, Any]] = copy.deepcopy(global_sensorList)
    pos = 0
    message = ''
    while True:
        pos = pos + 1
        message, addr = client.recvfrom(2048)
        debug("Received packet with length " + str(len(message)))
        if 100 < len(message) < 2048:
            break

    global_response = BinToHex(message)

    debug("response: " + global_response)

    if global_response[18] == 'b':
        if len(global_response) == 0:
            continue
        else:
            pos = 0

    real_data_element = parseResponseS2(global_response, pos)
    # real_data_element =
    # {0: [25615, 43879], 1: [25615, 47479], 2: [65535, 64534], 3: [1, 31679], 4: [0, 153], 5: [0, 12114],
    # 9: [25606, 10664], 10: [65535, 64534], 11: [65535, 64980], 12: [0, 5875], 13: [0, 12672], 14: [0, 0], 15: [0,
    # 65535], 16: [0, 65535], 17: [0, 65535], 18: [65535, 65520], 19: [65531, 34426], 20: [0, 0], 21: [0, 16],
    # 22: [65535, 65535], 23: [65535, 65450], 24: [65535, 65048], 25: [65515, 983], 26: [0, 0], 27: [0, 0], 28: [0,
    # 0], 29: [0, 65535], 30: [0, 65535], 31: [0, 65535], 32: [0, 65535], 33: [0, 0], 34: [65535, 65532], 35: [0,
    # 18386], 36: [0, 26940], 37: [0, 0], 38: [0, 65535], 39: [0, 65535], 40: [0, 65535], 41: [0, 0], 42: [65529,
    # 51037], 43: [65535, 65529], 44: [4, 9403], 45: [0, 0], 46: [65533, 6493], 47: [0, 0], 48: [65535, 18413],
    # 49: [0, 0], 50: [15776, 53404], 51: [65535, 64980], 52: [0, 12672], 53: [32767, 65535], 54: [65531, 42226],
    # 55: [15984, 17996], 56: [65535, 65532], 57: [0, 26940], 58: [32767, 65535], 59: [65253, 37546], 60: [0, 0],
    # 61: [0, 0], 62: [0, 0], 63: [0, 54], 64: [0, 57], 65: [0, 65535], 66: [0, 44], 67: [0, 0], 68: [282, 2829],
    # 69: [5, 58], 70: [300, 3000]}
    debug(real_data_element)
    for diff in list(dictdiffer.diff(old_element, real_data_element)):
        print(diff)
    old_element = copy.deepcopy(real_data_element)

    # Add values to global_sensorList copy

    for deviceSensor in global_sensorList:
        sensorLiveData = global_sensorList[deviceSensor]['pos']
        itemType = global_sensorList[deviceSensor]['type_csl']
        itemName = global_sensorList[deviceSensor]['name']

        print('global_sensorList[' + str(deviceSensor) + '] pos[' + str(sensorLiveData) + '] name:[' + str(
            itemName) + ']' + 'itemType:[' + str(itemType) + ']')

        if itemType == 'SolarPower':
            readSolarPower(deviceSensor, sensorLiveData, itemName)
        if itemType == 'barometer':
            readBaro(deviceSensor, sensorLiveData, itemName)
        if itemType == 'current':
            readCurrent(deviceSensor, sensorLiveData, itemName)
        if itemType == 'ohm':
            readOhm(deviceSensor, sensorLiveData, itemName)
        if itemType == 'battery':
            readBatt(deviceSensor, sensorLiveData, itemName)
        if itemType == 'tank':
            readTank(deviceSensor, sensorLiveData, itemName)
        if itemType == 'thermometer':
            readTemp(deviceSensor, sensorLiveData, itemName)
        if itemType == 'volt':
            readVolt(deviceSensor, sensorLiveData, itemName)

    print(json.dumps(sensorListTmp))

    sys.stdout.flush()
    time.sleep(0.9)
    empty_socket_has_exit(client, 'End of Application')
