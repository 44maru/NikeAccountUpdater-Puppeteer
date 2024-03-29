import base64
import logging.config
import os
import queue
import random
import csv
from datetime import datetime as dt
from time import sleep
import asyncio

import requests
import pyperclip
import fire

from pyppeteer import launch
from pyppeteer.errors import TimeoutError

"""
pyInstallerでbuildしてexeを実行すると以下のようなエラーがでる

  File "site-packages\pyppeteer\__init__.py", line 43, in <module>
NameError: name '__version__' is not defined

https://github.com/pyppeteer/pyppeteer/issues/213#issuecomment-768850251
上記を参照して、pyppeteerの__init__.pyのversion設定処理を修正する必要がある
"""


CHROME_PROXY_EXTENTION_DIR = "proxy_mng"

ACCOUNT_LOGIN_URL = "https://www.nike.com/jp/login"
ACCOUNT_SETTING_URL = "https://www.nike.com/jp/member/settings"
ACCOUNT_PROFILE_URL = "https://www.nike.com/jp/member/profile"
NIKE_ORDERS_URL = "https://www.nike.com/jp/orders"
NIKE_EVENT_URL = "https://web.nike.com/events/my_events/index.html#/discover"
NIKE_INBOX_URL = "https://www.nike.com/member/inbox/"

AUTHENTICATION_SERVER = "http://yamatoblackbox.com/autoremoteexecuter/auth.php"

MERUADO_POI_POI_URL = "https://m.kuku.lu/index.php"

LOG_CONF = "./logging.conf"
INPUT_CSV = "./input.csv"
INPUT_LOGIN_PATROL_CSV = "./input_login_patrol.csv"
INPUT_PHONE_NUMBER_CHECK_CSV = "./input_phone_number_check.csv"
INPUT_LOGIN_WITH_CHROME_PROFILE_CSV = "./input_login_with_chrome_profile.csv"
CONFIG_TXT = "./config.txt"
PROXY_TXT = "./proxy.txt"
ADDRESS_LIST_TXT = "./address_list.txt"

KEY_THREAD_NUM = "THREAD_NUM"
KEY_HEADLESS = "HEADLESS"
KEY_LOGIN_TYPING_INTERVAL_MIN = "LOGIN_TYPING_INTERVAL_MIN"
KEY_LOGIN_TYPING_INTERVAL_MAX = "LOGIN_TYPING_INTERVAL_MAX"
KEY_GET_NEW_ADDRESS_FROM_POI_POI = "GET_NEW_ADDRESS_FROM_MERUADO_POI_POI"
KEY_MERUADO_POI_POI_USER = "MERUADO_POI_POI_USER"
KEY_MERUADO_POI_POI_PASS = "MERUADO_POI_POI_PASS"
KEY_SERIAL_KEY = "SERIAL_KEY"
KEY_WINDOWS_PRODUCT_KEY = "WINDOWS_PRODUCT_KEY"
KEY_CHROME_USER_DATA_DIR = "CHROME_USER_DATA_DIR"
CONFIG_DICT = {}
PROXY_LIST = []
ADDRESS_LIST = []


