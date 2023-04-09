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
        if os.environ['DEBUG'] == 'pico':
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


def BinToHex(messageSi):
    responseSI = ''
    for x in messageSi:
        hexy = format(x, '02x')
        responseSI = responseSI + hexy + ' '
    return responseSI


def parse(messageSi):
    values = messageSi.split(' ff')
    values = striplist(values)
    return values


def getNextField(responseSi):
    debug("field_nr: " + responseSi[0:2])
    field_nr = int(responseSi[0:2], 16)
    debug("field_type: " + responseSi[3:6])
    field_type = int(responseSi[3:5], 16)
    if field_type == 1:
        debug(responseSi)
        debug("a: " + responseSi[6:11].replace(' ', ''))
        debug("b: " + responseSi[12:17].replace(' ', ''))
        data = responseSi[6:17]
        debug("data: " + data)
        responseSi = responseSi[21:]
        # if (data[0:11] == '7f ff ff ff'):
        # return field_nr, '', responseSi
        # else:
        a = int(data[0:5].replace(' ', ''), 16)
        b = int(data[6:11].replace(' ', ''), 16)
        # field_data = [a, b, data]
        field_data = [a, b]
        return field_nr, field_data, responseSi
    if field_type == 3:
        debug(responseSi)
        debug("a: " + responseSi[21:27].replace(' ', ''))
        debug("b: " + responseSi[27:32].replace(' ', ''))
        data = responseSi[21:32]
        debug("data: " + data)
        responseSi = responseSi[36:]
        if data[0:11] == '7f ff ff ff':
            return field_nr, '', responseSi
        else:
            a = int(data[0:5].replace(' ', ''), 16)
            b = int(data[6:11].replace(' ', ''), 16)
            # field_data = [a, b, data]
            field_data = [a, b]
            return field_nr, field_data, responseSi
    if field_type == 4:  # Text string
        # Strip first part
        responseSi = responseSi[21:]
        nextHex = responseSi[0:2]
        word = ''
        while nextHex != '00':
            word += nextHex
            responseSi = responseSi[3:]
            nextHex = responseSi[0:2]
        word = HexToByte(word)
        debug("Word: " + word)
        responseSi = responseSi[6:]  # Strip seperator
        return field_nr, word, responseSi
    debug("Unknown field type " + str(field_type))


def parseResponse(responseSi):
    dictSi = {}
    # strip header
    responseSi = responseSi[42:]

    while len(responseSi) > 6:
        field_nr, field_data, responseSi = getNextField(responseSi)
        # debug(str(field_nr) + " " + field_data)
        debug(str(field_nr))
        debug(responseSi + " " + str(len(responseSi)))
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
    responseSi = ''
    hexSi = ''

    try:
        s.sendall(messageSi)
        for x in s.recv(2048):
            hexSi = format(x, '02x')
            responseSi = responseSi + hexSi + ' '
            debug('Response: ' + responseSi)
    except:
        sys.stdout.flush()
        time.sleep(0.9)
        empty_socket_has_exit(client, 'send_receive')
    finally:
        debug("The 'try except' is finished - send_receive")

    return responseSi


def open_tcp(picoIp):
    try:
        # Create a TCP stream socket with address family of IPv4 (INET)
        serverport = 5001
        # Connect to the server at given IP and port
        s.connect((picoIp, serverport))
        return
    except BrokenPipeError:
        debug("Connection to " + str(picoIp) + ":5001 failed. Retrying in 1 sec.")
        time.sleep(5)
        # try again
        return open_tcp(picoIp)
    finally:
        debug("The show must go on")


