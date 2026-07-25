import json
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


class ReplayAPI:
    def __init__(self, url="http://127.0.0.1:25580", method="POST", use_proxy=False):
        self.url = url.rstrip("/")
        self.method = method.upper()
        self.use_proxy = use_proxy

    async def _request(self, endpoint, replay_id):
        url = f"{self.url}{endpoint}"
        logger.info(f"查询回放 {endpoint}: {replay_id}")
        try:
            timeout = aiohttp.ClientTimeout(total=600, sock_read=120)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                body = {"id": replay_id}
                if self.use_proxy:
                    body["proxy"] = True
                async with session.request(
                    self.method,
                    url,
                    json=body,
                ) as response:
                    if response.status == 404:
                        logger.warning(f"回放不存在: {replay_id}")
                        return {"ok": False, "error": "not_found", "detail": "回放不存在于 CDN"}
                    if response.status != 200:
                        logger.error(f"Replay API 请求失败: HTTP {response.status}")
                        return None

                    content_type = response.headers.get("Content-Type", "")
                    if "x-ndjson" in content_type:
                        result = None
                        buffer = b""
                        async for chunk in response.content.iter_chunked(4096):
                            buffer += chunk
                            while b"\n" in buffer:
                                line, buffer = buffer.split(b"\n", 1)
                                line = line.strip()
                                if not line:
                                    continue
                                try:
                                    data = json.loads(line)
                                except json.JSONDecodeError:
                                    continue
                                if "progress" in data:
                                    logger.info(f"下载进度: {data['progress']} ({data['size']} bytes, {data['src']})")
                                elif "ok" in data:
                                    result = data
                        return result
                    else:
                        result = await response.json(content_type=None)
                        if not isinstance(result, dict):
                            logger.error(f"Replay API 响应格式异常: {type(result).__name__}")
                            return None
                        return result
        except aiohttp.ClientError as e:
            logger.error(f"Replay API 连接异常: {e}")
            return None
        except Exception as e:
            logger.error(f"Replay API 未知异常: {e}")
            return None

    async def query_replay(self, replay_id):
        return await self._request("/replay", replay_id)

    async def query_scores(self, replay_id):
        return await self._request("/scores", replay_id)