"""Simple notification service for bioreactor class"""
import logging
import requests
from config import API_TIMEOUT, URL_TO_SEND, DELAY_TO_SEND
from queue import Queue
from time import sleep

logger = logging.getLogger(__name__)


def message_to_telegram(message: str | None, api_timeout: int = API_TIMEOUT) -> None:
    """send message via telegram API.
       Bot  send to telegram chat"""

    try:
        url = URL_TO_SEND + message
        r = requests.post(url, timeout=api_timeout)

        if r.status_code == 200:
            logger.info(f'Message was successfully sent. Response = {r.status_code}')
        else:
            logger.warning(f'Response code (is not 200) = {r.status_code}')

    except requests.exceptions.Timeout:
        logger.error("Telegram API request timeout")
    except requests.exceptions.ConnectionError:
        logger.error("Network error while sending to Telegram")
    except Exception as e:
        logger.error(f"Unable to send notification. Unexpected error during sending message: {e}")


def notification_worker(queue: Queue) -> None:
    """Simple worker to send messages with delay"""
    while True:
        sleep(DELAY_TO_SEND)  # delay between two messages to Telegram API
        try:
            next_message = queue.get()
            if next_message:
                logger.info('Notification worker received new message from FIFO queue and sent it for sending')
                message_to_telegram(next_message)
        except KeyboardInterrupt:
            break
        except:
            continue


if __name__ == '__main__':
    pass