def get_pico_config(pico_ip_get):
    config = {}
    open_tcp(pico_ip_get)
    response_list = []
    messageSi = '00 00 00 00 00 ff 02 04 8c 55 4b 00 03 ff'
    messageSi = add_crc(messageSi)

    req_count = int(0 + 1)
    # Response: 00 00 00 00 00 ff 02 04 8c 55 4b 00 11 ff 01 01 00 00 00 1e ff 02 01 00 00 00 30 ff 32 cf
    try:
        responseSi = send_receive(messageSi)
        req_count = int(responseSi.split()[19], 16) + 1
        debug("req_count: " + str(req_count))
        for posSi in range(req_count):
            messageSi = (
                    '00 00 00 00 00 ff 41 04 8c 55 4b 00 16 ff 00 01 00 00 00 ' + "%02x" % posSi + ' ff 01 03 00 00 00 00 ff 00 00 00 00 ff')
            messageSi = add_crc(messageSi)
            responseSi = send_receive(messageSi)
            elementSi = parseResponse(responseSi)
            config[posSi] = elementSi

    except KeyError:
        sys.stdout.flush()
        time.sleep(0.9)
        empty_socket_has_exit(client, 'get_pico_config')
    finally:
        # Close tcp connection
        s.close()

    return config


def toTemperature(temp):
    # Unsigned to signed
    if temp > 32768:
        temp = temp - 65536
    temp2 = float(("%.2f" % round(temp / float(10) + 273.15, 2)))
    return temp2


