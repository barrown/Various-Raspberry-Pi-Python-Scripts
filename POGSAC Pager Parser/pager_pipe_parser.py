#! python3
# v1.7

# set up a list of strings to ignore, made into lowercase
IGNORED_WORDS_LIST = ["animal name", "temperature alert", "northallerton fire call", "this offer expires", "test message", "test call", "testing", "test test", "+++time=", " pony ", " bitch ", " ewe ", " lamb "]

# to be able to read in the piped line from multimon-ng
from sys import stdin
from sys import exit

# send webhook to home assistant
from requests import post
home_assistant_url = "http://192.168.0.104:8123/api/webhook/-pager"

# set up database
import sqlite3
con = sqlite3.connect("db_of_pages.sqlite")
cur = con.cursor()
sql = ''' INSERT INTO pager(datetime,message,postcode,age,ismale) VALUES(?,?,?,?,?) '''

# pull out postcodes and any sex/age information using regular expressions
import re
regex_postcode = re.compile(r'([Gg][Ii][Rr] 0[Aa]{2})|((([A-Za-z][0-9]{1,2})|(([A-Za-z][A-Ha-hJ-Yj-y][0-9]{1,2})|(([A-Za-z][0-9][A-Za-z])|([A-Za-z][A-Ha-hJ-Yj-y][0-9][A-Za-z]?))))\s?[0-9][A-Za-z]{2})')
regex_sexage = re.compile(r'\b(?:MALE|FEMALE) \d{1,3}[DWMY]\b', re.IGNORECASE)
regex_noise = re.compile(r'<[a-zA-Z0-9]{2,3}>')

#    pattern = r'\b(?:MALE|FEMALE) \d{1,3}[DWMY]\b(.*?) GRD'

# initalise list of message logs to detect duplicates
message_log_list =  [""]*50


try:
    with open("all_pager_messages.txt","a",buffering=1) as legit:  # buffering 1 means writing to disk in every text line
        while True:
            # grab the string from standard input stream
            pager_line = stdin.readline()

            # send home assistant the webhook to increment the number of pages counter
            try:
                post(home_assistant_url)
            except:
                # we don't want to stop this script if home assistant is rebooting/offline
                pass
            
            # split into different parts; time, address, function, message
            # limit to 5 splits in case there are colons in the message
            splitline = pager_line.split(': ',5)
            
            # quick check for having the right number of parts
            if len(splitline) < 6:
                continue

            datetime = splitline[0]
            address = int(splitline[3].split()[0])
            message = splitline[5].strip()

            # ignore certain addresses that seem to be some guys emails
            if address == 549209:
                continue

            # ignore short messages
            if len(message) < 60:
                continue
            
            # remove junk messages that typically contain a bunch of asterisks or no spaces
            if message.count('*') > 16 or message.count(' ') < 3:
                continue
            
            # ignore messages containing certain watchwords
            break_outer_loop = False
            for word in IGNORED_WORDS_LIST:
                if word in message.lower():
                    break_outer_loop = True
                    continue
            if break_outer_loop:
                continue

            # ignore short messages from BOSS Mobile
            if "https://bossd.nfcsp.org.uk" in message and len(message) < 100:
                continue

            # replace <LF> with a space
            message = message.replace("<LF>"," ")
            
            # remove noise like <NUL><DEL><SYN><SOH><BS><DC3><CAN><HT><BEL><CR><NAK>
            message = regex_noise.sub('', message)

            # ignore messages that are mostly lowercase
            upper_count = sum(1 for char in message if char.isupper())
            lower_count = sum(1 for char in message if char.islower())
            if upper_count < lower_count:
                continue

            # ignore repeat messages
            if message[20:] in message_log_list:
                continue

            # we have a legit message, so lets pull out the sex, age and postcode
            sexagematch = regex_sexage.search(message)
            if sexagematch:
                # the first part of the group will be "MALE" or "FEMALE", so just grab the first letter in the string
                if sexagematch.group()[0].upper() == "M":
                    ismale = 1
                else:
                    ismale = 0
                
                # the second part of the group (after a whitespace) will be the age like "42Y"
                age = sexagematch.group().split()[1]
                if age[-1].upper() == 'Y':
                    age = int(age[:-1])
                elif age[-1].upper() == 'M' or age[-1].upper() == 'W' or age[-1].upper() == 'D':
                    age = 0
            else:
                ismale = None
                age = None


            # postcodes
            postcodematch = regex_postcode.search(message)
            if postcodematch:
                postcode = postcodematch.group()
            else:
                postcode = None


            # write out to file and database
            # datetime,message,postcode,age,ismale
            values = (datetime, message, postcode, age, ismale)
            cur.execute(sql, values)
            con.commit()

            pager_line = pager_line.replace("<LF>"," ").replace("<CR>","").replace("<HT>","").replace("<BEL>","").replace("<NUL>","").replace("<DEL>","").replace("<SYN>","").replace("<SOH>","").replace("<BS>","")
            legit.write(pager_line) # because buffering = 1 this is written to disk straight away
            del message_log_list[0]
            message_log_list.append(message[20:])

except BaseException as e:
    con.close()
    print(f"Python: We got an error or asked to stop... connection to database closed. Error: {e}")
    exit(1)



# SELECT MAX(datetime),message FROM pager;

####
# CREATE VIRTUAL TABLE pager USING fts5(datetime UNINDEXED, message, postcode UNINDEXED, age UNINDEXED, ismale UNINDEXED, tokenize = 'ascii');
####
