# Pi clock speeds
#
# Author: akamming
#
"""
<plugin key="ClockSpeedsPlug" name="Pi Clockspeeds" author="akamming" version="0.0.1" wikilink="http://www.domoticz.com/wiki/plugins/plugin.html" externallink="https://github.com/akamming/Domoticz_pi_Clockspeeds_Plugin">
    <description>
        <h2>Pi Clock Speeds</h2><br/>
        implements measuring of clock speed
        <h3>Devices</h3>
        <ul style="list-style-type:square">
            <li>ARM Clock Speed - measures ARM clock speed</li>
        </ul>
        <h3>Configuration</h3>
        Interval - sets ups up the interval in seconds<br/>
        Debug Level - Sets the debug level of the plugin<br/>
    </description>
    <params>
        <param field="Mode1" label="Interval" width="150px" required="true" default="180"></param>
        <param field="Mode6" label="Debug" width="150px">
            <options>
                <option label="None" value="0"  default="true" />
                <option label="Python Only" value="2"/>
                <option label="Basic Debugging" value="62"/>
                <option label="Basic+Messages" value="126"/>
                <option label="Queue" value="128"/>
                <option label="Connections Only" value="16"/>
                <option label="Connections+Queue" value="144"/>
                <option label="All" value="-1"/>
            </options>
        </param>
    </params>
</plugin>
"""
import DomoticzEx as Domoticz
import subprocess
import os
import time

#variables for application logic
debug=True
lastUpdate=0
interval=0

#constants
DEVICEID="Clockspeeds"
ARMSPEED=1
V3DSPEED=2
CORESPEED=3
UNDERVOLTAGEDETECTED=4
ARMFREQUENCYCAPPED=5
CURRENTLYTHROTTLED=6
SOFTTEMPERATURELIMITACTIVE=7
UNDERVOLTAGEHASOCCURRED=8
ARMFREQUENCYCAPPINGHASOCCURRED=9
THROTTLINGHASOCCURRED=10
SOFTTEMPERATURELIMITHASOCCURRED=11


def Debug(text):
    if (debug):
        Domoticz.Log("Debug: "+str(text))

def Log(text):
    Domoticz.Log("Debug: "+str(text))

def UpdateSwitch(DeviceID,idx,name,nv,sv):
    Debug ("UpdateSwitch("+str(DeviceID)+","+str(idx)+","+str(name)+","+str(nv)+","+str(sv)+" called")
    if (not DeviceID in Devices) or (not idx in Devices[DeviceID].Units):
        Domoticz.Unit(Name=Parameters["Name"]+"-"+name, Unit=idx, Type=244, Subtype=73, DeviceID=DeviceID, Used=True).Create()
    if (Devices[DeviceID].Units[idx].nValue==nv and Devices[DeviceID].Units[idx].sValue==sv):
        Debug("Switch status unchanged, not updating "+Devices[DeviceID].Units[idx].Name)
    else:
        Debug("Changing from + "+str(Devices[DeviceID].Units[idx].nValue)+","+Devices[DeviceID].Units[idx].sValue+" to "+str(nv)+","+str(sv))
        Devices[DeviceID].Units[idx].nValue = int(nv)
        Devices[DeviceID].Units[idx].sValue = sv
        Devices[DeviceID].Units[idx].Update(Log=True)
        Domoticz.Log("On/Off Switch ("+Devices[DeviceID].Units[idx].Name+")")

def UpdateSensor(DeviceID,idx,name,tp,subtp,options,nv,sv):
    Debug("UpdateSensor("+str(DeviceID)+","+str(idx)+","+str(name)+","+str(tp)+","+str(subtp)+","+str(options)+","+str(nv)+","+str(sv)+") called)")
    if (not DeviceID in Devices) or (not idx in Devices[DeviceID].Units):
        Domoticz.Unit(Name=Parameters["Name"]+"-"+name, Unit=idx, Type=tp, Subtype=subtp, DeviceID=DeviceID, Options=options, Used=True).Create()
    Debug("Changing from + "+str(Devices[DeviceID].Units[idx].nValue)+","+str(Devices[DeviceID].Units[idx].sValue)+" to "+str(nv)+","+str(sv))
    if str(sv)!=Devices[DeviceID].Units[idx].sValue:
        Devices[DeviceID].Units[idx].nValue = int(nv)
        Devices[DeviceID].Units[idx].sValue = sv
        Devices[DeviceID].Units[idx].Update(Log=True)
        Domoticz.Log("General/Custom Sensor ("+Devices[DeviceID].Units[idx].Name+")")
    else:
        Debug("not updating General/Custom Sensor ("+Devices[DeviceID].Units[idx].Name+")")

