# -*- coding: utf-8 -*-

'''
    Copyright (C) 2022 realvito

    DMAX Mediathek

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

import sys
import os
import xbmc
import xbmcaddon
import json
import xbmcvfs
import shutil
import io
PY2 = sys.version_info[0] == 2
from resources.lib.common import *
from resources.lib import mediatools
from resources.lib import navigator


def run():
	SEP = os.sep
	if mode == 'root': ##### Exchange old Favourites and Format of Favourites to new JSON-Format #####
		DONE = False    ##### [plugin.video.discovery.dmax v.3.0.9+v.3.1.0] - 22.03.2021+11.04.2021 #####
		OKAY = None
		EXCHANGE = {}
		EXCHANGE['items'] = []
		firstSCRIPT = TRANS_PATH(os.path.join('special://home'+SEP+'addons'+SEP+addon_id+SEP+'lib'+SEP)).encode('utf-8').decode('utf-8')
		UNO = os.path.join(firstSCRIPT, 'only_at_FIRSTSTART')
		if xbmcvfs.exists(UNO):
			sourceUSER = TRANS_PATH(os.path.join('special://home'+SEP+'userdata'+SEP+'addon_data'+SEP+addon_id+SEP)).encode('utf-8').decode('utf-8')
			sourceTEMP = TRANS_PATH(os.path.join('special://home'+SEP+'userdata'+SEP+'addon_data'+SEP+'TEMP'+SEP)).encode('utf-8').decode('utf-8')
			fav_OLD = os.path.join(sourceUSER, 'DMAX_favourChart.txt')
			fav_TEMP = os.path.join(sourceTEMP, 'DMAX_favourChart.txt')
			fav_WORK = os.path.join(sourceTEMP, 'favorites_DMAX.json')
			fav_NEW = os.path.join(sourceUSER, 'favorites_DMAX.json')
			if xbmcvfs.exists(sourceUSER):
				try:
					if xbmcvfs.exists(fav_OLD):
						xbmcvfs.mkdirs(sourceTEMP)
						xbmcvfs.copy(fav_OLD, fav_TEMP)
						xbmcvfs.delete(fav_OLD)
						debug_MS("(default.run=onlyFISRTTIME) ### xbmcvfs.copy(fav_OLD, fav_TEMP) - TEMP-Path erstellen + FAVORITEN kopieren nach TEMP-Path ###")
					if xbmcvfs.exists(fav_TEMP):
						def get_procedure(text):
							if not PY2 and isinstance(text, bytes):
								text = text.decode('utf-8')
							selections = ['utf-8', 'unicode_escape', 'latin-1']
							for _enc in selections:
								try:
									fh = io.open(text, 'r', encoding=_enc)
									fh.readlines()
									fh.seek(0)
								except UnicodeDecodeError:
									debug_MS("(default.run=onlyFISRTTIME) ~~~ FAILED = got unicode error with : {0}, trying different encoding ~~~".format(_enc))
								else:
									OKAY =_enc
									debug_MS("(default.run=onlyFISRTTIME) +++ SUCCESS = opening your Favorites of this addon with encoding : {0} +++".format(_enc))
									break
							return OKAY
						if get_procedure(fav_TEMP) is not None:
							with io.open(fav_TEMP, 'r', encoding=OKAY, errors='ignore') as output: # 'ascii' - TEST ok || 'utf-8' - TEST ok
								lines = output.readlines()
								for line in lines:
									if line.startswith('###START'):
										field = line.split('###')
										CFS_serie = repair_vokals(field[2])
										CFS_url = repair_vokals(field[3])
										CFS_img = repair_vokals(field[4]) if not 'icon.png' in field[4] else 'None'
										CFS_plot = repair_vokals(field[5]).replace('#n#', '[CR]') if field[5] != '' else 'None'
										EXCHANGE['items'].append({'name': CFS_serie, 'pict': CFS_img, 'url': CFS_url, 'plot': CFS_plot})
								with io.open(fav_WORK, 'w', encoding='utf-8') as input:
									input.write(py2_uni(json.dumps(EXCHANGE, indent=4, sort_keys=True)))
							debug_MS("(default.run=onlyFISRTTIME) ### input.write - FAVORITEN neu schreiben ###")
				except: pass
				try:
					xbmc.executeJSONRPC('{"jsonrpc":"2.0", "id":1, "method":"Addons.SetAddonEnabled", "params":{"addonid":"'+addon_id+'", "enabled":false}}')
					debug_MS("(default.run=onlyFISRTTIME) ### xbmcvfs.delete(UNO) - ADDON AUSSCHALTEN ###")
				except: pass
				xbmcvfs.delete(UNO)
				xbmc.executeJSONRPC('{"jsonrpc":"2.0", "id":1, "method":"Addons.SetAddonEnabled", "params":{"addonid":"'+addon_id+'", "enabled":true}}')
				debug_MS("(default.run=onlyFISRTTIME) ### ADDON WIEDER EINSCHALTEN ###")
				xbmc.sleep(500)
				if xbmcvfs.exists(fav_WORK):
					xbmcvfs.copy(fav_WORK, fav_NEW)
					shutil.rmtree(sourceTEMP, ignore_errors=True)
				debug_MS("(default.run=onlyFISRTTIME) ### shutil.rmtree(sourceTEMP) - FAVORITEN kopieren nach USERDATA-Path + TEMP-Path entfernen + EVERYTHING IS DONE !!! ###")
				xbmc.sleep(500)
				DONE = True
			else:
				xbmcvfs.delete(UNO)
				xbmc.sleep(500)
				DONE = True
		else:
			DONE = True
		if DONE is True: navigator.mainMenu()
	elif mode == 'listThemes':
		navigator.listThemes(url)
	elif mode == 'listAlphabet':
		navigator.listAlphabet()
	elif mode == 'listSeries':
		navigator.listSeries(url, page, position, extras)
	elif mode == 'listEpisodes':
		navigator.listEpisodes(url, origSERIE)
	elif mode == 'playVideo':
		navigator.playVideo(url)
	elif mode == 'listShowsFavs':
		navigator.listShowsFavs()
	elif mode == 'favs':
		navigator.favs(action, name, pict, url, plot)
	elif mode == 'AddToQueue':
		navigator.AddToQueue()
	elif mode == 'preparefiles':
		mediatools.preparefiles(url, name, cycle)
	elif mode == 'generatefiles':
		mediatools.generatefiles(url, name)
	elif mode == 'aConfigs':
		addon.openSettings()
	elif mode == 'iConfigs':
		xbmcaddon.Addon('inputstream.adaptive').openSettings()

run()
