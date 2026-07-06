from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import astrbot.api.message_components as Comp


@register("checkwtplayerlist", "Beafty_win", "一个用于战雷对局查询的AstrBot插件", "0.0.1")
class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.ocr = None
    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        from paddleocr import PaddleOCR
        self.ocr = PaddleOCR(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            engine="paddle",
        )
    def extract_room_id(self, text: str):
        import re
        matches = re.findall(
            r"[0-9a-f]{15}",
            text
        )
        if matches:
            return matches[0]
        return None
    def run_ocr(self, image_path):
        import cv2
        img = cv2.imread(image_path)
        if img is None:
            return "图片读取失败"
        h, w, c = img.shape
        ymin, ymax = int(h * 0.98), h
        xmin, xmax = 0, int(w * 0.3)
        cropped_img = img[ymin:ymax, xmin:xmax]
        result = self.ocr.predict(cropped_img)
        data = result[0]
        rec_texts = data.get("rec_texts", [])
        logger.info(rec_texts)
        if not rec_texts:
            return "未识别到内容"
        for text in rec_texts:
            room_id = self.extract_room_id(text)
            if room_id:
                return room_id
        return "未成功识别到房间ID,请手动输入文字"
    # 注册指令的装饰器。指令名为 room。注册成功后，发送 `/room` 就会触发这个指令!`
    @filter.command("room")
    async def room(self, event: AstrMessageEvent):
        chain = event.message_obj.message
        images = []
        texts = []
        for m in chain:
            if isinstance(m, Comp.Image):
                images.append(m)
            elif isinstance(m, Comp.Plain):
                t = m.text.strip()
                if t.startswith("/room"):
                    t = t.replace("/room", "", 1).strip()
                if t:
                    texts.append(t)
        if len(images) > 0 and len(texts) > 0:
            yield event.plain_result("不支持混合输入")
            return
        if len(images) == 1:
            room_id = self.run_ocr(images[0].file)
            yield event.plain_result(room_id)
            return
        if len(texts) > 0 and len(texts) < 16:
            yield event.plain_result(" ".join(texts))
            return
        yield event.plain_result("只支持一张完整截图或正确的房间号")
    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
