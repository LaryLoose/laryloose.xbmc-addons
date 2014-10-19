#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys, urllib, urllib2, re, xbmcplugin, xbmcgui, xbmcaddon, json

dbg = False
pluginhandle = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.heise_video')
translation = settings.getLocalizedString
forceViewMode = settings.getSetting("forceViewMode") == "true"
viewMode = str(settings.getSetting("viewMode"))
useFQ = settings.getSetting("useFQ") == "true"
format = settings.getSetting("format")
quality = settings.getSetting("quality")
maxViewPages = int(settings.getSetting("maxViewPages"))*2
if maxViewPages == 0: maxViewPages = 1

baseurl = 'http://www.heise.de'
vidout = 'http://www.heise.de/videout/feed?container={c}&sequenz={s}'

def index():
	addDir('Neue Videos', baseurl + '/video/?teaser=neuste;offset=0;into=reiter_1&hajax=1', 'newVideos', '')
	addDir('Android', baseurl + '/video/thema/Android', 'showVideos', '')
	addDir('c\'t Uplink', baseurl + '/video/thema/c%27t-uplink', 'showVideos', '')
	addDir('c\'t zockt', baseurl + '/video/thema/c%27t-zockt', 'showVideos', '')
	addDir('IFA', baseurl + '/video/thema/ifa', 'showVideos', '')
	addDir('Google I/O', baseurl + '/video/thema/Google-I%E2%88%95O', 'showVideos', '')
	addDir('Microsoft', baseurl + '/video/thema/Microsoft', 'showVideos', '')
	addDir('Schnurer hilft!', baseurl + '/video/thema/Schnurer-hilft', 'showVideos', '')
	xbmcplugin.endOfDirectory(pluginhandle)
	if forceViewMode: xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')
	
def showVideos(url):
	if dbg: print 'open ' + url
	content = getUrl(url)
	for href, img, title in re.compile('class="rahmen"[^<]*<a[^>]*href="([^"]*)">[^<]*<img[^>]*src="([^"]*)"[^>]*(?:title|alt)="([^"]*)"', re.DOTALL).findall(content):
		if not title: title = re.compile('<a[^>]*href="'+href+'"[^>]*title="([^>]+)">', re.DOTALL).findall(content)[0]
		if not baseurl in href: href = baseurl + href
		#if not baseurl in img: img = baseurl + img
		title = cleanTitle(title)
		if dbg: print 'add link: title=' + title + ' href=' +href + ' img=' + img
		addLink(title, href, 'playVideo', img, '')
	for nextpage in  re.compile('<li[^>]*class="next">[^<]*<a[^>]*href="([^"]*)">nächste</a>', re.DOTALL).findall(content):
		nextpage = baseurl + nextpage
		if dbg: print 'next page ' + nextpage
		addDir('Nächste Seite', nextpage, 'showVideos', '')
	xbmcplugin.endOfDirectory(pluginhandle)
	if forceViewMode: xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')
	
def newVideos(url):
	if dbg: print 'open ' + url
	jsondata = json.loads(getUrl(url))
	content = jsondata['actions'][1]['html']
	offset = int(re.search('offset=([\d]+);', url).group(1))
	for href, img, title in re.compile('class="rahmen"[^<]*<a[^>]*href="([^"]*)">[^<]*<img[^>]*src="([^"]*)"[^>]*(?:title|alt)="([^"]*)"', re.DOTALL).findall(content):
		if not title: title = re.compile('<a[^>]*href="'+href+'"[^>]*title="([^>]+)">', re.DOTALL).findall(content)[0]
		if not baseurl in href: href = baseurl + href
		if not baseurl in img: img = baseurl + img
		title = cleanTitle(title)
		if dbg: print 'add link: title=' + title + ' href=' +href + ' img=' + img
		addLink(title, href, 'playVideo', img, '')
		offset = offset + 1
	nextpage = re.sub('offset=([\d]+)', 'offset='+str(offset), url)
	addDir('Nächste Seite', nextpage, 'newVideos', '')
	xbmcplugin.endOfDirectory(pluginhandle)
	if forceViewMode: xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')
	
def playVideo(url):
	if dbg: print 'play video: ' + url
	content = getUrl(url)
	videos = []
	video = None	
	for datac, datas in re.compile('id="videoplayerjw-"[^>]*data-container="([0-9]+)"[^>]*data-sequenz="([0-9]+)"', re.DOTALL).findall(content):
		data = getUrl(vidout.replace('{c}', datac).replace('{s}', datas))
		for url, qly, frm in re.compile('file="([^"]+)"[ ]*label="([^"]+)"[ ]*type="video/([^"]+)"', re.DOTALL).findall(data):
			videos += [(frm, qly, url)]
	#for jsonurl in re.compile('json_url:[ ]*"([^"]*)"', re.DOTALL).findall(content):
	#	data = json.loads(getUrl(jsonurl))
	#	for frm in data['formats']:
	#		for qly in data['formats'][frm]:
	#			videos += [(frm, qly, data['formats'][frm][qly]['url'])]
	if videos: video = selectVideoDialog(videos)
	if video: return xbmcplugin.setResolvedUrl(pluginhandle, True, xbmcgui.ListItem(path=video))
	else: xbmc.executebuiltin('Notification(Video not found., 5000)')

def selectVideoDialog(videos):
	url = ''
	if useFQ:
		actqly = 0
		for frm, qly, src in videos:
			if frm == format:
				if actqly == 0: actqly = qly
				if quality == 'max' and frm == format and qly >= actqly: url = src
				elif qly == quality: 
					url = src
					break
	if not url:
		titles = []
		for frm, qly, src in videos: titles.append(frm + ' -> ' + qly)
		idx = xbmcgui.Dialog().select("", titles)
		url = videos[idx][2]
	return url

def cleanTitle(s):
	s = re.sub('&amp;', '&', s)
	s = re.sub('&quot;', '"', s)
	s = re.sub('Podcast[: ]*', '', s)
	s = re.sub('\s+', ' ', s)
	return s.strip()

def getUrl(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0')
	response = urllib2.urlopen(req, timeout=30)
	data = response.read()
	response.close()
	return data

def parameters_string_to_dict(parameters):
	''' Convert parameters encoded in a URL to a dict. '''
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split("&")
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

def addLink(name, url, mode, iconimage, fanart):
	u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode)
	liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	liz.setProperty('IsPlayable', 'true')
	return xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz)

def addDir(name, url, mode, iconimage):
	u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode)
	liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	return xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz, isFolder=True)

params = parameters_string_to_dict(sys.argv[2])
mode = params.get('mode')
url = params.get('url')

if type(url) == type(str()): url = urllib.unquote_plus(url)

if mode == 'showVideos': showVideos(url)
elif mode == 'playVideo': playVideo(url)
elif mode == 'newVideos': newVideos(url)
else: index()