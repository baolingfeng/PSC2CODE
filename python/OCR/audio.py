import re
import os
import sys
sys.path.append('..')
from setting import *

def srt_time_to_second(srt_time):
    first_part, millseconds = srt_time.split(',')
    hour, minute, second = first_part.split(":")

    return int(hour) * 3600 + int(minute) * 60 + int(second) + int(millseconds) * 1.0 / 1000

def translate_srt_script(filepath):
    script = []
    word_set = set()
    if not os.path.exists(filepath):
        return [], []
    
    with open(filepath) as fin:
        lines = fin.readlines()

        i = 0
        while i < len(lines):
            caption_id = lines[i]
            caption_time = lines[i+1]
            caption_text = lines[i+2]

            start, end = caption_time.split(" --> ")
            start = srt_time_to_second(start)
            end = srt_time_to_second(end)

            caption_text = re.sub("<.*?>", "", caption_text)
            script.append([start, end, caption_text.strip()])

            words = caption_text.split()
            word_set |= set(words)

            i += 4
    
    return script, word_set

def main():
    audio_file = os.path.join(audio_dir, "Intermediate Java Tutorial - 2 - Some More String Methods.srt")

    print translate_srt_script(audio_file)

if __name__ == '__main__':
    main()
