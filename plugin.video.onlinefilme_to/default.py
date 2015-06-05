#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib, urllib2, re, xbmcaddon, xbmcplugin, xbmcgui, xbmc
from stream import *
import HTMLParser
html_parser = HTMLParser.HTMLParser()

dbg = False
pluginhandle = int(sys.argv[1])
itemcnt = 0
baseurl = 'http://onlinefilme.to'
settings = xbmcaddon.Addon(id='plugin.video.onlinefilme_to')
maxitems = (int(settings.getSetting("items_per_page"))+1)*16
filterUnknownHoster = settings.getSetting("filterUnknownHoster") == 'true'
forceViewMode = settings.getSetting("forceViewMode") == 'true'
viewMode = str(settings.getSetting("viewMode"))
userAgent = 'Mozilla/5.0 (X11; Linux x86_64; rv:18.0) Gecko/20100101 Firefox/18.0'
	
def START():
	addDir('Neue Filme', makeurl('filme-online/newest?page=1'), 1, '', True)
	addDir('Neue Serien', makeurl('serie-online/newest?page=1'), 1, '', True)
	addDir('Filmkategorien', baseurl, 2, '', True, 'filme')
	addDir('Serienkategorien', baseurl, 2, '', True, 'serie')
	#addDir('Suche...', makeurl('search.php'), 4, '', True)
	if forceViewMode: xbmc.executebuiltin("Container.SetViewMode("+viewMode+")")

def INDEX(url, search=None, value=None, id=None):
	if (dbg): print url
	global itemcnt
	items = 0
	data = getUrl(url, search, value, id)
	for movie in re.findall('(<li>[^<]*<a[^>]*>[^<]*<div[^>]*class="movie-holder"[^>]*>.*?</li>)', data, re.S|re.I):
		#if (dbg): print movie
		href = find('<a[^>]*href="([^"]+)"', movie)
		title = find('<div[^>]*class="cover-surface"[^>]*>[^<]*<strong>([^<]*)</strong>', movie)
		image = find('<img[^>]*data-original="([^"]+)"', movie)
		if (dbg): print title, makeurl(href), makeurl(image)
		addLink(clean(title), makeurl(href), 10, makeurl(image))
		itemcnt = itemcnt + 1
		items = 1
	actPage = find('page=([\d]+)', url)
	if actPage and items:
		a = int(actPage)
		n = a + 1
		np = re.sub('page=' + str(a), 'page=' + str(n), url)
		if (dbg): print np
		if itemcnt >= maxitems: addDir('Weiter >>', np, 1, '',  True)
		else: INDEX(np)
	if forceViewMode: xbmc.executebuiltin("Container.SetViewMode(" + viewMode + ")")

def CATEGORIES(url, value):
	if (dbg): print url
	data = getUrl(url)
	for (href, title) in re.findall('<li>[^<]*<a[^>]*href="([^"]+' + value + '-online[^"]+)"[^>]*><strong>([^<]+)</strong>', data, re.S|re.I): 
		if (dbg): print href, title
		addDir(clean(title), href, 1, '', True)
	if forceViewMode: xbmc.executebuiltin("Container.SetViewMode(" + viewMode + ")")

def SEARCH(url):
    keyboard = xbmc.Keyboard('', 'Suche')
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
		search_string = urllib.quote(keyboard.getText())
		INDEX(url, search_string)

def PLAYVIDEO(url):
	global filterUnknownHoster
	print url
	data = getUrl(url)
	if not data: return False
	videos = []
	for streams in re.findall('<div[^>]*class="panel">(.*?>Weiter</a>)', data, re.S|re.I|re.DOTALL):
		hostqual = find('<span[^>]*data-tooltip[^>]*aria-haspopup[^>]*title="([^"]+)"', streams)
		if ' - ' not in hostqual: hoster = hostqual
		else: (hoster, qual) = hostqual.split('-')
		views = find('<span[^>]*>([^<]*)<span[^>]*>(?:Views|Herunterladen)</span>', streams)
		url = find('<a[^>]*href=["\']([^"\']+)["\'][^>]*>Weiter', streams)
		if (dbg): print hoster, views, makeurl(url)
		videos += [('[COLOR=blue]' + clean(hoster) + '[/COLOR] ' + clean(qual) + ' ' + clean(views) + ' views', makeurl(url))]
	lv = len(videos)
	if lv == 0:
		xbmc.executebuiltin("XBMC.Notification(Fehler!, Video nicht gefunden, 4000)")
		return False
	url = selectVideoDialog(videos) if lv > 1 else videos[0][1]
	if not url: return False
	stream_url = GetStream(url)
	if not stream_url: return False
	print 'open stream: ' + stream_url
	listitem = xbmcgui.ListItem(path=stream_url)
	return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def makeurl(url):
	if 'http:' not in url: return baseurl + '/' + url
	else: return url

