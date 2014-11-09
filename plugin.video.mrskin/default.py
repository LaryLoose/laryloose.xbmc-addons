#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys, urllib, urllib2, re, xbmcplugin, xbmcgui, xbmcaddon

dbg = False 
#dbg = True
pluginhandle = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.mrskin')
translation = settings.getLocalizedString
forceViewMode = settings.getSetting("forceViewMode") == "true"
useThumbAsFanart = settings.getSetting("useThumbAsFanart") == "true"
maxViewPages = int(settings.getSetting("maxViewPages"))*2
if maxViewPages == 0: maxViewPages = 1
viewMode = str(settings.getSetting("viewMode"))

startpage = 'http://www.mrskin.com'
playlist = 'http://www.mrskin.com/video/playlist?t=<tid>'
playlistPlayer = 'http://www.mrskin.com/feeds/playlistPlayer/xml?options[quality]=hd&options[id]=<pid>'
contrex = ['hd: \'([^\']*)\'', 'file: \'([^\']*)\'', 'resources:[^<]*"file":"([^"]*)"']

def index():
	addDir('Original Videos', '', 'origVideos', '')
	addDir('Playlists', '', 'indexPlaylists', '')
	xbmcplugin.endOfDirectory(pluginhandle)
	
def indexPlaylists():
	url = startpage + '/playlists'
	if dbg: print 'open ' + url
	content = getUrl(url)
	for categories in re.compile('<ul[^>]*id="video-categories"[^>]*>.*?</ul>', re.DOTALL).findall(content):
		for href, title in re.compile('<li[^>]*>[^<]*<a[^>]*href="([^"]*)"[^>]*>[^<]*<i[^>]*></i>([^<]*)<', re.DOTALL).findall(categories):
			if 'http' not in href: href = startpage + href
			title = cleanTitle(title).title()
			if dbg: print title + ' --> ' + href
			addDir(title, href, 'showPlaylists')
	xbmcplugin.endOfDirectory(pluginhandle)

def showPlaylists(url):
	if dbg: print 'open ' + url
	content = getUrl(url)
	for collection in re.compile('<div[^>]*id="video-playlist-collection">.*?</div>', re.DOTALL).findall(content):
		for pid, pic, title in re.compile('<li[^>]*>[^<]*<a[^>]*href="[^"]*p([0-9]+).html[^"]*"[^>]*>[^<]*<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"', re.DOTALL).findall(collection):
			if 'http' not in pic: pic = startpage + pic
			href = playlistPlayer.replace('<pid>', pid)
			title = cleanTitle(title)
			if dbg: print title + ' --> ' + href + ' --> ' + pic
			addDir(title, href, 'showPlVideos', pic)
	for nextpage in  re.compile('<li><a[^>]*href="([^"]*)"[^>]*>&raquo;', re.DOTALL).findall(content):
		if 'http' not in nextpage: nextpage = startpage + nextpage
		if dbg: print 'next page ' + nextpage
		addDir('Next Page', nextpage, 'showPlaylists')
	xbmcplugin.endOfDirectory(pluginhandle)
	if forceViewMode: xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def showPlVideos(url):
	if dbg: print 'open ' + url
	content = getUrl(url)
	for item in re.compile('<item>(.*?)</item>', re.DOTALL).findall(content):
		title = cleanTitle(re.compile('<jwplayer:clean_title>([^<]*)</jwplayer:clean_title>', re.DOTALL).findall(item)[0])
		desc = re.compile('<description><!\[CDATA\[([^<]*)\]\]></description>', re.DOTALL).findall(item)[0]
		img = re.compile('<jwplayer:thumbnail>([^<]*)</jwplayer:thumbnail>', re.DOTALL).findall(item)[0]
		href = re.compile('<jwplayer:file>([^<]*)</jwplayer:file>', re.DOTALL).findall(item)[0]
		if 'http' not in href: href = startpage + href 
		if dbg: print title + ' --> ' + href + ' --> ' + img
		addLink(title, href, 'playVideo', img)
	xbmcplugin.endOfDirectory(pluginhandle)
	if forceViewMode: xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def origVideos():
	url = startpage + '/video'
	if dbg: print 'open ' + url
	content = getUrl(url)
	for tagid, cat in re.compile('<a[^>]*data-tag="([^"]*)"[^>]*>[^<]*<i[^>]*>[^<]*</i>([^<]*)</a>', re.DOTALL).findall(content):
		cat = cleanTitle(cat)
		href = playlist.replace('<tid>', tagid)
		if dbg: print cat + ' --> ' + href
		addDir(cat, href, 'showVideos')
	xbmcplugin.endOfDirectory(pluginhandle)
	if forceViewMode: xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')
	
def showVideos(url):
	if dbg: print 'open ' + url
	content = getUrl(url)
	for href, img, title in re.compile('<a[^>]*href="([^"]*)"[^>]*class="[^"]*video[^"]*plain[^"]*"[^>]*>[^<]*<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"[^>]*>', re.DOTALL).findall(content):
		href = startpage + href
		title = cleanTitle(title)
		if dbg: print 'add link: title=' + title + ' href=' +href + ' img=' + img
		addLink(title, href, 'playVideo', img)
	for nextpage in  re.compile('<li>[^<]*<a[^>]*href="(/video/playlist[^"]*)"[^>]*data-page="[^"]*">[^<]*&raquo;[^<]*</a>[^<]*</li>', re.DOTALL).findall(content):
		nextpage = startpage + nextpage
		if dbg: print 'next page ' + nextpage
		addDir('Next Page', nextpage, 'showVideos')
	xbmcplugin.endOfDirectory(pluginhandle)
	if forceViewMode: xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def getVideoUrl(content):
	for rex in contrex:
		if dbg: print 'try search with ' + rex
		match = re.compile(rex, re.DOTALL).findall(content)
		if match: return match[0]
	
def playVideo(url):
	if dbg: print 'play video: ' + url
	if '_pma' in url:
		video = url
	else:
		content = getUrl(url)
		video = getVideoUrl(content)
	if video:
	    listitem = xbmcgui.ListItem(path=video.replace('\\', ''))
	    return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
	else:
	    xbmc.executebuiltin('Notification(Video not found., 5000)')

def cleanTitle(title):
		#title = re.sub('<[^>]*>', ' ', title)
		#title = re.sub('&#\d{3};', ' ', title)
		title = title.replace('&lt;','<').replace('&gt;','>').replace('&amp;','&').replace('&quot;','"').replace('&szlig;','ß').replace('&ndash;','-').replace('&nbsp;', ' ')
		#title = title.replace('&Auml;','Ä').replace('&Uuml;','Ü').replace('&Ouml;','Ö').replace('&auml;','ä').replace('&uuml;','ü').replace('&ouml;','ö')
		#title = title.replace('„','"').replace('“','"')
		title = re.sub('\s+', ' ', title)
		return title.strip()

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

def addLink(name, url, mode, iconimage, fanart=''):
	u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode)
	liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	liz.setProperty('IsPlayable', 'true')
	if useThumbAsFanart: liz.setProperty('fanart_image', fanart)
	return xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz)

def addDir(name, url, mode, iconimage=''):
	#name = '* ' + name
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
elif mode == 'origVideos': origVideos()
elif mode == 'indexPlaylists': indexPlaylists()
elif mode == 'showPlaylists': showPlaylists(url)
elif mode == 'showPlVideos': showPlVideos(url)
else: index()