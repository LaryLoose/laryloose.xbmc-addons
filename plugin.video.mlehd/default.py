#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib, urllib2, re, xbmcaddon, xbmcplugin, xbmcgui, xbmc
from jsunpacker import cJsUnpacker

pluginhandle = int(sys.argv[1])
itemcnt = 0
baseurl = 'http://mle-hd.se/'
settings = xbmcaddon.Addon(id='plugin.video.mlehd')
maxitems = (int(settings.getSetting("items_per_page"))+1)*24
forceViewMode = settings.getSetting("forceViewMode") == 'true'
viewMode = str(settings.getSetting("viewMode"))

def CATEGORIES():
	data = getUrl(baseurl)
	header = re.findall('id="primary-menu"(.*?)id="container"', data, re.S|re.I)
	cats = re.findall('<li[^>]*id="menu-item[^>]+>[^<]*<a href="(.*?)"[^>]*>([^<]*)</a>', str(header), re.S|re.I)
	addDir('Letzte Updates', baseurl, 1, '', True)
	for (url, name) in cats:
		if re.match('.*Filme.*A-Z.*', name): continue #skip 'Filme A-Z'
		name = re.sub('Kom.*?dien', 'Komödien', name) #ugly workaround for unicode literals in this string
		name = re.sub('[ ]*/[ ]*', ' / ', name)       #normalize all entries with a '/'
		if 'http:' not in url: url = baseurl + url
#		print name
		addDir(clean(name), url, 1, '', True)
	if forceViewMode: xbmc.executebuiltin("Container.SetViewMode("+viewMode+")")

def INDEX(caturl):
	print caturl
	global itemcnt
	data = getUrl(caturl)
	for entry in re.findall('<div class="entry[^"]*"(.+?)</div>', data, re.S|re.I):
		movie = re.findall('href="(.*?)"[^>]*title="(.*?)"[^>]*>[^<]*<img[^>]*src="(.*?)"', entry, re.S|re.I)
		if movie:
			(url, title, image) = movie[0]
			if 'http:' not in url: url =  baseurl + url
			addLink(clean(title), url, 2, image)
			itemcnt = itemcnt + 1
	currentPage = re.findall('class="current">(.*?)</', data, re.S|re.I)
	curr = int(currentPage[0]) if currentPage else 0
	nextPage = re.findall('<a href=["|\']([^>]*)["|\'][^>]*class="inactive"[^>]*>' + str(curr+1) + '</', data, re.S)
	if nextPage:
		if itemcnt >= maxitems: addDir('Weiter >>', nextPage[0], 1, '',  True)
		else: INDEX(nextPage[0])
	if forceViewMode: xbmc.executebuiltin("Container.SetViewMode("+viewMode+")")

def clean(s):
	matches = re.findall("&#\d+;", s)
	for hit in set(matches):
		try: s = s.replace(hit, unichr(int(hit[2:-1])))
		except ValueError: pass
	return urllib.unquote_plus(s)

def selectVideoDialog(videos):
	titles = []
	for i in range(1, len(videos)+1):
		titles.append('Teil ' + str(i))
	idx = xbmcgui.Dialog().select("", titles)
	return videos[idx]

def PLAYVIDEO(url):
	data = getUrl(url)
	videos = []
	proplayer = re.findall('id="(?:mediaspace|containingBlock)"(.*)</script>', data, re.S|re.I)
	if proplayer:
		videos = re.findall('file:.*?\'(.*?)\'', proplayer[0], re.S|re.I)
		if not videos: videos = re.findall('&amp;file=(.*?)&amp;', proplayer[0], re.S|re.I)
	else:
		iframes = re.findall('id="main".*?<iframe[^>]*src="(.*?)"[^>]*>', data, re.S|re.I)
		if iframes:
			for iframe in iframes:
				videos.append(getVideoFromIframe(iframe))

	url = selectVideoDialog(videos) if len(videos) > 1 else videos[0]

	if 'playlist-controller' in url:
		playlist = getUrl(url)
		loc = re.findall('<location>(.*?)</location>', playlist, re.S|re.I)
		if loc: url = loc[0]
	
	print 'try to play: ' + url
	return xbmcplugin.setResolvedUrl(pluginhandle, True, xbmcgui.ListItem(path=url))

def getVideoFromIframe(url):
	data = getUrl(url)
	stream_url = ''
	get_packedjava = re.findall('<script type=.text.javascript.>eval.function(.*?)</script>', data, re.S|re.DOTALL)
	if get_packedjava:
	    sUnpacked = cJsUnpacker().unpackByString(get_packedjava[0])
	    if re.match('.*?type="video/divx', sUnpacked): stream_url = re.findall('type="video/divx".*?src="(.*?)"', sUnpacked)
	    elif re.match('.*?file', sUnpacked): stream_url = re.findall("file','(.*?)'", sUnpacked)
	if not stream_url: stream_url = re.findall("file:[ ]*'(.*?)'", data)
	return stream_url[0] if stream_url else ''

def getUrl(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	data = response.read()
	response.close()
	return data.decode('utf-8')

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

def addDir(name, url, mode, image, is_folder=False):
	u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode)
	liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=image)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=is_folder)

print 'Arguments:', sys.argv
params = get_params()
url = None
mode = None

try: url = urllib.unquote_plus(params["url"])
except: pass
try: mode = int(params["mode"])
except: pass

if mode==None or url==None or len(url)<1: CATEGORIES()
elif mode==1: INDEX(url)
elif mode==2: PLAYVIDEO(url)

xbmcplugin.endOfDirectory(pluginhandle)
