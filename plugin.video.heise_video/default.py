#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys, urllib, urllib2, re, xbmcplugin, xbmcgui, xbmcaddon, json

dbg = False
pluginhandle = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.heise_video')
translation = settings.getLocalizedString
forceViewMode = settings.getSetting("forceViewMode") == "true"
maxViewPages = int(settings.getSetting("maxViewPages"))*2
if maxViewPages == 0: maxViewPages = 1
viewMode = str(settings.getSetting("viewMode"))

baseurl = 'http://www.heise.de'

def index():
	addDir('Neue Videos', '', 'newVideos', '')
	addDir('Android', baseurl + '/video/thema/Android', 'showVideos', '')
	addDir('c\'t Uplink', baseurl + '/video/thema/c%27t-uplink', 'showVideos', '')
	addDir('c\'t zockt', baseurl + '/video/thema/c%27t-zockt', 'showVideos', '')
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
	url = baseurl + '/video/?teaser=neuste;offset=0;into=reiter_1&hajax=1'
	if dbg: print 'open ' + url
	content = getUrl(url).replace('\\"','"')
	for href, img, title in re.compile('class="rahmen"[^<]*<a[^>]*href="([^"]*)">[^<]*<img[^>]*src="([^"]*)"[^>]*(?:title|alt)="([^"]*)"', re.DOTALL).findall(content):
		if not title: title = re.compile('<a[^>]*href="'+href+'"[^>]*title="([^>]+)">', re.DOTALL).findall(content)[0]
		if not baseurl in href: href = baseurl + href
		if not baseurl in img: img = baseurl + img
		title = cleanTitle(title)
		if dbg: print 'add link: title=' + title + ' href=' +href + ' img=' + img
		addLink(title, href, 'playVideo', img, '')
	xbmcplugin.endOfDirectory(pluginhandle)
	if forceViewMode: xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')
	
def playVideo(url):
	if dbg: print 'play video: ' + url
	content = getUrl(url)
	videos = []
	for jsonurl in re.compile('json_url:[ ]*"([^"]*)"', re.DOTALL).findall(content):
		data = json.loads(getUrl(jsonurl))
		for frm in data['formats']:
			for res in data['formats'][frm]:
				videos += [(frm + ' -> ' + res, data['formats'][frm][res]['url'])]
	if videos: video = selectVideoDialog(videos)
	if video: return xbmcplugin.setResolvedUrl(pluginhandle, True, xbmcgui.ListItem(path=video))
	else: xbmc.executebuiltin('Notification(Video not found., 5000)')

def selectVideoDialog(videos):
	titles = []
	for name, src in videos: titles.append(name)
	idx = xbmcgui.Dialog().select("", titles)
	return videos[idx][1]

def cleanTitle(title):
		#title = re.sub('<[^>]*>', ' ', title)
		#title = re.sub('&#\d{3};', ' ', title)
		title = title.replace('&lt;','<').replace('&gt;','>').replace('&amp;','&').replace('&quot;','"').replace('&szlig;','ß').replace('&ndash;','-')
		#title = title.replace('&Auml;','Ä').replace('&Uuml;','Ü').replace('&Ouml;','Ö').replace('&auml;','ä').replace('&uuml;','ü').replace('&ouml;','ö').replace('&nbsp;', ' ')
		#title = title.replace('„','"').replace('“','"')
		title = re.sub('Podcast[: ]*', '', title)
		title = re.sub('\s+', ' ', title)
		return title.strip()

def clean(s):
	matches = re.findall("&#\d+;", s)
	for hit in set(matches):
		try: s = s.replace(hit, unichr(int(hit[2:-1])))
		except ValueError: pass
	return urllib.unquote_plus(s)

def getUrl(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0')
	response = urllib2.urlopen(req, timeout=30)
	link = response.read()
	response.close()
	return link

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