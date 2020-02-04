#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys, re, xbmcplugin, xbmcgui, xbmcaddon
try:
	from urllib.request import urlopen, Request
	from urllib.parse import quote_plus, unquote_plus
	from html.parser import HTMLParser
except ImportError:
	from urllib2 import urlopen, Request
	from urllib import quote_plus, unquote_plus
	from HTMLParser import HTMLParser

htmlparser = HTMLParser()
pluginhandle = int(sys.argv[1])
itemcnt = 0
baseurl = 'http://www.gamestar.de'
channelurl = 'http://www.gamestar.de/videos/video-kanaele/'
getvideourl = 'http://www.gamestar.de/_misc/videos/portal/getVideoUrl.cfm?premium=1&videoId='
settings = xbmcaddon.Addon(id='plugin.video.gamestar_ll')
maxitems = (int(settings.getSetting("items_per_page"))+1)*10
forceMovieViewMode = settings.getSetting("forceMovieViewMode") == 'true'
useThumbAsFanart = settings.getSetting("useThumbAsFanart") == 'true'
hirespix = settings.getSetting("useHighresPix") == 'true'
movieViewMode = str(settings.getSetting("movieViewMode"))
settings = None

premiumrex = re.compile('^Die Redaktion|^Raumschiff GameStar|^GameStar TV', re.I)
userAgent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0'

premium = False
dbg = False

def CATEGORIES():
	dprint(channelurl)
	data = getUrl(channelurl)
	#dprint(data)
	list = {}
	rex = re.compile('<a[^>]*href="([^"]*)"[^>]*title="([^"]*)"[^>]*>[^<]*<img[^>]*>[^<]*<noscript>[^<]*<img[^>]*src="([^"]*)"', re.S|re.I)
	for url, title, img in rex.findall(data):
		if not premium and premiumrex.match(title): continue
		if 'http' not in url: url = baseurl + url
		if 'http' not in img: img = 'http:' + img
		if title in list: continue
		list[title] = ''
		dprint(url, title, img)
		addDir(colortitle(title, 'blue'), url, 1, renamepic(img), True)
	xbmc.executebuiltin("Container.SetViewMode(400)")

def INDEX(url):
	dprint(url)
	global itemcnt
	data = getUrl(url)
	#dprint(data)
	rex = re.compile('<a[^>]*href="([^"]*)"[^>]*title="([^"]*)"[^>]*>[^<]*<img[^>]*>[^<]*<noscript>[^<]*<img[^>]*src="([^"]*)"', re.S|re.I)
	for url, title, img in rex.findall(data):
		if not premium and premiumrex.match(title): continue 
		if 'http' not in url: url =  baseurl + url
		if 'http' not in img: img = 'http:' + img
		title = clean(filter(title))
		dprint(url, img, title)
		addLink(colortitle(title, 'blue'), url, 2, renamepic(img), renamepic(img, True))
		itemcnt = itemcnt + 1
	nextPage = re.findall('<a[^>]*href="([^"]*)"[^>]*>mehr anzeigen', data, re.S)
	if nextPage:
		url = nextPage[0]
		if 'http' not in url: url =  baseurl + url
		if itemcnt >= maxitems: addDir('Weiter >>', url, 1, '',  True)
		else: INDEX(url)
	if forceMovieViewMode: xbmc.executebuiltin("Container.SetViewMode(" + movieViewMode + ")")

def PLAYLINK(url):
	dprint(url)
	for mediaid in re.findall(',([\d]*?)\.htm', url, re.S): 
		url = getvideourl + mediaid
		dprint('mediaid: ' + mediaid, 'open stream: ' + url)
		listitem = xbmcgui.ListItem(path=url)
		return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)		
			
def colortitle(s, color):
	return re.sub(r'(^.*?(?: -|:))', r'[COLOR=blue]\g<1>[/COLOR]', s)

def clean(s):
	try: s = htmlparser.unescape(s)
	except: dprint("could not unescape string '%s'"%(s))
	s = re.sub('<[^>]*>', '', s)
	s = s.replace('_', ' ')
	s = re.sub('[ ]+', ' ', s)
	for hit in set(re.findall("&#\d+;", s)):
		try: s = s.replace(hit, unichr(int(hit[2:-1])))
		except ValueError: pass
	return s.strip('\n').strip()

def renamepic(p, fanart=False):
	if not p: return p
	if fanart: p = re.sub('b144x81', 'pic', p)
	if hirespix: p = re.sub('b144x81', '450x', p)
	return p

def filter(s):
	return re.sub('^Video: ', '', s)

def getUrl(url):
	req = Request(url)
	req.add_header('User-Agent', userAgent)
	req.add_header('Referer', url)
	response = urlopen(req, timeout=30)
	link = response.read().decode('utf8')
	response.close()
	return link

def get_params():
	param=[]
	paramstring=sys.argv[2]
	if len(paramstring)>=2:
		params=sys.argv[2]
		cleanedparams=params.replace('?','')
		if (params[len(params)-1]=='/'):
			params=params[0:len(params)-2]
		pairsofparams=cleanedparams.split('&')
		param={}
		for i in range(len(pairsofparams)):
			splitparams={}
			splitparams=pairsofparams[i].split('=')
			if (len(splitparams))==2:
				param[splitparams[0]]=splitparams[1]
	return param

def addLink(name, url, mode, iconimage, fanart, duration=0):
	u = sys.argv[0] + "?url=" + quote_plus(url) + "&mode=" + str(mode)
	liz = xbmcgui.ListItem(name)
	liz.setArt({'icon': "DefaultVideo.png", 'thumb': iconimage})
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	liz.setProperty('IsPlayable', 'true')
	if useThumbAsFanart: liz.setArt({'fanart': fanart})
	if duration>0: liz.setInfo('video', { 'duration' : duration })
	return xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz)

def addDir(name, url, mode, iconimage, is_folder=False):
	u = sys.argv[0] + "?url=" + quote_plus(url) + "&mode=" + str(mode)
	dprint(name)
	liz = xbmcgui.ListItem(name)
	liz.setArt({'icon': "DefaultFolder.png", 'thumb': iconimage})
	liz.setInfo(type="Picture", infoLabels={ "Title": name } )
	return xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz, isFolder=is_folder)

def dprint(*args):
	if dbg: 
		for s in list(args):
			print('gamestar.de: ' + s)

params = get_params()
url = mode = image = None

try: url = unquote_plus(params["url"])
except: pass
try: mode = int(params["mode"])
except: pass
try: image = unquote_plus(params["image"])
except: pass

if mode==None or url==None or len(url)<1: CATEGORIES()
elif mode==1: INDEX(url)
elif mode==2: PLAYLINK(url)

xbmcplugin.endOfDirectory(pluginhandle)
