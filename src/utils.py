# python src/utils.py

import os
import sys
import datetime
import hashlib
import json
import logging
import re
import subprocess
import time
from urllib.parse import unquote, urlparse
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage


current_abspath = os.path.dirname(os.path.abspath(__file__))


class ConsoleColor:
    # 定义ANSI颜色代码

    RESET = "\033[0m"  # 重置颜色样式
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BOLD = "\033[1m"  # 粗体
    UNDERLINE = "\033[4m"  # 下划线


def print_danger(msg):
    r"""
    打印危险颜色的消息
    """
    print(f'{ConsoleColor.RED} {msg} {ConsoleColor.RESET}')


def print_success(msg):
    r"""
    打印成功颜色的消息
    """
    print(f'{ConsoleColor.GREEN} {msg} {ConsoleColor.RESET}')


def logger(log_dir: str, show_console: bool = True, log_name: str = 'logger'):
    # 创建一个日志器
    re_logger = logging.getLogger(f"{log_name}")
    # 设置日志输出的最低等级, 低于当前等级则会被忽略
    re_logger.setLevel(logging.INFO)

    if not re_logger.handlers:
        # 避免重复添加处理器

        if show_console:
            # 创建控制台处理器
            sh = logging.StreamHandler()
            # 创建格式器
            sh_formator = logging.Formatter(
                fmt="%(asctime)s %(levelname)s %(message)s", datefmt="%Y/%m/%d %X")
            sh.setFormatter(sh_formator)
            # 将处理器添加至日志器中
            re_logger.addHandler(sh)

        # 创建日志文件存放文件夹
        # log_dir = os.path.join(current_abspath, "logs")
        os.makedirs(log_dir, exist_ok=True)
        # 创建文件处理器, log_file 为日志存放的文件夹
        log_file = os.path.join(
            log_dir, f'{time.strftime("%Y-%m-%d", time.localtime())}.log')
        fh = logging.FileHandler(log_file, encoding="UTF-8")
        # 创建格式器
        fh_formator = logging.Formatter(fmt="%(asctime)s %(filename)s %(lineno)d %(levelname)s %(message)s",
                                        datefmt="%Y/%m/%d %X")
        fh.setFormatter(fh_formator)
        # 将处理器添加至日志器中
        re_logger.addHandler(fh)

    return re_logger


def list_remove_duplicate(data: list):
    r"""
    去重
    """
    return list(set(data))


def get_tb_login_info():
    sensitive_config_file = os.path.join(
        current_abspath, 'sensitive_config.json')
    with open(sensitive_config_file, 'r') as scf:
        json_dict = json.load(scf)
    return json_dict["tb_acct"]


def get_os_type():
    r"""
    获取系统类型
    """
    os_type = sys.platform
    if os_type.startswith('linux'):
        return 'Linux'
    elif os_type.startswith('win'):
        return 'Windows'
    elif os_type.startswith('darwin'):
        return 'MacOS'
    else:
        return 'Unknown'


def win_name_hdlr(name):
    '''
    处理非法 Windows 文件/文件夹字符
    '''
    # 非法 Windows 文件/文件夹字符集
    inv_char_sets = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in name:
        if char in inv_char_sets:
            name = name.replace(char, '_')

    return name


def name_hdlr(name):
    '''
    处理非法文件/文件夹字符
    '''
    if get_os_type() == 'Windows':
        name = win_name_hdlr(name)
    else:
        # 暂作和 Windows 一样的处理
        name = win_name_hdlr(name)

    return name


def special_char_hdlr(name):
    '''
    处理文件/文件夹名的特殊字符
    '''
    name = name_hdlr(name)
    # 特殊文件/文件夹字符集
    inv_char_sets = [' ', '：', '...']
    for char in name:
        if char in inv_char_sets:
            name = name.replace(char, '-')
    return name


def generate_hash(input_string, byte_size: int = 8):
    r'''
    计算字符串 SHA-512 哈希，默认生成 8 字节(长度为 16 的 16 进制)哈希
    '''
    # 使用SHA-256哈希函数生成一个摘要对象
    sha512 = hashlib.sha512()
    # 将输入字符串编码并更新摘要对象
    sha512.update(input_string.encode('utf-8'))
    # 获取SHA-256哈希的摘要（字节形式）
    hash_digest = sha512.digest()
    # 取摘要的前 byte_size 个字节，并将其转换为16进制字符串
    hash_str = hash_digest[:byte_size].hex()
    return hash_str


