# -*- coding: utf-8 -*-
import urllib,re,xbmcplugin,xbmcgui,xbmcaddon,os,xbmc,urllib2

pluginhandle = int(sys.argv[1])
addon = xbmcaddon.Addon(id='plugin.video.streamoase_ll')
mainurl = 'http://stream-oase.tv'

home = addon.getAddonInfo('path').decode('utf-8')
image = xbmc.translatePath(os.path.join(home, 'Logo.png'))
next =  xbmc.translatePath(os.path.join(home, 'Next.png'))
#fanart = xbmc.translatePath(os.path.join(home, 'fanart.jpg'))
#image = 'http://stream-oase.tv/media/com_allvideoshare/action/Logo_HD.png'

def CATEGORIES():
	caturl = mainurl+'/index.php/hd-oase/category/'
	addDir('Neu', mainurl+'/index.php/hd-oase/video/latest', 1, image)
	addDir('Top 30 HD Filme', mainurl, 5, image)
	addDir('Action', caturl+'/action', 1, image)
	addDir('Abenteuer', caturl+'/abenteuer', 1, image)
	addDir('Drama', caturl+'/drama', 1, image)
	addDir('Krieg', caturl+'/krieg',1,image)
	addDir('Thriller', caturl+'/thriller',1,image)
	addDir('Horror', caturl+'/horror',1,image)
	addDir('Komoedie', caturl+'/komoedie',1,image)
	addDir('Zeichentrick', caturl+'/zeichentrick',1,image)
	addDir('Sci-Fi', caturl+'/sci-fi',1,image)
	addDir('Dokus', caturl+'/doku-s',1,image)
	addDir('LiveStreamOase', mainurl, 6, image)
	addDir('Suche', mainurl, 3, '')

def Index(url):
	content = getUrl(url)
	pagination = re.compile('"pagination-active".*?href="(.*?).?title').findall(content)
	for find in re.compile('<div id="avs_gallery">(.*?)<div style="clear:both"></div>', re.DOTALL).findall(content):
		for url, thumbnail, name in re.findall('<a ondragstart="return false;" href="(.*?)">.*?class="image" src="(.*?)".*?<span class="title">(.*?)</span>',find, re.DOTALL):
			url = mainurl + url
			addLink(name, url, 2, thumbnail)
	for nexturl in pagination:
		next_page = mainurl + nexturl	  
		addDir('Next', next_page, 1, image)    
	xbmcplugin.endOfDirectory(pluginhandle)

def Top30(url):
	content = getUrl(url)
	popurl = mainurl + '/index.php/component/allvideoshare/video/popular/'
	for url,thumbnail,name in re.compile('<a ondragstart="return false;" href="/index.php/component/allvideoshare/video/popular/(.*?)"> \r\n    \t.*?\r\n.*?class="image" src="(.*?)" width="86" height="125" title="Click to View : (.*?)" border="0" />').findall(content):
		url = popurl + url
		addLink(name, url, 2, thumbnail)
			
def getStream_Uploadnet(url):
	from t0mm0.common.net import Net
	net = Net()
	data = net.http_GET(url).content
	info = {}
	for i in re.finditer('<input[^>]*name="([^"]*)"[^>]*value="([^">]*)"[^>]*>', data):
		info[i.group(1)] = i.group(2)
	if len(info) == 0: 
		print 'Error: could not find login data'
		return
	data = net.http_POST(url, info).content
	stream_url = re.findall('file["\']*:[^"\']*["\']([^"\']*)["\']', data)
	if stream_url:
		return stream_url[0]

def getStream_Divxpress(url):
	from t0mm0.common.net import Net
	from jsunpacker import cJsUnpacker
	net = Net()
	data = net.http_GET(url).content
	info = {}
	for i in re.finditer('<input[^>]*name="([^"]*)"[^>]*value="([^">]*)"[^>]*>', data):
		info[i.group(1)] = i.group(2)
	if len(info) == 0: 
		print 'Error: could not find login data'
		return
	data = net.http_POST(url, info).content
	for packedjava in re.findall('javascript["\']*>eval.function(.*?)</script>', data, re.S|re.DOTALL):
		sUnpacked = cJsUnpacker().unpackByString(packedjava)
		stream_url = re.findall("file','(.*?)'", sUnpacked)
	if stream_url:
		return stream_url[0]
	
