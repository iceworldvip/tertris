/**
 * 全局配置中心
 * 兼容普通 script 标签加载方式
 */

(function(global) {
    'use strict';

    // 游戏板配置
    const BOARD_CONFIG = {
        WIDTH: 10,
        HEIGHT: 20,
        BLOCK_SIZE: 30
    };

    // 游戏时序配置
    const TIMING_CONFIG = {
        TICK_RATE: 1000,
        LEVEL_SPEEDUP: 50,
        MIN_TICK_RATE: 100,
        MOVE_DELAY: 100,
        HARD_DROP_DELAY: 500,
        PAUSE_DELAY: 500
    };

    // 方块形状定义
    const SHAPES = [
        [[0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]],
        [[1, 1], [1, 1]],
        [[0, 1, 0], [1, 1, 1]],
        [[1, 0, 0], [1, 1, 1]],
        [[0, 0, 1], [1, 1, 1]],
        [[0, 1, 1], [1, 1, 0]],
        [[1, 1, 0], [0, 1, 1]]
    ];

    // 方块颜色配置
    const COLORS = [
        '#00f0f0', '#f0f000', '#a000f0',
        '#f0a000', '#0000f0', '#00f000', '#f00000'
    ];

    // API 端点
    const API_ENDPOINTS = {
        ROOMS: '/api/rooms',
        ROOM_COUNT: '/api/rooms/count',
        ROOM_DETAIL: (roomId) => `/api/rooms/${roomId}`,
        JOIN_ROOM: (roomId) => `/api/rooms/${roomId}/join`,
        AI_ROOMS: '/api/ai/rooms',
        AI_ROOM_DETAIL: (roomId) => `/api/ai/rooms/${roomId}`,
        LEADERBOARD: '/api/leaderboard',
        SUBMIT_SCORE: '/api/leaderboard/submit',
        PLAYER_HISTORY: '/api/leaderboard/player/history',
        PLAYER_STATS: '/api/leaderboard/player/stats',
        TOP_PLAYERS: '/api/leaderboard/top-players',
        HEALTH: '/health'
    };

    // WebSocket 端点
    const WS_ENDPOINTS = {
        ROOM: (roomId) => `/ws/room/${roomId}`,
        AI: (roomId) => `/ws/ai/${roomId}`,
        LEGACY: (gameId) => `/ws/${gameId}`
    };

    // localStorage 键名（统一）
    const STORAGE_KEYS = {
        SOLO_KEY_CONFIG: 'tetris_key_config_solo',
        AI_KEY_CONFIG: 'tetris_key_config_ai',
        VERSUS_KEY_CONFIG: 'tetris_key_config_versus',
        HIGH_SCORE: 'tetris_high_score',
        NICKNAME: 'tetris_nickname'
    };

    // 基础按键配置
    const BASE_KEY_CONFIG = {
        moveLeft: 'ArrowLeft',
        moveRight: 'ArrowRight',
        moveDown: 'ArrowDown',
        rotate: 'ArrowUp',
        hardDrop: ' ',
        pause: 'p'
    };

    // 完整按键配置
    const FULL_KEY_CONFIG = {
        ...BASE_KEY_CONFIG,
        item1: '1',
        item2: '2',
        item3: '3'
    };

    // AI 模式按键配置
    const AI_MODE_KEY_CONFIG = {
        ...BASE_KEY_CONFIG,
        item1: '1',
        item2: '2'
    };

    // 按键显示名称映射
    const KEY_NAME_MAP = {
        'ArrowLeft': '←',
        'ArrowRight': '→',
        'ArrowUp': '↑',
        'ArrowDown': '↓',
        ' ': '空格',
        'Space': '空格'
    };

    // 操作名称映射
    const ACTION_NAMES = {
        moveLeft: '左移',
        moveRight: '右移',
        moveDown: '下移',
        rotate: '旋转',
        hardDrop: '硬降',
        pause: '暂停',
        item1: '道具槽1',
        item2: '道具槽2',
        item3: '道具槽3'
    };

    // 昵称生成词库
    const NICKNAME_WORDS = {
        ADJECTIVES: ['快乐的', '聪明的', '勇敢的', '神秘的', '可爱的', '调皮的', '冷静的', '热情的'],
        NOUNS: ['熊猫', '老虎', '海豚', '企鹅', '狐狸', '兔子', '老鹰', '狮子', '小熊', '猫咪']
    };

    // 创建全局配置对象
    global.TETRIS_CONFIG = {
        BOARD: BOARD_CONFIG,
        TIMING: TIMING_CONFIG,
        SHAPES,
        COLORS,
        API: API_ENDPOINTS,
        WS: WS_ENDPOINTS,
        STORAGE: STORAGE_KEYS,
        KEYS: {
            BASE: BASE_KEY_CONFIG,
            FULL: FULL_KEY_CONFIG,
            AI_MODE: AI_MODE_KEY_CONFIG,
            NAME_MAP: KEY_NAME_MAP,
            ACTION_NAMES: ACTION_NAMES
        },
        NICKNAME: NICKNAME_WORDS
    };

})(window);
