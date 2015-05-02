#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib, urllib2, re, xbmcaddon, xbmcplugin, xbmcgui, xbmc
from stream import *
import HTMLParser
html_parser = HTMLParser.HTMLParser()

dbg = False
pluginhandle = int(sys.argv[1])
itemcnt = 0
baseurl = 'http://silverkino.to'
settings = xbmcaddon.Addon(id='plugin.video.silverkino_to')
maxitems = (int(settings.getSetting("items_per_page"))+1)*16
filterUnknownHoster = settings.getSetting("filterUnknownHoster") == 'true'
forceViewMode = settings.getSetting("forceViewMode") == 'true'
viewMode = str(settings.getSetting("viewMode"))
userAgent = 'Mozilla/5.0 (X11; Linux x86_64; rv:18.0) Gecko/20100101 Firefox/18.0'
	
def START():
	addDir('Filme', makeurl('movies.php?cat=1'), 1, '', True)
	addDir('Serien', makeurl('movies.php?cat=4'), 1, '', True)
	addDir('Dokus', makeurl('movies.php?cat=7'), 1, '', True)
	addDir('Kategorien', makeurl('movies.php'), 2, '', True)
	addDir('Suche...', makeurl('search.php'), 4, '', True)
	if forceViewMode: xbmc.executebuiltin("Container.SetViewMode("+viewMode+")")

def INDEX(url, search=None, value=None, id=None):
	if (dbg): print url
	global itemcnt
	data = getUrl(url, search, value, id)
	for moviesection in re.findall('<div[^>]*id="movie_list"[^>]*>(.*?)<div[^>]*id="paging"', data, re.S|re.I):
		for movie in re.findall('(<a[^>]*>[^<]*<div[^>]*id="mov[\d]*".*?</a>)', moviesection, re.S|re.I):
			if (dbg): print movie
			url = find('<a[^>]*href="([^"]*)"', movie)
			title = find('<div[^>]*class="more"[^>]*id="mov[\d]*_info">([^<]*)<', movie)
			image = find('<img[^>]*src="(img_movies[^"]+)"[^>]*>', movie)
			if (dbg): print clean(title), makeurl(url), makeurl(image)
			addLink(clean(title), makeurl(url), 10, makeurl(image))
			itemcnt = itemcnt + 1
	nextPage = find('<div id="paging">.*?<a href="([^"]+)">></a>', data)
	if nextPage and 'pag=0' not in nextPage:	
		np = makeurl(clean(nextPage))
		if (dbg): print np
		if itemcnt >= maxitems: addDir('Weiter >>', np, 1, '',  True)
		else: INDEX(np)
	if forceViewMode: xbmc.executebuiltin("Container.SetViewMode("+viewMode+")")

def CATEGORIES(url):
	import operator
	if (dbg): print url
	data = getUrl(url)
	cats = find('<strong>Genre:</strong>[^<]*<br />[^<]*<ul>(.*?)</ul>', data)
	dict = { }
	for (value, id, title) in re.findall('<li>[^<]*<label>[^<]*<input[^>]*value="([^"]+)"[^>]*id="([^"]+)"[^>]*>([^<]*)</label>', cats, re.S|re.I):
		dict[clean(title)] = '&value='+value+'&id='+id
	for (title, vals) in sorted(dict.items(), key=operator.itemgetter(0)):	
		addDir(title, makeurl('search.php'), 3, '', True, vals)
	if forceViewMode: xbmc.executebuiltin("Container.SetViewMode("+viewMode+")")

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
	if not data: return
	videos = []
	for streams in re.findall('<div id="lm"(.*?<div[^>]*class="link_play">Weiter</div>)', data, re.S|re.I|re.DOTALL):
		hoster = find('<div[^>]*class="link_share">[^<]*<a[^>]*>([^<]+)</a>[^<]*</div>', streams)
		qual = find('<div[^>]*class="link_quality">[^<]*<a[^>]*>([^<]+)</a>[^<]*</div>', streams)
		views = find('<div[^>]*class="link_views">([^<]+)<span[^>]*>[^<]*Views[^<]*</span>', streams)
		url = find('<a href="([^"]+)"[^>]*target="_blank"[^>]*>', streams)
		videos += [('[COLOR=blue]' + hoster + '[/COLOR] ' + clean(qual) + ' ' + clean(views) + ' views', makeurl(url))]
	lv = len(videos)
	if lv == 0:
		xbmc.executebuiltin("XBMC.Notification(Fehler!, Video nicht gefunden, 4000)")
		return
	url = selectVideoDialog(videos) if lv > 1 else videos[0][1]
	if url:
		stream_url = GetStream(url)
		if stream_url:
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
	if not s: return
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
	for name, src in videos:
		titles.append(name)
	idx = xbmcgui.Dialog().select("", titles)
	if idx > -1: return videos[idx][1]

def GetStream(url):
	if (dbg): print url
	if baseurl in url:
		req = urllib2.Request(url)
		req.add_header('User-Agent', userAgent)
		response = urllib2.urlopen(req)
		url = response.geturl()
		response.close()
	if (dbg): print url
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
		req = urllib2.Request(stream_url)
		req.add_header('User-Agent', userAgent)
		response = urllib2.urlopen(req)
		stream_url = response.geturl()
		response.close()
		return stream_url

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

def addDir(name, url, mode, image, is_folder=False, vals=None):
	u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode)
	if vals: u = u + vals
	liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=image)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=is_folder)
	
params = get_params()
url = None
mode = None

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
elif mode==2: CATEGORIES(url)
elif mode==3: INDEX(url, None, value, id)
elif mode==4: SEARCH(url)
elif mode==10: PLAYVIDEO(url)

xbmcplugin.endOfDirectory(pluginhandle)
