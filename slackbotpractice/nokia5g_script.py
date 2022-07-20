#!/usr/bin/python3.6

import sys
import datetime
# import time
import xml.etree.ElementTree as ET
import cx_Oracle
import os
import pyodbc

# up to date with nokiabot 8.5
netact_con='omc/omc@10.4.189.138:1521/OSS'

def alarms(enbid):
    #print('enbid',enbid)
    con = cx_Oracle.connect(netact_con)
    cur = con.cursor()
    # print(cx_Oracle.version)
    almlist = {}
    n = 0
    numalm = 0
    alcount = {}
    while n < len(enbid) and numalm < 10:
        temp = enbid[n].strip().lstrip('0')[-7:]
        if len(temp) == 7:
            cur.execute(
                "SELECT * FROM fx_alarm where DN like 'PLMN-PLMN/MRBTS-" + temp + "%' and alarm_status = 1 FETCH FIRST 20 ROWS ONLY")
            alarmcount = [0, 0, 0, 0]  # [warning,min,major,critical]
            totallist = []
            for alm in cur:
                # print(alm)
                if alm[12] == 3:
                    almtype = 'Minor'
                    alarmcount[1] = alarmcount[1] + 1
                elif alm[12] == 2:
                    almtype = 'Major'
                    alarmcount[2] = alarmcount[2] + 1
                elif alm[12] == 1:
                    almtype = 'Critical'
                    alarmcount[3] = alarmcount[3] + 1
                else:
                    almtype = 'Indeterminate'
                    alarmcount[0] = alarmcount[0] + 1
                totallist.append([temp[-6:], alm[1], alm[5], alm[11], almtype, alm[15],
                                  alm[22]])  # DN, time, number, severity, text, other info
                numalm = numalm + 1
            # print(totallist)
            almlist[temp] = totallist.copy()
            alcount[temp] = alarmcount.copy()
        n = n + 1
    cur.close()
    con.close()
    # print('totallist ',totallist)
    response = ''
    if n < len(enbid):
        response = '10 alarms found in the first ' + str(n) + ' nodes and stopped looking\n'
    else:
        response = str(numalm) + ' alarms found in ' + str(n) + ' nodes\n'
    # print(almlist)
    for endid in almlist:
        response = response + '\ngNodeB ID ' + endid + '\n' + 'Indeterminate= ' + str(
            alcount[endid][0]) + '  Minor= ' + str(alcount[endid][1]) + '  Major= ' + str(
            alcount[endid][2]) + '  Critical= ' + str(alcount[endid][3]) + '\n'
        # print(response)
        # print(almlist[endid])
        for alm in almlist[endid]:
            # print('alm', alm)
            response = response + '\n' + format(str(alm[4]), " <10s") + format("Alarm # " + str(alm[3]),
                                                                               " <15s") + format("Time " + str(alm[2]),
                                                                                                 " <25s")
            response = response + '\n' + str(alm[1])
            response = response + '\n' + str(alm[5])
            response = response + '\n' + str(alm[6])
            response = response + '\n'
    response = response
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
            if len(enbid[n]) >= 9:  # 'enbid' + '-' + 'cellid' >= 8
                cell = []
                dash = enbid[n].split('-')
                if len(dash) > 1:
                    endid = dash[0].strip().lstrip('0')[-7:]
                    # print('endid',endid)
                    cells = dash[1].strip()
                    # print('cells',cells)
                    if 'all' not in cells.lower():
                        cell = cells.split(',')
                    else:
                        cell = ['all']
                    if len(endid) == 7:
                        # print('cell ', cell)
                        enbnumber1 = str(int(endid[-7:]) * 16384)
                        enbnumber2 = str(int(endid[-7:]) * 16384 + 16384)
                        cur.execute(
                            "SELECT CELLNAME_1SNG5M5,LAST_MODIFIED,NRCELLIDENTITY_NIXMNB,LCRID_KSYJJ9,ADMINISTRATIVESTATE_IMH7K7,OPERATIONALSTATE_12S0D4N,PHYSCELLID_KAJ1U2,CONF_ID FROM CMDNR.C_NR_NR_CLL WHERE NRCELLIDENTITY_NIXMNB >'" + enbnumber1 + "' and NRCELLIDENTITY_NIXMNB <'" + enbnumber2 + "' and conf_id =1 and CELLNAME_1SNG5M5 IS NOT NULL and LCRID_KSYJJ9 IS NOT NULL ORDER BY LAST_MODIFIED DESC FETCH FIRST 100 ROWS ONLY")
                        for cname in cur:
                            # print(cname)
                            if (str(cname[2])) not in totallist or cname[7] == 1:
                                if len(cell) > 0 and cell[0] == 'all':
                                    totallist[str(cname[2])] = [cname[4], cname[5], cname[6], cname[1], cname[0], endid,
                                                                cname[3]]
                                else:
                                    if len(cell) > 0 and str(cname[3]) in cell:
                                        totallist[str(cname[2])] = [cname[4], cname[5], cname[6], cname[1], cname[0],
                                                                    endid, cname[3]]
            else:
                break
            n = n + 1

        cur.close()
        con.close()
        # print('totallist',totallist)
        allowed = []
        for cname in totallist:
            if 'LBN' in totallist[cname][4] or 'NBN' in totallist[cname][4] or 'BTS' in totallist[cname][4] or 'WBN' in \
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
                    root2 = ET.SubElement(root1, 'managedObject', attrib={"class": "NRCELL"},
                                          version="NRBTS5G19A_1904_201",
                                          distName="PLMN-PLMN/MRBTS-" + totallist[row][5] + "/NRBTS-" + totallist[row][
                                              5] + "/NRCELL-" + str(totallist[row][6]), operation="update")
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
                response = 'no cells in NEW state'
    else:
        response = 'input type error'
    return response