HTML_LOGIN_PATH = "/html/body/div[6]/nav/div[1]/ul[2]/li[2]/button/span"
HTML_LOGIN_EMAIL_PATH = """//*[@id='nike-unite-loginForm']/div[2]/input"""
HTML_LOGIN_PASS_PATH = """//*[@id="nike-unite-loginForm"]/div[3]/input"""
HTML_KEEP_LOING_CHKBOX_PATH = """//*[@id="keepMeLoggedIn"]/label"""
HTML_LOGIN_BUTTON_PATH = """//*[@id="nike-unite-loginForm"]/div[6]/input"""
HTML_LOGIN_ERR_MSG_PATH = """//*[@id="nike-unite-loginForm"]/div[1]/ul/li"""
HTML_LOGIN_BLOCK_MSG_PATH = """//*[@id="nike-unite-error-view"]/div/ul/li"""
HTML_ACCOUNT_SETTING_PATH = """/html/body/div[7]/nav/div[1]/ul[2]/li[1]/a/span[2]"""
HTML_ACCOUNT_SETTING_EMAIL_PATH = """//*[@id="email"]"""
HTML_ACCOUNT_SETTING_PHONE_NUMBER_LABEL_PATH = """//*[@id="mobile-container"]/div/div/form/div[2]/div[4]/div/h3"""
HTML_ACCOUNT_SETTING_PHONE_NUMBER_PATH = """//*[@id="mobile-container"]/div/div/form/div[2]/div[4]/div/div/div/div[1]/span/span"""
HTML_ACCOUNT_SETTING_COUNTRY_OPTION_TEXT_PATH = """//*[@id="country"]/option[contains(text(), "{}")]"""
HTML_ACCOUNT_SETTING_COUNTRY_ID = "country"
HTML_ACCOUNT_SETTING_STATE_OPTION_TEXT_PATH = """//*[@id="state"]/option[contains(text(), "{}")]"""
HTML_ACCOUNT_SETTING_STATE_ID = "state"
HTML_ACCOUNT_SETTING_ADDRESS_PATH = """//*[@id="city"]"""
HTML_ACCOUNT_SETTING_ZIPCODE_PATH = """//*[@id="code"]"""
HTML_ACCOUNT_SETTING_SAVE_BUTTON_PATH = """//*[@id="mobile-container"]/div/div/form/div[2]/div[7]/div[2]/div[2]/button"""
HTML_ACCOUNT_SETTING_SAVE_ERROR_PATH = """//*[@id="mobile-container"]/div/div/form/div[2]/div[1]/div/div[2]/img"""

XPATH_ADD_MAIL_ADDRESS = """//*[@id="link_addMailAddrByAuto"]"""
XPATH_NEW_ADDRESS_VIEW_DATA = """//*[@id="area-newaddress-view-data"]/div/div[1]/u"""
XPATH_CLOSE_NEW_ADDRESS_VIEW = """//*[@id="link_newaddr_close"]"""
XPATH_CURRENT_ACCOUNT = """//*[@id="link_logindata"]"""
XPATH_CURRENT_ACOUNT_USER = """//*[@id="area_numberview"]"""
XPATH_CURRENT_ACOUNT_PASS = """//*[@id="area_passwordview_copy"]"""
XPATH_OTHER_ACOUNT = """//*[@id="link_loginform"]"""
XPATH_OTHER_ACOUNT_USER = """//*[@id="user_number"]"""
XPATH_OTHER_ACOUNT_PASS = """//*[@id="user_password"]"""

SUCCESS = "成功"
ERROR = "失敗"
OUT_DIR = "result"

JAPAN = "日本"

COUNT_OF_RANDOM_WINDOW_SIZE_CHANGING = 5


class LoginError(Exception):
    pass
    # def __init__(self):
    #    super(LoginError, self).__init__()


class AccountInfo():
    def __init__(self, email, password, newEmail="", chromeProfile=""):
        self.email = email
        self.newEmail = newEmail
        self.password = password
        self.chromeProfile = chromeProfile
        self.phoneNumber = None


class AddressInfo():
    def __init__(self, state, address, zipcode):
        self.state = state
        self.address = address
        self.zipcode = zipcode


async def changeWindowSize(page, connection, windowId, width, height):
    await page.setViewport({'width': width, 'height': height})
    await connection.send('Browser.setWindowBounds', {
        'bounds': {
            'height': height,
            'width': width
        },
        'windowId': windowId
    })


async def changeWindowSizeMax(page, connection, windowId, maxWidth, maxHeight):
    await page.setViewport({'width': maxWidth, 'height': maxHeight})
    await connection.send('Browser.setWindowBounds', {
        'bounds': {
            'windowState': 'maximized'
        },
        'windowId': windowId
    })


async def changeRandomMinusWindowSize(page, connection, targetId):
    windowInfo = (await connection.send('Browser.getWindowForTarget', {'targetId': targetId}))
    windowId = windowInfo['windowId']
    maxWidth = windowInfo['bounds']['width']
    maxHeight = windowInfo['bounds']['height']
    currentWidth = maxWidth
    currentHeight = maxHeight
    for i in range(COUNT_OF_RANDOM_WINDOW_SIZE_CHANGING):
        if random.randint(0, 1) == 0:
            currentWidth = max(currentWidth-random.randint(2, 20), 10)
        if random.randint(0, 1) == 0:
            currentHeight = max(currentHeight-random.randint(2, 20), 10)
        await changeWindowSize(page, connection, windowId, currentWidth, currentHeight)


