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
import io
import threading
PY2 = sys.version_info[0] == 2
if PY2:
	from urllib import urlencode, quote_plus  # Python 2.X
else: 
	from urllib.parse import urlencode, quote_plus  # Python 3.X

from .common import *


def preparefiles(url, name, rotation):
	debug_MS("(mediatools.preparefiles) -------------------------------------------------- START = tolibrary --------------------------------------------------")
	if mediaPath =="":
		return dialog.ok(addon_id, translation(30502))
	elif mediaPath !="" and ADDON_operate('service.cron.autobiblio'):
		newSOURCE = quote_plus(mediaPath+fixPathSymbols(name))
		if newMETHOD:
			url = url+'@@Series'
			newSOURCE = quote_plus(mediaPath+'Series'+os.sep+fixPathSymbols(name))
		newURL = '{0}?mode=generatefiles&url={1}&name={2}'.format(sys.argv[0], url, name)
		newNAME, newURL = quote_plus(name), quote_plus(newURL)
		debug_MS("(mediatools.preparefiles) ### newNAME : {0} ###".format(str(newNAME)))
		debug_MS("(mediatools.preparefiles) ### newURL : {0} ###".format(str(newURL)))
		debug_MS("(mediatools.preparefiles) ### newSOURCE : {0} ###".format(str(newSOURCE)))
		xbmc.executebuiltin('RunPlugin(plugin://service.cron.autobiblio/?mode=adddata&name={0}&stunden={1}&url={2}&source={3})'.format(newNAME, rotation, newURL, newSOURCE))
		return dialog.notification(translation(30531), translation(30532).format(name+'  (Serie)', str(rotation)), icon, 15000)

def generatefiles(url, name):
	debug_MS("(mediatools.generatefiles) -------------------------------------------------- START = generatefiles --------------------------------------------------")
	th = threading.Thread(target=LIBRARY_Worker, args=(url, name))
	th.daemon = True
	th.start()

