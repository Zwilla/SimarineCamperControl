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


def getNextField(response_gnf):
    debug("field_nr: " + response_gnf[0:2])
    field_nr = int(response_gnf[0:2], 16)
    debug("field_type: " + response_gnf[3:6])
    field_type = int(response_gnf[3:5], 16)
    if field_type == 1:
        debug(response_gnf)
        debug("a: " + response_gnf[6:11].replace(' ', ''))
        debug("b: " + response_gnf[12:17].replace(' ', ''))
        data = response_gnf[6:17]
        debug("data: " + data)
        response_gnf = response_gnf[21:]
        # if (data[0:11] == '7f ff ff ff'):
        # return field_nr, '', response_pr
        # else:
        a = int(data[0:5].replace(' ', ''), 16)
        b = int(data[6:11].replace(' ', ''), 16)
        # field_data = [a, b, data]
        field_data = [a, b]
        return field_nr, field_data, response_gnf
    if field_type == 3:
        debug(response_gnf)
        debug("a: " + response_gnf[21:27].replace(' ', ''))
        debug("b: " + response_gnf[27:32].replace(' ', ''))
        data = response_gnf[21:32]
        debug("data: " + data)
        response_gnf = response_gnf[36:]
        if data[0:11] == '7f ff ff ff':
            return field_nr, '', response_gnf
        else:
            a = int(data[0:5].replace(' ', ''), 16)
            b = int(data[6:11].replace(' ', ''), 16)
            # field_data = [a, b, data]
            field_data = [a, b]
            return field_nr, field_data, response_gnf
    if field_type == 4:  # Text string
        # Strip first part
        response_gnf = response_gnf[21:]
        nextHex = response_gnf[0:2]
        word = ''
        while nextHex != '00':
            word += nextHex
            response_gnf = response_gnf[3:]
            nextHex = response_gnf[0:2]
        word = HexToByte(word)
        debug("Word: " + word)
        response_gnf = response_gnf[6:]  # Strip seperator
        return field_nr, word, response_gnf
    debug("Unknown field type " + str(field_type))


def parseResponse(response_pr):
    dictSi = {}
    # strip header
    response_pr = response_pr[42:]

    while len(response_pr) > 6:
        field_nr, field_data, response_pr = getNextField(response_pr)
        # debug(str(field_nr) + " " + field_data)
        debug(str(field_nr))
        debug(response_pr + " " + str(len(response_pr)))
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
    config_gpc = {}
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
        for posSi in range(req_count):
            messageSi = (
                    '00 00 00 00 00 ff 41 04 8c 55 4b 00 16 ff 00 01 00 00 00 ' + "%02x" % posSi + ' ff 01 03 00 00 00 00 ff 00 00 00 00 ff')
            messageSi = add_crc(messageSi)
            response_gpc = send_receive(messageSi)
            elementSi = parseResponse(response_gpc)
            config_gpc[posSi] = elementSi

    except KeyError:
        sys.stdout.flush()
        time.sleep(0.9)
        empty_socket_has_exit(client, 'get_pico_config')
    finally:
        # Close tcp connection
        s.close()

    return config_gpc


