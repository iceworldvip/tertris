# 俄罗斯方块项目代码审查报告

## 📋 执行摘要

本项目是一个支持双人对战和道具系统的俄罗斯方块游戏，采用 FastAPI + WebSocket + Vanilla JS 架构。经过全面审查，发现了若干架构和代码质量问题。

***

## 🔴 严重问题 (Critical)

### 1. 后端 main.py 过于庞大

**文件**: [`backend/main.py`](backend/main.py)
**问题**: 800+ 行代码，包含模型、业务逻辑、WebSocket处理、路由等所有内容
**影响**:

- 违反单一职责原则
- 代码难以维护
- 团队协作困难
- 测试困难

**建议重构**:

```
backend/
├── main.py              # 入口和路由注册
├── config.py            # 配置常量
├── models/
│   ├── __init__.py
│   ├── game.py          # TetrisGame, Tetromino
│   ├── room.py          # BattleRoom, RoomManager
│   └── items.py         # ItemType, 道具逻辑
├── services/
│   ├── __init__.py
│   ├── game_service.py
│   └── room_service.py
└── websocket/
    ├── __init__.py
    └── handlers.py      # WebSocket 消息处理器
```

### 2. WebSocket 连接管理问题

**文件**: [`backend/main.py:312`](backend/main.py:312)
**问题**: 使用 `Dict[WebSocket, dict]` 存储连接信息

```python
self.connections: Dict[WebSocket, dict] = {}
```

**风险**:

- 内存泄漏（WebSocket 对象作为 key 可能无法正确释放）
- 类型注解错误（Pylance 报告 WebSocket 不能作为 dict key）
- 连接断开时清理可能不彻底

**建议**:

```python
# 使用连接 ID 作为 key
self.connections: Dict[str, dict] = {}  # conn_id -> connection_info
# 或使用 WeakKeyDictionary
from weakref import WeakKeyDictionary
self.connections: WeakKeyDictionary[WebSocket, dict] = WeakKeyDictionary()
```

### 3. 缺少事务性操作

**问题**: 道具效果、游戏状态变更没有原子性保证
**风险**: 并发情况下可能出现状态不一致

**建议**: 使用锁或异步队列处理状态变更

***

## 🟡 中等问题 (Major)

### 4. 魔法数字泛滥

**文件**: [`backend/main.py`](backend/main.py), [`frontend/js/tetris.js`](frontend/js/tetris.js)
**问题**: 大量硬编码数字

```python
# 后端
if lines_cleared >= 10:  # 道具触发条件
if current_time - self.last_hard_drop_time < 500:  # 防抖时间
self.moveDelay = 100  # 移动延迟

# 前端
this.hardDropDelay = 500;
this.moveDelay = 100;
```

**建议**: 提取为配置常量

```python
# backend/config.py
class GameConfig:
    ITEM_TRIGGER_LINES = 10
    HARD_DROP_COOLDOWN_MS = 500
    MOVE_DELAY_MS = 100
    MAX_PAUSE_COUNT = 3
    GAME_WIDTH = 10
    GAME_HEIGHT = 20
```

### 5. 前端代码过于庞大

**文件**: [`frontend/js/tetris.js`](frontend/js/tetris.js)
**问题**: 900+ 行，包含所有逻辑
**建议拆分为**:

```
frontend/js/
├── main.js          # 入口
├── game/
│   ├── core.js      # 游戏核心逻辑
│   ├── items.js     # 道具系统
│   └── controls.js  # 键盘控制
├── network/
│   └── websocket.js # WebSocket 连接
├── ui/
│   ├── renderer.js  # Canvas 渲染
│   ├── modals.js    # 弹窗管理
│   └── keyconfig.js # 按键设置
└── utils/
    └── helpers.js   # 工具函数
```

### 6. 错误处理不完善

**文件**: [`backend/main.py`](backend/main.py)
**问题**: WebSocket 消息处理缺少 try-except

```python
# 当前代码
message = json.loads(data)
msg_type = message.get("type")

# 如果 json 解析失败或缺少 type 字段，会抛出异常
```

**建议**:

```python
async def room_websocket(websocket: WebSocket, room_id: str):
    try:
        # ...
        async for data in websocket.iter_text():
            try:
                message = json.loads(data)
                await handle_message(websocket, message, room)
            except json.JSONDecodeError:
                await send_error(websocket, "Invalid JSON")
            except KeyError as e:
                await send_error(websocket, f"Missing field: {e}")
            except Exception as e:
                logger.exception("Error handling message")
                await send_error(websocket, "Internal error")
    except WebSocketDisconnect:
        # ...
```

### 7. 类型注解问题

**问题**: 大量 Pylance 类型错误未修复
**影响**: IDE 支持差，容易引入类型错误

**建议**: 修复类型注解或添加 `# type: ignore` 注释

***

## 🟢 架构改进建议

### 8. 引入事件驱动架构

**当前问题**: 道具效果直接调用，耦合度高

```python
# 当前
elif action == "hard_drop":
    game.hard_drop()
```

**建议**: 使用事件总线

```python
class EventBus:
    def emit(self, event: GameEvent):
        pass

# 使用
action_event = ActionEvent(action_type, player_id)
event_bus.emit(action_event)
```

