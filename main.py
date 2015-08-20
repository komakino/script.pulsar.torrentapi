# coding: utf-8

# First, you need to import the pulsar module
# Make sure you declare Pulsar as dependency in the addon.xml or it won't work
# You can read it at:
# https://github.com/steeve/plugin.video.pulsar/blob/master/resources/site-packages/pulsar/provider.py
import re, xbmc, xbmcaddon
from pulsar import provider

app_id = 'script.pulsar.torrentapi'
endpoint = 'http://www.torrentapi.org/pubapi.php'

thetvdb_api_key = '6751159EC176672B'

dateBasedEpisodeNumbering = [
    194751, # Conan (2010)
    270261, # The Tonight Show Starring Jimmy Fallon
    292421, # The Late Late Show with James Corden
    71998,  # Jimmy Kimmel Live
]

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

def getEpisodeAirDate(episode):

    if episode['tvdb_id'] == 194751:
        episode['season'] = int(episode['season']) - 2010

    # summary = globals.traktapi.getEpisodeSummary(episode['imdb_id'], episode['season'], episode['episode'])

    provider.log.info('Pre date query %s' % globals.traktapi)
    response = provider.GET('http://services.tvrage.com/feeds/episodeinfo.php', params={
            'exact': 1,
            'show': cleanTitle(episode['title']),
            'ep': '%(season)sx%(episode)s' % episode
            })
    try:
        xml = response.xml()
        return xml.find('./episode/airdate').text.replace('-','.')
    except Exception, e:
        provider.log.warning('Failed to parse XML %s' % episode['season'])
        return None

def search_episode(episode):
    epStringStandard = 'S%(season)02dE%(episode)02d' % episode

    if episode['tvdb_id'] in dateBasedEpisodeNumbering:
        epString = getEpisodeAirDate(episode)
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
