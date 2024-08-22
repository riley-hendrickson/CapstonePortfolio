import firebase_admin
import os
import uuid
from pathlib import Path # to build paths that work on all operating systems.
import random # used for downloadContentFromStore
import datetime
import pyrebase #to run this 'pip3 install pycryptodome' and 'pip3 install pyrebase4'
from firebase_admin import auth, credentials, initialize_app, storage

### Local paths NOTE: made universal accross different OS with Path module
cwd = Path.cwd()
weaveTEMP = r'weaveTEMP'
### storage paths  NOTE: doesn't have to be universal as it is just for firebase
finishedVideos = r'finished_videos/'
videos = r"/clips/"
photos = r"/photos/"
thanks = r"/thankYouClips/"
serviceAccount = "storage/wwucsgiving-firebase-service-key.json"

config = {
    "apiKey": "AIzaSyA7PgJQXuK0ed0O4lzs50BqOOhEDPt_HIQ",
    "authDomain": "wwucsgiving.firebaseapp.com",
    "databaseURL": "https://wwycsgiving.firebaseio.com",
    "projectId": "wwucsgiving",
    "storageBucket": "wwucsgiving.appspot.com",
    "messagingSenderId": "479821375690",
    "appId": "1:479821375690:web:ed5c4302a8f85a83126c33",
    "measurementId": "G-97T86J4WKB",
    "serviceAccount": serviceAccount
}
### firebase_admin ###
cred = credentials.Certificate(serviceAccount)
fbA = firebase_admin.initialize_app(cred, {'storageBucket': 'wwucsgiving.appspot.com'})
bucket = storage.bucket()

### pyrebase ###
fbP = pyrebase.initialize_app(config)
auth = fbP.auth() # used exclusivly in retrieveURL
#token = auth.create_custom_token("test") # used exclusivly in retrieveURL #CURRENTLY NOT WORKING
storP = fbP.storage()

### Macros ###
firstYear = 2022 # the year we began collecting content
curYear = datetime.datetime.now().year
allFiles = list(storP.child().list_files())

# firebase_admin function
# maybe change names of this and uploadVideosToStor and download
def uploadToStor(localPath, fileName):
    lf = localPath / fileName
    print(lf)
    print(type(lf))
    ff = finishedVideos + fileName
    blob = bucket.blob(ff)
    blob.upload_from_filename(str(lf))

# firebase_admin function
def downloadFromStor(localPath, filePathName, rename):
    blob = bucket.blob(filePathName)
    blob.download_to_filename(localPath / rename)

# pyrebase function
# TESTING FUNCTION
#def retrieveURL(firebasePath, fileName):
   #return storP.child(firebasePath + fileName).get_url(token)

# pyrebase function
# 3/1/2022 currently being worked on by pyrebase people.
# Is only able to list ALL files and not only a specified dir.
# TESTING FUNCTON
def listFiles(firebasePath):
    #print(files)
    # allFiles = storP.child(storagePath).list_files() # If it worked properly, it would only list the files in the storagePath. Instead lists them all
    curatedFiles = []
    # for i in range(len(allFiles)):
    #     file = allFiles[i]
    for file in allFiles:
        #print(file)
        if (firebasePath in file.name and file.name[-1] != r"/"): # remove if when bug is patched
            curatedFiles.append(file)
            #print("ADDING:")
            #print(file)
    return curatedFiles
    # Should only be the following line when bug is patched
    # return storP.child(firebasePath).list_files()

# pyrebase function
# 3/1/2022 currently being worked on by pyrebase people.
# Is only able to list ALL files and not only a specified dir.
def printListFiles(firebasePath):
    for file in allFiles:
        if (firebasePath in file.name and file.name[-1] != r"/"): # remove if when bug is patched
            print(f.name)

