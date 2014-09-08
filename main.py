#! /usr/bin/python
#Copyright 2014 Michael Archibald

# from BeautifulSoup import SoupStrainer, BeautifulSoup as BS
import re
import urllib2
import sys
from urllib2 import URLError

# URL from which the video streams will be pulled
STREAMS_URL = 'http://cdn.tribtv.com/ake/embed.html?station=wreg&feed=1&auto=true'

# Akamia Doesn't like us pulling the m3u8 file when we don't legitimately need it.
# So we pretend that we are running Android.
USER_AGENT = 'Mozilla/5.0 (Linux; Android 4.4; Nexus 5 Build/BuildID) AppleWebKit/537.36 (\
    KHTML, like Gecko) Version/4.0 Chrome/30.0.0.0 Mobile Safari/537.36'
    
# Matches lines that contain master.m3u8 URIs, station ids, and feed ids.
# Result: 'wgn[5] = "http://wgntribune-lh.akamaihd.net/z/WGNTribune3_1@192102/master.m3u8";'
REGEX_M3U8_LINE = re.compile('\w*\[\d\].*master.m3u8";')

# Matches the URI for the m3u8
# Result: 'http://wgntribune-lh.akamaihd.net/z/WGNTribune3_1@192102/master.m3u8'
REGEX_M3U8_URI = re.compile('http:\/\/.+m3u8')

# Matches stationId
# Result: 'wgn'
REGEX_STATION_ID = re.compile('\w+(?=\[\d\])')

# Matches feedName
# Result: 'WGNTribune3_1'
REGEX_FEED_NAME = re.compile('[^\/][\w\d_]+(?=\@\d+\/)')

# Matches feedId
# Result: '192102'
REGEX_FEED_ID = re.compile('\d+(?=\/.*m3u8)')

# List of stations. Each station is a list consisting of one or more feeds that correspond
# to that particular station.
# Suchthat- {'stationId': 'station_code', 'feeds':[{'feedId': '', 'manifestURI': 'manifest.m3u8_URI'}]}
stations = []

# streamsReq = urllib2.Request(STREAMS_URL, {}, {'User-Agent': USER_AGENT} )
# try: urllib2.urlopen(streamsReq)
# except URLError as e:
#     print e.reason 