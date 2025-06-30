# backend_server.py

from flask import Flask, request, jsonify, render_template
import tensorflow as tf
import numpy as np
import cv2
import base64
import os

# --- 初始化Flask应用 ---
app = Flask(__name__)

# --- 加载所有AI模型 (在应用启动时加载一次) ---
print("[INFO] 正在加载所有AI模型...")
# 全局模型 (我们用它来计算疲劳百分比和检测哈欠)
face_model = load_model('fatigue_detection_transfer_model_v2.h5')
FACE_LABELS = ["fatigue", "normal", "yawning"]
# 眼睛状态模型
eye_model = load_model('eye_state_classifier.h5')
EYE_LABELS = ["closed_eye", "open_eye"]
# OpenCV DNN 人脸检测器
net = cv2.dnn.readNetFromCaffe("deploy.prototxt", "res10_300x300_ssd_iter_140000.caffemodel")
print("[INFO] 所有模型加载完毕。")

# --- 定义API端点 ---
@app.route('/')
def index():
    # 渲染我们的前端页面
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    # 从前端请求中获取JSON数据
    data = request.get_json()
    # 获取base64格式的图片数据
    img_data = base64.b64decode(data['image'].split(',')[1])

    # 将图片数据转换为OpenCV格式
    np_arr = np.frombuffer(img_data, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    # --- 在这里运行您的核心检测逻辑 ---
    # (这部分逻辑与您最终版main.py的while循环内逻辑几乎完全相同)
    (h, w) = frame.shape[:2]
    fatigue_percentage = 0.0
    final_status = "NORMAL"

    blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
    net.setInput(blob)
    detections = net.forward()

    for i in range(0, detections.shape[2]):
        confidence = detections[0, 0, i, 2]
        if confidence > 0.5:
            # 只处理第一个检测到的人脸
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")

            face_crop = frame[startY:endY, startX:endX]
            if face_crop.size > 0:
                # 全局模型预测
                face_resized_global = cv2.resize(face_crop, (100, 100))
                face_preprocessed = tf.keras.applications.resnet50.preprocess_input(face_resized_global)
                face_expanded = np.expand_dims(face_preprocessed, axis=0)
                global_prediction = face_model.predict(face_expanded)[0]

                fatigue_percentage = float((global_prediction[0] + global_prediction[2]) * 100)
                global_label = FACE_LABELS[np.argmax(global_prediction)]

                if global_label == "yawning":
                    final_status = "YAWNING"
                elif global_label == "fatigue":
                     final_status = "FATIGUE"
                else:
                     final_status = "NORMAL"
            break

    # 将结果打包成JSON格式返回给前端
    return jsonify({
        'status': final_status,
        'fatigue_level': fatigue_percentage,
        'yawn_count': 0, # 简化版，可后续实现
        'blink_count': 0 # 简化版，可后续实现
    })

# --- 启动服务器 ---
if __name__ == '__main__':
    # port=os.environ.get("PORT", 5000) 让Render可以动态分配端口
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))