# Domoticz Kaiterra SenseEdge Mini Plugin
This is a hardware plugin to import air quality data from Kaiterra SenseEdge Mini devices into Domoticz.

Installation
----------------------
```bash
cd domoticz/plugins
git clone https://github.com/racquemis/domoticz-sensedge-plugin.git
```

Restart your Domoticz service with:

```bash
sudo service domoticz.sh restart
```
Setup
----------------------
If not already done, add the SenseEdge Mini devices to the [Kaiterra Dashboard](https://dashboard.kaiterra.com/) using the UUID of the devices.
Go to account settings in the dashboard generate or reuse an API key 


Go to **Setup**, **Hardware** in the Domoticz interface and add:
**Kaiterra SenseEdge Air Quality**.
Fill in the API key of the device and specify a polling interval. Save.
The plugin should now add new devices for each SenseEdge associated to the API key.
Add the devices you need from the **Setup**, **Devices** in Domoticz.


Features
----------------------
The plugin adds the following devices to domoticz:
- Temperature/Humidity [°C/%]
- CO2 Level [%]
- TVOC Level [ppb]
- PM2.5 Level [µg/m³]
- PM10 Level [µg/m³]
- AQI

For the TVOC and PM2.5/10 devices the battery level feature in Domoticz is used to show the Sensor Health of the device.


Polling Interval
----------------------
It is recommended not to set the polling interval too low. Default is 5 minutes. 
Minimum is based on number of devices (6 seconds per device) with an absolute minimum of 120s
The plugin suppports a maximum of 42 devices per hardware instance at which the minimum polling interval of an invidiual device will be around 4 minutes.
Since the rate limits of the API are not known these minimums are guesswork. They could prove too low or too high.

***Use the plugin at your own risk.***
