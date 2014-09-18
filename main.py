#! /usr/bin/python
#Copyright 2014 Michael Archibald

# from BeautifulSoup import SoupStrainer, BeautifulSoup as BS
import re
import urllib2
from localnewslib import LocalNewsDB

# URL from which the video streams will be pulled
STREAMS_URL = 'http://cdn.tribtv.com/ake/embed.html?station=wreg&feed=1&auto=true'

# Akamia Doesn't like us pulling the m3u8 file when we don't legitimately need it.
# So we pretend that we are running Android.
USER_AGENT = 'Mozilla/5.0 (Linux; Android 4.4; Nexus 5 Build/BuildID) AppleWebKit/537.36 (\
KHTML, like Gecko) Version/4.0 Chrome/30.0.0.0 Mobile Safari/537.36'

# If True, extra output will be displayed
VERBOSE = True
    
# Matches lines that contain master.m3u8 URIs, station ids, and feed ids.
# Result: 'wgn[5] = "http://wgntribune-lh.akamaihd.net/z/WGNTribune3_1@192102/master.m3u8";'
REGEX_STATION_LINE = re.compile('\w*\[\d\].*master.m3u8";')

# Matches the URI for the m3u8
# Result: 'http://wgntribune-lh.akamaihd.net/z/WGNTribune3_1@192102/master.m3u8'
REGEX_M3U8_URL = re.compile('http:\/\/.+m3u8')

# Matches stationName
# Result: 'wgn'
REGEX_STATION_Name = re.compile('\w+(?=\[\d\])')

# Matches feedName
# Result: 'WGNTribune3_1'
REGEX_FEED_NAME = re.compile('[^\/][\w\d_]+(?=\@\d+\/)')

# Matches feedId
# Result: '192102'
REGEX_FEED_ID = re.compile('\d+(?=\/.*m3u8)')

# Matches EXT-X-STREAM-INF line in an m3u8 file.
# Result: '#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=382000,RESOLUTION=320x180,CODECS="avc1.66.30, mp4a.40.2"'
REGEX_INF_LINE = re.compile('.+EXT-X-STREAM-INF.+')

# Matches an http URL
# Result: 'http://wregtribune-lh.akamaihd.net/i/WREGTribunePrimary_1@192110/index_350_av-b.m3u8?sd=10&rebase=on'
REGEX_HTTP_URL = re.compile('http:\/\/[^\s]+')

# Matches the resolution of the video stream.
# Result: '320x180'
REGEX_INF_RESOLUTION = re.compile('[^=]+(?=,CODECS)')

# Matches the bandwidth of the video stream.
# Result: '382000'
REGEX_INF_BANDWIDTH = re.compile('[^=]+(?=,RESOLUTION)')

# Matches the codecs of a video stream.
# Result: 'avc1.66.30, mp4a.40.2'
REGEX_INF_CODECS = re.compile('[^="]+(?=\")')

# List of stations. Each station is a list consisting of one or more feeds that correspond
# to that particular station.
# Suchthat- {'stationName', 'feedId', 'feedName', 'm3u8URL'}
stations = []

#Reference to the sqlite database.
db = None

def getStationLines(streamsURL):
    ''' Finds lines containing all information needed for any given channel from the URL. '''
    try: req = urllib2.urlopen(streamsURL)
    except: return None
    
    html = req.read();
    return REGEX_STATION_LINE.findall(html)

def parseStationLines(m3u8Lines):
    ''' Takes lines pulled using getStationLines() and seperates relevant data '''
    stations = []
    for line in m3u8Lines:
        station = {}
        station['stationName'] = REGEX_STATION_Name.search(line).group().upper()
        station['feedId'] = REGEX_FEED_ID.search(line).group()
        station['feedName'] = REGEX_FEED_NAME.search(line).group()
        station['m3u8URL'] = REGEX_M3U8_URL.search(line).group()
        stations.append(station)
    
    return stations

def getFeedM3U8(m3u8URL):
    m3u8Req = urllib2.Request(m3u8URL, None, {'User-Agent': USER_AGENT})
    try:
        response = urllib2.urlopen(m3u8Req)
        html = response.read()
        response.close()
        return html
    except Exception,e:
        print(e)
        return None
    
    
def parseFeed(stationName, m3u8URL):
    feeds = []
    try:
        m3u8 = getFeedM3U8(m3u8URL)
        infLines = REGEX_INF_LINE.findall(m3u8)
        httpLines = REGEX_HTTP_URL.findall(m3u8)
        
        for x in range(0, len(infLines)):
            feed = {}
            feed['feedId'] = REGEX_FEED_ID.search(httpLines[x]).group()
            feed['stationId'] = db._getStationId(stationName)
            feed['feedName'] = REGEX_FEED_NAME.search(httpLines[x]).group()
            feed['feedUrl'] = httpLines[x]
            feed['resolution'] = REGEX_INF_RESOLUTION.search(infLines[x]).group()
            feed['bandwidth'] = REGEX_INF_BANDWIDTH.search(infLines[x]).group()
            feed['codecs'] = REGEX_INF_CODECS.search(infLines[x]).group()
            feeds.append(feed)
            
        return feeds
    except:
        return None
    
def parseFeedTest(stations):
    matches = (x for x in stations if x['stationName'] == 'WREG')
    match = None
    for x in matches:
        match = x
        
    feeds = parseFeed(match['stationName'], match['m3u8URL'])
    return feeds

def parseFeeds(stations):
    feeds = []
    stationIndex = 1
    for station in stations:
        feed = parseFeed(station['stationName'], station['m3u8URL'])
        if feed != None: 
            feeds += feed
#         else:
#             deleteStation(db, _getStationId(db, station['stationName']))
#             
        if VERBOSE: print 'Parsed station %s of %s' % (stationIndex, len(stations))
        stationIndex += 1
    return feeds

    
def main():
    global db
    db = LocalNewsDB("feeds.sqlite")
    stationLines = getStationLines(STREAMS_URL)
    stations = parseStationLines(stationLines)
    db.insertStations(stations)
    feeds = parseFeeds(stations)
    db.insertFeeds(feeds)
#     insertFeedsTest(db)
    db.deleteUnusedStations()
    db.close()
    
main()