# -*- coding: utf-8 -*-

import sys
import os
import re
import xbmc
import xbmcgui
import xbmcplugin
import json
import xbmcvfs
import time
import _strptime
from datetime import datetime, timedelta
PY2 = sys.version_info[0] == 2
if PY2:
	from urllib import urlencode, quote, unquote  # Python 2.X
else: 
	from urllib.parse import urlencode, quote, unquote  # Python 3.X

from .common import *
from .config import Registration
from .utilities import Transmission


class Callonce(object):

	def __init__(self):
		self.config = Registration
		self.utilities = Transmission
		self.called = False

	def login_answer(self):
		if self.config().has_credentials() is True:
			USER, PWD = self.config().get_credentials()
		else:
			USER, PWD = self.config().save_credentials()
		if self.utilities().login(USER, PWD) is True:
			debug_MS("(navigator.login_answer) ##### Alles gefunden - Anmeldung Erfolg #####")
			dialog.notification(translation(30528).format('LOGIN'), translation(30529), icon, 8000)
			xbmc.executebuiltin('Container.Refresh')
			return True
		else:
			debug_MS("(navigator.login_answer) ##### NICHTS gefunden - ErrorMeldung #####")
			dialog.notification(translation(30521).format('Login', ''), translation(30530), icon, 12000)
		return False

	def call_registration(self, lastHM):
		debug_MS("(navigator.call_registration) #################### STARTING THE PROCESSES ####################")
		nowHM = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
		if lastHM != nowHM:
			addon.setSetting('last_starttime', nowHM+' / 02')
		if not self.called:
			addon.setSetting('verified_Account', 'false')
			self.called = True
			if START_MODUS == '0':
				choose = dialog.yesno(addon_id, translation(30502).format(addon_name), nolabel=translation(30503), yeslabel=translation(30504))
				if choose == -1: return False
				if choose:
					debug_MS("(navigator.call_registration) ### START_MODUS = NULL - eins ###")
					addon.setSetting('select_start', '0')
					if self.login_answer() is True:
						addon.setSetting('verified_Account', 'true')
						return True
				else:
					debug_MS("(navigator.call_registration) ### START_MODUS = NULL - zwei ###")
					addon.setSetting('select_start', '0')
					addon.setSetting('verified_Account', 'false')
					addon.setSetting('login_status', '0')
					addon.setSetting('liveFree', 'false')
					addon.setSetting('livePay', 'false')
					addon.setSetting('vodFree', 'false')
					addon.setSetting('vodPay', 'false')
					addon.setSetting('high_definition', 'false')
					addon.setSetting('authtoken', '0')
					return True
			if START_MODUS == '1':
				debug_MS("(navigator.call_registration) ### START_MODUS = EINS ###")
				if self.login_answer() is True:
					addon.setSetting('verified_Account', 'true')
					return True
			if START_MODUS == '2':
				debug_MS("(navigator.call_registration) ### START_MODUS = ZWEI ###")
				addon.setSetting('verified_Account', 'false')
				addon.setSetting('login_status', '0')
				addon.setSetting('liveFree', 'false')
				addon.setSetting('livePay', 'false')
				addon.setSetting('vodFree', 'false')
				addon.setSetting('vodPay', 'false')
				addon.setSetting('high_definition', 'false')
				addon.setSetting('authtoken', '0')
				return True
			return False
		xbmcplugin.endOfDirectory(ADDON_HANDLE)

if KODI_ov18:
	if kodibuild == 18:
		addon.setSetting('Notify_Select', '1')
	elif kodibuild == 19:
		addon.setSetting('Notify_Select', '2')
	elif kodibuild == 20:
		addon.setSetting('Notify_Select', '3')
	elif kodibuild >= 21:
		addon.setSetting('Notify_Select', '4')
else:
	addon.setSetting('Notify_Select', '5')

def mainMenu():
	addDir(translation(30601), artpic+'favourites.png', {'mode': 'listShowsFavs'})
	addDir(translation(30602), icon, {'mode': 'listNewest'})
	addDir(translation(30603), icon, {'mode': 'listDates'})
	addDir(translation(30604), icon, {'mode': 'listStations'})
	addDir(translation(30605), icon, {'mode': 'listAlphabet'})
	addDir(translation(30606), icon, {'mode': 'listTopics'})
	addDir(translation(30607), icon, {'mode': 'listGenres'})
	addDir(translation(30608), icon, {'mode': 'listThemes'})
	addDir(translation(30609), artpic+'basesearch.png', {'mode': 'SearchRTLPLUS'})
	if addon.getSetting('login_status') != "" and int(addon.getSetting('login_status')) > 1:
		if (addon.getSetting('liveFree') == 'true' or addon.getSetting('livePay') == 'true'):
			addDir(translation(30610), artpic+'livestream.png', {'mode': 'listLiveTV'})
	addDir(translation(30611), artpic+'livestream.png', {'mode': 'listEventTV'})
	addDir(translation(30612).format(str(cachePERIOD)), artpic+'remove.png', {'mode': 'clearCache'}, folder=False)
	TEXTBOX = ""
	if addon.getSetting('login_status') == '2': TEXTBOX = translation(30621).format('FREE-USER')
	elif addon.getSetting('login_status') == '3': TEXTBOX = translation(30621).format(addon.getSetting('username'))
	else: TEXTBOX = translation(30622)
	if enableADJUSTMENT:
		addDir(translation(30613)+TEXTBOX, artpic+'settings.png', {'mode': 'aConfigs'}, folder=False)
		if ADDON_operate('inputstream.adaptive'):
			addDir(translation(30614), artpic+'settings.png', {'mode': 'iConfigs'}, folder=False)
	else:
		addDir(TEXTBOX, icon, {'mode': 'blankFUNC'}, folder=False)
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def unsubscribe():
	if xbmcvfs.exists(sessFile) and Transmission().logout() is True:
		debug_MS("(navigator.unsubscribe) XXXXX USER FORCE REMOVING SESSION - DELETE SESSIONFILE XXXXX")
		dialog.notification(translation(30528).format('Neue SESSION'), translation(30529), icon, 8000)
		return True
	return False

def load_pagination(path, POS):
	DATA_ONE = Transmission().makeREQUEST('{0}&page=1'.format(path))
	if 'order=NameLong' in path and DATA_ONE.get('movies', '') and DATA_ONE.get('movies', {}).get('items', ''):
		DATA_ONE = DATA_ONE['movies']
	elif 'order=NameLong' in path and DATA_ONE.get('teaserSetInformations', '') and DATA_ONE.get('teaserSetInformations', {}).get('items', ''):
		DATA_ONE = DATA_ONE['teaserSetInformations']
	for item in DATA_ONE.get('items', []): yield item
	ALLPAGES = int(DATA_ONE.get('total', [])) // int(POS) if DATA_ONE.get('total', '') else -1
	debug_MS("(navigator.get_Pagination) ### Total-Items : {0} || Result of PAGES : {1} ###".format(str(DATA_ONE.get('total', None)), str(ALLPAGES+1)))
	for page in range(2, ALLPAGES+2, 1):
		debug_MS("(navigator.get_Pagination) ### newURL : {0}&page={1} ###".format(path, page))
		DATA_TWO = Transmission().makeREQUEST('{0}&page={1}'.format(path, page))
		if 'order=NameLong' in path and DATA_TWO.get('movies', '') and DATA_TWO.get('movies', {}).get('items', ''):
			DATA_TWO = DATA_TWO['movies']
		elif 'order=NameLong' in path and DATA_TWO.get('teaserSetInformations', '') and DATA_TWO.get('teaserSetInformations', {}).get('items', ''):
			DATA_TWO = DATA_TWO['teaserSetInformations']
		for item in DATA_TWO.get('items', []): yield item

