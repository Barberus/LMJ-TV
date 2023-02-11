# -*- coding: utf-8 -*-

import sys
import os
import re
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import json
import xbmcvfs
import shutil
import time
import _strptime
from datetime import datetime, timedelta
from calendar import timegm as TGM
import requests
import io
PY2 = sys.version_info[0] == 2
if PY2:
	from urllib import urlencode, quote_plus, unquote_plus  # Python 2.X
	from .external.concurrent.futures import *
	TRANS_PATH, LOG_MESSAGE, INPUT_APP = xbmc.translatePath, xbmc.LOGNOTICE, 'inputstreamaddon' # Stand: 05.12.20 / Python 2.X
else:
	from urllib.parse import urlencode, quote_plus, unquote_plus  # Python 3.X
	from concurrent.futures import *
	TRANS_PATH, LOG_MESSAGE, INPUT_APP = xbmcvfs.translatePath, xbmc.LOGINFO, 'inputstream' # Stand: 05.12.20  / Python 3.X
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


HOST_AND_PATH                 = sys.argv[0]
ADDON_HANDLE                  = int(sys.argv[1])
dialog                                      = xbmcgui.Dialog()
addon                                     = xbmcaddon.Addon()
addon_id                                = addon.getAddonInfo('id')
addon_name                         = addon.getAddonInfo('name')
addon_version                      = addon.getAddonInfo('version')
addonPath                             = TRANS_PATH(addon.getAddonInfo('path')).encode('utf-8').decode('utf-8')
dataPath                                = TRANS_PATH(addon.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
channelFavsFile                    = os.path.join(dataPath, 'favorites_DMAX.json')
defaultFanart                        = (os.path.join(addonPath, 'fanart.jpg') if PY2 else os.path.join(addonPath, 'resources', 'media', 'fanart.jpg'))
icon                                         = (os.path.join(addonPath, 'icon.png') if PY2 else os.path.join(addonPath, 'resources', 'media', 'icon.png'))
artpic                                      = os.path.join(addonPath, 'resources', 'media', '').encode('utf-8').decode('utf-8')
alppic                                      = os.path.join(addonPath, 'resources', 'media', 'alphabet', '').encode('utf-8').decode('utf-8')
SORTING                                = addon.getSetting('sorting_technique')
FORCE_SCRIPT                     = addon.getSetting('force_scene') == 'true'
useThumbAsFanart              = addon.getSetting('useThumbAsFanart') == 'true'
enableADJUSTMENT             = addon.getSetting('show_settings') == 'true'
DEB_LEVEL                             = (LOG_MESSAGE if addon.getSetting('enableDebug') == 'true' else xbmc.LOGDEBUG)
enableLIBRARY                     = addon.getSetting('dmax_library') == 'true'
mediaPath                              = addon.getSetting('mediapath')
newMETHOD                         = addon.getSetting('new_separation') == 'true'
libraryPERIOD                       = addon.getSetting('library_rhythm')
PRIMARY_CHANNEL            = '94' # '94' = DMAX // '148' = HGTV // '95' = TLC // '626' = TELE5
ACCESS_URL                          = 'https://eu1-prod.disco-api.com/token?realm=dmaxde'
BASE_API                               = 'https://eu1-prod.disco-api.com'
BASE_URL                               = 'https://dmax.de/'
KODI_ov20                             = int(xbmc.getInfoLabel('System.BuildVersion')[0:2]) >= 20

xbmcplugin.setContent(ADDON_HANDLE, 'tvshows')

def py2_enc(s, nom='utf-8', ign='ignore'):
	if PY2:
		if not isinstance(s, basestring):
			s = str(s)
		s = s.encode(nom, ign) if isinstance(s, unicode) else s
	return s

def py2_uni(s, nom='utf-8', ign='ignore'):
	if PY2 and isinstance(s, str):
		s = unicode(s, nom, ign)
	return s

def py3_dec(d, nom='utf-8', ign='ignore'):
	if not PY2 and isinstance(d, bytes):
		d = d.decode(nom, ign)
	return d

def translation(id):
	return py2_enc(addon.getLocalizedString(id))

def failing(content):
	log(content, xbmc.LOGERROR)

def debug_MS(content):
	log(content, DEB_LEVEL)

def log(msg, level=LOG_MESSAGE): # kompatibel mit Python-2 und Python-3
	msg = py2_enc(msg)
	return xbmc.log('[{0} v.{1}]{2}'.format(addon_id, addon_version, msg), level)

def get_userAgent():
	base = 'Mozilla/5.0 {0} AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36'
	if xbmc.getCondVisibility('System.Platform.Android'):
		if 'arm' in os.uname()[4]: return base.format('(X11; CrOS armv7l 7647.78.0)') # ARM based Linux
		return base.format('(X11; Linux x86_64)') # x86 Linux
	elif xbmc.getCondVisibility('System.Platform.Windows'):
		return base.format('(Windows NT 10.0; WOW64)') # Windows
	elif xbmc.getCondVisibility('System.Platform.IOS'):
		return base.format('(iPhone; CPU iPhone OS 10_3 like Mac OS X)') # iOS iPhone/iPad
	elif xbmc.getCondVisibility('System.Platform.Darwin'):
		return base.format('(Macintosh; Intel Mac OS X 10_10_1)') # Mac OSX
	return base.format('(X11; Linux x86_64)') # x86 Linux

def _header(REFERRER=None, USERTOKEN=None):
	header = {}
	header['Connection'] = 'keep-alive'
	header['Pragma'] = 'no-cache'
	header['Cache-Control'] = 'no-cache'
	header['Accept'] = 'application/json, text/javascript, */*; q=0.01'
	header['User-Agent'] = get_userAgent()
	header['DNT'] = '1'
	header['Upgrade-Insecure-Requests'] = '1'
	header['Accept-Encoding'] = 'gzip'
	header['Accept-Language'] = 'en-US,en;q=0.8,de;q=0.7'
	if REFERRER:
		header['Referer'] = REFERRER
	if USERTOKEN:
		header['Authorization'] = 'Bearer {}'.format(USERTOKEN)
	return header

def getMultiData(MURLS, method='GET', REF=None, AUTH=None, fields=None):
	COMBI_NEW = []
	number = len(MURLS)
	counter = 0
	def download(pos, url, token, cmanager):
		response = cmanager.request(method, url, fields, headers=_header(REF, token), timeout=5, retries=2)
		if response and response.status == 200:
			debug_MS("(common.getMultiData) === URL that wanted : {0} ===".format(url))
			return '{"Position":'+str(pos)+',"firstURL":"'+url+'",'+py3_dec(response.data[1:-1])+'}'
		else:
			failing("(common.getMultiData) ERROR - ERROR - ERROR ##### pos: {} === status: {} === url: {} #####".format(str(pos), str(response.status), url))
			return '{"ERROR_occurred":true}'
	with ThreadPoolExecutor() as executor:
		conn_mgr = urllib3.PoolManager(maxsize=10, block=True)
		entrance = requests.get(ACCESS_URL, headers=_header(REF, AUTH), allow_redirects=False, verify=True, timeout=30).json()
		auth_TK = entrance['data']['attributes']['token']
		future_connect = [executor.submit(download, pos, url, auth_TK, conn_mgr) for pos, url in MURLS]
		wait(future_connect, timeout=30, return_when=ALL_COMPLETED)
		for ii, future in enumerate(as_completed(future_connect), 1):
			try:
				COMBI_NEW.append(json.loads(future.result()))
				if ii == number:
					for item in COMBI_NEW:
						if item.get('ERROR_occurred', '') is True: counter += 1
					if counter == number:
						dialog.notification(translation(30521).format('DETAILS', ''), translation(30524), icon, 10000)
			except Exception as e:
				failing("(common.getMultiData) ERROR - ERROR - ERROR ##### no: {} === url: {} === error: {} #####".format(str(ii), url, str(e)))
				dialog.notification(translation(30521).format('URL', ''), translation(30523).format(str(e)), icon, 10000)
				executor.shutdown()
				return sys.exit(0)
		return json.dumps(COMBI_NEW, indent=2)

def getUrl(url, method='GET', REF=None, headers=None, cookies=None, allow_redirects=False, verify=True, stream=None, data=None, json=None):
	simple = requests.Session()
	ANSWER, auth_TK = (None for _ in range(2))
	try:
		entrance = simple.get(ACCESS_URL, headers=_header(REF, auth_TK), allow_redirects=allow_redirects, verify=verify, stream=stream, timeout=30).json()
		auth_TK = entrance['data']['attributes']['token']
		response = simple.get(url, headers=_header(REF, auth_TK), allow_redirects=allow_redirects, verify=verify, stream=stream, timeout=30)
		ANSWER = response.json() if method in ['GET', 'POST'] else py2_enc(response.text)
		debug_MS("(common.getUrl) === CALLBACK === status : {} || url : {} || header : {} ===".format(str(response.status_code), response.url, response.request.headers))
		if method == 'GET' and response.json().get('errors', ''):
			detail = (py2_enc(response.json().get('errors', {})[0].get('detail', '')) or 'NO DETAILS FOUND')
			failing("(common.getUrl) ERROR - ERROR - ERROR ##### {} === {} #####".format(url, detail))
			dialog.notification(translation(30521).format('URL', ''), translation(30523).format(detail), icon, 10000)
			return sys.exit(0)
	except requests.exceptions.RequestException as e:
		failing("(common.getUrl) ERROR - ERROR - ERROR ##### url: {} === error: {} #####".format(url, str(e)))
		dialog.notification(translation(30521).format('URL', ''), translation(30523).format(str(e)), icon, 10000)
		return sys.exit(0)
	return ANSWER

def ADDON_operate(IDD):
	js_query = xbmc.executeJSONRPC('{{"jsonrpc":"2.0", "id":1, "method":"Addons.GetAddonDetails", "params":{{"addonid":"{}", "properties":["enabled"]}}}}'.format(IDD))
	if '"enabled":false' in js_query:
		try:
			xbmc.executeJSONRPC('{{"jsonrpc":"2.0", "id":1, "method":"Addons.SetAddonEnabled", "params":{{"addonid":"{}", "enabled":true}}}}'.format(IDD))
			failing("(common.ADDON_operate) ERROR - ERROR - ERROR :\n##### Das benötigte Addon : *{0}* ist NICHT aktiviert !!! #####\n##### Es wird jetzt versucht die Aktivierung durchzuführen !!! #####".format(IDD))
		except: pass
	if '"error":' in js_query:
		dialog.ok(addon_id, translation(30501).format(IDD))
		failing("(common.ADDON_operate) ERROR - ERROR - ERROR :\n##### Das benötigte Addon : *{0}* ist NICHT installiert !!! #####".format(IDD))
		return False
	if '"enabled":true' in js_query:
		return True

def get_Local_DT(info):
	fixed_format = '%Y{0}%m{0}%dT%H{1}%M{1}%S'.format('-', ':') # 2022-06-18T14:10:00Z
	utcDT = datetime(*(time.strptime(info, fixed_format)[0:6]))
	try:
		localDT = datetime.fromtimestamp(TGM(utcDT.timetuple()))
		assert utcDT.resolution >= timedelta(microseconds=1)
		localDT = localDT.replace(microsecond=utcDT.microsecond)
	except (ValueError, OverflowError): # ERROR on Android 32bit Systems = cannot convert unix timestamp over year 2038
		localDT = datetime.fromtimestamp(0) + timedelta(seconds=TGM(utcDT.timetuple()))
		localDT = localDT - timedelta(hours=datetime.timetuple(localDT).tm_isdst)
	return localDT

def get_Time(info, event='SECONDS', roundTo=60):
	secs = int(info)/1000
	mins = (secs+roundTo/2) // roundTo * roundTo /60
	if event == 'SECONDS':
		return "{0:.0f}".format(secs)
	return "{0:.0f}".format(mins)

def getSorting():
	return [xbmcplugin.SORT_METHOD_UNSORTED, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE, xbmcplugin.SORT_METHOD_DURATION, xbmcplugin.SORT_METHOD_EPISODE, xbmcplugin.SORT_METHOD_DATE]

def repair_vokals(wrong):
	wrong = py2_enc(wrong)
	for n in (('Ã¤', 'ä'), ('Ã„', 'Ä'), ('Ã¶', 'ö'), ('Ã–', 'Ö'), ('Ã¼', 'ü'), ('Ãœ', 'Ü'), ('ÃŸ', 'ß'), ('â€ž', '„'), ('â€œ', '“'), ('â€™', '’'), ('â€“', '–'), ('Ã¡', 'á'), ('Ã©', 'é'), ('Ã¨', 'è')):
				wrong = wrong.replace(*n)
	return wrong.strip()

def cleaning(text):
	if text is not None:
		text = py2_enc(text)
		for n in (('&lt;', '<'), ('&gt;', '>'), ('&amp;', '&'), ('&Amp;', '&'), ('&apos;', "'"), ("&quot;", "\""), ("&Quot;", "\""), ('&szlig;', 'ß'), ('&mdash;', '-'), ('&ndash;', '-'), ('&nbsp;', ' '), ('&hellip;', '...'), ('\xc2\xb7', '-'),
					("&#x27;", "'"), ('&#34;', '"'), ('&#39;', '\''), ('&#039;', '\''), ('&#x00c4', 'Ä'), ('&#x00e4', 'ä'), ('&#x00d6', 'Ö'), ('&#x00f6', 'ö'), ('&#x00dc', 'Ü'), ('&#x00fc', 'ü'), ('&#x00df', 'ß'), ('&#xD;', ''),
					('&#xC4;', 'Ä'), ('&#xE4;', 'ä'), ('&#xD6;', 'Ö'), ('&#xF6;', 'ö'), ('&#xDC;', 'Ü'), ('&#xFC;', 'ü'), ('&#xDF;', 'ß'), ('&#x201E;', '„'), ('&#xB4;', '´'), ('&#x2013;', '-'), ('&#xA0;', ' '),
					('&Auml;', 'Ä'), ('&Euml;', 'Ë'), ('&Iuml;', 'Ï'), ('&Ouml;', 'Ö'), ('&Uuml;', 'Ü'), ('&auml;', 'ä'), ('&euml;', 'ë'), ('&iuml;', 'ï'), ('&ouml;', 'ö'), ('&uuml;', 'ü'), ('&#376;', 'Ÿ'), ('&yuml;', 'ÿ'),
					('&agrave;', 'à'), ('&Agrave;', 'À'), ('&aacute;', 'á'), ('&Aacute;', 'Á'), ('&acirc;', 'â'), ('&Acirc;', 'Â'), ('&egrave;', 'è'), ('&Egrave;', 'È'), ('&eacute;', 'é'), ('&Eacute;', 'É'), ('&ecirc;', 'ê'), ('&Ecirc;', 'Ê'),
					('&igrave;', 'ì'), ('&Igrave;', 'Ì'), ('&iacute;', 'í'), ('&Iacute;', 'Í'), ('&icirc;', 'î'), ('&Icirc;', 'Î'), ('&ograve;', 'ò'), ('&Ograve;', 'Ò'), ('&oacute;', 'ó'), ('&Oacute;', 'Ó'), ('&ocirc;', 'ô'), ('&Ocirc;', 'Ô'),
					('&ugrave;', 'ù'), ('&Ugrave;', 'Ù'), ('&uacute;', 'ú'), ('&Uacute;', 'Ú'), ('&ucirc;', 'û'), ('&Ucirc;', 'Û'), ('&yacute;', 'ý'), ('&Yacute;', 'Ý'),
					('&atilde;', 'ã'), ('&Atilde;', 'Ã'), ('&ntilde;', 'ñ'), ('&Ntilde;', 'Ñ'), ('&otilde;', 'õ'), ('&Otilde;', 'Õ'), ('&Scaron;', 'Š'), ('&scaron;', 'š'), ('&ccedil;', 'ç'), ('&Ccedil;', 'Ç'),
					('&alpha;', 'a'), ('&Alpha;', 'A'), ('&aring;', 'å'), ('&Aring;', 'Å'), ('&aelig;', 'æ'), ('&AElig;', 'Æ'), ('&epsilon;', 'e'), ('&Epsilon;', 'Ε'), ('&eth;', 'ð'), ('&ETH;', 'Ð'), ('&gamma;', 'g'), ('&Gamma;', 'G'),
					('&oslash;', 'ø'), ('&Oslash;', 'Ø'), ('&theta;', 'θ'), ('&thorn;', 'þ'), ('&THORN;', 'Þ'), ('&bull;', '•'), ('&iexcl;', '¡'), ('&iquest;', '¿'), ('&copy;', '(c)'), ('\t', '    '), ('<br />', ' - '),
					("&rsquo;", "’"), ("&lsquo;", "‘"), ("&sbquo;", "’"), ('&rdquo;', '”'), ('&ldquo;', '“'), ('&bdquo;', '”'), ('&rsaquo;', '›'), ('lsaquo;', '‹'), ('&raquo;', '»'), ('&laquo;', '«'),
					('\\xC4', 'Ä'), ('\\xE4', 'ä'), ('\\xD6', 'Ö'), ('\\xF6', 'ö'), ('\\xDC', 'Ü'), ('\\xFC', 'ü'), ('\\xDF', 'ß'), ('\\x201E', '„'), ('\\x28', '('), ('\\x29', ')'), ('\\x2F', '/'), ('\\x2D', '-'), ('\\x20', ' '), ('\\x3A', ':'), ("\\'", "'")):
					text = text.replace(*n)
		text = text.strip()
	return text

def fixPathSymbols(structure): # Sonderzeichen für Pfadangaben entfernen
	structure = structure.strip()
	structure = structure.replace(' ', '_')
	structure = re.sub('[{@$%#^\\/;,:*?!\"+<>|}]', '_', structure)
	structure = structure.replace('______', '_').replace('_____', '_').replace('____', '_').replace('___', '_').replace('__', '_')
	if structure.startswith('_'):
		structure = structure[structure.rfind('_')+1:]
	if structure.endswith('_'):
		structure = structure[:structure.rfind('_')]
	return structure

def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split('&')
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

params = parameters_string_to_dict(sys.argv[2])
name = unquote_plus(params.get('name', ''))
url = unquote_plus(params.get('url', ''))
pict = unquote_plus(params.get('pict', ''))
plot = unquote_plus(params.get('plot', ''))
mode = unquote_plus(params.get('mode', 'root'))
action = unquote_plus(params.get('action', ''))
page = unquote_plus(params.get('page', '1'))
position = unquote_plus(params.get('position', '0'))
origSERIE = unquote_plus(params.get('origSERIE', ''))
extras = unquote_plus(params.get('extras', 'standard'))
cineType = unquote_plus(params.get('cineType', 'episode'))
cycle = unquote_plus(params.get('cycle', '0'))