def get_filename_from_headers(headers):
    r'''
    从 http 响应头 Content-Disposition 中提取文件名
    '''
    content_disposition = headers.get('Content-Disposition')
    if content_disposition:
        # 从 Content-Disposition 中提取文件名
        parts = content_disposition.split(';')
        for part in parts:
            if part.strip().startswith('filename='):
                filename = part.split('=')[1].strip('\'"')
                return filename
    return None


def get_filename_from_url(url):
    r'''
    从 URL 中提取文件名
    '''
    # 不处理URL编码的情况，如果URL中包含特殊字符（例如空格），它们不会被解码
    # return url.split('/')[-1]

    # unquote 函数用于将URL编码的特殊字符解码回原始字符
    # os.path.basename 用于从文件路径中提取文件名部分
    # return os.path.basename(unquote(url.split('/')[-1]))

    # 从解析后的结果中获取路径部分，然后再获取文件名部分
    return os.path.basename(unquote(urlparse(url).path))


def get_full_filename_from_url(url):
    r'''
    从文件资源 URL 中提取完整文件名（包含后缀）

    例如: `get_full_filename_from_url('http://www.example.com/path/to/file.ext?abc=123')` 将返回 'file.ext'
    '''
    return unquote(urlparse(url).path).split("/")[-1]


def is_valid_url(url):
    r'''
    判断 URL 是否有效
    '''
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])  # 必须包含协议和域名
    except:
        return False


def print_progress_bar(iteration, total, bar_length=100):
    r'''
    打印进度条
    '''
    progress = iteration / total
    arrow = '=' * int(round(bar_length * progress))
    spaces = ' ' * (bar_length - len(arrow))
    sys.stdout.write(f'\r[{arrow}{spaces}] {int(progress * 100)}%')
    sys.stdout.flush()


def bytes_to_readable(bytes_value):
    # 将字节数转换为可读性更好的格式（KB/MB/GB）
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
    index = 0
    while bytes_value >= 1024 and index < len(suffixes) - 1:
        bytes_value /= 1024.0
        index += 1
    return f"{bytes_value:.2f} {suffixes[index]}"


def add_item_to_m3u(m3u_file, title, url):
    r'''
    m3u 文件添加项
    '''
    with open(m3u_file, 'a', encoding='utf-8') as file:
        file.write(f'#EXTINF:0,{title}\n{url}\n')


