# from gpiozero import Button
import logging
from config import BIOREACTOR_TUPLE
import time

logger = logging.getLogger(__name__)


class Button:
    """temporary simple mock for Button class from gpiozero"""

    def __init__(self, pin, pull_up=True, bounce_time=5.0):
        self.pin = pin
        self.value = False  # logic inversion. When HI level -> No alarm signal
        self.pull_up = pull_up
        self.bounce_time = bounce_time

    def __str__(self):
        return f'Button({self.pin}, {self.value})'


class Bioreactor:
    def __init__(self, name: str, pin: Button, alarm_flag: bool = False):
        self.name = name
        self.pin = pin
        # self.logger = logger
        self.alarm_flag = alarm_flag

        # alarm messages for each bioreactor
        self.alarm_on_msg = f'\U0001F198 Bioreactor {self.name} common alarm activated !'
        self.alarm_off_msg = f'\U00002705 Bioreactor {self.name} alarm cleared.'

    def __str__(self):
        return f'Bioreactor(name={self.name}, pin={self.pin})'

    def alarm_processor(self) -> str | None:
        """check alarm flag and pin state, sends notifications."""

        # initial state, function will return None if
        # any of two conditions (steps) isn't True
        processed_message = None

        # time registration string
        event_reg_time = f'\nEvent registration time: {time.strftime("%d-%m-%Y %H:%M:%S")}'

        # 1 first step - alarm activation: check pin and set alarm flag to True
        if self.pin.value == 0 and not self.alarm_flag:
            self.alarm_flag = True
            processed_message = self.alarm_on_msg + event_reg_time
            logger.error(self.alarm_on_msg)

        # 2 second step - alarm deactivation: check pin and set alarm flag to False
        if self.pin.value == 1 and self.alarm_flag:
            self.alarm_flag = False
            processed_message = self.alarm_off_msg + event_reg_time
            logger.info(self.alarm_off_msg)

        return processed_message


def create_bioreactor_list(device_list: tuple[dict]) -> tuple:
    """takes bioreactor tuple from config and return tuple with objects of Bioreactor class  """

    result = (Bioreactor(name=name, pin=Button(pin)) for device
              in device_list for name, pin in device.items())

    logger.info('Bioreactor list was successfully created')

    return tuple(result)


if __name__ == '__main__':
    # test create list
    bioreactors = create_bioreactor_list(BIOREACTOR_TUPLE)

