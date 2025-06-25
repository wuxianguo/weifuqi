from datetime import datetime
from flask import render_template, request, jsonify
from run import app
from wxcloudrun.dao import delete_counterbyid, query_counterbyid, insert_counter, update_counterbyid
from wxcloudrun.model import Counters
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont


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
    images = params.get('images', [])
    scene_name = params.get('scene_name', '')
    template_name = params.get('template_name', '')

    # 创建一张白底图片
    img = Image.new('RGB', (600, 400), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()

    # 绘制文本内容
    y = 30
    draw.text((30, y), f"场景: {scene} ({scene_name})", fill=(0, 0, 0), font=font)
    y += 40
    draw.text((30, y), f"关键词: {keywords}", fill=(0, 0, 0), font=font)
    y += 40
    draw.text((30, y), f"模板: {template} ({template_name})", fill=(0, 0, 0), font=font)
    y += 40
    draw.text((30, y), f"图片数量: {len(images)}", fill=(0, 0, 0), font=font)

    # 可以在此处扩展：如合成上传的图片等

    # 保存到内存并转为base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()

    # 返回base64字符串，前端可用 <img src="data:image/png;base64,xxx" /> 预览
    return make_succ_response({"image_base64": img_str})



