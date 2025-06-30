// 当网页完全加载后执行
document.addEventListener('DOMContentLoaded', () => {
    // 获取HTML中的各个元素
    const video = document.getElementById('webcam-feed');
    const canvas = document.getElementById('canvas');
    const context = canvas.getContext('2d');

    const statusEl = document.getElementById('status');
    const fatigueLevelEl = document.getElementById('fatigue-level');
    const yawnCountEl = document.getElementById('yawn-count');
    const blinkCountEl = document.getElementById('blink-count');

    let isDetecting = false;

    // 1. 访问用户摄像头
    const startWebcam = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            video.srcObject = stream;
            video.onloadedmetadata = () => {
                video.play();
                isDetecting = true; // 摄像头成功启动后才开始检测
                statusEl.textContent = "检测中...";
                statusEl.style.color = 'blue';
            };
        } catch (error) {
            console.error("摄像头访问出错!", error);
            statusEl.textContent = "摄像头访问出错!";
            statusEl.style.color = 'red';
        }
    };

    // 启动摄像头
    startWebcam();

    // 2. 定时向后端发送图像并更新UI
    // 每秒发送约2次图像进行检测（500毫秒）
    setInterval(() => {
        // 如果摄像头未启动或检测已停止，则不发送请求
        if (!isDetecting || video.paused || video.ended) {
            return;
        }

        // 将当前视频帧绘制到隐藏的canvas上
        context.drawImage(video, 0, 0, 640, 480);

        // 从canvas获取base64格式的图片数据
        const imageData = canvas.toDataURL('image/jpeg', 0.8); // 0.8表示图片质量

        // 3. 使用fetch API向后端发送数据
        fetch('/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ image: imageData })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // 4. 接收到后端返回的数据后，更新界面
            // console.log('从后端接收到:', data); // 调试时可以取消注释
            statusEl.textContent = data.status || "无";
            fatigueLevelEl.textContent = (data.fatigue_level || 0).toFixed(2) + '%';
            yawnCountEl.textContent = data.yawn_count || 0;
            blinkCountEl.textContent = data.blink_count || 0;

            // 根据状态改变颜色
            if (data.status && data.status.includes('FATIGUE')) {
                statusEl.style.color = 'red';
            } else if (data.status && data.status.includes('YAWNING')) {
                statusEl.style.color = 'orange';
            } else {
                statusEl.style.color = 'green';
            }
        })
        .catch(error => {
            console.error('与后端通信错误:', error);
            statusEl.textContent = "与后端通信失败";
            statusEl.style.color = 'red';
        });

    }, 500); // 每500毫秒执行一次
});