def listSeries(url, POS, QUERY):
	debug_MS("(navigator.listSeries) -------------------------------------------------- START = listSeries --------------------------------------------------")
	xbmcplugin.addSortMethod(ADDON_HANDLE, xbmcplugin.SORT_METHOD_LABEL)
	debug_MS("(navigator.listSeries) ### startURL : {0} || NUMBERS : {1} || QUERY : {2} ###".format(url, str(POS), unquote(QUERY)))
	COMBI_SERIES = []
	UNIKAT = set()
	for serie in load_pagination(url, POS):
		station, seoUrl, genre, category, Note_1, Note_6 = ("" for _ in range(6))
		if 'format' in serie and 'teasersets/' in url:
			if serie.get('format', ''): serie = serie['format']
			else: continue
		if QUERY != 'None':
			COMBIstring = cleaning(serie['metaTags'].lower().replace('video,', '').replace('videos,', '').replace('online sehen,', '').replace('internet tv,', '').replace('fernsehen,', '').replace('video on demand,', '').replace('tv now,', '').replace('TVNOW,', ''))
			COMBIstring += cleaning(serie['searchAliasName'].lower().replace(';', ','))
			COMBIstring += cleaning(serie['title'].lower())
		seriesID = (serie.get('id', None) or None)
		if seriesID is None or seriesID in UNIKAT:
			continue
		UNIKAT.add(seriesID)
		if serie.get('title', ''):
			title, seriesNAME = cleaning(serie['title']), cleaning(serie['title'])
		else: continue
		station = serie['station'].upper() if serie.get('station', '') else 'UNK'
		seoUrl = (serie.get('seoUrl', '') or "")
		if 'format' in serie and not 'teasersets/' in url:
			serie = serie['format']
		image = (cleanPhoto(serie.get('formatimageMoviecover169', '')) or cleanPhoto(serie.get('formatimageArtwork', '')) or IMG_series.format(seriesID))
		genre = (cleaning(serie.get('genre1', '')) or "")
		category = (serie.get('categoryId', '') or "")
		description = get_Description(serie, 'Series')
		freeEP = serie.get('hasFreeEpisodes', True)
		if freeEP is False and STATUS < 3:
			Note_1 = '   [COLOR skyblue](premium)[/COLOR]'
			Note_6 = '     [COLOR deepskyblue](premium)[/COLOR]'
		plot = seriesNAME+Note_1+'[CR][CR]'+description
		name = title+Note_6
		NOMEN, cineType = 'Series', 'episode'
		if category == 'film':
			NOMEN, cineType = 'Movies', 'movie'
			name = '[I]'+name+'[/I]' if markMOVIES else name
		if QUERY != 'None' and unquote(QUERY).lower() in str(COMBIstring):
			debug_MS("(navigator.listSeries) ##### seriesITEM : {0} #####".format(str(serie)))
			debug_MS("(navigator.listSeries) ### Found in SEARCH = TITLE : {0} ###".format(seriesNAME))
			debug_MS("(navigator.listSeries) ### Found in SEARCH = STRING : {0} ###".format(str(COMBIstring)))
			COMBI_SERIES.append([seriesID, name, seriesNAME, station, seoUrl, image, genre, plot, freeEP, NOMEN, cineType])
		elif QUERY == 'None':
			debug_MS("(navigator.listSeries) ##### seriesITEM : {0} #####".format(str(serie)))
			COMBI_SERIES.append([seriesID, name, seriesNAME, station, seoUrl, image, genre, plot, freeEP, NOMEN, cineType])
	if COMBI_SERIES:
		for seriesID, name, seriesNAME, station, seoUrl, image, genre, plot, freeEP, NOMEN, cineType in COMBI_SERIES:
			addType = 1
			if xbmcvfs.exists(channelFavsFile):
				with open(channelFavsFile, 'r') as fp:
					watch = json.load(fp)
					for item in watch.get('items', []):
						if item.get('url') == str(seriesID): addType = 2
			debug_MS("(navigator.listSeries) ### TITLE = {0} || IDD = {1} || PHOTO = {2} || addType = {3} ###".format(seriesNAME, str(seriesID), image, str(addType)))
			addDir(name, image, {'mode': 'listSeasons', 'url': str(seriesID), 'origSERIE': seriesNAME, 'photo': image, 'extras': NOMEN, 'type': cineType}, plot, genre=genre, studio=station, addType=addType)
	elif not COMBI_SERIES and QUERY != 'None':
		return dialog.notification(translation(30525).format('Ergebnisse'), translation(30526), icon, 8000)
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def listSeasons(SERIES_idd, SERIES_img):
	debug_MS("(navigator.listSeasons) -------------------------------------------------- START = listSeasons --------------------------------------------------")
	COMBI_SEASON = []
	start_url = '{0}/formats/{1}?fields=[%22id%22,%22title%22,%22station%22,%22hasFreeEpisodes%22,%22seoUrl%22,%22tabSeason%22,%22formatimageArtwork%22,%22formatimageMoviecover169%22,%22genre1%22,%22genres%22,%22categoryId%22,%22infoText%22,%22infoTextLong%22,%22onlineDate%22,%22annualNavigation%22,%22seasonNavigation%22]'.format(API_URL, str(SERIES_idd))
	try:
		DATA = Transmission().makeREQUEST(start_url)
		debug_MS("(navigator.listSeasons) ##### CONTENT : {0} #####".format(str(DATA)))
		seriesNAME = cleaning(DATA['title'])
	except: return dialog.notification(translation(30521).format('ID - ', str(SERIES_idd)), translation(30524), icon, 8000)
	seasonID = str(DATA['id'])
	seasonPLOT = get_Description(DATA, 'Seasons')
	showSEA = (DATA.get('tabSeason', False) or False)
	seasonIMG = cleanPhoto(SERIES_img)
	if ((prefCONTENT == '0' or showSEA is False) and DATA.get('annualNavigation', '') and DATA.get('annualNavigation', {}).get('total', '') == 1) or ((prefCONTENT == '1' and showSEA is True) and DATA.get('seasonNavigation', '') and DATA.get('seasonNavigation', {}).get('total', '') == 1):
		debug_MS("(navigator.listSeasons) no.1 ### SERIE = {0} || seasonID = {1} || PHOTO = {2} ###".format(seriesNAME, seasonID, str(seasonIMG)))
		listEpisodes(seasonID, 'OneDirect')
	else:
		if (prefCONTENT == '0' or showSEA is False) and DATA.get('annualNavigation', '') and DATA.get('annualNavigation', {}).get('items', []):
			for each in DATA.get('annualNavigation', {}).get('items', []):
				PREFIX = 'Jahr '
				number = str(each['year'])
				debug_MS("(navigator.listSeasons) no.2 ### SERIE = {0} || seasonID = {1} || PHOTO = {2} || JAHR = {3} ###".format(seriesNAME, seasonID, str(seasonIMG), number))
				COMBI_SEASON.append([seasonID, PREFIX, number, seasonPLOT, seasonIMG, seriesNAME])
		elif (prefCONTENT == '1' and showSEA is True) and DATA.get('seasonNavigation', '') and DATA.get('seasonNavigation', {}).get('items', []):
			for each in DATA.get('seasonNavigation', {}).get('items', []):
				PREFIX = 'Staffel '
				number = str(each['season'])
				debug_MS("(navigator.listSeasons) no.3 ### SERIE = {0} || seasonID = {1} || PHOTO = {2} || STAFFEL = {3} ###".format(seriesNAME, seasonID, str(seasonIMG), number))
				COMBI_SEASON.append([seasonID, PREFIX, number, seasonPLOT, seasonIMG, seriesNAME])
	if COMBI_SEASON:
		COURSE = True if SORTING == '0' else False
		for seasonID, PREFIX, number, seasonPLOT, seasonIMG, seriesNAME in sorted(COMBI_SEASON, key=lambda n:n[2].zfill(2), reverse=COURSE):
			name = translation(30623) if number == '0' else PREFIX+number
			addDir(name, seasonIMG, {'mode': 'listEpisodes', 'url': seasonID, 'origSERIE': seriesNAME, 'extras': PREFIX+number}, seasonPLOT, addType=2)
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def listEpisodes(SEASON_idd, SEASON_plus):
	debug_MS("(navigator.listEpisodes) -------------------------------------------------- START = listEpisodes --------------------------------------------------")
	COMBI_EPISODE = []
	REAR = False
	ENTRIES = '[%22id%22,%22title%22,%22broadcastStartDate%22,%22catchupStartDate%22,%22availableDate%22,%22catchupEndDate%22,%22articleShort%22,%22articleLong%22,%22teaserText%22,%22seoUrl%22,%22season%22,%22episode%22,%22duration%22,%22isDrm%22,%22free%22,%22payed%22,%22fsk%22,%22productionYear%22,'\
						'%22format%22,[%22id%22,%22title%22,%22station%22,%22seoUrl%22,%22formatImageClear%22,%22formatimageArtwork%22,%22defaultImage169Logo%22,%22genre1%22,%22genre2%22,%22genres%22,%22categoryId%22,%22formatType%22],%22manifest%22,[%22dash%22,%22dashhd%22]]&maxPerPage=500&order=BroadcastStartDate%20asc'
	if SEASON_plus not in ['standard', 'OneDirect']:
		if 'Jahr ' in SEASON_plus:
			start_url = '{0}/movies?filter={{%22BroadcastStartDate%22:{{%22between%22:{{%22start%22:%22{1}-01-01%2000:00:00%22,%22end%22:%22{1}-12-31%2023:59:59%22}}}},%22FormatId%22:{2}}}&fields={3}'.format(API_URL, SEASON_plus.split('Jahr ')[1], SEASON_idd, ENTRIES)
		elif 'Staffel ' in SEASON_plus:
			start_url = '{0}/movies?filter={{%22Season%22:{1},%22FormatId%22:{2}}}&fields={3}'.format(API_URL, SEASON_plus.split('Staffel ')[1], SEASON_idd, ENTRIES)
	elif SEASON_plus == 'OneDirect':
		start_url = '{0}/movies?filter={{%22FormatId%22:{1}}}&fields={2}'.format(API_URL, SEASON_idd, ENTRIES)
	else:
		start_url = SEASON_idd
	debug_MS("(navigator.listEpisodes) ### startURL : {0} ###".format(start_url))
	DATA = Transmission().makeREQUEST(start_url)
	if DATA.get('movies', '') and DATA.get('movies', {}).get('items', ''):
		DATA = DATA['movies']
	for vid in DATA.get('items', []):
		debug_MS("(navigator.listEpisodes) ##### FOLGE : {0} #####".format(str(vid)))
		tagline, description, Note_1, Note_2, Note_3, Note_4, Note_5, Note_6, Note_7, background, station, genre, category = ("" for _ in range(13))
		season, episode, duration = ('0' for _ in range(3))
		startDESC, startTITLE, begins, endDESC, mpaa, year = (None for _ in range(6))
		genreLIST = []
		STARTS = (vid.get('broadcastStartDate', None) or vid.get('catchupStartDate', None) or None)
		if str(STARTS)[:4].isdigit() and str(STARTS)[:4] not in ['0', '1970']:
			broadcast = datetime(*(time.strptime(STARTS[:19], '%Y{0}%m{0}%d %H{1}%M{1}%S'.format('-', ':'))[0:6])) # 2015-10-07 05:10:00
			startDESC = broadcast.strftime('%a{0} %d{0}%m{0}%y {1} %H{2}%M').format('.', '•', ':')
			for sd in (('Mon', translation(32101)), ('Tue', translation(32102)), ('Wed', translation(32103)), ('Thu', translation(32104)), ('Fri', translation(32105)), ('Sat', translation(32106)), ('Sun', translation(32107))): startDESC = startDESC.replace(*sd)
			startTITLE = broadcast.strftime('%d{0}%m{0}%y {1} %H{2}%M').format('.', '•', ':')
			begins = broadcast.strftime('%d{0}%m{0}%Y').format('.')
		ENDS = (vid.get('catchupEndDate', None) or vid.get('availableDate', None) or None)
		if str(ENDS)[:4].isdigit() and str(ENDS)[:4] not in ['0', '1970']:
			available = datetime(*(time.strptime(ENDS[:19], '%Y{0}%m{0}%d %H{1}%M{1}%S'.format('-', ':'))[0:6])) # 2025-01-01 06:00:00
			endDESC = available.strftime('%a{0} %d{0}%m{0}%y {1} %H{2}%M').format('.', '•', ':')
			for ed in (('Mon', translation(32101)), ('Tue', translation(32102)), ('Wed', translation(32103)), ('Thu', translation(32104)), ('Fri', translation(32105)), ('Sat', translation(32106)), ('Sun', translation(32107))): endDESC = endDESC.replace(*ed)
		protect = (vid.get('isDrm', False) or False)
		episID = (str(vid.get('id', '0')) or '0')
		title = cleaning(vid['title'])
		try: seriesname = cleaning(vid['format']['title'])
		except: 
			try: seriesname = cleaning(vid['format']['seoUrl']).replace('-', ' ').title()
			except: continue
		season = (str(vid.get('season', '0')) or '0')
		episode = (str(vid.get('episode', '0')) or '0')
		duration = get_Time(vid['duration']) if vid.get('duration', '') else '0'
		tagline = (cleaning(vid.get('teaserText', '')) or "")
		description = get_Description(vid)
		if description != "": description = '[CR]'+description
		if seriesname != "": Note_1 = seriesname
		if season != '0' and episode != '0':
			Note_3 = translation(30624).format(season, episode)
		Note_4 = translation(30625).format(str(startDESC)) if startDESC else '[CR]' if Note_3 != "" else ""
		if showDATE and startTITLE:
			Note_6 = translation(30626).format(str(startTITLE))
		if str(vid.get('fsk')).isdigit():
			mpaa = translation(30627).format(str(vid['fsk'])) if str(vid.get('fsk')) != '0' else translation(30628)
		if str(vid.get('productionYear'))[:4].isdigit() and str(vid.get('productionYear'))[:4] not in ['0', '1970']:
			year = str(vid['productionYear'])[:4]
		PayFree = (vid.get('payed', True) or vid.get('free', True))
		# BILD_1 = https://aistvnow-a.akamaihd.net/tvnow/movie/1454577/960x0/image.jpg
		# BILD_2 = https://ais.tvnow.de/tvnow/movie/1454577/960x0/image.jpg
		image = IMG_movies.format(episID)
		if vid.get('format', ''):
			background = (cleanPhoto(vid.get('format', {}).get('formatImageClear', '')) or cleanPhoto(vid.get('format', {}).get('formatimageArtwork', '')) or cleanPhoto(vid.get('format', {}).get('defaultImage169Logo', '')) or "")
			station = vid['format']['station'].upper() if vid['format'].get('station', '') else 'UNK'
			if vid.get('format', {}).get('genres', ''):
				genreLIST = [cleaning(item) for item in vid.get('format', {}).get('genres', '')]
				if genreLIST: genre = ' / '.join(sorted(genreLIST))
			if genre =="" and vid.get('format', {}).get('genre1', ''):
				genre = cleaning(vid['format']['genre1'])
			category = (vid.get('format', {}).get('categoryId', '') or "")
		cineType = 'movie' if category == 'film' else 'episode'
		if PayFree is False and STATUS < 3:
			Note_2 = '   [COLOR skyblue](premium)[/COLOR]'
			Note_7 = '     [COLOR deepskyblue](premium)[/COLOR]'
		if endDESC and PayFree is True and STATUS < 3 and datetime.now() < available:
			Note_5 = translation(30629).format(str(endDESC))
		plot = Note_1+Note_2+'[CR]'+Note_3+Note_4+Note_5+description
		title1 = title
		title2 = title+Note_6+Note_7
		COMBI_EPISODE.append([episID, background, image, title1, title2, plot, tagline, duration, seriesname, season, episode, genre, mpaa, year, begins, station, cineType, protect, PayFree])
	if COMBI_EPISODE:
		for episID, background, image, title1, title2, plot, tagline, duration, seriesname, season, episode, genre, mpaa, year, begins, station, cineType, protect, PayFree in COMBI_EPISODE:
			for method in getSorting(): xbmcplugin.addSortMethod(ADDON_HANDLE, method)
			LSM = xbmcgui.ListItem(title2)
			if plot in ['', 'None', None]: plot = "..."
			if kodibuild >= 20:
				videoInfoTag = LSM.getVideoInfoTag()
				if season not in ['0', 'None', None]: videoInfoTag.setSeason(int(season))
				if episode not in ['0', 'None', None]: videoInfoTag.setEpisode(int(episode))
				videoInfoTag.setTvShowTitle(seriesname)
				videoInfoTag.setTitle(title2)
				videoInfoTag.setTagLine(tagline)
				videoInfoTag.setPlot(plot)
				if duration not in ['0', 'None', None]: videoInfoTag.setDuration(int(duration))
				if begins: videoInfoTag.setDateAdded(begins)
				if year: videoInfoTag.setYear(int(year))
				videoInfoTag.setGenres([genre])
				#videoInfoTag.setDirectors([None])
				#videoInfoTag.setWriters([None])
				videoInfoTag.setStudios([station])
				videoInfoTag.setMpaa(mpaa)
				videoInfoTag.setMediaType(cineType)
			else:
				info = {}
				if season not in ['0', 'None', None]: info['Season'] = season
				if episode not in ['0', 'None', None]: info['Episode'] = episode
				info['Tvshowtitle'] = seriesname
				info['Title'] = title2
				info['Tagline'] = tagline
				info['Plot'] = plot
				if duration not in ['0', 'None', None]: info['Duration'] = duration
				if begins: info['Date'] = begins
				if year: info['Year'] = year
				info['Genre'] = genre
				#info['Director'] = None
				#info['Writer'] = None
				info['Studio'] = station
				info['Mpaa'] = mpaa
				info['Mediatype'] = cineType
				LSM.setInfo(type='Video', infoLabels=info)
			LSM.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
			if useSerieAsFanart and background != "":
				LSM.setArt({'fanart': background})
				REAR = True
			if not REAR and image and image != icon and not artpic in image:
				LSM.setArt({'fanart': image})
			LSM.setProperty('IsPlayable', 'true')
			LSM.setContentLookup(False)
			LSM.addContextMenuItems([(translation(30654), 'RunPlugin({0}?{1})'.format(HOST_AND_PATH, 'mode=AddToQueue'))])
			xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url='{0}?{1}'.format(HOST_AND_PATH, urlencode({'mode': 'playDash', 'xcode': episID})), listitem=LSM)
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def listNewest():
	debug_MS("(navigator.listNewest) ------------------------------------------------ START = listNewest -----------------------------------------------")
	BEFORE = (datetime.now() - timedelta(days=2)).strftime('%Y{0}%m{0}%dT%H{1}%M{1}%S'.format('-', ':'))
	NOW = datetime.now().strftime('%Y{0}%m{0}%dT%H{1}%M{1}%S'.format('-', ':'))
	ENTRIES = '[%22id%22,%22title%22,%22broadcastStartDate%22,%22catchupStartDate%22,%22availableDate%22,%22catchupEndDate%22,%22articleShort%22,%22articleLong%22,%22teaserText%22,%22seoUrl%22,%22season%22,%22episode%22,%22duration%22,%22isDrm%22,%22free%22,%22payed%22,%22fsk%22,%22productionYear%22,'\
						'%22format%22,[%22id%22,%22title%22,%22station%22,%22seoUrl%22,%22formatImageClear%22,%22formatimageArtwork%22,%22defaultImage169Logo%22,%22genre1%22,%22genre2%22,%22genres%22,%22categoryId%22,%22formatType%22],%22manifest%22,[%22dash%22,%22dashhd%22]]&maxPerPage=500&order=BroadcastStartDate%20desc'
	newURL = '{0}/movies?filter={{%22BroadcastStartDate%22:{{%22between%22:{{%22start%22:%22{1}%22,%22end%22:%22{2}%22}}}}}}&fields={3}'.format(API_URL, BEFORE.replace('T', '%20'), NOW.replace('T', '%20'), ENTRIES)
	listEpisodes(newURL, 'standard')
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def listDates():
	debug_MS("(navigator.listDates) ------------------------------------------------ START = listDates -----------------------------------------------")
	i = -7
	while i <= 7:
		WU = (datetime.now() - timedelta(days=i)).strftime('%Y{0}%m{0}%d'.format('-'))
		WT = (datetime.now() - timedelta(days=i)).strftime('%a{0}%d{1} %b'.format('~', '.'))
		MD = WT.split('~')[0].replace('Mon', translation(32101)).replace('Tue', translation(32102)).replace('Wed', translation(32103)).replace('Thu', translation(32104)).replace('Fri', translation(32105)).replace('Sat', translation(32106)).replace('Sun', translation(32107))
		MM = WT.split('~')[1].replace('Mar', translation(32201)).replace('May', translation(32202)).replace('Oct', translation(32203)).replace('Dec', translation(32204))
		ENTRIES = '[%22id%22,%22title%22,%22broadcastStartDate%22,%22catchupStartDate%22,%22availableDate%22,%22catchupEndDate%22,%22articleShort%22,%22articleLong%22,%22teaserText%22,%22seoUrl%22,%22season%22,%22episode%22,%22duration%22,%22isDrm%22,%22free%22,%22payed%22,%22fsk%22,%22productionYear%22,'\
							'%22format%22,[%22id%22,%22title%22,%22station%22,%22seoUrl%22,%22formatImageClear%22,%22formatimageArtwork%22,%22defaultImage169Logo%22,%22genre1%22,%22genre2%22,%22genres%22,%22categoryId%22,%22formatType%22],%22manifest%22,[%22dash%22,%22dashhd%22]]&maxPerPage=500&order=BroadcastStartDate%20asc'
		newURL = '{0}/movies?filter={{%22BroadcastStartDate%22:{{%22between%22:{{%22start%22:%22{1}%2000:00:01%22,%22end%22:%22{1}%2023:59:59%22}}}}}}&fields={2}'.format(API_URL, WU, ENTRIES)
		if i == 0: addDir("[COLOR lime]"+MM+" | "+MD+"[/COLOR]", icon, {'mode': 'listEpisodes', 'url': newURL})
		else: addDir(MM+" | "+MD, icon, {'mode': 'listEpisodes', 'url': newURL})
		i += 1
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def listStations():
	debug_MS("(navigator.listStations) -------------------------------------------------- START = listStations --------------------------------------------------")
	COMBI_CHANNEL = []
	MORE_TV = [{'stationID': 'tvnow', 'name': 'TVNOW'}, {'stationID': 'tvnowkids', 'name': 'TVNOW Kids'}, {'stationID': 'watchbox', 'name': 'WATCHBOX'}]
	DATA = Transmission().makeREQUEST('https://bff.apigw.tvnow.de/teaserrow/stations') # NEU: https://bff.apigw.tvnow.de/livestream/soccer
	for chan in DATA['items']:
		COMBI_CHANNEL.append({'stationID': str(chan['ecommerce']['teaserName']), 'name': cleaning(chan['label'])})
	COMBI_CHANNEL.extend(MORE_TV)
	for elem in COMBI_CHANNEL:
		if elem['stationID'] != 'geowild':
			newURL = '{0}/formats?filter={{%22Disabled%22:%220%22,%22Station%22:%22{1}%22}}&fields=[%22id%22,%22title%22,%22titleGroup%22,%22station%22,%22hasFreeEpisodes%22,%22seoUrl%22,%22formatimageArtwork%22,%22formatimageMoviecover169%22,%22genre1%22,%22categoryId%22,%22infoText%22,%22infoTextLong%22]&maxPerPage=500&order=NameLong%20asc'.format(API_URL, elem['stationID'])
			addDir(elem['name'], stapic+elem['stationID']+'.png', {'mode': 'listSeries', 'url': newURL, 'extras': 500})
			debug_MS("(navigator.listStations) ### stationNAME = {0} || stationID = {1} || LOGO = {2} ###".format(elem['name'], elem['stationID'], str(stapic+elem['stationID']+'.png')))
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def listAlphabet():
	debug_MS("(navigator.listAlphabet) ------------------------------------------------ START = listAlphabet -----------------------------------------------")
	for letter in ['0-9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']:
		newURL = '{0}/formats?filter={{%22Disabled%22:%220%22,%22TitleGroup%22:%22{1}%22}}&fields=[%22id%22,%22title%22,%22titleGroup%22,%22station%22,%22hasFreeEpisodes%22,%22seoUrl%22,%22formatimageArtwork%22,%22formatimageMoviecover169%22,%22genre1%22,%22categoryId%22,%22infoText%22,%22infoTextLong%22]&maxPerPage=500&order=NameLong%20asc'.format(API_URL, letter)
		addDir(letter, alppic+letter+'.jpg', {'mode': 'listSeries', 'url': newURL, 'extras': 500})
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def listTopics():
	debug_MS("(navigator.listTopics) -------------------------------------------------- START = listTopics --------------------------------------------------")
	UN_Supported = ['12924', '11649', '12616', '13183', '13757', '11652', '11650', '13793', '12775', '13084', '11994', '13175', '11759', '13044', '11734', '13411'] # these lists are empty or not compatible
	DATA = Transmission().makeREQUEST(API_URL+'/pages/nowtv/home-v1?fields=teaserSets.headline,teaserSets.id')
	for top in DATA['teaserSets']['items']:
		topicID = str(top['id'])
		name = cleaning(top['headline'])
		debug_MS("(navigator.listTopics) ### IDD = {0} || NAME = {1} ###".format(topicID, name))
		if not any(x in topicID for x in UN_Supported):
			newURL = '{0}/teasersets/{1}?fields=[%22teaserSetInformations%22,[%22format%22,[%22id%22,%22title%22,%22titleGroup%22,%22station%22,%22hasFreeEpisodes%22,%22seoUrl%22,%22formatimageArtwork%22,%22formatimageMoviecover169%22,%22genre1%22,%22categoryId%22,%22infoText%22,%22infoTextLong%22]]]&maxPerPage=100&order=NameLong%20asc'.format(API_URL, topicID)
			addDir(name, icon, {'mode': 'listSeries', 'url': newURL, 'extras': 100})
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def listGenres():
	debug_MS("(navigator.listGenres) -------------------------------------------------- START = listGenres --------------------------------------------------")
	xbmcplugin.addSortMethod(ADDON_HANDLE, xbmcplugin.SORT_METHOD_LABEL)
	DATA = Transmission().makeREQUEST(API_URL+'/genres?maxPerPage=100')
	for genre in DATA['items']:
		name = cleaning(genre['name'])
		seoUrl = genre['seoUrl']
		tagline = cleaning(genre['description'])
		newURL = '{0}/formats/genre/{1}?filter={{%22station%22:%22none%22}}&fields=[%22id%22,%22title%22,%22titleGroup%22,%22station%22,%22hasFreeEpisodes%22,%22seoUrl%22,%22formatimageArtwork%22,%22formatimageMoviecover169%22,%22genre1%22,%22categoryId%22,%22infoText%22,%22infoTextLong%22]&maxPerPage=500&order=NameLong%20asc'.format(API_URL, seoUrl.replace('-','%20'))
		debug_MS("(navigator.listGenres) ### genreITEM = {0} || newURL = {1} ###".format(name, str(newURL)))
		logo = genpic+name+'.png' if xbmcvfs.exists(genpic+name+'.png') else icon
		addDir(name, logo, {'mode': 'listSeries', 'url': newURL, 'extras': 500}, tagline=tagline)
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def listThemes():
	debug_MS("(navigator.listThemes) -------------------------------------------------- START = listThemes --------------------------------------------------")
	ENTRIES = '[%22id%22,%22title%22,%22broadcastStartDate%22,%22catchupStartDate%22,%22availableDate%22,%22catchupEndDate%22,%22articleShort%22,%22articleLong%22,%22teaserText%22,%22seoUrl%22,%22season%22,%22episode%22,%22duration%22,%22isDrm%22,%22free%22,%22payed%22,%22fsk%22,%22productionYear%22,'\
						'%22format%22,[%22id%22,%22title%22,%22station%22,%22seoUrl%22,%22formatImageClear%22,%22formatimageArtwork%22,%22defaultImage169Logo%22,%22genre1%22,%22genre2%22,%22genres%22,%22categoryId%22,%22formatType%22],%22manifest%22,[%22dash%22,%22dashhd%22]]&maxPerPage=100'
	# https://api.tvnow.de/v3/channels/station/rtl?fields=*&filter=%7B%22Active%22:true%7D&maxPerPage=500&page=1
	DATA = Transmission().makeREQUEST(API_URL+'/channels/station/rtl?fields=*&filter={%22Active%22:true}&maxPerPage=100')
	for theme in DATA['items']:
		themeID = str(theme['id'])
		name = cleaning(theme['title'])
		logo = 'https://aistvnow-a.akamaihd.net/tvnow/cms/'+theme['portraitImage']+'/image.jpg'
		newURL = '{0}/channels/{1}/movies?filter={{%22station%22:%22none%22}}&fields={2}'.format(API_URL, themeID, ENTRIES)
		debug_MS("(navigator.listThemes) ### IDD = {0} || NAME = {1} || PHOTO = {2} ###".format(themeID, name, logo))
		addDir(name, logo, {'mode': 'listEpisodes', 'url': newURL})
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def SearchRTLPLUS():
	debug_MS("(navigator.SearchRTLPLUS) ------------------------------------------------ START = SearchRTLPLUS -----------------------------------------------")
	keyword = None
	if xbmcvfs.exists(searchHackFile):
		with open(searchHackFile, 'r') as look:
			keyword = look.read()
	if xbmc.getInfoLabel('Container.FolderPath') == HOST_AND_PATH: # !!! this hack is necessary to prevent KODI from opening the input mask all the time !!!
		keyword = dialog.input(heading=translation(30630), type=xbmcgui.INPUT_ALPHANUM, autoclose=10000)
		if keyword:
			keyword = quote(keyword)
			with open(searchHackFile, 'w') as record:
				record.write(keyword)
	if keyword:
		newURL = API_URL+'/formats?fields=[%22id%22,%22title%22,%22titleGroup%22,%22station%22,%22hasFreeEpisodes%22,%22seoUrl%22,%22formatimageArtwork%22,%22formatimageMoviecover169%22,%22genre1%22,%22categoryId%22,%22searchAliasName%22,%22metaTags%22,%22infoText%22,%22infoTextLong%22]&maxPerPage=500'
		return listSeries(newURL, 500, keyword)
	return None

