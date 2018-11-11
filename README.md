# Cellular Monitor

This monitor has been tested with a **Dragonboard-410C** + **Shiratech LTE mezzanine** + **Linaro QCOMLT Debian**
This monitor polls the different available sensors and can be controlled remotely by text messages (SMS).
Alert can also be received on movement detection.
This monitor can be used to remotely watch secondary-residence, warehouse, boat, etc...
It does not rely on any local infrastructure except power supply.

Why using SMS (and not cellular 4G data / internet):
- simple and straightforward for any user
- No application to create on user side
- no server requested
- GSM has a better coverage
- Can use cheap SMS only plan (e.g. 2 euros per month in france)

features:
- Track remote temperature and set temperature alerts
- Enable alert on proximity/movement detection
- TODO: Daily reports feature
- TODO: Enable relays remotely (eg. controlling headers, door lock, shutters, etc)
- TODO: Earthquake detection (via accelerometer, gyro...)
- ...

Architecture:
- python smbus is used to poll the sensors (temperature, range)
- NetworkManager (via dbus) is used to send/receive sms

## Prerequisites
##### Install dep packages
apt-get update
apt-get install python3-smbus
apt-get install python3-dbus

##### Configure Modem connection
Either via UI or network manager (mmcli/nmcli)

##### Run the script
./cellularmonitor.py
(can be run at init)

Once started you should be able to send commands an receive events via test messages (SMS)

## SMS commands

The client mobile needs to authenticate to the monitor before performing any other commands.
This can be done via the "AUTH code" text message or via the /etc/cellularmonitor.json conf file.

##### AUTH [code]
Authenticate to the monitor as trusted contact (default code is 1234)
##### REGISTER
Register to the monitor as main contact for events
##### UNREGISTER
Unregister from the monitor
##### PING
simple ping-pong command
##### TEMP
Retrieve inst/min/max temperature values (celcius)
##### RANGE
Retrieve range value
##### REBOOT
Reboot the monitor
##### TIME
Retrieve time since boot (seconds)
##### DATE
Retrieve local date-time

## SMS Events
##### ALERT
Monitor has detected movement
##### STARTED
Monitor has started
