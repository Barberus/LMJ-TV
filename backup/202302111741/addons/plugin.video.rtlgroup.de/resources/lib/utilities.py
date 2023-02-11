# -*- coding: utf-8 -*-

import sys
import os
import re
import xbmc
import json
import xbmcvfs
import shutil
import time
import _strptime
from datetime import datetime, timedelta
import requests
try: import cPickle as pickle
except: import pickle
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from .common import *
from .config import Registration


def _header(send_token, REFERRER=None, USERTOKEN=None):
	header = {}
	header['Cache-Control'] = 'no-cache'
	header['Accept'] = 'application/json, text/plain, */*'
	header['User-Agent'] = get_userAgent()
	header['DNT'] = '1'
	header['Upgrade-Insecure-Requests'] = '1'
	header['Accept-Encoding'] = 'gzip'
	header['Accept-Language'] = 'en-US,en;q=0.8,de;q=0.7'
	if REFERRER:
		header['Referer'] = REFERRER
	if USERTOKEN and send_token:
		header['x-auth-token'] = USERTOKEN
	return header

class Transmission(object):

	def __init__(self):
		self.config = Registration
		self.maxTokenTime = 480 * 60 # max. Token-Time (Seconds) before clear the Token and delete Token-File [60*60 = 1 hour | 360*60 = 6 hours | 720*60 = 12 hours]
		self.tempSESS_folder = tempSESS
		self.session_file = sessFile
		self.tempFREE_folder = tempFREE
		self.free_file = freeFile
		self.MATO = (time.time() - self.maxTokenTime) # Date and time now minus 'maxTokenTime'
		self.verify_ssl = (True if addon.getSetting('verify_ssl') == 'true' else False)
		self.auth_TOKEN = addon.getSetting('authtoken')
		self.max_tries = (int(addon.getSetting('maximum_tries')) if addon.getSetting('maximum_tries') != "" else 0)
		self.cache = cache
		self.session = requests.Session()
		self.load_session()

	def clear_special(self, filename, foldername):
		debug_MS("(utilities.clear_special) ### START clear_special ###")
		if filename is not None and os.path.isfile(filename):
			if xbmcvfs.exists(foldername) and os.path.isdir(foldername):
				shutil.rmtree(foldername, ignore_errors=True)

	def save_special(self, filename, foldername, text=""):
		debug_MS("(utilities.save_special) ### START save_special ###")
		if not xbmcvfs.exists(foldername) and not os.path.isdir(foldername):
			xbmcvfs.mkdirs(foldername)
		if filename == self.session_file:
			with open(filename, 'wb') as input:
				pickle.dump(text, input)
		else:
			with open(filename, 'w') as save:
				json.dump(text, save, indent=4, sort_keys=True)

	def load_session(self):
		debug_MS("(utilities.load_session) ### START load_session ###")
		forceRenew = False
		if self.session_file is not None and os.path.isfile(self.session_file):
			if os.path.getmtime(self.session_file) < self.MATO:
				debug_MS("(utilities.load_session) ##### TIMEOUT FOR SESSION - DELETE SESSIONFILE #####")
				forceRenew = True
			else:
				try:
					with open(self.session_file, 'rb') as output:
						self.session = pickle.load(output)
					debug_MS("(utilities.load_session) ##### NOTHING CHANGED - SESSIONFILE OKAY #####")
				except:
					failing("(utilities.load_session) XXXXX !!! ERROR = SESSIONFILE [SESSIONFORMAT IS INVALID] = ERROR !!! XXXXX")
					forceRenew = True
		else:
			debug_MS("(utilities.load_session) ##### NOTHING FOUND - CREATE SESSIONFILE #####")
			forceRenew = True
		if forceRenew:
			if self.session_file is not None and os.path.isfile(self.session_file):
				self.clear_special(self.session_file, self.tempSESS_folder)
			if self.free_file is not None and os.path.isfile(self.free_file):
				self.clear_special(self.free_file, self.tempFREE_folder)
			if addon.getSetting('verified_Account') == 'true':
				self.renewal_login()

	def renewal_login(self):
		lastHM = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
		addon.setSetting('last_starttime', lastHM+' / 02')
		if self.config().has_credentials() is True:
			USER, PWD = self.config().get_credentials()
		else:
			USER, PWD = self.config().save_credentials()
		return self.login(USER, PWD, forceLogin=True)

	def convert_epoch(self, epoch):
		epochCipher = datetime(1970,1,1) + timedelta(seconds=int(epoch))
		return epochCipher.strftime('%d{0}%m{0}%y {1} %H{2}%M').format('.', '•', ':')

	def login(self, username, password, forceLogin=False):
		debug_MS("(utilities.login) ### START ...login-PROCESS - forceLogin = {0} || maxTRIES = {1}/4 ###".format(str(forceLogin), str(self.max_tries)))
		if forceLogin is False and self.session_file is not None and os.path.isfile(self.session_file):
			self.EPFT = os.path.getmtime(self.session_file)
			debug_MS("(utilities.login) ##### SESSION-File-Time (UTC grösser) = {0} || max-Time (UTC kleiner) = {1} #####".format(str(self.convert_epoch(self.EPFT)), str(self.convert_epoch(self.MATO))))
			if self.EPFT > self.MATO:
				return True
		payload = {'email': username, 'password': password}
		login_query = self.retrieveContent(LOGIN_LINK, 'POST', json=payload)
		if self.max_tries > 3:
			addon.setSetting('verified_Account', 'false')
			addon.setSetting('username', '')
			addon.setSetting('password', '')
			addon.setSetting('select_start', '0')
			dialog.ok(addon_id, translation(30507))
			self.clear_special(self.session_file, self.tempSESS_folder)
			return False
		elif str(login_query.get('token'))[:3] == 'eyJ':
			debug_MS("(utilities.login) ##### !!! DU BIST ERFOLGREICH EINGELOGGT !!! #####")
			self.persToken = login_query.get('token')
			debug_MS("(utilities.login) ##### persToken : {0} #####".format(str(self.persToken)))
			addon.setSetting('authtoken', self.persToken)
			self.save_special(self.session_file, self.tempSESS_folder, self.session)
			self.verify_premium(self.persToken)
			return True
		else:
			debug_MS("(utilities.login) XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
			debug_MS("(utilities.login) XXXXX !!! ERROR = DU BIST NICHT EINGELOGGT = ERROR !!! XXXXX")
			debug_MS("(utilities.login) XXXXX LOGIN-ANSWER = {0} XXXXX".format(str(login_query)))
			debug_MS("(utilities.login) XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
			addon.setSetting('login_status', '0')
			if addon.getSetting('maximum_tries') != "":
				next_test = str(int(addon.getSetting('maximum_tries'))+1)
				addon.setSetting('maximum_tries', next_test)
			addon.setSetting('liveFree', 'false')
			addon.setSetting('livePay', 'false')
			addon.setSetting('vodFree', 'false')
			addon.setSetting('vodPay', 'false')
			addon.setSetting('high_definition', 'false')
			addon.setSetting('authtoken', '0')
			addon.setSetting('license_ending', '')
			self.clear_special(self.session_file, self.tempSESS_folder)
		return False

	def verify_premium(self, receivedToken):
		addon.setSetting('login_status', '0')
		addon.setSetting('liveFree', 'false')
		addon.setSetting('livePay', 'false')
		addon.setSetting('vodFree', 'false')
		addon.setSetting('vodPay', 'false')
		b64_string = receivedToken.split('.')[1]
		b64_string += "=" * ((4 - len(b64_string) % 4) % 4)
		debug_MS("(utilities.verify_premium) ##### jsonDATA-Token base64-decoded : {0} #####".format(str(base64.b64decode(b64_string))))
		DATA = json.loads(base64.b64decode(b64_string))
		addon.setSetting('license_ending', '')
		if DATA.get('licenceEndDate', ''):
			try:
				ENDING = datetime(*(time.strptime(DATA['licenceEndDate'][:19], '%Y{0}%m{0}%dT%H{1}%M{1}%S'.format('-', ':'))[0:6]))# 2019-11-05T18:09:41+00:00
				lic_END = ENDING.strftime('%d{0}%m{0}%y {1} %H{2}%M').format('.', '•', ':')
				addon.setSetting('license_ending', str(lic_END))
			except: pass
		if DATA.get('subscriptionState', '') in [4, 5] or 'premium' in DATA.get('roles', ''):
			if DATA.get('subscriptionState', '') in [4, 5]:
				debug_MS("(utilities.verify_premium) ##### Paying-Member : subscriptionState = {0} = (Account is OK) #####".format(str(DATA["subscriptionState"])))
			else: debug_MS("(utilities.verify_premium) ##### Paying-Member : roles = {0} = (Account is OK) #####".format(str(DATA['roles'])))
			addon.setSetting('vodPay', 'true')
			addon.setSetting('login_status', '3')
			debug_MS("(utilities.verify_premium) ##### END-CHECK = Setting(vodPremium) : {0} #####".format(str(addon.getSetting("vodPay"))))
		if DATA.get('permissions', ''):
			debug_MS("(utilities.verify_premium) ##### checking-User-Packages in 'permissions RULES' #####")
			if DATA.get('permissions', {}).get('liveFree', '') is True:
				addon.setSetting('liveFree', 'true')
			if DATA.get('permissions', {}).get('livePay', '') is True:
				addon.setSetting('livePay', 'true')
			if DATA.get('permissions', {}).get('vodFree', '') is True:
				addon.setSetting('vodFree', 'true')
			if DATA.get('permissions', {}).get('vodPremium', '') is True:
				addon.setSetting('vodPay', 'true')
				addon.setSetting('login_status', '3')
			debug_MS("(utilities.verify_premium) ##### END-CHECK = Setting(liveGratis) : {0} #####".format(str(addon.getSetting("liveFree"))))
			debug_MS("(utilities.verify_premium) ##### END-CHECK = Setting(livePremium) : {0} #####".format(str(addon.getSetting("livePay"))))
			debug_MS("(utilities.verify_premium) ##### END-CHECK = Setting(vodGratis) : {0} #####".format(str(addon.getSetting("vodFree"))))
			debug_MS("(utilities.verify_premium) ##### END-CHECK = Setting(vodPremium) : {0} #####".format(str(addon.getSetting("vodPay"))))
		if addon.getSetting('login_status') != '3':
			debug_MS("(utilities.verify_premium) ##### Free-Member = Your Free-Account is OK #####")
			addon.setSetting('login_status', '2')
			addon.setSetting('high_definition', 'false')
			debug_MS("(utilities.verify_premium) ##### END-CHECK = Setting(vodPremium) : {0} #####".format(str(addon.getSetting("vodPay"))))
		debug_MS("(utilities.verify_premium) <<<<< Ende LOGIN <<<<<")

	def logout(self):
		debug_MS("(utilities.logout) ### START logout the Session... ###")
		self.clear_special(self.session_file, self.tempSESS_folder)
		xbmc.sleep(1000)
		logout_res = self.retrieveContent(REFRESH_LINK, method='TRACK')
		index_LoggedOUT = re.search(r'"error":"InvalidLogin"', logout_res.text)
		if index_LoggedOUT:
			debug_MS("(utilities.logout) ##### !!! DIE SESSION WURDE ERFOLGREICH BEENDET !!! #####")
			addon.setSetting('vodPay', 'false')
			return True
		return False

	def check_FreeToken(self, targetID, targetCOND):
		debug_MS("(utilities.check_FreeToken) ### START check_FreeToken ###")
		forceRenew, free_AUTH, USER_ACCESS = False, '0', False
		if self.free_file is not None and os.path.isfile(self.free_file):
			try:
				with open(self.free_file, 'r') as publish:
					free_AUTH = json.load(publish)['accessToken']
				debug_MS("(utilities.check_FreeToken) ##### NOTHING CHANGED - TOKENFILE OKAY #####")
				addon.setSetting('login_status', '1')
			except:
				failing("(utilities.check_FreeToken) XXXXX !!! ERROR = TOKENFILE [TOKENFORMAT IS INVALID] = ERROR !!! XXXXX")
				forceRenew = True
		else:
			debug_MS("(utilities.check_FreeToken) ##### NOTHING FOUND - CREATE TOKENFILE #####")
			forceRenew = True
		if forceRenew:
			if self.free_file is not None and os.path.isfile(self.free_file):
				self.clear_special(self.free_file, self.tempFREE_folder)
			if self.session_file is not None and os.path.isfile(self.session_file):
				self.clear_special(self.session_file, self.tempSESS_folder)
			nomURL = 'https://bff.apigw.tvnow.de/player/{0}'.format(targetID)
			if targetCOND == 'eventURL':
				nomURL = 'https://bff.apigw.tvnow.de/player/live/{0}?version=v6'.format(targetID)
			try:
				USER_ACCESS = self.retrieveContent(nomURL)['pageConfig']['user']['jwt']
				if USER_ACCESS:
					MAC_CLEAR, MAC_CODE = Registration().get_mac_key()
					CODING = {'accessToken': USER_ACCESS, 'clientId': MAC_CLEAR}
					debug_MS("(utilities.check_FreeToken) ### NEW TOKENFILE CREATED : {0} ### ".format(str(CODING)))
					self.save_special(self.free_file, self.tempFREE_folder, CODING)
					self.save_special(self.session_file, self.tempSESS_folder, self.session)
					addon.setSetting('login_status', '1')
					free_AUTH = USER_ACCESS
			except:
				failing("(utilities.check_FreeToken) ##### persToken : Gesuchtes Token-Dokument NICHT gefunden !!! #####")
				dialog.notification(translation(30521).format('Token nicht gefunden', ''), translation(30581), icon, 12000)
		return free_AUTH

	def makeREQUEST(self, url, method='GET', REF=None):
		content = self.cache.cacheFunction(self.retrieveContent, url, method, REF)
		return content

	def retrieveContent(self, url, method='GET', REF=None, headers=None, cookies=None, allow_redirects=True, stream=None, data=None, json=None):
		send_token = True if method in ['GET', 'TRACK'] and addon.getSetting('verified_Account') == 'true' and self.auth_TOKEN != '0' else False
		ANSWER = None
		try:
			if method in ['GET', 'TRACK']:
				result = self.session.get(url, headers=_header(send_token, REF, self.auth_TOKEN), allow_redirects=allow_redirects, verify=self.verify_ssl, stream=stream, timeout=30)
			elif method == 'POST':
				result = self.session.post(url, headers=_header(send_token, REF, self.auth_TOKEN), allow_redirects=allow_redirects, verify=self.verify_ssl, data=data, json=json, timeout=30)
			ANSWER = result.json() if method in ['GET', 'POST'] else result
			debug_MS("(utilities.retrieveContent) === CALLBACK === status : {} || url : {} || header : {} ===".format(str(result.status_code), result.url, result.request.headers))
		except requests.exceptions.RequestException as e:
			failing("(utilities.retrieveContent) ERROR - ERROR - ERROR : ##### url: {0} === error: {1} #####".format(url, str(e)))
			dialog.notification(translation(30521).format('URL', ''), translation(30523).format(str(e)), icon, 12000)
			return sys.exit(0)
		return ANSWER
