import asyncio
import json
import tempfile
import urllib.request
from jinja2 import Template
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
import astrbot.api.message_components as Comp
from astrbot.api import AstrBotConfig, logger
from .ocr import OCRHelper
from .api import RoomAPI
from .templates import ROOM_TEMPLATE
from .utils import check_room_id,format_api_result,build_room_render_data

@register(
    "checkwtplayerlist",
    "Beafty_win",
    "一个用于战雷对局查询的 AstrBot 插件",
    "0.0.1"
)
class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
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

    

    def get_t2i_mode(self):
        try:
            mode = self.config.get("t2i_mode", "astrbot")
        except AttributeError:
            try:
                mode = self.config["t2i_mode"]
            except KeyError:
                mode = "astrbot"
        return str(mode or "astrbot").strip().lower()

    def get_local_t2i_url(self):
        try:
            url = self.config.get("local_t2i_url", "http://127.0.0.1:7778/text2img")
        except AttributeError:
            try:
                url = self.config["local_t2i_url"]
            except KeyError:
                url = "http://127.0.0.1:7778/text2img"
        return str(url or "").strip()

    def render_local_t2i_bytes(self, html: str, width: int, height: int | None = None):
        url = self.get_local_t2i_url()
        payload_data = {
            "html": html,
            "width": width,
        }
        if height is not None:
            payload_data["height"] = height

        payload = json.dumps(payload_data).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.read()

    async def make_room_result(self, event, result):
        options = {"viewport": {"width": 1180, "height": 760}}
        data = build_room_render_data(result)
        mode = self.get_t2i_mode()

        try:
            if mode == "local":
                html = Template(ROOM_TEMPLATE).render(**data)
                img_bytes = await asyncio.to_thread(
                    self.render_local_t2i_bytes,
                    html,
                    1180,
                    None,
                )
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
                try:
                    tmp.write(img_bytes)
                    tmp.close()
                    return event.image_result(tmp.name)
                finally:
                    try:
                        tmp.close()
                    except Exception:
                        pass

            url = await self.html_render(ROOM_TEMPLATE, data, options=options)
            return event.image_result(url)
        except Exception as e:
            logger.warning(f"HTML 渲染图片失败: {e}")
            return event.plain_result(format_api_result(result))

    @filter.command("room")
    async def room(self, event: AstrMessageEvent):
        api = self.get_api()
        if api is None:
            yield event.plain_result("请先在插件配置中填写查询服务器地址(api_url)")
            return
        images, texts = self.parse_message(event)
        if images and texts:
            yield event.plain_result("不支持混合输入")
            return
        room_id = None
        if len(images) == 1:
            room_id = await self.ocr.recognize(images[0].file)
            if room_id is None:
                yield event.plain_result("未成功识别到房间ID，请手动输入房间号")
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
        if isinstance(result, dict) and "state" in result and result.get("state") != "ok":
            yield event.plain_result(f"查询失败: {result.get('state', 'unknown')}")
            return
        yield await self.make_room_result(event, result)

    async def terminate(self):
        pass
