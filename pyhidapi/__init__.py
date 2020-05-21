import ctypes, ctypes.util

path = ctypes.util.find_library('hidapi')

if not path:
	path = path = ctypes.util.find_library('hidapi.dll')

if not path:
	path = ctypes.util.find_library('hidapi-libusb')

if not path:
	path = ctypes.util.find_library('hidapi-hidraw')

if not path:
	raise ImportError('Cannot find hidapi library')

hidapi = ctypes.CDLL(path)

class c_hid_device_info(ctypes.Structure):
	def __iter__(self):
		p = self
		yield DeviceInfo(p)
		
		while p.next:
			p = p.next.contents
			yield DeviceInfo(p)

c_hid_device_info._fields_ = [
	('path', ctypes.c_char_p),
	('vendor_id', ctypes.c_ushort),
	('product_id', ctypes.c_ushort),
	('serial_number', ctypes.c_wchar_p),
	('release_number', ctypes.c_ushort),
	('manufacturer_string', ctypes.c_wchar_p),
	('product_string', ctypes.c_wchar_p),
	('usage_page', ctypes.c_ushort),
	('usage', ctypes.c_ushort),
	('interface_number', ctypes.c_int),
	('next', ctypes.POINTER(c_hid_device_info)),
]

hidapi.hid_open.argtypes = [ctypes.c_ushort, ctypes.c_ushort, ctypes.c_wchar_p]
hidapi.hid_open.restype = ctypes.c_void_p

hidapi.hid_open_path.argtypes = [ctypes.c_char_p]
hidapi.hid_open_path.restype = ctypes.c_void_p

hidapi.hid_close.argtypes = [ctypes.c_void_p]

hidapi.hid_read_timeout.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_int]
hidapi.hid_read.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t]
hidapi.hid_write.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t]
hidapi.hid_send_feature_report.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t]
hidapi.hid_get_feature_report.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t]

hidapi.hid_enumerate.restype = ctypes.POINTER(c_hid_device_info)

def enumerate(vid = 0, pid = 0):
	info = hidapi.hid_enumerate(vid, pid)
	
	if not info:
		return []
	
	l = list(info.contents)
	
	hidapi.hid_free_enumeration(info)
	
	return l

class HIDError(Exception):
	pass

class DeviceInfo:
	def __init__(self, cstruct):
		self.path = cstruct.path
		self.vendor_id = cstruct.vendor_id
		self.product_id = cstruct.product_id
		self.serial_number = cstruct.serial_number
		self.release_number = cstruct.release_number
		self.manufacturer_string = cstruct.manufacturer_string
		self.product_string = cstruct.product_string
		self.usage_page = cstruct.usage_page
		self.usage = cstruct.usage
		self.interface_number = cstruct.interface_number
	
	def open(self):
		return Device(path = self.path)

class Device:
	def __init__(self, vid = None, pid = None, serial = None, path = None):
		if path is not None:
			self._dev = hidapi.hid_open_path(path)
		
		elif vid is not None and pid is not None:
			self._dev = hidapi.hid_open(vid, pid, serial)
		
		else:
			raise TypeError('vid/pid or path is required')
		
		if not self._dev:
			raise HIDError('failed to open device')
	
	def __del__(self):
		self.close()
	
	def close(self):
		if self._dev:
			hidapi.hid_close(self._dev)
			self._dev = None
	
	def set_output_report(self, data, id = 0):
		if hidapi.hid_write(self._dev, ctypes.c_char_p(chr(id) + data), len(data) + 1) != len(data) + 1:
			raise HIDError('failed to set output')
	
	def get_input_report(self, timeout = -1):
		buf = ctypes.create_string_buffer(64)
		
		ret = hidapi.hid_read_timeout(self._dev, buf, 64, timeout)
		
		if ret < 0:
			raise HIDError('failed to get input')
		
		return buf[:ret]
	
	def set_feature_report(self, data, id = 0):
		if hidapi.hid_send_feature_report(self._dev, ctypes.c_char_p(bytes([id]) + data), len(data) + 1) != len(data) + 1:
			raise HIDError('failed to set feature')
	
	def get_feature_report(self, id = 0):
		buf = ctypes.create_string_buffer(64)
		buf[0] = id
		
		ret = hidapi.hid_get_feature_report(self._dev, buf, 64)
		
		if ret < 0:
			raise HIDError('failed to get feature')
		
		return buf[1:ret]
