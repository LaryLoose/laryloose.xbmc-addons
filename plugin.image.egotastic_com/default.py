#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib, urllib2, re, xbmcplugin, xbmcgui, sys, xbmcaddon
import HTMLParser
html_parser = HTMLParser.HTMLParser()

thisPlugin = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.egotastic_com')
translation = settings.getLocalizedString
forceViewMode = settings.getSetting("force_viewmode") == "true"
useCacheToDisc = settings.getSetting("cache_to_disc") == "true"
maxitems = (int(settings.getSetting("items_per_page"))+1)*15
itemcnt = 0
baseurl = 'http://www.egotastic.com'

def index():
	addDir(translation(30201), baseurl + '/photos', 'showPhotoIndex')
	addDir(translation(30203), baseurl + '/all-stars', 'showGalleryView')
	addDir(translation(30202), baseurl + '/celebrities', 'showCelebIndex')
	
def showPhotoIndex(url):
	global itemcnt
	content = getUrl(url)
	for href, img, title in re.findall('<div[^>]*class="thumb"[^>]*>[^<]*<a[^>]*href="([^"]+)"[^>]*>[^<]*<img[^>]*src="([^"]+)"[^>]*title="([^"]+)"[^>]*>', content, re.I|re.S|re.DOTALL):
		addDir(clean(title), href, 'showPictures', img)
		itemcnt = itemcnt + 1
	nextPage = find('<li[^>]*class="next_page"[^>]*>[^<]*<a[^>]*href="([^"]+)"', content)
	if nextPage:
		if itemcnt >= maxitems: addDir(translation(30301), nextPage, 'showPhotoIndex')
		else: showPhotoIndex(nextPage)
	if forceViewMode: xbmc.executebuiltin('Container.SetViewMode(500)')

def showCelebIndex(url, char=None):
	content = getUrl(url)
	if char is None:
		for c in re.findall('<div[^>]*class="celeb-key"[^>]*>([A-Za-z])</div>', content, re.I|re.S):
			addDir(c, url, 'showCelebIndex', '', c)
	else:
		range = find('<div[^>]*class="celeb-key"[^>]*>'+char+'</div>(.*?)(:!<div[^>]*class="celeb-key"[^>]*>(?!'+char+')|$)', content)
		for href, title in re.findall('<a[^>]*href="([^"]+)">([^<]*)</a>', range, re.I|re.S):
			addDir(clean(title), href, 'showGalleryView')
	if forceViewMode: xbmc.executebuiltin('Container.SetViewMode(500)')

def showGalleryView(url):
	global itemcnt
	content = getUrl(url)
	for href, title, img in re.findall('<div[^>]*class="main_img"[^>]*>[^<]*<a[^>]*href="([^"]+)"[^>]*title="([^"]+)"[^>]*>[^<]*<img[^>]*src="([^"]+)"', content, re.I|re.S):
		addDir(clean(title), href, 'showPictures', img)
		itemcnt = itemcnt + 1
	nextPage = find('<li[^>]*class="next_page"[^>]*>[^<]*<a[^>]*href="([^"]+)"', content)
	if nextPage:
		if itemcnt >= maxitems: addDir(translation(30301), nextPage, 'showGalleryView')
		else: showGalleryView(nextPage)
	if forceViewMode: xbmc.executebuiltin('Container.SetViewMode(500)')

def showPictures(url):
	import json
	content = getUrl(url)
	gallery = json.loads(find('var pi_gallery = (\{.*?\});', content))
	for entry in gallery["images"]:
		addPicture(getPicName(entry["image"]["full"]), entry["image"]["full"], entry["image"]["thumb"])
	xbmcplugin.addSortMethod(handle=thisPlugin, sortMethod=1)
	if forceViewMode: xbmc.executebuiltin('Container.SetViewMode(500)')
	
def getPicName(url):
	name = find('/([^/]*)$', url)
	name = re.sub('^TGIF-', '', name, re.I)
	name = re.sub('[-]', '_', name)
	name = re.sub('\.jpg', '', name, re.I)
	return name

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

def addPicture(name, url, iconimage=''):
	listItem = xbmcgui.ListItem(label=name, thumbnailImage=iconimage)
	listItem.setProperty('mimetype', 'image/jpeg') 
	return xbmcplugin.addDirectoryItem(thisPlugin, url, listItem, False)

def addDir(name, url, mode, iconimage='', char=''):
	u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&char=" + str(char)
	liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	liz.setInfo(type="Picture", infoLabels={ "Title": name } )
	return xbmcplugin.addDirectoryItem(handle=thisPlugin, url=u, listitem=liz, isFolder=True)

params = parameters_string_to_dict(sys.argv[2])
mode = params.get('mode')
url = params.get('url')
char = params.get('char')
if type(url)==type(str()): url = urllib.unquote_plus(url)

if mode == 'showPhotoIndex': showPhotoIndex(url)
elif mode == 'showCelebIndex': showCelebIndex(url, char)
elif mode == 'showGalleryView': showGalleryView(url)
elif mode == 'showPictures': showPictures(url)
else: index()

xbmcplugin.endOfDirectory(handle=thisPlugin, succeeded=True, updateListing=False, cacheToDisc=useCacheToDisc)


