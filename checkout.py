from selenium import webdriver
import os,logging,os.path,pickle,threading
import time,re,requests,json,random
from threading import Thread
from multiprocessing.pool import ThreadPool
import asyncio
import json 
from selenium.common.exceptions import NoSuchElementException,ElementNotInteractableException,ErrorInResponseException,ElementNotVisibleException,ElementNotSelectableException,ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import schedule
import calendar
import importlib
# file 
from utils.localstorage import LocalStorage 
from utils.handy_wrappers import HandyWrappers

# testing
# from seleniumwire import webdriver
from selenium.webdriver.common.proxy import Proxy, ProxyType


data = []
debug = False
orderIndex = -1

try:
    #We read our JSON data from a file called 'config.conf' for simplicity and readability.
    with open('config.conf') as json_file:
        data = json.load(json_file)

except Exception as e:
	print("Error: either no config.conf was found, or it contains invalid JSON syntax!")
	if(debug):
		print('Error Details: ' + str(e))


def Login(driver,username,password,id):
    max_tries = 5
    for t in range(max_tries):
        try:
            time.sleep(4)
            print(username + ' trying to login ' + str(t+1) +' times')

            try:
                driver.find_element_by_css_selector(".emailAddress > input").clear()
                time.sleep(0.5)
                driver.find_element_by_css_selector(".emailAddress > input").send_keys(username)
            except NoSuchElementException:
                pass
            except ElementNotInteractableException:
                pass
            
            try:
                driver.find_element_by_css_selector(".nike-unite-password-input > input").send_keys(password)
            except:
                pass

            # login_submit = WebDriverWait(driver,5,poll_frequency=1,
            #                     ignored_exceptions=[NoSuchElementException,
            #                                         ElementNotVisibleException,
            #                                         ElementNotSelectableException])
            # btn_submit = login_submit.until(EC.element_to_be_clickable((By.CSS_SELECTOR,".loginSubmit > input")))
            # btn_submit.click()

            try:
                driver.find_element_by_css_selector(".loginSubmit > input").click()
            except:
                pass
            
            current_url = driver.current_url
            # open cookies file
            if current_url.find("gs.nike.com") != -1:
                write_cookies(driver,id,username)
                break
            else:

                # CORS problem/ spamming login will have this issue
                try:
                    time.sleep(2)
                    driver.find_element_by_css_selector(".nike-unite-error-close > input").click()
                    driver.find_element_by_css_selector(".loginSubmit > input").click()
                    pass

                except NoSuchElementException:
                    print(username + ' have been login or  didnt meet have CORS Problem')

            current_url = driver.current_url
            
            
        except (NoSuchElementException):
            print(username + ' is logged in or there is cant find login Element ')
        except (ElementClickInterceptedException):
            print(username + 'there cannot login, try again..Error: ClickIntercaptedException')
        except (ErrorInResponseException):
            print(username + 'there cannot login, try again..Error: ErrorInResponseException')


def write_cookies(driver,id,username):
     # open cookies file
    cookies_file =  open("cookies/cookies"+ username +".pkl","wb")
    # empty cookies
    empty_list = []
    pickle.dump(empty_list, cookies_file)
    # renew cookies data
    print(username + ' renew cookies data')
    pickle.dump( driver.get_cookies() ,cookies_file)



def write_localStorage(driver,username,url):
       # get the local storage
    driver.get("https://unite.nike.com/session.html")
    # set the local storage to unite nike.com
    storage = LocalStorage(driver)
    try:
        uniteCredential = storage.get("com.nike.unite.credential")
    except:
        uniteCredential = None
    try:
        webCredential = storage.get("com.nike.commerce.nikedotcom.web.credential")
    except:
        webCredential = None
    try:
        identityUser  = storage.get("identity.user")
    except:
        identityUser  = None
    try:
        snkrsCredential = storage.get("com.nike.commerce.snkrs.web.credential")
    except:
        snkrsCredential = None

    localstorageData = {}
    localstorageData['user'] = []
    localstorageData['user'].append({
        'com.nike.commerce.nikedotcom.web.credential':webCredential,
        'com.nike.unite.credential':uniteCredential,
        'identity.user':identityUser,
        'snkrsCredential':snkrsCredential
    })

    print(username + ' open unite.nike.com get LATEST Data')
    with open('localstorage/'+ username + '.json', 'w+') as outfile:
        json.dump(localstorageData, outfile)

    print(username + ' redirect to checkout website')
    driver.get(url)

def Checkout(driver,cvv,id,username,submit_time):
    max_tries = 5
    for t in range(max_tries):
        try:
            time.sleep(4)
            print('switch payment iframe ' + str(t+1) + ' times')
            driver.switch_to.frame(driver.find_element_by_css_selector('.cvv'))
            time.sleep(2)

            print('proceed to checkout, now filling cvv')
            # driver.find_element_by_css_selector(".gdprConsentCheckbox").click()
            driver.find_element_by_name("cardCvc").send_keys(cvv)
            time.sleep(2)
            # switch back to default frame
            driver.switch_to.default_content()
            time.sleep(1)

            last_time = time.time()
            # while loop check timer every sec
            while(...):
                new_time = time.time()
                if(new_time > last_time+1):
                    OnsubmitTime = timer(submit_time,driver,username)
                    if(OnsubmitTime == True):
                        break
                    time.sleep(1)
            break 

        except NoSuchElementException as e:
            print(username + ' there cannot checkout, try again..Error: NoSuchElementException : '+ str(e))

