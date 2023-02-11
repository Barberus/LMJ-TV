# -*- coding: utf-8 -*-

import sys
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
	from urllib import urlencode  # Python 2.X
else: 
	from urllib.parse import urlencode  # Python 3.X

from .common import *


if not xbmcvfs.exists(dataPath):
	xbmcvfs.mkdirs(dataPath)

def mainMenu():
	addDir(translation(30601), artpic+'favourites.png', {'mode': 'listShowsFavs'})
	addDir(translation(30602), icon, {'mode': 'listSeries', 'url': BASE_API+'/content/shows?include=images,genres&sort=-newestEpisodePublishStart&filter[hasNewEpisodes]=true', 'extras': 'newest_Series'})
	addDir(translation(30603), icon, {'mode': 'listEpisodes', 'url': BASE_API+'/content/videos?include=show,images,genres&sort=-earliestPlayableStart&filter[primaryChannel.id]='+PRIMARY_CHANNEL, 'extras': 'newest_Episodes'})
	addDir(translation(30604), icon, {'mode': 'listSeries', 'url': BASE_API+'/content/shows?include=images,genres&sort=publishEnd&filter[hasExpiringEpisodes]=true', 'extras': 'last_chance'})
	addDir(translation(30605), icon, {'mode': 'listThemes', 'url': BASE_API+'/content/genres?include=images&filter[primaryChannel.id]='+PRIMARY_CHANNEL+'&page[size]=50'})
	addDir(translation(30606), icon, {'mode': 'listSeries', 'url': BASE_API+'/content/shows?include=images,genres&sort=views.lastWeek', 'extras': 'most_popular'})
	addDir(translation(30607), icon, {'mode': 'listAlphabet', 'extras': 'letter_A-Z'})
	addDir(translation(30608), icon, {'mode': 'listSeries', 'url': BASE_API+'/content/shows?include=images,genres&sort=name', 'extras': 'overview_all'})
	if enableADJUSTMENT:
		addDir(translation(30609), artpic+'settings.png', {'mode': 'aConfigs'}, folder=False)
		if ADDON_operate('inputstream.adaptive'):
			addDir(translation(30610), artpic+'settings.png', {'mode': 'iConfigs'}, folder=False)
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def listThemes(url):
	debug_MS("(navigator.listThemes) ------------------------------------------------ START = listThemes -----------------------------------------------")
	DATA = getUrl(url)
	debug_MS("++++++++++++++++++++++++")
	debug_MS("(navigator.listThemes[1]) no.01 XXXXX CONTENT : {0} XXXXX".format(str(DATA)))
	debug_MS("++++++++++++++++++++++++")
	IMAGES = list(filter(lambda x: x['type'] == 'image', DATA.get('included', [])))
	for elem in DATA.get('data', []):
		image = icon
		genreID = str(elem['id'])
		name = cleaning(elem['attributes']['name'])
		if elem.get('relationships').get('images', None) and elem.get('relationships').get('images').get('data', None):
			image = [img.get('attributes', {}).get('src', []) for img in IMAGES if img.get('id') == elem['relationships']['images']['data'][0]['id']][0]
		newURL = '{0}/content/shows?include=images,genres&sort=name&filter[genre.id]={1}'.format(BASE_API, genreID)
		addDir(name, image, {'mode': 'listSeries', 'url': newURL, 'extras': 'overview_genres'})
		debug_MS("(navigator.listThemes[2]) ### NAME : {0} || GENRE-ID : {1} || IMAGE : {2} ###".format(str(name), genreID, image))
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def listAlphabet():
	debug_MS("(navigator.listAlphabet) ------------------------------------------------ START = listAlphabet -----------------------------------------------")
	for letter in ['0-9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']:
		newURL = '{0}/content/shows?include=images,genres&sort=name&filter[name.startsWith]={1}'.format(BASE_API, letter.replace('0-9', '1'))
		addDir(letter, alppic+letter+'.jpg', {'mode': 'listSeries', 'url': newURL})
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def listSeries(url, PAGE, POS, ADDITION):
	debug_MS("(navigator.listSeries) ------------------------------------------------ START = listSeries -----------------------------------------------")
	debug_MS("(navigator.listSeries) ### URL : {0} ### PAGE : {1} ### POS : {2} ### ADDITION : {3} ###".format(url, str(PAGE), str(POS), str(ADDITION)))
	COMBI_PAGES, COMBI_SERIES, COMBI_FIRST = ([] for _ in range(3))
	UNIKAT = set()
	counter = int(POS)
	newURL = '{0}&filter[primaryChannel.id]={1}&page[number]={2}&page[size]=50'.format(url, PRIMARY_CHANNEL, str(PAGE))
	DATA_ONE = [] if 'filter[hasNewEpisodes]' in url and FORCE_SCRIPT else getUrl(newURL)
	DEB_TEXT = "{'data': [], 'FORCE_SCRIPT': True, 'Skip FirstUrl': True}" if 'filter[hasNewEpisodes]' in url and FORCE_SCRIPT else str(DATA_ONE)
	debug_MS("+++++++++++++++++++++++")
	debug_MS("(navigator.listSeries[1]) no.01 XXXXX DATA_ONE : {0} XXXXX".format(DEB_TEXT))
	debug_MS("++++++++++++++++++++++++")
	if 'filter[hasNewEpisodes]' in url and (('data' in DATA_ONE and len(DATA_ONE['data']) < 1) or not 'data' in DATA_ONE or FORCE_SCRIPT):
		for i in range(1, 10, 1):
			SLINK = '{0}&filter[primaryChannel.id]={1}&page[number]={2}&page[size]=50'.format(url.replace('&filter[hasNewEpisodes]=true', ''), PRIMARY_CHANNEL, str(i))
			debug_MS("(navigator.listSeries[2]) SERIES-PAGES XXX POS = {0} || URL = {1} XXX".format(str(i), SLINK))
			COMBI_PAGES.append([int(i), SLINK])
		if COMBI_PAGES:
			COMBI_SERIES = getMultiData(COMBI_PAGES)
			if COMBI_SERIES:
				DATA_TWO = json.loads(COMBI_SERIES)
				#log("++++++++++++++++++++++++")
				#log("(navigator.listSeries[3]) no.03 XXXXX DATA_TWO : {0} XXXXX".format(str(DATA_TWO)))
				#log("++++++++++++++++++++++++")
				for item in DATA_TWO:
					if item is not None and 'data' in item and len(item['data']) > 0:
						GENRES = list(filter(lambda x: x['type'] == 'genre', item.get('included', [])))
						IMAGES = list(filter(lambda x: x['type'] == 'image', item.get('included', [])))
						for each in item.get('data', []):
							debug_MS("(navigator.listSeries[3]) no.03 ### EACH-03 : {0} ###".format(str(each)))
							image = icon
							startTIMES = None
							genre, plot = ("" for _ in range(2))
							oneGEN, twoGEN = ([] for _ in range(2))
							if each.get('relationships').get('genres', None) and each.get('relationships').get('genres').get('data', None):
								oneGEN = [og.get('id', []) for og in each['relationships']['genres']['data']]
								twoGEN = [py2_enc(tg.get('attributes', {}).get('name', [])) for tg in GENRES if tg.get('id') in oneGEN]
								if twoGEN: genre = ' / '.join(sorted(twoGEN))
							if each.get('relationships').get('images', None) and each.get('relationships').get('images').get('data', None):
								image = [img.get('attributes', {}).get('src', []) for img in IMAGES if img.get('id') == each['relationships']['images']['data'][0]['id']][0]
							seriesID = (each.get('id', None) or None)
							if seriesID is None or seriesID in UNIKAT:
								continue
							UNIKAT.add(seriesID)
							each = each['attributes'] if each.get('attributes', '') else each
							if each.get('name', ''):
								name, seriesNAME = cleaning(each['name']), cleaning(each['name'])
							else: continue
							if str(each.get('newestEpisodePublishStart'))[:4].isdigit() and str(each.get('newestEpisodePublishStart'))[:4] not in ['None', '0', '1970']:
								LOCALstart = get_Local_DT(each['newestEpisodePublishStart'][:19]) # 2022-06-07T21:05:00
								if LOCALstart > (datetime.now() - timedelta(days=7, hours=3)): # 7 Tage und 2 Stunden
									startTIMES = LOCALstart.strftime('%Y{0}%m{0}%dT%H{1}%M').format('-', ':')
							NEWEST = True if (each.get('hasNewEpisodes', '') is True or startTIMES) else False
							if NEWEST is False: continue
							plot = (cleaning(each.get('description', '')).replace('\n\n\n', '\n\n') or "")
							debug_MS("(navigator.listSeries[3]) noFilter ### NAME : {0} || SERIE-IDD : {1} || IMAGE : {2} ###".format(str(name), seriesID, image))
							COMBI_FIRST.append([startTIMES, name, seriesNAME, image, seriesID, plot, genre, NEWEST])
	else:
		GENRES = list(filter(lambda x: x['type'] == 'genre', DATA_ONE.get('included', [])))
		IMAGES = list(filter(lambda x: x['type'] == 'image', DATA_ONE.get('included', [])))
		for elem in DATA_ONE.get('data', []):
			debug_MS("(navigator.listSeries[4]) no.04 ### ELEM-04 : {0} ###".format(str(elem)))
			image = icon
			startTIMES = None
			genre, plot = ("" for _ in range(2))
			oneGEN, twoGEN = ([] for _ in range(2))
			if elem.get('relationships').get('genres', None) and elem.get('relationships').get('genres').get('data', None):
				oneGEN = [og.get('id', []) for og in elem['relationships']['genres']['data']]
				twoGEN = [py2_enc(tg.get('attributes', {}).get('name', [])) for tg in GENRES if tg.get('id') in oneGEN]
				if twoGEN: genre = ' / '.join(sorted(twoGEN))
			if elem.get('relationships').get('images', None) and elem.get('relationships').get('images').get('data', None):
				image = [img.get('attributes', {}).get('src', []) for img in IMAGES if img.get('id') == elem['relationships']['images']['data'][0]['id']][0]
			seriesID = (elem.get('id', None) or None)
			if seriesID is None or seriesID in UNIKAT:
				continue
			UNIKAT.add(seriesID)
			elem = elem['attributes'] if elem.get('attributes', '') else elem
			if elem.get('name', ''):
				name, seriesNAME = cleaning(elem['name']), cleaning(elem['name'])
			else: continue
			if str(elem.get('newestEpisodePublishStart'))[:4].isdigit() and str(elem.get('newestEpisodePublishStart'))[:4] not in ['None', '0', '1970']:
				LOCALstart = get_Local_DT(elem['newestEpisodePublishStart'][:19]) # 2022-06-07T21:05:00
				if LOCALstart > (datetime.now() - timedelta(days=7, hours=3)): # 7 Tage und 2 Stunden
					startTIMES = LOCALstart.strftime('%Y{0}%m{0}%dT%H{1}%M').format('-', ':')
			NEWEST = True if (elem.get('hasNewEpisodes', '') is True or startTIMES) else False
			plot = (cleaning(elem.get('description', '')).replace('\n\n\n', '\n\n') or "")
			debug_MS("(navigator.listSeries[4]) noFilter ### NAME : {0} || SERIE-IDD : {1} || IMAGE : {2} ###".format(str(name), seriesID, image))
			COMBI_FIRST.append([startTIMES, name, seriesNAME, image, seriesID, plot, genre, NEWEST])
	for startTIMES, name, seriesNAME, image, seriesID, plot, genre, NEWEST in COMBI_FIRST:
		if seriesID and len(seriesID) < 9:
			counter += 1
			if 'views.lastWeek' in url:
				name = translation(30620).format(str(counter), seriesNAME)
			elif 'filter[hasExpiringEpisodes]' in url:
				name = translation(30621).format(name)
			if not 'filter[hasExpiringEpisodes]' in url and NEWEST is True:
				name = translation(30622).format(name)
			debug_MS("(navigator.listSeries[5]) Filtered ------ NAME : {0} || SERIE-IDD : {1} || IMAGE : {2} ---".format(str(name), seriesID, image))
			addType = 1
			if xbmcvfs.exists(channelFavsFile):
				with open(channelFavsFile, 'r') as fp:
					watch = json.load(fp)
					for item in watch.get('items', []):
						if item.get('url') == seriesID: addType = 2
			addDir(name, image, {'mode': 'listEpisodes', 'url': seriesID, 'extras': ADDITION, 'origSERIE': seriesNAME}, plot, genre, addType)
	if 'meta' in DATA_ONE and 'totalPages' in DATA_ONE['meta'] and isinstance(DATA_ONE['meta']['totalPages'], int) and int(PAGE) < int(DATA_ONE['meta']['totalPages']):
		debug_MS("(navigator.listSeries[6]) PAGES ### currentPG : {0} from totalPG : {1} ###".format(str(PAGE), str(DATA_ONE['meta']['totalPages'])))
		addDir(translation(30623), artpic+'nextpage.png', {'mode': 'listSeries', 'url': url, 'page': int(PAGE)+1, 'position': int(counter), 'extras': ADDITION})
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def listEpisodes(TVID, origSERIE):
	debug_MS("(navigator.listEpisodes) ------------------------------------------------ START = listEpisodes -----------------------------------------------")
	debug_MS("(navigator.listEpisodes) ### URL : {0} ### origSERIE : {1} ###".format(str(TVID), origSERIE))
	COMBI_PAGES, COMBI_EPISODE, COMBI_SECOND = ([] for _ in range(3))
	POSS = 0
	FAULTS = False
	backTIMES = (datetime.now() - timedelta(days=7, hours=2)).strftime('%Y{0}%m{0}%dT%H{1}%M{1}%SZ'.format('-', ':')) # 7 Tage und 2 Stunden // 2022-06-17T02:00:00Z
	for i in range(1, 6, 1):
		ELINK = '{0}/content/videos?include=images,genres&sort=-seasonNumber,-episodeNumber&filter[show.id]={1}&filter[videoType]=EPISODE,STANDALONE&page[number]={2}&page[size]=100'.format(BASE_API, TVID, str(i))
		if TVID.startswith(BASE_API): # filter[earliestPlayableStart.gt] = ab zurückliegendem Zeitpunkt // filter[earliestPlayableStart.lt] = bis vorausliegendem Zeitpunkt
			ELINK = '{0}&filter[earliestPlayableStart.gt]={1}&filter[videoType]=EPISODE,STANDALONE&page[number]={2}&page[size]=30'.format(TVID, backTIMES, str(i))
		debug_MS("(navigator.listEpisodes[1]) EPISODE-PAGES XXX POS = {0} || URL = {1} XXX".format(str(i), ELINK))
		COMBI_PAGES.append([int(i), ELINK])
	if COMBI_PAGES:
		COMBI_EPISODE = getMultiData(COMBI_PAGES)
		if COMBI_EPISODE:
			DATA_ONE = json.loads(COMBI_EPISODE)
			#log("++++++++++++++++++++++++")
			#log("(navigator.listEpisodes[2]) no.02 XXXXX DATA_ONE : {0} XXXXX".format(str(DATA_ONE)))
			#log("++++++++++++++++++++++++")
			for item in sorted(DATA_ONE, key=lambda k: int(k.get('Position', 0) or 0), reverse=False):
				if item is not None and 'ERROR_occurred' in item: FAULTS = True
				elif item is not None and 'data' in item and len(item['data']) > 0:
					GENRES = list(filter(lambda x: x['type'] == 'genre', item.get('included', [])))
					IMAGES = list(filter(lambda x: x['type'] == 'image', item.get('included', [])))
					SHOWS = list(filter(lambda x: x['type'] == 'show', item.get('included', [])))
					for each in item.get('data', []):
						debug_MS("(navigator.llistEpisodes[2]) no.02 ### EACH-02 : {0} ###".format(str(each)))
						image = icon
						genre, episID, plus_SUFFIX, title2, number, Note_1, Note_2, Note_3 = ("" for _ in range(8))
						season, episode, duration = ('0' for _ in range(3))
						newSERIE, startTIMES, endTIMES, begins, year, mpaa = (None for _ in range(6))
						oneGEN, twoGEN = ([] for _ in range(2))
						if each.get('relationships').get('genres', None) and each.get('relationships').get('genres').get('data', None):
							oneGEN = [og.get('id', []) for og in each['relationships']['genres']['data']]
							twoGEN = [py2_enc(tg.get('attributes', {}).get('name', [])) for tg in GENRES if tg.get('id') in oneGEN]
							if twoGEN: genre = ' / '.join(sorted(twoGEN))
						if each.get('relationships').get('images', None) and each.get('relationships').get('images').get('data', None):
							image = [img.get('attributes', {}).get('src', []) for img in IMAGES if img.get('id') == each['relationships']['images']['data'][0]['id']][0]
						if TVID.startswith(BASE_API) and each.get('relationships').get('show', None) and each.get('relationships').get('show').get('data', None):
							newSERIE = [py2_enc(tvs.get('attributes', {}).get('name', [])) for tvs in SHOWS if tvs.get('id') == each['relationships']['show']['data']['id']][0]
						seriesname = origSERIE if newSERIE is None else newSERIE
						episID = (str(each.get('id', '00')) or '00')
						each = each['attributes'] if each.get('attributes', '') else each
						if each.get('name', ''):
							title = cleaning(each['name'])
						else: continue
						if each.get('isExpiring', '') is True or each.get('isNew', '') is True:
							plus_SUFFIX = translation(30624) if each.get('isNew', '') is True else translation(30625)
						season = str(each['seasonNumber']).zfill(2) if each.get('seasonNumber', '') else '0'
						episode = str(each['episodeNumber']).zfill(2) if each.get('episodeNumber', '') else '0'
						videoTYPE = (each.get('videoType', 'SINGLE') or 'SINGLE')
						if videoTYPE.upper() == 'STANDALONE' and episode == '0':
							POSS += 1
						if season != '0' and episode != '0':
							title1 = translation(30626).format(season, episode)
							if videoTYPE.upper() == 'STANDALONE':
								title1 = translation(30627).format(season, episode)
							title2 = title+' - '+newSERIE+plus_SUFFIX if newSERIE else title+plus_SUFFIX
							number = 'S'+season+'E'+episode
						else:
							if videoTYPE.upper() == 'STANDALONE':
								episode = str(POSS).zfill(2)
								title1 = translation(30628).format(episode)
								title2 = title+'  (Special)'+plus_SUFFIX if not 'Special' in title else title+plus_SUFFIX
								if newSERIE:
									title2 = title+'  (Special) - '+newSERIE+plus_SUFFIX if not 'Special' in title else title+' - '+newSERIE+plus_SUFFIX
								number = 'S00E'+episode
							else:
								title1 = title+' - '+newSERIE+plus_SUFFIX if newSERIE else title+plus_SUFFIX
						if str(each.get('publishStart'))[:4].isdigit() and str(each.get('publishStart'))[:4] not in ['0', '1970']:
							LOCALstart = get_Local_DT(each['publishStart'][:19])
							startTIMES = LOCALstart.strftime('%d{0}%m{0}%y {1} %H{2}%M').format('.', '•', ':')
							begins = LOCALstart.strftime('%d{0}%m{0}%Y').format('.')
						if str(each.get('publishEnd'))[:4].isdigit() and str(each.get('publishEnd'))[:4] not in ['0', '1970']:
							LOCALend = get_Local_DT(each['publishEnd'][:19])
							endTIMES = LOCALend.strftime('%d{0}%m{0}%y {1} %H{2}%M').format('.', '•', ':')
						if str(each.get('airDate'))[:4].isdigit() and str(each.get('airDate'))[:4] not in ['0', '1970']:
							year = str(each['airDate'])[:4]
						if startTIMES and endTIMES: Note_1 = translation(30629).format(str(startTIMES), str(endTIMES))
						elif startTIMES and endTIMES is None: Note_1 = translation(30630).format(str(startTIMES))
						if str(each.get('rating')).isdigit():
							mpaa = translation(30631).format(str(each['rating'])) if str(each.get('rating')) != '0' else translation(30632)
						if mpaa is None and 'contentRatings' in each and each['contentRatings'] and len(each['contentRatings']) > 0:
							if str(each.get('contentRatings', {})[0].get('code', '')).isdigit():
								mpaa = translation(30631).format(str(each.get('contentRatings', {})[0].get('code', ''))) if str(each.get('contentRatings', {})[0].get('code', '')) != '0' else translation(30632)
						Note_2 = cleaning(each['description']).replace('\n\n\n', '\n\n') if each.get('description', '') else ""
						plot = seriesname+'[CR]'+Note_1+Note_2
						protect = (each.get('drmEnabled', False) or False)
						duration = get_Time(each['videoDuration']) if str(each.get('videoDuration')).isdigit() else '0'
						COMBI_SECOND.append([number, title1, title2, episID, image, plot, duration, seriesname, season, episode, genre, mpaa, year, begins, protect])
	if COMBI_SECOND:
		COMBI_SECOND = sorted(COMBI_SECOND, key=lambda d: d[0], reverse=True) if SORTING == '0' and not TVID.startswith(BASE_API) else COMBI_SECOND
		for number, title1, title2, episID, image, plot, duration, seriesname, season, episode, genre, mpaa, year, begins, protect in COMBI_SECOND:
			if SORTING == '1' and not TVID.startswith(BASE_API):
				for method in getSorting(): xbmcplugin.addSortMethod(ADDON_HANDLE, method)
			name = title1.strip() if title2 == "" else title1.strip()+"  "+title2.strip()
			cineType = 'episode' if episode != '0' else 'movie'
			debug_MS("(navigator.listEpisodes[3]) no.03 ##### NAME : {0} || IDD : {1} || GENRE : {2} #####".format(str(name), episID, str(genre)))
			debug_MS("(navigator.listEpisodes[3]) no.03 ##### IMAGE : {0} || SEASON : {1} || EPISODE : {2} #####".format(image, str(season), str(episode)))
			addLink(name, image, {'mode': 'playVideo', 'url': episID, 'cineType': cineType}, plot, duration, seriesname, season, episode, genre, mpaa, year, begins)
	elif not COMBI_SECOND and not FAULTS:
		debug_MS("(navigator.listEpisodes) ##### Keine COMBI_EPISODEN-Liste - Kein Eintrag gefunden #####")
		return dialog.notification(translation(30525), translation(30526).format(origSERIE), icon, 8000)
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def playVideo(PLID):
	debug_MS("(navigator.playVideo) ------------------------------------------------ START = playVideo -----------------------------------------------")
	STREAM, FINAL_URL, WALU = (False for _ in range(3))
	# NEW Playback = https://eu1-prod.disco-api.com/playback/videoPlaybackInfo/142036?usePreAuth=true
	DATA = getUrl('{0}/playback/videoPlaybackInfo/{1}?usePreAuth=true'.format(BASE_API, PLID))
	debug_MS("++++++++++++++++++++++++")
	debug_MS("(navigator.playVideo[1]) no.01 XXXXX CONTENT : {0} XXXXX".format(str(DATA)))
	debug_MS("++++++++++++++++++++++++")
	if 'data' in DATA and 'attributes' in DATA['data'] and len(DATA['data']['attributes']) > 0:
		SHORT = DATA['data']['attributes']
		if SHORT.get('protection', '') and SHORT.get('protection', {}).get('drmEnabled', '') is True:
			STREAM, MIME, FINAL_URL = 'MPD', 'application/dash+xml', SHORT['streaming']['dash']['url']
			WALU = SHORT['protection']['schemes']['widevine']['licenseUrl']
			drm_TOKEN = SHORT['protection']['drmToken']
			debug_MS("(navigator.playVideo[2]) no.02 ***** TAKE - Inputstream (mpd) - FILE *****")
		if not FINAL_URL and SHORT.get('protection', '') and SHORT.get('protection', {}).get('clearkeyEnabled', '') is True:
			STREAM, MIME, FINAL_URL = 'HLS', 'application/vnd.apple.mpegurl', SHORT['streaming']['hls']['url']
			debug_MS("(navigator.playVideo[2]) no.02 ***** TAKE - Inputstream (hls) - FILE *****")
	if FINAL_URL and STREAM and ADDON_operate('inputstream.adaptive'):
		LSM = xbmcgui.ListItem(path=FINAL_URL)
		LSM.setMimeType(MIME)
		LSM.setProperty(INPUT_APP, 'inputstream.adaptive')
		LSM.setProperty('inputstream.adaptive.manifest_type', STREAM.lower())
		if WALU:
			WAKEY = u'{0}|User-Agent={1}&PreAuthorization={2}&Content-Type=application/octet-stream|{3}|'.format(WALU, get_userAgent(), drm_TOKEN, 'R{SSM}')
			LSM.setProperty('inputstream.adaptive.license_key', WAKEY)
			debug_MS("(navigator.playVideo) LICENSE : {0}".format(str(WAKEY)))
			LSM.setProperty('inputstream.adaptive.license_type', 'com.widevine.alpha')
		xbmcplugin.setResolvedUrl(ADDON_HANDLE, True, LSM)
		log("(navigator.playVideo) {0}_stream : {1}|User-Agent={2}".format(STREAM.upper(), FINAL_URL, get_userAgent()))
	else:
		failing("(navigator.playVideo) ##### Abspielen des Streams NICHT möglich ##### URL : {0} #####\n ########## KEINEN passenden Stream-Eintrag gefunden !!! ##########".format(str(PLID)))
		return dialog.notification(translation(30521).format('ID - ', PLID), translation(30527), icon, 8000)

