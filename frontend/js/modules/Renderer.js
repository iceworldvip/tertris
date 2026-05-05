/**
 * 渲染器模块
 * 负责 Canvas 渲染
 */

import { BOARD_CONFIG, COLORS } from './Config.js';

export class Renderer {
    constructor(p1Canvas, p2Canvas, nextCanvas) {
        this.p1Ctx = p1Canvas.getContext('2d');
        this.p2Ctx = p2Canvas ? p2Canvas.getContext('2d') : null;
        this.nextCtx = nextCanvas.getContext('2d');
        this.blockSize = BOARD_CONFIG.BLOCK_SIZE;
        this.colors = COLORS;
    }

    /**
     * 绘制游戏板
     * @param {CanvasRenderingContext2D} ctx
     * @param {object} gameState
     */
    drawBoard(ctx, gameState) {
        if (!gameState) {
            this.drawEmptyBoard(ctx);
            return;
        }

        const { board, current_piece: currentPiece } = gameState;
        const width = BOARD_CONFIG.WIDTH;
        const height = BOARD_CONFIG.HEIGHT;

        // 清空画布
        ctx.fillStyle = '#0a0a0a';
        ctx.fillRect(0, 0, width * this.blockSize, height * this.blockSize);

        // 绘制网格
        this.drawGrid(ctx, width, height);

        // 绘制已固定的方块
        if (board) {
            for (let y = 0; y < height; y++) {
                for (let x = 0; x < width; x++) {
                    const cell = board[y][x];
                    if (cell !== -1 && cell !== null) {
                        this.drawBlock(ctx, x, y, this.colors[cell], this.blockSize);
                    }
                }
            }
        }

        // 绘制当前方块
        if (currentPiece) {
            this.drawPiece(ctx, currentPiece);
        }
    }

    /**
     * 绘制网格
     * @param {CanvasRenderingContext2D} ctx
     * @param {number} width
     * @param {number} height
     */
    drawGrid(ctx, width, height) {
        ctx.strokeStyle = '#1a1a1a';
        ctx.lineWidth = 1;

        for (let x = 0; x <= width; x++) {
            ctx.beginPath();
            ctx.moveTo(x * this.blockSize, 0);
            ctx.lineTo(x * this.blockSize, height * this.blockSize);
            ctx.stroke();
        }

        for (let y = 0; y <= height; y++) {
            ctx.beginPath();
            ctx.moveTo(0, y * this.blockSize);
            ctx.lineTo(width * this.blockSize, y * this.blockSize);
            ctx.stroke();
        }
    }

    /**
     * 绘制单个方块
     * @param {CanvasRenderingContext2D} ctx
     * @param {number} x
     * @param {number} y
     * @param {string} color
     * @param {number} size
     */
    drawBlock(ctx, x, y, color, size) {
        const px = x * size;
        const py = y * size;

        // 主体
        ctx.fillStyle = color;
        ctx.fillRect(px + 1, py + 1, size - 2, size - 2);

        // 高光
        ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
        ctx.fillRect(px + 1, py + 1, size - 2, 4);
        ctx.fillRect(px + 1, py + 1, 4, size - 2);

        // 阴影
        ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
        ctx.fillRect(px + 1, py + size - 5, size - 2, 4);
        ctx.fillRect(px + size - 5, py + 1, 4, size - 2);
    }

    /**
     * 绘制当前方块
     * @param {CanvasRenderingContext2D} ctx
     * @param {object} piece
     */
    drawPiece(ctx, piece) {
        const { shape, x, y, color } = piece;

        for (let row = 0; row < shape.length; row++) {
            for (let col = 0; col < shape[row].length; col++) {
                if (shape[row][col]) {
                    const boardX = x + col;
                    const boardY = y + row;
                    if (boardY >= 0) {
                        this.drawBlock(ctx, boardX, boardY, color, this.blockSize);
                    }
                }
            }
        }
    }

    /**
     * 绘制空游戏板
     * @param {CanvasRenderingContext2D} ctx
     */
    drawEmptyBoard(ctx) {
        ctx.fillStyle = '#0a0a0a';
        ctx.fillRect(0, 0, 300, 600);

        ctx.fillStyle = '#333';
        ctx.font = '20px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('等待玩家加入...', 150, 300);
    }

    /**
     * 绘制下一个方块预览
     * @param {object} nextPiece
     */
    drawNextPiece(nextPiece) {
        const ctx = this.nextCtx;
        const blockSize = 25;

        // 清空画布
        ctx.fillStyle = '#0a0a0a';
        ctx.fillRect(0, 0, 120, 120);

        if (!nextPiece) return;

        const { shape, color } = nextPiece;
        const offsetX = (120 - shape[0].length * blockSize) / 2;
        const offsetY = (120 - shape.length * blockSize) / 2;

        for (let y = 0; y < shape.length; y++) {
            for (let x = 0; x < shape[y].length; x++) {
                if (shape[y][x]) {
                    const px = offsetX + x * blockSize;
                    const py = offsetY + y * blockSize;

                    ctx.fillStyle = color;
                    ctx.fillRect(px + 1, py + 1, blockSize - 2, blockSize - 2);

                    ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
                    ctx.fillRect(px + 1, py + 1, blockSize - 2, 3);
                }
            }
        }
    }

    /**
     * 渲染整个房间状态
     * @param {object} roomState
     * @param {string} playerType
     */
    render(roomState, playerType) {
        if (!roomState) return;

        // 绘制玩家1
        if (this.p1Ctx) {
            this.drawBoard(this.p1Ctx, roomState.player1);
        }

        // 绘制玩家2
        if (this.p2Ctx) {
            this.drawBoard(this.p2Ctx, roomState.player2);
        }

        // 绘制下一个方块（显示当前玩家的）
        const myGame = playerType === 'player1' ? roomState.player1 :
                      (playerType === 'player2' ? roomState.player2 : null);
        if (myGame && myGame.next_piece) {
            this.drawNextPiece(myGame.next_piece);
        }
    }
}

export default Renderer;
