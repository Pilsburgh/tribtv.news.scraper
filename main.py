#! /usr/bin/python
#Copyright 2014 Michael Archibald

# from BeautifulSoup import SoupStrainer, BeautifulSoup as BS
import re
import urllib2
import sqlite3

# URL from which the video streams will be pulled
STREAMS_URL = 'http://cdn.tribtv.com/ake/embed.html?station=wreg&feed=1&auto=true'

# Akamia Doesn't like us pulling the m3u8 file when we don't legitimately need it.
# So we pretend that we are running Android.
USER_AGENT = 'Mozilla/5.0 (Linux; Android 4.4; Nexus 5 Build/BuildID) AppleWebKit/537.36 (\
KHTML, like Gecko) Version/4.0 Chrome/30.0.0.0 Mobile Safari/537.36'
    
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
# stations = []

# streamsReq = urllib2.Request(STREAMS_URL, {}, {'User-Agent': USER_AGENT} )
# try: urllib2.urlopen(streamsReq)
# except URLError as e:
#     print e.reason 

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

def connectDB(dbFilename):
    try:
        conn = sqlite3.connect(dbFilename)  # @UndefinedVariable
        conn.row_factory = sqlite3.Row  # @UndefinedVariable
        return conn
    except:
        return None

def getFeedM3U8(m3u8URL):
    m3u8Req = urllib2.Request(m3u8URL, None, {'User-Agent': USER_AGENT})
    try:
        response = urllib2.urlopen(m3u8Req)
        html = response.read()
        response.close()
        return html
    except:
        return None
    
def insertStations(stations):
    for station in stations:
        success = insertStation(station['stationName'])
#         print station['stationName'] + ' successful? ' + str(success)
    
def insertStation(stationName, stationState='', stationCity=''):
    ''' taking care of this as to insure a pattern of best practices '''
    if db:
        try:
            db.execute("insert into stations (STATION_NAME, STATION_STATE, STATION_CITY) values (?, ?, ?)", (stationName, stationState, stationCity))
            db.commit()
            return True
        except Exception,e:
            db.rollback()
            print str(e)
            return False
    else:
        return False
    
def insertFeed(feedId, stationId, feedName, feedUrl, resolution='', bandwidth='', codecs = '', requiresProxy=False):
    ''' kargs options are, 'resolution', 'bandwidth', 'codecs', 'requiresProxy' '''
    if db:
        try:
            db.execute("insert into feeds (FEED_ID, Station_ID, FEED_NAME, FEED_URL, FEED_RESOLUTION\
            , FEED_BANDWIDTH, FEED_CODECS, FEED_REQUIRES_PROXY) values (?, ?, ?, ?, ?, ?, ?\
            , ?)", (feedId, stationId, feedName, feedUrl, int(bandwidth), codecs, int(requiresProxy)))
            
            db.commit()
            return True
        except Exception,e:
            db.rollback()
            print str(e)
            return False
    else:
        return False

def getStationId(stationName):
    ''' Returns the primary key for a given station name. '''
    if db:
        return db.execute('SELECT STATION_ID FROM stations WHERE STATION_NAME=?', [stationName]).fetchone()[0]
    else:
        return None


db = connectDB('feeds.sqlite')
stationLines = getStationLines(STREAMS_URL)
stations = parseStationLines(stationLines)
insertStations(stations)
print getStationId(stations[3]['stationName'])
db.close()