def toTemperature(temp):
    # Unsigned to signed
    if temp > 32768:
        temp = temp - 65536
    temp2 = float(("%.2f" % round(temp / float(10) + 273.15, 2)))
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

        if type_csl == 0:
            type_csl = 'reserved 0.0'
            elementSize = 2

        if type_csl == 1:
            type_csl = 'volt'
            if config_csl[entry][3] == 'PICO INTERNAL':
                elementSize = 7
            sensorListSi[id_csl].update({'name': config_csl[entry][3]})
            sensorListSi[id_csl].update({'is 10351': config_csl[entry][4][0]})
            sensorListSi[id_csl].update({'is 32314': config_csl[entry][4][1]})
            sensorListSi[id_csl].update({'is id_csl': config_csl[entry][5][1]})
            sensorListSi[id_csl].update({'is 28': config_csl[entry][6][1]})  # 28 or 255
            sensorListSi[id_csl].update({'volt a': config_csl[entry][7][0] / float(1000)})
            sensorListSi[id_csl].update({'volt b': config_csl[entry][7][1] / float(1000)})
            elementSize = 7

        if type_csl == 2:
            type_csl = 'current'
            sensorListSi[id_csl].update({'name': config_csl[entry][3]})
            sensorListSi[id_csl].update({'set a': config_csl[entry][4][0]})
            sensorListSi[id_csl].update({'set b': config_csl[entry][4][1]})
            sensorListSi[id_csl].update({'Max Aamp': config_csl[entry][6][1]})
            if config_csl[entry][12][0] > 25000:
                current = (65535 - config_csl[entry][12][0]) / float(100)
            else:
                current = config_csl[entry][12][0] / float(100) * -1

            sensorListSi[id_csl].update({'current a': current})

            if config_csl[entry][12][1] > 25000:
                current = (65535 - config_csl[entry][12][1]) / float(100)
            else:
                current = config_csl[entry][12][1] / float(100) * -1

            sensorListSi[id_csl].update({'current b': current})

            sensorListSi[id_csl].update({'connected to device': config_csl[entry][10][1]})
            if config_csl[entry][10][1] == 255:
                sensorListSi[id_csl].update({'connected to device': 'not connected'})
            elementSize = 13

        if type_csl == 3:
            type_csl = 'thermometer'
            sensorListSi[id_csl].update({'name': config_csl[entry][3]})
            sensorListSi[id_csl].update({'ntc_type': '' + ntc_type[config_csl[entry][6][1]]})
            sensorListSi[id_csl].update({'Temperature.Calibration': config_csl[entry][7][1] / 100})
            sensorListSi[id_csl].update({'Temperature.Priority': toTemperaturePriority(config_csl[entry][9][1])})
            sensorListSi[id_csl].update({'temperature': toTemperature(config_csl[entry][10][0])})
            sensorListSi[id_csl].update({'temperature2': toTemperature(config_csl[entry][10][1])})
            sensorListSi[id_csl].update({'temperature3': toTemperature(config_csl[entry][12][0])})
            sensorListSi[id_csl].update({'temperature4': toTemperature(config_csl[entry][12][1])})
            sensorListSi[id_csl].update({'Temperature.MaxTemp': config_csl[entry][11][1] / 10})
            elementSize = 12

        if type_csl == 4:
            type_csl = 'SolarPower'
            sensorListSi[id_csl].update({'name': config_csl[entry][3]})
            sensorListSi[id_csl].update({'val.4.0': config_csl[entry][4][0]})
            sensorListSi[id_csl].update({'val.4.1': config_csl[entry][4][1]})
            sensorListSi[id_csl].update({'Amp Input': config_csl[entry][8][1]})
            if config_csl[entry][8][1] == 255:
                sensorListSi[id_csl].update({'Amp Input': 'no Input'})
            sensorListSi[id_csl].update({'val.9.0': config_csl[entry][9][0]})
            sensorListSi[id_csl].update({'val.9.1': config_csl[entry][9][1]})
            elementSize = 10

        if type_csl == 5:
            type_csl = 'barometer'
            sensorListSi[id_csl].update({'name': config_csl[entry][3]})
            sensorListSi[id_csl].update({'pressure': config_csl[entry][5][1] + 65536})
            sensorListSi[id_csl].update({'high.min': config_csl[entry][4][0] + 65536})
            sensorListSi[id_csl].update({'high.max': config_csl[entry][4][1] + 65536})
            sensorListSi[id_csl].update({'high over zero': config_csl[entry][5][1]})
            sensorListSi[id_csl].update({'low.min': config_csl[entry][9][0] + 65536})
            sensorListSi[id_csl].update({'low.max': config_csl[entry][9][1] + 65536})
            elementSize = 10

        if type_csl == 6:
            type_csl = 'ohm'
            sensorListSi[id_csl].update({'name': config_csl[entry][3]})
            sensorListSi[id_csl].update({'is 18046': config_csl[entry][4][0]})
            sensorListSi[id_csl].update({'is 224': config_csl[entry][4][1]})
            sensorListSi[id_csl].update({'val.8.0': config_csl[entry][8][0]})
            sensorListSi[id_csl].update({'val.8.1': config_csl[entry][8][1]})
            elementSize = 9

        if type_csl == 7:
            type_csl = '07 XX'
            sensorListSi[id_csl].update({'val 1': config_csl[entry][3][0]})
            sensorListSi[id_csl].update({'val 2': config_csl[entry][3][1]})
            sensorListSi[id_csl].update({'val 7200': config_csl[entry][4][1]})
            sensorListSi[id_csl].update({'val 5': config_csl[entry][3][0]})
            sensorListSi[id_csl].update({'val 3': config_csl[entry][7][0]})
            sensorListSi[id_csl].update({'val 4': config_csl[entry][7][1]})
            elementSize = 8

        if type_csl == 8:
            type_csl = 'tank'
            elementSize = 23
            try:
                sensorListSi[id_csl].update({'name': config_csl[entry][3]})
                sensorListSi[id_csl].update({'currentLevel': config_csl[entry][4][0] / float(1000)})
                sensorListSi[id_csl].update({'currentVolume': config_csl[entry][4][1] / float(10000)})
                sensorListSi[id_csl].update({'capacity': config_csl[entry][7][1] / 10})
                sensorListSi[id_csl].update({'fluid_type': fluid_type[config_csl[entry][6][1]]})
                sensorListSi[id_csl].update({'fluid': fluid[config_csl[entry][6][1]]})
                sensorListSi[id_csl].update({'ohm.empty': config_csl[entry][8][1]})
                sensorListSi[id_csl].update({'ohm.5% capacity': config_csl[entry][9][0]})
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

        if type_csl == 9:
            type_csl = 'battery'
            try:
                sensorListSi[id_csl].update({'name': config_csl[entry][3]})
                sensorListSi[id_csl].update({'capacity.C20.Joule': config_csl[entry][5][1] * 36 * 12})  # In Joule
                sensorListSi[id_csl].update({'capacity.C20.Ah': config_csl[entry][5][1] / 100})
                sensorListSi[id_csl].update({'capacity.C10.Joule': config_csl[entry][6][1] * 36 * 12})  # In Joule
                sensorListSi[id_csl].update({'capacity.C10.Ah': config_csl[entry][6][1] / 100})
                sensorListSi[id_csl].update({'capacity.C05.Joule': config_csl[entry][7][1] * 36 * 12})  # In Joule
                sensorListSi[id_csl].update({'capacity.C05.Ah': config_csl[entry][7][1] / 100})
                sensorListSi[id_csl].update({'battery_type': battery_type[config_csl[entry][8][1]]})
                sensorListSi[id_csl].update({'TempSensor is': config_csl[entry][10][1]})
                sensorListSi[id_csl].update({'stateOfCharge': float("%.2f" % (config_csl[entry][12][0] / 16000.0))})
                sensorListSi[id_csl].update(
                    {'capacity.remaining': config_csl[entry][12][1] * float("%.2f" % (config_csl[entry][12][0] / 16000.0))})
                sensorListSi[id_csl].update({'TTG.avg': config_csl[entry][13][1]})
                sensorListSi[id_csl].update({'TTG.SOC': (config_csl[entry][14][1] / 10)})
                sensorListSi[id_csl].update({'CEF': (config_csl[entry][15][1] / 10)})
                sensorListSi[id_csl].update({'is.charging': config_csl[entry][16][1]})

            except KeyError:
                print("Something went wrong - battery")
            finally:
                debug("The 'try except' is finished - battery" + config_csl[entry][3])
                elementSize = 18

        if type_csl == 10:
            type_csl = '10 System'
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
            elementSize = 30

        if type_csl == 13:
            type_csl = '13 Nick Roll'
            if config_csl[entry][7][1] == 1:
                sensorListSi[id_csl].update({'Ino Type': 'Boat'})
            if config_csl[entry][7][1] == 2:
                sensorListSi[id_csl].update({'Ino Type': 'Caravan'})
            sensorListSi[id_csl].update({'Calibration min 0': config_csl[entry][8][0]})
            sensorListSi[id_csl].update({'Calibration max 2500': config_csl[entry][8][1]})
            sensorListSi[id_csl].update({'val a': config_csl[entry][11][0]})
            sensorListSi[id_csl].update({'val b': config_csl[entry][11][1]})
            elementSize = 12

        if type_csl == 22:
            type_csl = '22 SCC8 CamperControl'
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
            elementSize = 13

        if type_csl == 23:
            type_csl = '23 SPU'
            sensorListSi[id_csl].update({'name': config_csl[entry][3]})
            sensorListSi[id_csl].update({'val.4.0': config_csl[entry][4][0]})
            sensorListSi[id_csl].update({'val.4.1': config_csl[entry][4][1]})
            elementSize = 17

        if type_csl == 25:
            type_csl = '25 reserved'
            elementSize = 2

        sensorListSi[id_csl].update({'type_csl': type_csl, 'pos': elementPos})
        elementPos = elementPos + elementSize
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
except KeyboardInterrupt:
    debug("See Pico at KeyboardInterrupt")