def find(rex, string):
	match = re.search(rex, string, re.S|re.I|re.DOTALL)
	if match: return match.group(1)
	else: return ''
	
def clean(s):
	if not s: return ''
	s = re.sub('^[\s]*', '', s)
	s = re.sub('[\s]*$', '', s)
	s = re.sub('<[^>]*>', '', s)
	try: s = html_parser.unescape(s)
	except: pass
	matches = re.findall("&#\d+;", s)
	for hit in set(matches):
		try: s = s.replace(hit, unichr(int(hit[2:-1])))
		except ValueError: pass
	return urllib.unquote(s)

def selectVideoDialog(videos):
	titles = []
	for name, src in videos: titles.append(name)
	idx = xbmcgui.Dialog().select("", titles)
	if idx > -1: return videos[idx][1]

def GetStream(url):
	target = None
	if (dbg): print "resolveUrl("+url+")"
	if baseurl in url: url = resolveUrl(url)
	if (dbg): print "findembed("+url+")"
	if 'watch_embeded.php' in url: target = findembed(url)
	if (dbg): print "target:" + str(target)
	if not target: target = findembed(url)
	if (dbg): print "target2:" + str(target)
	if target: url = target
	
	stream_url = get_stream_link().get_stream(url)
	if (dbg): print stream_url
	if stream_url is None:
		xbmc.executebuiltin("XBMC.Notification(Fehler!, Resolver liefert leeres Ergebnis, 4000)")
	elif re.match('.*not.*supported', stream_url, re.S|re.I):
		xbmc.executebuiltin("XBMC.Notification(Fehler!, Hoster nicht unterstuetzt, 4000)")
	elif re.match('^Error: ', stream_url, re.S|re.I):
		xbmc.executebuiltin("XBMC.Notification(Fehler!, " + re.sub('^Error: ','',stream_url) + ", 4000)")
	elif re.match('plugin:', stream_url, re.S|re.I):
		return stream_url
	else:
		return resolveUrl(stream_url)

def findembed(url):
	if (dbg): print url
	data = getUrl(url)
	if not data: return
	return find('<a[^>]*href="([^"]+)"[^>]*>[^<]*hier![^<]*</a>', data)
	
def resolveUrl(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', userAgent)
	response = urllib2.urlopen(req)
	url = response.geturl()
	response.close()
	return url
	
def getUrl(url, query=None, value=None, id=None):
	req = urllib2.Request(url)
	req.add_header('User-Agent', userAgent)
	if (dbg): print query
	if query or value or id:	
		values = { 'what' : '3', 'where' : '1', 'start_date' : '1900', 'end_date' : '2015', 'start_rating' : '1', 'end_rating' : '10', 'button' : 'Suche' }
		if query: values['src'] = query
		if value and id: values[id] = value
		response = urllib2.urlopen(req, urllib.urlencode(values))
	else:
		response = urllib2.urlopen(req)
	data = response.read()
	response.close()
	return data

def get_params():
	param = []
	paramstring = sys.argv[2]
	if len(paramstring) >= 2:
		params = sys.argv[2]
		cleanedparams = params.replace('?','')
		if (params[len(params)-1]=='/'): params = params[0:len(params)-2]
		pairsofparams = cleanedparams.split('&')
		param = {}
		for i in range(len(pairsofparams)):
			splitparams = pairsofparams[i].split('=')
			if (len(splitparams)) == 2:
				param[splitparams[0]] = splitparams[1]
	return param

def addLink(name, url, mode, image):
	u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode)
	liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=image)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	liz.setProperty('IsPlayable', 'true')
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)

def addDir(name, url, mode, image, is_folder=False, value=None):
	u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&value=" + str(value)
	liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=image)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=is_folder)
	
params = get_params()
url = None
mode = None
ret = True

try: url = urllib.unquote_plus(params["url"])
except: pass
try: mode = int(params["mode"])
except: pass
try: value = urllib.unquote_plus(params["value"])
except: pass
try: id = urllib.unquote_plus(params["id"])
except: pass

if mode==None or url==None or len(url)<1: START()
elif mode==1: INDEX(url)
elif mode==2: CATEGORIES(url, value)
elif mode==4: SEARCH(url)
elif mode==10: ret = PLAYVIDEO(url)

if ret: ret = 1
else: ret = 0
xbmcplugin.endOfDirectory(handle=pluginhandle, succeeded=ret)
#xbmcplugin.endOfDirectory(handle=pluginhandle)