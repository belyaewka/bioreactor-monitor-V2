from queue import Queue
from bioreactor import create_bioreactor_list
from notifications import notification_worker
import threading
from time import sleep
import logging

from config import BIOREACTOR_TUPLE, MAIN_LOOP_DELAY

# logging setup
logging.basicConfig(filename='monitor.log',
                    format='%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s | %(message)s',
                    datefmt='%d-%m-%Y %H:%M:%S',
                    level=logging.DEBUG,
                    encoding='utf-8'
                    )

# logger init
logger = logging.getLogger('main')


def change_state(device_list):
    for device in device_list:
        device.pin.value = not device.pin.value


def main():
    logger.info('Main program started')

    # init bioreactors list
    bioreactors = create_bioreactor_list(BIOREACTOR_TUPLE)

    # queue init
    message_queue = Queue()

    # separate thread for notification worker
    worker_thread = threading.Thread(target=notification_worker,
                                     args=(message_queue,),
                                     daemon=True)
    worker_thread.start()

    # main loop =======================================
    while True:
        try:
            for bioreactor in bioreactors:
                # check alarms of each device
                if msg := bioreactor.alarm_processor():
                    message_queue.put(msg)

            sleep(MAIN_LOOP_DELAY)

        except KeyboardInterrupt:
            logger.info('Keyboard Interrupt, main program end')
            exit()

        except Exception as e:
            logger.error(f'Unknown error during main loop {e}')
            continue
    # end of main loop ===============================


if __name__ == '__main__':
    main()