def LIBRARY_Worker(BroadCast_Idd, BroadCast_Name):
	debug_MS("(mediatools.LIBRARY_Worker) ### BroadCast_Idd = {0} ### BroadCast_Name = {1} ###".format(BroadCast_Idd, BroadCast_Name))
	if not enableLIBRARY or mediaPath =="":
		return
	BIBO_PAGES, BIBO_EPISODE, COMBINATION = ([] for _ in range(3))
	pos_ESP = 0
	elem_IDD = BroadCast_Idd.split('@@')[0] if '@@' in BroadCast_Idd else BroadCast_Idd
	if newMETHOD:
		EP_Path = os.path.join(py2_uni(mediaPath), 'Series', py2_uni(fixPathSymbols(BroadCast_Name)), '')
	else:
		EP_Path = os.path.join(py2_uni(mediaPath), py2_uni(fixPathSymbols(BroadCast_Name)), '')
	TVS_URL = '{0}/content/shows?include=images,genres,seasons&sort=name&filter[id]={1}'.format(BASE_API, elem_IDD)
	debug_MS("(mediatools.LIBRARY_Worker) ##### TVS_URL : {0} #####".format(str(TVS_URL)))
	debug_MS("(mediatools.LIBRARY_Worker) ##### EP_Path : {0} #####".format(str(EP_Path)))
	if os.path.isdir(EP_Path):
		shutil.rmtree(EP_Path, ignore_errors=True)
		xbmc.sleep(500)
	xbmcvfs.mkdirs(EP_Path)
	try:
		SHOW_DATA = getUrl(TVS_URL)
		TVS_title = cleaning(SHOW_DATA['data'][0]['attributes']['name'])
	except: return
	for elem in SHOW_DATA['data']:
		TVS_season, TVS_episode, TVS_plot, TVS_image, TVS_airdate, TVS_yeardate = ("" for _ in range(6))
		TVS_photoID = None
		if elem.get('relationships', None) and elem.get('relationships').get('images', None) and elem.get('relationships').get('images').get('data', None):
			TVS_photoID = [poid.get('id', []) for poid in elem.get('relationships', {}).get('images', {}).get('data', '')][0]
		elem = elem['attributes'] if elem.get('attributes', '') else elem
		TVS_season = (str(elem.get('seasonNumbers', '')) or "")
		TVS_episode = (str(elem.get('episodeCount', '')) or "")
		TVS_plot = (cleaning(elem.get('description', '')).replace('\n', '[CR]') or "")
		TVS_pictures  = SHOW_DATA.get('included', [])
		try: TVS_image = [img.get('attributes', '').get('src', []) for img in TVS_pictures if img.get('id') == TVS_photoID][0]
		except: pass
		TVS_airdate = (str(elem.get('latestVideo', {}).get('airDate', ''))[:10] or str(elem.get('newestEpisodePublishStart', ''))[:10] or "")
		TVS_yeardate = (str(elem.get('latestVideo', {}).get('airDate', ''))[:4] or str(elem.get('newestEpisodePublishStart', ''))[:4] or "")
	for qs in range(1, 6, 1):
		BLINK = '{0}/content/videos?include=images,genres&sort=name&filter[show.id]={1}&filter[videoType]=EPISODE,STANDALONE&page[number]={2}&page[size]=100'.format(BASE_API, elem_IDD, str(qs))
		debug_MS("(mediatools.LIBRARY_Worker[1]]) EPISODE-PAGES XXX POS = {0} || URL = {1} XXX".format(str(qs), BLINK))
		BIBO_PAGES.append([int(qs), BLINK])
	if BIBO_PAGES:
		BIBO_EPISODE = getMultiData(BIBO_PAGES)
		if BIBO_EPISODE:
			DATA_UNO = json.loads(BIBO_EPISODE)
			#log("++++++++++++++++++++++++")
			#log("(mediatools.LIBRARY_Worker[2]) no.02 XXXXX DATA_UNO : {0} XXXXX".format(str(DATA_UNO)))
			#log("++++++++++++++++++++++++")
			for sumo in DATA_UNO:
				if sumo is not None and 'data' in sumo and len(sumo['data']) > 0:
					GENRES = list(filter(lambda x: x['type'] == 'genre', sumo.get('included', [])))
					IMAGES = list(filter(lambda x: x['type'] == 'image', sumo.get('included', [])))
					for catch in sumo.get('data', []):
						EP_SUFFIX, Note_1, Note_2, Note_3, EP_fsk, EP_image, EP_airdate, EP_yeardate = ("" for _ in range(8))
						EP_season, EP_episode, EP_duration = ('0' for _ in range(3))
						startTIMES, endTIMES = (None for _ in range(2))
						oneGEN, twoGEN = ([] for _ in range(2))
						if catch.get('relationships').get('genres', None) and catch.get('relationships').get('genres').get('data', None):
							oneGEN = [og.get('id', []) for og in catch['relationships']['genres']['data']]
							twoGEN = [py2_enc(tg.get('attributes', {}).get('name', [])) for tg in GENRES if tg.get('id') in oneGEN]
							if twoGEN: twoGEN = sorted(twoGEN)
						if catch.get('relationships').get('images', None) and catch.get('relationships').get('images').get('data', None):
							EP_image = [img.get('attributes', {}).get('src', []) for img in IMAGES if img.get('id') == catch['relationships']['images']['data'][0]['id']][0]
						try: EP_genre1 = twoGEN[0]
						except: EP_genre1 = ""
						try: EP_genre2 = twoGEN[1]
						except: EP_genre2 = ""
						try: EP_genre3 = twoGEN[2]
						except: EP_genre3 = ""
						EP_idd = str(catch['id'])
						catch = catch['attributes'] if catch.get('attributes', '') else catch
						debug_MS("(mediatools.LIBRARY_Worker[2]) ##### ELEMENT : {0} #####".format(str(catch)))
						if catch.get('name', ''):
							EP_name = cleaning(catch['name'])
						else: continue
						if catch.get('isExpiring', '') is True or catch.get('isNew', '') is True:
							EP_SUFFIX = translation(30624) if catch.get('isNew', '') is True else translation(30625)
						EP_season = str(catch['seasonNumber']).zfill(2) if catch.get('seasonNumber', '') else '0'
						EP_episode = str(catch['episodeNumber']).zfill(2) if catch.get('episodeNumber', '') else '0'
						EP_type = (catch.get('videoType', 'SINGLE') or 'SINGLE')
						if EP_type.upper() == 'STANDALONE' and EP_episode == '0':
							pos_ESP += 1
						if EP_season != '0' and EP_episode != '0':
							EP_name = 'S'+EP_season+'E'+EP_episode+': '+EP_name
						else:
							if EP_type.upper() == 'STANDALONE':
								EP_episode = str(pos_ESP).zfill(2)
								EP_name = 'S00E'+EP_episode+': '+EP_name
						if str(catch.get('publishStart'))[:4].isdigit() and str(catch.get('publishStart'))[:4] not in ['0', '1970']:
							LOCALstart = get_Local_DT(catch['publishStart'][:19])
							startTIMES = LOCALstart.strftime('%d{0}%m{0}%y {1} %H{2}%M').format('.', '•', ':')
						if str(catch.get('publishEnd'))[:4].isdigit() and str(catch.get('publishEnd'))[:4] not in ['0', '1970']:
							LOCALend = get_Local_DT(catch['publishEnd'][:19])
							endTIMES = LOCALend.strftime('%d{0}%m{0}%y {1} %H{2}%M').format('.', '•', ':')
						if startTIMES and endTIMES: Note_1 = translation(30629).format(str(startTIMES), str(endTIMES))
						elif startTIMES and endTIMES is None: Note_1 = translation(30630).format(str(startTIMES))
						if str(catch.get('rating')).isdigit():
							EP_fsk = translation(30631).format(str(catch['rating'])) if str(catch.get('rating')) != '0' else translation(30632)
						if EP_fsk == "" and 'contentRatings' in catch and catch['contentRatings'] and len(catch['contentRatings']) > 0:
							if str(catch.get('contentRatings', {})[0].get('code', '')).isdigit():
								EP_fsk = translation(30631).format(str(catch.get('contentRatings', {})[0].get('code', ''))) if str(catch.get('contentRatings', {})[0].get('code', '')) != '0' else translation(30632)
						Note_2 = cleaning(catch['description']).replace('\n', '[CR]') if catch.get('description', '') else ""
						EP_plot = BroadCast_Name+'[CR]'+Note_1+Note_2
						EP_protect = (catch.get('drmEnabled', False) or False)
						EP_duration = get_Time(catch['videoDuration'], 'MINUTES') if str(catch.get('videoDuration')).isdigit() else '0'
						EP_airdate = (str(catch.get('airDate', ''))[:10] or str(catch.get('publishStart', ''))[:10] or "")
						EP_yeardate = (str(catch.get('airDate', ''))[:4] or str(catch.get('publishStart', ''))[:4] or "")
						EP_COMPLETE_EXTRAS = '{0}?{1}'.format(HOST_AND_PATH, urlencode({'mode': 'playVideo', 'url': EP_idd}))
						episodeFILE = py2_uni(fixPathSymbols(EP_name)) # NAME=STANDARD OHNE HINWEIS (neu|endet bald) !!!
						EP_LONG_title = EP_name+EP_SUFFIX # NAME=LONVERSION MIT SUFFIX=HINWEIS (neu|endet bald) !!!
						COMBINATION.append([episodeFILE, EP_LONG_title, TVS_title, EP_idd, EP_season, EP_episode, EP_plot, EP_duration, EP_image, EP_fsk, EP_genre1, EP_genre2, EP_genre3, EP_yeardate, EP_airdate, EP_protect, EP_COMPLETE_EXTRAS])
	if not COMBINATION: return
	if not os.path.exists(EP_Path):
		os.makedirs(EP_Path)
	for episodeFILE, EP_LONG_title, TVS_title, EP_idd, EP_season, EP_episode, EP_plot, EP_duration, EP_image, EP_fsk, EP_genre1, EP_genre2, EP_genre3, EP_yeardate, EP_airdate, EP_protect, EP_COMPLETE_EXTRAS in COMBINATION:
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
    <runtime>{5}</runtime>
    <thumb>{6}</thumb>
    <mpaa>{7}</mpaa>
    <genre clear="true">{8}</genre>
    <genre>{9}</genre>
    <genre>{10}</genre>
    <year>{11}</year>
    <aired>{12}</aired>
    <studio clear="true">DMAX</studio>
