#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TeslaCam Player 界面样式测试脚本
用于测试优化后的样式效果
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

try:
    from PyQt5.QtWidgets import QApplication
    from MainWindow import TeslaCamPlayer

    def main():
        """测试主函数"""
        app = QApplication(sys.argv)

        # 设置应用信息
        app.setApplicationName("TeslaCam Player UI Style Test")
        app.setApplicationVersion("1.0.0")

        # 创建主窗口
        window = TeslaCamPlayer()
        window.show()

        print("✅ TeslaCam Player 界面样式测试启动成功！")
        print("🎨 样式优化内容：")
        print("   - 现代化颜色主题")
        print("   - 优化的字体显示")
        print("   - 美化的按钮和控件")
        print("   - 改进的边框和圆角")
        print("   - 统一的视觉风格")
        print("")
        print("📋 测试步骤：")
        print("   1. 观察主窗口的整体样式")
        print("   2. 检查菜单栏和状态栏样式")
        print("   3. 测试按钮的悬停和点击效果")
        print("   4. 验证列表和滑块样式")
        print("   5. 检查下拉框样式")
        print("   6. 验证视频播放器边框")

        sys.exit(app.exec_())

except ImportError as e:
    print("❌ 导入错误: {}".format(e))
    print("请确保已安装所有依赖: pip install -r requirements.txt")
except Exception as e:
    print("❌ 运行错误: {}".format(e))

if __name__ == "__main__":
    main()
