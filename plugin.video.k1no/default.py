#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcaddon,xbmcplugin,xbmcgui,xbmc,HTMLParser
from stream import *

htmlparser = HTMLParser.HTMLParser()
pluginhandle = int(sys.argv[1])
itemcnt = 0
baseurl = 'http://k1no.do.am'
settings = xbmcaddon.Addon(id='plugin.video.k1no')
maxitems = (int(settings.getSetting("items_per_page"))+1)*10
filterUnknownHoster = settings.getSetting("filterUnknownHoster") == 'true'
forceMovieViewMode = settings.getSetting("forceMovieViewMode") == 'true'
movieViewMode = str(settings.getSetting("movieViewMode"))
dbg = False

def CATEGORIES(idx):
	data = getUrl(baseurl)
	cats = re.findall('<a[^>]*class="load"[^>]*>(.*?)</ul>', data, re.S|re.I|re.DOTALL)
	cats = re.findall('<li[^>]*>.*?<a[^>]*href="([^"]*?)"[^>]*?>([^<]*?)</a>', cats[idx], re.S|re.I|re.DOTALL)
	if (idx == 0):
		addDir('Letzten 30 Filme', baseurl, 4, '', True)
		#addDir('Serien', baseurl, 0, '', True)
	for (url, name) in cats:
	    if 'http:' not in url: url =  baseurl + url
	    addDir(name, url, 1, '', True)
	xbmc.executebuiltin("Container.SetViewMode(400)")

def UPDATES(url):
	print url
	data = getUrl(url)
	updhtm = re.findall('30lastmovies.png(.*?)"jv-content-inner"', data, re.I|re.S|re.DOTALL)
	movies = re.findall('<a[^>]*>([^<]*)</a>.*?<a href="([^"]*)"><img src="([^"]*)".*?<a', updhtm[0], re.I|re.S|re.DOTALL)
	if movies:
		for (title, url, image) in movies:
			if 'http:' not in url: url =  baseurl + url
			addDir(clean(title), url, 2, image, True)
	if forceMovieViewMode: xbmc.executebuiltin("Container.SetViewMode(" + movieViewMode + ")")


def INDEX(url):
	global itemcnt
	nextPageUrl = re.sub('-[\d]+$', '', url)
	print url
	data = getUrl(url)
	updates = re.findall('', data, re.I|re.S|re.DOTALL)
	movies = re.findall('<div[^>]*class="grid"[^>]*>.*?<a[^>]*>[^<]*<span[^>]*>([^<]*)<.*?<div class="grid-col">[^<]*<a href="([^"]*)"[^>]*>[^<]*<img[^>]*src="([^"]*)"[^>]*>', data, re.I|re.S|re.DOTALL)
	if movies:
		for (title, url, image) in movies:
			if 'http:' not in url: url =  baseurl + url
			addDir(clean(title), url, 2, image, True)
			itemcnt = itemcnt + 1
	nextPage = re.findall('<a class="swchItem"[^>]*? onclick="spages\(\'(\d+)\'[^>]*?"><span>&raquo;</span></a>', data, re.S)
	if nextPage:
		if itemcnt >= maxitems:
		    addDir('Weiter >>', nextPageUrl + '-' + nextPage[0], 1, '',  True)
		else:
		    INDEX(nextPageUrl + '-' + nextPage[0])
	if forceMovieViewMode: xbmc.executebuiltin("Container.SetViewMode(" + movieViewMode + ")")

def VIDEOLINKS(url, image):
	print url
	data = getUrl(url)
	streams = []
	objects = re.findall('<span[^>]*style="color[^>]*><div[^>]*>[^<]*<b>([^<]*)</b>[^<]*</div>[^<]*</span>[^<]*<div[^>]*><object[^>]*>(.*?)</object>', data, re.S|re.I|re.DOTALL)
	if objects: 
		for name, obj in objects:
			file = re.findall('<param[^>]*name="flashvars"[^>]*value="[^"]*file=([^"]*?)&amp;[^"]*"', obj, re.S|re.I|re.DOTALL)
			if file: streams += [(name, urllib.unquote_plus(file[0]))]
	streams += re.findall('<span[^>]*style="color[^>]*>[^<]*<div[^>]*>[^<]*<b>([^<]*)</b>[^<]*</div>[^<]*</span>[^<]*<div[^>]*>[^<]*<iframe[^>]*src="([^"]*)"[^>]*>[^<]*</iframe>', data, re.S|re.I|re.DOTALL)
	streams += re.findall('<span[^>]*style="color[^>]*><div[^>]*>[^<]*<b>([^<]*)</b>[^<]*</div>[^<]*</span>[^<]*<div[^>]*><a[^>]*href="([^"]*)"', data, re.S|re.I|re.DOTALL)
	if streams:
		for (filename, stream) in streams:
			if 'adf.ly' in stream:
				print 'resolving adfly url: ' + stream
				stream = get_stream_link().get_adfly_link(stream)
			hoster = get_stream_link().get_hostername(stream)
			if filterUnknownHoster and hoster == 'Not Supported': continue
			entry = '[COLOR=blue](' + hoster + ')[/COLOR] ' + filename
			addLink(entry, htmlparser.unescape(stream), 3, image)

def clean(s):
	s = htmlparser.unescape(s)
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
	if stream_url is None:
		xbmc.executebuiltin("XBMC.Notification(Fehler!, Resolver liefert leeres Ergebnis, 4000)")
	elif re.match('.*not.*supported', stream_url, re.S|re.I):
		xbmc.executebuiltin("XBMC.Notification(Fehler!, Hoster nicht unterstützt, 4000)")
	elif re.match('^Error: ', stream_url, re.S|re.I):
		xbmc.executebuiltin("XBMC.Notification(Fehler!, " + re.sub('^Error: ','',stream_url) + ", 4000)")
	else:
		req = urllib2.Request(stream_url)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		stream_url = response.geturl()
		response.close()
		print 'open stream: ' + stream_url
		listitem = xbmcgui.ListItem(path=stream_url)
		return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def getUrl(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	data=response.read()
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

if mode==None or url==None or len(url)<1: CATEGORIES(0)
elif mode==0: CATEGORIES(1)
elif mode==1: INDEX(url)
elif mode==2: VIDEOLINKS(url, image)
elif mode==3: GETLINK(url)
elif mode==4: UPDATES(url)

xbmcplugin.endOfDirectory(int(sys.argv[1]))