def createSensorList(config):
    sensorListSi = {}
    fluid = ['Unknown', 'freshWater', 'fuel', 'wasteWater']
    fluid_type = ['Unknown', 'fresh water', 'diesel', 'blackwater']
    elementPos = 0

    for entry in config.keys():
        debug(config[entry])
        # Set id
        id = config[entry][0][1]
        # Set type
        type = config[entry][1][1]
        # Default elementsize
        elementSize = 1
        sensorListSi[id] = {}

        if type == 0:
            type = 'reserved 0.0'
            elementSize = 2

        if type == 1:
            type = 'volt'
            if config[entry][3] == 'PICO INTERNAL':
                elementSize = 7
            sensorListSi[id].update({'name': config[entry][3]})
            sensorListSi[id].update({'volt': config[entry][4][0]})
            sensorListSi[id].update({'volt max': config[entry][4][1]})
            sensorListSi[id].update({'set a': config[entry][5][1]})
            sensorListSi[id].update({'set b': config[entry][6][1]})
            sensorListSi[id].update({'amp a': config[entry][7][0]})
            sensorListSi[id].update({'amp b': config[entry][7][1]})
            elementSize = 7

        if type == 2:
            type = 'current'
            sensorListSi[id].update({'name': config[entry][3]})
            sensorListSi[id].update({'set a': config[entry][4][0]})
            sensorListSi[id].update({'set b': config[entry][4][1]})
            sensorListSi[id].update({'Max Aamp': config[entry][6][0]})
            sensorListSi[id].update({'set 35': config[entry][10][0]})
            sensorListSi[id].update({'set c': config[entry][12][0]})
            sensorListSi[id].update({'set d': config[entry][12][1]})
            elementSize = 13

        if type == 3:
            type = 'thermometer'
            sensorListSi[id].update({'name': config[entry][3]})
            sensorListSi[id].update({'Temperature.NTC.Type': config[entry][6][1]})  # 1=NTC10k 2=NTC5k
            sensorListSi[id].update({'Temperature.Calibration': config[entry][7][1] / 100})
            sensorListSi[id].update({'Temperature.Priority': config[entry][9][1]})  # 1=high 3=Low
            sensorListSi[id].update({'Temperature.MaxTemp': config[entry][11][1] / 10})
            elementSize = 12

        if type == 4:
            type = '04 Sensor'
            sensorListSi[id].update({'name': config[entry][3]})
            sensorListSi[id].update({'val.4.0': config[entry][4][0]})
            sensorListSi[id].update({'val.4.1': config[entry][4][1]})
            sensorListSi[id].update({'val.9.0': config[entry][9][0]})
            sensorListSi[id].update({'val.9.1': config[entry][9][1]})
            elementSize = 10

        if type == 5:
            type = 'barometer'
            sensorListSi[id].update({'name': config[entry][3]})
            sensorListSi[id].update({'pressure': config[entry][5][1]})
            sensorListSi[id].update({'high.min': config[entry][4][0]})
            sensorListSi[id].update({'high.max': config[entry][4][1]})
            sensorListSi[id].update({'low.min': config[entry][9][0]})
            sensorListSi[id].update({'low.max': config[entry][9][1]})
            elementSize = 10

        if type == 6:
            type = 'ohm'
            sensorListSi[id].update({'name': config[entry][3]})
            sensorListSi[id].update({'val.4.0': config[entry][4][0]})
            sensorListSi[id].update({'val.4.1': config[entry][4][1]})
            sensorListSi[id].update({'val.8.0': config[entry][8][0]})
            sensorListSi[id].update({'val.8.1': config[entry][8][1]})
            elementSize = 9

        if type == 7:
            type = '07 XX'
            sensorListSi[id].update({'val 1': config[entry][3][0]})
            sensorListSi[id].update({'val 2': config[entry][3][1]})
            sensorListSi[id].update({'val 7200': config[entry][4][1]})
            sensorListSi[id].update({'val 5': config[entry][3][0]})
            sensorListSi[id].update({'val 3': config[entry][7][0]})
            sensorListSi[id].update({'val 4': config[entry][7][1]})
            elementSize = 8

        if type == 8:
            type = 'tank'
            elementSize = 23
            try:
                sensorListSi[id].update({'name': config[entry][3]})
                sensorListSi[id].update({'capacity': config[entry][7][1] / 10})
                sensorListSi[id].update({'fluid_type': fluid_type[config[entry][6][1]]})
                sensorListSi[id].update({'fluid': fluid[config[entry][6][1]]})
                sensorListSi[id].update({'ohm.empty': config[entry][8][1]})
                sensorListSi[id].update({'ohm.5% capacity': config[entry][9][0]})
                sensorListSi[id].update({'ohm.5%': config[entry][9][1]})
                sensorListSi[id].update({'ohm.25%.capacity': config[entry][10][0] / 10})
                sensorListSi[id].update({'ohm.25%': config[entry][10][1]})
                sensorListSi[id].update({'ohm.50%.capacity': config[entry][11][0] / 10})
                sensorListSi[id].update({'ohm.50%': config[entry][11][1]})
                sensorListSi[id].update({'ohm.75%.capacity': config[entry][12][0] / 10})
                sensorListSi[id].update({'ohm.75%': config[entry][12][1]})
                sensorListSi[id].update({'ohm.100%.capacity': config[entry][13][0] / 10})
                sensorListSi[id].update({'ohm.100%': config[entry][13][1]})
            except KeyError:
                print("Something went wrong tank:" + config[entry][3])
            finally:
                debug("The 'try except' is finished - tank")

        if type == 9:
            type = 'battery'
            try:
                sensorListSi[id].update({'name': config[entry][3]})
                sensorListSi[id].update({'capacity.C20.Joule': config[entry][5][1] * 36 * 12})  # In Joule
                sensorListSi[id].update({'capacity.C20.Ah': config[entry][5][1] / 100})
                sensorListSi[id].update({'capacity.C10.Joule': config[entry][6][1] * 36 * 12})  # In Joule
                sensorListSi[id].update({'capacity.C10.Ah': config[entry][6][1] / 100})
                sensorListSi[id].update({'capacity.C05.Joule': config[entry][7][1] * 36 * 12})  # In Joule
                sensorListSi[id].update({'capacity.C05.Ah': config[entry][7][1] / 100})
                if config[entry][8][1] == 1:
                    sensorListSi[id].update({'Battery.Type': 'Nass Wartungsarm standard'})
                if config[entry][8][1] == 2:
                    sensorListSi[id].update({'Battery.Type': 'Nass Wartungsfrei'})
                if config[entry][8][1] == 3:
                    sensorListSi[id].update({'Battery.Type': 'AGM'})
                if config[entry][8][1] == 4:
                    sensorListSi[id].update({'Battery.Type': 'Tiefzyklus'})
                if config[entry][8][1] == 5:
                    sensorListSi[id].update({'Battery.Type': 'Gel'})
                if config[entry][8][1] == 6:
                    sensorListSi[id].update({'Battery.Type': 'LiFePo4'})
                sensorListSi[id].update({'TTG.avg': config[entry][13][1]})
                sensorListSi[id].update({'TTG.SOC': (config[entry][14][1] / 10)})
                sensorListSi[id].update({'CEF': (config[entry][15][1] / 10)})
                sensorListSi[id].update({'is.charging': config[entry][16][1]})

            except KeyError:
                print("Something went wrong - tank")
            finally:
                debug("The 'try except' is finished - tank" + config[entry][3])
                elementSize = 18

        if type == 10:
            type = '10 System'
            sensorListSi[id].update({'name': config[entry][10]})
            sensorListSi[id].update({'name2': config[entry][15]})
            sensorListSi[id].update({'val 3.0': config[entry][3][0]})
            sensorListSi[id].update({'val 3.1': config[entry][3][1]})
            sensorListSi[id].update({'val 11.0': config[entry][11][0]})
            sensorListSi[id].update({'val 11.1': config[entry][11][1]})
            sensorListSi[id].update({'Port': config[entry][12][1]})
            sensorListSi[id].update({'val 13.0': config[entry][13][0]})
            sensorListSi[id].update({'val 13.1': config[entry][13][1]})
            sensorListSi[id].update({'val 14.0': config[entry][14][0]})
            sensorListSi[id].update({'val 14.1': config[entry][14][1]})
            sensorListSi[id].update({'val 29.0': config[entry][29][0]})
            sensorListSi[id].update({'val 29.1': config[entry][29][1]})
            elementSize = 30

        if type == 13:
            type = '13 Nick Roll'
            sensorListSi[id].update({'val 127': config[entry][5][1]})
            sensorListSi[id].update({'val 2500': config[entry][8][1]})
            sensorListSi[id].update({'val 11.0': config[entry][11][0]})
            sensorListSi[id].update({'val 11.1': config[entry][11][1]})
            elementSize = 12

        if type == 22:
            type = '22 SCC8 CamperControl'
            sensorListSi[id].update({'name': config[entry][3]})
            sensorListSi[id].update({'val a': config[entry][4][0]})
            sensorListSi[id].update({'val b': config[entry][4][1]})
            sensorListSi[id].update({'Switch.1.on.off': config[entry][5][0]})
            sensorListSi[id].update({'Switch.2.on.off': config[entry][6][0]})
            sensorListSi[id].update({'Switch.3.on.off': config[entry][7][0]})
            sensorListSi[id].update({'Switch.4.on.off': config[entry][8][0]})
            sensorListSi[id].update({'Switch.5.on.off': config[entry][9][0]})
            sensorListSi[id].update({'Switch.6.on.off': config[entry][10][0]})
            sensorListSi[id].update({'Switch.7.on.off': config[entry][11][0]})
            sensorListSi[id].update({'Switch.Main.on.off': config[entry][12][0]})
            elementSize = 13

        if type == 23:
            type = '23 SPU'
            sensorListSi[id].update({'name': config[entry][3]})
            sensorListSi[id].update({'val.4.0': config[entry][4][0]})
            sensorListSi[id].update({'val.4.1': config[entry][4][1]})
            elementSize = 17

        if type == 25:
            type = '25 reserved'
            elementSize = 2

        sensorListSi[id].update({'type': type, 'pos': elementPos})
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
message, addr = client.recvfrom(2048)
# picoIp = addr[0]
picoIp = "192.168.8.146"
debug("See Pico at " + str(picoIp))

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


