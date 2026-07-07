from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import astrbot.api.message_components as Comp
import asyncio
import re

@register("checkwtplayerlist", "Beafty_win", "一个用于战雷对局查询的AstrBot插件", "0.0.1")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.ocr = None

    async def initialize(self):
        try:
            from paddleocr import PaddleOCR
            self.ocr = PaddleOCR(
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
                engine="paddle",
            )
            logger.info("PaddleOCR初始化成功")
        except Exception as e:
            logger.error(f"PaddleOCR初始化失败: {e}")

    def extract_room_id(self, text: str):
        result = re.findall(r"[0-9a-f]{15}", text)
        return result[0] if result else None

    def _run_ocr_sync(self, image_path):
        import cv2
        if self.ocr is None:
            return "OCR未初始化"
        img = cv2.imread(image_path)
        if img is None:
            return "图片读取失败"
        h, w, _ = img.shape
        cropped_img = img[int(h * 0.98):h, 0:int(w * 0.3)]
        result = self.ocr.predict(cropped_img)
        rec_texts = result[0].get("rec_texts", [])
        for text in rec_texts:
            room_id = self.extract_room_id(text)
            if room_id:
                return room_id
        return "未成功识别到房间ID,请手动输入房间号"

    async def run_ocr(self, image_path):
        return await asyncio.to_thread(self._run_ocr_sync, image_path)

    @filter.command("room")
    async def room(self, event: AstrMessageEvent):
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
        if images and texts:
            yield event.plain_result("不支持混合输入")
            return
        if len(images) == 1:
            room_id = await self.run_ocr(images[0].file)
            yield event.plain_result(room_id)
            return
        if len(texts) == 1:
            room_id = texts[0]
            if len(room_id) == 15:
                if all(c in "0123456789abcdef" for c in room_id):
                    yield event.plain_result(room_id)
                else:
                    yield event.plain_result("房间号应为全小写16进制")
            else:
                yield event.plain_result("房间号长度错误")
            return
        yield event.plain_result("只支持一张完整截图或正确的房间号")

    @filter.command("test")
    async def test_(self, event: AstrMessageEvent):
        platforms = self.context.platform_manager.get_insts()
        logger.info(f"当前平台列表: {platforms}")

    async def terminate(self):
        pass