</episodedetails>'''.format(EP_LONG_title, TVS_title, EP_season, EP_episode, EP_plot, EP_duration, EP_image, EP_fsk, EP_genre1, EP_genre2, EP_genre3, EP_yeardate, EP_airdate)))
		streamfile = os.path.join(EP_Path, episodeFILE+'.strm')
		debug_MS("(mediatools.LIBRARY_Worker[3]) ##### streamFILE : {0} #####".format(cleaning(streamfile)))
		file = xbmcvfs.File(streamfile, 'w')
		file.write(EP_COMPLETE_EXTRAS)
		file.close()
	nfo_SERIE_string = os.path.join(EP_Path, 'tvshow.nfo')
	with io.open(nfo_SERIE_string, 'w', encoding='utf-8') as textobj_TVS:
		textobj_TVS.write(py2_uni(
'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<tvshow>
    <title>{0}</title>
    <showtitle>{0}</showtitle>
    <season>{1}</season>
    <episode>{2}</episode>
    <plot>{3}</plot>
    <thumb aspect="landscape" preview="">{4}</thumb>
    <fanart>
        <thumb dim="1280x720" colors="" preview="{4}">{4}</thumb>
    </fanart>
    <genre clear="true">{5}</genre>
    <genre>{6}</genre>
    <genre>{7}</genre>
    <year>{8}</year>
    <aired>{9}</aired>
    <studio clear="true">DMAX</studio>
</tvshow>'''.format(TVS_title, TVS_season, TVS_episode, TVS_plot, TVS_image, EP_genre1, EP_genre2, EP_genre3, TVS_yeardate, TVS_airdate)))
	debug_MS("(mediatools.LIBRARY_Worker[4]) XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX  ENDE = LIBRARY_Worker  XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