def listShowsFavs():
	debug_MS("(navigator.listShowsFavs) ------------------------------------------------ START = listShowsFavs -----------------------------------------------")
	xbmcplugin.addSortMethod(ADDON_HANDLE, xbmcplugin.SORT_METHOD_LABEL)
	if xbmcvfs.exists(channelFavsFile):
		with open(channelFavsFile, 'r') as fp:
			watch = json.load(fp)
			for item in watch.get('items', []):
				name = cleaning(item.get('name'))
				logo = icon if item.get('pict', 'None') == 'None' else item.get('pict')
				debug_MS("(navigator.listShowsFavs) ### NAME : {0} || URL : {1} || IMAGE : {2} ###".format(name, item.get('url'), logo))
				addDir(name, logo, {'mode': 'listEpisodes', 'url': item.get('url'), 'origSERIE': name}, cleaning(item.get('plot')), FAVclear=True)
	xbmcplugin.endOfDirectory(ADDON_HANDLE)

def favs(*args):
	TOPS = {}
	TOPS['items'] = []
	if xbmcvfs.exists(channelFavsFile):
		with open(channelFavsFile, 'r') as output:
			TOPS = json.load(output)
	if action == 'ADD':
		TOPS['items'].append({'name': name, 'pict': pict, 'url': url, 'plot': plot})
		with open(channelFavsFile, 'w') as input:
			json.dump(TOPS, input, indent=4, sort_keys=True)
		xbmc.sleep(500)
		dialog.notification(translation(30528), translation(30529).format(name), icon, 8000)
	elif action == 'DEL':
		TOPS['items'] = [obj for obj in TOPS['items'] if obj.get('url') != url]
		with open(channelFavsFile, 'w') as input:
			json.dump(TOPS, input, indent=4, sort_keys=True)
		xbmc.executebuiltin('Container.Refresh')
		xbmc.sleep(1000)
		dialog.notification(translation(30528), translation(30530).format(name), icon, 8000)

