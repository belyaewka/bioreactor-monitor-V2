"""Simple notification service for bioreactor class"""
import logging
import aiohttp
from config import URL_TO_SEND, DELAY_TO_SEND, TELEGRAM_API_TIMEOUT, URL_FOR_GOTIFY, GF_APP_TOKEN
import asyncio
from gotify import AsyncGotify

logger = logging.getLogger(__name__)

async def message_to_gotify(message: str,):
    logger.debug("Function message to GOTIFY started")
    try:
        async with AsyncGotify(
            base_url = URL_FOR_GOTIFY,
            app_token=GF_APP_TOKEN,
        ) as gotify:
            await gotify.create_message(
                message,
                title="Bioreactors Alerts",
                priority=10,
            )
    except Exception as e:
        logger.error(f"Error occured while sending to Gotify, error = {e.__class__.__name__}")

# 
async def message_to_telegram(message: str, api_timeout: int = TELEGRAM_API_TIMEOUT) -> None:
    """send message via telegram API.
       Bot  send to telegram chat"""
    
    url = URL_TO_SEND + message
    print(url)
    logger.debug("Function message to telegram started")
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=api_timeout)) as session:       
            async with session.post(url) as response:               
                if response.status == 200:
                    logger.info(f'Message was successfully sent. Response = {response.status}')
                else:
                    logger.warning(f'Response code (is not 200) = {response.status}')
 

    except Exception as e:
        logger.error(f"An error occured while sending to Telegram, error = {e.__class__.__name__}")
        
    finally:
        await session.close()


async def notification_worker(queue: asyncio.Queue) -> None:
    """Simple worker to send messages with delay"""
    logger.debug("Notification worker started")
    while True:        
        try:
            next_message = await queue.get()
            if next_message:
                logger.info('Notification worker received new message from FIFO queue and sent it for sending')
                print(next_message)
                await message_to_telegram(next_message)
                await message_to_gotify(next_message)
                await asyncio.sleep(DELAY_TO_SEND)
        except KeyboardInterrupt:
            break
        except:
            continue

async def test(msg: str):
    url = URL_TO_SEND + msg
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:       
        async with session.post(url) as response:               
            if response.status == 200:
                logger.info(f'Message was successfully sent. Response = {response.status}')
            else:
                logger.warning(f'Response code (is not 200) = {response.status}')
                               
if __name__ == '__main__':
    asyncio.run(message_to_gotify('Alarm test'))
    