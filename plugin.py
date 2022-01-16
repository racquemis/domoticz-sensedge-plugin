# Kaiterra SenseEdge Mini Plugin
#
# Author: Racquemis
#
"""
<plugin key="KaiterraSenseEdgePluginV1" name="Kaiterra SenseEdge Air Quality" author="Racquemis" version="1.0.0" wikilink="https://github.com/racquemis/domoticz-sensedge-plugin" externallink="https://github.com/racquemis/domoticz-sensedge-plugin">
    <description>
        <h2>Kaiterra SenseEdge Plugin (API version)</h2>
        Plugin for Kaiterra SenseEdge Mini<br/>
        <h3>Instructions</h3><br/>
        1. If not done already, Add the SenseEdge Mini devices to the Kaiterra Dashboard<br/>
        2. Create or retrieve an API key in the Account Settings on the Kaiterra Dashboard<br/>
        3. Enter the API Key in the field below<br/>
        4. Save.<br/><br/>
        The plugin will automatically retrieve all devices associated with the API key. <br/>
        It will create new devices in the Hardware page for each metric.
        (It can take up to several minutes, depending on number of devices, for all devices to be created)<br/>
        Battery Level is used on TVOC, PM2.5 and PM10 devices to show Sensor Health<br/><br/>

        Polling Interval is fixed to min. of 120 seconds. The plugins supports a maximum of 42 devices (Limitation in Domoticz).<br/>
        Polling Interval is overriden when the time requires the poll all the devices exceeds numDevices*6 seconds.
        
    </description>
    <params>
        <param field="Mode1" label="API Key" width="470px" required="true" default=""/>
        <param field="Mode2" label="Polling Interval" width="60px" required="true" default="120"/>
    </params>
</plugin>
"""
import Domoticz
import json

