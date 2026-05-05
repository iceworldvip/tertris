#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tetris UI Automation Test

使用 Playwright 进行俄罗斯方块游戏的 UI 自动化测试。
测试内容：
1. 打开游戏页面
2. 点击开始按钮
3. 自动执行游戏操作（移动、旋转、硬降）
4. 验证游戏状态
5. 验证游戏结束流程
"""

import asyncio
import time
from typing import Optional

from playwright.async_api import async_playwright, Page, Browser, Playwright


class TetrisAutomation:
    """Tetris 游戏自动化测试类"""

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright: Optional[Playwright] = None
        self.base_url = "http://localhost:8000"
        self.game_url = f"{self.base_url}/solo"

    async def setup(self):
        """初始化浏览器和页面"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()
        print(f"✅ 浏览器已启动")

    async def teardown(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        print("✅ 浏览器已关闭")

    async def open_game(self):
        """打开游戏页面"""
        print(f"🌐 正在打开游戏页面: {self.game_url}")
        await self.page.goto(self.game_url)
        await self.page.wait_for_load_state("networkidle")
        print("✅ 页面加载完成")

    async def click_start_button(self):
        """点击开始按钮"""
        print("🎮 点击开始按钮...")
        start_button = self.page.locator("#btn-start")
        await start_button.click()
        await asyncio.sleep(0.5)
        print("✅ 游戏已开始")

    async def move_left(self):
        """向左移动"""
        await self.page.keyboard.press("ArrowLeft")
        await asyncio.sleep(0.05)

    async def move_right(self):
        """向右移动"""
        await self.page.keyboard.press("ArrowRight")
        await asyncio.sleep(0.05)

    async def move_down(self):
        """向下移动（软降）"""
        await self.page.keyboard.press("ArrowDown")
        await asyncio.sleep(0.05)

    async def rotate(self):
        """旋转方块"""
        await self.page.keyboard.press("ArrowUp")
        await asyncio.sleep(0.05)

    async def hard_drop(self):
        """硬降（直接落到底部）"""
        await self.page.keyboard.press(" ")
        await asyncio.sleep(0.1)

    async def pause_game(self):
        """暂停游戏"""
        await self.page.keyboard.press("p")
        await asyncio.sleep(0.3)
        await self.page.keyboard.press("p")  # 再按一次取消暂停
        print("⏸️  暂停/恢复测试完成")

    async def get_score(self) -> int:
        """获取当前分数"""
        score_element = self.page.locator("#score")
        score_text = await score_element.text_content()
        return int(score_text) if score_text else 0

    async def get_level(self) -> int:
        """获取当前等级"""
        level_element = self.page.locator("#level")
        level_text = await level_element.text_content()
        return int(level_text) if level_text else 0

    async def get_lines(self) -> int:
        """获取已消除行数"""
        lines_element = self.page.locator("#lines")
        lines_text = await lines_element.text_content()
        return int(lines_text) if lines_text else 0

    async def is_game_over_visible(self) -> bool:
        """检查游戏结束界面是否可见"""
        overlay = self.page.locator("#game-over-overlay")
        is_hidden = await overlay.get_attribute("class")
        return "hidden" not in (is_hidden or "")

    async def play_automatic_moves(self, num_moves: int = 50):
        """
        执行自动游戏操作

        Args:
            num_moves: 执行的操作次数
        """
        print(f"🎮 开始自动游戏 ({num_moves} 步)...")

        for i in range(num_moves):
            # 随机选择一个操作
            import random
            action = random.choice(['left', 'right', 'down', 'rotate', 'hard_drop'])

            if action == 'left':
                await self.move_left()
            elif action == 'right':
                await self.move_right()
            elif action == 'down':
                await self.move_down()
            elif action == 'rotate':
                await self.rotate()
            elif action == 'hard_drop':
                await self.hard_drop()

            # 每10步显示一次状态
            if (i + 1) % 10 == 0:
                score = await self.get_score()
                level = await self.get_level()
                lines = await self.get_lines()
                print(f"   进度: {i + 1}/{num_moves} | 分数: {score} | 等级: {level} | 消行: {lines}")

            # 检查是否游戏结束
            if await self.is_game_over_visible():
                print("⚠️  游戏结束")
                break

            # 短暂等待避免操作过快
            await asyncio.sleep(0.05)

        print("✅ 自动游戏完成")

    async def verify_game_elements(self):
        """验证游戏元素是否存在"""
        print("🔍 验证游戏元素...")

        elements = [
            ("#game-canvas", "游戏画布"),
            ("#next-canvas", "下一个方块画布"),
            ("#btn-start", "开始按钮"),
            ("#btn-restart", "重新开始按钮"),
            ("#score", "分数显示"),
            ("#level", "等级显示"),
            ("#lines", "消行显示"),
        ]

        for selector, name in elements:
            element = self.page.locator(selector)
            is_visible = await element.is_visible()
            status = "✅" if is_visible else "❌"
            print(f"   {status} {name} ({selector})")

        print("✅ 元素验证完成")

    async def run_test(self):
        """运行完整的自动化测试"""
        print("=" * 50)
        print("🎮 Tetris UI 自动化测试开始")
        print("=" * 50)

        try:
            # 1. 初始化
            await self.setup()

            # 2. 打开游戏页面
            await self.open_game()

            # 3. 验证游戏元素
            await self.verify_game_elements()

            # 4. 开始游戏
            await self.click_start_button()

            # 5. 测试暂停功能
            await self.pause_game()

            # 6. 执行自动游戏
            await self.play_automatic_moves(100)

            # 7. 获取最终状态
            final_score = await self.get_score()
            final_level = await self.get_level()
            final_lines = await self.get_lines()

            print("\n" + "=" * 50)
            print("📊 游戏统计")
            print("=" * 50)
            print(f"   最终分数: {final_score}")
            print(f"   最终等级: {final_level}")
            print(f"   总消行数: {final_lines}")

            # 8. 检查游戏是否正常结束
            game_over = await self.is_game_over_visible()
            if game_over:
                print("   游戏结束界面: ✅ 显示正常")
            else:
                print("   游戏仍在进行中 (100步未结束)")

            print("=" * 50)
            print("✅ UI 自动化测试完成!")
            print("=" * 50)

        except Exception as e:
            print(f"❌ 测试失败: {e}")
            raise
        finally:
            await self.teardown()


async def main():
    """主函数"""
    test = TetrisAutomation()
    await test.run_test()


if __name__ == "__main__":
    asyncio.run(main())
