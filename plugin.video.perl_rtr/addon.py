#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib,urllib2,re,xbmcplugin,xbmcgui,sys,xbmcaddon,HTMLParser

htmlparser = HTMLParser.HTMLParser()
pluginhandle = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.perl_rtr')
forceViewMode = settings.getSetting("forceViewMode") == 'true'
ViewMode = str(settings.getSetting("ViewMode"))
baseurl = 'http://www.pearl.de'

def index():
	fillList(baseurl+'/podcast')
	addDir('Weiter im Archiv >>', '', 'showArchive', '')
	if forceViewMode: xbmc.executebuiltin("Container.SetViewMode(" + ViewMode + ")")
	xbmcplugin.endOfDirectory(pluginhandle)
	
def showArchive():
	fillList(baseurl+'/podcast/archiv.jsp')
	if forceViewMode: xbmc.executebuiltin("Container.SetViewMode(" + ViewMode + ")")
	xbmcplugin.endOfDirectory(pluginhandle)
	
def fillList(url):
	content = getUrl(url)
	match = re.compile('<div[^>]*class="box"[^>]*>(.*)<div[^>]*class="box"[^>]*>', re.DOTALL).findall(content)
	if match:
		vids = extractVideosNew(match[0])
		match = re.compile('(<img[^>]*class="bild"[^>]*>)[^<]*<strong>(.*?)</strong>', re.DOTALL).findall(match[0])
		pic = re.compile('src="(.*?)"', re.DOTALL).findall(match[0][0])
		title = clean(match[0][1])
		addDir(title, str(vids), 'showVideos', fixUrl(pic[0]))
	
	match = re.compile('<p[^>]*class="audioliste"[^>]*>[^<]*(<img[^>]*class="bild"[^>]*>)[^<]*<strong>(.*?)</strong>(.*?)</p>', re.DOTALL).findall(content)
	for each in match:
		pic = re.compile('src="(.*?)"', re.DOTALL).findall(each[0])
		title = clean(each[1])
		vids = extractVideos(each[2])
		addDir(title, str(vids), 'showVideos', fixUrl(pic[0]))
		
	match = re.compile('<p[^>]*class="videoliste"[^>]*>[^<]*(<img[^>]*class="bild"[^>]*>)[^<]*<img[^>]*>[^<]*<strong>(.*?)</strong>[^<]*<br>(.*?)</p>', re.DOTALL).findall(content)
	for each in match:
		pic = re.compile('src="(.*?)"', re.DOTALL).findall(each[0])
		title = clean(extractTitle(each[1]))
		vid = re.compile('<a[^>]*href="([^"]*videocast.php[^"]*)"[^>]*>', re.DOTALL).findall(each[2])
		addLink(title, vid[0], 'playVideo', fixUrl(pic[0]))

def extractVideosNew(txt):
	vids = []
	match = re.compile('<div[^>]*class="scrollContainer"[^>]*>(.*)$', re.DOTALL).findall(txt)
	if match:
		for each in re.compile('<p[^>]*>(.*?)</p>[^<]*<a[^>]*href="([^"]*videocast.php[^"]*)"[^>]*>', re.DOTALL).findall(match[0]):
			vids.append((enc(extractTitle(each[0])), enc(shorten(each[1]))))
	return vids

def extractVideos(txt):
	vids = []
	match = re.compile('video_klein_[a-zA-Z]+.jpg[^>]*>(.*)$', re.DOTALL).findall(txt)
	if match:
		for each in re.compile('<br>(.*?)<img[^>]*>[^<]*<a[^>]*href="([^"]*videocast.php[^"]*)"[^>]*>', re.DOTALL).findall(match[0]):
			vids.append((enc(extractTitle(each[0])), enc(shorten(each[1]))))
	return vids

def showVideos(str):
	for vid in re.compile('\([^(]*\'([^\)]*)\',[^(]*\'([^\)]*)\'\)', re.DOTALL).findall(str):
		addLink(clean(dec(vid[0])), dec(vid[1]), 'playVideo', '')
	xbmcplugin.endOfDirectory(pluginhandle)

def enc(str):
	return str.encode('hex')
	
def dec(str):
	return str.decode('hex')

def playVideo(url):
	content = getUrl(url)
	match = re.compile('<a[^>]*href="([^"]*\.mp4)"', re.DOTALL).findall(content)
	if match:
		url = url.rsplit('/',1)[0] + match[0]
		listitem = xbmcgui.ListItem(path=url)
		return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def extractTitle(s):
	s = s.replace('\n', ' ')
	s = re.sub('<[^>]*>', ' ', s)
	s = re.sub('&mdash;[ ]*[Jj]etzt[ ]*ansehen[ ]*bei', '', s)
	s = re.sub('[ ]+', ' ', s)
	return re.sub('^[ ]|[ ]$', '', s)

def clean(s):
	return htmlparser.unescape(s)
	
def fixUrl(url):
	return url if baseurl in url else baseurl+url

def shorten(url):
	match = re.compile('(.*video=.*?)&.*', re.DOTALL).findall(url)
	return match[0] if match else url

def getUrl(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
	response = urllib2.urlopen(req)
	data = response.read()
	response.close()
	return data

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

def addLink(name, url, mode, iconimage):
	u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode)
	liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	liz.setProperty('IsPlayable', 'true')
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)

def addDir(name, url, mode, iconimage):
	u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode)
	liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)

params = parameters_string_to_dict(sys.argv[2])
mode = params.get('mode')
url = params.get('url')
if type(url) == type(str()):
  url = urllib.unquote_plus(url)

if mode == 'showVideos': showVideos(url)
elif mode == 'playVideo': playVideo(url)
elif mode == 'showArchive': showArchive()
else: index()