def listLiveTV():
	debug_MS("(navigator.listLiveTV) -------------------------------------------------- START = listLiveTV --------------------------------------------------")
	if liveGratis is False and livePremium is False:
		failing("(navigator.listLiveTV) ##### Sie haben KEINE Berechtigung : Für LIVE-TV ist ein Premium-Account Voraussetzung !!! #####")
		return dialog.notification(translation(30533), translation(30534), icon, 8000)
	addon.setSetting('high_definition', 'true') if STATUS == 3 and addon.getSetting('force_best') == '0' else addon.setSetting('high_definition', 'false')
	choosingHD = (True if addon.getSetting('high_definition') == 'true' else False)
	DATA = Transmission().retrieveContent(API_URL+'/epgs/movies/nownext?fields=nowNextEpgMovies.*')
	for channel in DATA['items']:
		debug_MS("(navigator.listLiveTV) ##### channelITEM : {0} #####".format(str(channel)))
		title, subTitle, title_2, subTitle_2, plot = ("" for _ in range(5))
		START, START_2, END, END_2 = (None for _ in range(4))
		SHORT = channel['nowNextEpgMovies']['items'][0]
		station = cleaning(SHORT['station']).upper().replace('RTLPLUS', 'RTLUP')
		newStation = station.lower().replace('crime', 'rtlcrime').replace('living', 'rtlliving').replace('passion', 'rtlpassion').replace('nowus', 'now').replace('rtlplus', 'rtlup')
		station_2 = newStation.upper()
		liveID = str(SHORT['id'])
		title = (cleaning(SHORT.get('title', '')) or "")
		subTitle = (cleaning(SHORT.get('subTitle', '')) or "")
		if title == "" and subTitle != "":
			title = subTitle
		elif title != "" and subTitle != "":
			title = '{0} - {1}'.format(title, subTitle)
		if str(SHORT.get('startDate'))[:4].isdigit():
			startDT = datetime(*(time.strptime(SHORT['startDate'][:19], '%Y{0}%m{0}%d %H{1}%M{1}%S'.format('-', ':'))[0:6])) # 2019-06-02 11:40:00
			START = startDT.strftime('{0}%H{1}%M').format('(', ':')
		if str(SHORT.get('endDate'))[:4].isdigit():
			endDT = datetime(*(time.strptime(SHORT['endDate'][:19], '%Y{0}%m{0}%d %H{1}%M{1}%S'.format('-', ':'))[0:6])) # 2019-06-02 11:40:00
			END = endDT.strftime(' {0} %H{1}%M{2}').format('-', ':', ')')
		normSD, highHD = 'https://pnowlive-a.akamaized.net/live/{0}/dash/{0}.mpd'.format(newStation), 'https://pnowlive-a.akamaized.net/live/{0}hd/dash/{0}hd.mpd'.format(newStation)
		# NEW(hd) = https://p-nowlive.secure.footprint.net/live/rtlhd/dash/rtlhd.mpd // Juli.20222
		# NEW(sd) = https://pnowlive-a.akamaized.net/live/rtl/dash/rtl.mpd // Juli.20222
		photo = IMG_tvepg.format(liveID)
		if END: plot = translation(30631).format(END.replace('-', '').replace(')', '').strip())
		if channel.get('nowNextEpgMovies', {}).get('total', '') == 2:
			BRIEF = channel['nowNextEpgMovies']['items'][1]
			title_2 = (cleaning(BRIEF.get('title', '')) or "")
			subTitle_2 = (cleaning(BRIEF.get('subTitle', '')) or "")
			if title_2 == "" and subTitle_2 != "":
				title_2 = subTitle_2
			elif title_2 != "" and subTitle_2 != "":
				title_2 = '{0} - {1}'.format(title_2, subTitle_2)
			if str(BRIEF.get('startDate'))[:4].isdigit():
				startDT_2 = datetime(*(time.strptime(BRIEF['startDate'][:19], '%Y{0}%m{0}%d %H{1}%M{1}%S'.format('-', ':'))[0:6])) # 2019-06-02 11:40:00
				START_2 = startDT_2.strftime('%H{0}%M').format(':')
			if str(BRIEF.get('endDate'))[:4].isdigit():
				endDT_2 = datetime(*(time.strptime(BRIEF['endDate'][:19], '%Y{0}%m{0}%d %H{1}%M{1}%S'.format('-', ':'))[0:6])) # 2019-06-02 11:40:00
				END_2 = endDT_2.strftime('%H{0}%M').format(':')
			if START_2 and END_2:
				plot += translation(30632).format(title_2, START_2, END_2)
		name = translation(30633).format(station, title)
		special = translation(30633).format(station, title)
		if START and END:
			name = translation(30634).format(station, title, START+END)
		vidURL = highHD if choosingHD is True and livePremium is True else normSD
		LTM = xbmcgui.ListItem(name, path=vidURL)
		if kodibuild >= 20:
			videoInfoTag = LTM.getVideoInfoTag()
			videoInfoTag.setTitle(name), videoInfoTag.setPlot(plot), videoInfoTag.setStudios([station])
		else:
			LTM.setInfo(type='Video', infoLabels={'Title': name, 'Plot': plot, 'Studio': station})
		LTM.setArt({'icon': icon, 'thumb': photo, 'poster': photo, 'fanart': photo})
		xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url='{0}?{1}'.format(HOST_AND_PATH, urlencode({'mode': 'playDash', 'action': 'LIVE', 'xlink': vidURL, 'xdrm': True, 'xtele': station_2})), listitem=LTM)
	xbmcplugin.endOfDirectory(ADDON_HANDLE, cacheToDisc=False)

