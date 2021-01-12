# YouTube to atom feed server

This very very v0.1 script scrapes youtube videos (with youtube-dl), extracts periodic screenshots (hat-tip to https://mostlymaths.net/2021/01/202102-readings.html/ for the entire concept), uses some off-the-shelf ML models to repunctuate the subtitles, and severs it all to you as a feed to look at in your favourite feedreader.

ToDo;
1) Add playlist&channel subscriptions via api endoint
2) serve summaries via playlist&channel subendpoints
3) scrape for new videos in the background
4) deploy to heroku
5) profit??
6) improve the feed formatting (add description, links, etc, better styles)
inf) tests

# getting started

this needs the following:

`python3 -m pip install -U youtube_dl webvtt-py punctuator feedgen flask`

and get the punctuator model from the google drive link with `gdown https://drive.google.com/uc?id=0B7BsN5f2F1fZd1Q0aXlrUDhDbnM`, saved to the same directory as this repository. 
