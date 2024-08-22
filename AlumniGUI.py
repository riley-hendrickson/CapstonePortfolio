import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
from tkinter.scrolledtext import ScrolledText
from tkinter.ttk import *
import time
from PIL import Image, ImageTk
import shutil
import resources
import os.path
import urllib
import weave_utils
import storage_access
from moviepy.editor import *
from pathlib import Path
from datetime import datetime
from spreadsheets import Spreadsheet
from input_utils import detectIndices, existingPath
from concurrent.futures import as_completed, ProcessPoolExecutor
from config import AlumInfo, VideoConfig
from chapters import Chapter, TextChapter, GradTextChapter, StaticImageChapter, GenericVideosChapter, ThankYouVideoChapter, GradImageChapter
# import clean_worksheets
import multiprocessing
import threading
#import loky
from ColumnSelectGUI import ColumnSelectGUI
import io
import sys

def getDefaultChapters():
    return [
        TextChapter(duration=3, fadeIn=False, text='This is a special video message for you, {alum.firstName}!'),
        GradTextChapter(duration=7),
        GradImageChapter(duration=17), 
        TextChapter(duration=3, text='What students have been up to...'),
        GenericVideosChapter(videoCount=4),
        TextChapter(duration=5, text='Your donation could help shape the future of Computer Science!'),
        StaticImageChapter(duration=4, image=resources.donationOptions),
        ThankYouVideoChapter(videoCount=1),
        StaticImageChapter(duration=4, image=resources.qrPath),
        ]