def listEventTV():
	debug_MS("(navigator.listEventTV) -------------------------------------------------- START = listEventTV --------------------------------------------------")
	COMBI_SPECIAL = []
	DATA_ONE = Transmission().retrieveContent('https://bff.apigw.tvnow.de/livestream/soccer')
	for channel in DATA_ONE['events']:
		debug_MS("(navigator.eventTV) ##### channelITEM : {0} #####".format(str(channel)))
		Note_1, Note_2, Note_3, station, Note_4, plot = ("" for _ in range(6))
		START, END, mpaa = (None for _ in range(3))
		eventID = str(channel['id'])
		name = (cleaning(channel.get('headline', '')) or "")
		PayFree = (True if channel.get('isPremium', '') is False else False)
		if PayFree is False and livePremium is False: continue
		if str(channel.get('startsAt')).isdigit():
			LOCALstart = get_Local_DT(datetime(1970, 1, 1) + timedelta(milliseconds=channel.get('startsAt', ''))) # 1631805300000
			START = LOCALstart.strftime('%d{0}%m{0}%y {1} %H{2}%M').format('.', '•', ':')
		if str(channel.get('endsAt')).isdigit():
			LOCALend = get_Local_DT(datetime(1970, 1, 1) + timedelta(milliseconds=channel.get('endsAt', ''))) # 1631819700000
			END = LOCALend.strftime('%d{0}%m{0}%y {1} %H{2}%M').format('.', '•', ':')
		Note_1 = (cleaning(channel.get('title', ''))+'[CR]' or "")
		if START and END: Note_2 = translation(30635).format(str(START), str(END))
		elif START and END is None: Note_2 = translation(30636).format(str(START))
		if eventID not in ['0', 'None']:
			DATA_TWO = Transmission().retrieveContent('https://bff.apigw.tvnow.de/player/live/{0}?version=v6'.format(eventID))
			debug_MS("(navigator.eventTV) ##### streamITEM : {0} #####".format(str(DATA_TWO)))
			if DATA_TWO.get('videoConfig', '') and DATA_TWO.get('videoConfig', {}).get('meta', ''):
				SHORT = DATA_TWO['videoConfig']['meta']
				if SHORT.get('title', ''):
					name = cleaning(SHORT['title'])
				if SHORT.get('description', ''):
					Note_3 = cleaning(SHORT['description'])+'[CR]'
				if str(SHORT.get('fsk', '')).isdigit():
					mpaa = translation(30627).format(str(SHORT['fsk'])) if str(SHORT.get('fsk', '')) != '0' else translation(30628)
				if SHORT.get('station', ''):
					station = cleaning(SHORT['station']).upper()
		photo = icon
		if channel.get('image', '') and channel.get('image', {}).get('path', ''):
			photo = cleanPhoto(channel['image']['path'])
		Note_4 = (cleaning(channel.get('additionalInfo', '')) or "")
		plot = Note_1+Note_2+Note_3+Note_4
		COMBI_SPECIAL.append([eventID, name, PayFree, photo, plot, station, mpaa])
	if COMBI_SPECIAL:
		for eventID, name, PayFree, photo, plot, station, mpaa in COMBI_SPECIAL:
			LEM = xbmcgui.ListItem(name)
			if kodibuild >= 20:
				videoInfoTag = LEM.getVideoInfoTag()
				videoInfoTag.setTitle(name), videoInfoTag.setPlot(plot), videoInfoTag.setStudios([station]), videoInfoTag.setMpaa(mpaa)
			else:
				LEM.setInfo(type='Video', infoLabels={'Title': name, 'Plot': plot, 'Studio': station, 'Mpaa': mpaa})
			LEM.setArt({'icon': icon, 'thumb': photo, 'poster': photo, 'fanart': photo})
			xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url='{0}?{1}'.format(HOST_AND_PATH, urlencode({'mode': 'playDash', 'action': 'EVENT', 'xcode': eventID})), listitem=LEM)
	else:
		if STATUS == 3:
			debug_MS("(navigator.listEventTV) Leider gibt es in der Rubrik : EVENTSTREAMS - zurzeit überhaupt KEINE verfügbaren Videos !")
			return dialog.notification(translation(30525).format('Einträge'), translation(30527).format('EVENTSTREAMS'), icon, 8000)
		else:
			debug_MS("(navigator.listEventTV) Leider gibt es in der Rubrik : EVENTSTREAMS - zurzeit KEINE 'Gratis Videos' !")
			return dialog.notification(translation(30525).format("'Gratis Videos'"), translation(30527).format('EVENTSTREAMS'), icon, 8000)
	xbmcplugin.endOfDirectory(ADDON_HANDLE, cacheToDisc=False)

