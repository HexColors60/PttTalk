import json
import sys
import time
import traceback
import random

import log
from PyPtt import PTT

version = '0.1.0'


def get_password(password_file):
    try:
        with open(password_file) as AccountFile:
            account = json.load(AccountFile)
            ptt_id = account['ID']
            password = account['Password']
    except FileNotFoundError:
        print(f'Please note PTT ID and Password in {password_file}')
        print('{"ID":"YourID", "Password":"YourPassword"}')
        sys.exit()

    return ptt_id, password


def remove_from_pool(ptt_id):
    log.show_value(
        'remove_from_pool',
        log.level.INFO,
        'remove',
        ptt_id
    )
    global mail_pool
    global line_pool
    global waterball_pool

    if ptt_id in mail_pool:
        mail_pool.remove(ptt_id)
    if ptt_id in line_pool:
        line_pool.remove(ptt_id)
    if ptt_id in waterball_pool:
        waterball_pool.remove(ptt_id)


def pairing(ptt_bot, pool, msg_type):

    log.show_value(
        'pairing',
        log.level.INFO,
        '配對',
        msg_type
    )

    random.shuffle(pool)
    while len(pool) >= 2:
        target_0 = pool[0]
        target_1 = pool[1]
        remove_from_pool(target_0)
        remove_from_pool(target_1)

        ptt_bot.mail(
            target_0,
            'Ptt Talk 配對結果',
            f'成功配對 {target_1} 請交換{msg_type}',
            0)

        ptt_bot.mail(
            target_1,
            'Ptt Talk 配對結果',
            f'成功配對 {target_0} 請交換{msg_type}',
            0)

if __name__ == '__main__':

    log.show_value(
        'main',
        log.level.INFO,
        'Ptt Talk',
        version
    )

    ptt_id, password = get_password('account.txt')
    try:
        ptt_bot = PTT.API(
            # log_level=PTT.log.level.TRACE,
            # log_level=PTT.log.level.DEBUG,
            # host=PTT.data_type.host_type.PTT2

            # for 本機測試
            # connect_mode=PTT.connect_core.connect_mode.TELNET,
            # host=PTT.data_type.host_type.LOCALhost,
            # port=8888,
        )
        try:
            ptt_bot.login(
                ptt_id,
                password,
                # kick_other_login=True
            )
        except PTT.exceptions.LoginError:
            ptt_bot.log('登入失敗')
            sys.exit()
        except PTT.exceptions.WrongIDorPassword:
            ptt_bot.log('帳號密碼錯誤')
            sys.exit()
        except PTT.exceptions.LoginTooOften:
            ptt_bot.log('請稍等一下再登入')
            sys.exit()

        line_pool = []
        waterball_pool = []
        mail_pool = []

        max_pool_count = 2

        while True:
            newest_index = ptt_bot.get_newest_index(PTT.data_type.index_type.MAIL)
            ptt_bot.log(f'最新信箱編號 {newest_index}')

            for index in range(1, newest_index + 1):
                log.show(
                    'main',
                    log.level.INFO,
                    '開始讀信')
                mail_info = ptt_bot.get_mail(newest_index)

                author = mail_info.author
                if '(' in author:
                    author = author[:author.find('(')].strip()
                else:
                    author = author.strip()

                title = mail_info.title
                title = title.strip()

                log.show(
                    'main',
                    log.level.INFO,
                    '收到新信!!')

                log.show_value(
                    'main',
                    log.level.INFO,
                    'author',
                    author)
                log.show_value(
                    'main',
                    log.level.INFO,
                    'title',
                    title)

                ptt_bot.del_mail(index)

                response = ''

                if '站內信' in title:
                    if author not in mail_pool:
                        mail_pool.append(author)
                        response += '站內信'

                if '賴' in title or 'line' in title.lower():
                    if author not in line_pool:
                        line_pool.append(author)
                        if len(response) == 0:
                            response += '賴'
                        else:
                            response += ', 賴'

                if '水球' in title:
                    if author not in waterball_pool:
                        waterball_pool.append(author)
                        if len(response) == 0:
                            response += '水球'
                        else:
                            response += ', 水球'

                if len(response) == 0:
                    continue

                ptt_bot.mail(
                    author,
                    'Ptt Talk 註冊結果',
                    f'已經成功註冊 {response} 通信方式',
                    0
                )

            if len(line_pool) >= max_pool_count:
                pairing(ptt_bot, line_pool, '賴')

            if len(mail_pool) >= max_pool_count:
                pairing(ptt_bot, mail_pool, '站內信')

            if len(waterball_pool) >= max_pool_count:
                pairing(ptt_bot, waterball_pool, '水球')

            print('完成，休息')
            time.sleep(5)

    except Exception as e:
        traceback.print_tb(e.__traceback__)
        print(e)
    except KeyboardInterrupt:
        pass

    ptt_bot.logout()
