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


def make_root(game, language, quest_files):
    dc = mhef.n3ds.DLCCipher(game)

    root = tempfile.mkdtemp()
    full_path = os.path.join(root, '3ds/mh4g_us_')
    if game == mhef.n3ds.MH4G_EU:
        full_path = os.path.join(root, '3ds/mh4g_eu_')
    elif game == mhef.n3ds.MH4G_JP:
        full_path = os.path.join(root, '3ds/mh4g_nihon')
    os.makedirs(full_path)

    default_info = dc.encrypt(time.strftime('%Y%m%d00|1|0| |Monster Hunter Quest Server\n%Y%m%d00|2|0| |Version BETA               \n%Y%m%d00|3|0| |github.com/svanheulen/mhqs '))
    open(os.path.join(full_path, 'DLC_Info_Notice_{}.txt'.format(language)), 'wb').write(default_info)
    open(os.path.join(full_path, 'DLC_Info_Otomo_{}.txt'.format(language)), 'wb').write(default_info)
    open(os.path.join(full_path, 'DLC_Info_Quest_{}.txt'.format(language)), 'wb').write(default_info)
    open(os.path.join(full_path, 'DLC_Info_Special_{}.txt'.format(language)), 'wb').write(default_info)
    open(os.path.join(full_path, 'DLC_EShopInfo.txt'), 'wb').write(dc.encrypt('0|0|0|0|0|0|0'))
    open(os.path.join(full_path, 'DLC_ShopAmulInfo_{}.txt'.format(language)), 'wb').write(dc.encrypt('0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0'))
    open(os.path.join(full_path, 'DLC_ShopEquiInfo_{}.txt'.format(language)), 'wb').write(dc.encrypt('0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0'))

    open(os.path.join(full_path, 'DLC_Info_List_{}.txt'.format(language)), 'wb').write(dc.encrypt(time.strftime('%Y%m%d00|0|Content Preview')))
    open(os.path.join(full_path, time.strftime('DLC_Info_%Y%m%d00_{}.txt'.format(language))), 'wb').write(dc.encrypt(time.strftime('%y/%m/%d|0|Information:|Monster Hunter Quest Server|This software is licensed|under GPLv3. Please visit|github.com/svanheulen/mhqs|for more information.| | | | | ')))

    event_quests = ''
    for i in range(len(quest_files)):
        quest = open(quest_files[i], 'rb')
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
        event_quests += time.strftime('%Y%m%d') + u'{:02d}|{:05d}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}|{}\n'.format(i, info[8], title, info[0], info[9], 0, info[10], info[5], info[2], info[1], info[13], info[14], info[15], info[16], info[17], info[11], info[12], success, sub_quest, failure, main_monsters, client, summary)
        quest.seek(0)
        open(os.path.join(full_path, 'm{:05d}.mib'.format(info[8])), 'wb').write(dc.encrypt(quest.read()))
        quest.close()
    open(os.path.join(full_path, 'DLC_EventQuestInfo_{}.txt'.format(language)), 'wb').write(dc.encrypt(b'\xef\xbb\xbf' + event_quests.encode('utf-8')))

    default_quests = dc.encrypt('0|0| |0|0|0|0|0|0|0|98|98|98|98|98|0|0| | | | | | | | | | | | | | | ')
    open(os.path.join(full_path, 'DLC_ChallengeQuestInfo_{}.txt'.format(language)), 'wb').write(default_quests)
    open(os.path.join(full_path, 'DLC_EpisodeQuestInfo_{}.txt'.format(language)), 'wb').write(default_quests)

    open(os.path.join(full_path, 'DLC_OtomoInfo_{}.txt'.format(language)), 'wb').write(dc.encrypt('0|| | |0|0|0|0|0|0|0|0|0|0|0| '))

    open(os.path.join(full_path, 'DLC_Special_{}.txt'.format(language)), 'wb').write(dc.encrypt('0||0| '))

    return root

parser = argparse.ArgumentParser(description='Runs a proxy for serving custom MH4U DLC quests.')
parser.add_argument('region', choices=('JPN', 'USA', 'EUR'), help='your game region')
parser.add_argument('language', choices=('jpn', 'eng', 'fre', 'spa', 'ger', 'ita'), help='your game language')
parser.add_argument('questfile', nargs='+', help='the decrypted quest files to serve')
args = parser.parse_args()

game = mhef.n3ds.MH4G_JP
if args.region == 'USA':
    game = mhef.n3ds.MH4G_NA
elif args.region == 'EUR':
    game = mhef.n3ds.MH4G_EU

root = make_root(game, args.language, args.questfile)

log.startLogging(sys.stderr)
reactor.listenTCP(8080, proxy.TunnelProxyFactory())
reactor.listenTCP(8081, Site(File(root)))
reactor.run()

shutil.rmtree(root)