async def changeRandomPlusWindowSize(page, connection, targetId, maxWidth, maxHeight):
    windowInfo = (await connection.send('Browser.getWindowForTarget', {'targetId': targetId}))
    windowId = windowInfo['windowId']
    currentWidth = windowInfo['bounds']['width']
    currentHeight = windowInfo['bounds']['height']
    for i in range(COUNT_OF_RANDOM_WINDOW_SIZE_CHANGING):
        if random.randint(0, 1) == 0:
            currentWidth = min(
                currentWidth+random.randint(2, 10), maxWidth)
        if random.randint(0, 1) == 0:
            currentHeight = min(
                currentHeight+random.randint(2, 10), maxHeight)
        await changeWindowSize(page, connection, windowId, currentWidth, currentHeight)


async def changeRandomWindowSize(page, connection, targetId, maxWidth, maxHeight):
    if random.randint(0, 1) == 0:
        await changeRandomMinusWindowSize(page, connection, targetId)
    else:
        await changeRandomPlusWindowSize(page, connection, targetId, maxWidth, maxHeight)


async def callOperation(operation, accountInfo, semaphore):
    global output_q

    with await semaphore:
        browser = None
        page = None
        try:
            args = [
                '--start-maximized',
                "--load-extension={}/{}".format(
                    os.getcwd(), CHROME_PROXY_EXTENTION_DIR)
            ]
            if accountInfo.chromeProfile != '':
                args.append(
                    "--user-data-dir={}".format(CONFIG_DICT[KEY_CHROME_USER_DATA_DIR]))
                args.append(
                    "--profile-directory={}".format(accountInfo.chromeProfile))

            log.debug("chrome launch with args {}".format(args))

            browser = await launch(headless=CONFIG_DICT[KEY_HEADLESS],
                                   executablePath="C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                                   defaultViewport=None,
                                   ignoreDefaultArgs=[
                                       "--disable-extensions", "--enable-automation"],
                                   args=args
                                   )

            log.debug("get pages from browser")
            pages = await browser.pages()
            page = pages[len(pages)-1]
            # page = await browser.newPage()
            log.debug("Start operation for account %s", accountInfo.email)
            sleep(random.randint(500, 2000) / 1000.0)
            if 0 < len(PROXY_LIST):
                b64_json = base64.b64encode(("""{"url":"%s", "proxy":"%s"}""" % (
                    ACCOUNT_LOGIN_URL, random.choice(PROXY_LIST))).encode("utf-8"))
                await page.goto("https://configure.bnb/" + b64_json.decode("utf-8"))
            else:
                await page.goto(ACCOUNT_LOGIN_URL)

            await type_login_info(page, browser._connection, accountInfo.email, accountInfo.password)

            sleep(random.randint(500, 4000) / 1000)
            log.debug("Click login button %s", accountInfo.email)

            # loginボタンクリック後、ページの遷移が完了するのを待つ
            loadPromise = page.waitForNavigation({"timeout": 15000})
            await click(page, HTML_LOGIN_BUTTON_PATH)
            await loadPromise

            log.debug("sleep 3 - 5 sec")
            sleep(random.randint(3000, 5000) / 1000.0)
            await operation(page, accountInfo)

            log.info("Succeeded to operation for %s", accountInfo.email)
            output_q.put(
                [accountInfo, SUCCESS, ""])

        except LoginError as e:
            log.info("Failed to operation for %s", item[0])
            output_q.put([accountInfo, ERROR, e])

        except Exception as e:
            log.info("Failed to operation for %s", accountInfo.email)
            log.exception("Catched Exception : %s.", e)
            output_q.put(
                [accountInfo, ERROR, "Unknown error. Send log file to developer."])
            await page.screenshot(path="{}/{}.err.png".format(OUT_DIR, accountInfo.email), fullPage=True)

        finally:
            if page is not None:
                await page.close()

            if browser is not None:
                try:
                    await browser.close()
                except OSError as e:
                    log.exception(
                        "Failed to close browse due to OSError. Continue next operation forcibly. Account: %s. Error description: %s", accountInfo.email, e)


async def changeWindowSize(page, connection, windowId, width, height):
    await page.setViewport({'width': width, 'height': height})
    await connection.send('Browser.setWindowBounds', {
        'bounds': {
            'height': height,
            'width': width
        },
        'windowId': windowId
    })


