import os
import re
import sys
import json
# import shutil
import logging
import tempfile
import requests
from pathlib import Path
from datetime import datetime
from PyQt5.QtCore import *
import ffmpeg
# from utils import *
# import GlobalConfig
from Signal import Signal


# if get_os_type() == 'MacOS' and shutil.which('ffmpeg') is None:
#     # 设置环境变量使FFmpeg生效
#     # FFMPEG_HOME = '/Library/FFmpeg'
#     FFMPEG_HOME = '/usr/local/bin'
#     PATH = os.environ['PATH']

#     os.environ['PATH'] = f'{FFMPEG_HOME}:{PATH}'

# 设置环境变量使FFmpeg日志不输出到控制台，输出到指定日志文件（32=quiet）
# os.environ['FFREPORT'] = 'file=ffmpeg.log:level=32'


class CoreWorker(QThread):
    def __init__(self, parent, signals: Signal, inputFolder, audioFile,  outputFolder, tripleSpeed=10,
                 amapApiKey=None, mainView='front'):
        super().__init__(parent)

        self.parent = parent
        self.signals = signals

        # 输入视频文件夹路径
        self.inputFolder = inputFolder
        # 输入音频文件路径
        self.audioFile = audioFile
        # 输出视频文件夹路径
        self.outputFolder = outputFolder
        # 输出视频倍速
        self.tripleSpeed = tripleSpeed
        # 高德地图 API Key
        self.amapApiKey = amapApiKey
        # 主视角
        self.mainView = mainView

        self.current_abspath = os.path.dirname(os.path.abspath(__file__))

        # self.glogger = logger(GlobalConfig.LOG_DIR, False,
        #                       f"CamClipCombiner-CoreWorker-{id(self)}")
        self.glogger = logging.getLogger("CamClipCombiner-CoreWorker")

    def work(self):
        input_folder = self.inputFolder
        audioFile = self.audioFile
        output_folder = self.outputFolder

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # 1.将各个时间点的不同视角视频合并成一个视频
        self.process_tesla_clips(input_folder, output_folder)

        # 2.将合并后的视频进行拼接
        video_file_combined = os.path.join(
            output_folder, 'temp_combined.mp4')
        self.concatenate_videos(output_folder, video_file_combined)

        # 3.添加音频作为背景音乐
        video_file_with_audio = os.path.join(
            output_folder, 'temp_combined_with_audio.mp4')
        self.combine_video_audio(video_file_combined,
                                 audioFile, video_file_with_audio)

    def resourcePath(self, relative_path):
        """获取资源文件的绝对路径"""
        # 规范化路径
        relative_path = Path(relative_path)
        if hasattr(sys, '_MEIPASS') or getattr(sys, 'frozen', False):
            return os.path.join(sys._MEIPASS, relative_path)

        return os.path.join(self.current_abspath, relative_path)

    def get_event_json(self):
        event_json_file = os.path.join(
            self.inputFolder, 'event.json')
        if not os.path.exists(event_json_file):
            self.glogger.info(
                f"事件文件不存在: {event_json_file}, 请检查输入文件夹")
            return None
        with open(event_json_file, 'r') as scf:
            json_dict = json.load(scf)
        return json_dict

    def reverse_geocode(self, longitude, latitude):

        if self.amapApiKey is None:
            return None

        api_key = self.amapApiKey
        url = f"https://restapi.amap.com/v3/geocode/regeo?key={api_key}&location={longitude},{latitude}"

        try:
            response = requests.get(url)
            data = response.json()

            if data['status'] == '1':
                address = data['regeocode']['formatted_address']
                self.glogger.info(f"地址信息: {address}")
                return address
            else:
                info = data['info']
                self.glogger.info(f"逆地理编码失败: {info}")
                return None
        except Exception as e:
            self.glogger.exception(f"请求失败: {e}")
            return None

    def process_tesla_clips(self, folder_path, output_path):
        # 获取文件夹中所有视频文件
        video_files = [f for f in os.listdir(
            folder_path) if f.endswith('.mp4')]

        # 按时间戳分组视频
        video_groups = {}
        for file in video_files:
            # 提取时间戳部分
            timestamp_match = re.match(
                r'(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})', file)
            if timestamp_match:
                timestamp = timestamp_match.group(1)
                if timestamp not in video_groups:
                    video_groups[timestamp] = {}

                # 根据视角分类
                if 'front' in file:
                    video_groups[timestamp]['front'] = os.path.join(
                        folder_path, file)
                elif 'back' in file:
                    video_groups[timestamp]['back'] = os.path.join(
                        folder_path, file)
                elif 'left_repeater' in file:
                    video_groups[timestamp]['left'] = os.path.join(
                        folder_path, file)
                elif 'right_repeater' in file:
                    video_groups[timestamp]['right'] = os.path.join(
                        folder_path, file)

        event_json = self.get_event_json()
        self.glogger.info(f"event_json: {event_json}")

        if event_json and event_json['est_lat'] and event_json['est_lon']:
            address = self.reverse_geocode(event_json['est_lon'],
                                           event_json['est_lat'])
            if address:
                event_json['address'] = address
            else:
                event_json['address'] = ''

        count = 0
        total = len(video_groups)
        # 处理每个时间戳组的视频
        for timestamp, clips in sorted(video_groups.items()):
            count = count + 1
            # 检查是否四个视角都齐全
            if len(clips) != 4:
                self.glogger.info(f"警告: 时间戳 {timestamp} 的视频不完整(缺少某些视角), 跳过处理")
                continue

            try:
                # 输入文件
                front_input = ffmpeg.input(clips['front'])
                back_input = ffmpeg.input(clips['back'])
                left_input = ffmpeg.input(clips['left'])
                right_input = ffmpeg.input(clips['right'])

                # 获取前视视频的尺寸
                probe = ffmpeg.probe(clips['front'])
                video_stream = next(
                    (stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
                width = int(video_stream['width'])
                height = int(video_stream['height'])

                if self.mainView == "front":
                    combined = self.frontMainView(
                        front_input, back_input, left_input, right_input, width, height)
                elif self.mainView == "back":
                    combined = self.backMainView(
                        front_input, back_input, left_input, right_input, width, height)
                elif self.mainView == "left":
                    combined = self.leftMainView(
                        front_input, back_input, left_input, right_input, width, height)
                elif self.mainView == "right":
                    combined = self.rightMainView(
                        front_input, back_input, left_input, right_input, width, height)

                # 5. 添加时间戳文字
                timestamp_text = datetime.strptime(
                    timestamp, "%Y-%m-%d_%H-%M-%S").strftime("%Y-%m-%d %H:%M:%S")
                combined = ffmpeg.drawtext(
                    combined,
                    text=timestamp_text,
                    x=10,                   # 左边距10像素
                    y=10,                   # 上边距10像素
                    fontsize=24,
                    fontcolor='white',
                )
                # 6. 添加水印
                combined = ffmpeg.drawtext(
                    combined,
                    text='Tesla',
                    x='main_w-text_w-10',   # 右边距10像素
                    y='main_h-text_h-10',   # 下边距10像素
                    fontsize=24,
                    fontcolor='white',
                )
                # 7. 添加事件信息
                if event_json and event_json['city']:
                    address = event_json['address']
                    event_str = f'{address}'

                    combined = ffmpeg.drawtext(
                        combined,
                        text=event_str,
                        x=10,                   # 左边距10像素
                        y=35,                   # 上边距35像素
                        fontsize=24,
                        fontcolor='white',
                        fontfile=self.resourcePath("assets/SimHei.ttf")
                    )

                # 生成输出文件名
                output_filename = f"{timestamp}.mp4"
                output_filepath = os.path.join(output_path, output_filename)

                # 输出配置
                output = ffmpeg.output(
                    combined,
                    output_filepath,
                    vcodec='libx264',
                    crf=18,                 # 视频质量(0-51，值越小质量越高)
                    preset='fast',          # 编码速度与压缩率的平衡
                    pix_fmt='yuv420p',
                    movflags='faststart',   # 流媒体优化

                    r='30',                 # 设置统一的帧率，解决时间戳（DTS，解码时间戳）不连续问题
                )

                # 运行FFmpeg命令
                (
                    output
                    .global_args('-loglevel', 'quiet')
                    # .global_args('-report')
                    .run(quiet=True, overwrite_output=True)
                )

                self.glogger.info(f"已处理并保存: {output_filepath}")
                self.signals.process_progress.emit(int((count / total) * 100))

            except ffmpeg.Error as e:
                self.glogger.info(
                    f"处理时间戳 {timestamp} 的视频时出错: {e.stderr}")
                continue

    def frontMainView(self, front_input, back_input, left_input, right_input, width, height):

        def speed_up(input_stream): return input_stream.filter(
            'setpts', f'{1/self.tripleSpeed}*PTS')

        # 处理各个视角视频
        front = speed_up(front_input).filter('scale', width, height)
        back = speed_up(back_input).filter(
            'scale', width//4, height//4)
        left = speed_up(left_input).filter(
            'scale', width//4, height//4)
        right = speed_up(right_input).filter(
            'scale', width//4, height//4)

        # 叠加各个视频流
        # 1. 首先叠加前视(主画面)
        combined = front

        # 2. 叠加后视(右上角)
        combined = ffmpeg.overlay(
            combined,
            back,
            x='main_w-overlay_w',   # 右边距0像素
            y=0                     # 上边距0像素
        )

        # 3. 叠加左侧视(左下角)
        combined = ffmpeg.overlay(
            combined,
            left,
            x=0,                    # 左边距0像素
            y='main_h-overlay_h'    # 下边距0像素
        )

        # 4. 叠加右侧视(右下角)
        combined = ffmpeg.overlay(
            combined,
            right,
            x='main_w-overlay_w',   # 右边距0像素
            y='main_h-overlay_h'    # 下边距0像素
        )

        return combined

    def backMainView(self, front_input, back_input, left_input, right_input, width, height):

        def speed_up(input_stream): return input_stream.filter(
            'setpts', f'{1/self.tripleSpeed}*PTS')

        # 处理各个视角视频
        front = speed_up(front_input).filter('scale', width//4, height//4)
        back = speed_up(back_input).filter('scale', width, height)
        left = speed_up(left_input).filter('scale', width//4, height//4)
        right = speed_up(right_input).filter('scale', width//4, height//4)

        # 叠加各个视频流
        # 1. 首先叠加后视(主画面)
        combined = back

        # 2. 叠加前视(左上角)
        combined = ffmpeg.overlay(
            combined,
            front,
            x=0,                    # 左边距0像素
            y=0                     # 上边距0像素
        )

        # 3. 叠加左侧视(左下角)
        combined = ffmpeg.overlay(
            combined,
            left,
            x=0,                    # 左边距0像素
            y='main_h-overlay_h'    # 下边距0像素
        )

        # 4. 叠加右侧视(右下角)
        combined = ffmpeg.overlay(
            combined,
            right,
            x='main_w-overlay_w',   # 右边距0像素
            y='main_h-overlay_h'    # 下边距0像素
        )

        return combined

    def leftMainView(self, front_input, back_input, left_input, right_input, width, height):

        def speed_up(input_stream): return input_stream.filter(
            'setpts', f'{1/self.tripleSpeed}*PTS')

        # 处理各个视角视频
        front = speed_up(front_input).filter('scale', width//4, height//4)
        back = speed_up(back_input).filter('scale', width//4, height//4)
        left = speed_up(left_input).filter('scale', width, height)
        right = speed_up(right_input).filter('scale', width//4, height//4)

        # 叠加各个视频流
        # 1. 首先叠加左侧视(主画面)
        combined = left

        # 2. 叠加前视(左上角)
        combined = ffmpeg.overlay(
            combined,
            front,
            x=0,                    # 左边距0像素
            y=0                     # 上边距0像素
        )

        # 3. 叠加后视(右上角)
        combined = ffmpeg.overlay(
            combined,
            back,
            x='main_w-overlay_w',   # 右边距0像素
            y=0                     # 上边距0像素
        )

        # 4. 叠加右侧视(右下角)
        combined = ffmpeg.overlay(
            combined,
            right,
            x='main_w-overlay_w',   # 右边距0像素
            y='main_h-overlay_h'    # 下边距0像素
        )

        return combined

    def rightMainView(self, front_input, back_input, left_input, right_input, width, height):

        def speed_up(input_stream): return input_stream.filter(
            'setpts', f'{1/self.tripleSpeed}*PTS')

        # 处理各个视角视频
        front = speed_up(front_input).filter('scale', width//4, height//4)
        back = speed_up(back_input).filter('scale', width//4, height//4)
        left = speed_up(left_input).filter('scale', width//4, height//4)
        right = speed_up(right_input).filter('scale', width, height)

        # 叠加各个视频流
        # 1. 首先叠加右侧视(主画面)
        combined = right

        # 2. 叠加前视(左上角)
        combined = ffmpeg.overlay(
            combined,
            front,
            x=0,                    # 左边距0像素
            y=0                     # 上边距0像素
        )

        # 3. 叠加后视(右上角)
        combined = ffmpeg.overlay(
            combined,
            back,
            x='main_w-overlay_w',   # 右边距0像素
            y=0                     # 上边距0像素
        )

        # 4. 叠加左侧视(左下角)
        combined = ffmpeg.overlay(
            combined,
            left,
            x=0,                    # 左边距0像素
            y='main_h-overlay_h'    # 下边距0像素
        )

        return combined

    def concatenate_videos(self, input_folder, output_file):
        # 获取文件夹中所有MP4文件
        video_files = [f for f in os.listdir(
            input_folder) if f.endswith('.mp4')]

        # 按文件名中的时间排序
        def extract_time(filename):
            # 从文件名中提取时间部分：2022-03-20_15-13-27
            time_str = re.sub(r'\.mp4$', '', filename)
            try:
                return datetime.strptime(time_str, "%Y-%m-%d_%H-%M-%S")
            except ValueError:
                return datetime.min  # 如果解析失败，放到最前面

        video_files.sort(key=extract_time)

        if not video_files:
            self.glogger.info("没有找到MP4文件")
            return

        self.glogger.info("将按以下顺序拼接视频:")
        for f in video_files:
            self.glogger.info(f)

        # 创建临时目录存储中间文件
        with tempfile.TemporaryDirectory() as temp_dir:
            # 使用concat协议合并所有临时文件
            with open(os.path.join(temp_dir, "file_list.txt"), "w", encoding='utf-8') as f:
                for file in video_files:
                    f.write(f"file '{os.path.join(input_folder, file)}'\n")

            try:
                # 使用ffmpeg concat协议进行拼接
                (
                    ffmpeg
                    .input(os.path.join(temp_dir, "file_list.txt"), format='concat', safe=0)
                    .output(output_file, c='copy')
                    .global_args('-loglevel', 'quiet')
                    # .global_args('-report')
                    .run(quiet=True, overwrite_output=True)
                )
            except ffmpeg.Error as e:
                self.glogger.error(f"FFmpeg错误: {e.stderr}")
                raise

            self.glogger.info(f"视频拼接完成，输出文件: {output_file}")

    def combine_video_audio(self, video_path, audio_path, output_path):
        """
        将视频和音频合成，处理音频时长以匹配视频时长

        参数:
            video_path: 输入视频文件路径
            audio_path: 输入音频文件路径
            output_path: 输出文件路径
        """
        try:
            # 获取视频信息
            video_info = ffmpeg.probe(video_path)
            video_stream = next(
                (stream for stream in video_info['streams'] if stream['codec_type'] == 'video'), None)
            video_duration = float(video_stream['duration'])

            # 获取音频信息
            audio_info = ffmpeg.probe(audio_path)
            audio_stream = next(
                (stream for stream in audio_info['streams'] if stream['codec_type'] == 'audio'), None)
            audio_duration = float(audio_stream['duration'])

            self.glogger.info(
                f"视频时长: {video_duration}秒, 音频时长: {audio_duration}秒")

            # 处理音频流
            # audio_input = ffmpeg.input(audio_path, **{'stream_loop': -1})
            audio_input = ffmpeg.input(audio_path, stream_loop=-1)
            # 处理视频流
            video_input = ffmpeg.input(video_path).video

            # 合并音视频，确保以视频时长为准
            output = ffmpeg.output(
                video_input,
                audio_input,
                output_path,
                vcodec='copy',      # 直接复制视频流
                acodec='aac',       # 重新编码音频 libmp3lame 、 aac
                t=video_duration,   # 强制时长为视频时长（-t）
            )

            # 执行命令
            (
                output
                .global_args('-loglevel', 'quiet')
                # .global_args('-report')
                .run(quiet=True, overwrite_output=True)
            )
            self.glogger.info(f"合成完成，输出文件: {output_path}")

        except Exception as e:
            self.glogger.exception(f"处理过程中发生错误: {str(e)}")
            raise

    def run(self):
        try:
            self.work()
            self.glogger.info("处理完成")
            self.signals.process_finish.emit('success')
        except Exception as e:
            self.glogger.exception(f"处理失败: {str(e)}")
            self.signals.process_finish.emit("fail")

    def stop(self):
        self.terminate()
        self.wait()
        self.signals.process_finish.emit("stop")
        self.glogger.info("处理已停止")
