#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
检查 qt_material 实际支持的主题
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


def main():
    """主函数"""
    print("🔍 检查 qt_material 支持的主题")
    print("=" * 50)

    try:
        from ThemeManager import ThemeManager

        # 创建主题管理器
        theme_manager = ThemeManager()

        # 获取 qt_material 实际支持的主题
        print("📋 qt_material 实际支持的主题:")
        available_qt_themes = theme_manager.get_available_qt_material_themes()
        if available_qt_themes:
            for theme in sorted(available_qt_themes):
                print(f"   - {theme}")
        else:
            print("   ❌ 无法获取主题列表（可能 qt_material 未安装）")

        print("\n🎨 我们定义的主题:")
        all_themes = theme_manager.themes
        for theme_id, theme_info in all_themes.items():
            status = "✅" if theme_info["file"] in available_qt_themes else "❌"
            print(
                f"   {status} {theme_id}: {theme_info['name']} ({theme_info['file']})")

        print("\n🔧 过滤后的可用主题:")
        filtered_themes = theme_manager.filter_available_themes()
        for theme_id, theme_info in filtered_themes.items():
            print(f"   ✅ {theme_id}: {theme_info['name']}")

        print(f"\n📊 统计:")
        print(f"   总定义主题: {len(all_themes)}")
        print(
            f"   qt_material 支持: {len(available_qt_themes) if available_qt_themes else 0}")
        print(f"   实际可用主题: {len(filtered_themes)}")

        if not available_qt_themes:
            print("\n💡 建议:")
            print("   1. 确保已安装 qt_material: pip install qt-material")
            print("   2. 检查 qt_material 版本是否兼容")
            print("   3. 使用默认主题: light_blue, dark_blue")

    except ImportError as e:
        print("❌ 导入错误: {}".format(e))
        print("请确保已安装所有依赖: pip install -r requirements.txt")
    except Exception as e:
        print("❌ 运行错误: {}".format(e))


if __name__ == "__main__":
    main()
