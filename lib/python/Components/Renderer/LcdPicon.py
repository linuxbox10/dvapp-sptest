import os, re, unicodedata
from Renderer import Renderer
from enigma import ePixmap, ePicLoad
from Tools.Alternatives import GetWithAlternative
from Tools.Directories import pathExists, SCOPE_ACTIVE_SKIN, resolveFilename
from Components.Harddisk import harddiskmanager
from boxbranding import getDisplayType
from ServiceReference import ServiceReference
from Components.SystemInfo import SystemInfo
from Components.config import config, ConfigText, ConfigYesNo

config.misc.picon_path = ConfigText(default = "/usr/share/enigma2/picon/")
config.misc.picon_search_hdd = ConfigYesNo (default = False)

searchPaths = []
lastLcdPiconPath = None

def initLcdPiconPaths():
	global searchPaths
	searchPaths = []
	for part in harddiskmanager.getMountedPartitions():
		onMountpointAdded(part.mountpoint)
	path = str(config.misc.picon_path.value)
	for mp in ('/usr/share/enigma2/', '/', path):
		onMountpointAdded(mp)

def onMountpointAdded(mountpoint):
	global searchPaths
	try:
		if getDisplayType() in ('bwlcd255', 'bwlcd140') and not SystemInfo["grautec"] or os.path.isdir(mountpoint + 'piconlcd'):
			path = os.path.join(mountpoint, 'piconlcd') + '/'
		else:
			path = os.path.join(mountpoint, 'XPicons') + '/'
			if os.path.isdir(path) and path not in searchPaths:
				for fn in os.listdir(path):
					if fn.endswith('.png'):
						print "[LcdPicon] adding path:", path
						searchPaths.append(path)
						break
			path = os.path.join(mountpoint, 'XPicons/picon') + '/'
			if os.path.isdir(path) and path not in searchPaths:
				for fn in os.listdir(path):
					if fn.endswith('.png'):
						print "[LcdPicon] adding path:", path
						searchPaths.append(path)
						break
			path = os.path.join(mountpoint, 'picon') + '/'
			if os.path.isdir(path) and path not in searchPaths:
				for fn in os.listdir(path):
					if fn.endswith('.png'):
						print "[LcdPicon] adding path:", path
						searchPaths.append(path)
						break
			path = mountpoint
			if os.path.isdir(path) and path not in searchPaths:
				for fn in os.listdir(path):
					if fn.endswith('.png'):
						print "[LcdPicon] adding path:", path
						searchPaths.append(path)
						break
	except Exception, ex:
		print "[LcdPicon] Failed to investigate %s:" % mountpoint, ex

def onMountpointRemoved(mountpoint):
	global searchPaths
	if getDisplayType() in ('bwlcd255', 'bwlcd140') and not SystemInfo["grautec"] or os.path.isdir(mountpoint + 'piconlcd'):
		path = os.path.join(mountpoint, 'piconlcd') + '/'
	else:
		path = os.path.join(mountpoint, 'picon') + '/'
	try:
		searchPaths.remove(path)
		print "[LcdPicon] removed path:", path
	except:
		pass

def onPartitionChange(why, part):
	if why == 'add':
		onMountpointAdded(part.mountpoint)
	elif why == 'remove':
		onMountpointRemoved(part.mountpoint)

def findLcdPicon(serviceName):
	global lastLcdPiconPath
	if lastLcdPiconPath is not None:
		pngname = lastLcdPiconPath + serviceName + ".png"
		if pathExists(pngname):
			return pngname
	global searchPaths
	for path in searchPaths:
		if pathExists(path):
			pngname = path + serviceName + ".png"
			if pathExists(pngname):
				lastLcdPiconPath = path
				return pngname
	return ""