async def paste_txt(page, xpath):
    await page.waitForXPath(xpath)
    elem = await page.xpath(xpath)

    await elem[0].click()
    await page.keyboard.down('Control')
    await page.keyboard.press('KeyV')
    await page.keyboard.up('Control')


async def type_txt_with_changing_window_size(page, connection, targetId, maxWidth, maxHeight, xpath, txt):
    await page.waitForXPath(xpath)
    elem = await page.xpath(xpath)

    await elem[0].click(clickCount=3)
    await elem[0].press('Backspace')

    cnt = 1
    for s in txt:
        await asyncio.sleep(random.uniform(CONFIG_DICT[KEY_LOGIN_TYPING_INTERVAL_MIN], CONFIG_DICT[KEY_LOGIN_TYPING_INTERVAL_MAX]))
        await elem[0].type(s)
        if cnt % 5 == 0:
            await changeRandomWindowSize(page, connection, targetId, maxWidth, maxHeight)
        cnt += 1


async def type_txt(page, xpath, txt, timeout=15000):
    await page.waitForXPath(xpath, {"timeout": timeout})
    elem = await page.xpath(xpath)

    await elem[0].click(clickCount=3)
    await elem[0].press('Backspace')
    await elem[0].type(txt)


async def doesExist(page, xpath):
    return len(await page.xpath(xpath)) > 0


async def click(page, xpath):
    await page.waitForXPath(xpath)
    elem = await page.xpath(xpath)
    # 単純にclick()メソッドを実行しても動作しないときがあるのでevaluate()でjavascript実行を行う
    # await elem[0].click()
    await page.evaluate('elm => elm.click()', elem[0])


async def waitForEnabled(page, xpath):
    global log
    log.debug("Wait for element becomes enable. '{}'".format(xpath))
    cnt = 0
    while cnt < 30:
        if await isEnabled(page, xpath):
            return
        else:
            sleep(1)
            cnt += 1

    raise Exception(
        "Timedout wait for element becoms enable. '{}'".format(xpath))


async def isEnabled(page, xpath):
    await page.waitForXPath(xpath)
    return len(await page.xpath(xpath + "[@disabled]")) == 0


async def get_text(page, xpath, timeout=30000):
    await page.waitForXPath(xpath, {"timeout": timeout})
    elem = await page.xpath(xpath)
    return await (await elem[0].getProperty('textContent')).jsonValue()


async def press_enter(page, xpath):
    await page.waitForXPath(xpath)
    elem = await page.xpath(xpath)
    await elem[0].press('Enter')


async def type_login_info(page, connection, email, passwd):
    global log

    targetInfos = (await connection.send('Target.getTargets'))['targetInfos']
    log.debug(
        "connection.send('Target.getTargets'))['targetInfos']) -> {}".format(targetInfos))

    for targetInfo in targetInfos:
        if targetInfo['url'] == ACCOUNT_LOGIN_URL:
            targetId = targetInfo['targetId']
            break
    log.debug("targetId is {}".format(targetId))

    windowInfo = (await connection.send('Browser.getWindowForTarget', {'targetId': targetId}))
    windowId = windowInfo['windowId']
    maxWidth = windowInfo['bounds']['width']
    maxHeight = windowInfo['bounds']['height']

    for i in range(4):
        await changeRandomMinusWindowSize(page, connection, targetId)

    for i in range(random.randint(1, 5)):
        if random.randint(0, 1) == 0:
            await press_enter(page, HTML_LOGIN_PASS_PATH)
        else:
            await press_enter(page, HTML_LOGIN_EMAIL_PATH)
        await changeRandomWindowSize(page, connection, targetId, maxWidth, maxHeight)
        await asyncio.sleep(0.1)

    if random.randint(0, 1) == 0:
        log.debug("copy and paste at login text box : {}".format(email))
        await copy_paste_address_and_passwd(page, email, passwd)

    await type_txt_with_changing_window_size(page, connection, targetId, maxWidth, maxHeight, HTML_LOGIN_EMAIL_PATH, email)
    await type_txt_with_changing_window_size(page, connection, targetId, maxWidth, maxHeight, HTML_LOGIN_PASS_PATH, passwd)

    await changeWindowSizeMax(page, connection, windowId, maxWidth, maxHeight)


