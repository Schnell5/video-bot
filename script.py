# -*- coding: utf-8 -*- 
#!/usr/bin/python
#apt-get install python2.7
#apt-get install python-pip
#pip install --upgrade pip
#pip install -U setuptools
#pip install -U pip
#pip install pyTelegramBotAPI
#sudo apt-get install motion
#sudo apt-get install fswebcam
#sudo apt install alsa-utils
#https://markov.gq/2016/04/12/
#nmcli device wifi connect mai password 38379992

import sys
temp = sys.stdout
temp2 = sys.stderr 
reload(sys)
sys.setdefaultencoding('utf-8')
sys.stdout = temp
sys.stderr = temp2


import urllib
import time
import os
import telebot
import threading
import telnetlib
import re
from datetime import datetime, date
import ConfigParser
conf_file = '/etc/tele_motion.conf'
motion_conf_file = "/etc/motion/motion.conf"

def log( string, admin_note = False ):
    try:
       global last_log
       log_file = open( log_path ,"a")
       log_file.write( str(datetime.now().replace(microsecond=0) ) + "        " + str(string) + "\n\n" )
       log_file.close() 
       if admin_note: bot.send_message(admin_id ,  str(string) )
    except Exception, e:
       pass



se = {}
def settings():
	try:
		global se
		config = ConfigParser.ConfigParser()
		config.read(conf_file)

		se['admin_id'] = config.getint('main','admin_id')
		se['token'] = config.get('main','token')
		se['password'] = config.get('main','password')
		se['motion_dir'] = config.get('main','motion_dir')
		se['home_dir'] = config.get('main','home_dir')
		se['live_resolution'] = config.get('main','live_resolution')
		
		se['router_ip'] = config.get('router','router_ip')
		se['router_user'] = config.get('router','router_user')
		se['router_pass'] = config.get('router','router_pass')
		se['make_reboot'] = config.getboolean('router','make_reboot')

		se['wifi'] = config.getboolean('wifi','wifi')
		se['ssid_wifi'] = config.get('wifi','ssid_1')
		se['password_wifi'] = config.get('wifi','pass_1')

		se['state'] = config.getboolean('current','state')
		se['log_path'] =  se['home_dir'] + "/log.txt"
		se['live_path'] = se['home_dir'] + "/live.jpg"
		se['audio_path'] = se['home_dir'] + "/output.wav"
		se['script_path'] = se['home_dir'] + "/script.py"
		se['config_path'] = se['home_dir'] + "/main.conf"
		se['allow_add_user'] = config.getboolean('main','allow_add_user')

		try:
			se['start_time'] = config.get('main','start_time')
		except Exception, e:
			se['start_time'] = False

		try:
			se['stop_time'] = config.get('main','stop_time')
		except Exception, e:
			se['stop_time'] = False
			
		log("Settings was read")
	except Exception, e:
		log(e)


	


def update_settings(section, attribute, value ):
  try:
    global se
    se[attribute] = value
    config = ConfigParser.ConfigParser()
    config.read(conf_file)
    config.set(section, attribute, value )
    with open(conf_file, 'w') as configfile:
          config.write(configfile)
    log("Settings was updated")
  except Exception, e:
    log(e)








def check_request(chat_id, request ):
	global count_command
	count_command = count_command + 1
	admin_note = True 
	if str(chat_id) == str(se['admin_id']) :
		admin_note = False
	if chat_id in clients:
		log("Request: %s  from: %s" % ( request, chat_id), admin_note)
		return True
	log("UNAUTHORIZED!!!  request: %s   from: %s" % ( request, chat_id), admin_note)
	return False




def reboot():
	try:	
		#Checking for the internet
		if os.system("ping -c 1 yandex.ru")==0 or os.system("ping -c 1 google.ru")==0 or os.system("ping -c 1 8.8.8.8")==0:
			log("Rebooting is not need. Internet is OK")
			return True
		#Reconnect WIFI if it is present
		if se['wifi']:
			log("Problem. Trying connect to wifi with login: %s password: %s "%(se['ssid_wifi'],se['password_wifi']) )
			os.system("nmcli dev disconnect iface wlan0")
			os.system( "nmcli device wifi connect %s password %s"%(se['ssid_wifi'],se['password_wifi']) )
			time.sleep(10)
			if os.system("ping -c 1 yandex.ru")==0 or os.system("ping -c 1 google.ru")==0 or os.system("ping -c 1 8.8.8.8")==0:
				log("Wifi is OK with login: %s password: %s "%(se['ssid_wifi'],se['password_wifi'] ))
				return True
		#Reboot router
		if se['make_reboot']:
			log("Problem with internet. Rebooting router")
			tn = telnetlib.Telnet(se['router_ip'])
			tn.read_until("ogin:")
			tn.write(se['router_user'] + "\n")
			tn.read_until("assword:")
			tn.write(se['router_pass'] + "\n")
			tn.read_until("$")
			tn.write("reboot \n")
			tn.read_until("$")
			log("Rebooting is made")
		#Waiting for the internet
		count = 0
		while os.system("ping -c 1 yandex.ru")!=0 and os.system("ping -c 1 google.ru")!=0 and os.system("ping -c 1 8.8.8.8")!=0 :
			log("Waiting 15 seconds for the internet")
			time.sleep(15)
			count = count + 1
			if count == 20:
				log("Rebooting is not OK. Internet Access is not OK")
				return False
		log("Rebooting is OK. Internet Access is OK")
	except Exception, e:
		log(e)