def getStream_Mightyupload(url):
	data = getUrl(url)
	if re.match('.*File was deleted', data, re.S|re.I):
		xbmc.executebuiltin("XBMC.Notification(Fehler!, Datei wurde geloescht, 4000)")
		return
	stream_url = re.findall('file["\']*:[^"\']*["\']([^"\']*)["\']', data)
	if stream_url:
		return stream_url[0]

def selectVideoDialog(videos):
	titles = []
	for i in range(0, len(videos)):
		print videos[i][0]
		titles.append(videos[i][0])
	idx = xbmcgui.Dialog().select("", titles)
	return videos[idx][1]
	
def VIDEOLINKS(url):
	content = getUrl(url)
	players = []
	for match in re.compile('(http://www.uploadnetwork.eu/embed-.*?.html)').findall(content):
		print "found player: " + match
		players.append(('Uploadnetwork', getStream_Uploadnet(match)))
	for match in re.compile('(http://www.mightyupload.com/embed-.*?.html)').findall(content):
		print "found player: " + match
		players.append(('Uploadnetwork', getStream_Mightyupload(match)))
	for match in re.compile('(http://www.divxpress.com/embed-.*?.html)').findall(content):
		print "found player: " + match
		players.append(('Uploadnetwork', getStream_Divxpress(match)))
	
	lv = len(players)
	if lv == 0:
		xbmc.executebuiltin("XBMC.Notification(Fehler!, Kein passender Player gefunden, 4000)")
		print content
		return
	else:
		stream_url = selectVideoDialog(players) if lv > 1 else players[0][1]
		listitem = xbmcgui.ListItem(path = stream_url)
		return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)

def LiveStreamcat():
   addDir('Live Film Oase','http://stream-oase.tv',7,image)
   addDir('Live Serien Oase','http://stream-oase.tv',8,image)
   addLink('FB-CL','http://stream-oase.tv/index.php/oasen-livestreams/fb-cl',9,image)

def LiveFilmcat():
   addLink("Knallfrosch's Filme Mix",'http://stream-oase.tv/index.php/oasen-livestreams/live-film-oase/knallis-filme-mix',20,image)
   addDir("J2p4evr",'http://stream-oase.tv',10,image)
   addDir("Deutsches Kino",'http://stream-oase.tv',11,image)
   addLink('Edels Movies','http://stream-oase.tv/index.php/oasen-livestreams/live-film-oase/edels-movies',20,image)
   addLink('LoseBoss Movie World','http://stream-oase.tv/index.php/oasen-livestreams/live-film-oase/loseboss-movie-world',20,image)
   addLink('End78 Movies','http://stream-oase.tv/index.php/oasen-livestreams/live-film-oase/end78-movies',20,image)
   addLink("Hunter's Movies",'http://stream-oase.tv/index.php/oasen-livestreams/live-film-oase/hunters-movies',20,image)
   addLink("Zoocompany's Music & Movies",'http://stream-oase.tv/index.php/oasen-livestreams/live-film-oase/zoocompany-s-musik-movie-channel',20,image)
   addLink("Untouchable's Movie Channel",'http://stream-oase.tv/index.php/oasen-livestreams/live-film-oase/untouchable-s-movie-channel',20,image)
   addLink("SGSII Movies",'http://stream-oase.tv/index.php/oasen-livestreams/live-film-oase/sgsii-movies-serien/sgsii-movies',20,image)
   addLink("FunTV Movies",'http://stream-oase.tv/index.php/oasen-livestreams/live-film-oase/funtv/funtv-movies',20,image)
   addLink("FunTV Zeichentrick",'http://stream-oase.tv/index.php/oasen-livestreams/live-film-oase/funtv/funtv-zeichentrick',20,image)

