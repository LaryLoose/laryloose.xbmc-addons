#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys, urllib, urllib2, re, xbmcplugin, xbmcgui, xbmcaddon, json

dbg = False
pluginhandle = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.bild_de_ll')
translation = settings.getLocalizedString
forceViewMode = settings.getSetting("forceViewMode") == "true"
useThumbAsFanart = settings.getSetting("useThumbAsFanart") == "true"
filterBildPlus = settings.getSetting("filterBildPlus") == "true"
maxViewPages = int(settings.getSetting("maxViewPages"))*2
if maxViewPages == 0: maxViewPages = 1
viewMode = str(settings.getSetting("viewMode"))

base = 'http://www.bild.de'
videodropdown = base + '/navi/-35652780,contentContextId=15799990,view=dropdown.bild.html'

def index():
	for k, v in enumerate(getFolders()):
		if v[0] == 0: addDir(cleanTitle(v[2]), base + v[1], 'showVideos', '')
	xbmcplugin.endOfDirectory(pluginhandle)
	if forceViewMode: xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def showVideos(url):
	if dbg: print 'open ' + url
	content = getUrl(url)
	for d in re.compile('<div[^>]*class="module[^"]*"[^>]*>(.*?)<[^>]*class="socialbar"', re.DOTALL).findall(content):
		for url,thumb,kicker,headline,duration in re.compile('data-video-json="([^"]+)".*<[^>]*class="photo ondemand"[^>]*data-src="([^"]+)"[^>]*>.*<[^>]*class="kicker"[^>]*>([^<]*)</[^>]*>.*<[^>]*class="headline"[^>]*>([^<]*)<.*<[^>]*class="index"[^>]*>([^<]*)<', re.DOTALL).findall(d):
			if filterBildPlus and '/bild-plus/' in url: continue
			addLink(colorize(cleanTitle(kicker),'white') + ' - ' + cleanTitle(headline), base + url, 'playVideo', thumb, thumb, strToSeconds(duration))
	xbmcplugin.endOfDirectory(pluginhandle)
	if forceViewMode:
	    xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def strToSeconds(str):
	for m,s in re.compile('([\d]+):([\d]+) Min.', re.I).findall(str):
		return int(m)*60+int(s)
	return 0

def colorize(str, color):
	return '[COLOR='+color+']'+str+'[/COLOR]'
	
def getFolders():
	folders = []
	if dbg: print 'open URL ' + videodropdown
	content = getUrl(videodropdown)
	for href, cat in re.compile('<li>[^<]*<a href="(/video[^"]*)"[^<]*>([^<]*)</a>[^<]*</li>', re.DOTALL).findall(content):
		if dbg: print cat + ' --> ' + href
		folders.append((0, href, cat))
	return folders

def playVideo(url):
	if dbg: print url
	parsed = json.loads(getUrl(url))
	match = None
	for clip in parsed['clipList']:
		for src in clip.get('srces'):
			if not match: match = src.get('src')
	if match:
		listitem = xbmcgui.ListItem(path=match)
		return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
	else:
		xbmc.executebuiltin('Notification(Video wurde nicht gefunden., 5000)')

def cleanTitle(title):
	title = re.sub('<[^>]*>', ' ', title)
	title = re.sub('&#\d{3};', ' ', title)
	title = title.replace('&lt;','<').replace('&gt;','>').replace('&amp;','&').replace('&quot;','"').replace('&szlig;','ß').replace('&ndash;','-')
	title = title.replace('&Auml;','Ä').replace('&Uuml;','Ü').replace('&Ouml;','Ö').replace('&auml;','ä').replace('&uuml;','ü').replace('&ouml;','ö').replace('&nbsp;', ' ')
	title = title.replace('„','"').replace('“','"')
	title = re.sub('\s+', ' ', title)
	return title.strip()

def uniq(input):
	output = []
	for x in input:
		if x not in output:
			output.append(x)
	return output

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

def addLink(name, url, mode, iconimage, fanart, duration):
	u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode)
	liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	liz.setProperty('IsPlayable', 'true')
	if useThumbAsFanart: liz.setProperty('fanart_image', fanart)
	if duration>0: liz.setInfo('video', { 'duration' : duration })
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
else: index()