def getVideo(streamID, event=False):
	addon.setSetting('high_definition', 'true') if STATUS == 3 and addon.getSetting('force_best') == '0' else addon.setSetting('high_definition', 'false')
	choosingHD = (True if addon.getSetting('high_definition') == 'true' else False)
	ACCESS_TOKEN = AUTH_Token if AUTH_Token.startswith('eyJ') else '0'
	first_url = "https://bff.apigw.tvnow.de/player/{}".format(streamID)
	if event:
		first_url = "https://bff.apigw.tvnow.de/player/live/{}?version=v6".format(streamID)
	req = Transmission().retrieveContent(first_url, method='TRACK')
	if req.status_code in [402, 403] and (re.search(r'"errorType":"not_started"', req.text) or re.search(r'"errorType":"premium"', req.text)):
		if re.search(r'"errorType":"not_started"', req.text):
			failing("(navigator.getVideo) ##### Noch NICHT vefügbar : Die LIVE-Übertragung wurde noch nicht gestartet !!! #####")
			dialog.notification(translation(30531), translation(30532), icon, 8000)
		elif re.search(r'"errorType":"premium"', req.text):
			failing("(navigator.getVideo) ##### Sie haben KEINE Berechtigung : Für dieses Video ist ein Premium-Account Voraussetzung !!! #####")
			dialog.notification(translation(30533), translation(30535), icon, 8000)
	elif req.status_code == 200:
		DATA = req.json()
		PayFree = ('False' if DATA.get('videoConfig', '') and DATA['videoConfig'].get('meta', '') and DATA['videoConfig']['meta'].get('isPayedContent', '') is True else 'True')
		Station = (DATA['videoConfig']['meta']['station'].upper() if DATA.get('videoConfig', '') and DATA['videoConfig'].get('meta', '') and DATA['videoConfig']['meta'].get('station', '') else 'UNK')
		if DATA.get('videoConfig', '') and DATA.get('videoConfig', {}).get('sources', ''):
			tracks = DATA['videoConfig']['sources']
			protected = 'True' if tracks.get('drm', '') else 'False'
			if tracks.get('dashUrl', '') and choosingHD is True:
				debug_MS("(navigator.getVideo) ### sources.dashUrl : {0} || DRM-PRO : {1} ###".format(tracks['dashUrl'], str(protected)))
				return tracks['dashUrl'].replace('dash.secure.footprint.net', 'dash-a.akamaihd.net'), protected, PayFree, Station
			if tracks.get('dashFallbackUrl', ''): # Lower Quality
				debug_MS("(navigator.getVideo) ### sources.dashFallbackUrl : {0} || DRM-PRO : {1} ###".format(tracks['dashFallbackUrl'], str(protected)))
				return tracks['dashFallbackUrl'].replace('dash.secure.footprint.net', 'dash-a.akamaihd.net'), protected, PayFree, Station
		if DATA.get('videoConfig', '') and DATA.get('videoConfig', {}).get('videoSource', ''):
			source = DATA['videoConfig']['videoSource']
			protected = 'True' if source.get('drm', '') else 'False'
			if source.get('streams', ''):
				tracks = source['streams']
				if tracks.get('dashHdUrl', '') and choosingHD is True:
					debug_MS("(navigator.getVideo) ### videoSource.dashHdUrl : {0} || DRM-PRO : {1} ###".format(tracks['dashHdUrl'], str(protected)))
					return tracks['dashHdUrl'].replace('dash.secure.footprint.net', 'dash-a.akamaihd.net'), protected, PayFree, Station
				if tracks.get('dashUrl', ''): # Lower Quality
					debug_MS("(navigator.getVideo) ### videoSource.dashUrl : {0} || DRM-PRO : {1} ###".format(tracks['dashUrl'], str(protected)))
					return tracks['dashUrl'].replace('dash.secure.footprint.net', 'dash-a.akamaihd.net'), protected, PayFree, Station
		failing("(navigator.getVideo) ##### KEIN Streameintrag in der Player-API vorhanden !!! #####")
		dialog.notification(translation(30521).format('VIDEO', ''), translation(30536), icon, 8000)
	else:
		failing("(navigator.getVideo) ERROR - ERROR - ERROR : ##### url: {0} === error: {1} #####".format(first_url, req.text))
		dialog.notification(translation(30521).format('VIDEO', ''), translation(30522), icon, 8000)
	return None, None, 'False', 'UNK'

