# 俄罗斯方块项目重构优化方案

## 一、现状分析

### 1.1 重复代码问题

#### 1.1.1 按键配置系统重复（严重）
当前在三个文件中存在完全重复的按键配置逻辑：

| 文件 | 重复内容 | 行数 |
|------|---------|------|
| `tetris.js` | DEFAULT_KEY_CONFIG, KEY_NAME_MAP, load/save/reset 方法 | ~150行 |
| `ai-game.js` | 相同的配置和方法 | ~150行 |
| `solo.js` | 相同的配置和方法 | ~150行 |

**重复代码示例：**
```javascript
// 三个文件中都存在以下重复代码：
loadKeyConfig() { ... }
saveKeyConfig() { ... }
resetKeyConfig() { ... }
createKeyConfigModal() { ... }
updateKeyConfigUI() { ... }
startKeyBinding() { ... }
handleKeyBinding() { ... }
```

#### 1.1.2 CSS 样式重复
按键设置弹窗的 CSS 在以下文件中重复定义：
- `solo.html` (~100行)
- `single.html` (~100行)
- `index.html` (可能也有)

#### 1.1.3 游戏配置重复
```javascript
// solo.js 和 ai-game.js 中重复定义
const CONFIG = {
    BOARD_WIDTH: 10,
    BOARD_HEIGHT: 20,
    BLOCK_SIZE: 30,
    ...
};

// 方块形状和颜色定义重复
const SHAPES = [...];
const COLORS = [...];
```

#### 1.1.4 昵称生成逻辑重复
```javascript
// ai-game.js 和 tetris.js 中都存在
const adjectives = ['快乐的', '聪明的', ...];
const nouns = ['熊猫', '老虎', ...];
```

### 1.2 硬编码问题

#### 1.2.1 API 端点硬编码
```javascript
// 散落在各处的 API 调用
await fetch('/api/ai/rooms', ...)
await fetch('/api/leaderboard/submit', ...)
await fetch('/api/rooms', ...)
```

#### 1.2.2 WebSocket 端点硬编码
```javascript
this.ws = new WebSocket(`ws://${window.location.host}/ws/room/${roomId}`);
```

#### 1.2.3 本地存储键名硬编码且不一致
```javascript
// solo.js
localStorage.getItem('solo_key_config')

// ai-game.js
localStorage.getItem('tetrisKeyConfig')

// tetris.js
localStorage.getItem('tetris_key_config')
```

#### 1.2.4 难度配置硬编码
```javascript
// ai-game.js 中
const desc = {
    'easy': 'AI随机落子，移动缓慢，适合新手练习',
    'normal': 'AI会评估位置，偶尔失误，适合普通玩家',
    'hard': 'AI采用最优策略，反应迅速，挑战性极高'
};
```

## 二、重构方案

### 2.1 前端架构重构

```
frontend/
├── js/
│   ├── config/
│   │   ├── game.config.js      # 游戏常量配置
│   │   ├── api.config.js       # API 端点配置
│   │   └── key-bindings.config.js  # 默认按键配置
│   ├── core/
│   │   ├── KeyConfigManager.js   # 按键配置管理器
│   │   ├── GameConfig.js         # 游戏配置管理
│   │   └── APIService.js         # API 服务封装
│   ├── utils/
│   │   ├── nickname.generator.js # 昵称生成器
│   │   └── storage.js            # 本地存储封装
│   └── games/
│       ├── solo.js
│       ├── ai-game.js
│       └── tetris.js
└── css/
    ├── components/
    │   ├── key-config-modal.css   # 按键设置弹窗样式
    │   └── buttons.css            # 按钮组件样式
    └── main.css
```

### 2.2 创建共享模块

#### 2.2.1 KeyConfigManager 类
```javascript
// frontend/js/core/KeyConfigManager.js
export class KeyConfigManager {
    static DEFAULT_CONFIG = { ... };
    static KEY_NAME_MAP = { ... };
    
    constructor(storageKey) {
        this.storageKey = storageKey;
        this.config = this.load();
    }
    
