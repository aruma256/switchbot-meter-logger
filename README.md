# switchbot-meter-logger

<pre>
sudo apt-get install python3-pip python3-numpy libglib2.0-dev
sudo pip3 install bluepy bitstring influxdb-client
</pre>

## settings.json

```json
{
    "device": {
        "mac_addr": "ff:ff:ff:ff:ff:ff"
    },
    "influx": {
        "org": "meterorg",
        "bucket": "meterbucket",
        "url": "http://localhost:32772",
        "token": "***********************************************"
    }
}
```

