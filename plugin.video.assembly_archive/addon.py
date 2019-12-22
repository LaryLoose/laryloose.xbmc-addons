#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon

pluginhandle = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.assembly_archive')
translation = settings.getLocalizedString
forceViewMode = settings.getSetting("force_viewmode") == "true"
baseurl = 'http://archive.assembly.org/'
	
def index():
		content = getUrl(baseurl)
		for href,year in re.compile('class="mediacategory".*?href="([^"]+)"[^>]*><span>(.*?)</span>', re.DOTALL).findall(content):
			addDir(year,fixUrl(href),'showFolders','')
		xbmcplugin.endOfDirectory(pluginhandle)

def showFolders(url):
		content = getUrl(url)
		for href,category in re.compile('class="mediacategory"[^>]*>[^<]*<[^>]*>[^<]*<[^>]*href="([^"]+)"[^>]*>[^<]*<span>([^<]+)<', re.DOTALL).findall(content):
			addDir(cleanTitle(category),fixUrl(href),'showVideos','')
		xbmcplugin.endOfDirectory(pluginhandle)

def showVideos(url):
		content = getUrl(url)
		for href,name,img in re.compile('class="[^"]*video[^"]*"[^>]*>[^<]*<[^>]*class="[^"]*thumbnail[^"]*"[^>]*href="([^"]+)"[^>]*title="([^"]+)"[^>]*>[^<]*<picture>[^<]*<[^>]*>[^<]*<[^>]*class="[^"]*thumbnail-image[^"]*"[^>]*src="([^"]+)"[^>]*>', re.DOTALL).findall(content):
			addLink(cleanTitle(name), fixUrl(href), 'playVideo', img)
		if forceViewMode:
			xbmc.executebuiltin('Container.SetViewMode(500)')
		xbmcplugin.endOfDirectory(pluginhandle)

def cleanTitle(text):
		text = re.sub('<[^>]*>', ' ', text)
		text = re.sub('&amp;', '&', text)
		text = re.sub('&.*?;', ' ', text)
		text = re.sub('\s+', ' ', text)
		return re.sub('^\s|\s$', '', text).strip()

def fixUrl(url):
		if url in 'http://': return url
		else: return baseurl + url
	
def playVideo(url):
		content = getUrl(url)
		for youtubeID in re.compile('<[^>]*id="ytplayerembed"[^>]*src="[^"]*youtube.com/embed/([^"]+)"', re.DOTALL).findall(content):
			if xbmc.getCondVisibility("System.Platform.xbox") == True:
				fullData = "plugin://video/YouTube/?path=/root/video&action=play_video&videoid=" + youtubeID
			else:
				fullData = "plugin://plugin.video.youtube/play/?video_id=" + youtubeID
			listitem = xbmcgui.ListItem(path=fullData)
			return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def getUrl(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0')
        response = urllib2.urlopen(req,timeout=30)
        link=response.read()
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
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setProperty('IsPlayable', 'true')
        return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)

def addDir(name,url,mode,iconimage):
		u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
		liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
		liz.setInfo( type="Video", infoLabels={ "Title": name } )
		return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)

params=parameters_string_to_dict(sys.argv[2])
mode=params.get('mode')
url=params.get('url')
if type(url )== type(str()) : url = urllib.unquote_plus(url)

if mode == 'showFolders': showFolders(url)
elif mode == 'showVideos': showVideos(url)
elif mode == 'playVideo': playVideo(url)
else: index()
