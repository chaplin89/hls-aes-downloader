#!/usr/bin/env python3
import requests
import json
import logging
import m3u8
import pprint
import urllib.parse
import os.path
from progress.bar import ChargingBar

class Trainer:
    def __init__(self, uri, uuid):
        self.uri = uri
        self.uuid = uuid
        self.metadata = None
        self.courses = None

class Course:
    def __init__(self, uri, uuid):
        self.uri = uri
        self.uuid = uuid
        self.metadata = None
        self.lessons = None

class Lesson:
    def __init__(self, uri, uuid):
        self.uri = uri
        self.uuid = uuid
        self.metadata = None
        self.video = None
        self.master = None
        self.best_stream = None
        self.segments = None 

class AESKey:
    def __init__(self, key, iv):
        self.key = key
        self.iv = iv

class BrowserMock:
    __USER_AGENT='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36'
    __LANGUAGES='en,en-US;q=0.9,en-GB;q=0.8,it-IT;q=0.7,it;q=0.6'
    
    def __init__(self, cookies_jar_path='cookies.txt'):
        self.__cookies = self.__getCookies(cookies_jar_path)

    def GetCommonHeaders(self):
        headers = {
            'user-agent': BrowserMock.__USER_AGENT, 
            'accept-language': BrowserMock.__LANGUAGES,
            'cookie': self.__cookies
        }
        return headers

    def __getCookies(self, cookies_jar_path):
        try:
            with open(cookies_jar_path, "r") as cookies_jar:
                return cookies_jar.read().strip() 
        except:
            raise Exception("Cookies not found.")

class TrainerRequest:
    def __init__(self, uri, uuid):
        self.response = None
        self.uuid = uuid
        self.uri = uri
        self.courses = []
        self.__browser = BrowserMock()
        self.__headers = self.__browser.GetCommonHeaders()

    def DoRequest(self):
        if self.response is None:
            parameters = { 'trainer_id' : self.uuid }
            uri = os.path.join(self.uri, "api", "courses")
            trainer_req = requests.get(uri, params=parameters, headers=self.__headers)
            trainer_req.raise_for_status()
            logging.debug("Request for trainer with id {} successful.".format(self.uuid))
            self.response = trainer_req.json()
        return self.response

    def GetCourseRequests(self):
        return [CourseRequest(self.uri, x['id']) for x in self.response['data']['courses']]

class CourseRequest:
    def __init__(self, uri, uuid):
        self.response = None
        self.uuid = uuid
        self.uri = uri
        self.__browser = BrowserMock()
        self.__headers = self.__browser.GetCommonHeaders()

    def DoRequest(self):
        if self.response is None:
            parameters = { 'course_id' : self.uuid }
            uri = os.path.join(self.uri, "api", "course")
            course_req = requests.get(uri, params=parameters, headers=self.__headers)
            course_req.raise_for_status()
            logging.debug("Request for course with id {} successful.".format(self.uuid))
            self.response = course_req.json()
        return self.response

    def GetLessonRequests(self):
        return [LessonRequest(self.uri, x['id']) for x in self.response['data']['lessons']]

class LessonRequest:
    def __init__(self, uri, uuid):
        self.response = None
        self.browser = BrowserMock()
        self.uuid = uuid 
        self.uri = uri
        self.__headers = self.browser.GetCommonHeaders()

    def DoRequest(self):
        if self.response is None:
            parameters = { "lesson_id" : self.uuid }
            uri = os.path.join(self.uri, "api", "video")
            video_req = requests.get(uri, params=parameters, headers=self.__headers)
            video_req.raise_for_status()
            logging.debug("Request for video with id {} successful.".format(self.uuid))
            self.response = video_req.json()
        return self.response

    def GetMasterRequest(self):
        parameters = self.__getParameters()
        master_name = self.__getMasterName()
        base_address = self.__getBaseAddress()
        uuid = master_name.rsplit('/', 2)[1]
        return MasterRequest(base_address, uuid, parameters, master_name)

    def __getParameters(self):
        return self.response['data']['token']['token_querystring']
 
    def __getMasterName(self):
        return self.response['data']['token']['url']
  
    def __getBaseAddress(self):
        parsed = urllib.parse.urlparse(self.response['data']['token']['url'])
        return parsed.scheme + '://' + parsed.netloc + '/'

