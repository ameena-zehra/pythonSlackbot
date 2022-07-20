

import sys
import datetime
#import time
import xml.etree.ElementTree as ET
import cx_Oracle
import os
import pyodbc
#up to date with nokiabot 8.5
netact_con='omc/omc@10.4.189.138:1521/OSS'


def alarms(enbid):
	#print('enbid',enbid)
	con = cx_Oracle.connect(netact_con)
	cur = con.cursor()

	almlist={}
	n=0
	numalm=0
	alcount={}
	while n <len(enbid) and numalm <10:
		temp=enbid[n].strip().lstrip('0')[-6:]
		if len(temp)==6:
			cur.execute("SELECT * FROM fx_alarm where DN like 'PLMN-PLMN/MRBTS-"+temp+"%' and alarm_status = 1 FETCH FIRST 20 ROWS ONLY")
			alarmcount=[0,0,0,0]	#[warning,min,major,critical]
			totallist=[]
			for alm in cur:
				#print(alm)
				if alm[12] == 3:
					almtype='Minor'
					alarmcount[1]=alarmcount[1]+1
				elif alm[12] == 2:
					almtype='Major'
					alarmcount[2]=alarmcount[2]+1
				elif alm[12] == 1:
					almtype='Critical'
					alarmcount[3]=alarmcount[3]+1
				else:
					almtype='Indeterminate'
					alarmcount[0]=alarmcount[0]+1
				totallist.append([temp[-6:],alm[1],alm[5],alm[11],almtype, alm[15],alm[22]]) #DN, time, number, severity, text, other info
				numalm=numalm+1
			#print(totallist)
			almlist[temp]=totallist.copy()
			alcount[temp]=alarmcount.copy()
		n=n+1
	cur.close()
	con.close()
	#print('totallist ',totallist)
	response=''
	if n <len(enbid):
		response='10 alarms found in the first ' +str(n)+' nodes and stopped looking\n'
	else:
		response=str(numalm)+' alarms found in '+str(n)+' nodes\n'
	#print(almlist)
	for endid in almlist:		
		response=response+'\neNodeB ID '+endid+'\n'+'Indeterminate= ' + str(alcount[endid][0])+'  Minor= ' + str(alcount[endid][1])+'  Major= ' + str(alcount[endid][2])+'  Critical= ' + str(alcount[endid][3])+'\n'
		#print(response)
		#print(almlist[endid])
		for alm in almlist[endid]:
			#print('alm', alm)
			response=response+'\n'+format(str(alm[4])," <10s")+format("Alarm # "+str(alm[3])," <15s")+format("Time "+str(alm[2])," <25s")
			response=response+'\n'+str(alm[1])
			response=response+'\n'+str(alm[5])
			response=response+'\n'+str(alm[6])
			response=response+'\n'
	response=response
	return response

def build(value, enbid, recursive):
	con = cx_Oracle.connect(netact_con)
	cur = con.cursor()
	totallist = {}
	# with open("log.txt", "a") as text_file:
	# print(f"build enbid :",str(enbid),"at", datetime.datetime.now(), file=text_file)
	n = 0
	# print(recursive, enbid)
	if isinstance(enbid, list):
		while n < len(enbid):
			if len(enbid[n]) >= 8:  # 'enbid' + '-' + 'cellid' >= 8
				cell = []
				dash = enbid[n].split('-')
				if len(dash) > 1:
					endid = dash[0].strip().lstrip('0')[-6:]
					# print('endid',endid)
					cells = dash[1].strip()
					# print('cells',cells)
					if 'all' not in cells.lower():
						cell = cells.split(',')
					else:
						cell = ['all']
					if len(endid) == 6:
						# print('cell ', cell)
						cur.execute(
							"SELECT LNCEL_CELL_NAME,LAST_MODIFIED,LNCEL_ENB_ID,LNCEL_LCR_ID,LNCEL_AS_26,LNCEL_OS_132,LNCEL_PHY_CELL_ID,CONF_ID FROM cmdlte.c_lte_lncel WHERE LNCEL_ENB_ID='" + endid + "' and conf_id =1 and LNCEL_CELL_NAME IS NOT NULL and LNCEL_LCR_ID IS NOT NULL ORDER BY LAST_MODIFIED DESC FETCH FIRST 100 ROWS ONLY")
						for cname in cur:
							# print(cname)
							if (str(cname[2]) + str(cname[3])) not in totallist or cname[7] == 1:
								if len(cell) > 0 and cell[0] == 'all':
									totallist[str(cname[2]) + str(cname[3])] = [cname[4], cname[5], cname[6], cname[1],
																				cname[0], cname[2], cname[3]]
								else:
									if len(cell) > 0 and str(cname[3]) in cell:
										totallist[str(cname[2]) + str(cname[3])] = [cname[4], cname[5], cname[6],
																					cname[1], cname[0], cname[2],
																					cname[3]]
			else:
				break
			n = n + 1

		cur.close()
		con.close()
		# print('totallist',totallist)
		allowed = []

		for cname in totallist:
