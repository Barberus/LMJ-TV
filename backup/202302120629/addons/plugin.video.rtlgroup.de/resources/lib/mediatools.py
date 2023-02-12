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
import io
PY2 = sys.version_info[0] == 2
if PY2:
	from urllib import urlencode, quote_plus  # Python 2.X
else: 
	from urllib.parse import urlencode, quote_plus  # Python 3.X
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from .common import *


def getHTML(url, method='GET', REF=None, cookies=None, allow_redirects=True, stream=None, data=None, json=None):
	simple = requests.Session()
	REACTION = None
	try:
		response = simple.get(url, headers={'User-Agent': get_userAgent()}, allow_redirects=allow_redirects, verify=verify_ssl_connect, stream=stream, timeout=30)
		REACTION = response.json() if method in ['GET', 'POST'] else py2_enc(response.text)
	except requests.exceptions.RequestException as e:
		failing("(mediatools.getHTML) ERROR - ERROR - ERROR : ##### url: {0} === error: {1} #####".format(url, str(e)))
		dialog.notification(translation(30521).format('URL', ''), translation(30523).format(str(e)), icon, 12000)
		return sys.exit(0)
	return REACTION

def preparefiles(url, name, XTRA, rotation):
	debug_MS("(mediatools.preparefiles) -------------------------------------------------- START = tolibrary --------------------------------------------------")
	if mediaPath =="":
		return dialog.ok(addon_id, translation(30508))
	elif mediaPath !="" and ADDON_operate('service.cron.autobiblio'):
		title = name
		if XTRA in ['Series', 'Movies']:
			title += '  ('+XTRA.replace('es', 'e')+')'
			newSOURCE = quote_plus(mediaPath+fixPathSymbols(name))
			if newMETHOD:
				url = url+'@@'+XTRA
				newSOURCE = quote_plus(mediaPath+XTRA+os.sep+fixPathSymbols(name))
		elif XTRA not in ['Series', 'Movies']:
			title += '  ('+XTRA+')'
			url = url+'@@'+XTRA.replace('Jahr ', '')
			newSOURCE = quote_plus(mediaPath+fixPathSymbols(name)+os.sep+XTRA)
			if newMETHOD:
				newSOURCE = quote_plus(mediaPath+'Series'+os.sep+fixPathSymbols(name)+os.sep+XTRA)
		newURL = '{0}?mode=generatefiles&url={1}&name={2}'.format(sys.argv[0], url, name)
		newNAME, newURL = quote_plus(name), quote_plus(newURL)
		debug_MS("(mediatools.preparefiles) ### newNAME : {0} ###".format(str(newNAME)))
		debug_MS("(mediatools.preparefiles) ### newURL : {0} ###".format(str(newURL)))
		debug_MS("(mediatools.preparefiles) ### newSOURCE : {0} ###".format(str(newSOURCE)))
		xbmc.executebuiltin('RunPlugin(plugin://service.cron.autobiblio/?mode=adddata&name={0}&stunden={1}&url={2}&source={3})'.format(newNAME, rotation, newURL, newSOURCE))
		return dialog.notification(translation(30571), translation(30572).format(title, str(rotation)), icon, 15000)

def querypages(url, TVFOL, EPATH, POS=200):
	DATA_UNO = getHTML('{0}&page=1'.format(url))
	debug_MS("(mediatools.generatefiles[2]) no.02 - SUCCESSFULLY CREATED XXXXX URL-ONE : {0} XXXXX ".format(TVFOL))
	debug_MS("(mediatools.generatefiles[3]) no.03 ### EP-PATH : {0} ###".format(str(EPATH)))
	debug_MS("(mediatools.generatefiles[4]) no.04 ### URL-TWO : {0}&page=1 ###".format(url))
	if DATA_UNO.get('movies', '') and DATA_UNO.get('movies', {}).get('items', ''):
		DATA_UNO = DATA_UNO['movies']
	for item in DATA_UNO.get('items', []): yield item
	ALLPAGES = int(DATA_UNO.get('total', [])) // int(POS) if DATA_UNO.get('total', '') else -1
	debug_MS("(mediatools.querypages) ### Total-Items : {0} || Result of PAGES : {1} ###".format(str(DATA_UNO.get('total', None)), str(ALLPAGES+1)))
	for page in range(2, ALLPAGES+2, 1):
		DATA_DUE = getHTML('{0}&page={1}'.format(url, page))
		debug_MS("(mediatools.generatefiles[5]) no.05 ### URL-TRES : {0}&page={1} ###".format(url, page))
		if DATA_DUE.get('movies', '') and DATA_DUE.get('movies', {}).get('items', ''):
			DATA_DUE = DATA_DUE['movies']
		for item in DATA_DUE.get('items', []): yield item

