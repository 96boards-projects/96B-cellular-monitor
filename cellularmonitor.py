#!/usr/bin/python3

import adt7410
import time
import datetime
import smbus
import dbus
import smsmanager
import vl53l0x
import os
import json

import dbus.mainloop.glib
from gi.repository import GLib

TEMPERATURE_POLL_S = 5
RANGE_POLL_S = 1

I2C_BUS = 1
sensor_temp = 0
sensor_range = 0
sms = 0

# TEMPERATURE
TEMP_MIN_ALERT = 10
TEMP_MAX_ALERT = 30
RANGE_DIFF_TRIGGER_MM = 100
ALERT_TIMEOUT = 60

CMD_AUTH       = 'AUTH'
CMD_TEMP_GET   = 'TEMP'
CMD_RANGE_GET  = 'RANGE'
CMD_PING       = 'PING'
CMD_RESET      = 'RESET'
CMD_REGISTER   = 'REGISTER'
CMD_UNREGISTER = 'UNREGISTER'
CMD_REBOOT     = 'REBOOT'
CMD_TIME       = 'TIME'
CMD_DATE       = 'DATE'

class CellularMonitor(object):

	temp_min = 99.0
	temp_max = -99.0
	temp_inst = 0
	range_inst = 0
	last_alert = 0
	config = {}

	def __init__(self, config="/etc/cellularmonitor.json"):
		print('Init DBUS')
		dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
		print('Init temperature sensor')
		self.sensor_temp = adt7410.ADT7410(smbus.SMBus(I2C_BUS), 0x48)
		print('Init range sensor')
		self.sensor_range = vl53l0x.VL53L0X(smbus.SMBus(I2C_BUS), 0x29)
		print('Init sms manager')
		self.sms = smsmanager.SMSManager(self.sms_callback)
		print('Load config')
		self.conf_file = config
		self.load_config()

	def load_config(self):
		try:
			with open(self.conf_file, 'r') as f:
				self.config = json.load(f)
		except:
			print('Unable to open config file' + self.conf_file)

		if ('auth-code' not in self.config):
			self.config['auth-code'] = '1234'
		if ('auth-list' not in self.config):
			self.config['auth-list'] = []

	def save_config(self):
		try:
			with open(self.conf_file, 'w') as f:
				json.dump(self.config, f)
		except:
			print('Unable to open config file' + self.conf_file)

	def reset(self):
		self.temp_min = 99.0
		self.temp_max = -99.0

	def send_event(self, message):
		if ('contact' not in self.config):
			print('No contact')
			return
		try:
			self.sms.send(self.config['contact'], message)
		except:
			print('Unable to send message')

	def number_is_authenticated(self, number):
		if ('auth-list' in self.config):
			if (number in self.config['auth-list']):
				return True
		return False

	def sms_callback(self, message, number):
		print("From: " + number + ", Command: " + message)
		resp = ''

		message = message.upper()
		if (message == CMD_TEMP_GET):
			resp = 'temp: inst={:.2f};min={:.2f};max={:.2f}'.format(self.temp_inst, self.temp_min, self.temp_max)
		elif (message == CMD_RANGE_GET):
			resp = 'range: {}mm'.format(self.range_inst)
		elif (message == CMD_PING):
			resp = 'PONG'
		elif (message == CMD_RESET):
			self.reset()
			resp = 'RESET OK'
		elif (message == CMD_REGISTER):
			self.config['contact'] = number
			self.save_config()
			resp = 'REGISTERED'
		elif (message == CMD_UNREGISTER):
			self.config['contact'] = None
			self.save_config()
			resp = 'UNREGISTERED'
		elif (message == CMD_REBOOT):
			resp = 'REBOOTING'
			self.sms.send(number, resp)
			if (os.system('reboot') != 0):
				resp = 'REBOOT ERROR'
			else:
				exit(0)
		elif (CMD_AUTH in message):
			if (self.number_is_authenticated(number)):
				print(number + ' already authenticated')
			elif (self.config['auth-code'] in message):
				self.config['auth-list'].append(number)
				self.save_config()
				resp = 'AUTHENTICATED'
				print(number + ' Authenticated')
			else:
				print(number + ' Authentication failure')
		elif (message == CMD_TIME):
			resp = time.monotonic()
		elif (message == CMD_DATE):
			resp = datetime.datetime.now()
		else:
			return

		if (resp == ''):
			return

		resp = str(resp)
		print("To: " + number + ", Resp: " + resp);

		if (self.number_is_authenticated(number) == False):
			print('Error: Unkonwn number ' + number)
			return

		try:
			self.sms.send(number, resp)
		except:
			print('Unable to send message')

	def temperature_poll(self):
		try:
			self.temp_inst = self.sensor_temp.read()
		except:
			print('Unable to retrieve temperature')
			GLib.timeout_add_seconds(TEMPERATURE_POLL_S, self.temperature_poll)
			return

		self.temp_min = min(self.temp_inst, self.temp_min)
		self.temp_max = max(self.temp_inst, self.temp_max)

		GLib.timeout_add_seconds(TEMPERATURE_POLL_S, self.temperature_poll)

	def range_poll(self):
		try:
			range = self.sensor_range.read()
		except:
			print('Unable to retrieve range')
			GLib.timeout_add_seconds(RANGE_POLL_S, self.range_poll)
			return

		# Filter non-valid
		if (range == 0):
			GLib.timeout_add_seconds(RANGE_POLL_S, self.range_poll)
			return

		# Check if change changed
		if ((self.range_inst != 0) and (abs(self.range_inst - range) >=  RANGE_DIFF_TRIGGER_MM)):
			print('ALERT')
			now = time.monotonic()
			if ((now - self.last_alert) > ALERT_TIMEOUT):
				self.last_alert = now
				self.send_event("ALERT: movement")
			else:
				print("alert already sent " + str(now - self.last_alert))

		# Save
		self.range_inst = range

		# Reschedule
		GLib.timeout_add_seconds(RANGE_POLL_S, self.range_poll)

	def run(self):
		self.temperature_poll()
		self.range_poll()
		self.send_event('STARTED')
		loop = GLib.MainLoop()

		try:
			loop.run()
		except KeyboardInterrupt:
			print('Interrupted')
			self.save_config()

		print('exit')

def main():
	watch = CellularMonitor()
	watch.run()

if __name__ == '__main__':
	main()