async def copy_paste_address_and_passwd(page, email, passwd):
    pyperclip.copy(email)
    await paste_txt(page,  HTML_LOGIN_EMAIL_PATH)
    pyperclip.copy(passwd)
    await paste_txt(page,  HTML_LOGIN_PASS_PATH)


async def updateAccountSetting(page, accountInfo):
    await page.goto(ACCOUNT_SETTING_URL)
    addressInfo = random.choice(ADDRESS_LIST)
    await type_txt(page, HTML_ACCOUNT_SETTING_EMAIL_PATH, accountInfo.newEmail)
    await click_from_drop_down_list(page, HTML_ACCOUNT_SETTING_COUNTRY_OPTION_TEXT_PATH, HTML_ACCOUNT_SETTING_COUNTRY_ID, JAPAN)
    await click_from_drop_down_list(page, HTML_ACCOUNT_SETTING_STATE_OPTION_TEXT_PATH, HTML_ACCOUNT_SETTING_STATE_ID, addressInfo.state)
    await type_txt(page, HTML_ACCOUNT_SETTING_ADDRESS_PATH, addressInfo.address)
    await type_txt(page, HTML_ACCOUNT_SETTING_ZIPCODE_PATH, addressInfo.zipcode)
    await waitForEnabled(page, HTML_ACCOUNT_SETTING_SAVE_BUTTON_PATH)
    await click(page, HTML_ACCOUNT_SETTING_SAVE_BUTTON_PATH)

    await asyncio.sleep(1)
    if await doesExist(page, HTML_ACCOUNT_SETTING_SAVE_ERROR_PATH):
        raise Exception(
            "Error happend when clicked save button. {}".format(accountInfo.email))


async def getAccountPhoneNumber(page, accountInfo):
    await page.goto(ACCOUNT_SETTING_URL)
    try:
        # 確実に存在する要素が出現するまで待機
        await get_text(page, HTML_ACCOUNT_SETTING_PHONE_NUMBER_LABEL_PATH)
        # 電話番号が存在しないケースもあるのでタイムアウトを1secにする
        accountInfo.phoneNumber = await get_text(page, HTML_ACCOUNT_SETTING_PHONE_NUMBER_PATH, 1000)
    except TimeoutError as e:
        pass
    await asyncio.sleep(random.randint(3000, 5000)/1000.0)


async def accessRandomPage(page, accountInfo):
    await page.goto(ACCOUNT_PROFILE_URL)
    await asyncio.sleep(random.randint(3000, 5000)/1000.0)

    candidatePages = [NIKE_EVENT_URL, NIKE_INBOX_URL, NIKE_ORDERS_URL]
    random.shuffle(candidatePages)

    for i in range(2):
        await page.goto(candidatePages[i])
        await asyncio.sleep(random.randint(3000, 5000)/1000.0)

    await asyncio.sleep(random.randint(3000, 5000)/1000.0)


async def nothingToDo(page, accountInfo):
    pass


async def click_from_drop_down_list(page, dropDownTxtPathTmpl, dropDownId, selectTxt):
    await page.waitForXPath(dropDownTxtPathTmpl.format(selectTxt))
    elem = await page.xpath(dropDownTxtPathTmpl.format(selectTxt))
    dropDownValue = await (await elem[0].getProperty('value')).jsonValue()
    return await page.select("#{}".format(dropDownId), dropDownValue)


def load_config():
    for line in open(CONFIG_TXT, "r"):
        items = line.replace("\n", "").split("=")

        if len(items) != 2:
            continue

        if items[0] == KEY_THREAD_NUM:
            CONFIG_DICT[KEY_THREAD_NUM] = int(items[1])

        elif items[0] == KEY_HEADLESS:
            CONFIG_DICT[KEY_HEADLESS] = ("true" == items[1].lower())

        elif items[0] == KEY_LOGIN_TYPING_INTERVAL_MIN:
            CONFIG_DICT[KEY_LOGIN_TYPING_INTERVAL_MIN] = float(items[1])

        elif items[0] == KEY_LOGIN_TYPING_INTERVAL_MAX:
            CONFIG_DICT[KEY_LOGIN_TYPING_INTERVAL_MAX] = float(items[1])

        elif items[0] == KEY_GET_NEW_ADDRESS_FROM_POI_POI:
            # pyInstallerでdistuilsのimportがエラーになるので、distutilsを利用しない
            # virtualenvのバージョンが16.4だとエラーになるらしい(16.3に下げるとうまくいくらしい)
            #CONFIG_DICT[KEY_GET_NEW_ADDRESS_FROM_POI_POI] = bool(distutils.util.strtobool(items[1]))
            CONFIG_DICT[KEY_GET_NEW_ADDRESS_FROM_POI_POI] = (
                "true" == items[1].lower())

        else:
            CONFIG_DICT[items[0]] = items[1]


