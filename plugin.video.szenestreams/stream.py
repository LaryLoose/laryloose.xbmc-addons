import re, urllib2, cookielib, time, xbmcgui, socket, xbmc, os
from urllib2 import Request, URLError, urlopen as urlopen2
from urlparse import parse_qs
from urllib import quote, urlencode
from urllib import quote, unquote_plus, unquote, urlencode
from httplib import HTTPConnection, CannotSendRequest, BadStatusLine, HTTPException
from socket import gaierror, error
from t0mm0.common.net import Net
from jsunpacker import cJsUnpacker

COOKIEFILE = xbmc.translatePath( 'special://temp/dabdate_cookie.lwp' )

cj = cookielib.LWPCookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
urllib2.install_opener(opener)
if os.path.isfile(COOKIEFILE):
    cj.load(COOKIEFILE)
    xbmc.log( "Cookie is loaded", xbmc.LOGINFO )
xbmc.log( "Cookie is set, " + COOKIEFILE, xbmc.LOGINFO )

hosterlist = [
	('youtube', '.*www\.youtube\.com'),
	('putlocker', '.*www\.putlocker\.com/(?:file|embed)/'),
	('sockshare', '.*www\.sockshare\.com/(?:file|embed)/'),
	('videoslasher', '.*www\.videoslasher\.com/embed/'),
	('faststream', '.*faststream\.in'),
	('flashx', '.*flashx\.tv'),
	('vk', '.*vk\.(me|com)/'),
	('streamcloud', '.*streamcloud\.eu'),
	('vidstream', '.*vidstream\.in'),
	('xvidstage', '.*xvidstage\.com'),
	('nowvideo', '.*nowvideo\.(?:eu|sx)'),
	('movshare', '.*movshare\.net'),
	('divxstage', '.*(?:embed\.divxstage\.eu|divxstage\.eu/video)'),
	('videoweed', '.*videoweed\.es'),
	('novamov', '.*novamov\.com'),
	('primeshare', '.*primeshare'),
	('videomega', '.*videomega\.tv'),
	('bitshare', '.*bitshare\.com'),
	('movreel', '.*movreel\.com'),
	('uploadc', '.*uploadc\.com'),
	('youwatch', '.*youwatch\.org'),
	('yandex', '.*yandex\.ru'),
#	('K1no HD', '.*[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}'),
	('sharedsx', '.*shared\.sx'),
	('vivosx', '.*vivo\.sx'),
	('cloudyvideos', '.*cloudyvideos\.com'),
	('vidx', '.*vidx\.to')]


std_headers = {
	'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
	'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
	'Accept-Language': 'en-us,en;q=0.5',
}

