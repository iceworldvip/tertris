# 俄罗斯方块游戏项目

完整的多平台俄罗斯方块游戏，包含Web版（FastAPI + HTML5 Canvas）、Android App（Jetpack Compose）以及独立运行的Python版本。

## 项目结构

```
.
├── backend/                    # FastAPI 后端
│   ├── main.py                 # 主程序
│   ├── requirements.txt        # 依赖
│   ├── __init__.py
│   ├── legacy/                 # 独立运行版本
│   │   ├── tetris_curses.py    # Curses终端版
│   │   ├── tetris_pygame.py    # Pygame图形版
│   │   ├── tetris_console.py   # Windows控制台版
│   │   └── __init__.py
│   └── tests/                  # 测试脚本
│       ├── test_api.py         # API测试
│       ├── test_clear_lines.py # 消行测试
│       └── __init__.py
├── frontend/                   # Web前端
│   ├── index.html              # 主页面
│   ├── css/
│   │   └── style.css           # 样式
│   └── js/
│       └── tetris.js           # 游戏逻辑
├── android/                    # Android项目
│   ├── app/
│   │   └── src/main/java/com/tetris/android/
│   │       ├── MainActivity.kt
│   │       ├── model/
│   │       ├── network/
│   │       ├── ui/
│   │       └── viewmodel/
│   └── ...
├── run_server.py               # 后端启动脚本
└── README.md
```

## 快速开始

### Web 版

1. 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

2. 启动服务
```bash
cd ..
python run_server.py
```

3. 访问游戏
打开浏览器: http://localhost:8000

### Android 版

1. 打开 Android Studio
2. 导入 `android` 目录
3. 配置模拟器或真机
4. 点击运行

### 独立运行版本

```bash
# Pygame 版（需安装 pygame）
cd backend/legacy
python tetris_pygame.py

# Curses 终端版（Windows需安装 windows-curses）
python tetris_curses.py

# Windows 控制台版
python tetris_console.py
```

## 功能特性

### 后端 (FastAPI)
- ✅ RESTful API 创建/控制游戏
- ✅ WebSocket 实时状态同步
- ✅ 7种经典方块形状
- ✅ 方块旋转与碰撞检测
- ✅ 消行计分系统
- ✅ 等级系统（速度递增）
- ✅ 自动下落
- ✅ 多游戏会话支持

### 前端 (HTML5)
- ✅ Canvas 渲染游戏画面
- ✅ WebSocket 实时通信
- ✅ 键盘控制（方向键 + 空格）
- ✅ 下一个方块预览
- ✅ 分数/行数/等级显示
- ✅ 暂停/继续功能
- ✅ 响应式设计

### Android
- ✅ Jetpack Compose UI
- ✅ 实时WebSocket同步
- ✅ 触摸控制
- ✅ Material Design 3

## API 接口

### REST API

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/games` | 创建新游戏 |
| GET | `/api/games/{game_id}` | 获取游戏状态 |
| POST | `/api/games/{game_id}/action` | 执行动作 |
| DELETE | `/api/games/{game_id}` | 删除游戏 |

### WebSocket

连接: `ws://localhost:8000/ws/{game_id}`

消息格式:
```json
// 客户端发送
{"action": "move_left"}  // move_left, move_right, move_down, rotate, hard_drop, pause, reset

// 服务器返回
{"type": "state_update", "data": {...}}
```

## 操作说明

| 按键 | 功能 |
|------|------|
| ← | 左移 |
| → | 右移 |
| ↑ | 旋转 |
| ↓ | 加速下落 |
| 空格 | 直接落下 |
| P | 暂停/继续 |

## 开发

### 运行测试

```bash
# API测试
python backend/tests/test_api.py

# 消行功能测试
python backend/tests/test_clear_lines.py
```

### 代码格式化

```bash
black backend/
```

## 依赖说明

### 必需依赖
- `fastapi>=0.104.0` - Web框架
- `uvicorn[standard]>=0.24.0` - ASGI服务器
- `pydantic>=2.5.0` - 数据验证
- `websockets>=12.0` - WebSocket支持

### 可选依赖
- `pygame>=2.5.0` - Pygame版本
- `curses-windows` - Windows终端版本

## 许可证

MIT License
