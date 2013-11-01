#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib2, re, xbmcplugin, xbmcgui, sys, xbmcaddon, time
from datetime import datetime

pluginhandle = int(sys.argv[1])
settings = xbmcaddon.Addon(id='plugin.video.cczwei_de')
rssurl = 'http://www.cczwei.de/rss_tvissues_all.php'

def showVideos(url):
	content = getUrl(url)
	items = re.compile('<item>.*?</item>', re.DOTALL).findall(content)
	for i in range(0, len(items), 1):
		#title = re.compile('<title>(.*?)</title>', re.DOTALL).findall(items[i])[0]
		date = re.compile('<pubDate>.{5}(.{11}).*</pubDate>', re.DOTALL).findall(items[i])[0]
		desc = re.compile('<description>(.*?)</description>', re.DOTALL).findall(items[i])[0]
		video = re.compile('<enclosure url="(.*?)"[^>]*/>', re.DOTALL).findall(items[i])[0]
		dt = datetime(*(time.strptime(date, '%d %b %Y')[0:6]))
		addLink(dt.strftime('%d.%m.%Y') + ': ' + cleanDesc(desc), video, '')
	xbmcplugin.endOfDirectory(pluginhandle)

def cleanTitle(text):
	text = re.sub('CC2-NRWTV| - ', '', text)
	return re.sub('^\s|\s$', '', text)

def cleanDesc(text):
	text = re.sub('Heute:|CC2:|\r|http.*', '', text)
	return re.sub('^\s|\s$', '', text)

def getUrl(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0')
	response = urllib2.urlopen(req, timeout=30)
	link = response.read()
	response.close()
	return link

def addLink(name, url, iconimage):
	liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	liz.setProperty('IsPlayable', 'true')
	return xbmcplugin.addDirectoryItem(handle=pluginhandle,url=url,listitem=liz)

showVideos(rssurl)