class GUI:
    numMessages = 0
    maxMessages = 10
    filepath = ""
    filepath_clean = ""
    MAX_WORKERS = None
    readyToGenerate = 0

    def __init__(self):
        self.mpManager = multiprocessing.Manager()
        self.messageQueue = self.mpManager.Queue()
        self.messageHandlers = {
            'log': self.logMessage,
            'progress': self.updateProgress,
            'done': self.onFinished
        }

        self.window = tk.Tk()
        self.window.title("Alumni Donation Video Generator")
        self.window.geometry("1200x1000")
        self.window['background'] = '#ADD8E6'

        script_dir = os.path.dirname(os.path.abspath(__file__))
        backgroundImage = Image.open(os.path.join(script_dir, 'res//navyBackground.png'))
        backgroundImage = ImageTk.PhotoImage(backgroundImage)
        backgroundLabel = tk.Label(image=backgroundImage)
        backgroundLabel.image_names = backgroundImage
        backgroundLabel.pack()

        self.percent = tk.StringVar()
        self.numVideosGenerated = tk.StringVar()
        self.pathString = tk.StringVar()

        self.label = tk.Label(self.window, text="Please Enter Directory to CSV/XLSX File", font=('Dubai Medium', 18))
        self.label['background'] = '#ADD8E6'
        self.label['foreground'] = 'white'
        self.label.pack(padx=10, pady=10)

        selectFileButtonImage = Image.open(os.path.join(script_dir, 'res//button_select-file.jpg'))
        selectFileButtonImage = ImageTk.PhotoImage(selectFileButtonImage)
        self.enterDirectoryBtn = tk.Button(self.window, image=selectFileButtonImage, command=self.find_file, border=0)
        self.enterDirectoryBtn['background'] = '#ADD8E6'
        self.enterDirectoryBtn.pack(pady=20)

        self.file_name = tk.Label(self.window, textvariable=self.pathString, font=('Dubai Medium', 12))
        self.file_name['background'] = '#ADD8E6'
        self.file_name['foreground'] = 'white'
        self.file_name.pack()

        generateButtonImage = Image.open(os.path.join(script_dir, 'res//button_generate-videos.jpg'))
        generateButtonImage = ImageTk.PhotoImage(generateButtonImage)
        self.generateButton = tk.Button(self.window, image=generateButtonImage, command=self.call_Weave, border=0)
        self.generateButton['background'] = '#ADD8E6'
        self.generateButton.pack(pady=5)

        coreCount = multiprocessing.cpu_count()
        workerCounts = [1 << i for i in range(coreCount.bit_length())]
        workerCounts.reverse()
        workerCountFrame = tk.Frame(self.window)
        workerCountFrame['background'] = '#ADD8E6'
        workerCountFrame.pack(pady=10)
        workerCountLabel = tk.Label(workerCountFrame, text='Worker Count:', font=('Dubai Medium', 12, 'bold'))
        workerCountLabel['background'] = '#ADD8E6'
        workerCountLabel['foreground'] = 'white'
        workerCountLabel.pack(side=tk.LEFT)
        self.workerCount = Combobox(workerCountFrame, state='readonly', values=workerCounts, font=('Dubai Medium', 12), width=5)
        self.workerCount.current(0)
        self.workerCount.bind('<<ComboboxSelected>>', self.onWorkerCountChanged)
        self.workerCount.pack(side=tk.LEFT)

        self.bar = Progressbar(self.window, orient="horizontal", length=800)
        self.bar.pack(pady=10)

        self.percentProgress = Label(self.window, textvariable=self.percent, font=('Dubai Medium', 16))
        self.percentProgress['background'] = '#ADD8E6'
        self.percentProgress['foreground'] = 'white'
        self.percentProgress.pack()

        self.numVideosProgress = Label(self.window, textvariable=self.numVideosGenerated, font=('Dubai Medium', 16))
        self.numVideosProgress['background'] = '#ADD8E6'
        self.numVideosProgress['foreground'] = 'white'
        self.numVideosProgress.pack()

        self.outputLog = ScrolledText(self.window, width= 100, height=10, font=('Dubai Medium', 12), foreground='white', background='#ADD8E6', wrap=tk.WORD)
        self.outputLog.configure(state='disabled')
        self.outputLog.pack(pady=10)

        # if the user clicks the exit button, prompt the user to make sure they actually want to exit the application:
        self.window.protocol("WM_DELETE_WINDOW", self.exit_Clicked)

        self.window.after(0, self.processQueue)
        self.window.mainloop()

    def onWorkerCountChanged(self, event):
        self.MAX_WORKERS = int(self.workerCount.get())
        self.logMessage('Worker count set to ' + str(self.MAX_WORKERS))

    def find_file(self):
        filepath = filedialog.askopenfilename(title="Select Donor File", filetypes=(("CSV files", "*.csv"), ("Excel files", "*.xlsx")))
        if not filepath:
            self.logMessage('File selection cancelled. Please try again.')
            return
        self.indices = self.selectIndices(filepath)
        if self.indices is None:
            self.logMessage('Column selection cancelled. Please try again.')
            return
        self.filepath = filepath
        self.pathString.set(self.filepath)
        self.file_name['background'] = '#1c305c'
        self.readyToGenerate = 1
        self.workerCount['state'] = 'readonly'
        self.window.update_idletasks()
    
    def exit_Clicked(self):
        if messagebox.askyesno(title="Quit?", message="Are you sure you want to exit the application?"):
            self.window.destroy()

    def logMessage(self, message):
        self.outputLog.configure(state='normal') # allows the text box contents to be changed
        self.outputLog['background'] = '#1c305c'
        self.numMessages = self.numMessages + 1
        if(self.numMessages == 1):
            self.outputLog.insert(tk.INSERT, message)
        else:
            self.outputLog.insert(tk.INSERT, "\n" + message)
        self.outputLog.configure(state='disabled') # disables editing of the text box contents


    def updateProgress(self, generated, total):
        percent = int(generated / total * 100)
        self.bar['value'] = percent
        self.percent.set(f'{percent}% Completed')
        self.numVideosGenerated.set(f'{generated}/{total} videos generated')

    def onFinished(self):
        print('Cleaning up temporary files...\n')
        shutil.rmtree(resources.cwd / 'weaveTEMP', ignore_errors=True)
        print('Done!\n')
        self.workerCount['state'] = 'readonly'

    def processQueue(self):
        # process all the messages currently in the queue
        while not self.messageQueue.empty():
            event, args, kwargs = self.messageQueue.get()
            handler = self.messageHandlers.get(event)
            if handler:
                handler(*args, **kwargs)
            else:
                self.logMessage(f'WARNING: Unknown event "{event}" received on message queue')
                print(f'WARNING: Unknown event "{event}", args={args}, kwargs={kwargs}')

        # schedule this function to be called again in 10ms
        self.window.after(10, self.processQueue)

    def call_Weave(self):
            if(self.readyToGenerate == 0):
                self.logMessage("You must enter a file before you can generate videos!")
                return

            self.workerCount['state'] = 'disabled'

            inputPath = Path(self.filepath)
            outputPath = inputPath.with_stem(inputPath.stem + '_OUTPUT')

            # weave in a separate thread so the GUI doesn't freeze
            weaver = Weaver(self.messageQueue, self.MAX_WORKERS)
            thread = threading.Thread(target=weaver.weave, args=(inputPath, outputPath), kwargs={'indices': self.indices})
            thread.start()

    def selectIndices(self, filepath):
        indexGui = ColumnSelectGUI(filepath)
        self.window.wait_window(indexGui.window)
        return indexGui.result

