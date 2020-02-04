#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys, re, xbmcplugin, xbmcgui, xbmcaddon, json
try:
	from urllib.request import urlopen, Request
	from urllib.parse import quote_plus, unquote_plus
except ImportError:
	from urllib2 import urlopen, Request
	from urllib import quote_plus, unquote_plus

dbg = False
pluginhandle = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.bild_de_ll')
#translation = settings.getLocalizedString
forceViewMode = settings.getSetting("forceViewMode") == "true"
useThumbAsFanart = settings.getSetting("useThumbAsFanart") == "true"
filterBildPlus = settings.getSetting("filterBildPlus") == "true"
maxViewPages = int(settings.getSetting("maxViewPages"))*2
if maxViewPages == 0: maxViewPages = 1
viewMode = str(settings.getSetting("viewMode"))
settings = None

base = 'http://www.bild.de'
videodropdown = base + '/navi/-35652780,contentContextId=15799990,view=dropdown.bild.html'
userAgent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0'

def index():
	for k, v in enumerate(getFolders()):
		if v[0] == 0: addDir(cleanTitle(v[2]), base + v[1], 'showVideos', '')
	xbmcplugin.endOfDirectory(pluginhandle)
	if forceViewMode: xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def showVideos(url):
	dprint('open ' + url)
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
	dprint('open URL ' + videodropdown)
	content = getUrl(videodropdown)
	for href, cat in re.compile('<li>[^<]*<a href="(/video[^"]*)"[^<]*>([^<]*)</a>[^<]*</li>', re.DOTALL).findall(content):
		dprint(cat + ' --> ' + href)
		folders.append((0, href, cat))
	return folders

def playVideo(url):
	dprint(url)
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
	title = re.sub(u'<[^>]*>', u' ', title)
	title = re.sub(u'&#\d{3};', u' ', title)
	title = title.replace(u'&lt;',u'<').replace(u'&gt;',u'>').replace(u'&amp;',u'&').replace(u'&quot;',u'"').replace(u'&szlig;',u'ß').replace(u'&ndash;',u'-')
	title = title.replace(u'&Auml;',u'Ä').replace(u'&Uuml;',u'Ü').replace(u'&Ouml;',u'Ö').replace(u'&auml;',u'ä').replace(u'&uuml;',u'ü').replace(u'&ouml;',u'ö').replace(u'&nbsp;', u' ')
	title = title.replace(u'„',u'"').replace(u'“',u'"')
	title = re.sub(u'\s+', u' ', title)
	return title.strip()

def uniq(input):
	output = []
	for x in input:
		if x not in output:
			output.append(x)
	return output

def getUrl(url):
	req = Request(url)
	req.add_header('User-Agent', userAgent)
	req.add_header('Referer', url)
	response = urlopen(req, timeout=30)
	try:
		encoding = response.info().get_param('charset', 'utf8')
	except:
		encoding = 'utf8'
	link = response.read().decode(encoding)
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
	u = sys.argv[0] + "?url=" + quote_plus(url) + "&mode=" + str(mode)
	liz = xbmcgui.ListItem(name)
	liz.setArt({'icon': "DefaultVideo.png", 'thumb': iconimage})
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	liz.setProperty('IsPlayable', 'true')
	if useThumbAsFanart: liz.setArt({'fanart': fanart})
	if duration>0: liz.setInfo('video', { 'duration' : duration })
	return xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz)

def addDir(name, url, mode, iconimage):
	u = sys.argv[0] + "?url=" + quote_plus(url) + "&mode=" + str(mode)
	liz = xbmcgui.ListItem(name)
	liz.setArt({'icon': "DefaultVideo.png", 'thumb': iconimage})
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	return xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz, isFolder=True)

def dprint(*args):
	if dbg: 
		for s in list(args):
			print('bild.de: ' + s)
			
params = parameters_string_to_dict(sys.argv[2])
mode = params.get('mode')
url = params.get('url')

if type(url) == type(str()): url = unquote_plus(url)

if mode == 'showVideos': showVideos(url)
elif mode == 'playVideo': playVideo(url)
else: index()