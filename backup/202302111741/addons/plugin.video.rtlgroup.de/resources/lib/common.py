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
import socket
import time
import _strptime
from datetime import datetime, timedelta
from calendar import timegm as TGM
import base64
import uuid
import requests
import io
PY2 = sys.version_info[0] == 2
if PY2:
	from urllib import urlencode, quote, quote_plus, unquote, unquote_plus  # Python 2.X
	TRANS_PATH, LOG_MESSAGE, INPUT_APP = xbmc.translatePath, xbmc.LOGNOTICE, 'inputstreamaddon' # Stand: 05.12.20 / Python 2.X
else:
	from urllib.parse import urlencode, quote, quote_plus, unquote, unquote_plus  # Python 3.X
	TRANS_PATH, LOG_MESSAGE, INPUT_APP = xbmcvfs.translatePath, xbmc.LOGINFO, 'inputstream' # Stand: 05.12.20  / Python 3.X
try: import StorageServer
except: from . import storageserverdummy as StorageServer
from Cryptodome.Cipher import DES3
from Cryptodome.Util.Padding import pad, unpad
from inputstreamhelper import Helper
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


socket.setdefaulttimeout(40)
HOST_AND_PATH               = sys.argv[0]
ADDON_HANDLE                = int(sys.argv[1])
dialog                                    = xbmcgui.Dialog()
addon                                    = xbmcaddon.Addon()
addon_id                              = addon.getAddonInfo('id')
addon_name                       = addon.getAddonInfo('name')
addon_version                    = addon.getAddonInfo('version')
addonPath                           = TRANS_PATH(addon.getAddonInfo('path')).encode('utf-8').decode('utf-8')
dataPath                              = TRANS_PATH(addon.getAddonInfo('profile')).encode('utf-8').decode('utf-8')
tempSESS                             = TRANS_PATH(os.path.join(dataPath, 'tempSESS', '')).encode('utf-8').decode('utf-8')
tempFREE                             = TRANS_PATH(os.path.join(dataPath, 'tempFREE', '')).encode('utf-8').decode('utf-8')
sessFile                                 = os.path.join(tempSESS, 'COOKIE')
freeFile                                 = os.path.join(tempFREE, 'TOKEN')
searchHackFile                   = os.path.join(dataPath, 'searchString')
channelFavsFile                  = os.path.join(dataPath, 'favorites_RTLPLUS.json')
defaultFanart                      = (os.path.join(addonPath, 'fanart.jpg') if PY2 else os.path.join(addonPath, 'resources', 'media', 'fanart.jpg'))
icon                                       = (os.path.join(addonPath, 'icon.png') if PY2 else os.path.join(addonPath, 'resources', 'media', 'icon.png'))
artpic                                    = os.path.join(addonPath, 'resources', 'media', '').encode('utf-8').decode('utf-8')
alppic                                    = os.path.join(addonPath, 'resources', 'media', 'alphabet', '').encode('utf-8').decode('utf-8')
genpic                                   = os.path.join(addonPath, 'resources', 'media', 'genre', '').encode('utf-8').decode('utf-8')
stapic                                     = os.path.join(addonPath, 'resources', 'media', 'channel', '').encode('utf-8').decode('utf-8')
username                             = addon.getSetting('username')
password                              = addon.getSetting('password')
AUTH_Token                        = addon.getSetting('authtoken')
force_encryption                = addon.getSetting('encrypt_credentials')
START_MODUS                    = addon.getSetting('select_start')
liveGratis                              = (True if addon.getSetting('liveFree') == 'true' else False)
livePremium                        = (True if addon.getSetting('livePay') == 'true' else False)
vodGratis                              = (True if addon.getSetting('vodFree') == 'true' else False)
vodPremium                        = (True if addon.getSetting('vodPay') == 'true' else False)
STATUS                                 = int(addon.getSetting('login_status'))
cachePERIOD                      = int(addon.getSetting('cache_rhythm'))
cache                                    = StorageServer.StorageServer(addon_id, cachePERIOD) # (Your plugin name, Cache time in hours)
forceBEST                            = addon.getSetting('force_best')
selectionHD                         = (True if addon.getSetting('high_definition') == 'true' else False)
prefCONTENT                      = addon.getSetting('prefer_content')
SORTING                              = addon.getSetting('sorting_technique')
markMOVIES                       = addon.getSetting('mark_movies') == 'true'
showDATE                            = addon.getSetting('show_date') == 'true'
useSerieAsFanart                = addon.getSetting('useSerieAsFanart') == 'true'
verify_ssl_connect              = (True if addon.getSetting('verify_ssl') == 'true' else False)
enableADJUSTMENT           = addon.getSetting('show_settings') == 'true'
DEB_LEVEL                           = (LOG_MESSAGE if addon.getSetting('enableDebug') == 'true' else xbmc.LOGDEBUG)
enableLIBRARY                   = addon.getSetting('tvnow_library') == 'true'
mediaPath                            = addon.getSetting('mediapath')
newMETHOD                        = addon.getSetting('new_separation') == 'true'
libraryPERIOD                     = addon.getSetting('library_rhythm')
kodibuild                               = int(xbmc.getInfoLabel('System.BuildVersion')[0:2])
KODI_ov18                          = int(xbmc.getInfoLabel('System.BuildVersion')[0:2]) >= 18
IMG_tvepg                           = 'https://aistvnow-a.akamaihd.net/tvnow/epg/{}/960x0/image.jpg'
IMG_series                           = 'https://aistvnow-a.akamaihd.net/tvnow/format/{}_02logo/image.jpg'
IMG_movies                         = 'https://aistvnow-a.akamaihd.net/tvnow/movie/{}/1200x0/image.jpg'
IMG_coverdvd                     = 'https://aistvnow-a.akamaihd.net/tvnow/format/{}_08coverdvd/600x0/image.jpg'
BASE_URL                             = 'https://www.tvnow.de/'
API_URL                               = 'https://api.tvnow.de/v3'
LOGIN_LINK                        = 'https://auth.tvnow.de/login'
REFRESH_LINK                   = 'https://auth.tvnow.de/refresh'
LICENSE_URL                      = 'https://widevine.tvnow.de/index/{0}|{1}&x-auth-token={2}&Content-Type=application/x-www-form-urlencoded|{3}|'
# https://widevine.tvnow.de/index/livestream || https://widevine.tvnow.de/index/license || https://widevine.tvnow.de/index/proxy

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
	if not PY3 and isinstance(d, bytes):
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