class MasterRequest:
    def __init__(self, uri, uuid, parameters, master_name):
        self.response = None
        self.uri = uri
        self.uuid = uuid
        self.parameters = parameters
        self.master_name = master_name

    def DoRequest(self):
        if self.response is None:
            master_req = requests.get(self.master_name, params=self.parameters)
            master_req.raise_for_status()
            logging.debug("Request for master M3U8 with id {} successful.".format(self.uuid))
            self.response = master_req
            logging.debug(self.response)
        return self.response

    def GetBestStreamRequest(self):
       best_stream_name = self.__getMaximumBitrateSegment()
       return BestStreamRequest(self.uri, self.uuid, self.parameters, best_stream_name)

    def __getMaximumBitrateSegment(self):
        playlist = m3u8.loads(self.response.text)
        logging.debug('Parsing of Master M3U3 for id {} successful.'.format(self.uuid))

        if len(playlist.playlists) <= 1:
            raise Exception("This is not a variant playlist!")

        max_bitrate = max(playlist.playlists, key = lambda p: p.stream_info.bandwidth)
        logging.debug("The chosen bitrate for video with id {} is {}.".format(self.uuid, max_bitrate.stream_info.bandwidth))
        return max_bitrate.uri

class BestStreamRequest:
    def __init__(self, uri, uuid, parameters, best_stream_name):
        self.response = None
        self.uuid = uuid
        self.parameters = parameters
        self.uri = uri
        self.best_stream_name = best_stream_name
        self.key = None

    def DoRequest(self):
        if self.response is None:
            uri = os.path.join(self.uri, self.uuid, self.best_stream_name)
            best_stream_req = requests.get(uri, params = self.parameters)
            best_stream_req.raise_for_status()
            logging.debug("Request for best stream with id {} successful.".format(self.uuid))
            self.response = best_stream_req
            logging.debug(self.response)
        return self.response

    def GetKey(self):
        if self.key is None:
            playlist = m3u8.loads(self.response.text)
            if len(playlist.keys) != 1:
                raise Exception("Wrong number of keys detected {}".format(len(playlist.keys)))
            key = playlist.keys[0]
            uri = os.path.join(self.uri, self.uuid, key.uri)
            key_req = requests.get(uri, params=self.parameters)
            self.key = AESKey(key_req.content, key.iv)
        return self.key

    def GetSegmentRequests(self):
        playlist = m3u8.loads(self.response.text)
        return [SegmentRequest(self.uri, self.uuid, self.parameters, x) for x in playlist.segments]

class SegmentRequest:
    def __init__(self, uri, uuid, parameters, segment):
        self.response = None
        self.uuid = uuid
        self.parameters = parameters
        self.uri = uri
        self.segment = segment

    def DoRequest(self):
        if self.response is None:
            uri = os.path.join(self.uri, self.uuid, self.segment.uri)
            segment_req = requests.get(uri, params = self.parameters)
            segment_req.raise_for_status()
            logging.debug("Request for segment {} of video with id {} successful.".format(self.segment.uri, self.uuid))
            self.response = segment_req
        return self.response

class Container:
    def __init__(self, uuid, root='./'):
        self.uuid = uuid
        self.root = root
        self.path = os.path.join(root, uuid)

        if not os.path.isdir(root):
            os.mkdir(root)
        if not os.path.isdir(self.path):
            os.mkdir(self.path)

    def AddCourse(uuid):
        path = os.path.join(self.path, uuid)
        if not os.path.isdir(path):
            os.mkdir(path)

    def WriteMetadata(self, meta):
        path = os.path.join(self.path, 'metadata.json')
        with open(path, 'w') as s:
            s.write(json.dumps(meta, indent=4))