def generatefiles(BroadCast_URL, BroadCast_NAME):
	debug_MS("(mediatools.generatefiles) -------------------------------------------------- START = generatefiles --------------------------------------------------")
	debug_MS("(mediatools.generatefiles) ### BroadCast_URL = {0} || BroadCast_NAME = {1} ###".format(BroadCast_URL, BroadCast_NAME))
	if not enableLIBRARY or mediaPath =="":
		return
	EPIS_ENTRIES = '[%22id%22,%22title%22,%22broadcastStartDate%22,%22catchupStartDate%22,%22articleShort%22,%22articleLong%22,%22teaserText%22,%22seoUrl%22,%22season%22,%22episode%22,%22duration%22,%22isDrm%22,%22free%22,%22payed%22,%22fsk%22,%22productionYear%22,'\
									'%22format%22,[%22id%22,%22title%22,%22station%22,%22seoUrl%22,%22formatImageClear%22,%22formatimageArtwork%22,%22defaultImage169Logo%22,%22genre1%22,%22genre2%22,%22genres%22,%22categoryId%22,%22formatType%22],%22manifest%22,[%22dash%22,%22dashhd%22]]&maxPerPage=200'
	COMBINATION = []
	pos_ESP = 0
	elem_IDD, elem_TAG = BroadCast_URL, None
	if '@@' in BroadCast_URL:
		elem_IDD = BroadCast_URL.split('@@')[0]
		elem_TAG = BroadCast_URL.split('@@')[1]
	if newMETHOD:
		if elem_TAG and elem_TAG in ['Series', 'Movies']:
			TVS_Path = os.path.join(py2_uni(mediaPath), elem_TAG, py2_uni(fixPathSymbols(BroadCast_NAME)), '')
			EP_Path = os.path.join(py2_uni(mediaPath), elem_TAG, py2_uni(fixPathSymbols(BroadCast_NAME)), '')
		elif elem_TAG and elem_TAG not in ['Series', 'Movies']:
			TVS_Path = os.path.join(py2_uni(mediaPath), 'Series', py2_uni(fixPathSymbols(BroadCast_NAME)), '')
			EP_Path = os.path.join(py2_uni(mediaPath), 'Series', py2_uni(fixPathSymbols(BroadCast_NAME)), str(elem_TAG), '')
		else:
			TVS_Path = os.path.join(py2_uni(mediaPath), 'Series', py2_uni(fixPathSymbols(BroadCast_NAME)), '')
			EP_Path = os.path.join(py2_uni(mediaPath), 'Series', py2_uni(fixPathSymbols(BroadCast_NAME)), '')
	else:
		if elem_TAG and elem_TAG not in ['Series', 'Movies']:
			TVS_Path = os.path.join(py2_uni(mediaPath), py2_uni(fixPathSymbols(BroadCast_NAME)), '')
			EP_Path = os.path.join(py2_uni(mediaPath), py2_uni(fixPathSymbols(BroadCast_NAME)), str(elem_TAG), '')
		else:
			TVS_Path = os.path.join(py2_uni(mediaPath), py2_uni(fixPathSymbols(BroadCast_NAME)), '')
			EP_Path = os.path.join(py2_uni(mediaPath), py2_uni(fixPathSymbols(BroadCast_NAME)), '')
	url_1 = '{0}/formats/{1}?fields=[%22id%22,%22title%22,%22station%22,%22hasFreeEpisodes%22,%22seoUrl%22,%22tabSeason%22,%22formatimageArtwork%22,%22formatimageMoviecover169%22,%22genre1%22,%22genres%22,%22categoryId%22,%22infoText%22,%22infoTextLong%22,%22onlineDate%22,%22annualNavigation%22,%22seasonNavigation%22]'.format(API_URL, str(elem_IDD))
	debug_MS("(mediatools.generatefiles[1]) no.01 - PREPARE FOLDER FOR XXXXX URL-ONE : {0} XXXXX ".format(str(url_1)))
	if os.path.isdir(EP_Path):
		shutil.rmtree(EP_Path, ignore_errors=True)
		xbmc.sleep(300)
	if xbmcvfs.exists(os.path.join(TVS_Path, 'tvshow.nfo')):
		xbmcvfs.delete(os.path.join(TVS_Path, 'tvshow.nfo'))
	xbmcvfs.mkdirs(EP_Path)
	try:
		SHOW_DATA = getHTML(url_1)
		TVS_name = cleaning(SHOW_DATA['title'])
	except: return
	SERIES_IDD = str(SHOW_DATA['id'])
	TVS_studio, TVS_image, TVS_airdate = ("" for _ in range(3))
	TVS_studio = SHOW_DATA['station'].upper() if SHOW_DATA.get('station', '') else 'UNK'
	TVS_image = (cleanPhoto(SHOW_DATA.get('formatimageMoviecover169', '')) or cleanPhoto(SHOW_DATA.get('formatimageArtwork', '')) or IMG_series.format(SERIES_IDD))
	TVS_plot = get_Description(SHOW_DATA, 'TVS')
	if str(SHOW_DATA.get('onlineDate'))[:4] not in ['', 'None', '0', '1970']:
		TVS_airdate = str(SHOW_DATA['onlineDate'])[:10]
	if elem_TAG and elem_TAG not in ['Series', 'Movies']:
		if len(elem_TAG) == 4:
			url_2 = '{0}/movies?filter={{%22BroadcastStartDate%22:{{%22between%22:{{%22start%22:%22{1}-01-01%2000:00:00%22,%22end%22:%22{1}-12-31%2023:59:59%22}}}},%22FormatId%22:{2}}}&fields={3}'.format(API_URL, elem_TAG, SERIES_IDD, EPIS_ENTRIES)
		elif 'Staffel ' in elem_TAG:
			url_2 = '{0}/movies?filter={{%22Season%22:{1},%22FormatId%22:{2}}}&fields={3}'.format(API_URL, elem_TAG.split('Staffel ')[1], SERIES_IDD, EPIS_ENTRIES)
	else:
		url_2 = '{0}/movies?filter={{%22FormatId%22:{1}}}&fields={2}'.format(API_URL, SERIES_IDD, EPIS_ENTRIES)
	for vid in querypages(url_2, url_1, EP_Path):
		EP_tagline, EP_description, Note_1, Note_2, Note_3, Note_4, Note_5, Note_6, Note_7, EP_fsk, EP_yeardate, EP_studio, EP_airdate = ("" for _ in range(13))
		EP_season, EP_episode, EP_duration = ('0' for _ in range(3))
		startDESC, startTITLE = (None for _ in range(2))
		EP_genreLIST = []
		EP_STARTS = (vid.get('broadcastStartDate', None) or vid.get('catchupStartDate', None) or None)
		if str(EP_STARTS)[:4].isdigit() and str(EP_STARTS)[:4] not in ['0', '1970']:
			broadcast = datetime(*(time.strptime(EP_STARTS[:19], '%Y{0}%m{0}%d %H{1}%M{1}%S'.format('-', ':'))[0:6])) # 2015-10-07 05:10:00
			startDESC = broadcast.strftime('%a{0} %d{0}%m{0}%y {1} %H{2}%M').format('.', '•', ':')
			for sd in (('Mon', translation(32101)), ('Tue', translation(32102)), ('Wed', translation(32103)), ('Thu', translation(32104)), ('Fri', translation(32105)), ('Sat', translation(32106)), ('Sun', translation(32107))): startDESC = startDESC.replace(*sd)
			startTITLE = broadcast.strftime('%d{0}%m{0}%y {1} %H{2}%M').format('.', '•', ':')
		EP_protect = (vid.get('isDrm', False) or False)
		EP_idd = str(vid['id'])
		try: TVS_title = cleaning(vid['format']['title'])
		except: 
			try: TVS_title = cleaning(vid['format']['seoUrl']).replace('-', ' ').title()
			except: continue
		debug_MS("(mediatools.generatefiles[6]) no.06 xxxxx ELEM-06 : {0} xxxxx".format(str(vid)))
		EP_title = cleaning(vid['title'])
		pos_ESP += 1
		EP_season = str(vid['season']).zfill(2) if vid.get('season', '') else '0'
		EP_episode = str(vid['episode']).replace('P', '').zfill(2) if vid.get('episode', '') else '0'
		EP_duration = get_Time(vid['duration'], 'MINUTES') if vid.get('duration', '') else '0'
		EP_tagline = (cleaning(vid.get('teaserText', '')) or "")
		EP_description = get_Description(vid)
		if EP_description != "": EP_description = '[CR]'+EP_description
		if TVS_title !="": Note_1 = TVS_title
		if EP_season != '0' and EP_episode != '0':
			Note_3 = translation(30624).format(EP_season, EP_episode)
		Note_4 = translation(30625).format(str(startDESC)) if startDESC else '[CR]' if Note_3 != "" else ""
		if showDATE and startTITLE:
			Note_6 = translation(30626).format(str(startTITLE))
		if str(vid.get('fsk')).isdigit():
			EP_fsk = translation(30627).format(str(vid['fsk'])) if str(vid.get('fsk')) != '0' else translation(30628)
		if str(vid.get('productionYear'))[:4].isdigit() and str(vid.get('productionYear'))[:4] not in ['0', '1970']:
			EP_yeardate = str(vid['productionYear'])[:4]
		EP_PayFree = (vid.get('payed', True) or vid.get('free', True))
		EP_cover = IMG_coverdvd.format(SERIES_IDD)
		EP_image = IMG_movies.format(EP_idd)
		if vid.get('format', ''):
			EP_studio = vid['format']['station'].upper() if vid['format'].get('station', '') else 'UNK'
			if vid.get('format', {}).get('genres', ''):
				EP_genreLIST = [cleaning(item) for item in vid.get('format', {}).get('genres', '')]
				if EP_genreLIST: EP_genreLIST = sorted(EP_genreLIST)
		try: EP_genre1 = EP_genreLIST[0]
		except: EP_genre1 = ""
		try: EP_genre2 = EP_genreLIST[1]
		except: EP_genre2 = ""
		try: EP_genre3 = EP_genreLIST[2]
		except: EP_genre3 = ""
		if EP_PayFree is False and vodPremium is False:
			Note_2 = '   [COLOR skyblue](premium)[/COLOR]'
			Note_7 = '     [COLOR deepskyblue](premium)[/COLOR]'
		EP_plot = Note_1+Note_2+'[CR]'+Note_3+Note_4+EP_description
		EP_LONG_title = EP_title+Note_6+Note_7
		EP_airdate = (str(vid.get('broadcastStartDate', ''))[:10] or str(vid.get('broadcastPreviewStartDate', ''))[:10] or "")
		if newMETHOD and elem_TAG and elem_TAG == 'Movies':
			EP_SHORT_title = EP_title
		else:
			if EP_season != '0' and EP_episode != '0':
				EP_SHORT_title = 'S'+EP_season+'E'+EP_episode+'_'+EP_title
			else:
				EP_episode = str(pos_ESP).zfill(2)
				EP_SHORT_title = 'S00E'+EP_episode+'_'+EP_title
		EP_STREAM_ENTRIES = '{0}?{1}'.format(HOST_AND_PATH, urlencode({'mode': 'playDash', 'xcode': EP_idd}))
		episodeFILE = py2_uni(fixPathSymbols(EP_SHORT_title))
		COMBINATION.append([episodeFILE, EP_LONG_title, TVS_title, EP_idd, EP_season, EP_episode, EP_plot, EP_tagline, EP_duration, EP_cover, EP_image, EP_fsk, EP_genre1, EP_genre2, EP_genre3, EP_yeardate, EP_airdate, EP_studio, EP_STREAM_ENTRIES])
	if not COMBINATION: return
	else:
		if not os.path.exists(EP_Path):
			os.makedirs(EP_Path)
		if newMETHOD and elem_TAG and elem_TAG == 'Movies':
			for episodeFILE, EP_LONG_title, TVS_title, EP_idd, EP_season, EP_episode, EP_plot, EP_tagline, EP_duration, EP_cover, EP_image, EP_fsk, EP_genre1, EP_genre2, EP_genre3, EP_yeardate, EP_airdate, EP_studio, EP_STREAM_ENTRIES in COMBINATION:
				nfo_MOVIE_string = os.path.join(EP_Path, episodeFILE+'.nfo')
				with io.open(nfo_MOVIE_string, 'w', encoding='utf-8') as textobj_MO:
					textobj_MO.write(py2_uni(
'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<movie>
    <title>{0}</title>
    <originaltitle>{1}</originaltitle>
    <plot>{4}</plot>
    <tagline>{5}</tagline>
    <runtime>{6}</runtime>
    <thumb aspect="poster" preview="{7}">{7}</thumb>
    <thumb aspect="" preview="{8}">{8}</thumb>
    <fanart>
        <thumb dim="1280x720" colors="" preview="{8}">{8}</thumb>
    </fanart>
    <mpaa>{9}</mpaa>
    <genre clear="true">{10}</genre>
    <genre>{11}</genre>
    <genre>{12}</genre>
    <year>{13}</year>
    <aired>{14}</aired>
    <studio clear="true">{15}</studio>
</movie>'''.format(EP_LONG_title, TVS_title, EP_season, EP_episode, EP_plot, EP_tagline, EP_duration, EP_cover, EP_image, EP_fsk, EP_genre1, EP_genre2, EP_genre3, EP_yeardate, EP_airdate, EP_studio)))
				streamfile = os.path.join(EP_Path, episodeFILE+'.strm')
				debug_MS("(mediatools.generatefiles[7]) no.07 ##### streamFILE : {0} #####".format(cleaning(streamfile)))
				file = xbmcvfs.File(streamfile, 'w')
				file.write(EP_STREAM_ENTRIES)
				file.close()
		else:
			for episodeFILE, EP_LONG_title, TVS_title, EP_idd, EP_season, EP_episode, EP_plot, EP_tagline, EP_duration, EP_cover, EP_image, EP_fsk, EP_genre1, EP_genre2, EP_genre3, EP_yeardate, EP_airdate, EP_studio, EP_STREAM_ENTRIES in COMBINATION:
				nfo_EPISODE_string = os.path.join(EP_Path, episodeFILE+'.nfo')
				with io.open(nfo_EPISODE_string, 'w', encoding='utf-8') as textobj_EP:
					textobj_EP.write(py2_uni(
'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<episodedetails>
    <title>{0}</title>
    <showtitle>{1}</showtitle>
    <season>{2}</season>
    <episode>{3}</episode>
    <plot>{4}</plot>
    <tagline>{5}</tagline>
    <runtime>{6}</runtime>
    <thumb>{8}</thumb>
    <mpaa>{9}</mpaa>
    <genre clear="true">{10}</genre>
    <genre>{11}</genre>
    <genre>{12}</genre>
    <year>{13}</year>
    <aired>{14}</aired>
    <studio clear="true">{15}</studio>
</episodedetails>'''.format(EP_LONG_title, TVS_title, EP_season, EP_episode, EP_plot, EP_tagline, EP_duration, EP_cover, EP_image, EP_fsk, EP_genre1, EP_genre2, EP_genre3, EP_yeardate, EP_airdate, EP_studio)))
				streamfile = os.path.join(EP_Path, episodeFILE+'.strm')
				debug_MS("(mediatools.generatefiles[8]) no.08 ##### streamFILE : {0} #####".format(cleaning(streamfile)))
				file = xbmcvfs.File(streamfile, 'w')
				file.write(EP_STREAM_ENTRIES)
				file.close()
			nfo_SERIE_string = os.path.join(TVS_Path, 'tvshow.nfo')
			with io.open(nfo_SERIE_string, 'w', encoding='utf-8') as textobj_TVS:
				textobj_TVS.write(py2_uni(
'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<tvshow>
    <title>{0}</title>
    <showtitle>{0}</showtitle>
    <season></season>
    <episode></episode>
    <plot>{1}</plot>
    <thumb aspect="landscape" preview="">{2}</thumb>
    <fanart>
        <thumb dim="1280x720" colors="" preview="{2}">{2}</thumb>
    </fanart>
    <genre clear="true">{3}</genre>
    <genre>{4}</genre>
    <genre>{5}</genre>
    <year>{6}</year>
    <aired>{7}</aired>
    <studio clear="true">{8}</studio>
</tvshow>'''.format(TVS_name, TVS_plot, TVS_image, EP_genre1, EP_genre2, EP_genre3, EP_yeardate, TVS_airdate, TVS_studio)))
	debug_MS("(mediatools.generatefiles[9]) XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX  ENDE = generatefiles  XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
