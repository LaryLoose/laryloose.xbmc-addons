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
dbg = True

def CATEGORIES(idx):
	INDEX(baseurl+'/load/?page1')	
#	data = getUrl(baseurl+'/load')
#	addDir('Neue Filme', baseurl+'/load/?page1', 1, '', True)
#	#addDir('Update 100', baseurl+'/index/top_filme/0-30', 1, '', True)
#	#addDir('Update 200', baseurl+'/index/update_200/0-44', 1, '', True)
#	#addDir('Serien', baseurl, 0, '', True)
#	for cats in re.findall('<table[^>]*class="catsTable"[^>]*>(.*?)</table>', data, re.S|re.I|re.DOTALL):
#		for url, name in re.findall('<a[^>]*href="([^"]+)"[^>]*class="catName"[^>]*>([^<]*)</a>', cats, re.S|re.I|re.DOTALL):
#			if re.match('Suche|DVD.*s|Neue Film-Update.*s|Wunschfilm|Filme 2.*|Filme Ab 18', name, re.S|re.I): continue
#			if 'http:' not in url: url =  baseurl + url
#			addDir(name, url, 1, '', True)
#	#xbmc.executebuiltin("Container.SetViewMode(400)")

def INDEX(url):
	global itemcnt
	if dbg: print url
	data = getUrl(url)
	for (title, url, image) in re.findall('<div[^>]*class="grid"[^>]*>.*?<a[^>]*>[^<]*<span[^>]*>([^<]*)<.*?<div class="grid-col">[^<]*<a href="([^"]*)"[^>]*>[^<]*<img[^>]*src="([^"]*)"[^>]*>', data, re.I|re.S|re.DOTALL):
		if 'http' not in url: url =  baseurl + url
		if 'http' not in image: image =  baseurl + image
		addLink(clean(title), url, 10, image)
		itemcnt = itemcnt + 1
	nextPage = re.findall('<a[^>]*class="swchItem"[^>]*href="([^"]+)"[^>]*><span>&raquo;</span>', data, re.S)
	if nextPage:
		if 'http' not in nextPage[0]: nextPage[0] =  baseurl + nextPage[0]
		if itemcnt >= maxitems: addDir('Weiter >>', nextPage[0], 1, '',  True)
		else: INDEX(nextPage[0])
	if forceMovieViewMode: xbmc.executebuiltin("Container.SetViewMode(" + movieViewMode + ")")

def selectVideoDialog(videos):
	titles = []
	for name, src in videos:
		titles.append(name)
	idx = xbmcgui.Dialog().select("", titles)
	return videos[idx][1]

def PLAYVIDEO(url):
	if dbg: print url
	data = getUrl(url)
	if not data: return
	videos = []
	for (hoster, stream) in re.findall('<object[^>]*data="([^"]*)/[^"]*"[^>]*>.*?<param[^>]*value="flv=([^"&;]*)', data, re.S|re.I|re.DOTALL):
		host = get_stream_link().get_hostername(cleanUrl(stream))
		if dbg: print 'hoster: ' + hoster
		if dbg: print 'stream: ' + cleanUrl(stream)
		videos += [(hoster, stream)]
	for stream in re.findall('freevideocoding\.com.flvplayer\.swf\?file=([^>"\'&]*)["&\']', data, re.S|re.I|re.DOTALL):
		videos += [('freevideocoding', cleanUrl(stream))]
	for stream in re.findall('<iframe[^>"]*src="([^"]*)"', data, re.S|re.I|re.DOTALL):
		stream = cleanUrl(stream)
		hoster = get_stream_link().get_hostername(stream)
		if hoster == 'Not Supported': continue
		videos += [(hoster, stream)]
	lv = len(videos)
	if lv == 0:
		xbmc.executebuiltin("XBMC.Notification(Fehler!, Video nicht gefunden, 4000)")
		return
	url = selectVideoDialog(videos) if lv > 1 else videos[0][1]
	stream_url = GetStream(url)
	if stream_url:
		print 'open stream: ' + stream_url
		listitem = xbmcgui.ListItem(path=stream_url)
		return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def GetStream(url):
	if 'kinoxx.org' in url: return url
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
		return stream_url

def cleanUrl(s):
	try: s = htmlparser.unescape(s)
	except: print "could not unescape string '%s'"%(s)
	s = urllib2.unquote(s)
	if 'http' in s:
	    s = re.sub('http.*?//','',s)
	    s = 'http://' + urllib2.quote(s)
	return s.strip('\n').strip()

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

def getUrl(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	data=response.read()
	response.close()
	return data#.decode('utf-8')

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
	return xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz)

def addDir(name, url, mode, image, is_folder=False):
	u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&image="+urllib.quote_plus(image)
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

if mode==None or url==None or len(url)<1: CATEGORIES(0)
elif mode==0: CATEGORIES(1)
elif mode==1: INDEX(url)
elif mode==10: PLAYVIDEO(url)

xbmcplugin.endOfDirectory(pluginhandle)