def load_proxy():
    if not os.path.exists(PROXY_TXT):
        return

    for line in open(PROXY_TXT, "r"):
        proxyUrl = line.replace("\n", "")
        log.info("Found proxy {}".format(proxyUrl))
        PROXY_LIST.append(proxyUrl)


def load_address_list():
    with open(ADDRESS_LIST_TXT, "r", encoding="utf-8") as f:
        addressCsv = csv.reader(f, delimiter="\t")
        for items in addressCsv:
            ADDRESS_LIST.append(AddressInfo(items[2], items[3], items[1]))


async def get_new_address_from_meruado_poi_poi(page, prev_new_addr, org_addr):
    try:
        await asyncio.sleep(0.5)
        await click(page, XPATH_ADD_MAIL_ADDRESS)

        while True:
            try:
                new_address = await get_text(page, XPATH_NEW_ADDRESS_VIEW_DATA)
                if new_address != prev_new_addr and new_address != "":
                    break
                sleep(0.1)
            except Exception as e:
                global log
                #log.exception("Failed to get new address value : %s", e)
                sleep(0.5)

        await click(page, XPATH_CLOSE_NEW_ADDRESS_VIEW)

        return new_address

    except Exception as e:
        log.exception(
            "Unknown exception happened during getting new address : %s.", e)
        await page.screenshot(path="{}/{}.err.png".format(OUT_DIR, org_addr), fullPage=True)
        raise e


async def login_meruado_poi_poi(page):
    try:
        if CONFIG_DICT[KEY_MERUADO_POI_POI_USER] is None or CONFIG_DICT[KEY_MERUADO_POI_POI_PASS] is None \
                or CONFIG_DICT[KEY_MERUADO_POI_POI_USER] == "" or CONFIG_DICT[KEY_MERUADO_POI_POI_PASS] == "":
            await click(page, XPATH_CURRENT_ACCOUNT)
            CONFIG_DICT[KEY_MERUADO_POI_POI_USER] = await get_text(page, XPATH_CURRENT_ACOUNT_USER)
            CONFIG_DICT[KEY_MERUADO_POI_POI_PASS] = await get_text(page, XPATH_CURRENT_ACOUNT_PASS)
        else:
            await click(page, XPATH_OTHER_ACOUNT)
            await type_txt(page, XPATH_OTHER_ACOUNT_USER, CONFIG_DICT[KEY_MERUADO_POI_POI_USER])
            await type_txt(page, XPATH_OTHER_ACOUNT_PASS, CONFIG_DICT[KEY_MERUADO_POI_POI_PASS])
            await click(page, XPATH_CURRENT_ACCOUNT)
    except Exception as e:
        log.exception("Failed to login MERUADO_POI_POI : %s.", e)
        await page.screenshot(path="{}/meruado_poi_poi_login_error.png".format(OUT_DIR), fullPage=True)
        raise e


async def read_input_csv():
    global log
    inputAccountList = []
    prev_new_addr = "DUMMY"
    line_num = 0
    browser = None

    try:
        if CONFIG_DICT.get(KEY_GET_NEW_ADDRESS_FROM_POI_POI, False):
            log.info("'%s' is enabled. Try to get new mail-address from MAIL_ADDRESS_POI_POI...",
                     KEY_GET_NEW_ADDRESS_FROM_POI_POI)
            browser = await launch(headless=True,
                                   defaultViewport=None,
                                   ignoreDefaultArgs=[
                                       "--disable-extensions", "--enable-automation"],
                                   args=["--load-extension={}/{}".format(os.getcwd(), CHROME_PROXY_EXTENTION_DIR)])
            page = await browser.newPage()
            await page.goto(MERUADO_POI_POI_URL)
            await login_meruado_poi_poi(page)
            log.info("Login account ID = %s : PASS = %s",
                     CONFIG_DICT[KEY_MERUADO_POI_POI_USER], CONFIG_DICT[KEY_MERUADO_POI_POI_PASS])

        for line in open(INPUT_CSV, "r"):
            line_num += 1
            if line_num == 1:
                continue

            items = line.replace("\n", "").split(",")

            if len(items) != 3:
                continue

            if CONFIG_DICT.get(KEY_GET_NEW_ADDRESS_FROM_POI_POI, False):
                new_address = await get_new_address_from_meruado_poi_poi(page, prev_new_addr, items[0])
                items[1] = new_address
                prev_new_addr = new_address
                log.info(
                    "Collected new mail address : [%3d] %s", line_num - 1, new_address)

            inputAccountList.append(items)

        return inputAccountList

    finally:
        if browser is not None:
            await browser.close()


