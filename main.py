# coding: utf-8

# First, you need to import the pulsar module
# Make sure you declare Pulsar as dependency in the addon.xml or it won't work
# You can read it at:
# https://github.com/steeve/plugin.video.pulsar/blob/master/resources/site-packages/pulsar/provider.py
import re, xbmc, xbmcaddon
from pulsar import provider
from datetime import datetime,tzinfo,timedelta
import dateutil.parser

app_id = 'script.pulsar.torrentapi'
endpoint = 'http://www.torrentapi.org/pubapi.php'
trakt_apikey = '14b5146e25005b96c03cb8b125d7b5cb452e15e0cfe073685dc92992bbb707f9'

def hasDateBasedEpisodeNumbering(id):
    exceptions = provider.get_setting('showexceptions')
    return int(id) in [int(x.strip()) for x in exceptions.split(',')]

def request(query):
    response = provider.GET(endpoint, params={
        'get_token': 'get_token',
        'app_id': app_id
        })
    query.update({
        'token': response.data,
        'format': 'json_extended',
        'ranked': 0,
        'app_id': app_id
        })
    provider.log.info('Query: %s' % query)
    return provider.GET(endpoint, query)

def formatPayload(results,epString=''):
    try:
        json = results.json()
    except Exception, e:
        provider.log.info('Torrentapi answered: %s' % results.data)
        json = {}
    
    provider.log.info('Torrentapi answered: %s' % json)
    for torrent in json:
        item = {
            'uri': torrent['d'],
            'name': torrent['f'] + ' %s' % epString,
            'seeds': int(torrent['s']),
            'peers': int(torrent['l']),
            'size': int(torrent['t']),
            'resolution': 2,
            'rip_type': 7,
            'audio_codec': 2,
        }
        provider.log.info('Found match: %s' % item)
        yield item

def cleanTitle(title):
    return re.sub(r'\([^)]*\)', '', title).strip()

def getEpisodeAirDate(episode,epStringStandard):
    try:
        response = provider.GET('https://api-v2launch.trakt.tv/shows/%(imdb_id)s/seasons/%(season)s/episodes/%(episode)s?extended=full' % episode, headers={
            'trakt-api-version': 2,
            'trakt-api-key': trakt_apikey,
            'Content-Type': 'application/json',
            })
        
        date = response.json()['first_aired']
        date = dateutil.parser.parse(date) - timedelta(hours=8)
        datestring = date.strftime('%Y.%m.%d')

        provider.log.info('Found match: %s' % datestring)
        return datestring
    except Exception, e:
        return epStringStandard


def search_episode(episode):
    epStringStandard = 'S%(season)02dE%(episode)02d' % episode

    if hasDateBasedEpisodeNumbering(episode['tvdb_id']):
        epString = getEpisodeAirDate(episode,epStringStandard)
    else:
        epString = epStringStandard

    response = request({
        'mode': 'search',
        'search_tvdb': episode['tvdb_id'],
        'search_string': epString
        })

    return formatPayload(response,epString=epStringStandard)
    # return search("%(title)s S%(season)02dE%(episode)02d" % episode)

def search_movie(movie):
    provider.log.info('IMDB: %s' % movie['imdb_id'])
    response = request({
        'mode': 'search',
        'search_imdb': movie['imdb_id']
        })

    return formatPayload(response)

# This registers your module for use
provider.register(None, search_movie, search_episode)
