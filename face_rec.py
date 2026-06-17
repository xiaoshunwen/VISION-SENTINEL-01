# face_rec.py
import os
import cv2
import numpy as np
from insightface.app import FaceAnalysis
import config

class FaceEngine:
    def __init__(self):
        # 💡 这里直接读取 config 里的 DirectML 加速提供者，完美激活你的 780M 核显
        self.app = FaceAnalysis(name='antelopev2', providers=config.EP_PROVIDERS)
        self.app.prepare(ctx_id=0, det_size=config.FACE_DET_SIZE)
        self.known_faces = self._load_known_faces()

    def _load_known_faces(self):
        """扫描 faces 文件夹，提取并缓存已知人脸的特征向量"""
        known = {}
        if not os.path.exists(config.FACES_DIR):
            os.makedirs(config.FACES_DIR)
        for file in os.listdir(config.FACES_DIR):
            if file.endswith(('.jpg', '.png', '.jpeg')):
                name = os.path.splitext(file)[0]
                img = cv2.imread(os.path.join(config.FACES_DIR, file))
                if img is not None:
                    faces = self.app.get(img)
                    if len(faces) > 0:
                        known[name] = faces[0].normed_embedding
        return known

    def detect_faces(self, frame):
        """封装检测接口"""
        return self.app.get(frame)