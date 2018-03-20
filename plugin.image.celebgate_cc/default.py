#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib, urllib2, re, xbmcplugin, xbmcgui, sys, xbmcaddon, base64

dbg = False
thisPlugin = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.image.celebgate_cc')
translation = settings.getLocalizedString
forceViewMode = settings.getSetting("force_viewmode") == "true"
useCacheToDisc = settings.getSetting("cache_to_disc") == "true"
maxPerSite = (['42','84','168','336','672','1344','2688','5076','-1'])[int(settings.getSetting("max_per_site"))]
baseurl = 'http://celeb.gate.cc'
itemcnt = 0

def index():
	addDir(translation(30201), fixUrl('/de/recent.html'), 'showUpdateFolders', '')
	addDir(translation(30208), baseurl, 'birthdays', '')
	addDir(translation(30206), fixUrl('/country/DE.html?sort=c.firstname&direction=asc&page=1'), 'showNameFolders', '')
	addDir(translation(30207), fixUrl('/country/US.html?sort=c.firstname&direction=asc&page=1'), 'showNameFolders', '')
	addDir(translation(30210), fixUrl('/de/profession/actress.html?sort=c.firstname&direction=asc&page=1'), 'showNameFolders', '')
	addDir(translation(30209), fixUrl('/de/profession/musician.html?sort=c.firstname&direction=asc&page=1'), 'showNameFolders', '')
	addDir('Model', fixUrl('/de/profession/model.html?sort=c.firstname&direction=asc&page=1'), 'showNameFolders', '')
	addDir('Playboy', fixUrl('/tag/playboy.html?page=1'), 'showNameFolders', '')
	addDir('The Fappening', fixUrl('/blog/5/the-fappening-leaked-icloud-nude-pics'), 'showNameFolders', '')
	addDir(translation(30203), fixUrl('/de/top.html?sort=c.clicksDay&page=1'), 'showNameFolders', '')
	addDir(translation(30204), fixUrl('/de/top.html?sort=c.clicksMonth&page=1'), 'showNameFolders', '')
	addDir(translation(30205), fixUrl('/de/top.html?sort=c.clicksTotal&page=1'), 'showNameFolders', '')
	addDir(translation(30202), fixUrl('/de/home.html'), 'showAlphaFolders', '')
	addDir(translation(30302), fixUrl('/search?q='), 'search', '')
	xbmcplugin.endOfDirectory(thisPlugin)

def search(url):
    keyboard = xbmc.Keyboard('', translation(30302))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText()
        showNameFolders(url+search_string)

def birthdays(url):
	content = getUrl(url)
	for match in re.compile('<div[^>]*id="birthday-carousel"[^>]*>(.*)href="#birthday-carousel"', re.DOTALL).findall(content):
		for a in re.compile('(<a.*?<a.*?/a>.*?/a>)', re.DOTALL).findall(match):
			thumb, name = re.findall('<img[^>]*src="([^"]*)"[^>]*alt="([^"]*)"[^>]*', a, re.S|re.I)[0]
			href = re.findall('<a[^>]*data-id=[^>]*href="([^"]*)"', a, re.S|re.I)[0]
			desc = re.findall('<p>(.*)</p>', a, re.S|re.I)[0]
			addDir(name + " (" + cleanString(desc) + ")", fixUrl(href), 'showPictures', thumb)

def showAlphaFolders(url):
	if dbg: print "open " + url
	content = getUrl(url)
	for match in re.compile('<[^>]*id="list-nav">[^<]*<ul[^>]*>(.*?)</ul>', re.DOTALL).findall(content):
		for href,letter in re.compile('<li>[^<]*<a href="(.*?)"[^>]*>([A-Za-z])</a>[^<]*</li>', re.DOTALL).findall(match):
			addDir(letter, fixUrl(href) + "?sort=c.firstname&direction=asc&page=1", 'showNameFolders', '')
	
