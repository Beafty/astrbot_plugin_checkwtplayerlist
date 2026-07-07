import aiohttp
from astrbot.api import logger
class RoomAPI:
    def __init__(self, url):
        self.url = url
    async def send_room_id(self, room_id):
        logger.info(f"发送房间ID: {room_id}")
        data = {
            "room_id": room_id
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.url,
                    json=data,
                    timeout=10
                ) as response:
                    if response.status != 200:
                        logger.error(f"API请求失败: {response.status}")
                        return None
                    return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"API链接异常: {e}")
            return None
        except Exception as e:
            logger.error(f"API未知异常: {e}")
            return None