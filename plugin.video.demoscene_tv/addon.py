#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64

pluginhandle = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.demoscene_tv')
translation = settings.getLocalizedString
forceViewMode = settings.getSetting("force_viewmode") == "true"
hdQuality = settings.getSetting("hd_quality") == "true"
maxItems = (int(settings.getSetting("items_per_page"))+1)*20

def index():
	addDir(translation(30001),'plateform|http://www.demoscene.tv/page.php?id=172&lang=uk&vsmaction=listingprod&vsmprodsearch=1','showSearch','')
	addDir(translation(30002),'type|http://www.demoscene.tv/page.php?id=172&lang=uk&vsmaction=listingprod&vsmprodsearch=1','showSearch','')
	addDir(translation(30003),'year|http://www.demoscene.tv/page.php?id=172&lang=uk&vsmaction=listingprod&vsmprodsearch=1','showSearch','')
	addDir(translation(30004),'http://www.demoscene.tv/page.php?id=614&lang=uk&mode=mostviewed&offset=0','showFolders','')
	addDir(translation(30005),'http://www.demoscene.tv/page.php?id=614&lang=uk&mode=lastadded&offset=0','showFolders','')
	addDir(translation(30006),'http://www.demoscene.tv/page.php?id=614&lang=uk&mode=mostprod&offset=0','showFolders','')
	addDir(translation(30007),'http://www.demoscene.tv/page.php?id=614&lang=uk&mode=alphabetic&offset=0','showFolders','')
	addDir(translation(30010),'http://www.demoscene.tv/page.php?id=172&lang=uk&vsmaction=listingTopRatingProd&offset=0','showVideos','')
	addDir(translation(30009),'http://www.demoscene.tv/page.php?id=172&lang=uk&vsmaction=listingTopAlltimeViewedProd&offset=0','showVideos','')
	addDir(translation(30011),'http://www.demoscene.tv/page.php?id=172&lang=uk&vsmaction=listingTopMonthViewedProd&offset=0','showVideos','')
	addDir(translation(30012),'http://www.demoscene.tv/page.php?id=172&lang=uk&vsmaction=listingTopWeekViewedProd&offset=0','showVideos','')
	addDir(translation(30013),'http://www.demoscene.tv/page.php?id=172&lang=uk&vsmaction=listingLastAddedProd&offset=0','showVideos','')
	addDir(translation(30014),'http://www.demoscene.tv/page.php?id=172&lang=uk&vsmaction=listingLastReleasedProd&offset=0','showVideos','')
	xbmcplugin.endOfDirectory(pluginhandle)

def showSearch(param):
	type,url = param.split('|')
	content = getUrl(url)
	select = re.compile('<select[^<]*name="vsmprodsearch_' + type + '"[^<]*>(.*?)</select>', re.DOTALL).findall(content)
	if select is not None:
		options = re.compile('<option value="(\d+)">(.*?)</option>', re.DOTALL).findall(select[0])
		for i in range(0, len(options), 1):
			newurl = url + '&vsmprodsearch_' + type + '=' + options[i][0]
			addDir(options[i][1], newurl, 'showVideos', '')
	xbmcplugin.endOfDirectory(pluginhandle)

def showFolders(url):
	match = re.match(".*offset=(\d+)", url)
	offset = int(match.group(1)) if match is not None else 0
	count, test = 0, 1
	while test == 1:
		test = 0
		content = getUrl(url)
		match = re.compile('<td class="vsmchannelgrouptablecell"[^<]*><a href="(.*?)"[^<]*><img src="(.*?)"[^<]*>.*?style="border: 0px;">(.*?)</a><br/>(.*?)</div>', re.DOTALL).findall(content)
		for i in range(0, len(match), 1):
			title = match[i][2] if not match[i][3] else match[i][3] + ' - ' + match[i][2]
			print(title)
			addDir(title, match[i][0], 'showVideos', match[i][1])
			test = 1
		count += 20
		url = re.sub("offset=.*$", "offset="+str(count+offset), url)
		if count >= maxItems:
			addDir(translation(30008), url, 'showFolders', '')
			test = 0
	xbmcplugin.endOfDirectory(pluginhandle)

def showVideos(url):
	match = re.match(".*offset=(\d+)$", url)
	offset = int(match.group(1)) if match is not None else 0
	if re.match("http://www.demoscene\.tv/", url) is None:
		url = 'http://www.demoscene.tv/' + url
	if re.match("offset=", url) is None:
		url += '&offset=0'
	url = url.replace('&amp;','&') + '&displayProdGroup=true'
	count, test = 0, 1
	print(url)
	while test == 1:
		test = 0
		content = getUrl(url)
		print(url)
		match = re.compile('class="vsmmainproductiontable".*?<img src="(.*?)".*?class="vsm_viewcurrentprodtitle"[^<]*><a href="(.*?)"[^<]*>(.*?)</a>(.*?)</td>', re.DOTALL).findall(content)
		for i in range(0, len(match), 1):
			desc = re.sub('<[^>]*>', ' ', match[i][3])
			desc = re.sub('&nbsp;', ' ', desc)
			desc = re.sub('\s+', ' ', desc)
			addLink('"' + match[i][2] + '" ' + desc, match[i][1], 'playVideo', match[i][0])
			test = 1
		count += 20
		url = re.sub("offset=.*$", "offset="+str(count+offset), url)
		if count >= maxItems:
			print(url)
			addDir(translation(30008), url, 'showVideos', '')
			test = 0
	if forceViewMode:
		xbmc.executebuiltin('Container.SetViewMode(500)')
	xbmcplugin.endOfDirectory(pluginhandle)

def pickBestVideo(urls):
	quals = ['.*(hd|hq)[^/]*mp4','.*(hd|hq)[^/]*flv','.*flv'] if hdQuality else ['.*flv']
	for q in range(0, len(quals), 1):
		for i in range(0, len(urls), 1):
			match = re.match(quals[q], urls[i])
			if match is not None:
				return urls[i]
	return urls[0]

def playVideo(url):
	if re.match("http://www.demoscene\.tv/", url) is None:
		url = 'http://www.demoscene.tv/' + url
	url = url.replace('&amp;','&')
	content = getUrl(url)
	views = re.compile('class="vsm_viewprodfile"[^<]*>(.*?)</font>', re.DOTALL).findall(content)
	match = re.compile('<a[^<]*href="(.*?)"[^<]*>', re.DOTALL).findall(views[0])
	for i in range(0, len(match), 1):
		match[i] = re.sub('^.*?\'', '', match[i].lower())
		match[i] = re.sub('\'.*$', '', match[i])
	url = pickBestVideo(match)
	listitem = xbmcgui.ListItem(path=url)
	return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

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

def addLink(name,url,mode,iconimage):
	u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
	liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	liz.setProperty('IsPlayable', 'true')
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)

def addDir(name,url,mode,iconimage):
	u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
	liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

params=parameters_string_to_dict(sys.argv[2])
mode=params.get('mode')
url=params.get('url')
if type(url)==type(str()):
  url=urllib.unquote_plus(url)

if mode == 'showFolders':
    showFolders(url)
elif mode == 'showVideos':
    showVideos(url)
elif mode == 'showSearch':
    showSearch(url)
elif mode == 'playVideo':
    playVideo(url)
else:
    index()
