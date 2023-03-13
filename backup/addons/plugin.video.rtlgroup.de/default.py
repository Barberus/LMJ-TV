# -*- coding: utf-8 -*-

'''
    Copyright (C) 2023 realvito

    RTLPLUS - V.3

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.
'''

import os
import xbmc
import xbmcaddon
import xbmcvfs
import _strptime
from datetime import datetime
from resources.lib.common import *
from resources.lib import mediatools
from resources.lib import navigator
import inputstreamhelper


def run():
	if mode in ['root', 'playDash']: ##### Exchange old Setting (encrypt_credentials) to new Setting (encrypted) #####
		DONE = False    ##### [plugin.video.rtlgroup.de v.1.1.1+v.1.1.2] - 18.02.2023+24.02.2023 #####
		firstSCRIPT = xbmcvfs.translatePath(os.path.join('special://home{0}addons{0}{1}{0}lib{0}'.format(os.sep, addon_id))).encode('utf-8').decode('utf-8')
		UNO = os.path.join(firstSCRIPT, 'only_at_FIRSTSTART')
		if xbmcvfs.exists(UNO):
			log("(default.run=onlyFISRTTIME) ### Starte Aktion setze neuen Eintrag in SETTINGS ('encrypted') - UEBERTRAGE EINTRAG VOM SCHALTER IN ALTEN SETTINGS ###")
			sourceUSER = xbmcvfs.translatePath(os.path.join('special://home{0}userdata{0}addon_data{0}{1}{0}'.format(os.sep, addon_id))).encode('utf-8').decode('utf-8')
			if not xbmcvfs.exists(sourceUSER):
				xbmcvfs.mkdirs(sourceUSER)
			varSetting = xbmcaddon.Addon(addon_id).getSetting('encrypt_credentials')
			if varSetting in ['false', 'true']:
				newENT = ('JA - ENCRYPTED' if varSetting == 'true' else 'NEIN - NICHT ENCRYPTED')
				xbmcaddon.Addon(addon_id).setSetting('encrypted', newENT)
				log("(default.run=onlyFISRTTIME) ~~~ SUCCES = setze neue Einstellung : * <setting id='encrypted'>{}</setting> * ~~~".format(newENT))
			else:
				log("(default.run=onlyFISRTTIME) ~~~ SKIPPED/FAILED = neue Einstellung konnte nicht gesetzt werden: * NICHT GEFUNDEN * ~~~")
			log("(default.run=onlyFISRTTIME) ### Beende Aktion SETTINGS bearbeiten - EINTRAG KOPIEREN NACH USERDATA-SETTINGS + EVERYTHING IS DONE !!! ###")
			xbmcvfs.delete(UNO)
			xbmc.sleep(500)
			DONE = True
		else:
			DONE = True
		if DONE is True:
			if addon.getSetting('service_startWINDOW') == 'true':
				lastHM = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
				addon.setSetting('last_starttime', lastHM+' / 01')
				if navigator.Callonce().call_registration(lastHM) is True:
					addon.setSetting('service_startWINDOW', 'false')
				debug_MS("(default.run) ### settings_service_startWINDOW is now = {0} ###".format(str(addon.getSetting('service_startWINDOW'))))
			if mode == 'root':
				if addon.getSetting('checkwidevine') == 'true' and addon.getSetting('service_startWIDEVINE') == 'true':
					debug_MS("(checkwidevine) ### Widevineüberprüfung ist eingeschaltet !!! ###")
					is_helper = inputstreamhelper.Helper('mpd', drm='com.widevine.alpha')
					if is_helper.check_inputstream():
						debug_MS("(default.run=checkwidevine) ### Widevine ist auf Ihrem Gerät installiert und aktuell !!! ###")
					else:
						failing("(default.run=checkwidevine) ERROR - ERROR - ERROR :\n##### !!! Widevine oder Inputstream.Adaptive ist NICHT installiert !!! #####")
						dialog.notification(translation(30521).format('Widevine', ''), translation(30561), icon, 12000)
					debug_MS("(default.run=checkwidevine) ### settings_service_startWIDIVINE = FALSE ###")
					addon.setSetting('service_startWIDEVINE', 'false')
				navigator.mainMenu()
			elif mode == 'playDash':
				navigator.playDash(action, xcode, xlink, xdrm, xfree, xtele)
	elif mode == 'erase_account':
		navigator.erase_account()
	elif mode == 'refresh_data':
		navigator.refresh_data()
	elif mode == 'listSeries':
		navigator.listSeries(url, extras, searching)
	elif mode == 'listSeasons':
		navigator.listSeasons(url, photo)
	elif mode == 'listEpisodes':
		navigator.listEpisodes(url, extras)
	elif mode == 'listStations':
		navigator.listStations()
	elif mode == 'listAlphabet':
		navigator.listAlphabet()
	elif mode == 'listNewest':
		navigator.listNewest()
	elif mode == 'listDates':
		navigator.listDates()
	elif mode == 'listTopics':
		navigator.listTopics()
	elif mode == 'listGenres':
		navigator.listGenres()
	elif mode == 'listThemes':
		navigator.listThemes()
	elif mode == 'SearchRTLPLUS':
		navigator.SearchRTLPLUS()
	elif mode == 'listLiveTV':
		navigator.listLiveTV()
	elif mode == 'listEventTV':
		navigator.listEventTV()
	elif mode == 'listShowsFavs':
		navigator.listShowsFavs()
	elif mode == 'favs':
		navigator.favs(action, name, pict, url, plot, type)
	elif mode == 'blankFUNC':
		pass # do nothing
	elif mode == 'AddToQueue':
		navigator.AddToQueue()
	elif mode == 'preparefiles':
		mediatools.preparefiles(url, name, extras, cycle)
	elif mode == 'generatefiles':
		mediatools.generatefiles(url, name)
	elif mode == 'clearCache':
		navigator.clearCache()
	elif mode == 'aConfigs':
		addon.openSettings()
	elif mode == 'iConfigs':
		xbmcaddon.Addon('inputstream.adaptive').openSettings()

run()
