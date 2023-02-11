# -*- coding: utf-8 -*-

import sys
import os
import xbmc
import xbmcgui
import xbmcvfs
import shutil
import base64
import uuid
from platform import node
from Cryptodome.Cipher import DES3
from Cryptodome.Util.Padding import pad, unpad

from .common import *


class Registration(object):

	def __init__(self):
		self.tempSESS_folder = tempSESS
		self.session_file = sessFile
		self.username = addon.getSetting('username')
		self.password = addon.getSetting('password')
		self.force_encrypt = (True if addon.getSetting('encrypt_credentials') == 'true' else False)

	def get_mac_key(self):
		debug_MS("(config.get_mac_key) ### START get_mac_key ###")
		mac = uuid.getnode()
		try: clear_mac = ':'.join(i + j for i, j in zip(hex(mac)[2:].zfill(12)[::2], hex(mac)[2:].zfill(12)[1::2]))
		except: clear_mac = 'ERROR NO -MAC ADRESS- FOUND'
		if (mac >> 40) % 2:
			mac = node()
		return (str(clear_mac), uuid.uuid5(uuid.NAMESPACE_DNS, str(mac)).bytes)

	def vers_encrypt(self, data):
		MAC_CLEAR, MAC_CODE = self.get_mac_key()
		k = DES3.new(MAC_CODE, DES3.MODE_CBC, iv=b'\0\0\0\0\0\0\0\0')
		d = k.encrypt(pad(data.encode('utf-8'), DES3.block_size))
		return base64.b64encode(d)

	def vers_decrypt(self, data, route='UNKNOWN'):
		if not data:
			return ""
		its_base64 = re.match('^([A-Za-z0-9+/]{4})*([A-Za-z0-9+/]{3}=|[A-Za-z0-9+/]{2}==)?$', data)
		if its_base64 and self.force_encrypt is True:
			debug_MS("(config.vers_decrypt) XXX TESTING (base64.encoded) : {0} = SUCCESS FOR '{1}' XXX".format(its_base64.groups(), route))
			data += "=" * ((4 - len(data) % 4) % 4) # FIX for = TypeError: Incorrect padding
			MAC_CLEAR, MAC_CODE = self.get_mac_key()
			k = DES3.new(MAC_CODE, DES3.MODE_CBC, iv=b'\0\0\0\0\0\0\0\0')
			try:
				d = unpad(k.decrypt(base64.b64decode(data)), DES3.block_size)
				return d.decode('utf-8')
			except:
				if route == 'PASSWORD':
					dialog.ok(addon_id, translation(30507))
					self.clear_credentials()
				return ""
		elif not its_base64 and self.force_encrypt is False:
			debug_MS("(config.vers_decrypt) XXX '{0}' IS NORMAL - NOT BASE64-ENCODED XXX".format(route))
			return data
		else:
			if route == 'PASSWORD':
				dialog.ok(addon_id, translation(30507))
				self.clear_credentials()
			return ""

	def has_credentials(self):
		debug_MS("(config.has_credentials) ### START has_credentials ###")
		if self.username is not None and self.password is not None:
			if len(self.username) > 0 and len(self.password) >= 6:
				return True
		else:
			xbmc.sleep(3000)
			if self.username is not None and self.password is not None:
				if len(self.username) > 0 and len(self.password) >= 6:
					return True
		return False

	def get_credentials(self):
		debug_MS("(config.get_credentials) ### START get_credentials ###")
		return (self.vers_decrypt(self.username, 'USERNAME'), self.vers_decrypt(self.password, 'PASSWORD'))

	def save_credentials(self):
		debug_MS("(config.save_credentials) ### START save_credentials ###")
		USER = dialog.input(translation(30671), type=xbmcgui.INPUT_ALPHANUM)
		PASSWORD = dialog.input(translation(30672), type=xbmcgui.INPUT_ALPHANUM)
		if self.force_encrypt is True:
			_user = self.vers_encrypt(USER) if USER != '' else USER
			_code = self.vers_encrypt(PASSWORD) if PASSWORD != '' else PASSWORD
			debug_MS("(config.save_credentials) XXX encrypt-USER : {0} || encrypt-PASSWORD : {1} XXX".format(_user, _code))
		else:
			_user = USER
			_code = PASSWORD
			debug_MS("(config.save_credentials) XXX standard-USER : {0} || standard-PASSWORD : {1} XXX".format(_user, _code))
		addon.setSetting('username', _user)
		addon.setSetting('password', _code)
		return (USER, PASSWORD)

	def clear_credentials(self):
		debug_MS("(config.clear_credentials) ### START clear_credentials ###")
		addon.setSetting('username', '')
		addon.setSetting('password', '')
		addon.setSetting('select_start', '0')
		if self.session_file is not None and os.path.isfile(self.session_file):
			if xbmcvfs.exists(self.tempSESS_folder) and os.path.isdir(self.tempSESS_folder):
				shutil.rmtree(self.tempSESS_folder, ignore_errors=True)