def getPhoneNumberCheckAccountList(dummy):
    inputAccountList = []
    with open(INPUT_PHONE_NUMBER_CHECK_CSV, "r", encoding="utf-8") as f:
        inputCsv = csv.reader(f)
        next(inputCsv)  # skip header
        for items in inputCsv:
            inputAccountList.append(AccountInfo(
                email=items[0], password=items[1]))
    return inputAccountList


def getLoginPatrolAccountList(dummy):
    inputAccountList = []
    with open(INPUT_LOGIN_PATROL_CSV, "r", encoding="utf-8") as f:
        inputCsv = csv.reader(f)
        next(inputCsv)  # skip header
        for items in inputCsv:
            inputAccountList.append(AccountInfo(
                email=items[0], password=items[1]))
    return inputAccountList


def getLoginWithChromeProfileAccountList(dummy):
    inputAccountList = []
    with open(INPUT_LOGIN_WITH_CHROME_PROFILE_CSV, "r", encoding="utf-8") as f:
        inputCsv = csv.reader(f)
        next(inputCsv)  # skip header
        for items in inputCsv:
            print(items)
            inputAccountList.append(AccountInfo(
                email=items[0], password=items[1], chromeProfile=items[2]))
    return inputAccountList


def doAsyncOperation(operation, readInputData):
    semaphore = asyncio.Semaphore(CONFIG_DICT[KEY_THREAD_NUM])

    log.info("Start processing.\n")

    loop = asyncio.get_event_loop()
    accountInfoList = readInputData(loop)
    gatheringFuture = asyncio.gather(
        *[callOperation(operation, accountInfo, semaphore) for accountInfo in accountInfoList])
    loop.run_until_complete(gatheringFuture)


def getUpdateAccountList(loop):
    return [AccountInfo(email=item[0], newEmail=item[1], password=item[2]) for item in loop.run_until_complete(read_input_csv())]


def write_result_csv():
    success_cnt = 0
    error_cnt = 0
    f = open("%s\\%s" % (OUT_DIR, dt.now().strftime(
        'result-%Y%m%d-%H%M%S.csv')), "w")
    f.write("旧アドレス,新アドレス,結果,失敗理由\n")
    for i in range(output_q.qsize()):
        items = output_q.get()
        accountInfo = items[0]
        f.write("%s,%s,%s,%s\n" %
                (accountInfo.email, accountInfo.newEmail, items[1], items[2]))

        if items[1] == SUCCESS:
            success_cnt += 1
        else:
            error_cnt += 1
    f.close()
    log.info("")
    log.info("Success:%d Fail:%d" % (success_cnt, error_cnt))
    log.info("")
    log.info("Refer %s for more detail." % f.name)
    log.info("")


def writePhoneNumberResultCsv():
    success_cnt = 0
    error_cnt = 0
    f = open("%s\\%s" % (OUT_DIR, dt.now().strftime(
        'result-phone-number-%Y%m%d-%H%M%S.csv')), "w")
    for i in range(output_q.qsize()):
        items = output_q.get()
        accountInfo = items[0]

        if items[1] == SUCCESS:
            success_cnt += 1
        else:
            accountInfo.phoneNumber = "ERROR"
            error_cnt += 1

        f.write("%s:%s,%s\n" % (accountInfo.email,
                                accountInfo.password,
                                accountInfo.phoneNumber))

    f.close()
    log.info("")
    log.info("Success:%d Fail:%d" % (success_cnt, error_cnt))
    log.info("")
    log.info("Refer %s for more detail." % f.name)
    log.info("")