settings() # read conf file
bot = telebot.TeleBot(se['token'])
state_sender = 0
count_command = 0
clients = [ se['admin_id'] ] # make clients list




# camera_off - turn on motion detection
# camera_on - turn off motion detection
# help - get commands description
# config - get config file
# script - get script file 
# log - get log file 
# update - update software
# clearlog - clear log file 
# reboot - reboot device 
# restart - restart process
# state - show state of process
# photo - get live foto



@bot.message_handler(commands=['help'])
def help_bot(message):
	if not check_request(message.chat.id, "Asking for help message" ): return False
	try:
		string = "  Commnads\n"
		string = string + "    /camera_on -- Start motion detection\n"
		string = string + "     /camera_off -- Stop motion detection\n"
		string = string + "     /photo -- Make foto at that moment\n"
		string = string + "     /help -- Get info\n"
		string = string + "  /restart -- Restart bot\n"
		string = string + "  /update -- update software\n"
		string = string + "  start00:22 -- start time (start0 - for cancel)\n"
		string = string + "  stop00:32 -- stop time (stop0 - for cancel)\n"
		string = string + "  audioX -- Make X seconds audio record \n"
		bot.send_message(message.chat.id, string  )
	except Exception, e:
		bot.send_message(message.chat.id, (e) )



@bot.message_handler(commands=['script'])
def script_bot(message):
	if not check_request(message.chat.id, "Asking for script file" ): return False
	try:
		bot.send_document(message.chat.id,  open( se['script_path'] , 'rb') )
	except Exception, e:
		log(e)

@bot.message_handler(commands=['log'])
def log_bot(message):
	if not check_request(message.chat.id, "Asking for log file" ): return False
	try:
		bot.send_document(message.chat.id,  open( se['log_path'] , 'rb') )
	except Exception, e:
		log(e)

@bot.message_handler(commands=['update'])
def update(message):
	if not check_request(message.chat.id, "Asking for updating" ): return False
	try:
		#stop processes
		os.system("killall motion")
		#download files
		scriptF = urllib.urlopen("https://raw.githubusercontent.com/denchz/video-bot/master/script.py").read()
		motionF  = urllib.urlopen("https://raw.githubusercontent.com/denchz/video-bot/master/motion.conf").read()
		infoF = urllib.urlopen("https://raw.githubusercontent.com/denchz/video-bot/master/info_version").read()
		bot.send_message(message.chat.id,  "Current version: 1.13")
		
		#sednd info about changes
		bot.send_message(message.chat.id,  infoF)
		
		#update motion config file
		os.system("rm %s"%motion_conf_file )
		f = open("%s" % motion_conf_file, "w")
		f.write(motionF)
		f.close()
		
		#update script file
		os.system("rm %s"%se['script_path'] )
		f = open("%s" % se['script_path'], "w")
		f.write(scriptF)
		f.close()
		
		#restarting processes
		bot.send_message(message.chat.id,  "Software updated. Restarting bot...")
		os.system("killall motion")
		os.system("killall python")
	except Exception, e:
		log(e)

		
		
		
@bot.message_handler(commands=['clearlog'])
def log_clear(message):
	if not check_request(message.chat.id, "Asking for clearing log" ): return False
	try:
		os.system("rm " + se['log_path'] )
		time.sleep(2)
		bot.send_message(message.chat.id, "Log file cleared" )
	except Exception, e:
		log(e)

@bot.message_handler(commands=['reboot'])
def reboot_bot(message):
	if not check_request(message.chat.id, "Asking for rebooting device" ): return False
	try:
		bot.send_message(message.chat.id, "Device will be rebooted" )
		os.system("reboot")
	except Exception, e:
		log(e)

