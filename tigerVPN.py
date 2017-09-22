#!/usr/bin/env python3

def runningSudo():
    import os
    return not os.getuid()

def getWorkingDirectory():
    import os
    thisFile = os.path.abspath(__file__)
    thisDirectory = os.path.split(thisFile)[0]
    return thisDirectory

def getListOfConfigs(configDirectory):
    import os
    if not os.path.isdir(configDirectory):
        raise FileNotFoundError("Unable to find the configuration folder at %s" %configDirectory)
    rawFileList = os.listdir(configDirectory)
    configFiles = [configDirectory + os.sep + file for file in rawFileList if file.endswith(".ovpn")]
    return configFiles

def checkPing(server, count = 3):
    import subprocess
    import statistics
    command = "ping -c %s %s" %(count, server)
    pingTest = subprocess.Popen([command], stdout = subprocess.PIPE, shell = True)
    result = pingTest.stdout
    timeCollection = []
    for line in result:
        lineFields = line.decode().split()
        for field in lineFields:
            if field.startswith("time="):
                timeCollection.append(float(field.replace("time=","")))
    if timeCollection:
        return round(statistics.mean(timeCollection))
    else:
        return 999

def getLoginFile(workingDirectory):
    import os
    loginFile = workingDirectory + os.sep + "login.txt"
    if os.path.isfile(loginFile):
        return loginFile
    else:
        loginFileRefused = loginFile + ".refused"
        if os.path.isfile(loginFileRefused):
            return None
        if yesanswer("No credential file was found. Do you wish to create one?"):
            createCredFile(loginFile)
            return loginFile
        else:
            if not yesanswer("Do you want to be asked to create a credential file again?"):
                refusal = open(loginFileRefused, 'w')
                refusal.close()
                return None

def createCredFile(credFileName):
    import getpass
    import os
    user = None
    while not user:
        user = input("User: ")
        if not user:
            print("You must enter a user")
    password = None
    while not password:
        password1 = getpass.getpass("Password: ")
        if not password1:
            print("You must enter a password")
            continue
        password2 = getpass.getpass(" Confirm: ")
        if not password2:
            print("You must confirm your password")
        if password1 == password2:
            password = password1
        else:
            print("Passwords do not match")
    credFile = open(credFileName, 'w')
    print(user, file = credFile)
    print(password, file = credFile)
    credFile.close()
    os.chmod(credFileName, 0o400)
    
def createRankedServerList(configFiles):
    import os
    serverList = []
    for file in configFiles:
        config = open(file, 'r')
        line = config.readline()
        while line:
            if line.startswith("remote"):
                lineSplit = line.split()
                server = lineSplit[1]
                break
            line = config.readline()
        config.close()
        if not server:
            continue
        location = file.split(os.sep)[-1].split("@")[0].strip()
        print("Checking ping time for %s" %location)
        pingTime = checkPing(server)
        serverList.append((pingTime, location, file))
    serverList.sort()
    return serverList

def connect(configFile, configDirectory, loginFile):
    import os
    import subprocess
    startingDir = os.getcwd()
    os.chdir(configDirectory)
    if loginFile:
        loginArg = "--auth-user-pass %s" %loginFile
    else:
        loginArg = ""
    command = " ".join(["openvpn", "--config", '"%s"' %configFile, loginArg])
    print(command)
    try:
        vpn = subprocess.Popen([command], shell = True)
        #creds =  "%s\n%s\n" %(user, password)
        #vpn.communicate(input = creds.encode())
    except KeyboardInterrupt:
        print("Disconnecting")
        os.chdir(startingDir)
        
def selectServerConfigFile(rankedServerList):
    print("#\tPing\tLocation")
    for number, server in enumerate(rankedServerList):
        print("%s\t%s\t%s" %(number + 1, server[0], server[1]))
    validSelection = False
    while not validSelection:
        selection = input("Select server number: ")
        if not selection:
            continue
        try:
            selection = int(selection.strip())
        except:
            continue
        selection = selection - 1
        if selection in range(0, len(rankedServerList)):
            validSelection = True
    return rankedServerList[selection][2]
        
def runConnection():
    import os
    if not runningSudo():
        raise PermissionError("Admin is required to start a VPN. Please run this program using sudo.")
    workingDirectory = getWorkingDirectory()
    configDirectory = workingDirectory + os.sep + "config"
    loginFile = getLoginFile(workingDirectory)
    configFiles = getListOfConfigs(configDirectory)
    rankedServers = createRankedServerList(configFiles)
    selectedServerFile = selectServerConfigFile(rankedServers)
    #user, password = getUserNameAndPassword(workingDirectory)
    connect(selectedServerFile, configDirectory, loginFile)
    
def yesanswer(question):  #asks the question passed in and returns True if the answer is yes, False if the answer is no, and keeps the user in a loop until one of those is given.  Also useful for walking students through basic logical python functions
    answer = False  #initializes the answer variable to false.  Not absolutely necessary, since it should be undefined at this point and test to false, but explicit is always better than implicit
    while not answer:  #enters the loop and stays in it until answer is equal to True
        print (question + ' (Y/N)')  #Asks the question contained in the argument passed into this subroutine
        answer = input('>>') #sets answer equal to some value input by the user
        if str(answer) == 'y' or str(answer) == 'Y':  #checks if the answer is a valid yes answer
            return True  #sends back a value of True because of the yes answer
        elif str(answer) == 'n' or str(answer) == 'N': #checks to see if the answer is a valid form of no
            return False  #sends back a value of False because it was not a yes answer
        else: #if the answer is not a value indicating a yes or no
            print ('Invalid response.')
            answer = False #set ansewr to false so the loop will continue until a satisfactory answer is given
    
if __name__ == '__main__':
    runConnection()