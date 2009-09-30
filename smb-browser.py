#!/usr/bin/python
##This program was designed to assist users in finding and mounting samba
##shared folders on a network while being easy yet functional. 
##Copyright (C) <2007>  <David Braker>
##    This program is free software; you can redistribute it and/or modify
##    it under the terms of the GNU General Public License as published by
##    the Free Software Foundation; either version 2 of the License, or
##    (at your option) any later version.

##    This program is distributed in the hope that it will be useful,
##    but WITHOUT ANY WARRANTY; without even the implied warranty of
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##    GNU General Public License for more details.

##    You should have received a copy of the GNU General Public License along
##    with this program; if not, write to the Free Software Foundation, Inc.,
##    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
##On Debian GNU/Linux system you can find a copy of this
##license in `/usr/share/common-licenses/GPL'.

VERSION="1.04.6"
###think i fixed the bug where the progress bar for searching for workgroups would fail to stop 
##fixed problem with reading workgroups from the configuration file due to the change to configobj.
##will not mount the same share twice.
##removed un-used variables
##converted the last of ConfigParser to use a dictionary instead since it is a temporary storage in order to remove un-needed dependancies
##removed un-needed modules
##added activation of search when <Enter> is pressed in the entry box
##storing current unames and pw not working at the moment. not added when entered.-- FIXED
##added bookmark feature
import pango
import  gtk,commands,sys,os,threading,time,gobject,configobj,gettext,subprocess,stat
APP = 'smb-browser'
DIR = '/usr/share/locale/'
gettext.bindtextdomain(APP, DIR)
gettext.textdomain(APP)
_ = gettext.gettext
if len(sys.argv)>1:
	ARG=sys.argv[1]
	if ARG=="-v":
		print _("verbose mode")
	elif ARG=="-V":
		print _("Smb-Browser Version: "),VERSION
		sys.exit()
	else:
		print "Usage:"
		print "\t"+_("-v verbose")
		print "\t"+_("-V print Version")
		print "\t"+_("-h print this usage information")
		sys.exit()
else:
	sys.stdout=open("/dev/null", 'w')
	sys.stdin=open("/dev/null", 'r')	
gtk.gdk.threads_init()
HOME_PATH=os.path.expanduser("~")
configfile=HOME_PATH+"/.smb-browser.conf"
print "Configuration is stored in: "+configfile
conf="conf";hostname='';mntlocal='';userinfo="default";unmnt=''
info_data=gtk.Label("")
info_lbl=gtk.Label("\t"+_("Computer Information"))
host_ip_dict={}
FIRST_RUN=False;DEPTH1=False;DEPTH2=False;DEPTH3=False;FIND=False;RUN=False;CLEARING=False;SELECTED_BOOKMARK=''
SMBMOUNT_CMD="smbmount"
SMBUMOUNT_CMD="smbumount"
whereiscmd=subprocess.Popen("whereis mount.cifs",shell=True,stdout=subprocess.PIPE)
output=whereiscmd.stdout.readlines()
whereiscmd.stdout.close()
for x in output[0].split():
	if "mount.cifs" in x:
		MOUNT_CIFS_CMD=x
		UMOUNT_CIFS_CMD=x.split("mount.cifs")[0].rstrip("/")+"/umount.cifs"
		break
	else:
		MOUNT_CIFS_CMD=None


print MOUNT_CIFS_CMD
print UMOUNT_CIFS_CMD
###############
def create_default_conf():
	tmpwgs=""
	nmcmd=subprocess.Popen("nmblookup -A localhost",shell=True,stdout=subprocess.PIPE)
	nm=nmcmd.stdout.readlines()
	nmcmd.stdout.close()
#	nm=os.popen("nmblookup -A localhost")
	for line in nm:
		if "<00>" in line:
			if "<GROUP>" in line:
				line=line.rstrip()
				line=line.split()
				tmpwgs=line[0]
#	nm.close()
	if tmpwgs =="":
		print "starting"
		smbclcmd=subprocess.Popen("smbclient -NL localhost",shell=True,stdout=subprocess.PIPE)
		wgl=smbclcmd.stdout.readlines()
		#wwgl=os.popen("smbclient -NL localhost")
		#wgl=wwgl.readlines()
		smbclcmd.stdout.close()
		if "Connection to localhost failed\n" not in wgl:
			for item in wgl:
				if "Workgroup" in item:
					if "Master" in item:
						y= wgl[wgl.index(item)+2:len(wgl)]
						for item in y:
							name=item.rsplit(" ",1)[0].strip()
							tmpwgs=name
#		wwgl.close()
	return {'conf': {'version':VERSION, 'username': 'username', 'workgroup': tmpwgs, 'password': 'password', 'filemanager': 'thunar', 'mntlocal': HOME_PATH+"/mnt", 'flag': 'True', 'wgflag': 'False', 'clean': 'False', 'first_run': 'True',"mount_command":"smbmount"}}
def update_config():
	print "updating configuration"
	default_config=create_default_conf()
	for setting in default_config[conf]:
		if setting not in config[conf]:
			print setting
			config[conf][setting]=default_config[conf][setting]
		elif setting in["wgflag","flag","clean","first_run"]:
			if config[conf][setting].lower() not in ["true","false"]:
				config[conf][setting]=default_config[conf][setting]
	config[conf]["version"]=default_config[conf]["version"]
	config.write()
	print "done updateing configuration"
	
def import_conf():
	try:
		config=configobj.ConfigObj("/home/david/.smb-browser.conf")
	except:
		print "this is the except"
		config=False
	return config
if os.access(configfile,0)==False:
	print "no configuration file"
	config=configobj.ConfigObj(create_default_conf())
	config.filename=configfile
	config.write()
else:
	config=import_conf()
	if config==False:
		print "import of configuration file failed"
		config=configobj.ConfigObj(create_default_conf())
		config.filename=configfile
		config.write()
	elif conf in config.keys():
		print conf+" present"
		if "version" in config[conf]:
			file_version=config[conf]["version"]
			versions=[file_version,VERSION]
			versions.sort()
			versions.reverse()
			if versions[0]==versions[1]:
				print "versions are =, we need do nothing here"
			else:
				print "update 1"
				update_config()
		else:
			print "update 2"
			update_config()
	else:
		config=configobj.ConfigObj(create_default_conf())
		config.filename=configfile
		config.write()		

