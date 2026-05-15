import asyncio
from bioreactor import create_bioreactor_list
from notifications import notification_worker
import logging
from collections.abc import AsyncIterator

from config import BIOREACTOR_TUPLE, MAIN_LOOP_DELAY

# logging setup
logging.basicConfig(filename='monitor.log',
                    format='%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s | %(message)s',
                    datefmt='%d-%m-%Y %H:%M:%S',
                    level=logging.DEBUG,
                    encoding='utf-8'
                    )

# logger init
logger = logging.getLogger(__name__)

 # init bioreactors list
bioreactors = create_bioreactor_list(BIOREACTOR_TUPLE)

async def async_bioreactor_generator(bioreactor_list: list) -> AsyncIterator:
    for item in bioreactor_list:
        yield item


async def bioreactor_checker(queue: asyncio.Queue):
    logger.debug("Bioreactor checker started")
    while True:
        try:
            async for bioreactor in async_bioreactor_generator(bioreactors):
                # check alarms of each device
                print(bioreactor)
                if msg := await bioreactor.alarm_processor():
                    print(msg)
                    await queue.put(msg)

            await asyncio.sleep(MAIN_LOOP_DELAY)
            
        except KeyboardInterrupt:
            logger.info('Keyboard Interrupt, main program end')
            exit()

        except Exception as e:
            logger.error(f'Unknown error during main loop {e}')
            continue


async def main():
    logger.info('Main program started')

     # queue init
    message_queue = asyncio.Queue()
    print(message_queue)

    await asyncio.gather(
        bioreactor_checker(queue=message_queue),
        notification_worker(queue=message_queue)
    )

   

if __name__ == '__main__':
    asyncio.run(main())
