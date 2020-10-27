#!/usr/bin/env python3
import json
import os
from shutil import copyfile
import yaml

def GetDecryptedFileName(lesson_path):
    """Decrypted file in a lesson folder follow the convention lesson_id.decrypted."""
    decrypted_path = os.path.join(lesson_path, lesson_path.rsplit('/',1)[1])
    decrypted_path = decrypted_path + '.decrypted'
    return decrypted_path

def RemoveUnneededInfo(meta):
    """Starting from course metadata, this function remove unneeded information."""
    pointer = meta['data']
    trimmed = dict()
    key_root = ['summary', 'lesson_tot', 'description', 'title', 'highlights']
    key_trainers = ['last_name', 'first_name']
    key_lessons = ['lesson_num', 'summary', 'description', 'title']
    for key in key_root:
        trimmed[key] = pointer[key]

    pointer = meta['data']['trainers']
    trimmed['trainers'] = []
    for trainer in pointer:
        trimmed_trainer = dict()
        for key in key_trainers:
            trimmed_trainer[key] = trainer[key]
        trimmed['trainers'].append(trimmed_trainer)

    pointer = meta['data']['lessons']
    trimmed['lessons'] = []
    for lesson in pointer:
        trimmed_lesson = dict()
        for key in key_lessons:
            trimmed_lesson[key] = lesson[key]
        trimmed['lessons'].append(trimmed_lesson)
    return trimmed

if __name__ == '__main__':
    package_dir = './package'
    trainers = [x for x in os.listdir('./download') if os.path.isdir(os.path.join('./download',x))]
    if not os.path.isdir(package_dir):
        os.mkdir(package_dir)

    for index, trainer in enumerate(trainers):
        print("Trainer {}/{}: {}.".format(index+1, len(trainers), trainer))
        trainer_path = os.path.join('./download', trainer)
        trainer_meta = None
        with open(os.path.join(trainer_path, 'metadata.json'), 'r') as m:
            trainer_meta = json.loads(m.read())

        courses = [x for x in trainer_meta['data']['courses']]

        for index,course in enumerate(courses):
            course_id = course['id']
            course_path = os.path.join(trainer_path, course_id)
            course_meta = None
            course_meta_path = os.path.join(course_path, 'metadata.json')

            if os.path.isdir(course_path):
                print("\t✔ Course {}/{}: {}.".format(index+1, len(trainers), course_id))
            else:
                print("\t✕ Course {}/{}: {}.".format(index+1, len(trainers), course_id))
                continue

            with open(course_meta_path, 'r') as m:
                course_meta = json.loads(m.read())

            package_course_path = os.path.join(package_dir, course_meta['data']['title'])
            if not os.path.isdir(package_course_path):
                os.mkdir(package_course_path)
            
            package_course_meta_path = os.path.join(package_course_path, 'metadata.yaml')
            trimmed = RemoveUnneededInfo(course_meta)
            with open(package_course_meta_path, 'w') as m:
                yaml.dump(trimmed, m, allow_unicode=True) 

            lessons = [x for x in course_meta['data']['lessons']]
            for index, lesson in enumerate(lessons):
                lesson_id = lesson['id']
                lesson_path = os.path.join(course_path, lesson_id)
                lesson_meta = None
                lesson_meta_path = os.path.join(lesson_path, 'metadata.json')

                if os.path.isdir(lesson_path) and os.path.isfile(GetDecryptedFileName(lesson_path)):
                    print("\t\t✔ Lesson {}/{}: {}.".format(index+1, len(lessons), lesson_id))
                else:                
                    print("\t\t✕ Lesson {}/{}: {}.".format(index+1, len(lessons), lesson_id))
                    continue

                with open(lesson_meta_path, 'r') as m:
                    lesson_meta = json.loads(m.read())

                package_lesson_path = os.path.join(package_course_path, "Lesson_{}.mp4".format(lesson_meta['data']['lesson']['lesson_num']))
                os.system("ffmpeg -i \"{}\" -hide_banner -loglevel quiet -codec copy {}".format(GetDecryptedFileName(lesson_path), package_lesson_path.replace("'", "\\'").replace(' ', '\ ')))
            print('\n')

