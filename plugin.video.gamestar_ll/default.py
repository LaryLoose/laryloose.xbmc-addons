#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcaddon,xbmcplugin,xbmcgui,xbmc,HTMLParser

htmlparser = HTMLParser.HTMLParser()
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

premiumrex = re.compile('^Die Redaktion|^Raumschiff GameStar|^GameStar TV', re.I)

premium = False
dbg = False

def CATEGORIES():
	if dbg: print channelurl
	data = getUrl(channelurl)
	#print data
	list = {}
	rex = re.compile('<a[^>]*href="([^"]*)"[^>]*title="([^"]*)"[^>]*>[^<]*<img[^>]*>[^<]*<noscript>[^<]*<img[^>]*src="([^"]*)"', re.S|re.I)
	for url, title, img in rex.findall(data):
		if not premium and premiumrex.match(title): continue
		if 'http' not in url: url = baseurl + url
		if 'http' not in img: img = 'http:' + img
		if title in list: continue
		list[title] = ''
		if dbg: print url, title, img
		addDir(colortitle(title, 'blue'), url, 1, renamepic(img), True)
	xbmc.executebuiltin("Container.SetViewMode(400)")

def INDEX(url):
	if dbg: print url
	global itemcnt
	data = getUrl(url)
	#print data
	rex = re.compile('<a[^>]*href="([^"]*)"[^>]*title="([^"]*)"[^>]*>[^<]*<img[^>]*>[^<]*<noscript>[^<]*<img[^>]*src="([^"]*)"', re.S|re.I)
	for url, title, img in rex.findall(data):
		if not premium and premiumrex.match(title): continue 
		if 'http' not in url: url =  baseurl + url
		if 'http' not in img: img = 'http:' + img
		title = clean(filter(title))
		if dbg: print url, img, title
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
	if dbg: print url
	for mediaid in re.findall(',([\d]*?)\.htm', url, re.S): 
		url = getvideourl + mediaid
		if dbg:
		    print 'mediaid: ' + mediaid
		    print 'open stream: ' + url
		listitem = xbmcgui.ListItem(path=url)
		return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)		
			
def colortitle(s, color):
	return re.sub(r'(^.*?(?: -|:))', r'[COLOR=blue]\g<1>[/COLOR]', s)

def clean(s):
	try: s = htmlparser.unescape(s)
	except: print "could not unescape string '%s'"%(s)
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
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	data = response.read()
	response.close()
	return data

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

def addLink(name, url, mode, image, fanart):
	u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode)
	liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=image)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	liz.setProperty('IsPlayable', 'true')
	if useThumbAsFanart: liz.setProperty('fanart_image', fanart)
	return xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz)

def addDir(name, url, mode, image, is_folder=False):
	u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&image=" + urllib.quote_plus(image)
	liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=image)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	return xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz, isFolder=is_folder)

params = get_params()
url = mode = image = None

try: url = urllib.unquote_plus(params["url"])
except: pass
try: mode = int(params["mode"])
except: pass
try: image = urllib.unquote_plus(params["image"])
except: pass

if mode==None or url==None or len(url)<1: CATEGORIES()
elif mode==1: INDEX(url)
elif mode==2: PLAYLINK(url)

xbmcplugin.endOfDirectory(pluginhandle)
