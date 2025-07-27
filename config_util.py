import os
import json
import codecs
from langsmith.schemas import Feedback  # 用于LangSmith反馈系统（当前未实际使用）
import requests
from configparser import ConfigParser  # 用于解析INI格式的配置文件
import functools
from threading import Lock  # 线程锁，用于实现线程安全
import threading
from utils import util  # 自定义工具模块

# 线程本地存储（当前未使用）
_thread_local = threading.local()

# 全局锁，确保线程安全
lock = Lock()


def synchronized(func):
    """线程安全装饰器：通过全局锁确保函数单线程执行"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with lock:
            return func(*args, **kwargs)

    return wrapper


# ----------------------
# 全局配置变量初始化
# ----------------------
config: json = None  # 存储config.json内容
system_config: ConfigParser = None  # 存储system.conf配置
system_chrome_driver = None  # Chrome驱动路径（当前未使用）
# 各服务的API密钥和配置项
key_ali_nls_key_id = None  # 阿里云语音识别Key ID
key_ali_nls_key_secret = None  # 阿里云语音识别Key Secret
key_ali_nls_app_key = None  # 阿里云语音识别App Key
key_ms_tts_key = None  # 微软语音合成Key
Key_ms_tts_region = None  # 微软语音合成区域
baidu_emotion_app_id = None  # 百度情感分析App ID
baidu_emotion_api_key = None  # 百度情感分析API Key
baidu_emotion_secret_key = None  # 百度情感分析Secret Key
key_gpt_api_key = None  # GPT API密钥
gpt_model_engine = None  # GPT模型引擎
proxy_config = None  # 代理配置
ASR_mode = None  # 语音识别模式
local_asr_ip = None  # 本地语音识别服务IP
local_asr_port = None  # 本地语音识别服务端口
ltp_mode = None  # 语言技术平台模式
gpt_base_url = None  # GPT基础URL
tts_module = None  # 语音合成模块选择
key_ali_tss_key_id = None  # 阿里云语音合成Key ID
key_ali_tss_key_secret = None  # 阿里云语音合成Key Secret
key_ali_tss_app_key = None  # 阿里云语音合成App Key
volcano_tts_appid = None  # 火山引擎语音合成AppID
volcano_tts_access_token = None  # 火山引擎访问令牌
volcano_tts_cluster = None  # 火山引擎集群
volcano_tts_voice_type = None  # 火山引擎语音类型
start_mode = None  # 系统启动模式
fay_url = None  # FAY系统URL
system_conf_path = None  # system.conf文件路径
config_json_path = None  # config.json文件路径

# 配置中心API参数
CONFIG_SERVER = {
    'BASE_URL': 'http://219.135.170.56:5500',  # 配置中心API地址
    'API_KEY': 'your-api-key-here',  # API访问密钥
    'PROJECT_ID': 'd19f7b0a-2b8a-4503-8c0d-1a587b90eb69'  # 默认项目ID
}


def load_config_from_api(project_id=None):
    """
    从配置中心API加载配置

    Args:
        project_id: 项目ID，如果为None则使用全局设置的项目ID

    Returns:
        包含配置信息的字典，加载失败则返回None
    """
    global CONFIG_SERVER
    # 使用参数提供的项目ID或全局设置的项目ID
    pid = project_id or CONFIG_SERVER['PROJECT_ID']
    if not pid:
        util.log(2, "错误: 未指定项目ID，无法从API加载配置")
        return None

    # 构建API请求URL
    url = f"{CONFIG_SERVER['BASE_URL']}/api/projects/{pid}/config"

    # 设置请求头
    headers = {
        'X-API-Key': CONFIG_SERVER['API_KEY'],
        'Content-Type': 'application/json'
    }

    try:
        # 发送API请求
        response = requests.get(url, headers=headers)

        # 检查响应状态
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                # 提取项目数据
                project_data = result.get('project', {})

                # 创建ConfigParser对象并填充数据
                sys_config = ConfigParser()
                sys_config.add_section('key')  # 默认添加key节

                # 获取系统配置字典
                system_dict = project_data.get('system_config', {})

                # 遍历配置节和键值对
                for section, items in system_dict.items():
                    if not sys_config.has_section(section):
                        sys_config.add_section(section)
                    for key, value in items.items():
                        sys_config.set(section, key, str(value))

                # 获取用户配置
                user_config = project_data.get('config_json', {})

                # 构建返回的配置字典
                config_dict = {
                    'system_config': sys_config,
                    'config': user_config,
                    'project_id': pid,
                    'name': project_data.get('name', ''),
                    'description': project_data.get('description', ''),
                    'source': 'api'  # 标记配置来源
                }

                # 将system.conf的配置项平铺到字典（方便直接访问）
                for section in sys_config.sections():
                    for key, value in sys_config.items(section):
                        config_dict[f'{section}_{key}'] = value

                return config_dict
            else:
                util.log(2, f"API错误: {result.get('message', '未知错误')}")
        else:
            util.log(2, f"API请求失败: HTTP状态码 {response.status_code}")
    except Exception as e:
        util.log(2, f"从API加载配置时出错: {str(e)}")

    return None


@synchronized
def load_config():
    """
    加载配置文件的主函数（线程安全）
    如果本地文件不存在则从API加载，并将API配置缓存到本地

    Returns:
        包含所有配置信息的字典
    """
    # 声明全局变量（所有配置项）
    global config, system_config, key_ali_nls_key_id, key_ali_nls_key_secret, key_ali_nls_app_key
    global key_ms_tts_key, key_ms_tts_region, baidu_emotion_app_id, baidu_emotion_secret_key
    global baidu_emotion_api_key, key_gpt_api_key, gpt_model_engine, proxy_config, ASR_mode
    global local_asr_ip, local_asr_port, ltp_mode, gpt_base_url, tts_module, key_ali_tss_key_id
    global key_ali_tss_key_secret, key_ali_tss_app_key, volcano_tts_appid, volcano_tts_access_token
    global volcano_tts_cluster, volcano_tts_voice_type, start_mode, fay_url, CONFIG_SERVER
    global system_conf_path, config_json_path

    # 初始化配置文件路径
    if system_conf_path is None or config_json_path is None:
        # 默认使用当前目录下的配置文件
        system_conf_path = os.path.join(os.getcwd(), 'system.conf')
        config_json_path = os.path.join(os.getcwd(), 'config.json')

    # 检查本地配置文件是否存在
    sys_conf_exists = os.path.exists(system_conf_path)
    config_json_exists = os.path.exists(config_json_path)

    # 如果任一本地文件不存在，尝试从API加载配置
    if not sys_conf_exists or not config_json_exists:
        missing_files = []
        if not sys_conf_exists:
            missing_files.append('system.conf')
        if not config_json_exists:
            missing_files.append('config.json')

        util.log(1, f"本地配置文件缺失（{', '.join(missing_files)}），尝试从API加载配置...")

        # 从配置中心API加载配置
        api_config = load_config_from_api(CONFIG_SERVER['PROJECT_ID'])

        if api_config:
            util.log(1, "成功从配置中心加载配置")
            system_config = api_config['system_config']
            config = api_config['config']

            # 将API配置缓存到本地cache_data目录
            cache_dir = os.path.join(os.getcwd(), 'cache_data')
            system_conf_path = os.path.join(cache_dir, 'system.conf')
            config_json_path = os.path.join(cache_dir, 'config.json')
            save_api_config_to_local(api_config, system_conf_path, config_json_path)

    # 从本地文件加载配置
    # 1. 加载system.conf
    system_config = ConfigParser()
    system_config.read(system_conf_path, encoding='UTF-8')

    # 2. 读取各项配置（使用fallback提供默认值）
    key_ali_nls_key_id = system_config.get('key', 'ali_nls_key_id', fallback=None)
    key_ali_nls_key_secret = system_config.get('key', 'ali_nls_key_secret', fallback=None)
    key_ali_nls_app_key = system_config.get('key', 'ali_nls_app_key', fallback=None)
    key_ali_tss_key_id = system_config.get('key', 'ali_tss_key_id', fallback=None)
    key_ali_tss_key_secret = system_config.get('key', 'ali_tss_key_secret', fallback=None)
    key_ali_tss_app_key = system_config.get('key', 'ali_tss_app_key', fallback=None)
    key_ms_tts_key = system_config.get('key', 'ms_tts_key', fallback=None)
    key_ms_tts_region = system_config.get('key', 'ms_tts_region', fallback=None)
    baidu_emotion_app_id = system_config.get('key', 'baidu_emotion_app_id', fallback=None)
    baidu_emotion_api_key = system_config.get('key', 'baidu_emotion_api_key', fallback=None)
    baidu_emotion_secret_key = system_config.get('key', 'baidu_emotion_secret_key', fallback=None)
    key_gpt_api_key = system_config.get('key', 'gpt_api_key', fallback=None)
    gpt_model_engine = system_config.get('key', 'gpt_model_engine', fallback=None)
    ASR_mode = system_config.get('key', 'ASR_mode', fallback=None)
    local_asr_ip = system_config.get('key', 'local_asr_ip', fallback=None)
    local_asr_port = system_config.get('key', 'local_asr_port', fallback=None)
    proxy_config = system_config.get('key', 'proxy_config', fallback=None)
    ltp_mode = system_config.get('key', 'ltp_mode', fallback=None)
    gpt_base_url = system_config.get('key', 'gpt_base_url', fallback=None)
    tts_module = system_config.get('key', 'tts_module', fallback=None)
    volcano_tts_appid = system_config.get('key', 'volcano_tts_appid', fallback=None)
    volcano_tts_access_token = system_config.get('key', 'volcano_tts_access_token', fallback=None)
    volcano_tts_cluster = system_config.get('key', 'volcano_tts_cluster', fallback=None)
    volcano_tts_voice_type = system_config.get('key', 'volcano_tts_voice_type', fallback=None)
    start_mode = system_config.get('key', 'start_mode', fallback=None)
    fay_url = system_config.get('key', 'fay_url', fallback=None)

    # 3. 特殊处理：如果fay_url未配置，动态生成
    if not fay_url:
        from utils.util import get_local_ip
        local_ip = get_local_ip()
        fay_url = f"http://{local_ip}:5000"  # 使用本机IP和默认端口5000
        # 更新内存中的system_config对象（不写入文件）
        if not system_config.has_section('key'):
            system_config.add_section('key')
        system_config.set('key', 'fay_url', fay_url)

    # 4. 加载用户配置文件config.json
    with codecs.open(config_json_path, encoding='utf-8') as f:
        config = json.load(f)

    # 整合所有配置到字典
    config_dict = {
        'system_config': system_config,
        'config': config,
        # 平铺所有关键配置项（方便直接访问）
        'ali_nls_key_id': key_ali_nls_key_id,
        'ali_nls_key_secret': key_ali_nls_key_secret,
        'ali_nls_app_key': key_ali_nls_app_key,
        'ms_tts_key': key_ms_tts_key,
        'ms_tts_region': key_ms_tts_region,
        'baidu_emotion_app_id': baidu_emotion_app_id,
        'baidu_emotion_api_key': baidu_emotion_api_key,
        'baidu_emotion_secret_key': baidu_emotion_secret_key,
        'gpt_api_key': key_gpt_api_key,
        'gpt_model_engine': gpt_model_engine,
        'ASR_mode': ASR_mode,
        'local_asr_ip': local_asr_ip,
        'local_asr_port': local_asr_port,
        'proxy_config': proxy_config,
        'ltp_mode': ltp_mode,
        'gpt_base_url': gpt_base_url,
        'tts_module': tts_module,
        'ali_tss_key_id': key_ali_tss_key_id,
        'ali_tss_key_secret': key_ali_tss_key_secret,
        'ali_tss_app_key': key_ali_tss_app_key,
        'volcano_tts_appid': volcano_tts_appid,
        'volcano_tts_access_token': volcano_tts_access_token,
        'volcano_tts_cluster': volcano_tts_cluster,
        'volcano_tts_voice_type': volcano_tts_voice_type,
        'start_mode': start_mode,
        'fay_url': fay_url,
        'source': 'local'  # 标记配置来源
    }

    return config_dict


def save_api_config_to_local(api_config, system_conf_path, config_json_path):
    """
    将API获取的配置保存到本地文件

    Args:
        api_config: API加载的配置字典
        system_conf_path: system.conf文件路径
        config_json_path: config.json文件路径
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(system_conf_path), exist_ok=True)
        os.makedirs(os.path.dirname(config_json_path), exist_ok=True)

        # 保存system.conf
        with open(system_conf_path, 'w', encoding='utf-8') as f:
            api_config['system_config'].write(f)

        # 保存config.json
        with codecs.open(config_json_path, 'w', encoding='utf-8') as f:
            json.dump(api_config['config'], f, ensure_ascii=False, indent=4)

        util.log(1, f"配置中心配置已缓存到本地: {system_conf_path} 和 {config_json_path}")
    except Exception as e:
        util.log(2, f"保存配置中心配置到本地时出错: {str(e)}")


@synchronized
def save_config(config_data):
    """
    保存用户配置到config.json（线程安全）

    Args:
        config_data: 要保存的配置数据
    """
    global config, config_json_path
    config = config_data

    # 保存到文件（格式化JSON）
    with codecs.open(config_json_path, mode='w', encoding='utf-8') as file:
        file.write(json.dumps(config_data, sort_keys=True, indent=4, separators=(',', ': ')))