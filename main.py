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

    def get_api(self):
        api_url = self.get_api_url()
        if not api_url:
            return None
        if self.api is None or self.api.url != api_url:
            self.api = RoomAPI(api_url)
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
        yield event.plain_result(str(result))
    async def terminate(self):
        pass