### 9. 添加数据库持久化

**当前问题**: 所有数据在内存，重启后丢失

**建议**:

```python
# 使用 Redis 保存房间状态
import redis
redis_client = redis.Redis()

# 房间状态定期保存
async def save_room_state(room_id: str):
    state = room.get_state()
    redis_client.setex(f"room:{room_id}", 3600, json.dumps(state))
```

### 10. 引入测试框架

**当前问题**: 测试覆盖率低

**建议**:

```python
# 使用 pytest + pytest-asyncio
# 添加 tests/
├── conftest.py          # 共享fixture
├── test_models/
│   ├── test_game.py     # TetrisGame 测试
│   └── test_room.py     # BattleRoom 测试
├── test_services/
│   └── test_gameplay.py # 游戏流程测试
└── test_websocket/
    └── test_messages.py # WebSocket 消息测试
```

### 11. 添加监控和日志

**建议**:

```python
import structlog
logger = structlog.get_logger()

# 结构化日志
logger.info("game_action", 
    action="hard_drop", 
    player_id=player_id,
    room_id=room_id
)
```

### 12. CI/CD 配置

**建议添加** **`.github/workflows/ci.yml`**:

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install -r backend/requirements.txt
      - run: pip install pytest pytest-asyncio
      - run: pytest backend/tests/
      - run: python -m py_compile backend/main.py
```

***

## 📊 优先级矩阵

| 优先级   | 任务     | 影响        | 工作量 | 建议时间 |
| ----- | ------ | --------- | --- | ---- |
| 🔴 P0 | 拆分后端代码 | 维护性↑↑↑    | 中   | 1-2天 |
| 🔴 P0 | 修复类型注解 | 代码质量↑↑    | 小   | 半天   |
| 🟡 P1 | 添加配置常量 | 可维护性↑↑    | 小   | 2小时  |
| 🟡 P1 | 前端模块化  | 性能↑ 维护性↑↑ | 中   | 1-2天 |
| 🟡 P1 | 完善错误处理 | 稳定性↑↑     | 小   | 半天   |
| 🟢 P2 | 事件驱动重构 | 扩展性↑↑     | 大   | 3-5天 |
| 🟢 P2 | 数据库持久化 | 可靠性↑↑     | 中   | 1-2天 |
| 🟢 P2 | 测试框架   | 质量↑↑      | 中   | 1-2天 |
| ⚪ P3  | CI/CD  | 效率↑       | 小   | 2小时  |

***

## 💡 立即可执行的改进

### 1. 创建配置文件

```python
# backend/config.py
from dataclasses import dataclass

@dataclass(frozen=True)
class GameConfig:
    GAME_WIDTH: int = 10
    GAME_HEIGHT: int = 20
    ITEM_TRIGGER_LINES: int = 10
    HARD_DROP_COOLDOWN_MS: int = 500
    MOVE_DELAY_MS: int = 100
    MAX_PAUSE_COUNT: int = 3
    AUTO_FALL_INTERVAL: float = 1.0

CONFIG = GameConfig()
```

### 2. 创建工具模块

```python
# backend/utils.py
import logging
from functools import wraps

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def handle_errors(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Error in {func.__name__}")
            raise
    return wrapper
```

### 3. 添加输入验证

```python
from pydantic import BaseModel, validator

class GameAction(BaseModel):
    action: str
    
    @validator('action')
    def validate_action(cls, v):
        allowed = {'move_left', 'move_right', 'move_down', 'rotate', 'hard_drop', 'pause'}
        if v not in allowed:
            raise ValueError(f'Invalid action: {v}')
        return v
```

***

## 🎯 重构路线图

### Phase 1: 基础设施 (1周)

- [ ] 拆分后端代码结构
- [ ] 添加配置系统
- [ ] 完善错误处理
- [ ] 修复类型注解

### Phase 2: 质量保证 (1周)

- [ ] 前端模块化
- [ ] 添加测试框架
- [ ] 添加 CI/CD
- [ ] 代码审查流程

### Phase 3: 架构升级 (2-3周)

- [ ] 事件驱动重构
- [ ] 数据库持久化
- [ ] 性能优化
- [ ] 监控告警

***

## 📈 代码质量评分

| 维度    | 当前  | 目标   | 差距 |
| ----- | --- | ---- | -- |
| 可维护性  | ⭐⭐  | ⭐⭐⭐⭐ | -2 |
| 可测试性  | ⭐⭐  | ⭐⭐⭐⭐ | -2 |
| 可扩展性  | ⭐⭐⭐ | ⭐⭐⭐⭐ | -1 |
| 代码规范  | ⭐⭐  | ⭐⭐⭐  | -1 |
| 文档完整性 | ⭐⭐  | ⭐⭐⭐⭐ | -2 |

***

## ✅ 总结

本项目功能完整但架构需要优化。建议优先处理：

1. **后端代码拆分** - 提高可维护性
2. **类型注解修复** - 提高代码质量
3. **错误处理完善** - 提高稳定性

完整重构需要 3-4 周时间，可以分阶段进行。

***

*报告生成时间: 2024-03-14*
*审查工具: 静态代码分析 + 架构审查*
