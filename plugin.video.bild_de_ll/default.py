#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys, urllib, urllib2, re, xbmcplugin, xbmcgui, xbmcaddon

#try:
#    import StorageServer
#except:
#    import storageserverdummy as StorageServer
#cache = StorageServer.StorageServer('plugin.video.bild_de_ll', 24)

dbg = False
pluginhandle = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.bild_de_ll')
translation = settings.getLocalizedString
forceViewMode = settings.getSetting("forceViewMode") == "true"
useThumbAsFanart = settings.getSetting("useThumbAsFanart") == "true"
searchInMostClicked = settings.getSetting("searchInMostClicked") == "true"
viewMode = str(settings.getSetting("viewMode"))

startpage = 'http://www.bild.de'
baseurl = 'http://www.bild.de/video/clip/<fid>,zeigeTSLink=true,page=<pn>,isVideoStartseite=true,view=ajax,contentContextId=<cid>.bild.html'

def index():
	for k, v in enumerate(getFolders()):
		if v[0] == 0:
			addDir(cleanTitle(v[2]), v[2] + ';' + startpage + v[1], 'showVideos', '')
	xbmcplugin.endOfDirectory(pluginhandle)
	if forceViewMode:
	    xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def showVideos(params):
	name, url = params.split(';')
	if dbg: print 'open ' + url
	content = getUrl(url)
	entrycache = {}

	ins = False
	for k, v in enumerate(getFolders()):
		if v[0] == 0:
			ins = v[2] == name
		elif ins == True:
			addDir(cleanTitle(v[2]), v[2] + ';' + startpage + v[1], 'showVideos', '')

	vidrex = '(tb-.+?-videos-.+?)' if searchInMostClicked else '(tb-neueste-videos-.+?)'
	for k, (fid, cid) in enumerate(uniq(re.compile(vidrex + ',.*?contentContextId=(.+?)\.bild\.html', re.DOTALL).findall(content))):
		page, pages = 0, 0
		while page <= pages:
			url = baseurl
			url = url.replace("<fid>", fid).replace("<cid>", cid).replace("<pn>", str(page))
			if dbg: print 'open ' + url
			content = getUrl(url)
			spl = content.split('class="hentry')
			for i in range(1, len(spl), 1):
				title, url, thumb, bigthumb = getElements(spl[i])
				if dbg: print 'got title: %s, url: %s, thumb: %s, bigthumb: %s'%(title, url, thumb, bigthumb)
				if '(Bild-Plus)' in title: continue
				if not url in entrycache:
					entrycache[url] = ''
					addLink(title, url, 'playVideo', thumb, bigthumb)
			spl = content.split('href="#" data')
			for i in range(1,len(spl),1):
				match = re.compile('page=(.+?),', re.DOTALL).findall(spl[i])
				p = int(match[0]) if len(match)>0 else -1
				if p > pages:
					pages = p
			page = page +1
	xbmcplugin.endOfDirectory(pluginhandle)
	if forceViewMode:
	    xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')

def getElements(entry):
	title, url, thumb, bigthumb, date = '', '', '', '', ''
	match = re.compile('<time[^<]*>(.+?)</time>', re.DOTALL).findall(entry)
	if match:
		date = match[0].strip()
		date = date[:6]
		title = title + ' ' + date
	if 'class="premium' in entry:
	    title = title + '[COLOR=red] (Bild-Plus)[/COLOR]'
	match = re.compile('<span class="kicker">(.+?)</span>', re.DOTALL).findall(entry)
	if match:
		title = title + ' ' + cleanTitle(match[0])
	match = re.compile('<span class="headline">(.+?)</span></span>', re.DOTALL).findall(entry)
	if match:
		title2 = cleanTitle(match[0])
		title = title + ' - ' + title2
	match = re.compile('/video/(.+?)"', re.DOTALL).findall(entry)
	if match:
		url = 'http://www.bild.de/video/' + match[0].replace('.bild.html', ',view=xml.bild.xml')
	else:
	    match = re.compile('href="([^<]+?)"', re.DOTALL).findall(entry)
	    if match:
		url = 'http://www.bild.de' + match[0].replace('.bild.html', ',view=xml.bild.xml')
	match = re.compile('src="(.+?)"', re.DOTALL).findall(entry)
	if match:
		thumb = match[0]
		bigthumb = re.sub(',.*', '.bild.jpg', match[0])
	return(title, url, thumb, bigthumb)

def getFolders():
	folders = []
	match = re.compile('>BILD.TV<(.+?)</nav>', re.DOTALL).findall(getUrl(startpage))
	match = re.compile('(<li>[^<]*?<a href="[^<]+?"[^<]*?>[^<]*?</a>[^<]*?<ol.+?</ol>[^<]*?</li>)|(<li>[^<]*?<a href="[^<]+?"[^<]*?>[^<]*?</a>[^<]*?</li>)', re.DOTALL).findall(match[0])
	for i in range(0, len(match), 1):
		if match[i][0] != '':
			cats = re.compile('<a[^>]*?href="(.*?)"[^>]*?>(.+?)</a>[^<]*?<ol[^>]*?class=".*?">(.*?)</ol>', re.DOTALL).findall(match[i][0])
			for j in range(0, len(cats), 1):
				folders.append((0, cats[j][0], cats[j][1]))
				subcats = re.compile('<a[^>]*?href="(.*?)"[^>]*?>(.+?)</a>', re.DOTALL).findall(cats[j][2])
				for k in range(0, len(subcats), 1):
					folders.append((1, subcats[k][0], subcats[k][1]))
		elif match[i][1] != '':
			cats = re.compile('<a[^>]*?href="(.*?)"[^>]*?>(.+?)</a>', re.DOTALL).findall(match[i][1])
			folders.append((0, cats[0][0], cats[0][1]))
	return folders

def playVideo(url):
	content = getUrl(url)
	match = re.compile('<video src="(.+?)"', re.DOTALL).findall(content)
	if match:
	    listitem = xbmcgui.ListItem(path=match[0])
	    return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
	else:
	    xbmc.executebuiltin('Notification(Video wurde nicht gefunden., 5000)')

def cleanTitle(title):
		title = re.sub('<[^>]*>', ' ', title)
		title = re.sub('&#\d{3};', ' ', title)
		title = title.replace('&lt;','<').replace('&gt;','>').replace('&amp;','&').replace('&quot;','"').replace('&szlig;','ß').replace('&ndash;','-')
		title = title.replace('&Auml;','Ä').replace('&Uuml;','Ü').replace('&Ouml;','Ö').replace('&auml;','ä').replace('&uuml;','ü').replace('&ouml;','ö').replace('&nbsp;', ' ')
		title = title.replace('„','"').replace('“','"')
		title = re.sub('\s+', ' ', title)
		return title.strip()

def uniq(input):
	output = []
	for x in input:
		if x not in output:
			output.append(x)
	return output

def getUrl(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0')
        response = urllib2.urlopen(req,timeout=30)
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

def addLink(name, url, mode, iconimage, fanart):
	u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode)
	liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	liz.setProperty('IsPlayable', 'true')
	if useThumbAsFanart:
	    liz.setProperty('fanart_image', fanart)
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)

def addDir(name, url, mode, iconimage):
	name = '* ' + name
	u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode)
	liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)

params = parameters_string_to_dict(sys.argv[2])
mode = params.get('mode')
url = params.get('url')
if type(url)==type(str()):
  url = urllib.unquote_plus(url)

if mode == 'showVideos': showVideos(url)
elif mode == 'playVideo': playVideo(url)
else: index()