class BasePlugin:
    httpConn = None
    deviceConn = []
    deviceUuids = []
    lastOffset = -1
    heartbeatcount = 0
    
    PollingInterval = 120 #Set to minimum by default
    #enabled = False
    def __init__(self):
        return
    
    def onStart(self):
        for Unit in Devices:
            exists = False
            _uuid = Devices[Unit].DeviceID.split(":")[0]
            for item in self.deviceUuids:
                if _uuid in item:
                    exists = True
            if not exists:
                self.deviceConn.append(Domoticz.Connection(Name="SenseEdge " + Devices[Unit].DeviceID, Transport="TCP/IP", Protocol="HTTPS", Address="api.kaiterra.com", Port="443"))
                self.deviceUuids.append(Devices[Unit].DeviceID.split(':')[0])
                if int(Devices[Unit].DeviceID.split(':')[1]) >= self.lastOffset:
                    self.lastOffset = int(Devices[Unit].DeviceID.split(':')[1])
        self.httpConn = Domoticz.Connection(Name="UUID Collector", Transport="TCP/IP", Protocol="HTTPS", Address="api.kaiterra.com", Port="443")
        minReadTime = self.lastOffset * 6
        minPollingInterval = int(Parameters["Mode2"]) if int(Parameters["Mode2"])>self.PollingInterval else self.PollingInterval
        PollingInterval = minReadTime if minReadTime > minPollingInterval else minPollingInterval  
            
        Domoticz.Log("Min. Polling Interval: "+ str(minPollingInterval) +"s, Configured Polling Interval: " + str(self.PollingInterval) + "s")
        Domoticz.Heartbeat(2)

    def onStop(self):
        Domoticz.Log("onStop called")
        for connection in self.deviceConn:
            self.deviceConn.Disconnect()

    def onConnect(self, Connection, Status, Description):
        if (Status == 0):
            Domoticz.Debug("Sucessfull connection to Kaiterra API")
            if "SenseEdge" in Connection.Name:
                uuid = Connection.Name.split(' ')[1]
                Domoticz.Log("Processing: " + Connection.Name)
                sendData = { 'Verb' : 'GET',
                             'URL'  : ('/v1/account/me/device/' + uuid.split(":")[0] + '?select=meta,data&key=' + Parameters['Mode1']),
                             'Headers' : { 'Content-Type': 'application/json; charset=utf-8', \
                                           'Connection': 'keep-alive', \
                                           'Accept': 'Content-Type: application/json; charset=UTF-8', \
                                           'Host': 'api.kaiterra.com', \
                                           'User-Agent':'Domoticz/1.0' }
                             }
                Connection.Send(sendData)
                #Domoticz.Debug('v1/account/me/device/' + uuid.split(":")[0] + '?select=meta,data&key=' + Parameters['Mode1'])
            else:
                URL = '/v1/account/me/device?select=&key=' + Parameters["Mode1"]
                #Domoticz.Log(URL)
                sendData = { 'Verb' : 'GET',
                             'URL'  : URL,
                             'Headers' : { 'Content-Type': 'application/json; charset=utf-8', \
                                           'Connection': 'keep-alive', \
                                           'Accept': 'Content-Type: application/json; charset=UTF-8', \
                                           'Host': 'api.kaiterra.com', \
                                           'User-Agent':'Domoticz/1.0' }
                            }
                Connection.Send(sendData)
        else:
            Domoticz.Log("Failed to connect ("+str(Status)+") to: api.kaiterra.com with error: "+Description)

    def onMessage(self, Connection, Data):
        strData = Data["Data"].decode("utf-8", "ignore")
        Status = int(Data["Status"])
        if (Status == 200):
            json_data = json.loads(strData)
            if not "dmodel" in strData:
                for device in json_data:
                    if device['uuid'] not in self.deviceUuids:
                        self.deviceConn.append(Domoticz.Connection(Name="SenseEdge " + device['uuid'] + ":" + str(self.lastOffset+1), Transport="TCP/IP", Protocol="HTTPS", Address="api.kaiterra.com", Port="443"))
                        self.lastOffset = self.lastOffset + 1
            else:
                uuid = Connection.Name.split()[1]
                offset = int(Connection.Name.split()[1].split(":")[1])
                device_name = json_data['name']
                _uuid = uuid.split(":")[0]
                exists = False
                for item in self.deviceUuids:
                    if _uuid in item:
                        exists = True
                if exists == False:
                    Domoticz.Device(DeviceID=uuid, Name=device_name + " [AQI]", Unit=1+(offset*6), Used=0, Type=243, Subtype=31).Create()
                    Domoticz.Device(DeviceID=uuid, Name=device_name + " [Temp/Hum]", Unit=2+(offset*6), Used=0, Type=82).Create()
                    Domoticz.Device(DeviceID=uuid, Name=device_name + " [CO2]", Unit=3+(offset*6), Used=0, Type=249).Create()
                    Domoticz.Device(DeviceID=uuid, Name=device_name + " [TVOC]", Unit=4+(offset*6), Used=0, Type=243, Subtype=31, Options={'Custom': '1;ppb'}).Create()
                    Domoticz.Device(DeviceID=uuid, Name=device_name + " [PM2.5]", Unit=5+(offset*6), Used=0, Type=243, Subtype=31, Options={'Custom': '1;µg/m³'}).Create()
                    Domoticz.Device(DeviceID=uuid, Name=device_name + " [PM10]", Unit=6+(offset*6), Used=0, Type=243, Subtype=31, Options={'Custom': '1;µg/m³'}).Create()
                    self.deviceUuids.append(_uuid)
                    Domoticz.Log("Created Device: " + json_data['name'])
                ## Update Values
                km200_level = 255
                km203_level = 255
                if "info" in json_data:
                    if "daqi_std" in json_data['info']:
                        Devices[1+(offset*6)].Update(nValue=0,sValue=str(json_data['info']['daqi_std']))
                    if "sbay102" in json_data['info']:
                        if json_data['info']['sbay102']['stype'] == "km200":
                            km200_level = round(json_data["info"]['sbay102']['slifetime'] * 100)
                        if json_data["info"]["sbay102"]['stype'] == "km203":
                            km203_level = round(json_data["info"]['sbay102']['slifetime'] * 100)
                    if "sbay103" in json_data["info"]:
                        if json_data["info"]['sbay103']['stype'] == "km200":
                            km200_level = round(json_data["info"]['sbay103']['slifetime'] * 100)
                        if json_data["info"]['sbay103']['stype'] == "km203":
                            km203_level = round(json_data['info']['sbay103']['slifetime'] * 100)         
                if "data" in json_data:
                    temphum = [None,None]
                    for measurement in json_data['data']:
                        if measurement['param'] == "temperature":
                            temphum[0] = measurement["points"][0]['value']
                            if temphum[0] is not None and temphum[1] is not None:
                                Devices[2+(offset*6)].Update(nValue=0,sValue=str(temphum[0])+";"+str(temphum[1]) + ";0")
                        if measurement["param"] == "humidity":
                            temphum[1] = measurement["points"][0]['value']
                            if temphum[0] is not None and temphum[1] is not None:
                                Devices[2+(offset*6)].Update(nValue=0,sValue=str(temphum[0])+";"+str(temphum[1]) + ";0")
                        if measurement["param"] == "co2":
                            Devices[3+(offset*6)].Update(nValue=measurement["points"][0]['value'], sValue="")
                        if measurement["param"] == "tvoc-sgp":
                            Devices[4+(offset*6)].Update(nValue=0,sValue=str(measurement["points"][0]['value']),BatteryLevel=km203_level)                         
                        if measurement["param"] == "pm25":
                            Devices[5+(offset*6)].Update(nValue=0,sValue=str(measurement["points"][0]['value']),BatteryLevel=km200_level)                              
                        if measurement["param"] == "pm10":
                            Devices[6+(offset*6)].Update(nValue=0,sValue=str(measurement["points"][0]['value']),BatteryLevel=km200_level)                      

        elif (Status == 302):
            Domoticz.Log("Kaiterra API returned a Page Moved Error.")
            sendData = { 'Verb' : 'GET',
                         'URL'  : Data["Headers"]["Location"],
                         'Headers' : { 'Content-Type': 'text/xml; charset=utf-8', \
                                       'Connection': 'keep-alive', \
                                       'Accept': 'Content-Type: application/json; charset=UTF-8', \
                                       'Host': 'api.kaiterra.com:443', \
                                       'User-Agent':'Domoticz/1.0' },
                        }
            Connection.Send(sendData)
        elif (Status == 400):
            Domoticz.Error("Kaiterra API returned a Bad Request Error.")
        elif (Status == 500):
            Domoticz.Error("Kaiterra API returned a Server Error.")
        else:
            Domoticz.Error("Kaiterra API returned a status: "+str(Status))
        Connection.Disconnect()
                
                    

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Debug("onDisconnect called for connection to: "+Connection.Address+":"+Connection.Port)

    def onHeartbeat(self):
        if self.heartbeatcount == 0:
            self.httpConn.Connect()
        if self.heartbeatcount < len(self.deviceConn) and self.heartbeatcount > 0:
            self.deviceConn[self.heartbeatcount].Connect()
        if self.heartbeatcount == self.PollingInterval/2:
            self.heartbeatcount = 0
        else:
            self.heartbeatcount = self.heartbeatcount + 1
            
global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()
    
def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()
