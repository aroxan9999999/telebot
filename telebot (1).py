import os
import asyncio
import time
from telethon import TelegramClient, types
from telethon.tl.functions.messages import GetDialogsRequest
from tqdm.asyncio import tqdm_asyncio
from typing import List

settings = os.path.exists('D:/telegram_settings/settings.txt')
if not settings:
    path = 'D:/telegram_settings/'
    os.mkdir(path)
    with open(f"{path}/settings.txt", 'w', encoding='utf-8') as file:
        file.write(
            'api-id=your api-id\napi-hash=your api hash\npath=enter the path to save the files б, For example D:/telegram\nsemaphores=10\nphone_number=0000')

try:
    with open('D:/telegram_settings/settings.txt', "r") as file:
        api_id, api_hash, path_save_file, semaphore, phone_number = [value.split('=')[1] for value in file.readlines()][
                                                                    :5]
except Exception as exc:
    print('fix settings')
if not os.path.exists(path_save_file):
    if not os.path.exists('D:/telegram_media'):
        os.mkdir('D:/telegram_media')
    path_save_file = 'D:/telegram_media'

api_id, api_hash = int(api_id.replace('\n', '')), api_hash.replace('\n', '')

# Your API ID and hash obtained from https://my.telegram.org
API_ID = api_id
API_HASH = api_hash

# The title of the Telegram group to download messages from
group_title = input('Enter the nam of the group: ').strip()

# The path to the directory where downloaded media files will be saved
download_folder = f"{path_save_file}/{''.join([char if char.isalnum() else '_' for char in group_title])}"
print(download_folder)
if not os.path.exists(f"{download_folder}/messages"):
    os.makedirs(f"{download_folder}/messages")

# Number of messages to download
MESSAGE_LIMIT = int(input('Enter the messages limit: '))

semaphore = asyncio.Semaphore(int(semaphore))  # Change the value to limit the number of concurrent downloads


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


async def download_media_messages(chunk: List[types.Message], client: TelegramClient, pbar):
    async with semaphore:
        for message in chunk:
            try:
                if message.media is not None:
                    # Determine the message type and download the corresponding media file
                    if isinstance(message.media, types.MessageMediaPhoto):
                        file_name = f'{message.date.strftime("%Y-%m-%d %H-%M-%S")}.jpg'
                        await client.download_media(message.media, f'{download_folder}/{file_name}')
                    elif isinstance(message.media, types.MessageMediaDocument):
                        file_name = f'{message.date.strftime("%Y-%m-%d %H-%M-%S")}.mp4'
                        await client.download_media(message.media, f'{download_folder}/{file_name}')
                # Check if the message contains text
                if message.message is not None:
                    with open(f'{download_folder}/messages/{message.date.strftime("%Y-%m-%d %H-%M-%S")}.txt', 'w',
                              encoding='utf-8') as file:
                        file.write(message.message)
                pbar.update(1)  # update the progress bar for each message downloaded
            except Exception as e:
                print(f'Error occurred while processing message {message.id}: {str(e)}')
                continue


async def main():
    async with TelegramClient('username', api_id, api_hash) as client:
        await client.start()
        # Get the target group
        dialogs = await client(GetDialogsRequest(
            offset_date=None,
            offset_id=0,
            offset_peer='username',
            limit=MESSAGE_LIMIT,
            hash=0
        ))
        group_chat = None
        for dialog in dialogs.chats:
            if dialog.title == group_title:
                group_chat = dialog
                break
        if not group_chat:
            print(f"Could not find group chat with title '{group_title}'")
            await client.disconnect()
            return
        # Download the messages from the group chat
        group_chat = await client.get_messages(group_chat, limit=MESSAGE_LIMIT)
        # Create the download folder if it doesn't exist
        if not os.path.exists(download_folder):
            os.mkdir(download_folder)
        tasks = []
        pbar_dict = {}  # Dictionary to keep track of the progress bars for each task
        for i, chunk in enumerate(chunks(group_chat, semaphore._value)):
            task_id = f'task_{i}'
            pbar_dict[task_id] = tqdm_asyncio(total=len(chunk), desc=task_id)
            tasks.append(download_media_messages(chunk, client, pbar_dict[task_id]))
        await asyncio.gather(*tasks)
        print(f'All media messages from {group_title} have been downloaded to {download_folder}')


if __name__ == '__main__':
    start_time = time.time()
    asyncio.run(main())
    end_time = time.time()
    print(f'Total time taken: {round(end_time - start_time, 2)} seconds')
