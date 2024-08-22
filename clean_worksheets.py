# take in a file and remove all the donors we will not be making videos for
# remove:
#	businesses (do not have a first name)
# 	persons without emails (how do we get it there otherwise?)
#	Doesnt have first name OR doesn't have email
#
# Have it work with csv and xlsx files, return a file that either replaces _dirty with _clean or # # just appends clean on the end.
# if csv, call parse CSV
# if xlsx, call parse xlsx
# check if file already exists and ask for permission to overwrite it
# (delete it and just make a new one)
import csv
import sys
import time
import os
import random
import string
import textwrap
import pandas as pd
import concurrent.futures as cf
from moviepy.editor import *
from moviepy.video import *
from datetime import datetime
from pathlib import Path

csvFile = ".csv"
xlsxFile = ".xlsx"
outputExtension = "_CLEAN"

def parseFile():
    ### Find the donors file ###
    if (len(sys.argv) != 2):
        print("ERROR: incorrect number of perameters")
        print("Usage: python3 clean_worksheets.py <pathTo/donorFile OR donorFile> <pathTo/indexes.txt OR indexes.txt>\n If file contains spaces, use single quotes e.g. path/'file name has spaces.xlsx'")
        return

    path = Path(sys.argv[1])

    if (path.is_file() == False):
        print("ERROR: The donor file provided in the first argument cannot be found")
        print(path)
        return

    if (str(path)[-4:] == csvFile):
        parseCSV(path)
    elif (str(path)[-5:] == xlsxFile):
        parseXLSX(path)
    else:
        print("ERROR: The file type passed in is not supported by this program")
        print("Tip: Enter a .csv or .xlsx file")

def outputDNE(inputPath, fileType):
    outputPath = Path(str(inputPath)[:-len(fileType)] + outputExtension + fileType)
    if (outputPath.is_file() == False):
        return True
    else:
        print("The file: " + str(outputPath) + "\nalready exists.\nIs it okay to overwrite this file? (y/n): ",end="")
        answer = input().lower()
        if (answer == "y"):
            try:
                os.remove(outputPath)
                return True
            except:
                print("ERROR: program was unable to delete the existing file.")
                print("Tip: Delete or rename the file then try running again.")
        else:
            print("...Terminating the program...")
            print("Tip: Delete or rename the file then try running again.")
    return False

def parseXLSX(inputPath):
    start = datetime.now()
    outputPath = Path(str(inputPath)[:-5] + outputExtension + xlsxFile)

    newRows = []
    donorsFile = pd.read_excel(inputPath, engine='openpyxl')
    donorsFile = donorsFile.fillna('')
    dfRows = donorsFile.values.tolist()

    for row in dfRows:
        if (row[6] != '' and row[16] != ''):
            newRows.append(row)
    pd.DataFrame(newRows).to_excel(outputPath,index=False)

    finish = datetime.now()
    print("Finished in (hh:mm:ss.ms): " + str(finish - start))

def parseCSV(inputPath):
    start = datetime.now()
    outputPath = Path(str(inputPath)[:-4] + outputExtension + csvFile)
    with open(inputPath, 'r', encoding="utf8") as inputCSV:
        donors = csv.reader(inputCSV, delimiter=",")
        with open(outputPath, 'w', newline='', encoding="utf8") as outputCSV:
            output = csv.writer(outputCSV, delimiter=",")
            row = next(donors)
            row.append("Video Link")
            output.writerow(row)

            for row in donors:
                firstName = row[6]
                email = row[16]
                if firstName.strip() == '' and email.strip() == '':
                    continue
                output.writerow(row)

    finish = datetime.now()
    print("Finished in (hh:mm:ss.ms): " + str(finish - start))

parseFile()
