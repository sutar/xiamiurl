#coding: utf-8
import os
import re
import urllib2
import sys

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TRCK, TALB, USLT, error
from xiami_decode import xiami_decode
from bs4 import BeautifulSoup

reload(sys) 
sys.setdefaultencoding('utf8')

# ID3 info:
# APIC: picture
# TIT2: title
# TPE1: artist
# TRCK: track number
# TALB: album
# USLT: lyric

DIR_PREFIX = ''

def parse_alblum(alblumid):
    url = 'http://www.xiami.com/song/playlist/id/%s/type/1' % albumid
    content = urllib2.urlopen(url, timeout=30).read()
    xml = BeautifulSoup(content, features='xml')
    result = []
    songs = xml.playlist.trackList.find_all('track')
    pic = songs[0].pic.string.replace('_1', '_2')
    directory = '%s - [%s].(MP3)' % (songs[0].artist.string, songs[0].album_name.string)
    directory = directory.replace(' ','.')
    directory = directory.replace('/','')
    for x in songs:
        lyric = urllib2.urlopen(x.lyric.string, timeout=30).read()
        lyric = re.sub('(\[.*?\][\n]*)+', '', unicode(lyric))
        print 'parsing... ', x.title.string
        result.append(dict(
            url=xiami_decode(x.location.string),
            song=x.title.string,
            album=x.album_name.string,
            artist=x.artist.string,
            lyric=lyric
            )
        )
    return result, pic, directory

def wget(referer, down_url, filename):
    os.system('wget -c --output-document="%s" --referer="%s" "%s"' % (filename , referer, down_url))

def get_pic(directory, down_url):
    filename = unicode(directory + '/cover.jpg')
    print filename
    os.system('wget -c --output-document="%s" "%s"' % (filename, down_url))

def download_songs(result, album, directory):
    for idx, item in enumerate(result):
        track_num = idx + 1
        # filename format: 1. France Gall - Poupee de Son - Poupee De Cire Poupee De Son.mp3
        filename = '%s/%d. %s - %s - %s.mp3' % (directory, track_num, item['artist'], item['album'], item['song'])
        wget(album, item['url'], filename)
        id3_cook(directory, filename, item, track_num)

def id3_cook(directory, filename, item, track_num):
    pic_file = directory + '/cover.jpg'
    audio = MP3(filename, ID3=ID3)
    try:
        audio.add_tags()
    except:
        pass
    audio.tags.add(APIC(
        encoding=3,
        mime='image/jpeg',
        type=3,
        desc=u'Cover Picture',
        data=open(pic_file).read()
    ))
    audio.tags.add(TIT2(encoding=3, text=item['song'].decode('utf-8')))
    audio.tags.add(TALB(encoding=3, text=item['album'].decode('utf-8')))
    audio.tags.add(TPE1(encoding=3, text=item['artist'].decode('utf-8')))
    audio.tags.add(TRCK(encoding=3, text=str(track_num).decode('utf-8')))
    audio.tags.add(USLT(encoding=3, lang=u'eng', desc=u'desc', text=item['lyric'].decode('utf-8')))
    audio.save()

if __name__ == '__main__':
    # album = raw_input('Enter xiami album url: ')
    # album = 'http://www.xiami.com/album/460478'
    album = 'http://www.xiami.com/album/340249'
    albumid = album.split('/')[-1]
    result, pic, directory = parse_alblum(albumid)
    directory = DIR_PREFIX + directory
    if not os.path.exists(directory):
        os.mkdir(directory)
    get_pic(directory, pic)
    download_songs(result, album, directory)