def getARMClockSpeed():
    fn="/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq" # Get filename
    Debug("getClockSpeed() called")
    if os.path.exists(fn):
        #f = open(fn, "r+")
        f = open(fn)
        line = f.readline()
        f.close()
        speed = int(int(line)/1000)
        Debug("systemdevice exists, speed= "+str(speed))
        UpdateSensor(DEVICEID,ARMSPEED,"ARM Clock Speed",243,31,{'Custom':'1;Mhz'},int(speed),float(speed))
        return speed 
    else:
        Debug("No OS file found to check for clock speed, is this a Pi?")
        return -1

def UpdateThrottlingSensor(throttled,bit,UnitID,Name):
    if throttled&bit==bit:
        UpdateSwitch(DEVICEID,UnitID,Name,1,"On")
    else:
        UpdateSwitch(DEVICEID,UnitID,Name,0,"Off")


def getThrottling():
    Debug("getThrottling() called")

    #call vcgencmd
    result=subprocess.run(['vcgencmd','get_throttled'],capture_output=True,text=True)
    Debug("raw vcgencmd get_throttled out is "+str(result.stdout.strip()))

    #convert output to integer
    splittedoutput=result.stdout.strip().split("=")
    throttled=int(splittedoutput[1],16)
    Debug("throttled  = "+str(throttled))

    #and let's start updating the sensors
    UpdateThrottlingSensor(throttled,0x1,UNDERVOLTAGEDETECTED,"UnderVoltage Detected")
    UpdateThrottlingSensor(throttled,0x2,ARMFREQUENCYCAPPED,"ARM Frequency Capped")
    UpdateThrottlingSensor(throttled,0x4,CURRENTLYTHROTTLED,"Currently Throttled")
    UpdateThrottlingSensor(throttled,0x8,SOFTTEMPERATURELIMITACTIVE,"Soft Temperature Limit Active")
    UpdateThrottlingSensor(throttled,0x10000,UNDERVOLTAGEHASOCCURRED,"Under Voltage has Occurred")
    UpdateThrottlingSensor(throttled,0x20000,ARMFREQUENCYCAPPINGHASOCCURRED,"ARM Frequency Capping has Occurred")
    UpdateThrottlingSensor(throttled,0x40000,THROTTLINGHASOCCURRED,"Throttling has Occurred")
    UpdateThrottlingSensor(throttled,0x80000,SOFTTEMPERATURELIMITHASOCCURRED,"Soft Temperature Limit has Occurred")


def heartbeat():
    global interval
    global lastUpdate

    if (time.time()-lastUpdate)>=interval:
        lastUpdate=time.time() 
        Debug("Interval expired, run update")
        getARMClockSpeed()
        getThrottling()
    else:
        Debug(str(int(interval-(time.time()-lastUpdate)))+" seconds till next intervall, do nothing")


class BasePlugin:
    enabled = False
    def __init__(self):
        #self.var = 123
        return

    def onStart(self):
        global debug
        global interval

        Domoticz.Log("onStart called")

        interval=int(Parameters["Mode1"])
        Debug("Interval set to "+str(interval))

        if Parameters["Mode6"] != "0":
            debug=True
            Debug("Debugging switched on")
            Domoticz.Debugging(int(Parameters["Mode6"]))
            DumpConfigToLog()
        else:
            Log("Debugging switched off")
            debug=False
        
        heartbeat()


    def onStop(self):
        Domoticz.Log("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("onConnect called")

    def onMessage(self, Connection, Data):
        Domoticz.Log("onMessage called")

    def onCommand(self, DeviceID, Unit, Command, Level, Color):
        Domoticz.Log("onCommand called for Device " + str(DeviceID) + " Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")

    def onHeartbeat(self):
        Domoticz.Log("onHeartbeat called")
        heartbeat()

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

def onCommand(DeviceID, Unit, Command, Level, Color):
    global _plugin
    _plugin.onCommand(DeviceID, Unit, Command, Level, Color)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

# Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for DeviceName in Devices:
        Device = Devices[DeviceName]
        Domoticz.Debug("Device ID:       '" + str(Device.DeviceID) + "'")
        Domoticz.Debug("--->Unit Count:      '" + str(len(Device.Units)) + "'")
        for UnitNo in Device.Units:
            Unit = Device.Units[UnitNo]
            Domoticz.Debug("--->Unit:           " + str(UnitNo))
            Domoticz.Debug("--->Unit Name:     '" + Unit.Name + "'")
            Domoticz.Debug("--->Unit nValue:    " + str(Unit.nValue))
            Domoticz.Debug("--->Unit sValue:   '" + Unit.sValue + "'")
            Domoticz.Debug("--->Unit LastLevel: " + str(Unit.LastLevel))
    return