class LessonContainer:
    def __init__(self, uuid, root = './'):
        self.uuid = uuid
        self.root = root
        self.path = os.path.join(root, uuid)

        if not os.path.isdir(self.path):
            os.mkdir(self.path)

    def IsSegmentDownloaded(self, segment):
        path = os.path.join(self.root, self.uuid, segment.uri)
        return os.path.isfile(path)

    def WriteMetadata(self, meta):
        path = os.path.join(self.root, self.uuid, "metadata.json")
        with open(path, 'w') as s:
            s.write(json.dumps(meta, indent=4))

    def WriteSegment(self, segment, response):
        path = os.path.join(self.root, self.uuid, segment.uri)
        with open(path, 'wb') as s:
            s.write(response.content)
            logging.debug("Write segment {} of video with id {} successful.".format(segment.uri, self.uuid))

    def WriteKey(self, key):
        key_path = os.path.join(self.root, self.uuid, "key.bin")
        iv_path = os.path.join(self.root, self.uuid, "iv.bin")
        with open(key_path, 'wb') as k:
            k.write(key.key)
        with open(iv_path, 'w') as i:
            i.write(key.iv)

    
class Downloader:
    __URI = "https://example.com/"
    __LOGGING_LEVEL = logging.INFO

    def __init__(self):
        logging.basicConfig(filename='downloader.log', level=Downloader.__LOGGING_LEVEL)

    def DownloadTrainer(self, uuid):
        request = TrainerRequest(Downloader.__URI, uuid)
        response = request.DoRequest()

        trainer = Trainer(Downloader.__URI, uuid)
        trainer.courses = request.GetCourseRequests()
        trainer.metadata = response
        return trainer

    def DownloadCourse(self, course_request):
        response = course_request.DoRequest()
        lessons = course_request.GetLessonRequests()

        course = Course(course_request.uri, course_request.uuid)
        course.lessons = lessons
        course.metadata = response
        return course

    def DownloadLessons(self, lesson_request):
        response = lesson_request.DoRequest()
        master = lesson_request.GetMasterRequest()

        master.DoRequest()
        best_stream = master.GetBestStreamRequest()

        best_stream.DoRequest()
        segments = best_stream.GetSegmentRequests()
        key = best_stream.GetKey() 
        
        lesson = Lesson(lesson_request.uri, lesson_request.uuid)
        lesson.master = master
        lesson.best_stream = best_stream
        lesson.segments = segments
        lesson.metadata = response
        lesson.key = key
        return lesson

    def Download(self, trainers='trainers.txt'):
        with open(trainers, 'r') as t:

            for trainer_id in t:
                trainer_id = trainer_id.strip()
                trainer = self.DownloadTrainer(trainer_id)
                trainer_container = Container(trainer_id, './download/')
                trainer_container.WriteMetadata(trainer.metadata)
                print("Processing trainer with id {}.".format(trainer_id))
                for index, course_request in enumerate(trainer.courses):
                    course = self.DownloadCourse(course_request)
                    course_container = Container(course.uuid, trainer_container.path)
                    course_container.WriteMetadata(course.metadata)
                    print("Processing course {}/{}: '{}'".format(index+1, len(trainer.courses), course.metadata['data']['highlights']))
                    for index, lesson_request in enumerate(course.lessons):
                        lesson = self.DownloadLessons(lesson_request)
                        lesson_container = LessonContainer(lesson.uuid, course_container.path)
                        lesson_container.WriteMetadata(lesson.metadata)
                        lesson_container.WriteKey(lesson.key)
                        segment_bar = ChargingBar("Downloading lesson {}/{}:".format(index+1, len(course.lessons)), max=len(lesson.segments), suffix='%(index)d/%(max)d - ETA %(eta)ds')
                        for segment in lesson.segments:
                            if not lesson_container.IsSegmentDownloaded(segment.segment):
                                response = segment.DoRequest()
                                lesson_container.WriteSegment(segment.segment, response)
                            segment_bar.next()
                        print('\n')
                    print("Processing course '{}' completed.".format(course.metadata['data']['highlights']))
                print("Trainer {} completed.".format(trainer_id))

if __name__ == '__main__':
    downloader = Downloader()
    downloader.Download()