def readTemp(sensorId, elementId):
    try:
        sensorListTmp[sensorId].update({'temperature': toTemperature(element[elementId][10])})
    except KeyError:
        print("Something went wrong readTemp " + str(sensorId))
    finally:
        debug("The 'try except' is finished readTemp")


def readTank(sensorId, elementId):
    try:
        sensorListTmp[sensorId].update({'currentLevel': element[elementId][0]})
        # sensorListTmp[sensorId].update({'currentLevel': element[elementId][0] / float(1000)})

        # if len(sensorListTmp[sensorId]) >= 0:
        # sensorListTmp[sensorId].update({'currentVolume': element[elementId][1] / float(10000)})
        sensorListTmp[sensorId].update({'currentVolume': element[elementId][1]})
    except KeyError:
        print("Something went wrong readTank " + str(sensorId))
    finally:
        debug("The 'try except' is finished readTank")


def readBatt(sensorId, elementId):
    try:
        stateOfCharge = float("%.2f" % (element[elementId][0] / 16000.0))
        sensorListTmp[sensorId].update({'stateOfCharge': stateOfCharge})
        sensorListTmp[sensorId].update({'capacity.remaining': element[elementId][1] * stateOfCharge})
        sensorListTmp[sensorId].update({'volt': element[elementId + 2][1] / float(1000)})
    except KeyError:
        print("Something went wrong readBatt " + str(sensorId))
    finally:
        debug("The 'try except' is finished readBatt")


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


