import weave_utils
import storage_access
import resources
from pathlib import Path
from moviepy.editor import *
from datetime import datetime
from config import AlumInfo, VideoConfig

# Interface for all chapters.
# Subclasses should provide a constructor and implement generate()
class Chapter:
    def __init__(self):
        raise NotImplementedError()
    
    # Generate the chapter and return a list with one or more moviepy VideoFileClips
    def generate(self, alumInfo: AlumInfo, videoConfig: VideoConfig) -> list[VideoFileClip]:
        raise NotImplementedError()

# simple text chapter
class TextChapter(Chapter):
    def __init__(self, text: str, duration: float, fadeIn: bool = True):
        self.text = text
        self.duration = duration
        self.fadeIn = fadeIn

    def generate(self, alumInfo, videoConfig):
        formattedText = self.text.format(alum=alumInfo)
        return [weave_utils.textToVideo(videoConfig.workDir, self.duration, formattedText, videoConfig.width, videoConfig.height, fadeIn=self.fadeIn)]

# text chapter based on grad year
class GradTextChapter(Chapter):
    def __init__(self, duration: float):
        self.duration = duration

    def generate(self, alumInfo, videoConfig):
        gradText = "CS at Western continually modernizes itself to cultivate young minds and prepare students for successful careers in an ever-changing world."
        try:
            gradYear = int(float(alumInfo.gradYear))
            curYear = datetime.now().year
            yearsSinceGrad = curYear - gradYear
            # Check for how long ago the alumni graduated from Western (if at all) to make the intro text more personalized
            if(yearsSinceGrad <= 1):
                gradText = "Congratulations on graduating this past year! CS at Western has continued to grow and expand, all the while cultivating young minds and preparing students for successful careers."
            elif(yearsSinceGrad < 10):
                gradText = "Since your graduation only " + str(yearsSinceGrad) + " years ago, CS at Western has continued to grow and expand, all the while cultivating young minds and preparing students for successful careers."
            elif(yearsSinceGrad >= 10):
                gradText = "Since your graduation " + str(yearsSinceGrad) + " years ago, CS at Western has grown and expanded, all the while cultivating young minds and engaging students with the newest technologies."
        except:
            gradText = "As a friend and supporter of CS at Western, you have helped cultivate young minds and prepare students for successful careers."
        return [weave_utils.textToVideo(videoConfig.workDir, self.duration, gradText, videoConfig.width, videoConfig.height)]
 
 # image chapter based on grad year
class GradImageChapter(Chapter):
     def __init__(self, duration: float):
        self.duration = duration
        self.gradImagePath = str(resources.newBuildingPath)
        self.gradBuildingText = "The CS department is getting a new building, Kaiser Borsari Hall, Western's new electrical and computer engineering, and computer science building, started construction on March 20, 2023. It will provide state-of-the-art teaching spaces and experimental learning environments."
     def generate(self, alumInfo, videoConfig):
        self.gradImagePath = str(resources.newBuildingPath)
        try:
            gradYear = int(float(alumInfo.gradYear))
            curYear = datetime.now().year
            yearsSinceGrad = curYear - gradYear
            print(yearsSinceGrad)
            print(self.gradImagePath)
            # Check for how long ago the alumni graduated from Western (if at all) to make the intro text more personalized

            # Graduated after the CF building and Academic west was built show them the upcoming building
            if(yearsSinceGrad <= 14): 
                self.gradImagePath = str(resources.newBuildingPath)
                self.gradBuildingText = "The CS Department is getting a new building, Kaiser Borsari Hall! This building will host mainly Computer Science courses, as well as Electrical and Computer Engineering courses, and started construction on March 20, 2023. It will provide state-of-the-art teaching spaces and experimental learning environments."

            # Graduated befor the Academic West building was built show them that
            elif(yearsSinceGrad > 14 and yearsSinceGrad < 19):
                self.gradImagePath = str(resources.awBuildingPath)
                self.gradBuildingText = "The WWU campus has grown, the Academic West building was built in 2009 is an LEED certified building, and is one of the largest naturally ventilated academic buildings in the country and a national model for passive green design strategies."

            # Graduated before the CF building was built show them that.
            elif(yearsSinceGrad >= 19):
                self.gradImagePath = str(resources.cfBuildingPath)
                self.gradBuildingText = "The CS department has grown, the Communications Facility is a 131,000 SF building that was built in 2004. It houses the departments of the Computer Science, Physics, Communications, and Journalism. The building is organized into two five-story towers connected by a four-story atrium/lobby."

        except:
            self.gradImagePath = str(resources.newBuildingPath)

    

        return[weave_utils.textToVideoImage(videoConfig.workDir, self.gradImagePath ,self.duration, self.gradBuildingText, videoConfig.width, videoConfig.height)]
    # return [ImageClip(self.gradImagePath).set_duration(self.duration).resize(height=videoConfig.height,width=videoConfig.width)]

# simple image chapter
class StaticImageChapter(Chapter):
    def __init__(self, image, duration: float):
        self.image = str(image)
        self.duration = duration

    def generate(self, alumInfo, videoConfig):
        return [ImageClip(self.image).set_duration(self.duration).resize(height=videoConfig.height,width=videoConfig.width)]

# abstraction for chapters that use downloaded videos
class DownloadedVideoChapter(Chapter):
    def __init__(self, contentBin: str, videoCount: int):
        self.contentBin = contentBin
        self.videoCount = videoCount

    def generate(self, alumInfo, videoConfig, years=None):
        # hack to allow for different years to be used for different chapters
        # we only have 'thanks' clips for 2022
        if years is None:
            years = videoConfig.contentYears
        content = storage_access.downloadContentFromStor(videoConfig.workDir, self.contentBin, years, self.videoCount)
        clips = []
        for clipPath in content:
            edited = VideoFileClip(str(clipPath))
            edited = edited.set_fps(videoConfig.fps)
            edited = edited.resize(height=videoConfig.height,width=videoConfig.width)
            edited = edited.fx(afx.audio_normalize)
            edited = vfx.fadein(edited, 0.3, initial_color=None)
            edited = vfx.fadeout(edited, 0.3, final_color=None)
            clips.append(edited)
        return clips

# random generic clip(s)
class GenericVideosChapter(DownloadedVideoChapter):
    def __init__(self, videoCount: int):
        super().__init__('v', videoCount)

# random thank you clip(s)
class ThankYouVideoChapter(DownloadedVideoChapter):
    def __init__(self, videoCount: int):
        super().__init__('t', videoCount)

    #def generate(self, alumInfo, videoConfig):
    #    # hack to allow for different years to be used for different chapters
    #    # we only have 'thanks' clips for 2022
    #    years = ['2022']
    #    return super().generate(alumInfo, videoConfig, years)