def planactivate(filename, value, enbid, recursive):
    import paramiko
    t = datetime.datetime.now()
    # user = "FielduSer"
    # password = "nemuMOON13"
    user = "al6106329"
    password = "1*Brampton25"
    # ip="10.4.189.61"
    #ip = "10.4.189.29"
    ip = "10.4.189.151"
    # print("Please wait creating ssh client...")
    ssh_cl = paramiko.SSHClient()
    # ssh_cl.load_system_host_keys()
    ssh_cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # print("Please wait, connecting with remote server")
    ssh_cl.connect(hostname=ip, port=22, username=user, password=password)
    # time.sleep(10)
    # print('connected and doing FTP ', datetime.datetime.now())
    ftp_client = ssh_cl.open_sftp()
    ftp_client.put(filename + ".xml", "/var/opt/nokia/oss/global/racops/import/" + filename + ".xml")
    ftp_client.close()

    # print('time taken sftp', str(datetime.datetime.now()-t))
    stdin, stdout, stderr = ssh_cl.exec_command(
        "/opt/oss/bin/racclimx.sh -v -op Import_Export -fileName  " + filename + ".xml -importExportOperation planImport -planName " + filename)
    # print("Successfully executed command ",datetime.datetime.now())
    stdout = stdout.readlines()
    # print('stdout \n',stdout)
    # print('stderr \n',stderr)
    # print('time taken import', str(datetime.datetime.now()-t))

    stdin, stdout, stderr = ssh_cl.exec_command(
        "/opt/oss/bin/racclimx.sh -op Provision  -planName " + filename + " -bypassUnreachableLteBts true -automatedProvisioningRetryForUnreachableSites false -v")
    # print("Successfully executed command ",datetime.datetime.now())
    stdout = stdout.readlines()
    # print('stdout \n',stdout)

    # print('time taken provision', str(datetime.datetime.now()-t))
    stdin, stdout, stderr = ssh_cl.exec_command("/opt/oss/bin/racclimx.sh  -v -op planDeletion  -planName " + filename)
    # print("Successfully executed command ",datetime.datetime.now())
    # print('time taken delete', str(datetime.datetime.now()-t))
    stdin, stdout, stderr = ssh_cl.exec_command("rm /var/opt/nokia/oss/global/racops/import/" + filename + ".xml")
    ssh_cl.close()

    # time.sleep(5)
    response = cellstate(enbid)
    # print(response)
    return response