# Import random
# decide the content needed, then store it in a "to be weaved folder".
# Used listFiles, downloadFromStor
# Randomly selects "amount" distcint videos/images from the specified "path"
# and appends it to the contentList.
# Returns -1 upon failing where that could be it could not find that amount of content,
# but still returns as much as it can.
def downloadContentFromStor(weaveDir, photo_video, contentRandom, year, amount):
    # If we don't have a given year, choose a random year
    try:
        year = int(float(year))
    except:
        year = -1
    print(year)
    if (year < firstYear):
        year = random.randrange(firstYear, curYear + 1)

    if (photo_video == "p"):
        photo_video = photos
    elif (photo_video == "v"):
        photo_video = videos
    elif (photo_video == "t"):
        photo_video = thanks

    storagePath = str(year) + photo_video
    #print(storagePath)
    content = listFiles(storagePath)
    counter = 0
    #print(len(content))
    if len(content) <= amount:
        contentRandom = contentRandom + random.shuffle(content)
        for c in content: # as c.name is the entire path, extract the filetype and rename it
            fileType = "." + c.name.split(".")[-1]
            name = str(len(contentRandom)) + fileType
            downloadFromStor(weaveDir, c.name, name)
            contentRandom.append(weaveDir / name)
        return -1
    else:
        while counter < amount:
            num = random.randrange(len(content))
            fileType = "." + content[num].name.split(".")[-1]
            name = str(len(contentRandom)) + fileType
            downloadFromStor(weaveDir, content[num].name, name)
            contentRandom.append(weaveDir / name)
            content.remove(content[num])
            counter = counter + 1
    return 1
#################################### End of Function ####################################

def removeTempDir():
    if os.path.exists(cwd / weaveTEMP):
        while True:
            for dir in os.listdir(cwd / weaveTEMP):
                deleteDir(cwd / weaveTEMP / dir)
            try:
                os.rmdir(cwd / weaveTEMP)
                break
            except Exception as e:
                print(e)

# can remove makeUploaddir and makeWeavedir
def makeDir():
    newpath = cwd / weaveTEMP / str(uuid.uuid4())
    if not os.path.exists(newpath):
        os.makedirs(newpath)
    return newpath
#################################### End of Function ####################################
# Tested and works
# empties and deletes the given directory
def deleteDir(path):
    clearDir(path)
    try:
        os.rmdir(path)
    except Exception as e:
        print(e)
#################################### End of Function ####################################

# 3/9/2022
# ALL BELOW ARE TO BE TESTED

def deleteFile(pathToFile):
    try:
        os.remove(pathToFile)
    except Exception as e:
        print(e)

# emtpies the given direct
def clearDir(path):
    for file in os.listdir(path):
        deleteFile(path / file)
#################################### End of Function ####################################
# BEGON BYGON
# takes the directory and uploads all the videos to firebase
# def uploadVideos(path):
#     for f in os.listdir(path):
#         uploadToStor(path, f, finishedVideos)
#################################### End of Function #####################################
# pass in the firebase path to the dir full of finished videos
def clearFinishedVideosInStor():
    scan = input("Are you sure you want to delete all the videos in the online storage path\n" + finishedVideos + "?\ny/n: ")
    if scan == "n":
        print("The videos were not deleted.")
        return -1
    else:
        print("Deleting videos...")
        files = listFiles(finishedVideos)
        for f in files:
            blob = bucket.blob(finishedVideos + r'/' + f.name)
            blob.delete()
        print("Videos have been deleted")
        return 1
#################################### End of Function #####################################

# getters
def getPhotoPath():
    return photos
def getVideoPath():
    return videos
def getWeaveTEMP():
    return weaveTEMP

######################################## TESTING #########################################

#weaveDir = makeWeaveDir()
#print(weaveDir)
#deleteDir(weaveDir)
#uploadDir = makeUploadDir()
#print(uploadDir)
#deleteDir(uploadDir)


#downloadFromStor(localPath, fileName, firebasePath)
#uploadToStor(localPath, fileName, firebasePath)
#print(retrieveURL("2022/photos/class/", "2022-csci-1.JPG"))
#printListFiles(firebasePath)
#printListFiles("2022/clips/")
# files = listFiles("finished_videos/")
# for f in files:
#     print(f.name)
# print(files[1])
# files[1].delete()
# for f in files:
#     print(f.name)
#print(cwd)
#blob = bucket.blob(finishedVideos + "Filip_Davison_45739.mp4")
#print(blob)
#print(blob.name)
