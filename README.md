# Tertris - 俄罗斯方块在线对战

基于 FastAPI + WebSocket 的实时俄罗斯方块对战游戏，支持单人对战、AI 对战和多人匹配对战。

## 功能特性

### 🎮 游戏模式
- **Solo 模式** - 单人积分赛，挑战高分
- **AI 对战** - 与三个难度等级的 AI 对战（简单/普通/困难）
- **多人对战** - 创建房间与好友实时对战

### ⚡ 技术特性
- 实时 WebSocket 通信
- 自动匹配系统
- 道具系统（垃圾行、消除行）
- 排行榜系统
- 完整的单元测试覆盖（220+ 测试）
- UI 自动化测试（Playwright）

## 快速开始

### 安装依赖

```bash
pip install -e ".[dev]"
```

### 启动服务

```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 访问游戏

- 主对战页面: http://localhost:8000/
- 单人模式: http://localhost:8000/solo
- AI 对战: http://localhost:8000/single
- 排行榜: http://localhost:8000/leaderboard
- API 文档: http://localhost:8000/docs

## 项目结构

```
tertris/
├── backend/                    # FastAPI 后端
│   ├── main.py                 # 主程序入口
│   ├── config.py              # 配置常量
│   ├── models/                 # 数据模型
│   │   ├── game.py            # 游戏核心逻辑
│   │   ├── tetromino.py        # 方块定义
│   │   ├── room.py             # 对战房间
│   │   ├── ai_room.py          # AI 房间
│   │   ├── ai_player.py        # AI 玩家
│   │   ├── items.py            # 道具系统
│   │   └── leaderboard.py      # 排行榜
│   ├── handlers/               # 请求处理器
│   │   ├── websocket.py        # WebSocket 处理器
│   │   └── ai_websocket.py    # AI 对战处理器
│   ├── utils/                 # 工具函数
│   ├── tests/                 # 测试
│   │   ├── unit/              # 单元测试
│   │   │   ├── test_game.py
│   │   │   ├── test_tetromino.py
│   │   │   ├── test_room.py
│   │   │   ├── test_ai_player.py
│   │   │   ├── test_ai_room.py
│   │   │   └── test_items.py
│   │   └── test_ui_automation.py  # UI 自动化测试
│   └── legacy/                # 独立运行版本
│       ├── tetris_pygame.py   # Pygame 图形版
│       ├── tetris_curses.py    # Curses 终端版
│       └── tetris_console.py   # 控制台版
├── frontend/                   # Web 前端
│   ├── index.html            # 主对战页面
│   ├── solo.html             # 单人模式
│   ├── single.html           # AI 对战页面
│   ├── leaderboard.html      # 排行榜页面
│   ├── css/                  # 样式文件
│   └── js/                   # 游戏逻辑
│       ├── solo.js           # 单人游戏逻辑
│       ├── tetris.js         # 对战游戏逻辑
│       └── ai-game.js        # AI 对战逻辑
├── .github/workflows/         # CI/CD 配置
│   ├── ci.yml               # 持续集成
│   └── cd.yml               # 持续部署
├── pyproject.toml            # Python 项目配置
└── LICENSE                  # MIT 许可证
```

## 游戏操作

| 按键 | 功能 |
|------|------|
| ← | 左移 |
| → | 右移 |
| ↑ | 旋转 |
| ↓ | 加速下落 |
| 空格 | 直接落下（硬降） |
| P | 暂停/继续 |

## API 接口

### REST API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/rooms` | 获取房间列表 |
| POST | `/api/rooms` | 创建对战房间 |
| GET | `/api/rooms/{room_id}` | 获取房间详情 |
| POST | `/api/ai/rooms` | 创建 AI 对战房间 |
| GET | `/api/ai/rooms` | 获取 AI 房间列表 |
| POST | `/api/leaderboard/submit` | 提交分数 |
| GET | `/api/leaderboard` | 获取排行榜 |

### WebSocket

- 对战房间: `ws://localhost:8000/ws/room/{room_id}`
- AI 房间: `ws://localhost:8000/ws/ai/{room_id}`

## 开发

### 运行测试

```bash
# 单元测试
pytest backend/tests/unit -v

# UI 自动化测试
python backend/tests/test_ui_automation.py
```

### 代码质量

```bash
# 代码格式化
black backend/

# 类型检查
mypy backend/

# 代码检查
ruff check backend/
```

## 测试覆盖

- ✅ 游戏核心逻辑（碰撞检测、消行、计分）
- ✅ 7 种方块形状及旋转
- ✅ AI 玩家（Pierre Dellacherie 算法）
- ✅ 多人房间系统
- ✅ 道具系统
- ✅ UI 自动化测试

## 技术栈

**后端:**
- FastAPI - Web 框架
- WebSocket - 实时通信
- Pydantic - 数据验证
- SQLite - 数据持久化

**前端:**
- HTML5 Canvas - 游戏渲染
- 原生 JavaScript - 游戏逻辑
- CSS3 - 样式设计

**测试:**
- Pytest - 单元测试
- Playwright - UI 自动化测试

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件