#ADD NODE NAMES
			if 'LBN' in totallist[cname][4] or 'NBN' in totallist[cname][4] or 'WBN' in totallist[cname][4] or 'BTS' in \
					totallist[cname][4]:
				allowed.append(cname)

		# print('allowed',allowed)
		if len(allowed) > 0:
			totalnodes = 0
			# print('\nFollowing cell were found with NEW and working on Unlocking them')
			root = ET.Element('raml', version="2.0", xmlns="raml20.xsd")
			root1 = ET.SubElement(root, 'cmData', type="plan")
			root2 = ET.SubElement(root1, 'header')
			ET.SubElement(root2, 'log', dateTime=str(datetime.datetime.now()), action="created", appInfo="Script")
			filename = 'Nokiabot_' + value
			# print(format('Cell Name'," <40s"),format('Admin State'," <13s"),format('Oprational State'," <18s"),format('PCI'," <5s"),format('Last Modiefied'," <20s"))
			for row in allowed:
				# print(format(row," <40s"),format('Locked' if totallist[row][0] == 3 else 'Unlocked'," <13s"),format('Enabled' if totallist[row][1] == 1 else 'Disabled'," <18s"),format(str(totallist[row][2])," <5s"),format(str(totallist[row][3])," <20s"))
				if totallist[row][5].isdigit() and totallist[row][0] != int(value):
					root2 = ET.SubElement(root1, 'managedObject', attrib={"class": "LNCEL"},
										  version="FLF18_1711_06_1711_05",
										  distName="PLMN-PLMN/MRBTS-" + totallist[row][5] + "/LNBTS-" + totallist[row][
											  5] + "/LNCEL-" + str(totallist[row][6]), operation="update")
					root3 = ET.SubElement(root2, 'p', name="administrativeState")
					root3.text = value
					if len(filename) < 35 and totallist[row][5] not in filename:
						filename = filename + '_' + totallist[row][5]
					totalnodes = totalnodes + 1

			# print(ET.tostring(root, encoding='utf8').decode('utf8'))
			# print('totalnodes ', totalnodes)
			if totalnodes > 0:
				tree = ET.ElementTree(root)
				filename = filename + '_' + datetime.datetime.now().strftime("%Y%m%d_%H%M%S%f") + '_output_' + str(
					recursive)
				# print('\n',filename)
				tree.write(filename + '.xml')

				# dom = xml.dom.minidom.parse(filename+'.xml')
				# pretty_xml_as_string = dom.toprettyxml()
				# print(pretty_xml_as_string)

				# print(datetime.datetime.now())
				recursive = recursive + 1
				if recursive < 3:
					response = planactivate(filename, value, enbid, recursive)
					pass

				os.remove(filename + ".xml")
			else:
				# print('None of the found nodes required Administrative state changes')
				response = cellstate(enbid)

		else:
			if len(totallist) == 0:
				response = 'not found'
			else:
				response = 'no cells in proper state'
	else:
		response = 'input type error'
	return response

