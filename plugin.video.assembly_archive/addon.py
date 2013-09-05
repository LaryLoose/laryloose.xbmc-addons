#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,base64

pluginhandle = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.assembly_archive')
translation = settings.getLocalizedString
forceViewMode = settings.getSetting("force_viewmode") == "true"

def index():
		content = getUrl('http://archive.assembly.org/')
		years = re.compile('class="mediacategory".*?href="(.*?)"[^<]*><span>(.*?)</span>', re.DOTALL).findall(content)
		for i in range(0, len(years), 1):
			addDir(years[i][1],years[i][0],'showFolders','')
		xbmcplugin.endOfDirectory(pluginhandle)

def showFolders(url):
		content = getUrl(url)
		categories = re.compile('class="mediacategory".*?href="(.*?)"[^<]*>(.*?)</a>', re.DOTALL).findall(content)
		for i in range(0, len(categories), 1):
			addDir(cleanTitle(categories[i][1]),categories[i][0],'showVideos','')
		xbmcplugin.endOfDirectory(pluginhandle)

def showVideos(url):
		content = getUrl(url)
		videos = re.compile('class="video".*?href="(.*?)"[^<]*>[^<]*<img[^<]*src="(.*?)"[^<]*alt="(.*?)"[^<]*>[^<]*<span class="by">(.*?)</span>', re.DOTALL).findall(content)
		for i in range(0, len(videos), 1):
			print(videos[i])
			addLink('"' + cleanTitle(videos[i][2]) + '" by ' + cleanTitle(videos[i][3]), videos[i][0], 'playVideo', videos[i][1])
		if forceViewMode:
			xbmc.executebuiltin('Container.SetViewMode(500)')
		xbmcplugin.endOfDirectory(pluginhandle)

def cleanTitle(text):
		text = re.sub('<[^>]*>', ' ', text)
		text = re.sub('&amp;', '&', text)
		text = re.sub('&.*?;', ' ', text)
		text = re.sub('\s+', ' ', text)
		text = re.sub('^\s|\s$', '', text)
		return text

def playVideo(url):
        content = getUrl(url)
        match = re.compile('src="http://www.youtube.com/embed/(.+?)\\?', re.DOTALL).findall(content)
        youtubeID = match[0]
        if xbmc.getCondVisibility("System.Platform.xbox") == True:
          fullData = "plugin://video/YouTube/?path=/root/video&action=play_video&videoid=" + youtubeID
        else:
          fullData = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=" + youtubeID
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
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setProperty('IsPlayable', 'true')
        ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)
        return ok

def addDir(name,url,mode,iconimage):
		u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
		ok=True
		liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
		liz.setInfo( type="Video", infoLabels={ "Title": name } )
		ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
		return ok

params=parameters_string_to_dict(sys.argv[2])
mode=params.get('mode')
url=params.get('url')
if type(url)==type(str()):
  url=urllib.unquote_plus(url)

if mode == 'showFolders':
    showFolders(url)
elif mode == 'showVideos':
    showVideos(url)
elif mode == 'playVideo':
    playVideo(url)
else:
    index()
