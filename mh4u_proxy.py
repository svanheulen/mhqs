import argparse
import os
import shutil
import struct
import sys
import tempfile
import time

from twisted.internet import reactor
from twisted.web.server import Site
from twisted.web.static import File
from twisted.python import log

import mhef.n3ds

import proxy


def make_quests(path, cipher, language, quest_path):
    quests_page = ''
    i = 0
    for quest_file in os.listdir(quest_path):
        quest_fullpath = os.path.join(quest_path, quest_file)
        if os.path.isfile(quest_fullpath) and quest_file[-4:] == '.mib':
            quest = open(quest_fullpath, 'rb')
            quest.seek(0xa0)
            info = struct.unpack('8I2H3B33x5H', quest.read(82))
            quest.seek(info[7])
            language_offset = struct.unpack('5I', quest.read(20))
            lang_id = 0
            if language == 'fre':
                lang_id = 1
            elif language == 'spa':
                lang_id = 2
            elif language == 'ger':
                lang_id = 3
            elif language == 'ita':
                lang_id = 4
            quest.seek(language_offset[lang_id])
            text_offset = struct.unpack('7I', quest.read(28))
            quest.seek(text_offset[0])
            title = quest.read(text_offset[1] - text_offset[0]).decode('utf-16').strip('\x00')
            success = quest.read(text_offset[2] - text_offset[1]).decode('utf-16').strip('\x00').split('\n')
            if len(success) < 2:
                success.append(' ')
            success = '|'.join(success)
            failure = quest.read(text_offset[3] - text_offset[2]).decode('utf-16').strip('\x00').split('\n')
            if len(failure) < 2:
                failure.append(' ')
            failure = '|'.join(failure)
            summary = quest.read(text_offset[4] - text_offset[3]).decode('utf-16').strip('\x00').split('\n')
            if len(summary) < 7:
                summary.extend([' '] * (7 - len(summary)))
            summary = '|'.join(summary)
            main_monsters = quest.read(text_offset[5] - text_offset[4]).decode('utf-16').strip('\x00').split('\n')
            if len(main_monsters) < 2:
                main_monsters.append(' ')
            main_monsters = '|'.join(main_monsters)
            client = quest.read(text_offset[6] - text_offset[5]).decode('utf-16').strip('\x00')
            sub_quest = quest.read(language_offset[lang_id] - text_offset[6]).decode('utf-16').strip('\x00')
            quests_page += time.strftime('%Y%m%d') + u'{:02d}|{:05d}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}\n'.format(i, info[8], title, info[0], info[9], 0, info[10], info[5], info[2], info[1], info[13], info[14], info[15], info[16], info[17], info[11], info[12], success, sub_quest, failure, main_monsters, client, summary)
            quest.seek(0)
            open(os.path.join(path, 'm{:05d}.mib'.format(info[8])), 'wb').write(cipher.encrypt(quest.read()))
            quest.close()
            i += 1
            print '[+] Load Quest File : ' + title
    
        
    return cipher.encrypt(b'\xef\xbb\xbf' + quests_page.encode('utf-8'))


