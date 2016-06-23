#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib, urllib2, re, xbmcaddon, xbmcplugin, xbmcgui, xbmc
from stream import *
import HTMLParser
html_parser = HTMLParser.HTMLParser()

dbg = False
pluginhandle = int(sys.argv[1])
itemcnt = 0
baseurl = 'http://www.movietown.org'
settings = xbmcaddon.Addon(id='plugin.video.movietown_org')
maxitems = (int(settings.getSetting("items_per_page"))+1)*16
#filterUnknownHoster = settings.getSetting("filterUnknownHoster") == 'true'
filterUnknownHoster = True
forceViewMode = settings.getSetting("forceViewMode") == 'true'
viewMode = str(settings.getSetting("viewMode"))
userAgent = 'Mozilla/5.0 (X11; Linux x86_64; rv:18.0) Gecko/20100101 Firefox/18.0'
	
def START():
	addDir('Neue Filme', makeurl('movies'), 0, '', True, 'movie')
	addDir('Neue Serien', makeurl('series'), 0, '', True, 'series')
	addDir('Kategorien', makeurl('movies'), 2, '', True)
	#addDir('Suche...', makeurl('search.php'), 4, '', True)
	#if forceViewMode: xbmc.executebuiltin("Container.SetViewMode("+viewMode+")")

def INDEX(url, type):
	if (dbg): print url
	token = find("<script>[^<]*token:[ ]*'([^']+)'", getUrl(url))
	if dbg: print "token: " + token
	ADDITEMS(buildJsonUrl(token, type, 1))

def ADDITEMS(url):
	import json
	global itemcnt
	items = False
	data = getUrl(url)
	if data:
		jsondata = json.loads(data)
		for item in jsondata['items']:
			if (dbg): print item
			id = item['id']
			title = item['original_title']
			image = item['poster']
			if (dbg): print str(id)+", "+title+", "+makeurl(image)
			addLink(clean(title), url, 10, makeurl(image), id)
			itemcnt = itemcnt + 1
			items = True
	if items:
		a = find('&page=([0-9]+)', url)
		n = int(a) + 1
		np = re.sub('&page='+str(a), '&page='+str(n), url)
		if (dbg): print np
		if itemcnt >= maxitems: addDir('Weiter >>', np, 1, '',  True)
		else: ADDITEMS(np)
	if forceViewMode: xbmc.executebuiltin("Container.SetViewMode(" + viewMode + ")")

def buildJsonUrl(token, type, page, genre=''):
	return makeurl("titles/paginate?_token="+str(token)+"&perPage="+str(maxitems)+"&page="+str(page)+"&order=release_dateDesc&type="+str(type)+"&genres[]="+str(genre))

def CATEGORIES(url):
	if (dbg): print url
	data = getUrl(url)
	token = find("<script>[^<]*token:[ ]*'([^']+)'", data)
	if dbg: print "token: " + token
	for (value, label) in re.findall('<input type="checkbox" class="checkbox" value="([^"]+)" data-bind="checked: params.genres"/>[ ]*([^<]+)[ ]*</label>', data, re.S|re.I): 
		if (dbg): print value, label
		addDir(label, buildJsonUrl(token, 'movie', 1, value), 1, '',  True)
	if forceViewMode: xbmc.executebuiltin("Container.SetViewMode(" + viewMode + ")")

def SEARCH(url):
    keyboard = xbmc.Keyboard('', 'Suche')
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
		search_string = urllib.quote(keyboard.getText())
		INDEX(url, search_string)

def PLAYVIDEO(url, id):
	import json
	global filterUnknownHoster
	if (dbg): print url, id
	data = getUrl(url)
	if not data: return False
	jsondata = json.loads(data)
	videos = []
	for item in jsondata['items']:
		if (str(item['id']) == str(id)):
			for link in item['link']:
				hoster = get_stream_link().get_hostername(link['url'])
				if (filterUnknownHoster and str(hoster) == 'Not Supported'): continue
				qual = link['quality']
				lnk = link['url']
				if (dbg): print hoster, makeurl(lnk)
				season = link['season']
				episode = link['episode']
				title = ''
				if season: title += "S"+str(season)+"E"+str(episode)+" "
				videos += [(title+'[COLOR=blue]' + clean(hoster) + '[/COLOR] ' + clean(qual), makeurl(lnk))]
			break
	lv = len(videos)
	if (dbg): print "found hoster: " + str(lv)
	if lv == 0:
		xbmc.executebuiltin("XBMC.Notification(Fehler!, Video nicht gefunden, 4000)")
		return False
	url = selectVideoDialog(videos) if lv > 1 else videos[0][1]
	if not url: return False
	if (dbg): print "url: " + url
	stream_url = GetStream(url)
	if not stream_url: return False
	print 'open stream: ' + stream_url
	listitem = xbmcgui.ListItem(path=stream_url)
	return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def makeurl(url):
	if 'http' not in url: return baseurl + '/' + url
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
	if (dbg): print "GetStream: " + url
	stream_url = get_stream_link().get_stream(url)
	if (dbg): print stream_url
	if stream_url is None:
		xbmc.executebuiltin("XBMC.Notification(Fehler!, Resolver liefert leeres Ergebnis, 4000)")
	elif re.match('.*not.*supported', stream_url, re.S|re.I):
		xbmc.executebuiltin("XBMC.Notification(Fehler!, Hoster nicht unterstuetzt, 4000)")
	elif re.match('^Error: ', stream_url, re.S|re.I):
		xbmc.executebuiltin("XBMC.Notification(Fehler!, " + re.sub('^Error: ','',stream_url) + ", 4000)")
	else:
		return stream_url

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
	
def getUrl(url, info=None):
	req = urllib2.Request(url)
	req.add_header('User-Agent', userAgent)
	response = urllib2.urlopen(req, info)
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

def addLink(name, url, mode, image, value=None):
	u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&value=" + str(value)
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

if mode==None or url==None or len(url)<1: START()
elif mode==0: INDEX(url, value)
elif mode==1: ADDITEMS(url)
elif mode==2: CATEGORIES(url)
elif mode==4: SEARCH(url)
elif mode==10: ret = PLAYVIDEO(url, value)

if ret: ret = 1
else: ret = 0
#xbmcplugin.endOfDirectory(handle=pluginhandle, succeeded=ret)
xbmcplugin.endOfDirectory(handle=pluginhandle)