def remove_item_from_m3u(m3u_file, title_to_remove):
    r'''
    m3u 文件移除项
    '''
    with open(m3u_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    with open(m3u_file, 'w', encoding='utf-8') as file:
        remove_next_line = False
        for line in lines:
            if remove_next_line:
                remove_next_line = False
                continue
            if line.strip() == f'#EXTINF:0,{title_to_remove}':
                remove_next_line = True
                continue
            file.write(line)

# ************************* 发送系统通知 *************************


def send_macos_notification(title, message):
    r'''
    发送 MacOS 通知
    '''
    # 构建 AppleScript 代码
    applescript = f'display notification "{message}" with title "{title}"'
    # 使用 subprocess 运行 AppleScript
    subprocess.run(["osascript", "-e", applescript])


def send_win_notification(title, message):
    r'''
    发送 Windows 通知
    '''
    from win11toast import toast  # type: ignore

    toast(title, message)


def send_notification(title, message):
    r'''
    发送系统通知和邮件通知

    Parameters:
        title (str): 通知标题
        message (str): 通知内容

    Returns:
        None
    '''
    os_type = get_os_type()
    if os_type == 'MacOS':
        send_macos_notification(title, message)
    elif os_type == 'Windows':
        send_win_notification(title, message)
    else:
        pass


# ************************* 身份证号校验和信息获取 *************************

def validate_id_card(id_card):
    """
    身份证号校验

    Parameters:
        id_card (str): 身份证号

    Returns:
        bool: 身份证号是否有效
    """

    # 正则表达式匹配身份证号码
    pattern = re.compile(r'^\d{17}[\dXx]$')
    if not pattern.match(id_card):
        return False

    # 获取前17位
    id_card_digits = id_card[:17]

    # 计算校验码
    factor = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    check_sum = sum(int(id_card_digits[i]) * factor[i] for i in range(17)) % 11

    # 校验码映射
    check_code_map = {0: '1', 1: '0', 2: 'X', 3: '9', 4: '8',
                      5: '7', 6: '6', 7: '5', 8: '4', 9: '3', 10: '2'}

    # 获取校验码
    check_code = check_code_map[check_sum]

    # 检查校验码是否匹配
    return id_card[-1].upper() == check_code


def get_birth_date(id_card):
    """
    获取身份证号中的生日信息

    Parameters:
        id_card (str): 身份证号

    Returns:
        str: 生日
    """

    # 提取出生日期码
    birth_date_str = id_card[6:14]

    # 转换为日期格式
    try:
        birth_date = datetime.datetime.strptime(
            birth_date_str, '%Y%m%d').date()
        return birth_date
    except ValueError:
        return None


def get_gender(id_card):
    """
    获取身份证号中的性别

    Parameters:
        id_card (str): 身份证号

    Returns:
        str: 性别
    """

    # 获取性别码
    gender_code = int(id_card[16])

    # 奇数为男性，偶数为女性
    return "男性" if gender_code % 2 == 1 else "女性"


def get_http_status_message(status_code):
    """
    获取 HTTP 状态码对应的消息

    Parameters:
        status_code (int): HTTP 状态码

    Returns:
        str: HTTP 状态码对应的消息
    """

    http_status_codes = {
        100: '100 Continue, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/100',
        101: '101 Switching Protocols, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/101',
        103: '103 Early Hints, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/103',
        200: '200 OK, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/200',
        201: '201 Created, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/201',
        202: '202 Accepted, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/202',
        203: '203 Non-Authoritative Information, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/203',
        204: '204 No Content, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/204',
        205: '205 Reset Content, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/205',
        206: '206 Partial Content, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/206',

        207: '207 Multi-Status, Detail: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/207',
        208: '208 Already Reported, Detail: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/208',
        226: '226 IM Used, Detail: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/226',

        300: '300 Multiple Choices, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/300',
        301: '301 Moved Permanently, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/301',
        302: '302 Found, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/302',
        303: '303 See Other, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/303',
        304: '304 Not Modified, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/304',
        307: '307 Temporary Redirect, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/307',
        400: '400 Bad Request, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/400',
        401: '401 Unauthorized, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/401',
        402: '402 Payment Required, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/402',
        403: '403 Forbidden, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/403',
        404: '404 Not Found, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/404',
        405: '405 Method Not Allowed, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/405',
        406: '406 Not Acceptable, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/406',
        407: '407 Proxy Authentication Required, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/407',
        408: '408 Request Timeout, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/408',
        409: '409 Conflict, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/409',
        410: '410 Gone, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/410',
        411: '411 Length Required, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/411',
        412: '412 Precondition Failed, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/412',
        413: '413 Payload Too Large, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/413',
        414: '414 URI Too Long, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/414',
        415: '415 Unsupported Media Type, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/415',
        416: '416 Range Not Satisfiable, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/416',
        417: '417 Expectation Failed, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/417',
        418: '418 I\'m a teapot, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/418',
        421: '421 Misdirected Request, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/421',
        422: '422 Unprocessable Entity, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/422',
        423: '423 Locked, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/423',
        424: '424 Failed Dependency, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/424',
        425: '425 Too Early, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/425',
        426: '426 Upgrade Required, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/426',
        428: '428 Precondition Required, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/428',
        429: '429 Too Many Requests, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/429',
        431: '431 Request Header Fields Too Large, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/431',
        451: '451 Unavailable For Legal Reasons, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/451',
        500: '500 Internal Server Error, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/500',
        501: '501 Not Implemented, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/501',
        502: '502 Bad Gateway, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/502',
        503: '503 Service Unavailable, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/503',
        504: '504 Gateway Timeout, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/504',
        505: '505 HTTP Version Not Supported, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/505',
        506: '506 Variant Also Negotiates, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/506',
        507: '507 Insufficient Storage, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/507',
        508: '508 Loop Detected, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/508',
        510: '510 Not Extended, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/510',
        511: '511 Network Authentication Required, Detail: https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Status/511',
    }

    return http_status_codes.get(status_code, 'Unknown Status Code')
