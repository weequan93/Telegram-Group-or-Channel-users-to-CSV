from telethon import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty, InputPeerChannel, InputPeerUser
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError
from telethon.tl.functions.channels import InviteToChannelRequest
import sys
import csv
import traceback
import time
import random
import re
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


api_id = os.getenv("APP_ID")        # YOUR API_ID
api_hash = os.getenv("API_HASH")       # YOUR API_HASH
phone = os.getenv("PHONE_NUMBER")       # YOUR PHONE NUMBER, INCLUDING COUNTRY CODE
client = TelegramClient(phone, api_id, api_hash)

# client.connect()

# if not client.is_user_authorized():
#     client.send_code_request(phone)
#     client.sign_in(phone, input('Enter the code: '))

async def add_users_to_group():
    input_file = sys.argv[1]
    users = []
    with open(input_file, encoding='UTF-8') as f:
        rows = csv.reader(f,delimiter=",",lineterminator="\n")
        next(rows, None)
        for row in rows:
            user = {}
            user['username'] = row[0]
            try:
                user['id'] = int(row[1])
                user['access_hash'] = int(row[2])
            except IndexError:
                print ('users without id or access_hash')
            users.append(user)

    #random.shuffle(users)
    chats = []
    last_date = None
    chunk_size = 10
    groups=[]

    result = await client(GetDialogsRequest(
                offset_date=last_date,
                offset_id=0,
                offset_peer=InputPeerEmpty(),
                limit=chunk_size,
                hash = 0
            ))
    chats.extend(result.chats)

    for chat in chats:
        try:
            if chat.megagroup== True: # CONDITION TO ONLY LIST MEGA GROUPS.
                groups.append(chat)
        except:
            continue

    print('Choose a group to add members:')
    i=0
    for group in groups:
        print(str(i) + '- ' + group.title)
        i+=1

    g_index = input("Enter a Number: ")
    target_group=groups[int(g_index)]
    print('\n\nGrupo elegido:\t' + groups[int(g_index)].title)

    target_group_entity = InputPeerChannel(target_group.id,target_group.access_hash)

    mode = int(input("Enter 1 to add by username or 2 to add by ID: "))

    error_count = 0

    for user in users:
        try:
            print ("Adding {}".format(user['username']))
            if mode == 1:
                if user['username'] == "":
                    continue
                user_to_add = await client.get_input_entity(user['username'])
            elif mode == 2:
                user_to_add = InputPeerUser(user['id'], user['access_hash'])
            else:
                sys.exit("Invalid Mode Selected. Please Try Again.")
            await client(InviteToChannelRequest(target_group_entity,[user_to_add]))
            print("Waiting 60 Seconds...")
            await asyncio.sleep(60)
        except PeerFloodError:
            print("Getting Flood Error from telegram. Script is stopping now. Please try again after some time.")
        except UserPrivacyRestrictedError:
            print("The user's privacy settings do not allow you to do this. Skipping.")
        except:
            traceback.print_exc()
            print("Unexpected Error")
            error_count += 1
            if error_count > 10:
                sys.exit('too many errors')
            continue

async def list_users_in_group():
    chats = []
    last_date = None
    chunk_size = 200
    groups=[]
    
    # result = await client(GetDialogsRequest(
    #             offset_date=last_date,
    #             offset_id=0,
    #             offset_peer=InputPeerEmpty(),
    #             limit=chunk_size,
    #             hash = 0
    #         ))
    result = await client.get_dialogs()
    chats.extend([d.entity for d in result])
    
    for chat in chats:
        try:
            print(chat.title)
            # print(chat)
            
            groups.append(chat)
            # if chat.megagroup== True:
        except:
            continue
    
    print('Choose a group to scrape members from:')
    i=0
    for g in groups:
        print(str(i) + '- ' + g.title)
        i+=1
    
    g_index = input("Enter a Number: ")
    target_group=groups[int(g_index)]

    print('\n\nGrupo elegido:\t' + groups[int(g_index)].title)
    
    print('Fetching Members...')
    all_participants = []
    all_participants = await client.get_participants(target_group, aggressive=True)
    
    print('Saving In file...')
    with open("members-" + re.sub("-+","-",re.sub("[^a-zA-Z]","-",str.lower(target_group.title))) + ".csv","w",encoding='UTF-8') as f:
        writer = csv.writer(f,delimiter=",",lineterminator="\n")
        writer.writerow(['username','user id', 'access hash','name','group', 'group id', 'online', 'bot', 'phone'])
        for user in all_participants:

            if user.username:
                username= user.username
            else:
                username= ""
            if user.first_name:
                first_name= user.first_name
            else:
                first_name= ""
            if user.last_name:
                last_name= user.last_name
            else:
                last_name= ""
            name= (first_name + ' ' + last_name).strip()
            
            # Handle different status types
            online_status = "Unknown"
            if user.status is None:
                online_status = "Never"
            elif hasattr(user.status, 'was_online'):
                # UserStatusOffline
                online_status = user.status.was_online
            elif user.status.__class__.__name__ == 'UserStatusOnline':
                online_status = "Online"
            elif user.status.__class__.__name__ == 'UserStatusRecently':
                online_status = "Recently"
            elif user.status.__class__.__name__ == 'UserStatusLastWeek':
                online_status = "Last week"
            elif user.status.__class__.__name__ == 'UserStatusLastMonth':
                online_status = "Last month"
            else:
                online_status = str(user.status.__class__.__name__)
            
            writer.writerow([username,user.id,user.access_hash,name,target_group.title, target_group.id, online_status, user.bot, user.phone])  
    print('Members scraped successfully.')

def printCSV():
    input_file = sys.argv[1]
    users = []
    with open(input_file, encoding='UTF-8') as f:
        rows = csv.reader(f,delimiter=",",lineterminator="\n")
        next(rows, None)
        for row in rows:
            user = {}
            user['username'] = row[0]
            user['id'] = int(row[1])
            user['access_hash'] = int(row[2])
            users.append(user)
            print(row)
            print(user)
    sys.exit('FINITO')

# print('Fetching Members...')
# all_participants = []
# all_participants = client.get_participants(target_group, aggressive=True)

async def main():
    await client.start()
    
    print('What do you want to do:')
    mode = int(input("Enter \n1-List users in a group\n2-Add users from CSV to Group (CSV must be passed as a parameter to the script\n3-Show CSV\n\nYour option:  "))

    if mode == 1:
        await list_users_in_group()
    elif mode == 2:
        await add_users_to_group()
    elif mode == 3:
        printCSV()
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
