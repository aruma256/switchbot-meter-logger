import binascii
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
from queue import deque
import time

from bluepy.btle import Scanner, DefaultDelegate, BTLEDisconnectError
from bitstring import BitStream

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

ONE_MIN = timedelta(minutes=1)

with open('settings.json') as f:
    settings = json.load(f)

INFLUX_CLIENT = InfluxDBClient(url=settings['influx']['url'], token=settings['influx']['token'])
INFLUX_API = INFLUX_CLIENT.write_api(write_options=SYNCHRONOUS)

class MeterData:
    """
    https://github.com/OpenWonderLabs/python-host/wiki/Meter-BLE-open-API#New_Broadcast_Message
    """
    def __init__(self, value):
        b = BitStream('0x' + value)

        b.read('pad:16')

        b.read('pad:1')
        self.device_type = b.read('uint:7')

        b.read('pad:4')
        self.group = b.read('uint:4')

        b.read('pad:1')
        self.battery = b.read('uint:7')

        self.temperature_alert_status = b.read('uint:2')
        self.humidity_alert_status = b.read('uint:2')
        self.temperature_decimal = b.read('uint:4')

        self.temperature_mode_flag = b.read('uint:1')
        self.temperature_int = b.read('uint:7')

        self.temperature_scale = b.read('uint:1')
        self.humidity = b.read('uint:7')

        sign = '' if self.temperature_mode_flag else '-'
        self.temperature = Decimal(f'{sign}{self.temperature_int}.{self.temperature_decimal}')

        self.datetime = datetime.now(tz=timezone.utc)

class _ScanCallback(DefaultDelegate):

    def __init__(self, listener, target_addr, target_ad_type=22):
        self.listener = listener
        self.target_addr = target_addr
        self.target_ad_type = target_ad_type

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if dev.addr == self.target_addr and isNewDev:
            value = dev.getValueText(self.target_ad_type)
            if value:
                self.listener(MeterData(value))

class MeterListener:

    def __call__(self, data: MeterData):
        INFLUX_API.write(settings['influx']['bucket'], settings['influx']['org'], f'meter,host=room temperature={data.temperature} {int(data.datetime.timestamp())}', write_precision='s')
        INFLUX_API.write(settings['influx']['bucket'], settings['influx']['org'], f'meter,host=room humidity={data.humidity} {int(data.datetime.timestamp())}', write_precision='s')

if __name__ == '__main__':
    listener = MeterListener()
    callback = _ScanCallback(listener, settings['device']['mac_addr'])
    scanner = Scanner().withDelegate(callback)
    target_time = datetime.now()
    target_time = datetime(target_time.year, target_time.month, target_time.day, target_time.hour, target_time.minute)
    while True:
        while target_time < datetime.now():
            target_time += ONE_MIN
        time.sleep((target_time - datetime.now()).total_seconds())
        try:
            scanner.scan(10)
        except BTLEDisconnectError as e:
            print(e)
            print(datetime.now())
            scanner.clear()

