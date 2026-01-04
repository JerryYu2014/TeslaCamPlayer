# -*- coding: utf-8 -*-

"""
TeslaCam Player 主题管理器
基于 qt_material 的主题切换功能
"""

import os
import configparser
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from qt_material import apply_stylesheet


class ThemeManager:
    """主题管理器"""
    
    def __init__(self):
        self.current_theme = "light_blue"
        self.app = None
        
        # 定义可用主题（基于 qt_material 常见支持的主题）
        self.themes = {
            "light_blue": {
                "name": "浅蓝主题",
                "description": "清新的浅蓝色主题",
                "file": "light_blue.xml"
            },
            "dark_blue": {
                "name": "深蓝主题", 
                "description": "专业的深蓝色主题",
                "file": "dark_blue.xml"
            },
            "light_lightgreen": {
                "name": "浅绿主题",
                "description": "护眼的浅绿色主题", 
                "file": "light_lightgreen.xml"
            },
            "dark_lightgreen": {
                "name": "深绿主题",
                "description": "深绿色主题",
                "file": "dark_lightgreen.xml"
            },
            "light_purple": {
                "name": "浅紫主题",
                "description": "优雅的浅紫色主题",
                "file": "light_purple.xml"
            },
            "dark_purple": {
                "name": "深紫主题",
                "description": "神秘的深紫色主题",
                "file": "dark_purple.xml"
            },
            "light_teal": {
                "name": "浅青主题",
                "description": "清新的浅青色主题",
                "file": "light_teal.xml"
            },
            "dark_teal": {
                "name": "深青主题",
                "description": "深青色主题",
                "file": "dark_teal.xml"
            }
        }
    
    def set_app(self, app):
        """设置应用程序实例"""
        self.app = app
    
    def get_available_themes(self):
        """获取所有可用主题"""
        return self.filter_available_themes()
    
    def get_current_theme(self):
        """获取当前主题"""
        return self.current_theme
    
    def get_theme_name(self, theme_id):
        """获取主题名称"""
        return self.themes.get(theme_id, {}).get("name", theme_id)
    
    def apply_theme(self, theme_id):
        """应用主题"""
        if theme_id not in self.themes:
            return False
        
        if not self.app:
            return False
        
        try:
            theme_file = self.themes[theme_id]["file"]
            apply_stylesheet(self.app, theme=theme_file)
            self.current_theme = theme_id
            return True
        except Exception as e:
            print(f"应用主题失败: {e}")
            return False
    
    def set_current_theme(self, theme_id):
        """设置当前主题（不应用，仅更新状态）"""
        if theme_id in self.themes:
            self.current_theme = theme_id
            return True
        return False
    
    def load_theme_from_config(self, config_path):
        """从配置文件加载主题"""
        if os.path.exists(config_path):
            try:
                config = configparser.ConfigParser()
                config.read(config_path, encoding='utf-8')
                theme = config.get("Settings", "theme", fallback="light_blue")
                if theme in self.themes:
                    self.current_theme = theme
                    return theme
            except Exception as e:
                print(f"读取主题配置失败: {e}")
        return "light_blue"
    
    def save_theme_to_config(self, config_path):
        """保存主题到配置文件"""
        try:
            if os.path.exists(config_path):
                config = configparser.ConfigParser()
                config.read(config_path, encoding='utf-8')
                config.set("Settings", "theme", self.current_theme)
                with open(config_path, "w", encoding="utf-8") as f:
                    config.write(f)
            else:
                # 创建新配置文件
                with open(config_path, "w", encoding="utf-8") as f:
                    f.write("[Settings]\n")
                    f.write(f"theme = {self.current_theme}\n")
            return True
        except Exception as e:
            print(f"保存主题配置失败: {e}")
            return False
    
    def get_available_qt_material_themes(self):
        """获取 qt_material 实际支持的主题"""
        try:
            from qt_material import list_themes
            return list_themes()
        except ImportError:
            print("qt_material 未安装")
            return []
        except Exception as e:
            print(f"获取主题列表失败: {e}")
            return []
    
    def filter_available_themes(self):
        """过滤出实际可用的主题"""
        available_qt_themes = self.get_available_qt_material_themes()
        if not available_qt_themes:
            # 如果无法获取主题列表，返回常见主题（这些通常是可用的）
            common_themes = ["light_blue", "dark_blue", "light_lightgreen", "dark_lightgreen"]
            return {k: v for k, v in self.themes.items() if k in common_themes}
        
        # 过滤出实际存在的主题
        filtered_themes = {}
        for theme_id, theme_info in self.themes.items():
            if theme_info["file"] in available_qt_themes:
                filtered_themes[theme_id] = theme_info
            else:
                print(f"主题 {theme_id} ({theme_info['file']}) 不可用")
        
        # 如果过滤后没有主题，至少返回默认主题
        if not filtered_themes:
            return {k: v for k, v in self.themes.items() if k in ["light_blue", "dark_blue"]}
        
        return filtered_themes


class ThemeMenu(QMenu):
    """主题菜单"""
    
    def __init__(self, theme_manager, parent=None):
        super().__init__("主题", parent)
        self.theme_manager = theme_manager
        self.parent = parent
        self.create_theme_actions()
    
    def create_theme_actions(self):
        """创建主题动作"""
        # 清除现有动作
        self.clear()
        
        themes = self.theme_manager.get_available_themes()
        current_theme = self.theme_manager.get_current_theme()
        
        for theme_id, theme_info in themes.items():
            action = QAction(theme_info["name"], self)
            action.setCheckable(True)
            action.setChecked(theme_id == current_theme)
            action.triggered.connect(lambda checked, tid=theme_id: self.on_theme_selected(tid))
            self.addAction(action)
    
    def on_theme_selected(self, theme_id):
        """主题选择处理"""
        if self.theme_manager.apply_theme(theme_id):
            # 更新菜单状态
            self.create_theme_actions()
            
            # 保存配置
            if hasattr(self.parent, 'save_config'):
                self.parent.save_config()
            
            # 显示提示
            theme_name = self.theme_manager.get_theme_name(theme_id)
            if hasattr(self.parent, 'status_bar'):
                self.parent.status_bar.showMessage(f"已切换到 {theme_name}", 2000)
    
    def update_menu_state(self):
        """更新菜单状态（不重新创建，仅更新选中状态）"""
        themes = self.theme_manager.get_available_themes()
        current_theme = self.theme_manager.get_current_theme()
        
        for action in self.actions():
            if action.isCheckable():
                # 通过动作文本找到对应的主题ID
                for theme_id, theme_info in themes.items():
                    if action.text() == theme_info["name"]:
                        action.setChecked(theme_id == current_theme)
                        break