class Weaver:
    def __init__(self, messageQueue: multiprocessing.Queue, maxWorkers: int):
        self.messageQueue = messageQueue
        self.maxWorkers = maxWorkers

    def emit(self, event, *args, **kwargs):
        self.messageQueue.put((event, args, kwargs))

    def logMessage(self, message):
        self.emit('log', message)

    def updateProgress(self, generated, total):
        self.emit('progress', generated, total)

    def weaveVideo(self, alum: AlumInfo, config: VideoConfig, chapters: list[Chapter]):
        '''Generate and upload a video for the given row
        Returns the URL of the uploaded video'''

        # print(f'Processing {alum.firstName} {alum.lastName} ({alum.gradYear})')
        self.logMessage("Processing " + alum.firstName + ", " + alum.lastName + ", " + str(alum.gradYear))

        # debugging
        #return 'https://asdf.com/qwerty'

        # Generate chapters
        chapterClips = []
        for chapter in chapters:
            chapterClips += chapter.generate(alum, config)

        # Concatenate chapters together
        final_clip = concatenate_videoclips(chapterClips, method='compose')

        # Add music
        music = AudioFileClip(str(resources.musicPath)).set_duration(final_clip.duration)
        music = afx.volumex(music, 0.1)
        new_audio = CompositeAudioClip([final_clip.audio,music])
        final_clip = final_clip.set_audio(new_audio)

        # Render the final video
        videoName = urllib.parse.quote(f'{alum.firstName}_{alum.lastName}_{weave_utils.genHash()}')
        videoNameExt = videoName + '.mp4'
        final_clip.write_videofile(str(config.workDir / videoNameExt), audio_codec='aac', temp_audiofile=str(config.workDir / 'temp-audio.m4a'), logger=None, verbose=False)

        self.logMessage("Success! Uploading video to firebase...")

        # Upload the video to firebase
        storage_access.uploadToStor(config.workDir, videoNameExt)
        videoUrl = 'https://wwucsgiving.web.app/?name=' + videoName
        self.logMessage("Video URL: " + videoUrl)

        # Delete the temporary directory when we're done
        shutil.rmtree(config.workDir)

        return videoUrl


    # TODO: handle output file already existing (prompt to overwrite or something)
    # TODO: chapter selection/customization GUI instead of hardcoding?
    def weave(self, inputPath, outputPath, indices, chapters=getDefaultChapters()):
        '''Generates videos and outputs a spreadsheet with video URLs'''
        start = datetime.now()

        if outputPath.exists():
            if not messagebox.askyesno(title='Overwrite file?', message='The output file already exists. Overwrite?', default='no', icon='warning'):
                return

        # Parse input spreadsheet
        spreadsheet = Spreadsheet.fromFile(inputPath)

        # Process rows
        videoUrlColumn = spreadsheet.addColumn('Video URL')
        #with loky.get_reusable_executor(max_workers=self.maxWorkers) as executor:
        with ProcessPoolExecutor(max_workers=self.maxWorkers) as executor:
            futureToRow = {}
            # Start video generation tasks
            for rowIndex, rowData in spreadsheet.getRows():
                kwargs = {key: rowData[index] and str(rowData[index]).strip() for key, index in indices.items()}
                alum = AlumInfo(**kwargs)
                if not alum.firstName:
                    self.logMessage(f'WARNING: Skipping row {rowIndex} (missing firstName)')
                    continue
                if not alum.lastName:
                    self.logMessage(f'WARNING: Skipping row {rowIndex} (missing lastName)')
                    continue
                if not alum.email:
                    self.logMessage(f'WARNING: Skipping row {rowIndex} (missing email)')
                    continue
                config = VideoConfig()
                future = executor.submit(self.weaveVideo, alum, config, chapters)
                futureToRow[future] = rowIndex
            # Update spreadsheet with video URLs as they become available
            generatedCount = 0
            totalCount = len(futureToRow)
            self.updateProgress(0, totalCount)
            for future in as_completed(futureToRow):
                generatedCount += 1
                self.updateProgress(generatedCount, totalCount)
                rowIndex = futureToRow[future]
                try:
                    videoUrl = future.result()
                    spreadsheet.setCell(rowIndex, videoUrlColumn, videoUrl)
                    print(f'Finished processing row {rowIndex}, video URL: {videoUrl}')
                except Exception as e:
                    self.logMessage(f'Error processing row {rowIndex}: {e}')
                    # uncomment for debugging (warning: may break progress bar and/or entire program if an error occurs)
                    #raise e

        # Save output spreadsheet
        spreadsheet.save(outputPath)
        self.logMessage('Output saved to ' + str(outputPath))
        duration = datetime.now() - start
        self.logMessage('Finished in ' + str(duration))
        print('Finished in ' + str(duration))
        self.emit('done')

# main guard is needed for multiprocessing.* to work
if __name__ == '__main__':
    # prevent modules that rely on stdout from breaking when using PyInstaller's --noconsole
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w')

    # needed for PyInstaller to work
    multiprocessing.freeze_support()
    # loky is broken in frozen apps on windows: https://github.com/joblib/loky/issues/236
    #loky.freeze_support() # this should fix it but isn't released yet: https://github.com/joblib/loky/pull/375

    GUI()