###############
def check_for_mnt_cmd(cmd):
	cmdinfo=subprocess.Popen(cmd+" -V ",shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	error=cmdinfo.stderr.readlines()
	output=cmdinfo.stdout.readlines()
	if error!=[]:
		if "command not found" in error[0]:
			print "command not found"
			return False
	else:
		if "version" in output[0].lower():
			print "version was printed, command present"
		return True

username_pw_list={}
#####parser####
def ERROR(MSG):
	d = gtk.MessageDialog(parent=None, flags=gtk.MESSAGE_WARNING, buttons=gtk.BUTTONS_OK, message_format=MSG)
	d.set_position(gtk.WIN_POS_CENTER_ALWAYS)
	d.show_all()
	d.run()
	d.destroy()
	
def clean(clncheckbox):
	x=clncheckbox.get_active()
def findwgs():
	global FIND,RUN,timer2
	if FIND==True:
		print "Already finding..."
		return
	print "finding wgs"
	start_bar2(_("Searching for workgroups"))
	FIND=True
	RUN=True
	MASTER_IPS=[]
	tup= wg_entry.get_text().strip()
	savedwgs=[]
	if tup !="":
		for item in tup.split(","):
			print item
			savedwgs.append(item)
	print "savedwgs includes from the find func",savedwgs
	if checkbox.get_active()==True:
		user=" -NL "
	elif checkbox.get_active()==False:
		user=" -U "+uname_entry.get_text()+"%"+pw_entry.get_text()+" -L "
	gtk.gdk.threads_enter()
	wgtreestore.clear();mnt.set_sensitive(False);	
	gtk.gdk.threads_leave()
	nmlcmd=subprocess.Popen("nmblookup \"*\"",shell=True,stdout=subprocess.PIPE)
	OUTPUT=nmlcmd.stdout.readlines()
	nmlcmd.stdout.close()
#	OUTPUT=os.popen("nmblookup \"*\"")
	for line in OUTPUT:
		if "<00>" in line:
			line=line.rstrip().split()
			MASTER_IPS.append(line[0])
#	OUTPUT.close()
	nmbMcmd=subprocess.Popen("nmblookup -M -- -",shell=True,stdout=subprocess.PIPE)
	OUTPUT=nmbMcmd.stdout.readlines()
#	OUTPUT=os.popen("nmblookup -M -- -")
	for line in OUTPUT:
		if "<" in line:
			line=line.rstrip().split()
			if line[0] not in MASTER_IPS:
				MASTER_IPS.append(line[0])
#	OUTPUT.close()
	nmbMcmd.stdout.close()
	###here we have a list of ips for the master browsers, now we will get names for them and their workgrous####
	WORKGROUPS=[]
	MASTERS=[]
	for IP in MASTER_IPS:
		nmbAcmd=subprocess.Popen("nmblookup -A "+IP,shell=True,stdout=subprocess.PIPE)
		OUTPUT=nmbAcmd.stdout.readlines()
		nmbAcmd.stdout.close()
		#OUTPUT=os.popen("nmblookup -A "+IP)
		for line in OUTPUT:
			if "<00>" in line:
#				print line
				if "<GROUP>" not in line:
					##this gives us the name of the master browser##
					line=line.rstrip().split()
					if line[0] not in MASTERS:
						MASTERS.append(line[0])
				if "<GROUP>" in line:
#					print line
					##this gives us the name of the workgroup that the master browser is in##
					if "<00>" in line:
						line=line[line.index('\t')+1:line.index("<00>")].strip()
						if line=="":
							print "empty2"
						elif line not in WORKGROUPS:
							print "adding1",line
							WORKGROUPS.append(line)
							gtk.gdk.threads_enter()
							wgtreestore.append(None, [line])
							gtk.gdk.threads_leave()
		#OUTPUT.close()
	###here we begin to scan each master browser for a list of alternate workgroups###"
	print MASTERS
#	time.sleep(2)
	for pc in MASTERS:
		print pc
		smbcmd=subprocess.Popen("nmblookup -A "+IP,shell=True,stdout=subprocess.PIPE,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
		OUTPUT2=smbcmd.stdout.readlines()
		smbcmd.stdin.close()
		smbcmd.stdout.close()
		smbcmd.stderr.close()
#		null,OUTPUT,null2=os.popen3("smbclient -NL "+pc)
#		OUTPUT2=OUTPUT.readlines()
		for x in OUTPUT2:
			if "LOGON_FAILURE" in x:
				MSG=x+"\n"+_("Please check that your username and password are correct. Or check the 'guest' box in the preferences.")
				ERROR(MSG)			
		for line in OUTPUT2:
			if "Workgroup" in line:
				if "Master" in line:
					y=OUTPUT2[OUTPUT2.index(line)+2:len(OUTPUT2)]
					for item in y:
						name=item.rsplit(" ",1)[0].strip()
#						WORKGROUPS=[]#this was added to force the following section
						if name not in WORKGROUPS:
							print name,"<a name"
							if name !="":
								WORKGROUPS.append(name)
								gtk.gdk.threads_enter()
								piter = wgtreestore.append(None, [name])
								gtk.gdk.threads_leave()
						else:
							print name+" already exists"
#		null.close();null2.close();OUTPUT.close()
		print "Done Closing"
		FIND=False
	gtk.gdk.threads_enter()
	for item in savedwgs:
		if item not in WORKGROUPS:
			piter = wgtreestore.append(None, [item])
	if WORKGROUPS==[]:
		MSG=_("Sorry but no workgroups were found. If you know the name of a workgroup on your network please specify it in the 'Preferences' section. You might also check you connection.")
		ERROR(MSG)
	gtk.gdk.threads_leave()
	end_bar2(_("Done searching for workgroups"))
	RUN=False
def start_bar(label):
	global timer,DEPTH1,DEPTH2,DEPTH3
	if DEPTH1 or DEPTH2== True:
		print "not starting"
		return
	print "CONT"
	gtk.gdk.threads_enter()
	progbar.show()
	progbar.set_text(label)
	def update_window():
		progbar.pulse()
		return True
	timer = gobject.timeout_add(90,update_window)
	gtk.gdk.threads_leave()
def end_bar(label):
	global timer,bar_state,DEPTH1,DEPTH2,DEPTH3
	print DEPTH1,DEPTH2,DEPTH3
	if DEPTH1 or DEPTH2 == True:
		print "not ending haha"
		return
	print "end activated"
	gtk.gdk.threads_enter()
	progbar.set_text(label)
	gobject.source_remove(timer)
	progbar.set_fraction(0)
	progbar.set_text(_("Finished."))
	bar_state=False
	gtk.gdk.threads_leave()
def start_bar2(label):
	global timer2,FIND
	if FIND== True:
		print "not starting"
		return
	print "CONT"
	gtk.gdk.threads_enter()
	scan_progbar.show()
	scan_progbar.set_text(label)
	def update_window():
		scan_progbar.pulse()
		return True
	timer2 = gobject.timeout_add(90,update_window)
	gtk.gdk.threads_leave()
def end_bar2(label):
	print "end bar 2"
	global timer2,FIND
	print FIND
	if  FIND== True:
		print "not ending"
		return
	print "end activated"
	gtk.gdk.threads_enter()
	scan_progbar.set_text(label)
	gobject.source_remove(timer2)
	scan_progbar.set_fraction(0)
	scan_progbar.set_text(_("Finished."))
	gtk.gdk.threads_leave()
def wg_processor(wg_name,userinfo):
	global DEPTH1,DEPTH2,DEPTH3
	print "wg processor"
	if wg_name=="Search Results":
		print "Not a valid workgroup"
		return
	start_bar(_("Scanning..."))
	if DEPTH1==True:
		print "depth 1 running, not continuing"
		return
	DEPTH1=True
	s = wgtreeview.get_selection()
	selected_treestore, iter = s.get_selected()
	print parent
	depth=len(s.get_selected_rows()[1][0])
	mnt.set_sensitive(False)
	wgtreemodel=wgtreeview.get_model()
	xy=wgtreestore.get_path(iter)
	treeiter=wgtreestore.iter_nth_child(iter, 0)
##		this loop empties the workgroup of hosts/computers##
	while treeiter !=None:
		gtk.gdk.threads_enter()
		print wgtreestore.get_value(treeiter,0)
		wgtreestore.remove(treeiter)
		treeiter=wgtreestore.iter_nth_child(iter, 0)
		gtk.gdk.threads_leave()
#		time.sleep(3)
#	start_bar("Scanning...")
	info_lbl.set_text("\t"+_("Computer Information"))
	print wg_name+" is a workgroup"
##		this section deals with workgroups containing the character  ( ' )###
	if "\"" in wg_name:
		wg_name="\'"+wg_name+"\'"
	else:
		wg_name="\""+wg_name+"\""
	print wg_name
	print "userinfo = ",userinfo
	print "wg_name = ",wg_name
	nmblcmd=subprocess.Popen("nmblookup "+wg_name.strip(),shell=True,stdout=subprocess.PIPE)
	OUTPUT=nmblcmd.stdout.readlines()
#	OUTPUT=os.popen("nmblookup "+wg_name.strip())
	nmblcmd.stdout.close()
	IP_ADRESSES=[]
	for line in OUTPUT:
#		print line
		if "<00>" in line:
			if line.rstrip().split()[0] not in IP_ADRESSES:
				IP_ADRESSES.append(line.rstrip().split()[0])
#	OUTPUT.close()
	print IP_ADRESSES,"<<< here are the IP_ADRESSES"
##		THIS NEXT LOOP FINDS THE COMPUTER NAME FOR EACH IP ADDRESS##
	for IP in IP_ADRESSES:
		nmbAcmd=subprocess.Popen("nmblookup -A "+IP,shell=True,stdout=subprocess.PIPE)
		OUTPUT=nmbAcmd.stdout.readlines()
		nmbAcmd.stdout.close()
		#OUTPUT=os.popen("nmblookup -A "+IP)
		for line in OUTPUT:
			if "<00>" in line:
				if "<GROUP>" not in line:
					name=line.rstrip().split()[0]
					gtk.gdk.threads_enter()
					wgtreestore.append(iter, [(name)])
					wgtreeview.expand_row(xy,True)
					gtk.gdk.threads_leave()
#					time.sleep(2)
#		OUTPUT.close()
	gtk.gdk.threads_enter()	
	if wgtreestore.iter_nth_child(iter, 0) == None:
		MSG=_("Sorry, We could not locate any hosts on")+" "+wg_name+"."
		ERROR(MSG)
	gtk.gdk.threads_leave()
	DEPTH1=False
	end_bar(_("Done Scanning."))
	
	
def host_processor(hostname,userinfo,iter):
	global DEPTH2
	get_from_user=False
	if DEPTH2==True:
		print "depth 2 running, not continuing"
		return
	endit=True
	start_bar(_("Scanning..."))
	DEPTH2=True
	set_pc_info(hostname)
	print host_ip_dict,"this is the dict of hosts and ips"
	shares=[]
	treeiter=wgtreestore.iter_nth_child(iter, 0)
##	this loop empties the list of shares on the host##
	while treeiter !=None:
		gtk.gdk.threads_enter()
		print wgtreestore.get_value(treeiter,0)
		wgtreestore.remove(treeiter)
		treeiter=wgtreestore.iter_nth_child(iter, 0)
		gtk.gdk.threads_leave()
	shares=[]
	print "STARTING"
	if hostname in host_ip_dict.keys():
		print host_ip_dict[hostname]
		hostname1=host_ip_dict[hostname]
	else:
		nmbLcmd=subprocess.Popen("nmblookup "+hostname,shell=True,stdout=subprocess.PIPE)
		nmbfile=nmbLcmd.stdout.readlines()
		nmbLcmd.stdout.close()
		#nmbfile=os.popen("nmblookup "+hostname)
		print "2"
		for line in nmbfile:
#			print line
			if "<00>" in line:
				ip_add=line.split()[0]
				print "IP Address: ",line.split()[0]
#		nmbfile.close()
		print "NOT IN THE HOSTIP DICT"
		hostname1="\'"+hostname+"\'"
	if userinfo=="default":
		if checkbox.get_active()==True:
			user=" -NL "
		elif checkbox.get_active()==False:
			user=" -U "+uname_entry.get_text()+"%"+pw_entry.get_text()+" -L "
	else:
		user=userinfo
##checking as guest
	smbCcmd=subprocess.Popen("smbclient  -NL"+hostname1+" -I "+ip_add,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	#null,fh2,null2=os.popen3("smbclient  -NL"+hostname1+" -I "+ip_add)
	fh2=smbCcmd.stdout.readlines()
	smbCcmd.stdout.close()
	smbCcmd.stderr.close()
	smbCcmd.stdin.close()
	for line in fh2:
		if "Disk" in line:
			line= line[line.index("\t")+1:line.index(" Disk      ")]
			line=line.rstrip()
			if line not in shares:
				print "added as guest",line
				shares.append(line)
				print shares
	print "done with guest"
#	null.close();fh2.close();null2.close()
##checking as user  if  so set in the preferences
	if user.strip()!="-NL":
		print "##check as user"
		print "smbclient  "+user+hostname1+" -I "+ip_add
		smbCLcmd=subprocess.Popen("smbclient  "+user+hostname1+" -I "+ip_add,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		#null,fh2,null2=os.popen3("smbclient  "+user+hostname1+" -I "+ip_add)
		fh2=smbCLcmd.stdout.readlines()
		smbCLcmd.stdout.close()
		smbCLcmd.stderr.close()
		smbCLcmd.stdin.close()		
		for line in fh2:
			print line
			if "LOGON_FAIL" in line:
				print "##checking for user info in the currently saved list"
				print "Logon failed"
				if hostname in username_pw_list.keys():
					print "WE found it in the new list"
					user=" -U "+username_pw_list[hostname]["user"]+"%"+username_pw_list[hostname]["password"]+" -L "
					print "smbclient  "+user+hostname1+" -I "+ip_add
					smbclcmd=subprocess.Popen("smbclient  "+user+hostname1+" -I "+ip_add,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
					#null,fh2,null2=os.popen3("smbclient  "+user+hostname1+" -I "+ip_add)
					fh2=smbclcmd.stdout.readlines()
					smbclcmd.stdout.close()
					smbclcmd.stderr.close()
					smbclcmd.stdin.close()
					for line in fh2:
						if "Disk" in line:
							line= line[line.index("\t")+1:line.index(" Disk      ")]
							line=line.rstrip()
							if line not in shares:
								print "added as a user",line
								shares.append(line)
						elif "LOGON_FAIL" in line:
							MSG=_("Logon Failed! Please enter your:")
							get_from_user=True
					#null.close();null2.close();fh2.close()
				else:
					MSG=_("Logon Failed! Please enter your:")
					get_from_user=True
			if "Disk" in line:
				line= line[line.index("\t")+1:line.index(" Disk      ")]
				line=line.rstrip()
				if line not in shares:
					shares.append(line)
#		null.close();null2.close();fh2.close()
	xy=wgtreestore.get_path(iter)
	for item in shares:
		gtk.gdk.threads_enter()
		wgtreestore.append(iter,[(item)])
		wgtreeview.expand_row(xy,True)
		gtk.gdk.threads_leave()
#		time.sleep(2)
	if shares==[]:
		MSG=_("No shares were found. Please check that")+" "+hostname+_("is sharing files. You may need to supply a username and password to find the shares.")
		get_from_user=True
#	fh2.close()
	if get_from_user==True:
##if  a login failed or no shares were found, we ask the user for a username and password
		gtk.gdk.threads_enter()
		username,password= get_uname_pw(None,MSG,hostname)
		gtk.gdk.threads_leave()
		if username and password != None:
			userinfo=" -U "+username+"%"+password+" -L "
		else:
			if endit==True:
				DEPTH2=False
				end_bar(_("Done Scanning."))
			return
		print hostname,userinfo,iter
		if endit==True:
			DEPTH2=False
			end_bar(_("Done Scanning."))
		#DEPTH2=False
		return host_processor(hostname,userinfo,iter)
	#DEPTH2=False
	if endit==True:
		DEPTH2=False
		end_bar(_("Done Scanning."))
	
	
def scanwgornb(wgtreeviewx,userinfo):
	global DEPTH1,DEPTH2,DEPTH3,wgtreeview,parent,ip_add#,ips,
	s = wgtreeview.get_selection()
	selected_treestore, iter = s.get_selected()
	if iter:
		parent=wgtreeview.get_model().iter_parent(iter)
	else:
		return
	depth=len(s.get_selected_rows()[1][0])
	mnt.set_sensitive(False)
	itemclicked =selected_treestore.get_value(iter, 0)
	if depth==1:
		print "processing workgroups"
		return wg_processor(itemclicked,None)
	elif depth==2:
		print "host/computer name processing"
#		set_pc_info(itemclicked)
		return host_processor(itemclicked,userinfo,iter)
	elif depth==3:
		print "a share name was selected setting options"
		if DEPTH3==True:
			print "depth 3 running, not continuing"
			return
		DEPTH3=True
		print "this section sets mount button sensitive since the selection is a share. depth =",depth
		gtk.gdk.threads_enter()
		itemclicked=selected_treestore.get_value(parent,0)
		mnt.set_sensitive(True)
		gtk.gdk.threads_leave()
		parent_iter = wgtreestore.iter_parent(iter)
		grand_parent_iter = wgtreestore.iter_parent(parent_iter)
		grand_parent=wgtreestore.get_value(grand_parent_iter,0)
		if grand_parent=="Search Results":
			ip_add=wgtreestore.get_value(parent_iter,0)
		DEPTH3=False
		set_pc_info(itemclicked)
def set_pc_info(hostname):
	global ip_add
	print host_ip_dict.keys(),"dict"
	if hostname in host_ip_dict.keys():
		print "depth did not = 1 and thus we are populating the host information"
		print hostname
		ip_add=host_ip_dict[hostname]
		info_lbl.set_text("\t"+_("Computer Information")+"\n"+_("Host name: ")+hostname+"\n"+_("IP Address: ")+ip_add)
	else:
		nmbcmd=subprocess.Popen("nmblookup "+hostname,shell=True,stdout=subprocess.PIPE)
		nmbfile=nmbcmd.stdout.readlines()
		nmbcmd.stdout.close()
#		nmbfile=os.popen("nmblookup "+hostname)
		print "2"
		for line in nmbfile:
#			print line
			if "<00>" in line:
				ip_add=line.split()[0]
				print "IP Address: ",line.split()[0]
				info_lbl.set_text("\t"+_("Computer Information")+"\n"+_("Host name: ")+hostname+"\n"+_("IP Address: ")+ip_add)
#		nmbfile.close()
def st_func(button):
#	print button.get_label()
#	print "starting"
	udt=UD_thread()
	udt.setDaemon(1)
	udt.start()
def st_scanwgornb(widget,userinfo1):
#	print button.get_label()
#	print "starting"
	global userinfo
	userinfo=userinfo1
	sct=scan_thread()
	sct.setDaemon(1)
	sct.start()
def foldersel(foldbtn):	
	global filew
	filew = gtk.FileChooserDialog(title=_("Choose a folder"),action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
		buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
	response=filew.run()
	if response ==gtk.RESPONSE_OK:
		mntlocal_entry.set_text(filew.get_filename())
	filew.destroy()
	
def umount(umntbtn):
	global unmnt
	if "cifs" in config[conf]["mount_command"].strip():
		UMOUNT_CMD=UMOUNT_CIFS_CMD
	elif "smbmount" in config[conf]["mount_command"].strip():
		UMOUNT_CMD=SMBUMOUNT_CMD
	(badd,output)=commands.getstatusoutput(UMOUNT_CMD+" \'"+unmnt+"\'")
	if badd:
			ERROR(output)
	if not badd:
		if clncheckbox.get_active() == True:
			os.removedirs(unmnt)
	umntbtn.set_sensitive(False)
	add_bookmark_btn.set_sensitive(False)
#	print ("smbumount "+"\'"+unmnt+"\'")
	progbar.set_text(unmnt+" unmounted.")
	unmnt=""
	return lsmounted()

def get_uname_pw(nothing,MSG,hostname):
	print "Getting uname and pw from user"
	info_window = gtk.MessageDialog(parent=None, flags=gtk.MESSAGE_WARNING, message_format=MSG)
	info_window.add_button(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL)
	info_window.add_button(gtk.STOCK_OK,gtk.RESPONSE_OK)
	uname=gtk.Entry()
	passwd=gtk.Entry()
	passwd.set_visibility(False)
	passwd.set_invisible_char("*") 
	UNAME_label=gtk.Label(_("Username:"))
	passwd_label=gtk.Label(_("Password:"))
	for widget in info_window:
		widget.pack_start(UNAME_label,False,False,2)
		widget.pack_start(uname,False,False,2)
		widget.pack_start(passwd_label,False,False,2)
		widget.pack_start(passwd,False,False,2)
	info_window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
	info_window.show_all()
	response=info_window.run()
	if response==gtk.RESPONSE_OK:
		print hostname
		if hostname not in username_pw_list.keys():
			username_pw_list[hostname]={}
		user_name=uname.get_text()
		password=passwd.get_text()
		username_pw_list[hostname]["user"]=user_name
		username_pw_list[hostname]["password"]=password
		info_window.destroy()
		return user_name,password
	else:
		info_window.destroy()
		print "canceled"
		return None,None
	print response," this is the repsonze"

def mount_by_user_input(addoptions,MSG,sharemnt,mnt):
	section=sharemnt.lstrip("'//").split("/")[0]
	username,password= get_uname_pw(None,MSG,section)
	MOUNT_CMD=config[conf]["mount_command"]
	print username
	print password
	if username and password != None:
		user_options="username="+username+"%"+password
	else:
		return
	failed2,output2=commands.getstatusoutput(MOUNT_CMD+"  "+sharemnt+" "+mnt+" -o "+user_options+","+addoptions)
	print MOUNT_CMD+"  "+sharemnt+" "+mnt+" -o "+user_options+","+addoptions
	if failed2:
		print "####################\n################"
		print output2
		return mount_by_user_input(addoptions," "+_("Access Denied! Please enter your:"),sharemnt,mnt)
	else:
		#~ bookmarks_cmb.set_active(0)
		progbar.set_text(_("Done mounting")+" "+sharemnt)
		return lsmounted()

def mount(widget):
	print "######### starting mount#################"
	global ip_add,CLEARING,SELECTED_BOOKMARK
	MOUNT_CMD=config[conf]["mount_command"]
	if MOUNT_CMD=="NONE":
		ERROR( "no mount command found")
		return
	##########additional options###########
	if type(widget)==gtk.Button:
		(selected_treestore, iter) = wgtreeview.get_selection().get_selected()
		sharename =selected_treestore.get_value(iter, 0)
		hostname=wgtreestore.get_value(selected_treestore.iter_parent(iter),0)
		if hostname in host_ip_dict:
			sharemnt="\'//"+host_ip_dict[hostname]+"/"+sharename+"\'"
		else:
			sharemnt="\'//"+hostname+"/"+sharename+"\'"
		host=hostname+"/"
		mnt="\'"+mntlocal+ host+sharename+"\'"
	elif type(widget)==gtk.MenuItem:
		print "menu activatd"
		print "#################"
		hostname= SELECTED_BOOMARK.split("/")[0]
		key=SELECTED_BOOMARK
		print hostname
		print "#################"
		nmcmd=subprocess.Popen("nmblookup "+hostname,shell=True,stdout=subprocess.PIPE)
		nmbinfo=nmcmd.stdout.readlines()
		nmcmd.stdout.close()
		#nmbinfo =os.popen("nmblookup "+hostname)
		for line in nmbinfo:
			if "<00>" in line:
				ip_add=line.split()[0]
		print SELECTED_BOOMARK
		sharemnt="\'"+config["bookmarks"][key]["share_name"]+"\'"
		mnt="\'"+config["bookmarks"][key]["mount_location"]+"\'"
#		nmbinfo.close()
	###the server/share names and mount location have been set above, now we get all the options other than uname and pw
	addoptions=''
	MN=mntops_entry.get_text().strip(",")
	if MN  !="":
		addoptions=addoptions+","+MN
	model = mnt_rwro.get_model()
	index = mnt_rwro.get_active()
	if model[index][0] =="ro":
		addoptions=addoptions+",ro"
	print addoptions+"this is add options"
	addoptions=addoptions+"ip="+ip_add
	#############end additional options#########
	if checkbox.get_active() ==True:
		user_options="sec=none,user=guest"
	else:
		user_options="username="+uname_entry.get_text()+"%"+pw_entry.get_text()
	print addoptions
	print user_options
	###start the mounting process
	###first try by settings
	print sharemnt
	mntedcmd=subprocess.Popen("mount",shell=True,stdout=subprocess.PIPE)
	mounted_volumes=mntedcmd.stdout.readlines()
	mntedcmd.stdout.close()
#	mounted_volumes=os.popen("mount")
	for line in mounted_volumes:
		if line.startswith(sharemnt.strip("'")):
			print "already mounted"
			mounted_volumes.close()
			#~ bookmarks_cmb.set_active(0)
#			mounted_volumes.close()
			return ERROR(_("That share is already mounted"))
			
	#mounted_volumes.close()
	if os.access(mnt,0)==False:
		mkdircmd=subprocess.Popen("mkdir -p "+mnt,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		#(error,output)=commands.getstatusoutput("mkdir -p "+mnt)
		error=mkdircmd.stderr.readlines()
		if error != []:
			ERROR(error[0])
	failed1,output1=commands.getstatusoutput(MOUNT_CMD+"  "+sharemnt+" "+mnt+" -o "+user_options+","+addoptions)
	print MOUNT_CMD+"  "+sharemnt+" "+mnt+" -o "+user_options+","+addoptions," <<<1"
	if failed1:
		print output1
		if "denied" in output1:
			print "lets get check our running list for info"
			if hostname in username_pw_list.keys():
				print "FOUND HOSTNAME"
				user_options="username="+username_pw_list[hostname]["user"]+"%"+username_pw_list[hostname]["password"]
				failed2,output2=commands.getstatusoutput(MOUNT_CMD+"  "+sharemnt+" "+mnt+" -o "+user_options+","+addoptions)
				print MOUNT_CMD+"  "+sharemnt+" "+mnt+" -o "+user_options+","+addoptions," <<<2"
				if failed2:
					if "denied" in output2:
						return mount_by_user_input(addoptions," "+_("Access Denied! Please enter your:"),sharemnt,mnt)
						#return mount_by_user_input(addoptions," Access Denied! Please enter \n your:")
				else:
					#~ bookmarks_cmb.set_active(0)
					progbar.set_text(_("Done mounting")+" "+sharemnt)
					return lsmounted()
			else:
				return mount_by_user_input(addoptions," "+_("Access Denied! Please enter your:"),sharemnt,mnt)
	else:
		#~ bookmarks_cmb.set_active(0)
		progbar.set_text(_("Done mounting")+" "+sharemnt)
		return lsmounted()


def search(srchbtn,userinfo):
	global ip_add
	print "this is activated when you click the search by name or ip button"
	hostname=srch_entry.get_text().upper().strip()
	if hostname.strip()=="":
		return
	NEXT=False
	method="ip"
##	OK FIRST LETS GET PARSE THE WORKGROUPS IN THE WGTREESTORE##
	WORKGROUPS=[]
	for x in wgtreestore:
		WORKGROUPS.append(wgtreestore.get_value(x.iter,0))
## 	this loop parses the hostname that is being searched for to see if it contains any letters... thus being a name not an ip##
	for x in hostname:
		if x !=".":
			try: 
				int(x)
			except:
				method="Name"
				break
	print "Searching by "+method
	if method =="Name":	##this method searches by name
		nmbLHcmd=subprocess.Popen("nmblookup "+hostname,shell=True,stdout=subprocess.PIPE)
		OUTPUT=nmbLHcmd.stdout.readlines()
		nmbLHcmd.stdout.close()
		#OUTPUT=os.popen("nmblookup "+hostname)
		for line in OUTPUT:
			if "<00>" in line:
#				print line
				hostip=line.rstrip().split()[0]
				NEXT=True
			elif "failed to find" in line:
				return ERROR(line)
#		OUTPUT.close()
	else:##this method searches by ip adress
		smbCHcmd=subprocess.Popen("smbclient -NL "+hostname,shell=True,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
		OUTPUT=smbCHcmd.stdout.readlines()
#		null,OUTPUT,null2=os.popen3("smbclient -NL "+hostname)
		smbCHcmd.stdout.close();smbCHcmd.stderr.close();smbCHcmd.stdin.close()
		for line in OUTPUT:
#			print line
			if "Connection to "+hostname+" failed" in line:
				NEXT=False
				return ERROR(line)
			else:
				hostip=hostname
				NEXT=True
		#OUTPUT.close();null.close();null2.close()
	if NEXT==True:		##here we do somethign with the ip of the computer being searched for"
		print "Running NEXT"
		wgname=''		##here we are just setting a variable to be filled later
		nmbHIcmd=subprocess.Popen("nmblookup -A "+hostip,shell=True,stdout=subprocess.PIPE)
		OUTPUT=nmbHIcmd.stdout.readlines()
		nmbHIcmd.stdout.close()
		#OUTPUT=os.popen("nmblookup -A "+hostip)
#		OUTPUT=open("test-file")
		for line in OUTPUT:
			if "No reply from" in line:
				pcname=hostip
				ip_add=hostip
				wgname="Search Results"
				break
			if "<00>" in line:
				if "<GROUP>" in line:## this finds out workgroup name
					line=line.lstrip()
					wgname=line.split()[0]
				if "<GROUP>" not in line:## here we get the name of the pc##
					pcname=line.rstrip().split()[0]
		#OUTPUT.close()
		n=1
		ITER=wgtreestore.iter_nth_child(None, 0)
		FOUND=False
		for x in wgtreestore:
			cur_name= wgtreestore.get_value(ITER,0).strip()
			if cur_name == wgname:
				FOUND=True
				break
			ITER=wgtreestore.iter_nth_child(None, n)
			n=n+1
		if FOUND==False:
			ITER= wgtreestore.append(None, [wgname])
		ITER2=wgtreestore.iter_nth_child(ITER, 0)
		print wgtreestore.get_value(ITER,0).strip()
		n=0
		PC_PRESENT=False
		treeiter=wgtreestore.iter_nth_child(ITER, n)
		while treeiter !=None:
			cur_name=wgtreestore.get_value(treeiter,0)
			n=n+1
			treeiter=wgtreestore.iter_nth_child(ITER, n)
			if cur_name==pcname:
				PC_PRESENT=True
		if PC_PRESENT == False:
			wgtreestore.append(ITER, [pcname])
			wgtreeview.expand_row(wgtreestore.get_path(ITER),True)
def lsmounted():
	lshare=[]
	lsmntcmd=subprocess.Popen("mount",shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	output=lsmntcmd.stdout.readlines()
	lsmntcmd.stdout.close();lsmntcmd.stderr.close()
#	error,output=os.popen2("mount")
	for item in output:
		if "smbfs" in item:
			item2=item.rstrip()
			lshare.append(item2[item2.index(" on ")+4:item2.index(" type smbfs")])
		elif "cifs" in item:
			item3=item.rstrip()
			print item3
			lshare.append(item3[item3.index(" on ")+4:item3.index(" type cifs")])
#	error.close()
#	output.close()
	mntedlist.clear()
	z=0	
	for item in lshare:	
		iter = mntedlist.append( [z,item] )
		z=z+1
def addprefsel(mntedtreeview):
	global unmnt
	s = mntedtreeview.get_selection()
	(ls, iter) = s.get_selected()	
	if iter is None:
		umntbtn.set_sensitive(False)
		add_bookmark_btn.set_sensitive(False)
	else:
		unmnt=ls.get_value(iter, 1)
		umntbtn.set_sensitive(True)
		add_bookmark_btn.set_sensitive(True)
def addprefsel2(mntedtreeview,x,y):
	return fm(fmbtn)
def fm(fmbtn):
	global unmnt
	fmngr=fm_entry.get_text()
	if unmnt !='':
		location=unmnt
		print fmngr+" \""+location+"\" &"+"1"
		os.system(fmngr+" \""+location+"\" &")
	else:
		print fmngr+" $HOME/mnt &"+"2"
		os.system(fmngr+" $HOME/mnt &")

def save(savebtn):
	y=checkbox.get_active()
	x=wgcheckbox.get_active()
	z=clncheckbox.get_active()
	conf="conf"
	pwvar= pw_entry.get_text()
	unamevar=uname_entry.get_text()
	fmvar=fm_entry.get_text()
	localvar=mntlocal_entry.get_text()
#	mnt_cmd="mount.cifs"
	if mnt_cmd_smb.get_active() == True:
		mnt_cmd=SMBMOUNT_CMD
	elif mnt_cmd_cifs.get_active()==True:
		mnt_cmd=MOUNT_CIFS_CMD
		#check if MOUNT_CIFS_CMD is suid
		if os.stat(MOUNT_CIFS_CMD).st_mode & stat.S_ISUID ==0:
			if os.getuid()!=0:
				print "not SUID and not root"
				ERROR(_("It appears that you are not 'root' and that your mount.cifs command is not SUID. Please fix this with the following as root in a terminal: chmod u+s ")+str(MOUNT_CIFS_CMD))
				mnt_cmd_smb.set_active(True)
				return
	if check_for_mnt_cmd(mnt_cmd) ==False:
			if mnt_cmd ==SMBMOUNT_CMD:
				cmdtotry=MOUNT_CIFS_CMD
			else:
				cmdtotry=SMBMOUNT_CMD
			ERROR(_("It appears that the command which you have chosen does not exist, please try:")+" "+cmdtotry)
			return
	config[conf]["username"]=unamevar
	config[conf]["workgroup"]=wg_entry.get_text().upper()
	config[conf]["filemanager"]=fmvar
	config[conf]["password"]=pwvar
	config[conf]["mntlocal"]=localvar
	config[conf]["flag"]=y
	config[conf]["wgflag"]=x
	config[conf]["clean"]=z
	config[conf]["mount_command"]=mnt_cmd
	config.write()
	readconf()


def userfunc(checkbox):
	global flags
	x=checkbox.get_active()
	if x ==True:
		pw_entry.set_sensitive(False)
		uname_entry.set_sensitive(False)
	else:
		pw_entry.set_sensitive(True)
		uname_entry.set_sensitive(True)
def delete_event( widget, event=None, data=None):
	global RUN,DEPTH1,DEPTH2,DEPTH3
	if RUN or DEPTH1 or DEPTH2 or DEPTH3==True:
		print "killing program"
		os.kill(os.getpid(),9)
	gtk.main_quit()
	return False
def prt(button):
	print "clicked"


def load_bookmarks():
	print "updating bookmarks"
	global CLEARING,list_menu
	CLEARING=True
	#~ bookmark_liststore.clear()
	CLEARING=False
	#~ bookmark_liststore.append(["Select a Bookmark:"]) 
	#~ bookmarks_cmb.set_active(0)
	z=0	
	for x in list_menu:
		list_menu.remove(x)
	#~ bookmark_list.clear()
	if "bookmarks" in config.keys():
		print "present"
		for item in config["bookmarks"]:
			#~ bookmark_liststore.append([item]) 
			#~ iter = bookmark_list.append( [z,item] )
			#~ z=z+1
#for i in range(3):
			buf = item
			list_menu_items = gtk.MenuItem(buf)
			list_menu_items.add_events(gtk.gdk.BUTTON_PRESS_MASK)
			list_menu_items.connect("button-press-event", right_clicked)
			list_menu.append(list_menu_items)
			list_menu_items.connect("activate", mount)#, buf)
			list_menu_items.show()


	print "end of bookmark update"

def add_bookmark(add_btn):
	s = mntedtreeview.get_selection()
	print config.keys()
	if "bookmarks"  not in config.keys():
		print "adding bookmarks section to config"
		config["bookmarks"]={}
	(selected_treestore, iter) = s.get_selected()
	itemclicked =selected_treestore.get_value(iter, 1)
	mnted_vols_cmd=subprocess.Popen("mount",shell=True,stdout=subprocess.PIPE)
	mounted_volumes=mnted_vols_cmd.stdout.readlines()
	mnted_vols_cmd.stdout.close()
	#mounted_volumes=os.popen("mount")
	for line in mounted_volumes:
		if itemclicked in line:
			line=line.split(" on /")
			share=line[0].lstrip("//")
			if share not in config["bookmarks"]:
				#bookmark_liststore.append([share]) 
				print "bookmarking ",itemclicked
				config["bookmarks"][share]={}
				config["bookmarks"][share]["share_name"]="//"+share
				config["bookmarks"][share]["mount_location"]=itemclicked
				config.write()
				load_bookmarks()
			else:
				print "already bookmarked"
	#mounted_volumes.close()

def del_bookmark(widget):
	global SELECTED_BOOMARK
	print SELECTED_BOOMARK
	bookmark = SELECTED_BOOMARK
	dialog=gtk.MessageDialog(parent=window,flags=gtk.DIALOG_MODAL,type=gtk.MESSAGE_QUESTION,buttons=gtk.BUTTONS_YES_NO,message_format ="Are you sure you want to delete the bookmark for "+bookmark)
	dialog.set_position(gtk.WIN_POS_CENTER_ALWAYS)
	dialog.show_all()
	response=dialog.run()
	dialog.destroy()
	print response
	if response ==gtk.RESPONSE_YES:
		if bookmark in config["bookmarks"]:
			del config["bookmarks"][bookmark]
			config.write()
			print "delete bookmark",bookmark
			load_bookmarks()
	elif response ==gtk.RESPONSE_NO:
		print "no"

def umount_as_root(widget):
	print "success"
	error,output=commands.getstatusoutput("gksu -m \""+_("You have requested to unmount the share with root permissions. Please enter the root password.")+"\" -u root umount "+"\'"+unmnt+"\'")
	if "error" in output:
			print "ERROR"
			ERROR(output)
	lsmounted()
def right_clicked(widget,event):
	global SELECTED_BOOMARK
	print "right clicked"
	print type(widget)
	if type(widget) == gtk.TreeView:
		if  unmnt =="":
			return
		if event.button==3:
			print "button 3"
			menu.popup( None, None, None, event.button, event.time)
	elif type(widget)==gtk.MenuItem:
		for x in widget:
			print x.get_text()
			print "Setting bookmar var"
			SELECTED_BOOMARK=x.get_text()
			print SELECTED_BOOMARK
		if event.button==3:
			del_bookmark_menu.popup( None, None, None, event.button, event.time)


window=gtk.Window(gtk.WINDOW_TOPLEVEL)
window.connect("delete_event", delete_event)
window.set_title("Smb Browser")
del_bookmark_menu=gtk.Menu()
del_bookmark_menuitem=gtk.MenuItem(_("Delete Bookmark"))
del_bookmark_menuitem.connect("activate",del_bookmark)
del_bookmark_menu.append(del_bookmark_menuitem)
del_bookmark_menuitem.show()
menu=gtk.Menu()
umount_root=gtk.MenuItem(("Unmount as root"))
umount_root.connect("activate",umount_as_root)
menu.append(umount_root)
umount_root.show()
#######parser widgets####
wgtreestore = gtk.TreeStore(str)
wgtreeview = gtk.TreeView(wgtreestore)
wgtvcolumn = gtk.TreeViewColumn(_("Network"))
wgtreeview.append_column(wgtvcolumn)
wgtreeview.connect("cursor-changed",st_scanwgornb,"default")
wgcell = gtk.CellRendererText()
wgtvcolumn.pack_start(wgcell, True)
wgtvcolumn.add_attribute(wgcell, 'text', 0)
wgtreeview.set_search_column(0)
wgtvcolumn.set_sort_column_id(0)
wgscrolledwindow = gtk.ScrolledWindow()
wgscrolledwindow.set_policy(True, True)
wgscrolledwindow.add(wgtreeview)
#####end parser widgets######

mntedcelR = gtk.CellRendererText()
mntedlist = gtk.ListStore(int,str)
mntedtreeview = gtk.TreeView(mntedlist)
mntedtreeview.insert_column_with_attributes(0, _("Mounted Shares (To view the files, click 'Browse')"), mntedcelR, text=1)
mntedmodel = mntedtreeview.get_selection()
mntedmodel.set_mode(gtk.SELECTION_SINGLE)
mntedtreeview.set_model(mntedlist)
mntedtreeview.add_events(gtk.gdk.BUTTON_PRESS_MASK)
mntedtreeview.connect("button-press-event", right_clicked)
mntedtreeview.set_search_column(0)
mntedtreeview.set_tooltip_text(_("Right click to unmount as root"))
mntedtreeview.connect("cursor-changed", addprefsel)
mntedtreeview.connect("row_activated", addprefsel2)
mntedscrolledwindow = gtk.ScrolledWindow()
mntedscrolledwindow.set_policy(True, True)
mntedscrolledwindow.add(mntedtreeview)


mnt=gtk.Button(_('Mount'))
add_bookmark_btn=gtk.Button(stock=gtk.STOCK_ADD)
add_bookmark_btn.get_children()[0].get_children()[0].get_children()[1].set_label(_("BookMark"))
add_bookmark_btn.connect("clicked",add_bookmark)
#mnt.connect('clicked', mount,"NONE")
mnt.connect('clicked', mount)
umntbtn=gtk.Button(_('Un-Mount'))
umntbtn.connect('clicked', umount)
quit=gtk.Button(label=None,stock=gtk.STOCK_QUIT)#'Quit')
quit.connect('clicked', delete_event)
about=gtk.Button(stock=gtk.STOCK_ABOUT)
version_lbl=gtk.Label("Smb-Browser "+_("Version:")+" "+VERSION)
def abtfunc(x):
	global VERSION,CHANGELOG
	x=gtk.AboutDialog()
	x.set_version(VERSION)
	x.set_name("Smb Browser")
	y=["David Braker (LinuxNIT)\nContact: linuxnit@elivecd.org\n\n\n\nLayout suggestions by\nElmo40[Leo Fortey] from #elive"]
	x.set_authors(y)
	if os.access("/usr/share/pixmaps/smb-browser.png",0)==True:
		image=gtk.gdk.pixbuf_new_from_file_at_size("/usr/share/pixmaps/smb-browser.png",60,60)
	else:
		image=None
	x.set_logo(image)
	def close(w, res):
		if res == gtk.RESPONSE_CANCEL:
			w.hide()
	x.connect("response", close)
	x.set_wrap_license(True)
	x.set_license(_("This program was designed to assist users in finding and mounting samba shared folders on a network while being easy yet functional Copyright (C) <2007>  <David Braker> This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version. This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with this program; if not, write to the Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA. On a Debian GNU/Linux system you can find a copy of this license in `/usr/share/common-licenses/'."))
	x.set_comments(_("This program was designed to assist users in finding and mounting samba shared folders on a network while being easy yet functional."))
	x.show()
about.connect("clicked",abtfunc)
scanbtn=gtk.Button(_('Search'))
scanbtn.set_tooltip_text(_("To enable this, check the 'Scan for other workgroups' option in the preferences"))
scanbtn.connect('clicked', st_func)
fmbtn=gtk.Button(_("Browse"))
fmbtn.connect('clicked', fm)
srchbtn=gtk.Button(_("Search by Name or IP"))
srchbtn.connect('clicked', search,"default")

bookmark_menu=gtk.MenuItem(_("Bookmarks"))
list_menu=gtk.Menu()
def menuitem_response(widget,buf):
	print buf

bookmark_menu.set_submenu(list_menu)
bookmark_menu.set_tooltip_text(_("Right click on a bookmark to delete it."))

menu_bar = gtk.MenuBar()
menu_bar.append (bookmark_menu)

srch_entry=gtk.Entry()
srch_entry.connect("activate",search,"default")
statuslbl=gtk.Label()
statuslbl.set_justify(gtk.JUSTIFY_LEFT)

##Main widget section##
mntbox=gtk.HBox(False)
mntbox.pack_start(scanbtn, False, False, 0)
mntbox.pack_end(mnt, False, True, 0)
srchbbox=gtk.HBox(False, 5)
srchbbox.pack_start(srch_entry, False, False, 0)
srchbbox.pack_start(srchbtn, False, True, 0)
srchbbox.pack_start(menu_bar, False, True, 0)
progbar = gtk.ProgressBar()
scan_progbar=gtk.ProgressBar()

bbox=gtk.HBox(False,True)#ButtonBox()
bbox.pack_start(about,True,True,0)
bbox.pack_start(version_lbl, True, True, 0)
bbox.pack_end(quit, True, True, 0)

sep=gtk.VSeparator()
#####we have##
## HButtonBoxes#
##scrolledwindows
infobox=gtk.VBox()
#infobox.pack_start(info_lbl,True,False,0)
infobox.pack_start(info_data,True,False,0)
infobox.pack_end(progbar, False, False, 0)

MainHbox1=gtk.HBox(False,2)
MainVbox2=gtk.VBox(False,0)
MainHbox1.pack_start(wgscrolledwindow, True, True, 0)
MainHbox1.pack_start(sep, False, False, 0)
MainVbox2.pack_end(mntedscrolledwindow, True,True, 0)

vpane=gtk.VPaned()
vpane.pack1(infobox,True,True)
vpane.pack2(MainVbox2,True,True)

main_hpaned=gtk.HPaned()
sysbox_top=gtk.VBox(False,3)
sysbox_bottom=gtk.VBox(False,3)
sysbox_top.pack_start(MainHbox1, True, True, 0)
sysbox_top.pack_start(scan_progbar, False, False, 0)
sysbox_top.pack_start(mntbox, False, False, 0)
umbbox=gtk.HBox(False,6)
umbbox.pack_start(fmbtn,False,False,0)
umbbox.pack_start(umntbtn,False,False,0)
umbbox.pack_start(add_bookmark_btn, False, True, 0)
sysbox_bottom.pack_start(info_lbl,False,False,0)
sysbox_bottom.pack_end(umbbox, False,False, 0)
sysbox_bottom.pack_end(vpane, True, True, 0)

#sysbox_bottom.pack_start(progbar, False, False, 0)

main_hpaned.pack1(sysbox_top,True,True)
main_hpaned.pack2(sysbox_bottom,True,True)
main_hpaned.set_position(175)
main_hpaned.set_border_width(5)
main_box=gtk.VBox(False)
main_box.pack_start(srchbbox,False,False,0)
main_box.pack_start(main_hpaned,True,True,0)
####end main widget section###
	####preference widget config section####
		###preferences-tab labels entries etc####
pwlbl=gtk.Label(_("Password"))
pw_entry = gtk.Entry()
pw_entry.set_visibility(False)
pw_entry.set_invisible_char("*") 
unamelbl=gtk.Label(_("User Name"))
uname_entry=gtk.Entry()
wglbl=gtk.Label(_("Prefered Workgroups"))
wg_entry=gtk.Entry()
wg_entry.set_tooltip_text(_("Use a comma to separate workgroups"))
fmlbl=gtk.Label(_("Prefered File Manager"))
fm_entry=gtk.Entry()
mntlocallbl=gtk.Label(_("Mount Location"))
mntlocal_entry=gtk.Entry()
foldbtn=gtk.Button(_("Browse"))
foldbtn.connect('clicked', foldersel)
wgcheckbox=gtk.CheckButton(_("Scan for other workgroups"),False)
savebtn=gtk.Button(stock=gtk.STOCK_SAVE)
savebtn.connect('clicked',save)
checkbox=gtk.CheckButton(_("Guest"),False)
checkbox.connect('clicked', userfunc)
clncheckbox=gtk.CheckButton(_("Clean directories"))
clncheckbox.set_tooltip_text(_("This will remove empty directories when unmounting."))
clncheckbox.connect('clicked', clean)
mnt_cmd_cifs=gtk.RadioButton(None,"mount.cifs")
mnt_cmd_cifs.set_tooltip_text(_("This typically requires you to SUID the mount.cifs command in order to be run as user. To do this, run the following commands as root:")+" chmod u+s "+MOUNT_CIFS_CMD+" & chmod u+s "+UMOUNT_CIFS_CMD)


mnt_cmd_smb=gtk.RadioButton(mnt_cmd_cifs,"smbmount")
mount_cmd_lbl=gtk.Label(_("Mount command"))
		####end pref-tab labels entries etc####
	###preference tab packing####
confvbox=gtk.VBox()
prefbox=gtk.HBox()
usrbox=gtk.HButtonBox()
usrbox.pack_start(unamelbl,False, True, 2)
usrbox.pack_start(checkbox,False, True, 2)
brsbox=gtk.HButtonBox()
brsbox.pack_start(mntlocallbl,False, True, 2)
brsbox.pack_start(foldbtn,False, True, 2)
confvbox.pack_start(fmlbl,False, True, 2)
confvbox.pack_start(fm_entry,False, True, 2)
confvbox.pack_start(wglbl,False, True, 2)
confvbox.pack_start(wg_entry,False, True, 2)
confvbox.pack_start(wgcheckbox,False, True, 2)
confvbox.pack_start(usrbox,False, True, 2)
confvbox.pack_start(uname_entry,False, True, 2)
confvbox.pack_start(pwlbl,False, True, 2)
confvbox.pack_start(pw_entry,False, True, 2)
confvbox2=gtk.VBox()
confvbox2.pack_start(brsbox,False, True, 2)
confvbox2.pack_start(mntlocal_entry,False, True, 2)
confvbox2.pack_start(clncheckbox,False, True, 2)
confvbox2.pack_start(mount_cmd_lbl,False, True, 2)
confvbox2.pack_start(mnt_cmd_smb,False, True, 2)
confvbox2.pack_start(mnt_cmd_cifs,False, True, 2)
#confvbox.pack_start(clncheckbox,False, True, 2)

confhbbox=gtk.HButtonBox()
confhbbox.pack_end(savebtn,False, True, 2)
confvbox2.pack_end(confhbbox,False, True, 2)
prefbox.pack_start(confvbox,False,False,2)
prefbox.pack_end(confvbox2,False,False,2)
#~ prefbox.pack_start(pref_sep,False,False,2)
#~ prefbox.pack_start(bookmark_box,False,True,2)
	### End preference tab packing####
	
####END prefernce widget config section####
####Help Tab#####
helpbox=gtk.VBox()
helpswindow=gtk.ScrolledWindow(None,None)
helpswindow.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_ALWAYS)
helpswindow.add_with_viewport(helpbox)
###Text Views###
maintext=gtk.TextView()
maincontent=gtk.TextView()
maincontent2=gtk.TextView()
preftext=gtk.TextView()
prefcontent=gtk.TextView()
wgcontent=gtk.TextView()
scan2content=gtk.TextView()
scantext=gtk.TextView()
searchtext=gtk.TextView()
wgtext=gtk.TextView()
scantext2=gtk.TextView()
mtlocaltext=gtk.TextView()
cleantext=gtk.TextView()
scan2_content=gtk.TextView()
wg_content=gtk.TextView()
mtlocal_content=gtk.TextView()
clean_content=gtk.TextView()
###Text Buffers
scanbuf=scantext.get_buffer()
wgbuf=wgtext.get_buffer()
scan2buf=scantext2.get_buffer()
mtlocalbuf=mtlocaltext.get_buffer()
cleanbuf=cleantext.get_buffer()
searchbuf=searchtext.get_buffer()

buffer = maintext.get_buffer ()
main_content_buffer=maincontent.get_buffer()
main_content_buffer2=maincontent2.get_buffer()
pref_buffer=preftext.get_buffer()
pref_content_buffer=prefcontent.get_buffer()
scan2_content_buf=scan2_content.get_buffer()
wg_content_buf=wg_content.get_buffer()
clean_content_buf=clean_content.get_buffer()
mtlocal_content_buf=mtlocal_content.get_buffer()

main_content_buffer.set_text("\t"+_("If you enable the scan function in the preferences, then Smb-browser will use nmblookup to find master browsers on the network. It will then search each master browser for a list of Workgroups. On larger networks, especially where computers  come and go a lot, this can take a long time. It is  faster to simply specify your Workgroup name in the preferences."))
main_content_buffer2.set_text("\t"+_("This will contact a computer directly using either its name or ip address if it is on the network."))
wg_content_buf.set_text("\t"+_("Here you should specify the Workgroup or Workgroups you prefer to search. You can specify multiple workgroups separating them with a comma."))
scan2_content_buf.set_text("\t"+_("See above."))
mtlocal_content_buf.set_text("\t"+_("This is the location of where the Samba shares will be mounted on your computer. You must have write permissions for this directory."))
clean_content_buf.set_text("\t"+_("If this is checked, then Smb-browser will remove the directories created when mounting shares. If it finds a file in one of the directories it will not remove it"))

for x in [maincontent,maincontent2,prefcontent,maintext,preftext,scantext,searchtext,wgtext, scantext2, mtlocaltext, cleantext,scan2_content,wg_content,mtlocal_content,clean_content]:
	x.set_wrap_mode(gtk.WRAP_WORD)
	x.set_editable(False)
for x in [maintext,preftext]:
	x.set_justification(gtk.JUSTIFY_CENTER)

def insert_tag(buffer,text,property,value,fontsize):
	iter = buffer.get_iter_at_offset (0)
	tag_table=buffer.get_tag_table()
	tag=gtk.TextTag("name")
	tag.set_property(property,value)
	tag.set_property("size-points",fontsize)
	sob,eob = buffer.get_bounds()
	tag_table.add(tag)
	buffer.insert_with_tags_by_name(eob,text,"name")
insert_tag(buffer,_("Main"),"weight",pango.WEIGHT_BOLD,15)
insert_tag(pref_buffer,_("Preferences"),"weight",pango.WEIGHT_BOLD,15)
insert_tag(scanbuf,_("Scan:"),"foreground","blue",12)
insert_tag(searchbuf,_("Search:"),"foreground","blue",12)
insert_tag(wgbuf,_("Workgroup:"),"foreground","blue",12)
insert_tag(scan2buf,_("Scan:"),"foreground","blue",12)
insert_tag(mtlocalbuf,_("Mount Location:"),"foreground","blue",12)
insert_tag(cleanbuf,_("Clean:"),"foreground","blue",12)
helpbox.pack_start(maintext,False,True,0)
helpbox.pack_start(scantext,False,True,0)
helpbox.pack_start(maincontent,True,True,0)
helpbox.pack_start(searchtext,False,True,0)
helpbox.pack_start(maincontent2,True,True,0)
helpbox.pack_start(preftext,False,True,0)
helpbox.pack_start(wgtext,True,True,0)
helpbox.pack_start(wg_content,True,True,0)
helpbox.pack_start(scantext2,True,True,0)
helpbox.pack_start(scan2_content,True,True,0)
helpbox.pack_start(mtlocaltext,True,True,0)
helpbox.pack_start(mtlocal_content,True,True,0)
helpbox.pack_start(cleantext,True,True,0)
helpbox.pack_start(clean_content,True,True,0)
####End Help Tab#####
####Mount Options Tab#####
mntoptbox=gtk.Fixed()
mntops=gtk.Label(_("Additional mount options")+"\n"+_("see 'man smbmount' for details.")+"\n"+_("(comma separated)"))
mntops_entry=gtk.Entry()
mntoptbox.put(mntops,0,300)#pack_start(mntops,False, False, 2)
mntoptbox.put(mntops_entry,190,300)#pack_start(mntops_entry,False, False, 2)
mnt_rwro= gtk.combo_box_new_text()
mnt_rwro.append_text("rw")
mnt_rwro.append_text("ro")
mnt_rwro.set_active(0)
mntoptbox.put(mnt_rwro,0,0)#pack_start(mnt_rwro,False, False, 2)
####End Mount Options Tab#####

mainlbl=gtk.Label(_("Main"))
conflbl=gtk.Label(_("Preferences"))
mntoptlbl=gtk.Label(_("Mount Options"))
helplbl=gtk.Label(_("Help"))
abtlbl=gtk.Label(_("About"))

notebook = gtk.Notebook()
notebook.set_tab_pos(gtk.POS_TOP)
#notebook.set_tab_pos(gtk.POS_LEFT)
notebook.show()
show_tabs = True
show_border = True
notebook.append_page(main_box, mainlbl)
notebook.append_page(prefbox, conflbl)
notebook.append_page(mntoptbox, mntoptlbl)
notebook.append_page(helpswindow,helplbl)
notebook.set_current_page(2)

VBOX=gtk.VBox(False)
VBOX.pack_start(notebook,True,True,1)
VBOX.pack_start(bbox,False,False,1)
window.add(VBOX)
window.set_size_request(550, 480)

if os.access("/usr/share/pixmaps/smb-browser.png",0)==True:
	window.set_icon_from_file("/usr/share/pixmaps/smb-browser.png")
window.show_all()


def readconf():
	print "read conf "
	print "this is activated at startup"
	global mntlocal
	mntlocal=config[conf]["mntlocal"]
	print config
	check=mntlocal[len(mntlocal)-1:len(mntlocal)]
	if check != "/":
		mntlocal=mntlocal+"/"
	mntlocal_entry.set_text(mntlocal)
	wg_entry.set_text(config[conf]["workgroup"].strip("'"))
	pw_entry.set_text(config[conf] ["password"])
	fm_entry.set_text(config[conf] ["filemanager"])
	uname_entry.set_text(config[conf]["username"])
	if "smbmount" in config[conf]["mount_command"].strip():
		print "Activateing smbmount"
		mnt_cmd_smb.set_active(True)
	elif "mount.cifs" in config[conf]["mount_command"].strip():
		if os.stat(MOUNT_CIFS_CMD).st_mode & stat.S_ISUID ==0:
			if os.getuid()!=0:
				print "not SUID and not root"
				if check_for_mnt_cmd("smbmount")==True:
					mnt_cmd_smb.set_active(True)
					ERROR(_("It appears that you are not 'root' and that your mount.cifs command is not SUID. We found 'smbmount' and have changed your configurations to use that. To use mount.cifs, please run the following as root in a terminal: chmod u+s ")+str(MOUNT_CIFS_CMD))
				else:
					ERROR(_("It appears that you are not 'root' and that your mount.cifs command is not SUID. Until this is fixed, you will not be able to mount shares as user. Please run the following as root in a terminal: chmod u+s ")+str(MOUNT_CIFS_CMD))
		else:
			print "Activateing cifs"
			mnt_cmd_cifs.set_active(True)
	tup= wg_entry.get_text()
	x=wgcheckbox.get_active()
	wgtreestore.clear()
	if x ==True:
		scanbtn.set_sensitive(True)
	else:
		for parent in wg_entry.get_text().split(","):
			wgtreestore.append(None, [parent])
		scanbtn.set_sensitive(False)
	print "end of readconf "
def readconf1():
	global FIRST_RUN
	if config[conf]["first_run"] in ["True",True]:
		FIRST_RUN=True
		print "running first run checks"
		if check_for_mnt_cmd(config[conf]["mount_command"].strip()) ==False:
			print "mount command not found"
			if config[conf]["mount_command"].strip() ==SMBMOUNT_CMD:
				print "try mount.cifs"
				cmdtotry=MOUNT_CIFS_CMD
				if check_for_mnt_cmd(MOUNT_CIFS_CMD) == False:
					ERROR(_("Could not find mount.cifs or smbmount"))
			else:
				print "try smbmount"
				cmdtotry=SMBMOUNT_CMD
				if check_for_mnt_cmd(SMBMOUNT_CMD) == False:
					ERROR(_("Could not find mount.cifs or smbmount"))
			config[conf]["mount_command"]=cmdtotry
		print "first run = ",config[conf]["first_run"]
		notebook.set_current_page(1)
		config[conf]["first_run"]=False
		config.write()
	print "running readconf1"
	x=config[conf]["wgflag"]
	print x
	if x=="True":
		print "true"
		wgcheckbox.set_active(True)
	elif x=="False":
		print "false"
		wgcheckbox.set_active(False)
	y=config[conf]["flag"]
	if y=="True":
		print "True"
		checkbox.set_active(True)
	elif y=="False":
		print "false"
		checkbox.set_active(False)
	z=config[conf]["clean"]
	if z=="True":
		print "True"
		clncheckbox.set_active(True)
	elif z=="False":
		print "false"
		clncheckbox.set_active(False)
	print "end of readconf1"
	return readconf()
mnt.set_sensitive(False)
umntbtn.set_sensitive(False)
add_bookmark_btn.set_sensitive(False)
readconf1()
lsmounted()
load_bookmarks()
if FIRST_RUN==False:
	#~ if mnt_cmd_smb.get_active() == True:
		#~ mnt_cmd="smbmount"
	#~ elif mnt_cmd_cifs.get_active()==True:
		#~ mnt_cmd="mount.cifs"
	if check_for_mnt_cmd(config[conf]["mount_command"].strip()) ==False:
		if config[conf]["mount_command"].strip() =="smbmount":
			cmdtotry="mount.cifs"
		else:
			cmdtotry="smbmount"
		ERROR(_("It appears that the mount command in your config does not exist, please try:")+" "+cmdtotry)
class scan_thread(threading.Thread):#,x,userinfo):
	def run(self):
		global userinfo
		scanwgornb(wgtreestore,userinfo)
class UD_thread(threading.Thread):
	def run(self):
		findwgs()
class MAIN(threading.Thread):
	def __init__(self):
		gtk.main()

main=MAIN()
