#!/usr/bin/env python
import youtube_dl
import pprint

# test video
video_url="https://www.youtube.com/watch?v=enThZV_Dc9A"

ydl_options = {
    'outtmpl': '%(id)s_480_crf28.%(ext)s',  # use the video id for filename
    'writethumbnail': False,
    'no_warnings': False,
    'continuedl': False,
    'restrictfilenames':True,
    'quiet': False,
    'format': "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]", # Note the format specification is important so we get mp4 and not taller than 720
    'postprocessors': [{
        'key': 'ExecAfterDownload',
        'exec_cmd': 'echo "Compressing to CRF 28" && ffmpeg -i {} -crf 28 {}_tmp.mp4 && mv {}_tmp.mp4 {}',
    }],
}



with youtube_dl.YoutubeDL(ydl_options) as ydl:
    try:
        ydl.add_default_info_extractors()
        ydl.download([video_url])
    except (youtube_dl.utils.DownloadError,youtube_dl.utils.ContentTooShortError,youtube_dl.utils.ExtractorError) as e:
        print('error_occured')