def J2pcat():
	addLink("j2P's HD",'http://stream-oase.tv/index.php/oasen-livestreams/live-film-oase/j2p4evr/j2ps-hd',20,image)
	addLink("j2P's Movies & Series",'http://stream-oase.tv/index.php/oasen-livestreams/live-film-oase/j2p4evr/j2p-s-movies-series',20,image)

def ball(url):
	playurl='http://iphone-streaming.ustream.tv/uhls/%s/streams/live/iphone/playlist.m3u8'
	content=urllib2.urlopen(url).read()
	if content:
	 match=re.search('http://www.ustream.tv/embed/(.*?)\?v', content, re.S)
	 urlid=match.group(1)
	 url=playurl % urlid
	 listitem = xbmcgui.ListItem(path=url)
	 xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
	 xbmc.sleep(10000)
	 if xbmc.Player().isPlaying() == True and int(xbmc.Player().getTime()) == 0:
		xbmc.Player().pause()
	else:
	 print 'zur Zeit keine Streams vorhanden' 

def deutschcat():
	addLink("Deutsches Kino Stream 1",'http://stream-oase.tv/index.php/oasen-livestreams/live-film-oase/deutsches-kino/deutsches-kino-stream1',20,image)

def seriencat():
	addLink("Himym HD",'http://stream-oase.tv/index.php/oasen-livestreams/live-serien-oase/streamoase-serien/streamoase-himym',20,image)
	addLink("Sons of Anarchy",'http://stream-oase.tv/index.php/oasen-livestreams/live-serien-oase/streamoase-serien/streamoase-sons-of-anarchy',20,image)
	addLink("Taahm",'http://stream-oase.tv/index.php/oasen-livestreams/live-serien-oase/streamoase-serien/streamoase-taahm',20,image)
	addLink('Supernatural','http://stream-oase.tv/index.php/oasen-livestreams/live-serien-oase/streamoase-serien/streamoase-supernatural',20,image)
	addLink('The Walking Dead HD','http://stream-oase.tv/index.php/oasen-livestreams/live-serien-oase/streamoase-serien/the-walking-dead-hd',20,image)
	addLink('SGSII Ein Käfig voller Helden','http://stream-oase.tv/index.php/oasen-livestreams/live-serien-oase/streamoase-serien/sgsii-ein-kaefig-voller-helden',20,image)
	addLink("Falling Skies HD",'http://stream-oase.tv/index.php/oasen-livestreams/live-serien-oase/streamoase-serien/falling-skies-hd',20,image)
	addLink("The Big Bang Theory",'http://stream-oase.tv/index.php/oasen-livestreams/live-serien-oase/streamoase-serien/the-big-bang-theory',20,image)
	addLink("Desperate Housewives",'http://stream-oase.tv/index.php/oasen-livestreams/live-serien-oase/streamoase-serien/desperate-housewives',20,image)
	addLink("Die wilden Siebziger",'http://stream-oase.tv/index.php/oasen-livestreams/live-serien-oase/streamoase-serien/die-wilden-siebziger',20,image)
	addLink("SGII Lost",'http://stream-oase.tv/index.php/oasen-livestreams/live-serien-oase/streamoase-serien/sgsii-lost',20,image)

def parseVeetle(url):
   import json
   decode = 'http://tvmpt.x10.mx/fightnight/decode.php?id='
   content = getUrl(url)
   print content
   match = re.search('src="http://veetle.com/index.php/widget/index/(.*?)/0/true/default/false"', content)
   testid = match.group(1)
   url = decode + str(testid)
   content = urllib2.urlopen(url).read()
   test = 'm' + content + 'm'
   match = re.search('m (.*?) m', test)
   veetleid = match.group(1)
   url = 'http://www.veetle.com/index.php/channel/ajaxStreamLocation/%s/flash' % veetleid
   stream = json.loads(urllib2.urlopen(url).read())
   status = stream['success']
   if status == True:
	 url = stream['payload']
	 listitem = xbmcgui.ListItem(path = url)
	 xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
	 xbmc.sleep(5000)
	 if xbmc.Player().isPlaying() == True and int(xbmc.Player().getTime()) == 0:
	   xbmc.Player().pause()
   else:
	 xbmc.executebuiltin("XBMC.Notification(Zur Zeit kein Streams vorhanden)")
		
