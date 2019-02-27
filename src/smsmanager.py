import dbus

MM_SERVICE = 'org.freedesktop.ModemManager1'
MM_OBJPATH = '/org/freedesktop/ModemManager1'
MM_INTFACE = MM_SERVICE

OBJMANAGER_IFACE = 'org.freedesktop.DBus.ObjectManager'
PROP_IFACE = 'org.freedesktop.DBus.Properties'
SMS_IFACE = 'org.freedesktop.ModemManager1.Sms'
MDM_IFACE = 'org.freedesktop.ModemManager1.Modem'
MSG_IFACE = 'org.freedesktop.ModemManager1.Modem.Messaging'

class SMSManager(object):
	def __init__(self, sms_cb):
		self.bus = dbus.SystemBus()
		om = dbus.Interface(self.bus.get_object(MM_SERVICE, MM_OBJPATH),
							OBJMANAGER_IFACE)

		objects = om.GetManagedObjects()
		# Retrieve modem list
		if not len(objects):
			raise RuntimeError("No modem found")

		for path in objects.keys():
			self.device = self.bus.get_object(MM_SERVICE, path)
			break

		self.device.Enable(True, dbus_interface=MDM_IFACE)

		self.sms_cb = sms_cb
		self.bus.add_signal_receiver(self.__sms_added,
					bus_name=MM_SERVICE,
					dbus_interface=MSG_IFACE,
					signal_name="Added")

	def __sms_added(self, path, received):
		if (received == False):
			return

		sms_prop = dbus.Interface(self.bus.get_object(MM_SERVICE, path), PROP_IFACE)
		message = sms_prop.Get(SMS_IFACE, 'Text')
		number = sms_prop.Get(SMS_IFACE, 'Number')
		self.sms_cb(message, number)

	def send(self, number, message):
		msg = dbus.Dictionary({
					dbus.String('number') : dbus.String(number),
 					dbus.String('text') : dbus.String(message)
				}, signature=dbus.Signature("sv"));

		sms_path = self.device.Create(msg, dbus_interface=MSG_IFACE)

		sms = self.bus.get_object(MM_SERVICE, sms_path)
		sms.Send(dbus_interface=SMS_IFACE)
