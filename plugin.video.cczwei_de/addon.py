#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib, urllib2, re, xbmcplugin, xbmcgui, sys, xbmcaddon, time
from datetime import datetime

pluginhandle = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.cczwei_de')

def index():
	content = getUrl('http://www.cczwei.de/index.php?id=tvissuearchive')
	items = re.compile('<item>.*?</item>', re.DOTALL).findall(content)
	for date, url, issue, desc in re.compile('CLASS="header">([^<]+)<.*?CLASS="text"><a href="([^"]+)"><b>([^<]*)</b>.*?>.*?<ul><li><a[^>]*>(.*?)</a></li></ul>', re.DOTALL|re.I).findall(content):
		#name = date + ' ' + issue + ' ' + clean(desc)
		name = date + ' ' + clean(desc)
		addLink(name, url, 'playVideo', '')
	xbmcplugin.endOfDirectory(pluginhandle)

def playVideo(url):
	if 'www.cczwei.de' not in url: url = 'http://www.cczwei.de/' + url
	print url
	content = getUrl(url)
	for video in re.compile('href="([^"]*.mp4)"', re.DOTALL).findall(content):
		listitem = xbmcgui.ListItem(path = video)
		return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def clean(s):
	try: s = htmlparser.unescape(s)
	except: print "could not unescape string '%s'"%(s)
	s = re.sub('<[^>]*>', ',', s)
	s = s.replace('_', ' ')
	s = re.sub('[ ]+', ' ', s)
	s = re.sub('[,]+', ', ', s)
	for hit in set(re.findall("&#\d+;", s)):
		try: s = s.replace(hit, unichr(int(hit[2:-1])))
		except ValueError: pass
	return s.strip('\n').strip()

def getUrl(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0')
	response = urllib2.urlopen(req, timeout=30)
	data = response.read()
	response.close()
	return data.decode('utf-8')

def addLink(name, url, mode, iconimage):
	u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
	liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	liz.setProperty('IsPlayable', 'true')
	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz)

def parameters_string_to_dict(parameters):
        paramDict = {}
        if parameters:
            paramPairs = parameters[1:].split("&")
            for paramsPair in paramPairs:
                paramSplits = paramsPair.split('=')
                if (len(paramSplits)) == 2:
                    paramDict[paramSplits[0]] = paramSplits[1]
        return paramDict

params = parameters_string_to_dict(sys.argv[2])
mode = params.get('mode')
url = params.get('url')
if type(url) == type(str()): url = urllib.unquote_plus(url)

print sys.argv[2]
if mode == 'playVideo': playVideo(url)
else: index()

