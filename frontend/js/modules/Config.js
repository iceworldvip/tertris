/**
 * 游戏配置模块
 * 集中管理所有游戏相关的配置
 */

export const BOARD_CONFIG = {
  WIDTH: 10,
  HEIGHT: 20,
  BLOCK_SIZE: 30,
};

export const TIMING_CONFIG = {
  TICK_RATE: 1000,
  LEVEL_SPEEDUP: 50,
  MIN_TICK_RATE: 100,
  MOVE_DELAY: 100,
  HARD_DROP_DELAY: 500,
  PAUSE_DELAY: 500,
};

export const SHAPES = [
  [
    [0, 0, 0, 0],
    [1, 1, 1, 1],
    [0, 0, 0, 0],
    [0, 0, 0, 0],
  ],
  [
    [1, 1],
    [1, 1],
  ],
  [
    [0, 1, 0],
    [1, 1, 1],
  ],
  [
    [1, 0, 0],
    [1, 1, 1],
  ],
  [
    [0, 0, 1],
    [1, 1, 1],
  ],
  [
    [0, 1, 1],
    [1, 1, 0],
  ],
  [
    [1, 1, 0],
    [0, 1, 1],
  ],
];

export const COLORS = [
  "#00f0f0",
  "#f0f000",
  "#a000f0",
  "#f0a000",
  "#0000f0",
  "#00f000",
  "#f00000",
];

export const API_CONFIG = {
  BASE_URL: "",
  ROOMS: "/api/rooms",
  AI_ROOMS: "/api/ai/rooms",
  LEADERBOARD: "/api/leaderboard",
};

export const WS_CONFIG = {
  ROOM: (roomId) => `/ws/room/${roomId}`,
  AI_ROOM: (roomId) => `/ws/ai/${roomId}`,
};

export const NICKNAME_CONFIG = {
  ADJECTIVES: [
    "快乐的",
    "勇敢的",
    "聪明的",
    "神秘的",
    "闪电",
    "超级",
    "酷炫",
    "萌萌",
  ],
  NOUNS: ["方块", "战士", "骑士", "法师", "忍者", "熊猫", "猫咪", "狗狗"],
};

export const ITEM_CONFIG = {
  TYPES: {
    ADD_GARBAGE: { name: "垃圾行", icon: "🗑️", desc: "给对手加1-3行" },
    CLEAR_LINE: { name: "清行", icon: "✨", desc: "自己消1-2行" },
  },
  TRIGGER_LINES: 5,
};

export const KEYBINDINGS = {
  FULL: {
    moveLeft: "ArrowLeft",
    moveRight: "ArrowRight",
    moveDown: "ArrowDown",
    rotate: "ArrowUp",
    hardDrop: " ",
    pause: "p",
    item1: "1",
    item2: "2",
    item3: "3",
  },
};

export default {
  BOARD: BOARD_CONFIG,
  TIMING: TIMING_CONFIG,
  SHAPES,
  COLORS,
  API: API_CONFIG,
  WS: WS_CONFIG,
  NICKNAME: NICKNAME_CONFIG,
  ITEM: ITEM_CONFIG,
  KEYS: KEYBINDINGS,
};
