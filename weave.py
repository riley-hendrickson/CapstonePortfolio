import shutil
import urllib
import argparse
import resources
import weave_utils
import storage_access
from moviepy.editor import *
from pathlib import Path
from datetime import datetime
from spreadsheets import Spreadsheet
from input_utils import detectIndices, existingPath
from concurrent.futures import ProcessPoolExecutor, as_completed
from config import AlumInfo, VideoConfig
from chapters import Chapter, TextChapter, GradTextChapter, StaticImageChapter, GenericVideosChapter, ThankYouVideoChapter

MAX_WORKERS = None # default: use all available cores
#MAX_WORKERS = 8
#MAX_WORKERS = 4
#MAX_WORKERS = 1

def getDefaultChapters():
    return [
        TextChapter(duration=3, fadeIn=False, text='This is a special video message for you, {alum.firstName}!'),
        GradTextChapter(duration=7),
        GenericVideosChapter(videoCount=4),
        TextChapter(duration=3, text='Your donation could help shape the future of computer science!'),
        ThankYouVideoChapter(videoCount=1),
        StaticImageChapter(duration=4, image=resources.qrPath),
    ]

def weaveVideo(alum: AlumInfo, config: VideoConfig, chapters: list[Chapter]):
    '''Generate and upload a video for the given row
    Returns the URL of the uploaded video'''

    print(f'Processing {alum.firstName} {alum.lastName} ({alum.gradYear})')

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
    final_clip.write_videofile(str(config.workDir / videoNameExt), audio_codec='aac')

    # Upload the video to firebase
    storage_access.uploadToStor(config.workDir, videoNameExt)
    videoUrl = 'https://wwucsgiving.web.app/?name=' + videoName

    # Delete the temporary directory when we're done
    shutil.rmtree(config.workDir)

    return videoUrl


def weave(inputPath, outputPath=None, indices=None, interactive=False, chapters=getDefaultChapters()):
    '''Generates videos and outputs a spreadsheet with video URLs'''
    start = datetime.now()

    if outputPath is None:
        outputPath = inputPath.with_stem(inputPath.stem + '_OUTPUT')

    if outputPath.exists():
        if not interactive:
            raise RuntimeError(f'Output file already exists: {outputPath}')
        if input(f'Output file already exists: {outputPath}. Overwrite? (y/n): ').lower() != 'y':
            print('Aborting')
            return

    # Parse input spreadsheet
    spreadsheet = Spreadsheet.fromFile(inputPath)

    # Auto-detect indices if not provided
    if indices is None:
        indices = detectIndices(spreadsheet.getHeaders(), interactive=interactive)
        if interactive:
            # Find first valid row (with non-empty firstName and lastName)
            firstValidRow = next((row for i, row in spreadsheet.getRows() if row[indices['firstName']] and row[indices['lastName']]), None)
            if firstValidRow is None:
                print('Could not find any rows with firstName and lastName')
                return
            # Prompt user to confirm values
            print('Do all values for the first donor look correct?')
            for key, index in indices.items():
                print(f'  {key}: {firstValidRow[index]}')
            if input('(y/n): ').lower() != 'y':
                print('Aborting')
                return

    # Process rows
    videoUrlColumn = spreadsheet.addColumn('Video URL')
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futureToRow = {}
        # Start video generation tasks
        for rowIndex, rowData in spreadsheet.getRows():
            kwargs = {key: rowData[index] and str(rowData[index]).strip() for key, index in indices.items()}
            alum = AlumInfo(**kwargs)
            if not alum.firstName or not alum.lastName:
                print(f'WARNING: Skipping row {rowIndex} (missing firstName or lastName)')
                continue
            config = VideoConfig()
            future = executor.submit(weaveVideo, alum, config, chapters)
            futureToRow[future] = rowIndex
        # Update spreadsheet with video URLs as they become available
        for future in as_completed(futureToRow):
            rowIndex = futureToRow[future]
            try:
                videoUrl = future.result()
                spreadsheet.setCell(rowIndex, videoUrlColumn, videoUrl)
                print(f'Finished processing row {rowIndex}, video URL: {videoUrl}')
            except Exception as e:
                print(f'Error processing row {rowIndex}: {e}')

    # Save output spreadsheet
    spreadsheet.save(outputPath)
    print(f'Output saved to {outputPath}')
    print(f'Finished in {datetime.now() - start}')

def main():
    '''Main entry point: python3 weave.py <input file> [<output file>]'''

    parser = argparse.ArgumentParser(description='Weave together personalized videos using student data')
    parser.add_argument('inputFile', type=existingPath, help='Input spreadsheet file (CSV or XLSX)')
    parser.add_argument('outputFile', type=Path, help='Output file name (must be same format). Default is input file name with _OUTPUT appended', nargs='?')

    args = parser.parse_args()

    weave(args.inputFile, args.outputFile, interactive=True)

    shutil.rmtree(resources.cwd / 'weaveTEMP', ignore_errors=True)

if __name__ == '__main__':
    main()
