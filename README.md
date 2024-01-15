# Domoticz_pi_Clockspeeds_Plugin

Reimplements the ARM clock speed monitoring which was removed from domoticz 2024.1

## Devices

- ARM clock speed - ARM clockspeed in Mhz
- V3D clock speed - V3D clockspeed in Mhz
- Core clock speed - Core clockspeed in Mhz
- 8 get_throttled switches - according to pi documentation (https://www.raspberrypi.com/documentation/computers/os.html#vcgencmd)

## Config

- interval - the interval in seconds (how often is the sensor updated)
- debug level - sets the correct debug level
