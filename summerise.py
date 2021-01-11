# youtube-dl to summeries.

# dl all videos from a playlist when uploaded
# get 

import youtube_dl
import webvtt
import tempfile
import punctuator
# from PIL import Image
import base64

import datetime
from contextlib import contextmanager
import sys, os
import subprocess as sp
import glob

from pprint import pprint as p

from punctuator import Punctuator
punctuator = Punctuator('Demo-Europarl-EN.pcl')
print("loaded model")

@contextmanager
def temp_working_directory():
    """
    A context manager which changes the working directory to a new tempdir
    path, and then changes it back to its previous value on exit.
    Usage:
    > # Do something in original directory
    > with working_directory('/my/new/path'):
    >     # Do something in new directory
    > # Back to old directory
    """

    with tempfile.TemporaryDirectory() as path:
        prev_cwd = os.getcwd()
        os.chdir(path)
        try:
            yield
        finally:
            os.chdir(prev_cwd)

class ContentItem():
    
    def __init__(self, line=None, image=None):
        if line is not None:
            self.type = "line"
            self.data = line
        elif image is not None:
            self.type = "image"
            self.data = image
        else:
            raise ValueError("set at most one of line and image")
    
    def render(self):
        if self.type == "line":
            return f"""<div> {self.data} </div>\n"""
        if self.type == "image":
            return f"""<div> <img src="data:image/jpeg;base64,{self.data}" width=200 /> </div>\n"""

def download(url="https://www.youtube.com/watch?v=b8UF-P5_2WQ"):
    ydl_opts = {
        'format': 'bestvideo[height<=720]',
        'writesubtitles':True, 'writeautomaticsub':True, 'subtitlesformat':'vtt', 'subtitleslang':'en',
        'outtmpl': 'file.mkv',
    }
    ydl = youtube_dl.YoutubeDL(ydl_opts)
    info_dict = ydl.extract_info(url, download=False)
    if (not info_dict["subtitles"]) and (not info_dict["automatic_captions"]):
        raise RuntimeError(f"no captions for url {url}")
    info_dict = ydl.extract_info(url, download=True)
    title = info_dict['title']
    fn = ydl.prepare_filename(info_dict)
    return info_dict

def get_thumbs():
    sp.run(["ffmpeg", "-vsync", "0", "-i", "file.mkv", "-vf", "fps=1,select='not(mod(t,30))'", "-frame_pts", "1", "tempfile.%d.jpg"], check=True)

def get_subs():
    """we want to return a list of word, time tuples.
    When we have that, we can define a useable start time for each sentence given the punctuation
    we find later.
    """
    vtt = webvtt.read('file.mkv.en.vtt')

    lines = []
    for line in vtt:
        lines.append((line.start, line.text.strip().splitlines()))

    p(lines)
    transcript = []
    start_times = []

    for start_time, phrase_collection in lines:
        # print(transcript[-5:], start_time, phrase_collection)
        for phrase in phrase_collection:
            # if it's new (not the last phrase we added)
            if transcript and transcript[-1] == phrase:
                continue
            start_times.append(start_time)
            transcript.append(phrase)

    return start_times, transcript

def parse_time(time_string):
    """
    parses a time string like HH:MM:SS.ms into a integer number of seconds.
    We don't use datetime or related as this is a simple offset time, not a wall clock time?
    """
    h, m, s = time_string.split(":")
    h = int(h)
    m = int(m)
    s = int(s.split(".")[0])
    return h * 60*60 + m * 60 + s

def get_timestamped_subs():
    start_times, transcript = get_subs()
    punctuated_transcript = punctuator.punctuate(" ".join(transcript))

    start_idxs = [i for i, word in enumerate(punctuated_transcript.split(" ")) if word.strip()[-1] == "."]
    # the indices are the index of the word after the full stop, 
    # so we need to index into list of times for each word (not line)
    start_times = [parse_time(s) for s in start_times]
    start_times_per_word = []
    for start_time, line in zip(start_times, transcript):
        start_times_per_word.extend([start_time]*len(line.split(" ")))

    # test print; should show a line with the timestamp
    output_times, output_lines = [], []
    for start_idx, sentence in zip(start_idxs, punctuated_transcript.split(".")):
        # print(start_times_per_word[start_idx], sentence)
        output_times.append(start_times_per_word[start_idx])
        output_lines.append(sentence)
        
    
    return output_times, [ContentItem(line=l) for l in output_lines]
    
def get_timestamped_imgs():
    times, img_datas = [], []
    for infile in glob.glob("tempfile.*.jpg"):
        timestamp = int(infile.split(".")[1])
        with open(infile, "rb") as f:
            data = base64.b64encode(f.read()).decode("ascii")
        times.append(timestamp)
        img_datas.append(data)
    return times, [ContentItem(image=i) for i in img_datas]

def page_content_for_url(url):
    with temp_working_directory():
        video_metadata = download(url)
        title = video_metadata["title"]
        get_thumbs()
        line_times, lines = get_timestamped_subs()
        img_times, img_datas = get_timestamped_imgs()

    content = list(zip(line_times, lines))
    content.extend((zip(img_times, img_datas)))
    content.sort(key=lambda i: i[0])
    return content, video_metadata
    

if __name__ == "__main__":
    
    url = sys.argv[1]
    content, metadata = page_content_for_url(url)

    with open(f"{metadata['title']}.html", "w") as f:
        for timestamp, item in content:
            f.write(item.render())