def getLcdPiconName(serviceName):
	#remove the path and name fields, and replace ':' by '_'
	fields = GetWithAlternative(serviceName).split(':', 10)[:10]
	if not fields or len(fields) < 10:
		return ""
	pngname = findLcdPicon('_'.join(fields))
	if not pngname and not fields[6].endswith("0000"):
		#remove "sub-network" from namespace
		fields[6] = fields[6][:-4] + "0000"
		pngname = findLcdPicon('_'.join(fields))
	if not pngname and fields[0] != '1':
		#fallback to 1 for other reftypes
		fields[0] = '1'
		pngname = findLcdPicon('_'.join(fields))
	if not pngname and fields[2] != '1':
		#fallback to 1 for services with different service types
		fields[2] = '1'
		pngname = findLcdPicon('_'.join(fields))
	if not pngname: # picon by channel name
		name = ServiceReference(serviceName).getServiceName()
		name = unicodedata.normalize('NFKD', unicode(name, 'utf_8', errors='ignore')).encode('ASCII', 'ignore')
		name = re.sub('[^a-z0-9]', '', name.replace('&', 'and').replace('+', 'plus').replace('*', 'star').lower())
		if len(name) > 0:
			pngname = findLcdPicon(name)
			if not pngname and len(name) > 2 and name.endswith('hd'):
				pngname = findLcdPicon(name[:-2])
	return pngname

class LcdPicon(Renderer):
	def __init__(self):
		Renderer.__init__(self)
		self.PicLoad = ePicLoad()
		self.PicLoad.PictureData.get().append(self.updatePicon)
		self.piconsize = (0,0)
		self.pngname = ""
		self.lastPath = None
		if getDisplayType() in ('bwlcd255', 'bwlcd140') and not SystemInfo["grautec"]:
			pngname = findLcdPicon("lcd_picon_default")
		else:
			pngname = findLcdPicon("picon_default")
		self.defaultpngname = None
		if not pngname:
			if getDisplayType() in ('bwlcd255', 'bwlcd140') and not SystemInfo["grautec"]:
				tmp = resolveFilename(SCOPE_ACTIVE_SKIN, "lcd_picon_default.png")
			else:
				tmp = resolveFilename(SCOPE_ACTIVE_SKIN, "picon_default.png")
			if pathExists(tmp):
				pngname = tmp
			else:
				if getDisplayType() in ('bwlcd255', 'bwlcd140') and not SystemInfo["grautec"]:
					pngname = resolveFilename(SCOPE_ACTIVE_SKIN, "lcd_picon_default.png")
				else:
					pngname = resolveFilename(SCOPE_ACTIVE_SKIN, "picon_default.png")
		if os.path.getsize(pngname):
			self.defaultpngname = pngname

	def addPath(self, value):
		if pathExists(value):
			global searchPaths
			if not value.endswith('/'):
				value += '/'
			if value not in searchPaths:
				searchPaths.append(value)

	def applySkin(self, desktop, parent):
		attribs = self.skinAttributes[:]
		for (attrib, value) in self.skinAttributes:
			if attrib == "path":
				self.addPath(value)
				attribs.remove((attrib,value))
			elif attrib == "size":
				self.piconsize = value
		self.skinAttributes = attribs
		return Renderer.applySkin(self, desktop, parent)

	GUI_WIDGET = ePixmap

	def postWidgetCreate(self, instance):
		self.changed((self.CHANGED_DEFAULT,))

	def updatePicon(self, picInfo=None):
		ptr = self.PicLoad.getData()
		if ptr is not None:
			self.instance.setPixmap(ptr.__deref__())
			self.instance.show()

	def changed(self, what):
		if self.instance:
			pngname = ""
			if what[0] == 1 or what[0] == 3:
				pngname = getLcdPiconName(self.source.text)
				if not pathExists(pngname): # no picon for service found
					pngname = self.defaultpngname
				if self.pngname != pngname:
					if pngname:
						self.PicLoad.setPara((self.piconsize[0], self.piconsize[1], 0, 0, 1, 1, "#FF000000"))
						self.PicLoad.startDecode(pngname)
					else:
						self.instance.hide()
					self.pngname = pngname

harddiskmanager.on_partition_list_change.append(onPartitionChange)
initLcdPiconPaths()