def readCurrent(sensorId, elementId):
    try:
        current = element[elementId][1]
        if current > 25000:
            current = (65535 - current) / float(100)
        else:
            current = current / float(100) * -1
        sensorListTmp[sensorId].update({'current': current})
    except KeyError:
        print("Something went wrong readCurrent " + str(sensorId))
    finally:
        debug("The 'try except' is finished readCurrent")


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
    # element = {0: [25615, 43879], 1: [25615, 47479], 2: [65535, 64534], 3: [1, 31679], 4: [0, 153], 5: [0, 12114], 9: [25606, 10664], 10: [65535, 64534], 11: [65535, 64980], 12: [0, 5875], 13: [0, 12672], 14: [0, 0], 15: [0, 65535], 16: [0, 65535], 17: [0, 65535], 18: [65535, 65520], 19: [65531, 34426], 20: [0, 0], 21: [0, 16], 22: [65535, 65535], 23: [65535, 65450], 24: [65535, 65048], 25: [65515, 983], 26: [0, 0], 27: [0, 0], 28: [0, 0], 29: [0, 65535], 30: [0, 65535], 31: [0, 65535], 32: [0, 65535], 33: [0, 0], 34: [65535, 65532], 35: [0, 18386], 36: [0, 26940], 37: [0, 0], 38: [0, 65535], 39: [0, 65535], 40: [0, 65535], 41: [0, 0], 42: [65529, 51037], 43: [65535, 65529], 44: [4, 9403], 45: [0, 0], 46: [65533, 6493], 47: [0, 0], 48: [65535, 18413], 49: [0, 0], 50: [15776, 53404], 51: [65535, 64980], 52: [0, 12672], 53: [32767, 65535], 54: [65531, 42226], 55: [15984, 17996], 56: [65535, 65532], 57: [0, 26940], 58: [32767, 65535], 59: [65253, 37546], 60: [0, 0], 61: [0, 0], 62: [0, 0], 63: [0, 54], 64: [0, 57], 65: [0, 65535], 66: [0, 44], 67: [0, 0], 68: [282, 2829], 69: [5, 58], 70: [300, 3000]}
    debug(element)
    for diff in list(dictdiffer.diff(old_element, element)):
        debug(diff)
    old_element = copy.deepcopy(element)

    # Add values to sensorList copy

    for item in sensorList:
        # debug("sensorList[" + str(item) + "]: " + sensorList[item]["name"])
        elId = sensorList[item]['pos']
        itemType = sensorList[item]['type']

        if itemType == 'barometer':
            readBaro(item, elId)
        if itemType == 'thermometer':
            readTemp(item, elId)
        if itemType == 'battery':
            readBatt(item, elId)
        if itemType == 'ohm':
            readOhm(item, elId)
        if itemType == 'volt':
            readVolt(item, elId)
        if itemType == 'current':
            readCurrent(item, elId)
        if itemType == 'tank':
            readTank(item, elId)

    print(json.dumps(sensorListTmp))

    sys.stdout.flush()
    time.sleep(0.9)
    empty_socket_has_exit(client, 'End of Application')