def make_root(root, region, language, event, challenge):
    cipher = mhef.n3ds.DLCCipher(mhef.n3ds.MH4G_JP)
    path = os.path.join(root, '3ds/mh4g_nihon')
    if args.region == 'USA':
        cipher = mhef.n3ds.DLCCipher(mhef.n3ds.MH4G_NA)
        path = os.path.join(root, '3ds/mh4g_us_')
    elif args.region == 'EUR':
        cipher = mhef.n3ds.DLCCipher(mhef.n3ds.MH4G_EU)
        path = os.path.join(root, '3ds/mh4g_eu_')
    elif args.region == 'KOR':
        cipher = mhef.n3ds.DLCCipher(mhef.n3ds.MH4G_KR)
        path = os.path.join(root, '3ds/mh4g_kr_')
    os.makedirs(path)
    default_info = cipher.encrypt(time.strftime('%Y%m%d00|1|0| |Monster Hunter Quest Server\n%Y%m%d00|2|0| |Version BETA 2             \n%Y%m%d00|3|0| |github.com/svanheulen/mhqs '))
    open(os.path.join(path, 'DLC_Info_Notice_{}.txt'.format(language)), 'wb').write(default_info)
    open(os.path.join(path, 'DLC_Info_Otomo_{}.txt'.format(language)), 'wb').write(default_info)
    open(os.path.join(path, 'DLC_Info_Quest_{}.txt'.format(language)), 'wb').write(default_info)
    open(os.path.join(path, 'DLC_Info_Special_{}.txt'.format(language)), 'wb').write(default_info)
    open(os.path.join(path, 'DLC_EShopInfo.txt'), 'wb').write(cipher.encrypt('0|0|0|0|0|0|0'))
    open(os.path.join(path, 'DLC_ShopAmulInfo_{}.txt'.format(language)), 'wb').write(cipher.encrypt('0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0'))
    open(os.path.join(path, 'DLC_ShopEquiInfo_{}.txt'.format(language)), 'wb').write(cipher.encrypt('0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0'))
    open(os.path.join(path, 'DLC_ShopItemInfo_{}.txt'.format(language)), 'wb').write(cipher.encrypt('0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0'))
    open(os.path.join(path, 'DLC_Info_List_{}.txt'.format(language)), 'wb').write(cipher.encrypt(time.strftime('%Y%m%d00|0|Content Preview')))
    open(os.path.join(path, time.strftime('DLC_Info_%Y%m%d00_{}.txt'.format(language))), 'wb').write(cipher.encrypt(time.strftime('%y/%m/%d|0|Information:|Monster Hunter Quest Server|This software is licensed|under GPLv3. Please visit|github.com/svanheulen/mhqs|for more information.| | | | | ')))
    default_quests = cipher.encrypt('0|0| |0|0|0|0|0|0|0|98|98|98|98|98|0|0| | | | | | | | | | | | | | | ')
    if event:
        open(os.path.join(path, 'DLC_EventQuestInfo_{}.txt'.format(language)), 'wb').write(make_quests(path, cipher, language, event))
    else:
        open(os.path.join(path, 'DLC_EventQuestInfo_{}.txt'.format(language)), 'wb').write(default_quests)
    if challenge:
        open(os.path.join(path, 'DLC_ChallengeQuestInfo_{}.txt'.format(language)), 'wb').write(make_quests(path, cipher, language, challenge))
    else:
        open(os.path.join(path, 'DLC_ChallengeQuestInfo_{}.txt'.format(language)), 'wb').write(default_quests)
    open(os.path.join(path, 'DLC_EpisodeQuestInfo_{}.txt'.format(language)), 'wb').write(default_quests)
    open(os.path.join(path, 'DLC_EpisodeQuestInfo2_{}.txt'.format(language)), 'wb').write(cipher.encrypt(' | | | | |0|0|0'))
    open(os.path.join(path, 'DLC_OtomoInfo_{}.txt'.format(language)), 'wb').write(cipher.encrypt('0|| | |0|0|0|0|0|0|0|0|0|0|0| '))
    open(os.path.join(path, 'DLC_Special_{}.txt'.format(language)), 'wb').write(cipher.encrypt('0||0| '))


parser = argparse.ArgumentParser(description='Runs a proxy for serving custom MH4U DLC quests.')
parser.add_argument('region', choices=('JPN', 'USA', 'EUR', 'KOR'), help='your game region')
parser.add_argument('language', choices=('jpn', 'eng', 'fre', 'spa', 'ger', 'ita', 'kor'), help='your game language')
parser.add_argument('--event', help='the decrypted event quest files to serve')
parser.add_argument('--challenge', help='the decrypted challenge quest files to serve')
args = parser.parse_args()

root = tempfile.mkdtemp()
try:
    make_root(root, args.region, args.language, args.event, args.challenge)
    log.startLogging(sys.stderr)
    reactor.listenTCP(8080, proxy.TunnelProxyFactory())
    reactor.listenTCP(8081, Site(File(root)))
    reactor.run()
finally:
    shutil.rmtree(root)