def planactivate(filename,value,enbid,recursive):
	
	import paramiko
	t=datetime.datetime.now()
	# user="FielduSer"
	# password="nemuMOON13"
	user="al6106329"
	password="1*Brampton25"
	#ip="10.4.189.61"
	#ip = "10.4.189.29"
	ip="10.4.189.151"
	#print("Please wait creating ssh client...")
	ssh_cl = paramiko.SSHClient()
	#ssh_cl.load_system_host_keys()
	ssh_cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	#print("Please wait, connecting with remote server")
	ssh_cl.connect(hostname=ip, port=22, username=user, password=password)

	#time.sleep(10)
	#print('connected and doing FTP ', datetime.datetime.now())	
	ftp_client= ssh_cl.open_sftp()
	ftp_client.put(filename+".xml","/var/opt/nokia/oss/global/racops/import/"+filename+".xml")
	ftp_client.close()
	
	#print('time taken sftp', str(datetime.datetime.now()-t))
	stdin, stdout, stderr = ssh_cl.exec_command("/opt/oss/bin/racclimx.sh -v -op Import_Export -fileName  "+filename+".xml -importExportOperation planImport -planName "+filename)
	#print("Successfully executed command ",datetime.datetime.now())
	stdout = stdout.readlines()
	#print('stdout \n',stdout)
	#print('stderr \n',stderr)
	#print('time taken import', str(datetime.datetime.now()-t))
	
	stdin, stdout, stderr = ssh_cl.exec_command("/opt/oss/bin/racclimx.sh -op Provision  -planName "+filename+" -bypassUnreachableLteBts true -automatedProvisioningRetryForUnreachableSites false -v" )
	#print("Successfully executed command ",datetime.datetime.now())
	stdout = stdout.readlines()
	#print('stdout \n',stdout)

	#print('time taken provision', str(datetime.datetime.now()-t))	
	stdin, stdout, stderr = ssh_cl.exec_command("/opt/oss/bin/racclimx.sh  -v -op planDeletion  -planName "+filename)
	#print("Successfully executed command ",datetime.datetime.now())
	#print('time taken delete', str(datetime.datetime.now()-t))
	stdin, stdout, stderr = ssh_cl.exec_command("rm /var/opt/nokia/oss/global/racops/import/"+filename+".xml")	
	ssh_cl.close()
	
	#time.sleep(5)
	response=cellstate(enbid)
	#print(response)
	return response
			
def cellstate(enbid):

	con = cx_Oracle.connect(netact_con)
	cur = con.cursor()
	#print('enbid',enbid)
	totallist={}
	
	n=0
	while n <len(enbid):
		if len(enbid[n])>5:
			dash=enbid[n].split('-')
			temp=dash[0].strip()
			cur.execute("SELECT LNCEL_CELL_NAME,LAST_MODIFIED,LNCEL_ENB_ID,LNCEL_LCR_ID,LNCEL_AS_26,LNCEL_OS_132,LNCEL_PHY_CELL_ID,CONF_ID FROM cmdlte.c_lte_lncel WHERE LNCEL_ENB_ID='"+temp[-6:]+"' and conf_id =1 and LNCEL_CELL_NAME IS NOT NULL and LNCEL_LCR_ID IS NOT NULL ORDER BY LNCEL_LCR_ID, LAST_MODIFIED DESC FETCH FIRST 100 ROWS ONLY")

			for cname in cur:
				if (str(cname[2])+str(cname[3])) not in totallist or cname[7]==1:
					totallist[str(cname[2])+str(cname[3])]=[cname[4],cname[5],cname[6],cname[1],cname[0],cname[2],cname[3]]	
		else:
			break
		n=n+1	
	
	cur.close()
	con.close()
	#print('totallist',totallist)
	
	if len(totallist)>0:
		response=format('CID'," <5s")+format('Cell Name'," <41s")+format('Admin'," <10s")+format('Operational'," <13s")+format('PCI'," <4s")
		for row in totallist:
			#print(format(row," <40s"),format('Locked' if totallist[row][0] == 3 else 'Unlocked'," <13s"),format('Enabled' if totallist[row][1] == 1 else 'Disabled'," <18s"),format(str(totallist[row][2])," <5s"))
			response=response+'\n'+format(str(totallist[row][6])," <5s")+format(totallist[row][4]," <41s")+format('Unlocked' if totallist[row][0] == 1 else 'Locked'," <10s")+format('Enabled' if totallist[row][1] == 1 else 'Disabled'," <13s")+format(str(totallist[row][2])," <4s")
	else:
		response='eNodeB not found on Netact'
		
	return response
	