def clearCache():
	debug_MS("(common.clearCache) -------------------------------------------------- START = clearCache --------------------------------------------------")
	debug_MS("(common.clearCache) ========== Lösche jetzt den Addon-Cache ==========")
	cache.delete('%')
	xbmc.sleep(1000)
	dialog.ok(addon_id, translation(30505))

def get_Local_DT(utcDT):
	try:
		localDT = datetime.fromtimestamp(TGM(utcDT.timetuple()))
		assert utcDT.resolution >= timedelta(microseconds=1)
		localDT = localDT.replace(microsecond=utcDT.microsecond)
	except (ValueError, OverflowError): # ERROR on Android 32bit Systems = cannot convert unix timestamp over year 2038
		localDT = datetime.fromtimestamp(0) + timedelta(seconds=TGM(utcDT.timetuple()))
		localDT = localDT - timedelta(hours=datetime.timetuple(localDT).tm_isdst)
	return localDT

def get_Description(info, event='EP'):
	if event == 'EP':
		if 'articleLong' in info and info['articleLong'] and len(info['articleLong']) > 10:
			return cleaning(info['articleLong'])
		elif 'articleShort' in info and info['articleShort'] and len(info['articleShort']) > 10:
			return cleaning(info['articleShort'])
	else:
		if 'infoTextLong' in info and info['infoTextLong'] and len(info['infoTextLong']) > 10:
			return cleaning(info['infoTextLong'])
		elif 'infoText' in info and info['infoText'] and len(info['infoText']) > 10:
			return cleaning(info['infoText'])
	return ""

def get_Time(info, event='SECONDS', roundTo=60):
	try:
		info = re.sub('[a-z]', '', info)
		secs = sum(x * int(t) for x, t in zip([1, 60, 3600], reversed(info.split(':'))))
		mins = (secs+roundTo/2) // roundTo * roundTo /60
		if event == 'SECONDS':
			return "{0:.0f}".format(secs)
		return "{0:.0f}".format(mins)
	except: return '0'

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

def cleanPhoto(img): # UNICODE-Zeichen für Browser übersetzen - damit Fotos angezeigt werden
	img = quote(py2_enc(img), safe='/:')
	img = img.replace('http:', 'https:') if img[:5] == 'http:' else img
	if img.count('%') == img.count('%25'): # It's double QUOTED (Umlaute z.B. 'ö' zu falsch='%25C3%25B6' richtig='%C3%B6')
		img = unquote(img)
	return img.strip()

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
action = unquote_plus(params.get('action', 'DEFAULT'))
origSERIE = unquote_plus(params.get('origSERIE', ''))
photo = unquote_plus(params.get('photo', ''))
extras = unquote_plus(params.get('extras', 'standard'))
searching = unquote_plus(params.get('searching', 'None'))
type = unquote_plus(params.get('type', 'episode'))
cycle = unquote_plus(params.get('cycle', '0'))

xcode = unquote_plus(params.get('xcode', '')) if params.get('xcode') else None
xlink = unquote_plus(params.get('xlink', '')) if params.get('xlink') else None
xdrm = unquote_plus(params.get('xdrm', '')) if params.get('xdrm') else None
xfree = unquote_plus(params.get('xfree', '')) if params.get('xfree') else None
xtele = unquote_plus(params.get('xtele', 'UNK'))
