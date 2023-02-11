# -*- coding: utf-8 -*-

'''
    Copyright (C) 2022 realvito

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

import xbmcaddon
import _strptime
from datetime import datetime
from resources.lib.common import *
from resources.lib import mediatools
from resources.lib import navigator
import inputstreamhelper


def run():
	if mode == 'root':
		if addon.getSetting('service_startWINDOW') == 'true':
			lastHM = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
			addon.setSetting('last_starttime', lastHM+' / 01')
			if navigator.Callonce().call_registration(lastHM) is True:
				addon.setSetting('service_startWINDOW', 'false')
			debug_MS("(default.run) ### settings_service_startWINDOW is now = {0} ###".format(str(addon.getSetting('service_startWINDOW'))))
		if addon.getSetting('checkwidevine') == 'true' and addon.getSetting('service_startWIDEVINE') == 'true':
			debug_MS("(checkwidevine) ### Widevineüberprüfung ist eingeschaltet !!! ###")
			is_helper = inputstreamhelper.Helper('mpd', drm='com.widevine.alpha')
			if is_helper.check_inputstream():
				debug_MS("(default.run=checkwidevine) ### Widevine ist auf Ihrem Gerät installiert und aktuell !!! ###")
				debug_MS("(default.run=checkwidevine) ### settings_service_startWIDIVINE = FALSE ###")
				addon.setSetting('service_startWIDEVINE', 'false')
			else:
				failing("(default.run=checkwidevine) ERROR - ERROR - ERROR :\n##### !!! Widevine oder Inputstream.Adaptive ist NICHT installiert !!! #####")
				dialog.notification(translation(30521).format('Widevine', ''), translation(30561), icon, 12000)
				debug_MS("(default.run=checkwidevine) ### settings_service_startWIDIVINE = FALSE ###")
				addon.setSetting('service_startWIDEVINE', 'false')
		navigator.mainMenu()
	elif mode == 'unsubscribe':
		navigator.unsubscribe()
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
	elif mode == 'playDash':
		if addon.getSetting('service_startWINDOW') == 'true':
			lastHM = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
			addon.setSetting('last_starttime', lastHM+' / 01')
			if navigator.Callonce().call_registration(lastHM) is True:
				addon.setSetting('service_startWINDOW', 'false')
			debug_MS("(default.playDash) ### settings_service_startWINDOW is now = {0} ###".format(str(addon.getSetting('service_startWINDOW'))))
		navigator.playDash(action, xcode, xlink, xdrm, xfree, xtele)
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