    load() { ... }
    save() { ... }
    reset() { ... }
    getDisplayName(key) { ... }
    bindKey(action, key) { ... }
    
    // 创建 UI 方法
    createModal(container) { ... }
    showModal() { ... }
    hideModal() { ... }
}
```

#### 2.2.2 API 配置中心
```javascript
// frontend/js/config/api.config.js
export const API_CONFIG = {
    BASE_URL: '',
    ENDPOINTS: {
        AI_ROOMS: '/api/ai/rooms',
        ROOMS: '/api/rooms',
        LEADERBOARD: '/api/leaderboard',
        // ...
    },
    WS_ENDPOINTS: {
        ROOM: (roomId) => `/ws/room/${roomId}`,
        AI: (roomId) => `/ws/ai/${roomId}`,
    }
};
```

#### 2.2.3 游戏常量配置
```javascript
// frontend/js/config/game.config.js
export const GAME_CONFIG = {
    BOARD: {
        WIDTH: 10,
        HEIGHT: 20,
        BLOCK_SIZE: 30
    },
    TIMING: {
        TICK_RATE: 1000,
        LEVEL_SPEEDUP: 50,
        MIN_TICK_RATE: 100
    },
    SHAPES: [...],
    COLORS: [...]
};
```

### 2.3 后端配置化

```
backend/
├── config/
│   ├── game_settings.yaml     # 游戏参数配置
│   ├── ai_difficulty.yaml     # AI难度配置
│   └── items.yaml             # 道具配置
```

#### 2.3.1 AI难度配置化
```yaml
# backend/config/ai_difficulty.yaml
difficulties:
  easy:
    move_delay: 2.0
    mistake_rate: 0.3
    description: "AI随机落子，移动缓慢，适合新手练习"
  
  normal:
    move_delay: 1.0
    mistake_rate: 0.1
    description: "AI会评估位置，偶尔失误，适合普通玩家"
  
  hard:
    move_delay: 0.3
    mistake_rate: 0.0
    description: "AI采用最优策略，反应迅速，挑战性极高"
```

#### 2.3.2 道具配置化
```yaml
# backend/config/items.yaml
items:
  add_garbage:
    name: "垃圾行"
    icon: "🗑️"
    target_type: "opponent"
    description: "给对手添加3行垃圾"
  
  clear_line:
    name: "清行"
    icon: "✨"
    target_type: "self"
    description: "消除最下面一行"
```

## 三、实施计划

### 阶段1：提取共享配置（优先级：高）
1. 创建 `frontend/js/config/` 目录
2. 提取 GAME_CONFIG
3. 提取 API_CONFIG
4. 统一本地存储键名

### 阶段2：创建 KeyConfigManager（优先级：高）
1. 创建 KeyConfigManager 类
2. 重构 tetris.js
3. 重构 ai-game.js
4. 重构 solo.js

### 阶段3：CSS 组件化（优先级：中）
1. 创建 CSS 组件目录
2. 提取 key-config-modal.css
3. 更新 HTML 文件引用

### 阶段4：后端配置化（优先级：中）
1. 创建 YAML 配置文件
2. 实现配置加载器
3. 重构 AI 玩家类
4. 重构道具系统

### 阶段5：工具函数提取（优先级：低）
1. 提取昵称生成器
2. 提取存储工具
3. 创建工具函数库

## 四、预期收益

| 指标 | 当前 | 预期 | 改善 |
|------|------|------|------|
| 重复代码行数 | ~500行 | ~50行 | -90% |
| 配置修改点 | 6+处 | 1处 | -83% |
| 新增模式开发成本 | 2天 | 4小时 | -75% |
| 维护复杂度 | 高 | 低 | 显著改善 |

## 五、风险评估

### 低风险
- 配置提取：只涉及常量移动，不影响业务逻辑
- CSS 组件化：样式不变，只改变组织方式

### 中风险
- KeyConfigManager 重构：需要测试所有按键功能
- 建议：分文件逐步替换，保留原代码备份

### 高风险
- 后端配置化：需要修改运行时行为
- 建议：先实现配置加载，再逐步替换硬编码
