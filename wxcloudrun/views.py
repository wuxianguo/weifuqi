from datetime import datetime
from flask import render_template, request, jsonify
from run import app
from wxcloudrun.dao import delete_counterbyid, query_counterbyid, insert_counter, update_counterbyid
from wxcloudrun.model import Counters
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import requests
import time
import logging

logging.basicConfig(
    filename='server.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s'
)


@app.route('/')
def index():
    """
    :return: 返回index页面
    """
    return render_template('index.html')


@app.route('/api/count', methods=['POST'])
def count():
    """
    :return:计数结果/清除结果
    """

    # 获取请求体参数
    params = request.get_json()

    # 检查action参数
    if 'action' not in params:
        return make_err_response('缺少action参数')

    # 按照不同的action的值，进行不同的操作
    action = params['action']

    # 执行自增操作
    if action == 'inc':
        counter = query_counterbyid(1)
        if counter is None:
            counter = Counters()
            counter.id = 1
            counter.count = 1
            counter.created_at = datetime.now()
            counter.updated_at = datetime.now()
            insert_counter(counter)
        else:
            counter.id = 1
            counter.count += 1
            counter.updated_at = datetime.now()
            update_counterbyid(counter)
        return make_succ_response(counter.count)

    # 执行清0操作
    elif action == 'clear':
        delete_counterbyid(1)
        return make_succ_empty_response()

    # action参数错误
    else:
        return make_err_response('action参数错误')


@app.route('/api/count', methods=['GET'])
def get_count():
    """
    :return: 计数的值
    """
    counter = Counters.query.filter(Counters.id == 1).first()
    return make_succ_response(0) if counter is None else make_succ_response(counter.count)


@app.route('/api/generate', methods=['POST'])
def generate_image():
    """
    :return: 生成图片的base64字符串
    """
    params = request.get_json()
    scene = params.get('scene', '')
    keywords = params.get('keywords', '')
    template = params.get('template', '')
    scene_name = params.get('scene_name', '')
    template_name = params.get('template_name', '')

    # 拼接prompt
    prompt = f"{scene_name}，{template_name}，关键词：{keywords}"

    try:
        img_base64 = generate_doubao_image(prompt)
        return make_succ_response({"image_base64": img_base64})
    except Exception as e:
        return make_err_response(str(e))


def generate_doubao_image(prompt):
    DOUBAO_API_KEY = "f5bfd631-054f-4d92-8d83-6552830cd68d"
    DOUBAO_SUBMIT_URL = "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks"
    DOUBAO_RESULT_URL = "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks/{}"

    # 1. 提交生成任务
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DOUBAO_API_KEY}"
    }
    payload = {
        "model": "doubao-seedance-1-0-pro-250528",
        "content": [
            {
                "type": "text",
                "text": "{prompt}  --ratio 16:9"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url":"https://xxx.jpg"
                }
            }
        ]
    }

    

    resp = requests.post(DOUBAO_SUBMIT_URL, json=payload, headers=headers)
    resp.raise_for_status()
    task_id = resp.json()["id"]

    # 2. 轮询任务状态
    for _ in range(20):  # 最多等20*3=60秒
        time.sleep(3)
        result_resp = requests.get(DOUBAO_RESULT_URL.format(task_id), headers=headers)
        result_resp.raise_for_status()
        result_data = result_resp.json()
        # 假设图片URL在 result_data["result"]["image_url"]
        if "result" in result_data and "image_url" in result_data["result"]:
            image_url = result_data["result"]["image_url"]
            break
    else:
        raise Exception("图片生成超时")

    # 3. 下载图片并转为base64
    img_resp = requests.get(image_url)
    img_base64 = base64.b64encode(img_resp.content).decode()
    return img_base64



