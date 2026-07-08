import json
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
import astrbot.api.message_components as Comp
from astrbot.api import AstrBotConfig
from .ocr import OCRHelper
from .api import RoomAPI
from .utils import check_room_id

@register(
    "checkwtplayerlist",
    "Beafty_win",
    "一个用于战雷对局查询的AstrBot插件",
    "0.0.1"
)
class MyPlugin(Star):
    def __init__(self, context: Context,config: AstrBotConfig):
        super().__init__(context)
        self.ocr = OCRHelper()
        self.config = config
        self.api = None

    def get_api_url(self):
        try:
            api_url = self.config.get("api_url", "")
        except AttributeError:
            try:
                api_url = self.config["api_url"]
            except KeyError:
                api_url = ""
        return str(api_url or "").strip()

    def get_api_method(self):
        try:
            api_method = self.config.get("api_method", "POST")
        except AttributeError:
            try:
                api_method = self.config["api_method"]
            except KeyError:
                api_method = "POST"
        return RoomAPI.normalize_method(api_method)

    def get_api_param(self):
        try:
            api_param = self.config.get("api_param", "getroom")
        except AttributeError:
            try:
                api_param = self.config["api_param"]
            except KeyError:
                api_param = "getroom"
        return str(api_param or "getroom").strip() or "getroom"

    def get_api(self):
        api_url = self.get_api_url()
        api_method = self.get_api_method()
        api_param = self.get_api_param()
        if not api_url:
            return None
        if (
            self.api is None
            or self.api.url != api_url
            or self.api.method != api_method
            or self.api.param_name != api_param
        ):
            self.api = RoomAPI(api_url, api_method, api_param)
        return self.api
    async def initialize(self):
        await self.ocr.initialize()
    def parse_message(self, event: AstrMessageEvent):
        images = []
        texts = []
        for m in event.message_obj.message:
            if isinstance(m, Comp.Image):
                images.append(m)
            elif isinstance(m, Comp.Plain):
                text = m.text.strip()
                if text.startswith("/room"):
                    text = text[5:].strip()
                if text:
                    texts.append(text)
        return images, texts
    def format_api_result(self, result):
        task = result.get("task", "")
        data = result.get("data")
        if isinstance(data, dict):
            room_id = data.get("roomId") or data.get("room_id") or data.get("id") or ""
            lines = ["查询成功"]
            if task:
                lines.append(f"任务: {task}")
            if room_id:
                lines.append(f"房间ID: {room_id}")
            return "\n".join(lines)

        text = json.dumps(result, ensure_ascii=False)
        return text if len(text) <= 1500 else text[:1500] + "\n...(响应过长，已截断)"
    @filter.command("room")
    async def room(self,event: AstrMessageEvent):
        api = self.get_api()
        if api is None:
            yield event.plain_result("请先在插件配置中填写查询服务器地址（api_url）")
            return
        images, texts = self.parse_message(event)
        if images and texts:
            yield event.plain_result("不支持混合输入")
            return
        room_id = None
        if len(images) == 1:
            room_id = await self.ocr.recognize(images[0].file)
            if room_id is None:
                yield event.plain_result("未成功识别到房间ID,请手动输入房间号")
                return
        elif len(texts) == 1:
            room_id = texts[0]
        else:
            yield event.plain_result("只支持一张完整截图或正确的房间号")
            return
        if not check_room_id(room_id):
            yield event.plain_result("房间号格式错误")
            return
        result = await api.send_room_id(room_id)
        if result is None:
            yield event.plain_result("查询服务器异常")
            return
        if result.get("state") != "ok":
            yield event.plain_result(f"查询失败: {result.get('state', 'unknown')}")
            return
        yield event.plain_result(self.format_api_result(result))
    async def terminate(self):
        pass

