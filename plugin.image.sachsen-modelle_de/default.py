import urllib, urllib2, re, xbmcplugin, xbmcgui, sys, xbmcaddon

thisPlugin = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.sachsen-modelle_de')
translation = settings.getLocalizedString
forceViewMode = settings.getSetting("force_viewmode") == "true"
useCacheToDisc = settings.getSetting("cache_to_disc") == "true"
  
baseurl = 'http://sachsen-modelle.de/release'
thumburl = baseurl + '/galerie/bilder/<album>/<picname>.jpg'
indexurl = baseurl + '/galerie/albums.php'

def index():
		print ('get index from ' + indexurl)
		content = getUrl(indexurl)
		albums = re.compile('<a href="([^<]*?)">[^<]*<img[^<]*src=([^<]*?) .*?<span class="title">(.*?)</span>.*?<span class="fineprint">(.*?)</span>', re.DOTALL).findall(content)
		for a in range(0, len(albums), 1):
			lastchange = re.compile('nderung(.*?[0-9]{4})', re.DOTALL).findall(albums[a][3])
			piccount = re.compile('beinhaltet (.*?) Bilder\.', re.DOTALL).findall(albums[a][3])
			print albums[a][2]
			addDir(clean(albums[a][2]) + ' [COLOR=blue](' + piccount[0] + ')[/COLOR] ' + lastchange[0], albums[a][0], 'showFolders', albums[a][1].replace('.highlight','.sized'))
		xbmcplugin.endOfDirectory(thisPlugin)

def showFolders(url):
		print ('get folders from ' + url)
		content = getUrl(url)
		albums = re.compile('<a href="([^<]*?)">[^<]*<img[^<]*src=([^<]*?) ', re.DOTALL).findall(content)
		captions = re.compile('<span class="caption"><b>([^<]*)<', re.DOTALL).findall(content)
		next = re.compile('<a href=([^<]*?)><img[^<]*nav_next.gif', re.DOTALL).findall(content)
		for a in range(0, len(albums), 1):
			title = captions[a] if captions[a] else 'no name'
			thumb = re.sub('\.thumb', '.sized', albums[a][1])
			addDir(clean(title), albums[a][0], 'showPictures', thumb)
		if next:
			addDir('Next', next[0], 'showFolders', '')
		if forceViewMode: xbmc.executebuiltin('Container.SetViewMode(500)')
		xbmcplugin.endOfDirectory(thisPlugin)

def showPictures(url):
		print('get pictures from ' + url)
		content = getUrl(url)
		pictures = re.compile('<a href="[^<]*view_photo.php\?set_albumName=(.*?)&id=(.*?)">[^<]*<img', re.DOTALL).findall(content)
		captions = re.compile('<span class="caption">([^<]*)<', re.DOTALL).findall(content)
		for p in range(0, len(pictures), 1):
			title = captions[p] if captions[p] else pictures[p][1]
			thumb = re.sub('<album>', pictures[p][0], thumburl)
			thumb = re.sub('<picname>', pictures[p][1], thumb)
			pic = re.sub('\.sized', '', thumb)
			addPicture(clean(title), pic, thumb)
		if forceViewMode: xbmc.executebuiltin('Container.SetViewMode(500)')
		xbmcplugin.endOfDirectory(handle=thisPlugin, succeeded=True, updateListing=False, cacheToDisc=useCacheToDisc)

def clean(s):
	s = re.sub('[\r\n]|<[^>]*>',' ',s)
	s = re.sub('[ ]+', ' ', s)
	return s.strip().decode("windows-1252")

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

params = parameters_string_to_dict(sys.argv[2])
mode = params.get('mode')
url = params.get('url')
if type(url)==type(str()): url = urllib.unquote_plus(url)

if mode == 'showFolders': showFolders(url)
elif mode == 'showPictures': showPictures(url)
else: index()