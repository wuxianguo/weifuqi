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
import os
from volcenginesdkarkruntime import Ark
import json

logging.basicConfig(
    filename='server.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s'
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)


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
    logging.info(request.get_json())

    params = request.get_json()
    scene = params.get('scene', '')
    keywords = params.get('keywords', '')
    template = params.get('template', '')
    scene_name = params.get('scene_name', '')
    template_name = params.get('template_name', '')

    # 拼接prompt
    prompt = f"{scene_name}，{template_name}，关键词：{keywords}"
    logging.info(f"prompt: {prompt}")

    try:
        response = generate_doubao_image(prompt)
        return make_succ_response(response)
    except Exception as e:
        logging.info(f"{str(e)}")
        return make_err_response(str(e))


def generate_doubao_image(prompt):
    DOUBAO_API_KEY = "f5bfd631-054f-4d92-8d83-6552830cd68d"

    # 1. 提交生成任务
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DOUBAO_API_KEY}"
    }
   
   # 请确保您已将 API Key 存储在环境变量 ARK_API_KEY 中
    # 初始化Ark客户端，从环境变量中读取您的API Key
    client = Ark(
        # 此为默认路径，您可根据业务所在地域进行配置
        base_url="https://ark.cn-beijing.volces.com/api/v3",
        # 从环境变量中获取您的 API Key。此为默认方式，您可根据需要进行修改
        api_key= DOUBAO_API_KEY,
    )

    imagesResponse = client.images.generate(
        model="doubao-seedream-3-0-t2i-250415",
        prompt=f"{prompt}",
        size="1024x768",
    )

    #print(imagesResponse.data[0].url)
    return parse_and_generate_response(imagesResponse)


def parse_and_generate_response(resp):
    # 解析各字段
    model = resp.model
    data = resp.data
    usage = resp.usage

    # 解析图片URL
    image_url = None
    if isinstance(data, list) and len(data) > 0:
        image_url = data[0].url

    # 下载图片并转为base64
    img_base64 = None
    if image_url:
        img_resp = requests.get(image_url)
        img_base64 = base64.b64encode(img_resp.content).decode()

    # 组装返回信息
    result = {
        "model": model,
        "data": [
            {
                "url": image_url,
                "image_base64": img_base64
            }
        ],
        "usage": usage.to_json()
    }
    return result



