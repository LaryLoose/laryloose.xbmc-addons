#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys, urllib, urllib2, re, xbmcplugin, xbmcgui, xbmcaddon

dbg = False 
pluginhandle = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.videocelebs.net')
translation = settings.getLocalizedString
forceViewMode = settings.getSetting("forceViewMode") == "true"
useThumbAsFanart = settings.getSetting("useThumbAsFanart") == "true"
max = settings.getSetting("maxItemsToView")
maxPerSite = ([10,20,30,50,100,150,200,500,-1])[1 if not max else int(max)]
viewModeVideos = str(settings.getSetting("viewModeVideos"))
viewModeLists = str(settings.getSetting("viewModeLists"))

startpage = 'https://videocelebs.net'
userAgent = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0'

itemcnt = 0

def index():
	if dbg: print 'index(): open ' + startpage
	content = getUrl(startpage)
	for items in re.compile('<ul[^>]*id="menu-select"[^>]*>(.*?)</ul>', re.DOTALL).findall(content):
		for href, cat in re.compile('<li[^>]*>[^<]*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.DOTALL).findall(items):
			if 'http' not in href: href = startpage + href
			if dbg: print cat, href
			if 'Contact us' in cat: continue
			addDir(cat, href, 'showList')
	addDir('Tags', startpage, 'showTags')
	addDir('Years', startpage, 'showYears')
	if forceViewMode: xbmc.executebuiltin('Container.SetViewMode('+viewModeLists+')')
	xbmcplugin.endOfDirectory(pluginhandle)

def showTags(url):
	if dbg: print 'showTags(): open ' + url
	content = getUrl(url)
	for items in re.compile('<div[^>]*class="tagcloud"[^>]*>(.*?)</div>', re.DOTALL).findall(content):
		for href, cat in re.compile('<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.DOTALL).findall(items):
			if 'http' not in href: href = startpage + href
			if dbg: print cat, href
			addDir(cat, href, 'showVideos')
	if forceViewMode: xbmc.executebuiltin('Container.SetViewMode('+viewModeLists+')')
	xbmcplugin.endOfDirectory(pluginhandle)

def showYears(url):
	if dbg: print 'showYears(): open ' + url
	content = getUrl(url)
	for items in re.compile('<div[^>]*id="menu-years"[^>]*>[^<]*<ul>(.*?)</div>', re.DOTALL).findall(content):
		for href, cat in re.compile('<li[^>]*>[^<]*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.DOTALL).findall(items):
			if 'http' not in href: href = startpage + href
			if dbg: print cat, href
			addDir(cat, href, 'showVideos')
	if forceViewMode: xbmc.executebuiltin('Container.SetViewMode('+viewModeLists+')')
	xbmcplugin.endOfDirectory(pluginhandle)

def showList(url):
	if dbg: print 'showList(): open ' + url
	content = getUrl(url)
	for items in re.compile('<div[^>]*class="list-celebs"[^>]*>(.*?)</div>', re.DOTALL).findall(content):
		for href, cat in re.compile('<li[^>]*>[^<]*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.DOTALL).findall(items):
			if 'http' not in href: href = startpage + href
			if dbg: print cat, href
			addDir(cat, href, 'showVideos')
		xbmcplugin.endOfDirectory(pluginhandle)
		if forceViewMode: xbmc.executebuiltin('Container.SetViewMode('+viewModeLists+')')
		return
	showVideos(url)

def showVideos(url):
	global itemcnt
	itemsfound = False
	if dbg: print 'showVideos(): open ' + url
	content = getUrl(url)
	for items in re.compile('<div[^>]*class="midle_div"[^>]*>(.*?)<div[^>]*class="(?:footer_block|wp-pagenavi)"', re.DOTALL).findall(content):
		for href, img, title in re.compile('<div[^>]*>[^<]*<a[^>]*href="([^"]+)"[^>]*>.*?<img[^>]*src="([^"]+)"[^>]*alt="([^"]*)"', re.DOTALL).findall(items):
			if dbg: print 'add link: title=' + title + ' href=' +href + ' img=' + img
			addLink(title, href, 'playVideo', img)
			itemcnt += 1
			itemsfound = True
	if itemsfound:
		for nextpage in  re.compile('<span[^>]*class="current"[^>]*>[^<]*</span>[^<]*<a[^>]*href="([^"]+)"', re.DOTALL).findall(content):
			if 'http' not in nextpage: nextpage = startpage + nextpage
			if dbg: print 'next page ' + nextpage
			if maxPerSite == -1 or int(itemcnt) < int(maxPerSite): showVideos(nextpage)
			addDir('Next Page', nextpage, 'showVideos')
	if forceViewMode: xbmc.executebuiltin('Container.SetViewMode('+viewModeVideos+')')
	xbmcplugin.endOfDirectory(pluginhandle)
	
def getVideoUrl(content):
	dict = {}
	for key, val in re.compile("([^,:]+):[ ]*'([^']*)'", re.DOTALL).findall(find('var flashvars[ ]*=[ ]*\{([^\}]+)\}', content)): 
		dict[key.strip()] = val.strip()
		if dbg: print key.strip() + ' : ' + val.strip() 
	rnd = dict.get('rnd')
	lic = dict.get('license_code')
	video = dict.get('video_alt_url')
	if not video: video = dict.get('video_url')
	return decryptHash(video, lic, "16")
	
def playVideo(url):
	if dbg: print 'playVideo(): ' + url
	content = getUrl(url)
	video = getVideoUrl(content)
	if dbg: print 'playVideo(): video url: ' + video
	if video:
		video = video + '|User-Agent=' + userAgent + '&Referer=' + startpage
		listitem = xbmcgui.ListItem(path=video.replace('\\', ''))
		return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
	else:
	    xbmc.executebuiltin('Notification(Video not found., 5000)')

def getUrl(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', userAgent)
	req.add_header('Referer', url)
	response = urllib2.urlopen(req, timeout=30)
	link = response.read()
	response.close()
	return link

def find(rex, string):
	match = re.search(rex, string, re.S|re.I|re.DOTALL)
	if match: return match.group(1)
	else: return ''

def calcSeed(licenseCode, hashRange):
    licenseCodeArray = list(licenseCode)
    f = m = ''
    for c in licenseCodeArray:
        if c == '$': continue
        f += c if int(c) != 0 else '1'
    j = int(len(f)/2)
    k = int(f[:j+1])
    l = int(f[j:])
    fi = abs(l - k)
    fi += abs(k - l)
    fi *= 2
    fArray = list(str(fi))
    i = int(hashRange)/2+2
    for g in xrange(0, j+1):
        for h in xrange(1, 5):
            n = int(licenseCodeArray[g+h]) + int(fArray[g])
            if n >= i: n-= i
            m += str(n)
    return m

def decryptHash(videoUrl, licenseCode, hashRange):
    videoUrlPart = videoUrl.split('/')
    splt = 2*int(hashRange)
    chash = videoUrlPart[7][:splt]
    nchash = videoUrlPart[7][splt:]
    seedArray = list(calcSeed(licenseCode, hashRange))
    if seedArray and chash:
        k = len(chash)-1
        while k >= 0:
            hashArray = list(chash)
            hal = len(hashArray)
            m = l = k
            while m < len(seedArray):
                l += int(seedArray[m])
                m += 1
            while l >= hal: l -= hal
            n = ''
            o = 0
            while o < hal:
                n += hashArray[l] if o == k else hashArray[k] if o == l else hashArray[o]
                o += 1
            chash = n
            k -= 1
        videoUrlPart[7] = chash + nchash
    del videoUrlPart[0:2]
    return '/'.join(videoUrlPart)

def parameters_string_to_dict(parameters):
	paramDict = {}
	if parameters:
		paramPairs = parameters[1:].split("&")
		for paramsPair in paramPairs:
			paramSplits = paramsPair.split('=')
			if (len(paramSplits)) == 2:
				paramDict[paramSplits[0]] = paramSplits[1]
	return paramDict

def addLink(name, url, mode, iconimage, fanart=''):
	u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode)
	liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	liz.setProperty('IsPlayable', 'true')
	if useThumbAsFanart: liz.setProperty('fanart_image', fanart)
	return xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz)

def addDir(name, url, mode, iconimage=''):
	#name = '* ' + name
	u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode)
	liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	return xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz, isFolder=True)

params = parameters_string_to_dict(sys.argv[2])
mode = params.get('mode')
url = params.get('url')

if type(url) == type(str()): url = urllib.unquote_plus(url)

if mode == 'showTags': showTags(url)
elif mode == 'showYears': showYears(url)
elif mode == 'showList': showList(url)
elif mode == 'showVideos': showVideos(url)
elif mode == 'playVideo': playVideo(url)
else: index()