def AddToQueue():
	return xbmc.executebuiltin('Action(Queue)')

def addDir(name, image, params={}, plot=None, genre=None, addType=0, FAVclear=False, folder=True):
	u = '{0}?{1}'.format(HOST_AND_PATH, urlencode(params))
	liz = xbmcgui.ListItem(name)
	if plot in ['', 'None', None]: plot = "..."
	if KODI_ov20:
		videoInfoTag = liz.getVideoInfoTag()
		videoInfoTag.setTitle(name), videoInfoTag.setPlot(plot), videoInfoTag.setGenres([genre]), videoInfoTag.setStudios(['DMAX'])
	else:
		liz.setInfo(type='Video', infoLabels={'Title': name, 'Plot': plot, 'Genre': genre, 'Studio': 'DMAX'})
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if image and useThumbAsFanart and image != icon and not artpic in image:
		liz.setArt({'fanart': image})
	entries = []
	if addType == 1 and FAVclear is False:
		entries.append([translation(30651), 'RunPlugin({0}?{1})'.format(HOST_AND_PATH, urlencode({'mode': 'favs', 'action': 'ADD', 'name': params.get('origSERIE'), 'pict': 'None' if image == icon else image,
			'url': params.get('url'), 'plot': plot.replace('\n', '[CR]')}))])
	if addType in [1, 2] and enableLIBRARY:
		entries.append([translation(30653), 'RunPlugin({0}?{1})'.format(HOST_AND_PATH, urlencode({'mode': 'preparefiles', 'url': params.get('url'), 'name': params.get('origSERIE'), 'cycle': libraryPERIOD}))])
	if FAVclear is True:
		entries.append([translation(30652), 'RunPlugin({0}?{1})'.format(HOST_AND_PATH, urlencode({'mode': 'favs', 'action': 'DEL', 'name': name, 'pict': image, 'url': params.get('url'), 'plot': plot}))])
	liz.addContextMenuItems(entries)
	return xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=u, listitem=liz, isFolder=folder)

