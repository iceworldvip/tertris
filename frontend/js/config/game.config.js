/**
 * 游戏常量配置中心
 * 集中管理所有游戏相关的常量配置
 */

// 游戏板配置
export const BOARD_CONFIG = {
    WIDTH: 10,
    HEIGHT: 20,
    BLOCK_SIZE: 30
};

// 游戏时序配置
export const TIMING_CONFIG = {
    TICK_RATE: 1000,        // 初始下落间隔(ms)
    LEVEL_SPEEDUP: 50,      // 每级减少的间隔(ms)
    MIN_TICK_RATE: 100,     // 最小下落间隔(ms)
    MOVE_DELAY: 100,        // 移动防抖延迟(ms)
    HARD_DROP_DELAY: 500,   // 硬降防抖延迟(ms)
    PAUSE_DELAY: 500        // 暂停防抖延迟(ms)
};

// 方块形状定义
export const SHAPES = [
    [[0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]],  // I - 使用4x4矩阵以便正确旋转
    [[1, 1], [1, 1]],         // O
    [[0, 1, 0], [1, 1, 1]],   // T
    [[1, 0, 0], [1, 1, 1]],   // L
    [[0, 0, 1], [1, 1, 1]],   // J
    [[0, 1, 1], [1, 1, 0]],   // S
    [[1, 1, 0], [0, 1, 1]]    // Z
];

// 方块颜色配置
export const COLORS = [
    '#00f0f0', // I - 青色
    '#f0f000', // O - 黄色
    '#a000f0', // T - 紫色
    '#f0a000', // L - 橙色
    '#0000f0', // J - 蓝色
    '#00f000', // S - 绿色
    '#f00000'  // Z - 红色
];

// 方块显示名称
export const SHAPE_NAMES = ['I', 'O', 'T', 'L', 'J', 'S', 'Z'];

// 游戏模式配置
export const GAME_MODES = {
    SOLO: {
        name: '积分赛',
        description: '单人挑战，尽可能获得高分',
        hasItems: false,
        hasAI: false
    },
    VERSUS_AI: {
        name: '对战AI',
        description: '与AI进行1对1对战',
        hasItems: true,
        hasAI: true
    },
    VERSUS_PLAYER: {
        name: '双人对战',
        description: '与其他玩家实时对战',
        hasItems: true,
        hasAI: false
    }
};

// 默认导出完整配置对象
export const GAME_CONFIG = {
    BOARD: BOARD_CONFIG,
    TIMING: TIMING_CONFIG,
    SHAPES,
    COLORS,
    SHAPE_NAMES,
    MODES: GAME_MODES
};

export default GAME_CONFIG;
