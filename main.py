#!/usr/bin/env python3

import sys, struct
from functools import partial
from PyQt5 import QtCore, QtWidgets

import pyhidapi

class MainWindow(QtWidgets.QWidget):
	def __init__(self, parent = None):
		QtWidgets.QWidget.__init__(self, parent)
		
		self.setWindowTitle('arcin configuration')
		
		self.layout = QtWidgets.QFormLayout(self)
		self.layout.setFieldGrowthPolicy(self.layout.AllNonFixedFieldsGrow)

class Config:
	def __init__(self, fmt, *options):
		self.struct = struct.Struct(fmt)
		self.options = options
	
	def load(self, data):
		data = data[:self.struct.size]
		
		for option, value in zip(self.options, self.struct.unpack(data)):
			option.set(value)
	
	def save(self):
		return self.struct.pack(*(option.get() for option in self.options))

class String:
	def __init__(self, form, label, size):
		self.widget = QtWidgets.QLineEdit(form)
		self.widget.setMaxLength(size - 1)
		form.layout.addRow(label, self.widget)
	
	def get(self):
		return str(self.widget.text()).encode()
	
	def set(self, value):
		self.widget.setText(value.decode().strip('\0'))

class Flags:
	def __init__(self, form, label, *flags):
		self.flags = []
		
		f = QtWidgets.QFrame(form)
		f.setFrameStyle(f.StyledPanel | f.Sunken)
		form.layout.addRow(label, f)
		
		fl = QtWidgets.QVBoxLayout(f)
		
		for bit, name in flags:
			checkbox = QtWidgets.QCheckBox(name, form)
			fl.addWidget(checkbox)
			self.flags.append((bit, checkbox))
	
	def get(self):
		r = 0
		
		for bit, checkbox in self.flags:
			if checkbox.isChecked():
				r |= 1 << bit
		
		return r
	
	def set(self, value):
		for bit, checkbox in self.flags:
			checkbox.setChecked(value & (1 << bit))

class Enum:
	def __init__(self, form, label, *options):
		self.widget = QtWidgets.QComboBox(form)
		form.layout.addRow(label, self.widget)
		
		for value, name in options:
			self.widget.addItem(name, value)
	
	def get(self):
		return self.widget.itemData(self.widget.currentIndex())
	
	def set(self, value):
		self.widget.setCurrentIndex(self.widget.findData(value))

class HIDDeviceDialog(QtWidgets.QDialog):
	def __init__(self, parent):
		QtWidgets.QDialog.__init__(self, parent)
		
		self.path = None
		
		self.setModal(True)
		self.setWindowTitle('Select device')
		
		layout = QtWidgets.QVBoxLayout(self)
		
		layout.addWidget(QtWidgets.QLabel('Connected devices:'))
		
		self.listwidget = QtWidgets.QListWidget(self)
		layout.addWidget(self.listwidget)
		
		buttons = QtWidgets.QHBoxLayout()
		layout.addLayout(buttons)
		
		refresh = QtWidgets.QPushButton('Refresh', self)
		refresh.pressed.connect(self.refresh)
		buttons.addWidget(refresh)
		
		select = QtWidgets.QPushButton('Select', self)
		select.pressed.connect(self.select)
		buttons.addWidget(select)
		
		self.refresh()
	
	def refresh(self):
		self.devices  = pyhidapi.enumerate(0x1d50, 0x6080)
		self.devices += pyhidapi.enumerate(0x1ccf, 0x101c)
		self.devices += pyhidapi.enumerate(0x1ccf, 0x1014)
		names = ['%s (%s)' % (dev.product_string, dev.serial_number) for dev in self.devices]
		
		self.listwidget.clear()
		self.listwidget.addItems(names)
		self.listwidget.setCurrentRow(0)
	
	def select(self):
		self.dev = self.devices[self.listwidget.currentRow()]
		
		self.accept()
	
	@classmethod
	def getDev(cls, parent):
		dialog = HIDDeviceDialog(parent)
		
		if not dialog.exec_():
			return None
		
		return dialog.dev

def select_device():
	devices  = pyhidapi.enumerate(0x1d50, 0x6080)
	devices += pyhidapi.enumerate(0x1ccf, 0x101c)
	devices += pyhidapi.enumerate(0x1ccf, 0x1014)

	if len(devices) == 1:
		return devices[0]
	
	return HIDDeviceDialog.getDev(mainwindow)

def write():
	dev = select_device()
	
	if not dev:
		return
	
	dev = dev.open()
	
	data = config.save()
	
	# Write config.
	dev.set_feature_report(struct.pack('<BBx60s', 0, len(data), data), 0xc0)
	
	# Reset device.
	dev.set_feature_report('\x20'.encode(), 0xb0)
	
	QtWidgets.QMessageBox.information(mainwindow, 'Information', 'Write complete')

def read():
	dev = select_device()
	
	if not dev:
		return
	
	dev = dev.open()
	
	seq, n, data = struct.unpack('<BBx60s', dev.get_feature_report(0xc0))
	
	config.load(data)

if __name__ == '__main__':   
    app = QtWidgets.QApplication(sys.argv)
    mainwindow = MainWindow()
    config = Config('<12sLbbBB',
        String(mainwindow, 'Label', 12),
        Flags(mainwindow, 'Flags',
            (0, 'Hide serial number'),
            (1, 'Invert QE1'),
            (2, 'Invert QE2'),
            (3, 'LED1 always on'),
            (4, 'LED2 always on'),
            (5, 'Analog Mode'),
        ),
        Enum(mainwindow, 'QE1 sensitivity',
            (0, '1:1'),
            *([(-n, '1:%d' % n) for n in (2, 3, 4, 6, 8, 11, 16)] + [(n, '%d:1' % n) for n in (2, 3, 4, 6, 8, 11, 16)])
        ),
        Enum(mainwindow, 'QE2 sensitivity',
            (0, '1:1'),
            *([(-n, '1:%d' % n) for n in (2, 3, 4, 6, 8, 11, 16)] + [(n, '%d:1' % n) for n in (2, 3, 4, 6, 8, 11, 16)])
        ),
        Enum(mainwindow, 'PS2 mode',
            (0, 'Disabled'),
            (1, 'Pop\'n Music'),
            (2, 'IIDX (QE1)'),
            (3, 'IIDX (QE2)'),
        ),
        Enum(mainwindow, 'QE Correction',
            (0, 'Disabled'),
            (1, 'SDVX e-AMUSEMENT CLOUD'),
        ),
    )

    l = QtWidgets.QHBoxLayout()
    mainwindow.layout.addRow('', l)

    b = QtWidgets.QPushButton('Read', mainwindow)
    #mainwindow.layout.addRow('', b)
    l.addWidget(b)
    b.pressed.connect(read)

    b = QtWidgets.QPushButton('Write', mainwindow)
    #mainwindow.layout.addRow('', b)
    l.addWidget(b)
    b.pressed.connect(write)

    mainwindow.show()
    sys.exit(app.exec_())