def writeLoginPatrolResultCsv():
    writeLoginResultCsv(dt.now().strftime(
        'result-login-result-%Y%m%d-%H%M%S.csv'))


def writeLoginWithChromeProfileResultCsv():
    writeLoginResultCsv(dt.now().strftime(
        'result-login-with-chrome-result-%Y%m%d-%H%M%S.csv'))


def writeLoginResultCsv(csvFileName):
    success_cnt = 0
    error_cnt = 0
    f = open("%s\\%s" % (OUT_DIR, csvFileName), "w")
    for i in range(output_q.qsize()):
        items = output_q.get()
        accountInfo = items[0]

        if items[1] == SUCCESS:
            success_cnt += 1
        else:
            accountInfo.phoneNumber = "ERROR"
            error_cnt += 1

        f.write("%s:%s,%s\n" % (accountInfo.email,
                                accountInfo.password,
                                items[1]))

    f.close()
    log.info("")
    log.info("Success:%d Fail:%d" % (success_cnt, error_cnt))
    log.info("")
    log.info("Refer %s for more detail." % f.name)
    log.info("")


# def mach_license():
#    return licencemanager.match_license()


def output_meruado_poi_poi_info():
    if CONFIG_DICT.get(KEY_GET_NEW_ADDRESS_FROM_POI_POI, False):
        log.info("MERUADO_POI_POI account infomation is below.")
        log.info("ID   = %s", CONFIG_DICT[KEY_MERUADO_POI_POI_USER])
        log.info("PASS = %s", CONFIG_DICT[KEY_MERUADO_POI_POI_PASS])
        log.info("")


def hasPermission():
    import uuid
    import re
    import hashlib
    import json

    global log

    serialKey = CONFIG_DICT[KEY_SERIAL_KEY]
    productKey = CONFIG_DICT[KEY_WINDOWS_PRODUCT_KEY]
    macAddress = '-'.join(re.split('(..)', format(uuid.getnode(), 'x'))[1::2])
    log.debug("DEBUG: macAddress -> %s", macAddress)
    pVal = productKey + macAddress
    pVal = hashlib.sha256(pVal.encode()).hexdigest().upper()
    postData = {"POSTSTR": serialKey, "PKEY": pVal}
    log.debug("DEBUG: Post authentication data -> %s", postData)
    response = requests.post(AUTHENTICATION_SERVER, data=postData)

    if response.status_code != 200:
        log.info("Authentication server return HTTP status %d",
                 response.status_code)
        return False

    responseDict = json.loads(response.text)

    if responseDict["ReturnCode"] != "200":
        log.info("ERROR: Authentication error. ReturnCode:%s, HTML:'%s', Message:'%s'",
                 responseDict["ReturnCode"],
                 responseDict["HTML"],
                 responseDict["Message"],
                 )
        return False

    return True


def main():
    global log
    try:
        load_config()
        if not hasPermission():
            input("Please push Enter to exit.")
            return
        load_proxy()
        load_address_list()
        operation, readInputData, writeResultData = fire.Fire(
            {
                "updateAccount": getFunctionsForAccountUpdate,
                "checkPhoneNumber": getFunctionsForPhoneNumberCheck,
                "loginPatrol": getFunctionsForLoginPatrol,
                "loginWithChromeProfile": getFunctionsForLoginWithChromeProfile,
            }
        )
        doAsyncOperation(operation, readInputData)
        writeResultData()
        output_meruado_poi_poi_info()
    except Exception as e:
        log.exception("Happened exception stop operation... : %s", e)

    input("Please push Enter to exit.")


def getFunctionsForAccountUpdate():
    return updateAccountSetting, getUpdateAccountList, write_result_csv


def getFunctionsForPhoneNumberCheck():
    return getAccountPhoneNumber, getPhoneNumberCheckAccountList, writePhoneNumberResultCsv


def getFunctionsForLoginPatrol():
    return accessRandomPage, getLoginPatrolAccountList, writeLoginPatrolResultCsv


def getFunctionsForLoginWithChromeProfile():
    return nothingToDo, getLoginWithChromeProfileAccountList, writeLoginWithChromeProfileResultCsv


if __name__ == "__main__":
    log = logging.getLogger()
    logging.config.fileConfig(LOG_CONF)
    output_q = queue.Queue()
    main()