def cellstate(enbid):
    con = cx_Oracle.connect(netact_con)
    cur = con.cursor()
    # print('enbid',enbid)
    totallist = {}

    n = 0
    while n < len(enbid):
        if len(enbid[n]) > 6:
            dash = enbid[n].split('-')
            temp = dash[0].strip()

            enbnumber1 = str(int(temp[-7:]) * 16384)
            enbnumber2 = str(int(temp[-7:]) * 16384 + 16384)
            print(enbnumber1)
            cur.execute(
                "SELECT CELLNAME_1SNG5M5,LAST_MODIFIED,NRCELLIDENTITY_NIXMNB,LCRID_KSYJJ9,ADMINISTRATIVESTATE_IMH7K7,OPERATIONALSTATE_12S0D4N,PHYSCELLID_KAJ1U2,CONF_ID FROM CMDNR.C_NR_NR_CLL WHERE NRCELLIDENTITY_NIXMNB >'" + enbnumber1 + "' and NRCELLIDENTITY_NIXMNB <'" + enbnumber2 + "' and conf_id =1 and CELLNAME_1SNG5M5 IS NOT NULL and LCRID_KSYJJ9 IS NOT NULL ORDER BY LCRID_KSYJJ9 FETCH FIRST 100 ROWS ONLY")
            for cname in cur:
                # print(cname)
                if (str(cname[2])) not in totallist or cname[7] == 1:
                    totallist[str(cname[2])] = [cname[4], cname[5], cname[6], cname[1], cname[0], cname[2], cname[3]]
        else:
            break
        n = n + 1

    cur.close()
    con.close()
    # print('totallist',totallist)

    if len(totallist) > 0:
        response = format('CID', " <5s") + format('Cell Name', " <50s") + format('Admin', " <10s") + format(
            'Operational', " <13s") + format('PCI', " <4s")
        for row in totallist:
            # print(format(row," <40s"),format('Locked' if totallist[row][0] == 3 else 'Unlocked'," <13s"),format('Enabled' if totallist[row][1] == 1 else 'Disabled'," <18s"),format(str(totallist[row][2])," <5s"))
            response = response + '\n' + format(str(totallist[row][6]), " <5s") + format(totallist[row][4],
                                                                                         " <50s") + format(
                'Unlocked' if totallist[row][0] == 2 else 'Locked', " <10s") + format(
                'Enabled' if totallist[row][1] == 1 else 'Disabled', " <13s") + format(str(totallist[row][2]), " <4s")
    else:
        response = 'eNodeB not found on Netact'

    return response


