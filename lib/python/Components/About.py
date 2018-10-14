from boxbranding import getBoxType, getMachineBuild, getImageVersion
from sys import modules
import socket, fcntl, struct, time, os

def getVersionString():
	return getImageVersion()

def getImageVersionString():
	try:
		if os.path.isfile('/var/lib/opkg/status'):
			st = os.stat('/var/lib/opkg/status')
		else:
			st = os.stat('/usr/lib/ipkg/status')
		tm = time.localtime(st.st_mtime)
		if tm.tm_year >= 2011:
			return time.strftime("%Y-%m-%d %H:%M:%S", tm)
	except:
		pass
	return _("unavailable")

def getFlashDateString():
	try:
		return time.strftime(_("%Y-%m-%d %H:%M"), time.localtime(os.stat("/boot").st_ctime))
	except:
		return _("unknown")

def getEnigmaVersionString():
	import enigma
	enigma_version = enigma.getEnigmaVersionString()
	if '-(no branch)' in enigma_version:
		enigma_version = enigma_version [:-12]
	return enigma_version

def getGStreamerVersionString():
	import enigma
	return enigma.getGStreamerVersionString()

def getKernelVersionString():
	try:
		f = open("/proc/version","r")
		kernelversion = f.read().split(' ', 4)[2].split('-',2)[0]
		f.close()
		return kernelversion
	except:
		return _("unknown")

def getModelString():
	model = getBoxType()
	return model

def getChipSetString():
	if getMachineBuild() in ('dm7080', 'dm820'):
		return "7435"
	elif getMachineBuild() in ('dm520', 'dm525'):
		return "73625"
	elif getMachineBuild() in ('dm900', 'dm920', 'et13000', 'sf5008'):
		return "7252S"
	elif getMachineBuild() in ('hd51', 'vs1500', 'h7'):
		return "7251S"
	elif getMachineBuild() in ('alien5'):
		return "S905D"
	else:
		try:
			f = open('/proc/stb/info/chipset', 'r')
			chipset = f.read()
			f.close()
			return str(chipset.lower().replace('\n','').replace('bcm','').replace('brcm','').replace('sti',''))
		except IOError:
			return _("unavailable")

def getCPUSpeedString():
	if getMachineBuild() in ('wetekplay'):
		return "1,2 GHz"
	elif getMachineBuild() in ('dags72604', 'vusolo4k', 'vuultimo4k', 'vuzero4k'):
		return "1,5 GHz"
	elif getMachineBuild() in ('formuler1tc', 'formuler1', 'triplex', 'tiviaraplus'):
		return "1,3 GHz"
	elif getMachineBuild() in ('u51', 'u52', 'u53', 'u5', 'u5pvr', 'h9', 'cc1', 'sf8008', 'hd60', 'i55plus', 'ustym4kpro'):
		return "1,6 GHz"
	elif getMachineBuild() in ('vuuno4kse', 'vuuno4k', 'dm900', 'dm920', 'gb7252', 'dags7252', 'xc7439', '8100s'):
		return "1,7 GHz"
	elif getMachineBuild() in ('alien5'):
		return "2,0 GHz"
	elif getMachineBuild() in ('hd51', 'hd52', 'sf4008', 'vs1500', 'et1x000', 'h7', 'et13000', 'sf5008', 'osmio4k'):
		try:
			import binascii
			f = open('/sys/firmware/devicetree/base/cpus/cpu@0/clock-frequency', 'rb')
			clockfrequency = f.read()
			f.close()
			return "%s MHz" % str(round(int(binascii.hexlify(clockfrequency), 16)/1000000,1))
		except:
			return "1,7 GHz"
	else:
		try:
			file = open('/proc/cpuinfo', 'r')
			lines = file.readlines()
			for x in lines:
				splitted = x.split(': ')
				if len(splitted) > 1:
					splitted[1] = splitted[1].replace('\n','')
					if splitted[0].startswith("cpu MHz"):
						mhz = float(splitted[1].split(' ')[0])
						if mhz and mhz >= 1000:
							mhz = "%s GHz" % str(round(mhz/1000,1))
						else:
							mhz = "%s MHz" % str(round(mhz,1))
			file.close()
			return mhz
		except IOError:
			return _("unavailable")

