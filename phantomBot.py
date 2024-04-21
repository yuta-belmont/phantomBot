from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import subprocess
import pyautogui
from pynput.keyboard import Controller, Key
import itertools
from hashlib import sha256
import binascii

EXTENSION_PATH = r'path to your crx file'

#open chrome
OPT = webdriver.ChromeOptions()
OPT.add_extension(EXTENSION_PATH) #nav to phantom wallet
DRIVER = webdriver.Chrome(options = OPT)

seed_words = ['enter your 11 words here in a list']

#switch to wallet tab
def main():
    startup() #optionally pass the number of permutations you'd like to skip if you want here

#___________________________
#helper functions below: 
#___________________________

def startup(skip_count = 0):
    possible_words = get_bip39_words_list() 
    count = 0
    time.sleep(3.5)
    #switch to current tab
    switchToCurrentTab()
    #go to input seed words url
    DRIVER.get('chrome-extension://bfnaelmomeimhlpmgjnjophhpkkoljpa/onboarding.html?append=true')
    time.sleep(1)
    #enter the seed words:
    #Check the first 11 positions
    for pos in range(11):
        #iterate thru all 2048 words in this position:
        for word in possible_words:
            input_string = ''
            check_seed_words = seed_words.copy()
            check_seed_words.insert(pos, word)

            #Check if the last word is valid for the checksum.
            #This allows us to reduce the search space by ~16x
            if check_seed_words[-1] in checkSum(check_seed_words[:-1]):
                for word1 in check_seed_words:
                    input_string += word1 + ' '
            else:
                continue

            #We can skip iterations if we've already done them.
            #The number of skips is passed into startUp as a param.
            if skip_count > 0:
                skip_count -= 1
                count += 1
                continue
            
            #input the words and check if the account has balance:
            inputSeedWords(input_string)
            count += 1
            if accountHasBalance():
                print(count, "Wallet found:", input_string)
                return
            else:
                print(count, "Empty wallet:", input_string)
                DRIVER.get('chrome-extension://bfnaelmomeimhlpmgjnjophhpkkoljpa/onboarding.html?append=true')

    #check the 12th position:
    for word in possible_words:
        check_seed_words = seed_words.copy()
        check_seed_words.append(word)
        input_string = ''

        #if the last word is valid for the checksum:
        if check_seed_words[-1] in checkSum(check_seed_words[:-1]):
            for word1 in check_seed_words:
                input_string += word1 + ' '
        else:
            continue

        #We can skip iterations if we've already done them.
        #The number of skips is passed into startUp as a param.
        if skip_count > 0:
            skip_count -= 1
            count += 1
            continue

        #input seed words and check account has balance:
        inputSeedWords(input_string)
        count += 1
        if accountHasBalance():
            print(count, "Wallet found:", input_string)
            return
        else:
            print(count, "Empty wallet:", input_string)
            DRIVER.get('chrome-extension://bfnaelmomeimhlpmgjnjophhpkkoljpa/onboarding.html?append=true')

def inputSeedWords(seed_word_string): #space delimited string of seed words
    switchToCurrentTab()
    #select input field
    elem = tryToLocateElement('/html/body/div/main/div[2]/form/div/div[2]/div[1]/input')
    elem.send_keys(seed_word_string)
    #enter the wallet
    time.sleep(0.5)
    tryToLocateElement('/html/body/div/main/div[2]/form/button').click()
    #click view accounts
    time.sleep(0.5)
    tryToLocateElement('/html/body/div/main/div[2]/form/button[1]').click()

def accountHasBalance():
    sol_balance = tryToLocateElement('/html/body/div/main/div[2]/form/div/div[2]/div[2]/div[2]/div[2]/p[1]').text[0]
    eth_balance = DRIVER.find_element(by = By.XPATH, value = '/html/body/div/main/div[2]/form/div/div[2]/div[3]/div[2]/div[2]/p[1]').text[0]
    mat_balance = DRIVER.find_element(by = By.XPATH, value = '/html/body/div/main/div[2]/form/div/div[2]/div[4]/div[2]/div[2]/p[1]').text[0]
    if sol_balance == '0' and eth_balance == '0' and mat_balance == '0':
        return False
    return True

def switchToCurrentTab():
    window_handles = DRIVER.window_handles
    desired_window = window_handles[-1]
    DRIVER.switch_to.window(desired_window)

def get_bip39_words_list():
    lines = None
    # downloaded from https://raw.githubusercontent.com/bitcoin/bips/master/bip-0039/english.txt
    with open('phantomBot/english.txt') as file:
        lines = [line.rstrip() for line in file]
    assert(len(lines) == 2048)
    return lines

def checkSum(seed_phrase):
    bits_string = ''
    bip39_words_list = get_bip39_words_list()
    for word in seed_phrase:
        decimal_index = bip39_words_list.index(word)
        binary_index = bin(decimal_index)[2:].zfill(11)
        bits_string += binary_index

    bits_to_add = None
    chars_for_checksum = None
    if len(seed_phrase) == 11:
        bits_to_add = 7
        chars_for_checksum = 1
    elif len(seed_phrase) == 23:
        bits_to_add = 3
        chars_for_checksum = 2
    
    combos = itertools.product(['0', '1'], repeat=bits_to_add)
    combos = [ ''.join(list(i)) for i in combos]
    combos = sorted(combos, key=lambda x: int(x, 2))
    
    candidates = set()
    for combo in combos:
        entropy = '{}{}'.format(bits_string, combo)
        hexstr = "{0:0>4X}".format(int(entropy,2)).zfill(int(len(entropy)/4))
        data = binascii.a2b_hex(hexstr)
        hs = sha256(data).hexdigest()
        last_bits = ''.join([ str(bin(int(hs[i], 16))[2:].zfill(4)) for i in range(0, chars_for_checksum) ])
        last_word_bin = '{}{}'.format(combo, last_bits)
        candidates.add(bip39_words_list[int(last_word_bin, 2)])
    return candidates

#tries to click every quarter second. Times out after 30 seconds.
def tryToLocateElement(xpath, timeout = 30):
    sleepTimer = 0
    while sleepTimer < timeout:
        try:
            elem = DRIVER.find_element(by = By.XPATH, value = xpath)
            return elem
        except:
            pass
        time.sleep(0.25)
        sleepTimer += 0.25
    print("Failed to find element: [", xpath, "] after", timeout, "seconds.")

if __name__=="__main__":
    main()