def listcell(enbid):
    con = cx_Oracle.connect(netact_con)
    cur = con.cursor()
    totallist = {}
    n = 0
    response = ''
    fdd = True
    eci_obj = {}
    celldata = {}
    while n < len(enbid):
        if len(enbid[n]) > 6:
            cell = []
            temp = enbid[n].strip()
            n = n + 1
            if n < len(enbid):
                ######
                while n < len(enbid) and len(enbid[n]) < 7:
                    cell.append(int(enbid[n].strip()))
                    n = n + 1
            # print('cell ', cell)
            cur.execute("SELECT CO_GID, CO_DN from CMDCTP.ctp_common_objects where CO_DN like 'PLMN-PLMN/MRBTS-" + temp[
                                                                                                                   -7:] + "/NRBTS-" + temp[
                                                                                                                                      -7:] + "/NRCELL-%' and CO_DN like '%/NRCELL__DD-1' FETCH FIRST 100 ROWS ONLY")
            narray = []
            for cname in cur:
                # print(cname)
                if cname[0] not in narray:
                    narray.append(cname[0])
                    tempcell = cname[1].find('/NRCELL-') + 8
                    if 'NRCELL_FDD' in cname[1]:
                        tempcel2 = cname[1].find('/NRCELL_FDD')
                        fdd = True
                    if 'NRCELL_TDD' in cname[1]:
                        tempcel2 = cname[1].find('/NRCELL_TDD')
                        fdd = False
                    # print(cname[1][tempcell+7:tempcel2])
                    if len(cell) > 0:
                        if int(cname[1][tempcell:tempcel2]) in cell:
                            totallist[str(cname[0])] = [temp[-7:], cname[1][tempcell:tempcel2]]
                            if cname[1][tempcell:tempcel2].isdigit():
                                eci = str(int(temp[-7:]) * 16384 + int(cname[1][tempcell:tempcel2]))
                                eci_obj[eci] = str(cname[0])
                    else:
                        totallist[str(cname[0])] = [temp[-7:], cname[1][tempcell:tempcel2]]
                        if cname[1][tempcell:tempcel2].isdigit():
                            eci = str(int(temp[-7:]) * 16384 + int(cname[1][tempcell:tempcel2]))
                            eci_obj[eci] = str(cname[0])
            # print(eci_obj)
            enbnumber1 = str(int(temp[-7:]) * 16384)
            enbnumber2 = str(int(temp[-7:]) * 16384 + 16384)
            cur.execute(
                "SELECT NRCELLIDENTITY_NIXMNB, CELLTECHNOLOGY_A7NS01, FREQBANDINDICATORNR_10GIHKW, NRARFCN_IY0SMZ, CHBW_R7S9GD, PRA_HROOTSEQUENCEINDEX_1OV4JID, CONF_ID  FROM CMDNR.C_NR_NR_CLL WHERE NRCELLIDENTITY_NIXMNB >'" + enbnumber1 + "' and NRCELLIDENTITY_NIXMNB <'" + enbnumber2 + "' and conf_id =1 and CELLNAME_1SNG5M5 IS NOT NULL and LCRID_KSYJJ9 IS NOT NULL ORDER BY LCRID_KSYJJ9 FETCH FIRST 100 ROWS ONLY")
            for cname in cur:
                # print(cname)
                if (str(cname[0])) in eci_obj and cname[6] == 1:
                    totallist[eci_obj[str(cname[0])]] = [str(cname[0]), str(cname[1]), str(cname[2]), str(cname[3]),
                                                         str(cname[4]), str(cname[5])]
                if cname[6] == 1:
                    celldata[str(cname[0])] = [str(cname[0]), str(cname[1]), str(cname[2]), str(cname[3]),
                                               str(cname[4]), str(cname[5])]
        else:
            break
    # print(totallist)
    if len(totallist) > 0:
        if fdd:
            response = response + format('gNB ID', " <9s") + format('Cell ID', " <8s") + format('Tech',
                                                                                                " <5s") + format('Band',
                                                                                                                 " <6s") + format(
                'DL_NRARFCN', " <11s") + format('DL_Bndwth', " <11s") + format('UL_NRARFCN', " <11s") + format(
                'UL_Bndwth', " <11s") + format('RSI', " <7s")
            for gid in totallist:
                cur.execute(
                    "SELECT obj_gid,NRARFCNDL_11XGV1E,CHBWDL_I2J69X,NRARFCNUL_11U6RGU,CHBWUL_IN8YKF FROM CMDNR.C_NR_N_27771 where obj_gid =" + gid + " FETCH FIRST 1 ROWS ONLY")
                for cname in cur:
                    if None not in cname:
                        # print(cname)
                        totallist[str(cname[0])] = totallist[str(cname[0])] + [str(cname[1]), str(cname[2]),
                                                                               str(cname[3]), str(cname[4])]
                        gnb = str(int(int(totallist[str(cname[0])][0]) / 16384))
                        cid = str(int(int(totallist[str(cname[0])][0]) % 16384))
                        # print(totallist)
                        response = response + '\n' + format(gnb, " <9s") + format(cid, " <8s") + format(
                            'FDD' if str(totallist[str(cname[0])][1]).strip() == '0' else '', " <5s") + format(
                            'n' + totallist[str(cname[0])][2], " <6s") + format(totallist[str(cname[0])][6],
                                                                                " <11s") + format(
                            totallist[str(cname[0])][7], " <11s") + format(totallist[str(cname[0])][8],
                                                                           " <11s") + format(
                            totallist[str(cname[0])][9], " <11s") + format(totallist[str(cname[0])][5], " <7s")
                    else:
                        totallist[str(cname[0])] = totallist[str(cname[0])] + [str(cname[1]), str(cname[2]),
                                                                               str(cname[3]), str(cname[4])]
                        response = response + '\n' + format(totallist[str(cname[0])][0], " <9s")

    elif len(celldata) > 0:
        response = response + format('gNB ID', " <9s") + format('Cell ID', " <8s") + format('Tech', " <5s") + format(
            'Band', " <6s") + format('NRARFCN', " <11s") + format('Bndwth', " <11s") + format('RSI', " <7s")
        for cell in celldata:
            gnb = str(int(int(cell) / 16384))
            cid = str(int(int(cell) % 16384))
            response = response + '\n' + format(gnb, " <9s") + format(cid, " <8s") + format(
                'TDD' if celldata[cell][1] == '1' else '', " <5s") + format('n' + celldata[cell][2], " <6s") + format(
                celldata[cell][3], " <11s") + format(celldata[cell][4], " <11s") + format(celldata[cell][5], " <7s")

    else:
        response = 'not found'

    cur.close()
    con.close()
    return response

