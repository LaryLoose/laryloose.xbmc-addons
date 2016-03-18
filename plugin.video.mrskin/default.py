#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys, urllib, urllib2, re, xbmcplugin, xbmcgui, xbmcaddon

#dbg = False 
dbg = True
pluginhandle = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.mrskin')
translation = settings.getLocalizedString
forceViewMode = settings.getSetting("forceViewMode") == "true"
useThumbAsFanart = settings.getSetting("useThumbAsFanart") == "true"
maxViewPages = int(settings.getSetting("maxViewPages"))*2
if maxViewPages == 0: maxViewPages = 1
viewMode = str(settings.getSetting("viewMode"))

startpage = 'http://www.mrskin.com'
playlisturl = 'http://www.mrskin.com/playlist/<pid>.xml'
contrex = ['"file":"([^"]+-hd[^"]*)"', '"file":"([^"]+-sd[^"]*)"', '"file":"([^"]+)"']
userAgent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0'

def index():
	addDir('Original Videos', '', 'origVideos', '')
	addDir('Playlists', '', 'indexPlaylists', '')
	xbmcplugin.endOfDirectory(pluginhandle)
	
def indexPlaylists():
	url = startpage + '/playlists'
	if dbg: print 'open ' + url
	content = getUrl(url)
	addDir('Last Updates', url, 'showPlaylists')
	for href, cat in re.compile('<a[^>]*class=\'filter-link\'[^>]*href=\'([^\']+)\'[^>]*>[^<]*<span[^>]*class=\'category\'[^>]*>([^<]*)</span>', re.DOTALL).findall(content):
		cat = cleanTitle(cat)
		if 'http' not in href: href = startpage + href
		if dbg: print cat, href
		addDir(cat, href, 'showPlaylists')
	xbmcplugin.endOfDirectory(pluginhandle)

def showPlaylists(url):
	if dbg: print 'open ' + url
	content = getUrl(url)
	for href, img, title in re.compile('<a[^>]*href="([^"]+)">[^<]*<img[^>]*class="img-responsive"[^>]*src="([^"]*)"[^>]*>.*?<[^>]*class=["\']title["\'][^>]*>([^<]+)<', re.DOTALL).findall(content):
		href = startpage + href
		title = cleanTitle(title)
		if dbg: print 'add link: title=' + title + ' href=' +href + ' img=' + img
		addDir(title, href, 'showPlVideos', img)
	for nextpage in  re.compile('<span[^>]*class=\'next\'>[^<]*<a[^>]*rel="next"[^>]*href="([^"]+)"[^>]*>', re.DOTALL).findall(content):
		nextpage = startpage + nextpage
		if dbg: print 'next page ' + nextpage
		addDir('Next Page', nextpage, 'showPlaylists')
	xbmcplugin.endOfDirectory(pluginhandle)
	if forceViewMode: xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')	

def showPlVideos(url):
	if dbg: print 'parsing ' + url
	url = playlisturl.replace('<pid>', find('p([0-9]+)$', url))
	if dbg: print 'open ' + url
	content = getUrl(url)
	print content
	for item in re.compile('<item>(.*?)</item>', re.DOTALL).findall(content):
		bitrate = 0
		title = cleanTitle(find('<title>([^<]*)</title>', item))
		img = find('<jwplayer:thumbnail>([^<]*)</jwplayer:thumbnail>', item)
		for ibrate, ihref in re.compile('<media:content bitrate="([0-9]+)" url="([^"]+)"', re.I).findall(item):
			#print ibrate, ihref
			if int(ibrate) > bitrate: 
				bitrate = int(ibrate)
				href = ihref
		if 'http' not in href: href = startpage + href 
		if dbg: print title + ' --> ' + href + ' --> ' + img
		addLink(title, href, 'playVideo', img)
	xbmcplugin.endOfDirectory(pluginhandle)
	if forceViewMode: xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')
	
def origVideos():
	url = startpage + '/video'
	if dbg: print 'open ' + url
	content = getUrl(url)
	addDir('Last Updates', url, 'showVideos')
	for href, cat in re.compile('<a[^>]*class=\'filter-link\'[^>]*href=\'([^\']+)\'[^>]*>[^<]*<span[^>]*class=\'category\'[^>]*>([^<]*)</span>', re.DOTALL).findall(content):
		cat = cleanTitle(cat)
		if 'http' not in href: href = startpage + href
		if dbg: print cat, href
		addDir(cat, href, 'showVideos')
	xbmcplugin.endOfDirectory(pluginhandle)
	if forceViewMode: xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def showVideos(url):
	if dbg: print 'open ' + url
	content = getUrl(url)
	for href, img, title in re.compile('<a[^>]*href="([^"]+)">[^<]*<img[^>]*class="img-responsive"[^>]*src="([^"]*)"[^>]*>.*?<[^>]*class=["\']title["\'][^>]*>([^<]+)<', re.DOTALL).findall(content):
		href = startpage + href
		title = cleanTitle(title)
		if dbg: print 'add link: title=' + title + ' href=' +href + ' img=' + img
		addLink(title, href, 'playVideo', img)
	for nextpage in  re.compile('<span[^>]*class=\'next\'>[^<]*<a[^>]*rel="next"[^>]*href="([^"]+)"[^>]*>', re.DOTALL).findall(content):
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
	if '.mp4' in url:
		video = url
	else:
		content = getUrl(url)
		video = getVideoUrl(content)
	if video:
		video = video + '|User-Agent=' + userAgent + '&Referer=' + startpage
		listitem = xbmcgui.ListItem(path=video.replace('\\', ''))
		return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
	else:
	    xbmc.executebuiltin('Notification(Video not found., 5000)')

def cleanTitle(title):
	title = title.replace('&lt;','<').replace('&gt;','>').replace('&amp;','&').replace('&quot;','"').replace('&szlig;','ß').replace('&ndash;','-').replace('&nbsp;', ' ')
	title = re.sub('\s+', ' ', title)
	return title.strip()

def getUrl(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', userAgent)
	req.add_header('Referer', url)
	response = urllib2.urlopen(req, timeout=30)
	link = response.read()
	response.close()
	return link

def find(rex, string):
	match = re.search(rex, string, re.S|re.I|re.DOTALL)
	if match: return match.group(1)
	else: return ''

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