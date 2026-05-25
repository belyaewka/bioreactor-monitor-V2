import logging
import json
import time
import aiohttp
import asyncio

from gpiozero import Button

from config import BIOREACTOR_TUPLE, BOUNCE_TIME, DUONING_API_TIMEOUT


logger = logging.getLogger(__name__)


class BaseBioreactor:
    def __init__(self, name: str, alarm_flag: bool):
        self.name: str = name
        self.alarm_flag: bool = alarm_flag

        # alarm messages for each bioreactor
        self.alarm_on_msg = f'\U0001F198 Bioreactor {self.name} alarm activated!'
        self.alarm_off_msg = f'\U00002705 Bioreactor {self.name} alarms cleared.'
    
    def __str__(self) -> str:
        return f'Bioreactor(name={self.name}'
    
    @staticmethod
    def event_reg_time() -> str:
        return f'\nEvent registered at: {time.strftime("%d-%m-%Y %H:%M:%S")}'

    
    async def alarm_processor(self):
        raise NotImplementedError('Subclass must implement this method')
    


class RelayBioreactor(BaseBioreactor):
    def __init__(self, name: str, pin: Button, alarm_flag: bool = False):
        super().__init__(name, alarm_flag)
        self.pin = pin
    

    def __str__(self) -> str:
        return f'Bioreactor(name={self.name}, pin={self.pin})'
    
    def check_alarm_state(self) -> str | None:
        """check alarm flag and pin state, returns string with alarm or None
        Warning - it's blocking function, cannot use in async event loop as is"""

        # initial state, function will return None if
        # any of two conditions (steps) isn't True
        processed_message = None

        logger.info(f"{time.strftime("%d-%m-%Y %H:%M:%S")} Bioreactor {self.name}, pin state = {self.pin.value}, alarm_flag = {self.alarm_flag}")

        # 1 first step - alarm activation: check pin and set alarm flag to True
        if self.pin.value == 1 and not self.alarm_flag: # button is pressed 
            self.alarm_flag = True
            processed_message = self.alarm_on_msg + self.event_reg_time()
            logger.error(self.alarm_on_msg)

        # 2 second step - alarm deactivation: check pin and set alarm flag to False
        if self.pin.value == 0 and self.alarm_flag: # button is released
            self.alarm_flag = False
            processed_message = self.alarm_off_msg + self.event_reg_time()
            logger.info(self.alarm_off_msg)

      
        return processed_message


    async def alarm_processor(self) -> str | None:
        "async method to run blocking func"
        result = await asyncio.to_thread(self.check_alarm_state)
        return result
 

class ApiTypeBioreactor(BaseBioreactor):
    def __init__(self, name: str, uri: str, alarm_flag: bool = False):
        super().__init__(name, alarm_flag)
        self.uri = uri
    

    def __str__(self):
        return f'Bioreactor(name={self.name}, uri={self.uri})'
    

    async def get_api_data(self) -> dict:
        result_dict = {}        
                     
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=DUONING_API_TIMEOUT)) as session:
                async with session.get(url = self.uri) as api_response:               
                    if api_response.status == 200:
                        logger.info(f"Succesfuly received data from API, status code = {api_response.status}")
                        result_dict = await api_response.json() 
                        
        except Exception as e:
                logger.error(f"An error occured during request to API, error = {e.__class__.__name__}")
        
        return result_dict 
    
    
    async def alarm_processor(self) -> str | None:
        """Try to get alarm data, returns string with alarm or None (if request fail or No alarms)"""
        
        # initial values
        processed_message = None      

        # get data from bioreactor API
        received_data: dict = await self.get_api_data()
        
        # check if result dict is not empty and get data from it. Else, there's nothing to do, we can not process alarms.
        if received_data:
            comal_state: int = received_data['com_al']
            active_alarms: str = received_data['active_alarms']
        else:
            logger.error("Cannot get real alarm data- comal_state and active_alarms. Alarm processor cannot continue")
            return
   
        # 1 first step - alarm activation: check <com_al> and set alarm flag to True
        if comal_state == 1 and not self.alarm_flag: # alarm activated 
            self.alarm_flag = True
            processed_message = self.alarm_on_msg + f"\nActive alarms: {active_alarms}. " + self.event_reg_time()
            logger.error(self.alarm_on_msg + f"Active alarms: {active_alarms}")

        # 2 second step - alarm deactivation: check <com_al> and set alarm flag to False
        if comal_state == 0 and self.alarm_flag: # alarm deactivated
            self.alarm_flag = False
            processed_message = self.alarm_off_msg + self.event_reg_time()
            logger.info(self.alarm_off_msg)

        return processed_message
  


def create_bioreactor_list(device_list: tuple[dict[str, int],...]) -> list:
    """takes bioreactor tuple from config and return tuple with objects of bioreactors"""

    bioreactors_list: list = []

    for device in device_list:

        match device['type']:

            case 'dry_contact':
                alarm_pin = Button(device['pin'], pull_up = True, bounce_time = BOUNCE_TIME)
                bioreac_obj = RelayBioreactor(name=device['name'], pin=alarm_pin)
            
            case 'opc_ua-api':
                bioreac_obj = ApiTypeBioreactor(name=device['name'], uri=device['uri'])

        bioreactors_list.append(bioreac_obj)

    logger.info('Bioreactor list was successfully created')

    return bioreactors_list


if __name__ == '__main__':
    async def test():
            
        # test create list
        bioreactors = create_bioreactor_list(BIOREACTOR_TUPLE)
        print(bioreactors)

        res = await bioreactors[-1].alarm_processor()
        print(res)

    asyncio.run(test())

 