def addLink(name, image, params={}, plot=None, duration=None, seriesname=None, season=None, episode=None, genre=None, mpaa=None, year=None, begins=None):
	u = '{0}?{1}'.format(HOST_AND_PATH, urlencode(params))
	liz = xbmcgui.ListItem(name)
	if plot in ['', 'None', None]: plot = "..."
	if KODI_ov20:
		videoInfoTag = liz.getVideoInfoTag()
		if season not in ['0', 'None', None]: videoInfoTag.setSeason(int(season))
		if episode not in ['0', 'None', None]: videoInfoTag.setEpisode(int(episode))
		videoInfoTag.setTvShowTitle(seriesname)
		videoInfoTag.setTitle(name)
		videoInfoTag.setTagLine(None)
		videoInfoTag.setPlot(plot)
		if duration not in ['0', 'None', None]: videoInfoTag.setDuration(int(duration))
		if begins: videoInfoTag.setDateAdded(begins)
		if begins: videoInfoTag.setFirstAired(begins)
		#if begins: videoInfoTag.setPremiered(begins)
		if year: videoInfoTag.setYear(int(year))
		videoInfoTag.setGenres([genre])
		videoInfoTag.setStudios(['DMAX'])
		videoInfoTag.setMpaa(mpaa)
		videoInfoTag.setMediaType(params.get('cineType'))
	else:
		info = {}
		if season not in ['0', 'None', None]: info['Season'] = season
		if episode not in ['0', 'None', None]: info['Episode'] = episode
		info['Tvshowtitle'] = seriesname
		info['Title'] = name
		info['Tagline'] = None
		info['Plot'] = plot
		if duration not in ['0', 'None', None]: info['Duration'] = duration
		if begins: info['Date'] = begins
		if begins: info['Aired'] = begins
		if year: info['Year'] = year
		info['Genre'] = genre
		info['Studio'] = 'DMAX'
		info['Mpaa'] = mpaa
		info['Mediatype'] = params.get('cineType')
		liz.setInfo(type='Video', infoLabels=info)
	### NEW FOR KODI-21: videoInfoTag = liz.getVideoInfoTag()
	### NEW FOR KODI-21: videoInfoTag.setInfo(info)
	### DELETED IN KODI-21: liz.setInfo(type='Video', infoLabels=info)
	liz.setArt({'icon': icon, 'thumb': image, 'poster': image, 'fanart': defaultFanart})
	if image and useThumbAsFanart and image != icon and not artpic in image:
		liz.setArt({'fanart': image})
	liz.setProperty('IsPlayable', 'true')
	liz.setContentLookup(False)
	liz.addContextMenuItems([(translation(30654), 'RunPlugin({0}?{1})'.format(HOST_AND_PATH, 'mode=AddToQueue'))])
	return xbmcplugin.addDirectoryItem(handle=ADDON_HANDLE, url=u, listitem=liz)
