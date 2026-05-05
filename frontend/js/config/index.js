/**
 * 配置中心入口
 * 将所有配置集中导出，便于统一管理
 */

// 注意：此文件使用 ES6 模块语法
// 如需在普通 script 标签中使用，请使用 config.global.js

export { GAME_CONFIG, BOARD_CONFIG, TIMING_CONFIG, SHAPES, COLORS } from './game.config.js';
export { API_CONFIG, API_ENDPOINTS, WS_ENDPOINTS, STORAGE_KEYS } from './api.config.js';
export { 
    BASE_KEY_CONFIG, 
    FULL_KEY_CONFIG, 
    AI_MODE_KEY_CONFIG,
    KEY_NAME_MAP,
    ACTION_NAMES,
    getDefaultKeyConfig 
} from './key-bindings.config.js';

// 创建全局配置对象（供非模块化代码使用）
export function createGlobalConfig() {
    return {
        game: GAME_CONFIG,
        api: API_CONFIG,
        keys: {
            BASE_KEY_CONFIG,
            FULL_KEY_CONFIG,
            AI_MODE_KEY_CONFIG,
            KEY_NAME_MAP,
            ACTION_NAMES
        }
    };
}