def showNameFolders(url):
	if dbg: print "open " + url
	global itemcnt
	content = getUrl(url)
	cnt = 0
	for l in re.compile('<ol[^>]*class="gallery"[^<]*>(.*?)</ol>', re.DOTALL).findall(content):
		for href,img,caption in re.compile('<li>[^<]*<a[^>]*href="([^"]*)"[^>]*>[^<]*<figure>[^<]*<img[^>]*src="([^"]*)"[^>]*>[^<]*<figcaption>([^<]*)</figcaption>[^<]*</figure>[^<]*</a>[^<]*</li>', re.DOTALL).findall(l):
			addDir(fixString(caption), fixUrl(href), 'showPictures', img)
			cnt = cnt + 1
	page = re.compile('.*page=([0-9]+)').findall(url)
	if page: 
		next = re.sub('page=([0-9]+)', 'page=' + str(int(page[0])+1), url)
		if cnt == 0: return
		itemcnt = itemcnt + cnt
		if maxPerSite == -1 or int(itemcnt) < int(maxPerSite): showNameFolders(next)
		else: addDir(translation(30301), fixUrl(next), 'showNameFolders', '')

def showUpdateFolders(url):
	if dbg: print "open " + url
	content = getUrl(url)
	for href,img,name in re.compile('<a[^>]*href="([^"]+)"[^>]*>[^<]*<figure>[^<]*<img[^>]*src="([^"]+)"[^>]*alt="([^"]+)"', re.DOTALL).findall(content):
		href = re.sub('gallery', 'pictures', href)
		addDir(name, fixUrl(href), 'showPictures', img)

def showPictures(url):
	if dbg: print "getting pictures from " + url
	content = getUrl(url)
	for href,img,picname in re.compile('<li[^>]*class="gallery-image"[^>]*>[^<]*<a[^>]*data-orig=["]*([^" ]+)["]*[^>]*>[^<]*<figure*[^>]*>[^<]*<img[^>]*src="([^"]+)"[^>]*alt="([^"]*)"[^>]*>', re.DOTALL).findall(content):
		addPicture(picname, href, img)
	for cur, max in re.compile('<li[^>]*class="active"[^>]*>[^<]*<span>([0-9]+)</span>[^<]*</li>.*>([0-9])+</a>[^<]*</li>[^<]*<li>[^<]*<a[^>]*rel="next"', re.DOTALL).findall(content):
		next = int(cur) + 1
		if next <= max:
			if 'p=' in url: nexturl = re.sub('p=([0-9]+)', 'p=' + str(next), url)
			else: nexturl = url + '?p=' + str(next)
			addDir(translation(30301), fixUrl(nexturl), 'showPictures', '')
	if forceViewMode: xbmc.executebuiltin('Container.SetViewMode(500)')

def cleanString(str):
	str = re.sub('<br>', ' -', str)
	str = re.sub('<[^>]+>', ' ', str)
	str = re.sub('[\n\r]', ' ', str)
	str = re.sub('[ ]+', ' ', str)
	return fixString(str.strip())

def fixString(str):
	return str.replace('&#039;', "'")

def fixUrl(url):
	if baseurl not in url: return baseurl + url
	else: return url

def getUrl(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0')
	response = urllib2.urlopen(req, timeout = 30)
	link = response.read()
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

def addPicture(name, url, iconimage):
	listItem = xbmcgui.ListItem(label=name, thumbnailImage=iconimage)
	listItem.setProperty('mimetype', 'image/jpeg') 
	return xbmcplugin.addDirectoryItem(thisPlugin, url, listItem, False)

def addDir(name, url, mode, iconimage):
	u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode)
	liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	liz.setInfo(type="Picture", infoLabels={ "Title": name } )
	return xbmcplugin.addDirectoryItem(handle=thisPlugin, url=u, listitem=liz, isFolder=True)

params = parameters_string_to_dict(sys.argv[2])
mode = params.get('mode')
url = params.get('url')
if type(url)==type(str()): url = urllib.unquote_plus(url)

if mode == 'showAlphaFolders': showAlphaFolders(url)
elif mode == 'showNameFolders': showNameFolders(url)
elif mode == 'showTopFolders': showTopFolders(url)
elif mode == 'showUpdateFolders': showUpdateFolders(url)
elif mode == 'showPictures': showPictures(url)
elif mode == 'addPictures': addPictures(url)
elif mode == 'search': search(url)
elif mode == 'birthdays': birthdays(url)
else: index()

xbmcplugin.endOfDirectory(handle=thisPlugin, cacheToDisc=useCacheToDisc)