# uses for check submit time is reach or not
def timer(submit_time,driver,username):
    current_time = str(calendar.timegm(time.gmtime()))
    if current_time >= submit_time:    
        driver.find_element_by_css_selector(".button-submit").click()
        print(username + ' time reach, submit button')
        return True
    else: 
        print(username + ' time hvnt reach')
        return False

def read_localStorage(driver,username,token):
    storage = LocalStorage(driver)
    storage.set("com.nike.commerce.nikedotcom.web.credential",json.dumps(token))
    file = 'localstorage/'+ username + '.json'
    if os.path.isfile(file):
        with open('localstorage/'+ username + '.json') as json_file:
            data = json.load(json_file)
            for p in data['user']:
                storage.set("com.nike.commerce.nikedotcom.web.credential",p['com.nike.commerce.nikedotcom.web.credential'])
                storage.set('com.nike.unite.credential',p['com.nike.unite.credential'])
                storage.set('identity.user',p['identity.user'])
                storage.set('com.nike.commerce.nikedotcom.web.credential',p['com.nike.commerce.nikedotcom.web.credential'])
    else:
        pass


def read_cookies(driver,username,id):
       # load cookies from last check
    file = "cookies/"+ username +".pkl"
    if os.path.isfile(file):
        # exists
        print( username  + ' reading cookies from file')
        cookies = pickle.load(open(file, "rb"))
        for cookie in cookies:
            driver.add_cookie(cookie)

    else:
        # doesn't exist cookies, so write current cookies into prevent block by CORS
        write_cookies(driver,id,username)
        print( username  + ' have no cookies file')
        pass

# main process 
def main(data,id):
    # init data
    username    = data['username']
    password    = data['password']
    url         = data['url']
    cvv         = data['cvv']
    token       = data['token']
    submit_time = data['time']
    # http        = data['http']
    # https       = data['https']
    # socks5      = data['socks5']
    # enable chrome driver
    driverLocation = "./chromedriver"
    chromeOptions = webdriver.ChromeOptions()
    os.environ["webdriver.chrome.driver"] = driverLocation
    # Chrome enable headless,proxy
    # chromeOptions.add_argument("--headless")
    # chromeOptions.add_argument("--proxy-server=https://username:password@ip:port")
    chromeOptions.add_experimental_option("excludeSwitches", ["enable-automation"])
    chromeOptions.add_experimental_option('useAutomationExtension', False)
    chromeOptions.add_experimental_option("detach", True)
    chromeOptions.add_argument('log-level=2')

    # prox = Proxy()
    # prox.proxy_type = ProxyType.MANUAL
    # prox.http_proxy = http
    # prox.socks_proxy = socks5
    # prox.ssl_proxy = https
    # capabilities = webdriver.DesiredCapabilities.CHROME
    # prox.add_to_capabilities(capabilities)
    #  ssl ignore
    # chromeOptions.add_argument('--ignore-certificate-errors')
    # chromeOptions.add_argument('--ignore-ssl-errors')

    # Instantiate Chrome Browser Command
    driver = webdriver.Chrome(options = chromeOptions,executable_path=driverLocation)
    
    #open tab
    print(username + ' open unite.nike.com set cookies')
    driver.get("https://unite.nike.com/session.html")
    # driver.get("https://whatismyipaddress.com/")
    # set the local storage to unite nike.com
    read_localStorage(driver,username,token)
    
    time.sleep(3)
    driver.get(url)
    print(username + " open " + url)
    time.sleep(1)
    # print URL 
    read_cookies(driver,username,id)

    #  need to check did user login or not, if not then proceed to login
    Login(driver,username,password,id)
    write_localStorage(driver,username,url)
    time.sleep(5)

    # get current URL see if access to payment page
    current_url = driver.current_url
    max_tries = 5
    for t in range(max_tries):
        if (current_url.find("gs.nike.com") != -1):
            # check out driver page
            print(username + " successful get into payment page in " + str(t+1) +" times")
            Checkout(driver,cvv,id,username,submit_time)
            break
        else:
            print(username + " not getting EL payment page in " + str(t+1) +" times")
            time.sleep(5)

    time.sleep(35)

# threadpool run data
def run_main(data):
    id()
    main(data['users'][orderIndex],orderIndex)

# iterate json 
def id():
    global orderIndex
    orderIndex+=1
    return orderIndex


startTime  = time.time()
# main = run_main(orderIndex,data)
pool = ThreadPool(processes=5)
pool.map(run_main,(data for user in data['users']))
pool.close