def playDash(action, xcode, xlink, xdrm, xfree, xtele):
	debug_MS("(navigator.playDash) -------------------------------------------------- START = playDash --------------------------------------------------")
	addon.setSetting('high_definition', 'true') if STATUS == 3 and addon.getSetting('force_best') == '0' else addon.setSetting('high_definition', 'false')
	choosingHD = (True if addon.getSetting('high_definition') == 'true' else False)
	ACCESS_TOKEN = AUTH_Token if AUTH_Token.startswith('eyJ') else '0'
	UAG = 'User-Agent={0}&Referer=https://www.tvnow.de/'.format(get_userAgent())
	finalURL = False
	FOUND = 0
	if xbmc.Player().isPlaying():
		xbmc.Player().stop()
	if action in ['LIVE', 'IPTV'] and xlink:
		if liveGratis is False and livePremium is False:
			failing("(navigator.playDash) ##### Sie haben KEINE Berechtigung : Für LIVE-TV ist ein Premium-Account Voraussetzung !!! #####")
			return dialog.notification(translation(30533), translation(30534), icon, 8000)
		else:
			FOUND, finalURL = 1, xlink
	elif action in ['DEFAULT', 'EVENT'] and xcode:
		xevent = True if action == 'EVENT' else False
		xlink, xdrm, xfree, xtele = getVideo(xcode, xevent)
		if (xlink and vodPremium is True and STATUS == 3 and ACCESS_TOKEN != '0') or (xlink and vodPremium is False and xfree == 'True'):
			FOUND, finalURL = 1, xlink
	debug_MS("(navigator.playDash) ### ACTION : {0} || XLINK : {1} || XTELE : {2} ###".format(str(action), str(xlink), str(xtele)))
	debug_MS("(navigator.playDash) ### XCODE : {0} || XDRM : {1} || XFREE : {2} ###".format(str(xcode), str(xdrm), str(xfree)))
	debug_MS("(navigator.playDash) ### finalURL : {0} || FOUND : {1} || choosingHD : {2} ###".format(str(finalURL), str(FOUND), str(choosingHD)))
	if FOUND == 1 and finalURL:
		debug_MS("--------------------------------------------------------------------------- Gefunden ---------------------------------------------------------------------------------")
		liz = xbmcgui.ListItem(path=finalURL)
		log("(navigator.playDash) StreamURL : {0}".format(finalURL))
		liz.setMimeType('application/dash+xml')
		liz.setProperty(INPUT_APP, 'inputstream.adaptive')
		liz.setProperty('inputstream.adaptive.manifest_type', 'mpd')
		liz.setProperty('inputstream.adaptive.stream_headers', 'User-Agent={0}'.format(get_userAgent()))
		if KODI_ov18 and xdrm == 'True':
			if ACCESS_TOKEN == '0':
				specification = 'eventURL' if action == 'EVENT' else 'standardURL'
				ACCESS_TOKEN = Transmission().check_FreeToken(xcode, specification)
			debug_MS("(navigator.playDash) ### TOKEN : {0} ###".format(str(ACCESS_TOKEN)))
			if ACCESS_TOKEN != '0':
				liz.setProperty('inputstream.adaptive.license_key', LICENSE_URL.format('license', UAG, ACCESS_TOKEN, 'R{SSM}'))
				debug_MS("(navigator.playDash) LICENSE : {0}".format(LICENSE_URL.format('license', UAG, ACCESS_TOKEN, 'R{SSM}')))
				liz.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
				if action in ['LIVE', 'EVENT', 'IPTV']:
					liz.setProperty('inputstream.adaptive.manifest_update_parameter', 'full')
					if kodibuild >= 20:
						videoInfoTag = liz.getVideoInfoTag()
						videoInfoTag.setTitle('Livestream - '+xtele), videoInfoTag.setStudios([xtele])
					else:
						liz.setInfo(type='Video', infoLabels={'Title': 'Livestream - '+xtele, 'Studio': xtele})
					if action in ['LIVE', 'EVENT']:
						xbmc.Player().play(item=finalURL, listitem=liz)
					elif action == 'IPTV':
						xbmcplugin.setResolvedUrl(ADDON_HANDLE, True, liz)
					xbmc.sleep(3000)
					if not xbmc.getCondVisibility('Window.IsVisible(fullscreenvideo)') and not xbmc.Player().isPlaying():
						return dialog.notification(translation(30521).format('DASH - URL', ''), translation(30537), icon, 8000)
		if action == 'DEFAULT':
			xbmcplugin.setResolvedUrl(ADDON_HANDLE, True, liz)

