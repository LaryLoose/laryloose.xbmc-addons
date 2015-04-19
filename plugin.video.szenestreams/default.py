#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcaddon,xbmcplugin,xbmcgui,xbmc,HTMLParser
from stream import *

htmlparser = HTMLParser.HTMLParser()
pluginhandle = int(sys.argv[1])
itemcnt = 0
baseurl = 'http://www.szene-streams.com'
settings = xbmcaddon.Addon(id='plugin.video.szene-streams')
maxitems = (int(settings.getSetting("items_per_page"))+1)*10
filterUnknownHoster = settings.getSetting("filterUnknownHoster") == 'true'
forceMovieViewMode = settings.getSetting("forceMovieViewMode") == 'true'
movieViewMode = str(settings.getSetting("movieViewMode"))
dbg = False

def CATEGORIES():
	data = getUrl(baseurl)
	cats = re.findall('<a[^>]*?class="CatInf"[^>]*?href="(.*?)"[^>]*?>.*?<div class="CatNumInf">(.*?)</div>[^<]*?<div[^>]*?class="CatNameInf">(.*?)</div>', data, re.S|re.I)
	addDir('Letzte Updates', baseurl, 1, '', True)
	addDir('Suche...', baseurl + '/publ', 4, '', True)
	addDir('Serien', baseurl + '/load', 0, '', True)
	for (url, num, name) in cats:
	    if 'http:' not in url: url =  baseurl + url
	    addDir(name + '  [COLOR=blue](' + num + ')[/COLOR]', url, 1, '', True)
	xbmc.executebuiltin("Container.SetViewMode(400)")

def SERIES(url):
	data = getUrl(url)
	cats = re.findall('<a[^>]*?class="CatInf"[^>]*?href="(.*?)"[^>]*?>.*?<div class="CatNumInf">(.*?)</div>[^<]*?<div[^>]*?class="CatNameInf">(.*?)</div>', data, re.S|re.I)
	addDir('Letzte Updates', baseurl + '/load/0-1', 1, '', True)
	for (url, num, name) in cats:
	    if 'http:' not in url: url =  baseurl + url
	    addDir(name + '  [COLOR=blue](' + num + ')[/COLOR]', url, 1, '', True)
	xbmc.executebuiltin("Container.SetViewMode(400)")

def INDEX(url, search=None):
	global itemcnt
	nextPageUrl = re.sub('-[\d]+$', '', url)
	print url
	data = getUrl(url, search)
	movies = re.findall('<div class="ImgWrapNews">[^<]*<a[^<]*<img[^>]*src="([^"]*.[jpg|png])"[^>]*alt="([^"]*)"[^>]*>.*?class="[^"]*entryLink[^"]*".*?href="([^"]*)"', data, re.S|re.I)
	if movies:
		for (image, title, url) in movies:
			if 'http:' not in url: url =  baseurl + url
			addDir(clean(title), url, 2, image, True)
			itemcnt = itemcnt + 1                                       
	nextPage = re.findall('<a class="swchItem"[^>]*onclick="spages\(\'(\d+)\'[^>]*?"[^>]*><span>&raquo;</span>', data, re.S)
	if nextPage:
		if itemcnt >= maxitems:
		    addDir('Weiter >>', nextPageUrl + '-' + nextPage[0], 1, '',  True)
		else:
		    INDEX(nextPageUrl + '-' + nextPage[0])
	if forceMovieViewMode: xbmc.executebuiltin("Container.SetViewMode(" + movieViewMode + ")")

def VIDEOLINKS(url, image):
	data = getUrl(url)
	streams = []
	raw = re.findall('(<fieldset[^>]*>[^<]*<legend>.*?</fieldset>)', data, re.S)
	if raw:
		for each in raw:
			series = re.findall('<div class="spoiler"><font[^>]*><b[^>]*>(.+?)</b>(.*?)<input', each, re.S|re.I)
			if not series: series = re.findall('<legend>(.+?)</legend>[^<]*<div class="spoiler">(.*?)<input', each, re.S|re.I)
			if not series: series = re.findall('<legend>(.+?)</legend>.*?(<iframe.*?</iframe>|<a[^>]*href=".+"[^>]*>).*', each, re.S|re.I)
			if series:
				for ser in series:
					for (s, n) in re.findall('<a[^>]*href="([^"]+)"[^>]*>([^<]*)<', each, re.S|re.I):
						if dbg: print 'ser1'
						if ser: n = clean(ser[1]) + ' ' + extractFilename(s)
						n = clean(n) if n else extractFilename(s)
						if n: streams += [(n, s)]
					for s in re.findall('<iframe[^>]*src="([^"]*)"[^>]*>', each, re.S|re.I):
						if dbg: print 'ser2'
						if ser: n = clean(ser[1])  
						if not n: n = 'unknown'
						if n: streams += [(n, s)]
			elif re.match('.*?iframe.*?src.*', each, re.S|re.I):
				if dbg: print 'nonser1'
				streams += re.findall('<font[^>]*>.*?src=".*?/player/(.*?)\..{3}".*?<iframe.*?src=["|\'](.*?)["|\']', each, re.S|re.I)
			else:
				if dbg: print 'nonser2'
				streams += re.findall('<font[^>]*>.*?src=".*?/player/(.*?)\..{3}".*?</font>.*?target="_blank" href=["|\'](.*?)["|\']', each, re.S|re.I)
	if streams:
		for (filename, stream) in streams:
			hoster = get_stream_link().get_hostername(stream)
			if filterUnknownHoster and hoster == 'Not Supported': continue
			entry = '[COLOR=blue](' + hoster + ')[/COLOR] ' + filename
			addLink(entry, clean(stream), 3, image)

def SEARCH(url):
    keyboard = xbmc.Keyboard('', 'Suche')
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText()
        INDEX(url, search_string)

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

def extractFilename(path):
    path = re.sub('^.*/', '',clean(path)).replace('.html', '').replace('_', ' ')
    return re.sub('\.[a-zA-Z]{3}', '', path)

def GETLINK(url):
	stream_url = get_stream_link().get_stream(url)
	if stream_url:
		if re.match('^Error: ', stream_url, re.S|re.I):
			xbmc.executebuiltin("XBMC.Notification(Fehler!, " + re.sub('^Error: ','',stream_url) + ", 4000)")
		else:
			listitem = xbmcgui.ListItem(path=stream_url)
			return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def getUrl(url, query=None):
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	print query
	if query:	
		values = { 'query' : query, 'a' : '2' }
		response = urllib2.urlopen(req, urllib.urlencode(values))
	else:
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

def addLink(name, url, mode, image):
	u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
	liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=image)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	liz.setProperty('IsPlayable', 'true')
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)

def addDir(name, url, mode, image, is_folder=False):
	u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&image="+urllib.quote_plus(image)
	liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=image)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=is_folder)

params = get_params()
url = mode = image = None

try: url = urllib.unquote_plus(params["url"])
except: pass
try: mode = int(params["mode"])
except: pass
try: image = urllib.unquote_plus(params["image"])
except: pass

if mode==None or url==None or len(url)<1: CATEGORIES()
elif mode==0: SERIES(url)
elif mode==1: INDEX(url)
elif mode==2: VIDEOLINKS(url, image)
elif mode==3: GETLINK(url)
elif mode==4: SEARCH(url)

xbmcplugin.endOfDirectory(int(sys.argv[1]))