def getCPUString():
	if getMachineBuild() in ('osmio4k', 'dags72604', 'vuuno4kse', 'vuuno4k', 'vuultimo4k', 'vusolo4k', 'vuzero4k', 'hd51', 'hd52', 'sf4008', 'dm900', 'dm920', 'gb7252', 'dags7252', 'vs1500', 'et1x000', 'xc7439', 'h7', '8100s', 'et13000', 'sf5008'):
		return "Broadcom"
	elif getMachineBuild() in ('u51', 'u52', 'u53', 'u5', 'u5pvr', 'h9', 'cc1', 'sf8008', 'hd60', 'i55plus', 'ustym4kpro'):
		return "Hisilicon"
	elif getMachineBuild() in ('alien5', 'wetekplay', 'wetekplay2'):
		return "AMlogic"
	else:
		try:
			system="unknown"
			file = open('/proc/cpuinfo', 'r')
			lines = file.readlines()
			for x in lines:
				splitted = x.split(': ')
				if len(splitted) > 1:
					splitted[1] = splitted[1].replace('\n','')
					if splitted[0].startswith("system type"):
						system = splitted[1].split(' ')[0]
					elif splitted[0].startswith("Processor"):
						system = splitted[1].split(' ')[0]
			file.close()
			return system
		except IOError:
			return _("unavailable")

def getCpuCoresString():
	try:
		file = open('/proc/cpuinfo', 'r')
		lines = file.readlines()
		for x in lines:
			splitted = x.split(': ')
			if len(splitted) > 1:
				splitted[1] = splitted[1].replace('\n','')
				if splitted[0].startswith("processor"):
					if getMachineBuild() in ('u51', 'u52', 'u53', 'vuultimo4k', 'u5', 'u5pvr', 'h9', 'alien5', 'cc1', 'sf8008', 'hd60', 'i55plus', 'ustym4kpro'):
						cores = 4
					elif int(splitted[1]) > 0:
						cores = 2
					else:
						cores = 1
		file.close()
		return cores
	except IOError:
		return _("unavailable")

def _ifinfo(sock, addr, ifname):
	iface = struct.pack('256s', ifname[:15])
	info  = fcntl.ioctl(sock.fileno(), addr, iface)
	if addr == 0x8927:
		return ''.join(['%02x:' % ord(char) for char in info[18:24]])[:-1].upper()
	else:
		return socket.inet_ntoa(info[20:24])

def getIfConfig(ifname):
	ifreq = {'ifname': ifname}
	infos = {}
	sock  = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	# offsets defined in /usr/include/linux/sockios.h on linux 2.6
	infos['addr']    = 0x8915 # SIOCGIFADDR
	infos['brdaddr'] = 0x8919 # SIOCGIFBRDADDR
	infos['hwaddr']  = 0x8927 # SIOCSIFHWADDR
	infos['netmask'] = 0x891b # SIOCGIFNETMASK
	try:
		for k,v in infos.items():
			ifreq[k] = _ifinfo(sock, v, ifname)
	except:
		pass
	sock.close()
	return ifreq

def getIfTransferredData(ifname):
	f = open('/proc/net/dev', 'r')
	for line in f:
		if ifname in line:
			data = line.split('%s:' % ifname)[1].split()
			rx_bytes, tx_bytes = (data[0], data[8])
			f.close()
			return rx_bytes, tx_bytes

def getHardwareTypeString():
	try:
		if os.path.isfile("/proc/stb/info/boxtype"):
			return open("/proc/stb/info/boxtype").read().strip().upper()
		if os.path.isfile("/proc/stb/info/azmodel"):
			return "AZBOX " + open("/proc/stb/info/azmodel").read().strip().upper() + "(" + open("/proc/stb/info/version").read().strip().upper() + ")" 
		if os.path.isfile("/proc/stb/info/vumodel"):
			return "VU+" + open("/proc/stb/info/vumodel").read().strip().upper() + "(" + open("/proc/stb/info/version").read().strip().upper() + ")" 
		if os.path.isfile("/proc/stb/info/model"):
			return open("/proc/stb/info/model").read().strip().upper()
	except:
		pass
	return _("unavailable")

def getImageTypeString():
	try:
		return open("/etc/issue").readlines()[-2].capitalize().strip()[:-6]
	except:
		pass
	return _("undefined")

def getPythonVersionString():
	try:
		import commands
		status, output = commands.getstatusoutput("python -V")
		return output.split(' ')[1]
	except:
		return _("unknown")

# For modules that do "from About import about"
about = modules[__name__]