finally:
    debug("See Pico at f KeyboardInterrupt")

# picoIp_ot = addr[0]
picoIp = "192.168.8.146"
debug("See Pico/CC at " + str(picoIp))

config: dict[int, dict[Any, Any]] = get_pico_config(picoIp)
debug("CONFIG:")
debug(config)

# sensorList = {}
sensorList = createSensorList(config)
debug("SensorList:")
debug(sensorList)
print(json.dumps(sensorList))

responseB = [''] * 50
responseC = []

old_element = {}


def readBaro(sensorId, elementId):
    sensorListTmp[sensorId].update({'pressure': element[elementId][1] + 65536})


def readVolt(sensorId, elementId):
    try:
        sensorListTmp[sensorId].update({'volt': element[elementId][1] / float(1000)})
        current = element[elementId + 1][1]
        if current > 25000:
            current = (65535 - current) / float(100)
        else:
            current = current / float(100) * -1

        sensorListTmp[sensorId].update({'current': current})
        stateOfCharge = float("%.2f" % (element[elementId][0] / 16000.0))

        if element[elementId][0] != 65535:
            timeRemaining = round(sensorList[sensorId]['capacity.C20.Ah'] / 12 / ((current * stateOfCharge) + 0.001))
            if timeRemaining < 0:
                timeRemaining = 60 * 60 * 24 * 7  # One week
            sensorListTmp[sensorId].update({'capacity.timeRemaining': timeRemaining})
    except KeyError:
        print("Something went wrong readVolt " + str(sensorId))
    finally:
        debug("The 'try except' is finished readVolt")