def getUrl(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; rv:16.0) Gecko/20100101 Firefox/16.0')
	response = urllib2.urlopen(req)
	data = response.read()
	response.close()
	return data
		
def MovieSearch(url):
	import mechanize
	search_entered = search()
	browser = mechanize.Browser(factory = mechanize.RobustFactory())
	browser.set_handle_robots(False)
	browser.open(mainurl)
	for form in browser.forms():
	  print "Form name:", form.name
	  print form 
	browser.select_form("hsearch")           
	#browser.select_form(nr=0)
	browser.form["avssearch"] = search_entered   
	browser.submit()					
	html = browser.response().read()
	#print html
	for find in re.compile('<div id="avs_gallery">(.*?)<div style="clear:both"></div>', re.DOTALL).findall(html):
	  for url, thumb, title in re.findall('<a ondragstart="return false;" href="(.*?)">.*?class="image" src="(.*?)".*?<span class="title">(.*?)</span>',find, re.DOTALL):
		url = mainurl + url
	addLink(title, url, 2, thumb)

def search():
	search_entered = ''
	keyboard = xbmc.Keyboard(search_entered, 'Suche HD-Filme')
	keyboard.doModal()
	if keyboard.isConfirmed():
		search_entered = keyboard.getText()#.replace(' ','+')  # sometimes you need to replace spaces with + or %20
		if search_entered == None:
			return False         
	return search_entered		

def get_params():
	param=[]
	paramstring=sys.argv[2]
	if len(paramstring)>=2:
			params=sys.argv[2]
			cleanedparams=params.replace('?','')
			if (params[len(params)-1]=='/'):
					params=params[0:len(params)-2]
			pairsofparams=cleanedparams.split('&')
			param={}
			for i in range(len(pairsofparams)):
					splitparams={}
					splitparams=pairsofparams[i].split('=')
					if (len(splitparams))==2:
							param[splitparams[0]]=splitparams[1]
							
	return param

def addLink(name, url, mode, iconimage):
	u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode)
	liz = xbmcgui.ListItem(name, iconImage = "DefaultVideo.png", thumbnailImage = iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	liz.setProperty('IsPlayable', 'true')
	#liz.setProperty('fanart_image', fanart)
	return xbmcplugin.addDirectoryItem(handle = pluginhandle, url = u, listitem = liz)

def addDir(name, url, mode, iconimage):
	u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name)
	liz = xbmcgui.ListItem(name, iconImage = "DefaultFolder.png", thumbnailImage = iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	#liz.setProperty('fanart_image', fanart)
	return xbmcplugin.addDirectoryItem(handle = pluginhandle, url = u, listitem = liz, isFolder = True)

params = get_params()
url = None
name = None
mode = None

try: url = urllib.unquote_plus(params["url"])
except: pass
try: name = urllib.unquote_plus(params["name"])
except: pass
try: mode = int(params["mode"])
except: pass

#print "Mode: " + str(mode)
#print "URL: " + str(url)
#print "Name: " + str(name)

if mode == None or url == None or len(url) < 1: CATEGORIES()      
elif mode == 1: Index(url)  
elif mode == 2: VIDEOLINKS(url)
elif mode == 3: MovieSearch(url)
#elif mode == 4: Index1(url)
elif mode == 5: Top30(url)
elif mode == 6: LiveStreamcat()
elif mode == 7: LiveFilmcat()
elif mode == 8: seriencat()
elif mode == 9: ball(url)
elif mode == 10: J2pcat()
elif mode == 11: deutschcat()
elif mode == 20: parseVeetle(url)		

xbmcplugin.endOfDirectory(int(sys.argv[1]))
