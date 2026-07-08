import aiohttp
from astrbot.api import logger


class RoomAPI:
    def __init__(self, url, method="POST", param_name="getroom"):
        self.url = url
        self.method = self.normalize_method(method)
        self.param_name = str(param_name or "getroom").strip() or "getroom"

    @staticmethod
    def normalize_method(method):
        method = str(method or "POST").strip().upper()
        return method if method in {"GET", "POST", "PUT", "PATCH", "DELETE"} else "POST"

    async def send_room_id(self, room_id):
        logger.info(f"发送房间ID: {room_id}")
        data = {
            self.param_name: room_id
        }
        try:
            async with aiohttp.ClientSession() as session:
                request_kwargs = {"params": data} if self.method == "GET" else {"json": data}
                async with session.request(
                    self.method,
                    self.url,
                    timeout=10,
                    **request_kwargs
                ) as response:
                    if response.status != 200:
                        logger.error(f"API请求失败: HTTP {response.status}")
                        return None

                    result = await response.json(content_type=None)
                    if not isinstance(result, dict):
                        logger.error(f"API响应格式异常: {type(result).__name__}")
                        return None
                    return result
        except aiohttp.ClientError as e:
            logger.error(f"API连接异常: {e}")
            return None
        except Exception as e:
            logger.error(f"API未知异常: {e}")
            return None