class get_stream_link:

	def __init__(self):
		#self._callback = None
		self.net = Net()

	def get_stream(self, link):
		hoster = self.get_hostername(link)
		if   hoster == 'putlocker': return self.streamPutlockerSockshare(link, 'putlocker')
		elif hoster == 'sockshare': return self.streamPutlockerSockshare(link, 'sockshare')
		elif hoster == 'youtube': return self.youtube(link)
		elif hoster == 'videoslasher': return self.videoslaher(link)
		elif hoster == 'faststream': return self.generic1(link, 'Faststream', 10, 0)
		elif hoster == 'flashx': return self.flashx(link)
		elif hoster == 'vk': return self.vk(link)
		elif hoster == 'streamcloud': return self.streamcloud(link)
		elif hoster == 'vidstream': return self.vidstream(link)
		elif hoster == 'xvidstage': return self.xvidstage(link)
		elif hoster == 'videoweed': return self.videoweed(link)
		elif hoster == 'nowvideo': return self.generic2(link)
		elif hoster == 'movshare': return self.generic2(link)
		elif hoster == 'divxstage': return self.generic2(link)
		elif hoster == 'novamov': return self.generic2(link)
		elif hoster == 'primeshare': return self.primeshare(link)
		elif hoster == 'videomega': return self.videomega(link)
		elif hoster == 'bitshare': return self.bitshare(link)
		elif hoster == 'movreel': return self.movreel(link)
		elif hoster == 'uploadc': return self.uploadc(link)
		elif hoster == 'youwatch': return self.youwatch(link)
		elif hoster == 'yandex': return self.generic1(link, 'Yandex', 0, 0)
		elif hoster == 'vidx': return self.generic1(link, 'ViDX', 10, 0)
		elif hoster == 'K1no HD': return link
		elif hoster == 'sharedsx': return self.generic1(link, 'Shared.sx', 0, 1)
		elif hoster == 'vivosx': return self.generic1(link, 'Vivo.sx', 0, 1)
		elif hoster == 'cloudyvideos': return self.generic1(link, 'CloudyVideos', 2, 2)
		return 'Not Supported'

	def getUrl(self, url):
		req = urllib2.Request(url)
		req.add_header('User-Agent', 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3')
		response = urllib2.urlopen(req)
		data = response.read()
		response.close()
		return data
		
	def get_adfly_link(self, adflink):
		print 'resolving adfly url: \'%s\' using http://dead.comuv.com/bypasser/process.php' % (adflink)
		data = self.net.http_POST('http://dead.comuv.com/bypasser/process.php', {'url':adflink}, {'Referer':'http://dead.comuv.com/', 'X-Requested-With':'XMLHttpRequest'}).content
		link = re.findall('<a[^>]*href="([^"]*)"', data, re.S|re.I|re.DOTALL)
		if link: return link[0]
		else: return 'empty'

	def get_adfly_link_2(self, adflink):
		print 'resolving adfly url: \'%s\' using http://cyberflux.info/shortlink.php' % (adflink)
		data = self.net.http_POST('http://cyberflux.info/shortlink.php', {'urllist':adflink}, {'Referer':'http://cyberflux.info/shortlink.php'}).content
		link = re.findall(adflink + '[ ]*=[ ]*<a[^>]*href=([^>]*)>', data, re.S|re.I|re.DOTALL)
		if link: return link[0]
		else: return 'empty'

	def waitmsg(self, sec, msg):
		isec = int(sec)
		if isec > 0:
			dialog = xbmcgui.DialogProgress()
			dialog.create('Resolving', '%s Link.. Wait %s sec.' % (msg, sec))
			dialog.update(0)
			c = 100 / isec
			i = 1
			p = 0
			while i < isec+1:
				p += int(c)
				time.sleep(1)
				dialog.update(int(p))
				i += 1
			dialog.close()
	
	def get_hostername(self, link):
		if link:
			for (hoster, urlrex) in hosterlist:
				if re.match(urlrex, link, re.S|re.I): return hoster
		return 'Not Supported'

	def get_stream_url(self, sUnpacked):
		if not sUnpacked: return
		stream_url = re.findall('type="video/divx"src="(.*?)"', sUnpacked, re.S|re.I|re.DOTALL)
		if not stream_url: stream_url = re.findall("file','(.*?)'", sUnpacked, re.S|re.I|re.DOTALL)
		if not stream_url: stream_url = re.findall('file:"(.*?)"', sUnpacked, re.S|re.I|re.DOTALL)
		if stream_url: return stream_url[0]

	def youtube(self, url):
		print url
		match = re.compile('youtube.com/embed/([^\?]+)', re.DOTALL).findall(url)
		if match:
			youtubeID = match[0]
			if xbmc.getCondVisibility("System.Platform.xbox") == True:
				video_url = "plugin://video/YouTube/?path=/root/video&action=play_video&videoid=" + youtubeID
			else:
				video_url = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=" + youtubeID
			return video_url

	def uploadc(self, url):
		data = self.net.http_GET(url).content
		ipcount_val = re.findall('<input type="hidden" name="ipcount_val".*?value="(.*?)">', data)
		id = re.findall('<input type="hidden" name="id".*?value="(.*?)">', data)
		fname = re.findall('<input type="hidden" name="fname".*?alue="(.*?)">', data)	
		if id and fname and ipcount_val:
			info = {'ipcount_val' : ipcount_val[0], 'op' : 'download2', 'usr_login' : '', 'id' : id[0], 'fname' : fname[0], 'method_free' : 'Slow access'}
			data2 = self.net.http_POST(url, info).content
			stream_url = self.get_stream_url(data2)
			if not stream_url:
				get_packedjava = re.findall("(\(p,a,c,k,e,d.*?)</script>", data2, re.S|re.DOTALL)
				if get_packedjava:
					sUnpacked = cJsUnpacker().unpackByString(get_packedjava[0])
					stream_url = self.get_stream_url(sUnpacked)
			if stream_url: return stream_url
			else: return 'Error: Konnte Datei nicht extrahieren'

	def youwatch(self, url):
		print url
		resp = self.net.http_GET(url)
		data = resp.content
		for frm in re.findall('<form[^>]*method="POST"[^>]*action=\'\'[^>]*>(.*?)</form>', data, re.S|re.I):
			info = {}
			for i in re.finditer('<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"', frm): info[i.group(1)] = i.group(2)
			if len(info) == 0: return 'Error: konnte Logindaten nicht extrahieren'
			info['referer'] = resp.get_url()
			self.waitmsg(int(10), 'Youwatch')
			data = self.net.http_POST(resp.get_url(), info).content
			get_packedjava = re.findall("(\(p,a,c,k,e,d.*?)</script>", data, re.S|re.I)
			if get_packedjava:
				sJavascript = get_packedjava[0]
				sUnpacked = cJsUnpacker().unpackByString(sJavascript)
				if sUnpacked:
					stream_url = re.findall('file:"([^"]*(?:mkv|mp4|avi|mov|flv|mpg|mpeg))"', sUnpacked)
					if stream_url: return stream_url[0]
					else: return 'Error: Konnte Datei nicht extrahieren'

	def movreel(self, url):
		data = self.net.http_GET(url).content
		id = re.findall('<input type="hidden" name="id".*?value="(.*?)">', data)
		fname = re.findall('<input type="hidden" name="fname".*?value="(.*?)">', data)
		if id and fname:
			info = {'op': 'download1', 'usr_login': '', 'id': id[0], 'fname': fname[0], 'referer': '', 'method_free': ' Kostenloser Download'}
			data2 = self.net.http_POST(url, info).content
			id = re.findall('<input type="hidden" name="id".*?value="(.*?)">', data2)
			rand = re.findall('<input type="hidden" name="rand".*?value="(.*?)">', data2)
			if id and rand:
				info2 = {'op': 'download2', 'usr_login': '', 'id': id[0], 'rand': rand[0], 'referer': '', 'method_free': ' Kostenloser Download'}
				data = self.net.http_POST(url, info2).content
				stream_url = re.findall("var file_link = '(.*?)'", data, re.S)
				if stream_url: return stream_url[0]
				else: return 'Error: Konnte Datei nicht extrahieren'

	def bitshare(self, url):
		data = self.net.http_GET(url).content
		if re.match('.*?(Ihr Traffic.*?Heute ist verbraucht|Your Traffic is used up for today)', data, re.S|re.I): return 'Error: Ihr heutiger Traffic ist aufgebraucht'
		elif re.match(".*?The file owner decided to limit file.*?access", data, re.S|re.I): return 'Error: Nutzer hat Dateizugriff limitiert'
		elif re.match(".*?Sorry aber sie.*?nicht mehr als 1 Dateien gleichzeitig herunterladen", data, re.S|re.I): return 'Error: Mehr als 1 Datei gleichzeitig ist nicht erlaubt'
		else:
			stream_url = re.findall("url: '(http://.*?.bitshare.com/stream/.*?.avi)'", data)
			if stream_url: return stream_url[0]
			else: return 'Error: Konnte Datei nicht extrahieren'

	def videomega(self, url):
		if not re.match('.*?iframe.php', url):
			id = url.split('ref=')
			if id: url = "http://videomega.tv/iframe.php?ref=%s" % id[1]
		data = self.net.http_GET(url).content
		unescape = re.findall('unescape."(.*?)"', data, re.S)
		if unescape:
			javadata = urllib2.unquote(unescape[0])
			if javadata:
				stream_url = re.findall('file: "(.*?)"', javadata, re.S)
				if stream_url: return stream_url[0]
				else: return 'Error: Konnte Datei nicht extrahieren'

	def primeshare(self, url):
		data = self.getUrl(url)
		hash = re.findall('<input type="hidden".*?name="hash".*?value="(.*?)"', data)
		if hash:
			info = {'hash': hash[0]}
			self.waitmsg(16, "Primeshare")
			data = self.net.http_POST(url, info).content
			stream_url = re.findall('url: \'(.*?)\'', data, re.S)
			if stream_url: return stream_url[2]
			else: return 'Error: Konnte Datei nicht extrahieren'

	def videoweed(self, url):
		data = self.net.http_GET(url).content
		r = re.search('flashvars.domain="(.+?)".*flashvars.file="(.+?)".*' + 'flashvars.filekey="(.+?)"', data, re.DOTALL)
		if r:
			domain, fileid, filekey = r.groups()
			api_call = ('%s/api/player.api.php?user=undefined&codes=1&file=%s' + '&pass=undefined&key=%s') % (domain, fileid, filekey)
			if api_call:
				data = self.net.http_GET(api_call).content
				rapi = re.search('url=(.+?)&title=', data)
				if rapi:
					stream_url = rapi.group(1)
					if stream_url: return stream_url
					else: return 'Error: Konnte Datei nicht extrahieren'

	def vk(self, url):
		data = self.net.http_GET(url).content
		vars = re.findall('<param[^>]*name="flashvars"[^>]*value="([^"]*)"', data, re.I|re.S|re.DOTALL)
		if vars:
			urls = re.findall('url([0-9]+)=([^&]*)&', vars[0], re.I|re.S|re.DOTALL)
			if urls:
				maxres = 0
				maxurl = ''
				for (res, url) in urls:
					if (int(res) > maxres):
						maxres = int(res)
						maxurl = url
				return maxurl

	def xvidstage(self, url):
		data = self.net.http_GET(url).content
		info = {}
		for i in re.finditer('<input.*?name="(.*?)".*?value="(.*?)">', data):
			info[i.group(1)] = i.group(2)
		data = self.net.http_POST(url, info).content
		get_packedjava = re.findall("(\(p,a,c,k,e,d.*?)</script>", data, re.S|re.DOTALL)
		if get_packedjava:
			sJavascript = get_packedjava[1]
			sUnpacked = cJsUnpacker().unpackByString(sJavascript)
			if sUnpacked:
				if re.match('.*?type="video/divx', sUnpacked):
					stream_url = re.findall('type="video/divx"src="(.*?)"', sUnpacked)
					if stream_url: return stream_url[0]
				elif re.match(".*?file", sUnpacked):
					stream_url = re.findall("file','(.*?)'", sUnpacked)
					if stream_url: return stream_url[0]
					else: return 'Error: Konnte Datei nicht extrahieren'

	def vidstream(self, url):
		data = self.net.http_GET(url).content
		if re.match('.*?maintenance mode', data, re.S): return 'Error: Server wegen Wartungsarbeiten ausser Betrieb'
		info = {}
		for i in re.finditer('<input[^>]*name="([^"]*)"[^>]*value="([^"]*)">', data):
			info[i.group(1)] = i.group(2)
		if len(info) == 0: return 'Error: konnte Logindaten nicht extrahieren'
		print 'URL: '+ url, info
		data = self.net.http_POST(url, info).content
		if re.match('.*?not found', data, re.S|re.I): return 'Error: Datei nicht gefunden'
		stream_url = re.findall('file: "([^"]*)"', data)
		if stream_url: return stream_url[0]
		else: return 'Error: Konnte Datei nicht extrahieren'

	def streamcloud(self, url):
		data = self.net.http_GET(url).content
		info = {}
		print url
		if re.match('.*?No such file with this filename', data, re.S|re.I): return 'Error: Dateiname nicht bekannt'
		for i in re.finditer('<input[^>]*name="([^"]*)"[^>]*value="([^"]*)">', data):
			info[i.group(1)] = i.group(2).replace('download1', 'download2')
		if len(info) == 0: return 'Error: konnte Logindaten nicht extrahieren'
		#wait required
		#print "POSTDATA: " + str(info)
		#self.waitmsg(10, "Streamcloud")
		data = self.net.http_POST(url, info).content
		if re.match('.*?This video is encoding now', data, re.S): return 'Error: Das Video wird aktuell konvertiert'
		if re.match('.*?The file you were looking for could not be found', data, re.S): return 'Error: Die Datei existiert nicht'
		stream_url = re.findall('file: "(.*?)"', data)
		if stream_url: return stream_url[0]
		else: return 'Error: Konnte Datei nicht extrahieren'

	def videoslaher(self, url):
		url = url.replace('file','embed')
		info = {'foo': "vs", 'confirm': "Close Ad and Watch as Free User"}
		data = self.net.http_POST(url, info).content
		code = re.findall("code: '(.*?)'", data, re.S)
		hash = re.findall("hash: '(.*?)'", data, re.S)
		xml_link = re.findall("playlist: '(/playlist/.*?)'", data, re.S)
		if code and hash and xml_link:
			data = self.net.http_GET("http://www.videoslasher.com"+xml_link[0]).content
			stream_url = re.findall('<media:content url="(.*?)"', data)
			if stream_url:
				info = {'user': "0", 'hash': hash[0], 'code': code[0]}
				data = self.net.http_POST("http://www.videoslasher.com/service/player/on-start", info).content
				if 'ok' in data: return stream_url[1]
				else: return 'Error: konnte stream nicht bestaetigen'
			else: return 'Error: Stream-URL nicht gefunden'
		else: return 'Error: konnte Logindaten nicht extrahieren'

	def streamPutlockerSockshare(self, url, provider):
		data = self.getUrl(url.replace('/file/','/embed/'))
		if re.match('.*?File Does not Exist', data, re.S): return 'Error: Die Datei existiert nicht'
		elif re.match('.*?Encoding to enable streaming is in progresss', data, re.S): return "Error: Die Datei wird aktuell konvertiert"
		else:
			enter = re.findall('<input type="hidden" value="(.*?)" name="fuck_you">', data)
			values = {'fuck_you': enter[0], 'confirm': 'Close+Ad+and+Watch+as+Free+User'}
			user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
			headers = { 'User-Agent' : user_agent}
			cookiejar = cookielib.LWPCookieJar()
			cookiejar = urllib2.HTTPCookieProcessor(cookiejar)
			opener = urllib2.build_opener(cookiejar)
			urllib2.install_opener(opener)
			data = urlencode(values)
			req = urllib2.Request(url, data, headers)
			try: response = urllib2.urlopen(req)
			except: return 'Error: Error @ urllib2.Request()'
			else:
				link = response.read()
				if link:
					embed = re.findall("get_file.php.stream=(.*?)'\,", link, re.S)
					if embed:
						req = urllib2.Request('http://www.%s.com/get_file.php?stream=%s' %(provider, embed[0]))
						req.add_header('User-Agent', user_agent)
						try: response = urllib2.urlopen(req)
						except: return 'Error: Error @ urllib2.Request()'
						else:
							link = response.read()
							if link:
								stream_url = re.findall('<media:content url="(.*?)"', link, re.S)
								filename = stream_url[1].replace('&amp;','&')
								if filename: return filename
								else: return 'Error: Konnte Datei nicht extrahieren'

	def flashx(self, url):
		print 'flashx: ' + url
		resp = self.net.http_GET(url)
		data = resp.content								
		for frm in re.findall('<form[^>]*method="POST"[^>]*>(.*?)</form>', data, re.S|re.I):
			info = {}
			for i in re.finditer('<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"', frm): info[i.group(1)] = i.group(2)
			if len(info) == 0: return 'Error: konnte Logindaten nicht extrahieren'
			info['referer'] = ""
			self.waitmsg(int(5), "flashx")
			data = self.net.http_POST(resp.get_url(), info).content
			get_packedjava = re.findall("(\(p,a,c,k,e,d.*?)</script>", data, re.S|re.DOTALL)
			if get_packedjava:
				sJavascript = get_packedjava[0]
				sUnpacked = cJsUnpacker().unpackByString(sJavascript)
				if sUnpacked:
					stream_url = re.findall('file:"([^"]*(?:mkv|mp4|avi|mov|flv|mpg|mpeg))"', sUnpacked)
					if stream_url: return stream_url[0]
					else: return 'Error: Konnte Datei nicht extrahieren'

	def generic1(self, url, hostername, waitseconds, filerexid):
		print hostername + ': ' + url
		filerex = [ 'file:[ ]*[\'\"]([^\'\"]+(?:mkv|mp4|avi|mov|flv|mpg|mpeg))[\"\']', 
					'data-url=[\'\"]([^\'\"]+)[\"\']',
					'<a[^>]*href="([^"]+)">[^<]*<input[^>]*value="Click for your file">' ]
		resp = self.net.http_GET(url)
		data = resp.content
		for frm in re.findall('<form[^>]*method="POST"[^>]*>(.*?)</form>', data, re.S|re.I):
			info = {}
			for i in re.finditer('<input[^>]*name="([^"]*)"[^>]*value="([^"]*)"', frm): info[i.group(1)] = i.group(2)
			if len(info) == 0: return 'Error: konnte Logindaten nicht extrahieren'
			info['referer'] = resp.get_url()
			self.waitmsg(int(waitseconds), hostername)
			data = self.net.http_POST(resp.get_url(), info).content
			if re.match('.*Video is processing now', data, re.S|re.I): return "Error: Die Datei wird aktuell konvertiert" 
			print "search for: " + filerex[filerexid]
			stream_url = re.findall(filerex[filerexid], data, re.S|re.I)
			if stream_url: return stream_url[0]
			else: return 'Error: Konnte Datei nicht extrahieren'

	def generic2(self, url):
		url = re.sub('[ ]+', '', url)
		data = self.net.http_GET(url).content
		if re.match('.*?The file is being converted', data, re.S|re.I): return "Error: Das Video wird aktuell konvertiert"
		dom = re.findall('flashvars.domain="(.*?)"', data)
		file = re.findall('flashvars.file="(.*?)"', data)
		key = re.findall('flashvars.filekey="(.*?)"', data)
		if file and not key:
			varname = re.findall('flashvars.filekey=(.*?);', data)
			if varname: key = re.findall('var[ ]+%s="(.*?)"'%(varname[0]), data)
		if dom and file and key:
			url = "%s/api/player.api.php?file=%s&key=%s"%(dom[0], file[0], key[0])
			if re.match('.*?The video has failed to convert', data, re.S|re.I): return "Error: Das Video wurde nicht fehlerfrei konvertiert"
			data = self.net.http_GET(url).content
			rapi = re.search('url=([^&]+)&title=', data)
			if rapi:
				stream_url = rapi.group(1)
				if stream_url: return stream_url
				else: return 'Error: Konnte Datei nicht extrahieren'
		else: return "Error: Video wurde nicht gefunden"