def readOhm(sensorId, elementId):
    try:
        sensorListTmp[sensorId].update({'ohm': element[elementId][1]})
    except KeyError:
        print("Something went wrong readOhm " + str(sensorId))
    finally:
        debug("The 'try except' is finished readOhm")


while True:
    updates = []
    sensorListTmp: dict[Any, dict[Any, Any]] = copy.deepcopy(sensorList)

    message = ''
    while True:
        message, addr = client.recvfrom(2048)
        debug("Received packet with length " + str(len(message)))
        if 100 < len(message) < 2048:
            break

    responseSi = BinToHex(message)

    debug("response: " + responseSi)

    if responseSi[18] == 'b':
        if len(responseSi) == 0:
            continue
        else:
            pos = 0

    element = parseResponse(responseSi)
    # element = {0: [25615, 43879], 1: [25615, 47479], 2: [65535, 64534], 3: [1, 31679], 4: [0, 153], 5: [0, 12114],
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
    debug(element)
    for diff in list(dictdiffer.diff(old_element, element)):
        debug(diff)
    old_element = copy.deepcopy(element)

    # Add values to sensorList copy

    for item in sensorList:
        # debug("sensorList[" + str(item) + "]: " + sensorList[item]["name"])
        elId = sensorList[item]['pos']
        itemType = sensorList[item]['type_csl']

        if itemType == 'barometer':
            readBaro(item, elId)
        if itemType == 'ohm':
            readOhm(item, elId)
        if itemType == 'volt':
            readVolt(item, elId)

    print(json.dumps(sensorListTmp))

    sys.stdout.flush()
    time.sleep(0.9)
    empty_socket_has_exit(client, 'End of Application')
