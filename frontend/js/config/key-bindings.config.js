/**
 * 按键绑定默认配置
 */

// 基础按键配置（适用于所有模式）
export const BASE_KEY_CONFIG = {
    moveLeft: 'ArrowLeft',
    moveRight: 'ArrowRight',
    moveDown: 'ArrowDown',
    rotate: 'ArrowUp',
    hardDrop: ' ',
    pause: 'p'
};

// 完整按键配置（含道具快捷键）
export const FULL_KEY_CONFIG = {
    ...BASE_KEY_CONFIG,
    item1: '1',
    item2: '2',
    item3: '3'
};

// AI 对战模式按键配置（2个道具槽）
export const AI_MODE_KEY_CONFIG = {
    ...BASE_KEY_CONFIG,
    item1: '1',
    item2: '2'
};

// 按键显示名称映射
export const KEY_NAME_MAP = {
    'ArrowLeft': '←',
    'ArrowRight': '→',
    'ArrowUp': '↑',
    'ArrowDown': '↓',
    ' ': '空格',
    'Space': '空格'
};

// 操作名称映射（用于UI显示）
export const ACTION_NAMES = {
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

// 根据游戏模式获取默认配置
export function getDefaultKeyConfig(mode) {
    switch (mode) {
        case 'solo':
            return { ...BASE_KEY_CONFIG };
        case 'ai':
            return { ...AI_MODE_KEY_CONFIG };
        case 'versus':
            return { ...FULL_KEY_CONFIG };
        default:
            return { ...FULL_KEY_CONFIG };
    }
}

export default {
    BASE_KEY_CONFIG,
    FULL_KEY_CONFIG,
    AI_MODE_KEY_CONFIG,
    KEY_NAME_MAP,
    ACTION_NAMES,
    getDefaultKeyConfig
};