def listcell(enbid):
	con = cx_Oracle.connect(netact_con)
	cur = con.cursor()
	totallist={}
	n=0
	response=''
	fdd=True
	while n <len(enbid):
		if len(enbid[n])>5:
			cell=[]
			temp=enbid[n].strip()
			n=n+1
			if n < len(enbid):
			######
				while n < len(enbid) and len(enbid[n]) <5:
					cell.append(int(enbid[n].strip()))
					n=n+1
			#print('cell ', cell)
			cur.execute("SELECT CO_GID, CO_DN from CMDCTP.ctp_common_objects where CO_DN like 'PLMN-PLMN/MRBTS-"+temp[-6:]+"/LNBTS-"+temp[-6:]+"/LNCEL-_/LNCEL__DD-0' or CO_DN like 'PLMN-PLMN/MRBTS-"+temp[-6:]+"/LNBTS-"+temp[-6:]+"/LNCEL-__/LNCEL__DD-0' or CO_DN like 'PLMN-PLMN/MRBTS-"+temp[-6:]+"/LNBTS-"+temp[-6:]+"/LNCEL-___/LNCEL__DD-0' FETCH FIRST 100 ROWS ONLY")
			narray = []
			for cname in cur:
				#print(cname)
				if cname[0]not in narray:
					narray.append(cname[0])
					tempcell=cname[1].find('/LNCEL-')+7
					if 'LNCEL_FDD' in cname[1]:
						tempcel2=cname[1].find('/LNCEL_FDD')
						fdd=True
					if 'LNCEL_TDD' in cname[1]:
						tempcel2=cname[1].find('/LNCEL_TDD')
						fdd=False
					#print(cname[1][tempcell+7:tempcel2])
					if len(cell)>0:
						if int(cname[1][tempcell:tempcel2]) in cell:
							totallist[str(cname[0])]=[temp[-6:],cname[1][tempcell:tempcel2]]
					else:
						totallist[str(cname[0])]=[temp[-6:],cname[1][tempcell:tempcel2]]
		else:
			break
	#print(totallist)
	if len(totallist)>0:
		if fdd:
			response=response+format('eNB ID'," <8s")+ format('Cell ID'," <8s")+format('DLEARFCN'," <9s")+format('DL Bndwth'," <10s")+format('ULEARFCN'," <9s")+format('UL Bndwth'," <10s")+format('RSI'," <7s")
			for gid in totallist:
				cur.execute("SELECT obj_gid,LNCEL_FDD_EARFCN_DL,LNCEL_FDD_DL_CH_BW,LNCEL_FDD_EARFCN_UL,LNCEL_FDD_UL_CH_BW,LNCEL_FDD_ROOT_SEQ_INDEX,LNCEL_FDD_DL_MIMO_MODE FROM cmdlte.c_lte_lncel_fdd where obj_gid ="+gid+" FETCH FIRST 1 ROWS ONLY")
				for cname in cur:
					if None not in cname:
						#print(cname)
						totallist[str(cname[0])]=totallist[str(cname[0])]+[cname[1],int(cname[2]/10),cname[3],int(cname[4]/10),cname[5],cname[6]]
						#print(totallist)
						response=response+'\n'+format(str(totallist[str(cname[0])][0]).strip()," <8s")+ format(str(totallist[str(cname[0])][1]).strip()," <8s")+format(str(totallist[str(cname[0])][2]).strip()," <9s")+format(str(totallist[str(cname[0])][3]).strip()," <10s")+format(str(totallist[str(cname[0])][4]).strip()," <9s")+format(str(totallist[str(cname[0])][5]).strip()," <10s")+format(str(totallist[str(cname[0])][6]).strip()," <7s")
					else:
						totallist[str(cname[0])]=totallist[str(cname[0])]+[cname[1],cname[2],cname[3],cname[4],cname[5],cname[6]]
						response=response+'\n'+format(str(totallist[str(cname[0])][0]).strip()," <8s")
		else:
			response=response+format('eNB ID'," <8s")+ format('Cell ID'," <8s")+format('EARFCN'," <9s")+format('Bndwth'," <10s")+format('RSI'," <7s")
			for gid in totallist:
				cur.execute("SELECT obj_gid,LNCEL_TDD_EARFCN,LNCEL_TDD_CH_BW,LNCEL_TDD_ROOT_SEQ_INDEX,LNCEL_TDD_DL_MIMO_MODE FROM CMDLTE.c_lte_lncel_tdd where obj_gid ="+gid+" FETCH FIRST 1 ROWS ONLY")
				for cname in cur:
					if None not in cname:
						#print(cname)
						totallist[str(cname[0])]=totallist[str(cname[0])]+[cname[1],int(cname[2]/10),cname[3],cname[4]]
						#print(totallist)
						response=response+'\n'+format(str(totallist[str(cname[0])][0]).strip()," <8s")+ format(str(totallist[str(cname[0])][1]).strip()," <8s")+format(str(totallist[str(cname[0])][2]).strip()," <9s")+format(str(totallist[str(cname[0])][3]).strip()," <10s")+format(str(totallist[str(cname[0])][4]).strip()," <7s")
					else:
						totallist[str(cname[0])]=totallist[str(cname[0])]+[cname[1],cname[2],cname[3],cname[4]]
						response=response+'\n'+format(str(totallist[str(cname[0])][0]).strip()," <8s")
		
		
		response=response
	else:
		response='not found'
		
	cur.close()
	con.close()
	return response

