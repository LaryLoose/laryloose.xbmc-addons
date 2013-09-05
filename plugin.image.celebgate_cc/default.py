#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib, urllib2, re, xbmcplugin, xbmcgui, sys, xbmcaddon, base64

thisPlugin = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.celebgate_cc')
translation = settings.getLocalizedString
forceViewMode = settings.getSetting("force_viewmode") == "true"
useCacheToDisc = settings.getSetting("cache_to_disc") == "true"

baseurl = 'http://www.celeb.gate.cc'
thumburl = 'http://files.celeb.gate.cc/headshots/preview/'
piclisturl = 'http://www.celeb.gate.cc/de/<name>/pictures/list.xml?name=<name>&first=1&last=9999'
picsurl = 'http://files.celeb.gate.cc/pictures/'
prevurl = 'http://files.celeb.gate.cc/pictures/preview/'

def index():
		addDir(translation(30201), baseurl + '/de/home.html', 'showUpdateFolders', '')
		addDir(translation(30202), baseurl + '/de/home.html', 'showAlphaFolders', '')
		addDir(translation(30203), baseurl + '/de/misc/top_daily.html', 'showTopFolders', '')
		addDir(translation(30204), baseurl + '/de/misc/top_monthly.html', 'showTopFolders', '')
		addDir(translation(30205), baseurl + '/de/misc/top_alltime.html', 'showTopFolders', '')
		xbmcplugin.endOfDirectory(thisPlugin)

def showAlphaFolders(url):
		content = getUrl(url)
		match = re.compile('<ul class="letters">(.*?)</ul>', re.DOTALL).findall(content)
		letters = re.compile('<li>[^<]*<a href="(.*?)" title="(.*?)">([A-Za-z])</a>[^<]*</li>', re.DOTALL).findall(match[0])
		for i in range(0, len(letters), 1):
			addDir(letters[i][2] + '    (' + letters[i][1].replace(' &#10;', ', ') + ')', baseurl + letters[i][0], 'showNameFolders', '')
		xbmcplugin.endOfDirectory(thisPlugin)

def showTopFolders(url):
		content = getUrl(url)
		lists = re.compile('<ul[^>]*class="list"[^<]*>(.*?)</ul>', re.DOTALL).findall(content)
		for l in range(0, len(lists), 1):
			names = re.compile('<li>([^<]*)<a[^>]*href="(.*?)"[^>]*name="(.*?)"[^>]*>(.*?)</a>[^<]*</li>', re.DOTALL).findall(lists[l])
			for n in range(0, len(names), 1):
				addDir(names[n][0] + ' ' + names[n][3], baseurl + names[n][1], 'showPictures', thumburl + names[n][2] + '.jpg')
		xbmcplugin.endOfDirectory(thisPlugin)

def showNameFolders(url):
		content = getUrl(url)
		lists = re.compile('<ul[^>]*class="list"[^<]*>(.*?)</ul>', re.DOTALL).findall(content)
		for l in range(0, len(lists), 1):
			names = re.compile('<li>[^<]*<a[^>]*href="(.*?)"[^>]*name="(.*?)"[^>]*>(.*?)</a>[^<]*</li>', re.DOTALL).findall(lists[l])
			for n in range(0, len(names), 1):
				addDir(names[n][2], baseurl + names[n][0], 'showPictures', thumburl + names[n][1] + '.jpg')
		xbmcplugin.endOfDirectory(thisPlugin)
		
def showUpdateFolders(url):
		content = getUrl(url)
		updates = re.compile('<div class="updatebox_day">(.*?)<div class="clear">', re.DOTALL).findall(content)
		for u in range(0, len(updates), 1):
			updateinfo = re.compile('<div class="update_info">[^<]*<h[0-9]>(.*?)</h[0-9]>[^<]*<h[0-9]>(.*?)</h[0-9]>', re.DOTALL).findall(updates[u])
			names = re.compile('<li>[^<]*<a[^>]*href="(.*?)"[^>]*name="(.*?)"[^>]*>(.*?)</a>[^<]*</li>', re.DOTALL).findall(updates[u])
			for n in range(0, len(names), 1):
				addDir(updateinfo[0][0] + ' ' + updateinfo[0][1] + ' ' + names[n][2], baseurl + names[n][0], 'showPictures', thumburl + names[n][1] + '.jpg')
		xbmcplugin.endOfDirectory(thisPlugin)

def showPictures(url):
		namematch = re.compile(baseurl + '/de/(.*?)/[^/]*html', re.DOTALL).findall(url)
		url = piclisturl.replace('<name>', namematch[0])
		print('get pictures from ' + url)
		content = getUrl(url)
		#print(content)
		pics = re.compile('<id2>(.*?)</id2>', re.DOTALL).findall(content)
		for p in range(0, len(pics), 1):
			picname = base64.standard_b64decode(pics[p])
			addPicture(picname, picsurl + picname, prevurl + picname)
		if forceViewMode: xbmc.executebuiltin('Container.SetViewMode(500)')
		xbmcplugin.endOfDirectory(handle=thisPlugin, succeeded=True, updateListing=False, cacheToDisc=useCacheToDisc)

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
		return xbmcplugin.addDirectoryItem(thisPlugin, url, listItem, False)

def addDir(name, url, mode, iconimage):
		u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode)
		liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
		liz.setInfo(type="Picture", infoLabels={ "Title": name } )
		return xbmcplugin.addDirectoryItem(handle=thisPlugin, url=u, listitem=liz, isFolder=True)

params=parameters_string_to_dict(sys.argv[2])
mode=params.get('mode')
url=params.get('url')
if type(url)==type(str()):
  url=urllib.unquote_plus(url)

if mode == 'showAlphaFolders':
    showAlphaFolders(url)
elif mode == 'showNameFolders':
    showNameFolders(url)
elif mode == 'showTopFolders':
    showTopFolders(url)
elif mode == 'showUpdateFolders':
    showUpdateFolders(url)
elif mode == 'showPictures':
    showPictures(url)
else:
    index()




