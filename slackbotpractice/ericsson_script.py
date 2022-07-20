import paramiko
import sys
import time

#function that creates an SSH connection with amos (shell in ENM)  with the given node name and command function
#invoked by the functions below that DO NOT USE SPECIFIC CELL NAMES
def amosnodecmds(enbname,function,lines):
    # user = "crouser"
    user = "al6106329"
    #password = "Bell@123"
    password = "Temp@1234"
    # password = "Cro2021$"
    ip = "10.240.74.29"
    # ip = "10.7.158.43"
    print(enbname)
    cmd = "amos " + enbname
    ssh_cl = paramiko.SSHClient()
    ssh_cl.load_system_host_keys()
    ssh_cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_cl.connect(hostname=ip, port=22, username=user, password=password)
    ch = ssh_cl.invoke_shell()

    while not ch.send_ready():
        print("NOT READY \n")
        time.sleep(1)

    ch.send(cmd)
    ch.send("\n")

    while not ch.recv_ready():
        time.sleep(1)

    while not ch.send_ready():
        print("NOT READY \n")
        time.sleep(1)

    ch.send("lt all \n")

    while not ch.recv_ready():
        time.sleep(1)


    while not ch.send_ready():
        print("NOT READY \n")
        time.sleep(1)

    ch.send(function+" \n")

    while not ch.recv_ready():
        time.sleep(1)

    time.sleep(30)

    receive = ch.recv(9216)
    receive=receive.decode('UTF-8')

    if "Checking ip contact...Not OK" in receive:
        print(receive)
        response="Node not found"

    elif "Wrong Username" in receive:
        response="ENM Login error"
    else:

        receivetemp=receive.split('\n')

        n=len(receivetemp)-1
        m=lines
        k=0
        size=n-m
        temp=[''] *size

        while m<n:
            temp[k]=receivetemp[m]
            m=m+1
            k=k+1

        rcv=" "
        for line in temp:
            rcv=rcv+line+"\n"

        response=rcv

    return response

    ch.close()

#similar function to the one above that creates an SSH connection with amos (shell in ENM)  with the given node name and command function
#invoked by the functions below that USE SPECIFIC CELL NAMES
def amoscellcmds(enbname,cellsarr,function,action):
    # user = "crouser"
    user = "al6106329"
    #password = "Bell@123"
    password = "Temp@1234"
    # password = "Cro2021$"
    ip = "10.240.74.29"
    # ip = "10.7.158.43"
    print(enbname)
    cmd = "amos " + enbname
    ssh_cl = paramiko.SSHClient()
    ssh_cl.load_system_host_keys()
    ssh_cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_cl.connect(hostname=ip, port=22, username=user, password=password)
    # user = "al6106329"
    # password = "0o9i8u7Y"
    # # password = "Cro2021$"
    # ip = "10.240.74.29"
    # # ip = "10.7.158.43"
    # 
    # cmd = "amos " + enbname
    # ssh_cl = paramiko.SSHClient()
    # ssh_cl.load_system_host_keys()
    # ssh_cl.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # ssh_cl.connect(hostname=ip, port=22, username=user, password=password)    
    ch = ssh_cl.invoke_shell()

    while not ch.send_ready():
        print("NOT READY \n")
        time.sleep(1)

    ch.send(cmd)
    ch.send("\n")

    while not ch.recv_ready():
        time.sleep(1)

    while not ch.send_ready():
        print("NOT READY \n")
        time.sleep(1)

    ch.send("lt all \n")

    while not ch.recv_ready():
        time.sleep(1)

    while not ch.send_ready():
        print("NOT READY \n")
        time.sleep(1)

    ch.send("rbs \n")

    while not ch.recv_ready():
        time.sleep(1)

    while not ch.send_ready():
        print("NOT READY \n")
        time.sleep(1)
    ch.send("rbs \n")

    while not ch.recv_ready():
        time.sleep(1)

    if len(cellsarr) >= 1 and cellsarr[0] != "all":
        for cellid in cellsarr:

            while not ch.send_ready():
                print("NOT READY \n")
                time.sleep(1)

            cellcmd=function+ cellid
            ch.send(cellcmd)
            ch.send("\n")

            while not ch.recv_ready():
                time.sleep(1)

            while not ch.send_ready():
                print("NOT READY \n")
                time.sleep(1)

            ch.send("y \n")

            while not ch.recv_ready():
                time.sleep(1)

            time.sleep(40)

            receive = ch.recv(10240)
            receive = receive.decode('UTF-8')

            if ">> Set." not in receive:
                response = "Error: couldn't perform function. Try again."

            else:
                response="Successfully "+action+" cell(s)"


    if len(cellsarr)==1 and cellsarr[0]=='all':
        while not ch.send_ready():
            print("NOT READY \n")
            time.sleep(1)

        ch.send(function+" all \n")

        while not ch.recv_ready():
            time.sleep(1)

        while not ch.send_ready():
            print("NOT READY \n")
            time.sleep(1)

        ch.send("y \n")

        while not ch.recv_ready():
            time.sleep(1)

        time.sleep(30)

        receive = ch.recv(4096)
        receive = receive.decode('UTF-8')

        if ">> Set." not in receive:
            response = "Error: couldn't perform function. Try again."

        else:
            response="Successfully "+action+" all cells"


    return response
    ch.close()


#function invoked for the status function (calls function THAT DOES NOT USE CELL NAMES above to create ENM ssh connection with parameters specific to this function)
def cellstate(enbname):

    function="st cell"
    lines=60
    response=amosnodecmds(enbname,function,lines)
    return response

#function invoked for the alarms function (calls function above that DOES NOT USE CELL NAMES to create ENM ssh connection with parameters specific to this function)
def alarms(enbname):
     function="ala"
     lines=63
     response=amosnodecmds(enbname,function,lines)
     return response

#function invoked for the cellId function (calls function above that DOES NOT USE CELL NAMES to create ENM ssh connection with parameters specific to this function)
def getcellid(enbproxy):
    enbarr=enbproxy.split('/')
    enbname=enbarr[0]
    proxy=enbarr[1]
    if len(enbarr)==2:
        function="get "+proxy
        lines=60
        cellinfo=amosnodecmds(enbname,function,lines)
        temp=cellinfo.split("\n")
        for row in temp:
            if "cellId" in row:
                cellidrow=row
        response=cellidrow
    else:
        response="Invalid input"
    return response

#function invoked for the lock cells function (calls function above that USES CELL NAMES to create ENM ssh connection with parameters specific to this function)
def lock(enbcells):
    enbcellsarr=enbcells.split('/')
    enbname=enbcellsarr[0]


    if len(enbcellsarr)<=1:
        response="Please enter cell names"
    if len(enbcellsarr)>1:

        cells = enbcellsarr[1]
        cellsarr = cells.split(',')

        function="bl "
        action="locked"
        response=amoscellcmds(enbname,cellsarr,function,action)
        
    return response

#function invoked for the unlock cells function (calls function above that USES CELL NAMES to create ENM ssh connection with parameters specific to this function)
def unlock(enbcells):
    enbcellsarr=enbcells.split('/')
    enbname=enbcellsarr[0]


    if len(enbcellsarr)<=1:
        response="Please enter cell names"
    if len(enbcellsarr)>1:

        cells = enbcellsarr[1]
        cellsarr = cells.split(',')

        function="deb "
        action="unlocked"
        response=amoscellcmds(enbname,cellsarr,function,action)

    return response