def listShowsFavs():
	debug_MS("(navigator.listShowsFavs) ------------------------------------------------ START = listShowsFavs -----------------------------------------------")
	xbmcplugin.addSortMethod(ADDON_HANDLE, xbmcplugin.SORT_METHOD_LABEL)
	if xbmcvfs.exists(channelFavsFile):
		with open(channelFavsFile, 'r') as fp:
			watch = json.load(fp)
			for item in watch.get('items', []):
				title = '[I]'+cleaning(item.get('name'))+'[/I]' if markMOVIES and item.get('type') == 'movie' else cleaning(item.get('name'))
				logo = icon if item.get('pict', 'None') == 'None' else cleanPhoto(item.get('pict'))
				debug_MS("(navigator.listShowsFavs) ### NAME : {0} || URL : {1} || IMAGE : {2} || cineType : {3} ###".format(title, item.get('url'), logo, item.get('type')))
				addDir(title, logo, {'mode': 'listSeasons', 'url': item.get('url'), 'origSERIE': cleaning(item.get('name')), 'photo': logo, 'type': item.get('type')}, cleaning(item.get('plot')), FAVclear=True)
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def favs(*args):
	TOPS = {}
	TOPS['items'] = []
	if xbmcvfs.exists(channelFavsFile):
		with open(channelFavsFile, 'r') as output:
			TOPS = json.load(output)
	if action == 'ADD':
		TOPS['items'].append({'name': name, 'pict': pict, 'url': url, 'plot': plot, 'type': type})
		with open(channelFavsFile, 'w') as input:
			json.dump(TOPS, input, indent=4, sort_keys=True)
		xbmc.sleep(500)
		dialog.notification(translation(30538), translation(30539).format(name), icon, 8000)
	elif action == 'DEL':
		TOPS['items'] = [obj for obj in TOPS['items'] if obj.get('url') != url]
		with open(channelFavsFile, 'w') as input:
			json.dump(TOPS, input, indent=4, sort_keys=True)
		xbmc.executebuiltin('Container.Refresh')
		xbmc.sleep(1000)
		dialog.notification(translation(30538), translation(30540).format(name), icon, 8000)

