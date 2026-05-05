/**
 * API 配置中心
 * 集中管理所有 API 端点和 WebSocket 连接配置
 */

// 基础配置
const BASE_URL = '';

// API 端点定义
export const API_ENDPOINTS = {
    // 房间相关
    ROOMS: '/api/rooms',
    ROOM_COUNT: '/api/rooms/count',
    ROOM_DETAIL: (roomId) => `/api/rooms/${roomId}`,
    JOIN_ROOM: (roomId) => `/api/rooms/${roomId}/join`,
    
    // AI 房间相关
    AI_ROOMS: '/api/ai/rooms',
    AI_ROOM_DETAIL: (roomId) => `/api/ai/rooms/${roomId}`,
    
    // 排行榜相关
    LEADERBOARD: '/api/leaderboard',
    SUBMIT_SCORE: '/api/leaderboard/submit',
    PLAYER_HISTORY: '/api/leaderboard/player/history',
    PLAYER_STATS: '/api/leaderboard/player/stats',
    TOP_PLAYERS: '/api/leaderboard/top-players',
    
    // 健康检查
    HEALTH: '/health'
};

// WebSocket 端点定义
export const WS_ENDPOINTS = {
    ROOM: (roomId) => `/ws/room/${roomId}`,
    AI: (roomId) => `/ws/ai/${roomId}`,
    LEGACY: (gameId) => `/ws/${gameId}`
};

// localStorage 键名配置（统一键名，避免之前的不一致问题）
export const STORAGE_KEYS = {
    SOLO_KEY_CONFIG: 'tetris_key_config_solo',
    AI_KEY_CONFIG: 'tetris_key_config_ai',
    VERSUS_KEY_CONFIG: 'tetris_key_config_versus',
    HIGH_SCORE: 'tetris_high_score',
    NICKNAME: 'tetris_nickname'
};

// 请求配置
export const REQUEST_CONFIG = {
    DEFAULT_TIMEOUT: 10000,
    RETRY_ATTEMPTS: 3,
    RETRY_DELAY: 1000
};

// 导出完整配置
export const API_CONFIG = {
    BASE_URL,
    ENDPOINTS: API_ENDPOINTS,
    WS_ENDPOINTS,
    STORAGE_KEYS,
    REQUEST: REQUEST_CONFIG
};

export default API_CONFIG;
