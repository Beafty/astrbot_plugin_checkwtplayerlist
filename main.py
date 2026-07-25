import asyncio
import json
import tempfile
import urllib.request
from pathlib import Path
from datetime import datetime
import base64
from jinja2 import Template
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
import astrbot.api.message_components as Comp
from astrbot.api import AstrBotConfig, logger
from .ocr import OCRHelper
from .api import RoomAPI, ReplayAPI
from .templates import ROOM_TEMPLATE, REPLAY_TEMPLATE, SCORES_TEMPLATE
from .utils import check_room_id, format_api_result, build_room_render_data, check_replay_id, build_replay_render_data, build_scores_render_data

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
        self.replay_api = None

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

    def get_replay_api_url(self):
        try:
            url = self.config.get("replay_api_url", "http://127.0.0.1:25580")
        except AttributeError:
            try:
                url = self.config["replay_api_url"]
            except KeyError:
                url = "http://127.0.0.1:25580"
        return str(url or "http://127.0.0.1:25580").strip()

    def get_replay_api_method(self):
        try:
            method = self.config.get("replay_api_method", "POST")
        except AttributeError:
            try:
                method = self.config["replay_api_method"]
            except KeyError:
                method = "POST"
        return RoomAPI.normalize_method(method)

    def get_replay_use_proxy(self):
        try:
            return bool(self.config.get("replay_use_proxy", False))
        except AttributeError:
            try:
                return bool(self.config["replay_use_proxy"])
            except KeyError:
                return False

    def get_replay_api(self):
        url = self.get_replay_api_url()
        method = self.get_replay_api_method()
        use_proxy = self.get_replay_use_proxy()
        if not url:
            return None
        if (
            self.replay_api is None
            or self.replay_api.url != url.rstrip("/")
            or self.replay_api.method != method
            or self.replay_api.use_proxy != use_proxy
        ):
            self.replay_api = ReplayAPI(url, method, use_proxy)
        return self.replay_api

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
        font_path = (
            Path(__file__).resolve().parent
            / "fonts"
            / "symbols_skyquake.ttf"
        )

        self.skyquake_font_base64 = base64.b64encode(
            font_path.read_bytes()
        ).decode("ascii")

    def parse_message(self, event: AstrMessageEvent):
        images = []
        texts = []
        for m in event.message_obj.message:
            if isinstance(m, Comp.Image):
                images.append(m)
            elif isinstance(m, Comp.Plain):
                text = m.text.strip()
                for prefix in ("/room", "/replay", "/score"):
                    if text.startswith(prefix):
                        text = text[len(prefix):].strip()
                        break
                if text:
                    texts.append(text)
        return images, texts

    def get_t2i_mode(self):
        return "local" if self.config.get("use_local_t2i", False) else "astrbot"

    def get_local_t2i_url(self):
        if not self.config.get("use_local_t2i", False):
            return ""
        try:
            local_t2i_url = self.config.get("local_t2i_url", "")
        except AttributeError:
            local_t2i_url = ""
        return str(local_t2i_url or "").strip()

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
        data["skyquake_font_base64"] = self.skyquake_font_base64
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

    def get_debug_config(self):
        try:
            debug_cfg = self.config.get("debug", {})
        except AttributeError:
            try:
                debug_cfg = self.config["debug"]
            except KeyError:
                debug_cfg = {}
        return debug_cfg if isinstance(debug_cfg, dict) else {}

    def get_debug_save_json(self):
        debug_cfg = self.get_debug_config()
        return bool(debug_cfg.get("save_json", False))

    def get_debug_json_dir(self):
        debug_cfg = self.get_debug_config()
        return str(debug_cfg.get("json_dir", "debug")).strip() or "debug"

    def _save_debug_json(self, result, room_id: str | None = None):
        if result is None:
            return
        if not self.get_debug_save_json() or result.get("state") != "ok":
            return
        try:
            out_dir = Path(__file__).resolve().parent / self.get_debug_json_dir()
            out_dir.mkdir(parents=True, exist_ok=True)

            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_room_id = room_id or "unknown"
            file_path = out_dir / f"{ts}_{safe_room_id}.json"

            with file_path.open("w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存调试 JSON 失败: {e}")

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
        yield event.plain_result(f"识别到房间号{room_id}")
        result = await api.send_room_id(room_id)

        if result is None:
            yield event.plain_result("查询服务器异常")
            return

        self._save_debug_json(result, room_id)

        if isinstance(result, dict) and "state" in result and result.get("state") != "ok":
            yield event.plain_result(f"查询失败: {result.get('state', 'unknown')}")
            return
        yield await self.make_room_result(event, result)

    async def make_replay_result(self, event, result):
        options = {"viewport": {"width": 0, "height": 0}}
        data = build_replay_render_data(result)
        data["skyquake_font_base64"] = self.skyquake_font_base64
        mode = self.get_t2i_mode()

        try:
            if mode == "local":
                html = Template(REPLAY_TEMPLATE).render(**data)
                img_bytes = await asyncio.to_thread(
                    self.render_local_t2i_bytes,
                    html,
                    0,
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

            url = await self.html_render(REPLAY_TEMPLATE, data, options=options)
            return event.image_result(url)
        except Exception as e:
            logger.warning(f"Replay HTML 渲染图片失败: {e}")
            return event.plain_result(f"回放解析完成，但图片渲染失败: {e}")

    async def make_scores_result(self, event, result):
        options = {"viewport": {"width": 0, "height": 0}}
        data = build_scores_render_data(result)
        data["skyquake_font_base64"] = self.skyquake_font_base64
        mode = self.get_t2i_mode()

        try:
            if mode == "local":
                html = Template(SCORES_TEMPLATE).render(**data)
                img_bytes = await asyncio.to_thread(
                    self.render_local_t2i_bytes,
                    html,
                    0,
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

            url = await self.html_render(SCORES_TEMPLATE, data, options=options)
            return event.image_result(url)
        except Exception as e:
            logger.warning(f"Scores HTML 渲染图片失败: {e}")
            return event.plain_result(f"记分板解析完成，但图片渲染失败: {e}")

    @filter.command("replay")
    async def replay(self, event: AstrMessageEvent):
        api = self.get_replay_api()
        if api is None:
            yield event.plain_result("请先在插件配置中填写 Replay API 地址(replay_api_url)")
            return
        images, texts = self.parse_message(event)
        if images and texts:
            yield event.plain_result("不支持混合输入")
            return
        replay_id = None
        if len(images) == 1:
            replay_id = await self.ocr.recognize_replay(images[0].file)
            if replay_id is None:
                yield event.plain_result("未成功识别到回放 ID，请手动输入")
                return
        elif len(texts) == 1:
            replay_id = texts[0]
        else:
            yield event.plain_result("只支持一张完整截图或正确的回放 ID")
            return
        if not check_replay_id(replay_id):
            yield event.plain_result("回放 ID 格式错误（需为 hex 或十进制数字）")
            return
        # 15位hex自动补0
        replay_id = replay_id.strip().lower()
        if all(c in "0123456789abcdef" for c in replay_id) and len(replay_id) == 15:
            replay_id = "0" + replay_id
        yield event.plain_result(f"识别到回放 ID {replay_id}")
        result = await api.query_replay(replay_id)

        if result is None:
            yield event.plain_result("Replay API 服务器异常")
            return

        if isinstance(result, dict) and not result.get("ok"):
            detail = result.get("detail") or result.get("error") or "unknown"
            yield event.plain_result(f"回放解析失败: {detail}")
            return
        yield await self.make_replay_result(event, result)

    @filter.command("score")
    async def score(self, event: AstrMessageEvent):
        api = self.get_replay_api()
        if api is None:
            yield event.plain_result("请先在插件配置中填写 Replay API 地址(replay_api_url)")
            return
        images, texts = self.parse_message(event)
        if images and texts:
            yield event.plain_result("不支持混合输入")
            return
        replay_id = None
        if len(images) == 1:
            replay_id = await self.ocr.recognize_replay(images[0].file)
            if replay_id is None:
                yield event.plain_result("未成功识别到回放 ID，请手动输入")
                return
        elif len(texts) == 1:
            replay_id = texts[0]
        else:
            yield event.plain_result("只支持一张完整截图或正确的回放 ID")
            return
        if not check_replay_id(replay_id):
            yield event.plain_result("回放 ID 格式错误（需为 hex 或十进制数字）")
            return
        # 15位hex自动补0
        replay_id = replay_id.strip().lower()
        if all(c in "0123456789abcdef" for c in replay_id) and len(replay_id) == 15:
            replay_id = "0" + replay_id
        yield event.plain_result(f"识别到回放 ID {replay_id}")
        result = await api.query_scores(replay_id)

        if result is None:
            yield event.plain_result("Replay API 服务器异常")
            return

        if isinstance(result, dict) and not result.get("ok"):
            detail = result.get("detail") or result.get("error") or "unknown"
            yield event.plain_result(f"记分板解析失败: {detail}")
            return
        yield await self.make_scores_result(event, result)

    async def terminate(self):
        pass