def AddToQueue():
	return xbmc.executebuiltin('Action(Queue)')

def addDir(name, image, params={}, plot=None, tagline=None, genre=None, studio=None, addType=0, FAVclear=False, folder=True):
	u = '{0}?{1}'.format(HOST_AND_PATH, urlencode(params))
	liz = xbmcgui.ListItem(name)
	if plot in ['', 'None', None]: plot = "..."
	if kodibuild >= 20:
		videoInfoTag = liz.getVideoInfoTag()
		videoInfoTag.setTvShowTitle(params.get('origSERIE')), videoInfoTag.setTitle(name), videoInfoTag.setPlot(plot), videoInfoTag.setTagLine(tagline), videoInfoTag.setGenres([genre]), videoInfoTag.setStudios([studio])
	else:
		liz.setInfo(type='Video', infoLabels={'Tvshowtitle': params.get('origSERIE'), 'Title': name, 'Plot': plot, 'Tagline': tagline, 'Genre': genre, 'Studio': studio})
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if image and image != icon and not artpic in image:
		liz.setArt({'fanart': image})
	entries = []
	if addType == 1 and FAVclear is False:
		entries.append([translation(30651), 'RunPlugin({0}?{1})'.format(HOST_AND_PATH, urlencode({'mode': 'favs', 'action': 'ADD', 'name': params.get('origSERIE'), 'pict': 'None' if image == icon else image, 'url': params.get('url'),
			'plot': plot.replace('\n', '[CR]'), 'type': params.get('type')}))])
	if addType in [1, 2] and enableLIBRARY:
		entries.append([translation(30653), 'RunPlugin({0}?{1})'.format(HOST_AND_PATH, urlencode({'mode': 'preparefiles', 'url': params.get('url'), 'name': params.get('origSERIE'), 'extras': params.get('extras'), 'cycle': libraryPERIOD}))])
	if FAVclear is True:
		entries.append([translation(30652), 'RunPlugin({0}?{1})'.format(HOST_AND_PATH, urlencode({'mode': 'favs', 'action': 'DEL', 'name': name, 'pict': image, 'url': params.get('url'), 'plot': plot, 'type': params.get('type')}))])
	liz.addContextMenuItems(entries)
	return xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=u, listitem=liz, isFolder=folder)