@bot.message_handler(commands=['restart'])
def restart_bot(message):
	if not check_request(message.chat.id, "Asking for kill motion and python processes" ): return False
	try:
		os.system("killall motion")
		bot.send_message(message.chat.id, "Motion stopped. Python  will stopped")
		os.system("killall python")
	except Exception, e:
		log(e)

@bot.message_handler(commands=['check_bot'])
def state_bot(message):
	if not check_request(message.chat.id, "Asking for state message " ): return False
	try:
		bot.send_message(message.chat.id,  "Checking..." )
		string = "Clients: " + str(clients)
		if se['state']:
			string = string + "\nDetection status: ON"
		else: 
			string = string + "\nDetection status: OFF"
		
		string = string + "\nCount of commands: " + str(count_command)
		
		string_camera = ""
		camera = os.listdir("/dev/")
		for line in camera:
			if "video" in line:
				string_camera = string_camera  + "\nCamera " + line + ": OK"
		if string_camera =="":
			string = string + "\n Camera: FAIL"
		else: 
			string = string + string_camera
	
		#Checking sender
		state_motion = state_sender 
		time.sleep(3)
		if state_motion != state_sender:
			string = string + "\nState of motion detection: OK"
		else:
			string = string + "\nState of motion detection: FAIL"

		string = string + "\n\nCurrent time: " + str( datetime.now().replace(microsecond=0) )
		string = string + "\nStart time: " + str( se['start_time'])
		string = string + "\nStop time: " + str( se['stop_time'])
		bot.send_message(message.chat.id,  string )
		
		settings_new()
		bot.send_message(message.chat.id,  str(se) )
	except Exception, e:
		log(e)

@bot.message_handler(regexp='^(?i)start\D*\d\D*')
def start_time_bot(message):
	if not check_request(message.chat.id, "Setting start time " ): return False
	try:
		global se
		text = message.text.replace(" ","")
		
		if text == "start0":
			se['start_time'] = False
			update_settings('main', 'start_time', False )
			bot.send_message(message.chat.id,  "Start Time canceled")
			return True
		hour = re.findall(r"\D*(\d*)\D*\d*", text)[0] 
		minute = re.findall(r"\D*\d*\D*(\d*)", text)[0] 
		try:
			dt = datetime.strptime("%s:%s"%(hour, minute), "%H:%M")
		except Exception, e:
			bot.send_message(message.chat.id,  "Error in time format" )
			return True
		update_settings('main', 'start_time', str( dt.strftime("%H.%M") ) )
		se['start_time'] = str( dt.strftime("%H.%M") )
		bot.send_message(message.chat.id,  "Start time is: " + str( dt.strftime("%H.%M") )  + "\n Now is " + str( datetime.now().strftime("%H.%M") ) )
	except Exception, e:
		log(e)

@bot.message_handler(regexp='^(?i)stop\D*\d\D*')
def stop_time_bot(message):
	if not check_request(message.chat.id, "Setting start time " ): return False
	try:
		global se
		text = message.text.replace(" ","")

		if text == "stop0":
			se['stop_time'] = False
			update_settings('main', 'stop_time', False )
			bot.send_message(message.chat.id,  "Stop Time canceled")
			return True
		hour = re.findall(r"\D*(\d*)\D*\d*", text)[0] 
		minute = re.findall(r"\D*\d*\D*(\d*)", text)[0] 
		try:
			dt = datetime.strptime("%s:%s"%(hour, minute), "%H:%M")
		except Exception, e:
			bot.send_message(message.chat.id,  "Error in time format" )
			return True

		update_settings('main', 'stop_time', str( dt.strftime("%H.%M") ))
		se['stop_time'] = str( dt.strftime("%H.%M") )
		bot.send_message(message.chat.id,  "Stop time is: " + str( dt.strftime("%H.%M") )  + "\n Now is " + str( datetime.now().strftime("%H.%M") ) )
	except Exception, e:
		log(e)

@bot.message_handler(commands=['photo'])
def foto_bot(message):
	if not check_request(message.chat.id, "Asking for live foto" ): return False

	try:
		global se
		if se['state']:
			os.system("killall motion")
			bot.send_message(message.chat.id, "Camera stopped" )
		#First camera photo
		files = os.listdir("/dev/")
		for line in files:
			if "video" in line:
				bot.send_message(message.chat.id, "Photo from device %s: "%line )
				os.system("rm %s" % (se['live_path']) )
				time.sleep(0.5)
				os.system("fswebcam -d /dev/%s -r %s %s" % (line, se['live_resolution'], se['live_path']) )
				time.sleep(1)
				os.system("fswebcam -d /dev/%s -r %s %s" % (line, se['live_resolution'], se['live_path']) )
				os.system("fswebcam -d /dev/%s -r %s %s" % (line, se['live_resolution'], se['live_path']) )
				os.system("fswebcam -d /dev/%s -r %s %s" % (line, se['live_resolution'], se['live_path']) )
				bot.send_photo(message.chat.id,  open( se['live_path'] , 'rb') )
		if se['state']:
			os.system("motion")
			bot.send_message(message.chat.id, "Camera started" )
	except Exception, e:
		log(e)

