import csv
import time
import zlib
import requests
import simplejson
import zmq
from pathlib import Path
import pandas as pd

########################################################################################################################
# Configuration

_relayEDDN = 'tcp://eddn.edcd.io:9500'
_timeoutEDDN = 600000

# Software from which updates should be taken into consideration
_authSoftware = [
    "EDDiscovery",
    "EDDI",
    "Maddavo's Market Share",
    "E:D Market Connector [Windows]",
    "E:D Market Connector [Linux]",
    "EDO Materials Helper"
]

# Path to the csv with commodities list
_filepath = "commodities.csv"

# This is the number of stations and carriers there are in Elite Dangerous (estimated)
# This number could be outdated if not updated recently
_stationsNum = 332250

# How much more should the price be than what the average is to perform an action
CRITICALMULTIPLIER = 2

# How much demand should there be to perform an action
CRITICALDEMAND = 100000

# Option to easily debug missing commodities and updates
commodityDebug = False


########################################################################################################################
# main function is strongly based on https://github.com/EDCD/EDDN/blob/master/examples/Python%203.4/Client_Complete.py
########################################################################################################################
# Start
def main():
    print('Starting LLAMA')

    con = zmq.Context()
    sub = con.socket(zmq.SUB)

    sub.setsockopt(zmq.SUBSCRIBE, b"")
    sub.setsockopt(zmq.RCVTIMEO, _timeoutEDDN)

    while True:
        try:
            df = pd.read_csv(_filepath, header=None)
            comDict = df.set_index(0).T.to_dict('list')

            sub.connect(_relayEDDN)
            print('Connecting to ' + _relayEDDN)

            while True:
                _msg = sub.recv()

                if not _msg:
                    sub.disconnect(_relayEDDN)
                    print('Disconnected from ' + _relayEDDN)
                    break

                # print('Received a message')

                _msg = zlib.decompress(_msg)
                if not _msg:
                    print('Error when decompressing the message')

                _json = simplejson.loads(_msg)
                if not _json:
                    print('Error when parsing the message')

                # Commodity V3
                if _json['$schemaRef'] == 'https://eddn.edcd.io/schemas/commodity/3':

                    _auth = _json['header']['softwareName'] in _authSoftware

                    # Inform if a software is giving commodity updates but not in authorised list
                    if not _auth:
                        if commodityDebug:
                            print('        - ' + 'UNAUTHORISED')
                            print('    - Software: ' + _json['header']['softwareName']
                                  + ' / '
                                  + _json['header']['softwareVersion'])
                            print()

                    else:
                        for commodity in _json['message']['commodities']:
                            temp = comDict.get(commodity.get('name'))
                            if temp is None:
                                if commodityDebug:
                                    print("Unmonitored good with id: \"" + commodity.get('name') + "\" | Uploaded from: " + _json['header']['softwareName'] + " | This is probably a rare station specific resource but could be something from a new update")
                                pass
                            else:
                                if commodity.get('buyPrice') != 0:
                                    temp[0] = (((_stationsNum - 1) * temp[
                                        0]) + commodity.get('buyPrice')) / _stationsNum
                                if commodity.get('sellPrice') != 0:
                                    temp[1] = (((_stationsNum - 1) * temp[
                                        1]) + commodity.get('sellPrice')) / _stationsNum
                                    if commodity.get('sellPrice') > (
                                            temp[1] * CRITICALMULTIPLIER) and commodity.get(
                                            'demand') > CRITICALDEMAND:
                                        ##################################################################################################################
                                        # Put action to execute here
                                        ##################################################################################################################
                                        pass
                                with open('commodities.csv', 'w', newline='') as f:
                                    writer = csv.writer(f)
                                    for key, value in comDict.items():
                                        writer.writerow([key] + value)

                # Inform message is in an unhandled commodity schema
                elif commodityDebug and 'commodity' in _json['$schemaRef']:
                    print("New schema for commodity found: " + _json['$schemaRef'])
                    print("From software: " + _json['header']['softwareName'])

        # If connection fails
        except zmq.ZMQError as e:
            print('ZMQSocketException: ' + str(e))
            sub.disconnect(_relayEDDN)
            print('Disconnected from ' + _relayEDDN)
            time.sleep(5)


def startup():
    if not Path(_filepath).exists():
        github_url = "https://raw.githubusercontent.com/DarkKryU/L.L.A.M.A./main/commodities.csv?token=GHSAT0AAAAAACW3S6AMESRIMFASCVB7AVAAZWU5VHA"
        try:
            response = requests.get(github_url)
            response.raise_for_status()
            with open(_filepath, 'wb') as file:
                file.write(response.content)
        except requests.exceptions.RequestException as e:
            print(f"Failed to download the file with commodities data: {e}")
    main()


########################################################################################################################

if __name__ == '__main__':
    startup()
