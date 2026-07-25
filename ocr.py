import asyncio
import re
import cv2
from astrbot.api import logger
from paddleocr import PaddleOCR

class OCRHelper:
    def __init__(self):
        self.ocr = None
        self.lock = asyncio.Lock()
    async def initialize(self):
        try:
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

    def extract_replay_id(self, text: str):
        result = re.findall(r"[0-9a-f]{15}", text)
        return result[0] if result else None

    def _run_sync(self, image_path, extractor=None):
        if extractor is None:
            extractor = self.extract_room_id
        if self.ocr is None:
            return None
        img = cv2.imread(image_path)
        if img is None:
            return None
        h, w, _ = img.shape
        cropped_img = img[
            int(h * 0.98):h,
            0:int(w * 0.3)
        ]
        result = self.ocr.predict(cropped_img)
        rec_texts = result[0].get(
            "rec_texts",
            []
        )
        for text in rec_texts:
            extracted = extractor(text)
            if extracted:
                return extracted
        return None

    async def recognize(self, image_path):
        async with self.lock:
            return await asyncio.to_thread(
                self._run_sync,
                image_path
            )

    async def recognize_replay(self, image_path):
        async with self.lock:
            return await asyncio.to_thread(
                self._run_sync,
                image_path,
                self.extract_replay_id
            )