@bot.message_handler(regexp='^(?i)audio')
def audio_bot(message):
	if not check_request(message.chat.id, "Asking for audio " ): return False

	try:
		if not re.match("^(?i)audio\d\d?$",message.text) or re.match("^(?i)audio0",message.text):
			bot.send_message(message.chat.id, "Wrong format. Example audio1, audio99" )
			return False
		time_audio = message.text.replace("Audio","").replace("audio","")
		bot.send_message(message.chat.id, "Audio " + time_audio + " seconds is recording. Wait" )
		os.system("arecord -d %s -f S16_LE -D hw:1,0 -r 48000 %s" % (time_audio, se['audio_path']) )
		time.sleep( int(time_audio ) + 2 )
		bot.send_document(message.chat.id,  open( se['audio_path'] , 'rb') )
	except Exception, e:
		log(e)

@bot.message_handler(commands=['camera_off'])
def stop_bot(message=False):
	if not check_request(message.chat.id, "Asking for stop motion " ): return False
	try:
		global se
		os.system("killall motion")
		if message: bot.send_message(message.chat.id, "Camera stopped" )
		se['state'] = False
		update_settings('current', 'state', se['state'])
	except Exception, e:
		log(e)

@bot.message_handler(commands=['camera_on'])
def start_bot(message=False):
	if not check_request(message.chat.id, "Asking for start motion" ):  return False
	try:
		global se
		os.system("rm /var/lib/motion/*")
		os.system("motion")
		if message: bot.send_message(message.chat.id, "Camera started" )
		se['state'] = True
		update_settings('current', 'state', se['state'])
	except Exception, e:
		log(e)

@bot.message_handler(regexp='^(?i)add' + se['password'])
def add_bot(message):
	try:
		global se
		#if not allow_add_user:
		#	bot.send_message(message.chat.id, "Adding is denied")
		#	return False
		log("Asking for adding  from:" + str(message.chat.id), admin_note = True )
		clients.append(message.chat.id)
		clients = list(set(clients))
		bot.send_message(message.chat.id, "You was added ID:" + str(message.chat.id) + "\nUse help command to get commands list")
	except Exception, e:
		log(e)



@bot.message_handler(commands=['delete'])
def delete_bot(message):
	if not check_request(message.chat.id, "Asking for help message " ):  return False
	try:
		global clients
		clients.remove(message.chat.id)
		log("Asking for deleting  from:" + str(message.chat.id) )
		bot.send_message(message.chat.id, "You was deleted " )
	except Exception, e:
		log(e)


def sender():
	global se
	global state_sender
	global clients
	while True:	
		try:
			state_sender = ( state_sender  + 1 ) % 100000
			if se['state'] == False:
				time.sleep(3)
				continue	
			os.system("rm %s*.avi"% se['motion_dir'])
			files = os.listdir(se['motion_dir']) 
			if len(files) == 0:
				time.sleep(1)
				continue
			files.sort()
			log("Sending foto:" + str(files[0]) )
			for foto in files:
				for line in clients:
					bot.send_photo(line ,  open(se['motion_dir'] + foto , 'rb') )  
				os.system("rm " + se['motion_dir'] + foto ) 
		except Exception,e :
			log(e)
			time.sleep(5)

def bot_polling():
	while True:
		try:
			bot.polling()
		except Exception,e :
			log(e)	
			reboot()

def time_stop_start():
	while True:
		try:
			time.sleep(30)
			if str(se['start_time']) == str( datetime.now().strftime("%H.%M") )  and se['state'] == False:
				start_bot()
				log("Motion started by timer" , admin_note = True  )
			if str(se['stop_time']) == str( datetime.now().strftime("%H.%M") ) and se['state'] == True :
				stop_bot()
				log("Motion stoped by timer" , admin_note = True  )
		except Exception,e :
			log(e)



reboot() # check internet

thread1 = threading.Thread(target=bot_polling) # start telegram
thread1.start()
thread2 = threading.Thread(target=sender) 
thread2.start()
thread3 = threading.Thread(target=time_stop_start) 
thread3.start()

time.sleep(2)
log("Bot started" , admin_note = True)
if se['state']: start_bot()
