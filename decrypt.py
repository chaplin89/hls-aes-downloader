#!/usr/bin/env python3
from Crypto.Cipher import AES
import os
from progress.bar import ChargingBar

class Decrypt:
    def __init__(self):
        pass

    def DecryptFile(self, file_path):
        key = None
        iv = None
        decrypted = None

        path = os.path.dirname(file_path)
        key_path = os.path.join(path, 'key.bin')
        iv_path = os.path.join(path, 'iv.bin')
         
        with open(key_path, 'rb') as k:
            key = k.read()    
        with open(iv_path, 'r') as i:
            iv =bytes(bytearray.fromhex(i.read()[2::]))

        aes = AES.new(key, AES.MODE_CBC, iv)

        with open(file_path, 'rb') as d:
                decrypted = aes.decrypt(d.read())
        return decrypted

    def Initialize(self, lesson_path):
        decrypted_path = os.path.join(lesson_path, lesson_path.rsplit('/',1)[1])
        decrypted_path = decrypted_path + '.decrypted'

        with open(decrypted_path, 'w') as o:
            pass

    def ProcessFile(self, file_path):
        decrypted = self.DecryptFile(file_path)
        parent = os.path.dirname(file_path)
        decrypted_path = os.path.join(parent, parent.rsplit('/',1)[1])
        decrypted_path = decrypted_path + '.decrypted'

        with open(decrypted_path, 'ab') as o:
                o.write(decrypted)


if __name__ == '__main__':
    decrypt = Decrypt()
    trainers = [x for x in os.listdir('./download') if os.path.isdir(os.path.join('./download',x))]
    for index, trainer in enumerate(trainers):
        print("Start processing trainer {}/{}: {}.".format(index+1, len(trainers), trainer))
        trainer_path = os.path.join('./download', trainer)
        courses = [x for x in os.listdir(trainer_path) if os.path.isdir(os.path.join(trainer_path, x))]
        for index,course in enumerate(courses):
            print("Start processing course {}/{}: {}.".format(index+1, len(trainers), course))
            course_path = os.path.join(trainer_path, course)
            lessons = [x for x in os.listdir(course_path) if os.path.isdir(os.path.join(course_path, x))]
            for index, lesson in enumerate(lessons):
                lesson_path = os.path.join(course_path, lesson)
                segments = [x for x in os.listdir(lesson_path) if os.path.isfile(os.path.join(lesson_path,x)) and x.endswith('.ts')]
                segments.sort(key=lambda x: int(x[x.find('segment')+len('segment'): x.rfind('.'):]))
                segment_bar = ChargingBar("Processing lesson {}/{}:".format(index+1, len(lessons)), max=len(segments), suffix='%(index)d/%(max)d - ETA %(eta)ds')
                decrypt.Initialize(lesson_path)
                for segment in segments:
                    segment_path = os.path.join(lesson_path, segment)
                    decrypt.ProcessFile(segment_path)
                    segment_bar.next()
            print('\n')


