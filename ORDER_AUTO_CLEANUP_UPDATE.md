# 闲鱼订单自动超时清理功能

## 📅 更新日期
2025-10-27

## 🎯 更新目的
解决闲鱼订单长期处于 `pending` 状态导致的问题：
- ❌ 用户创建订单但未回填订单号
- ❌ 占用待支付订单名额
- ❌ 达到限制后无法创建新订单
- ❌ 管理员无法审核没有订单号的订单

## ✨ 新增功能

### 1. 闲鱼订单自动超时
- ⏰ 默认 30 分钟后自动将 `pending` 状态的闲鱼订单标记为 `expired`
- 🔄 超时时间可通过 `.env` 配置
- 📊 自动释放用户的待支付订单名额

### 2. 后台定时清理任务
- 🧹 每 5 分钟自动运行一次清理任务（可配置）
- 📝 详细记录清理日志
- 🛡️ 线程安全的数据库操作

### 3. 可配置的超时策略
- ✅ USDT 订单：30 分钟（已有功能，由 tron_payment 监控）
- ✅ 闲鱼订单：30 分钟（新增，由定时任务清理）
- ✅ 清理间隔：5 分钟（可调整）

## 📝 配置说明

### 在 `.env` 文件中添加以下配置：

```env
# 订单超时设置
ORDER_TIMEOUT_MINUTES=30              # USDT订单超时时间（分钟）
XIANYU_ORDER_TIMEOUT_MINUTES=30       # 闲鱼订单超时时间（分钟）
ORDER_CLEANUP_INTERVAL_MINUTES=5      # 订单清理任务运行间隔（分钟）

# 防刷配置
MAX_PENDING_ORDERS_PER_USER=3         # 每个用户最多同时待支付订单数
MIN_ORDER_INTERVAL_SECONDS=60         # 下单最小间隔（秒）
```

### 配置项说明

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `ORDER_TIMEOUT_MINUTES` | 30 | USDT订单超时时间 |
| `XIANYU_ORDER_TIMEOUT_MINUTES` | 30 | 闲鱼订单超时时间 |
| `ORDER_CLEANUP_INTERVAL_MINUTES` | 5 | 清理任务运行间隔 |
| `MAX_PENDING_ORDERS_PER_USER` | 3 | 每个用户最多待支付订单数 |
| `MIN_ORDER_INTERVAL_SECONDS` | 60 | 下单最小间隔 |

## 🔧 技术实现

### 1. 配置文件修改 (`config.py`)
```python
# 新增配置项
XIANYU_ORDER_TIMEOUT_MINUTES = int(os.getenv('XIANYU_ORDER_TIMEOUT_MINUTES', '30'))
ORDER_CLEANUP_INTERVAL_MINUTES = int(os.getenv('ORDER_CLEANUP_INTERVAL_MINUTES', '5'))
```

### 2. 数据库方法 (`database.py`)
```python
def cleanup_expired_xianyu_orders(self, timeout_minutes: int) -> int:
    """
    清理过期的闲鱼待支付订单
    
    Args:
        timeout_minutes: 超时时间（分钟）
        
    Returns:
        清理的订单数量
    """
    # 查找并更新过期订单为 expired 状态
    # 返回清理数量
```

### 3. 定时任务 (`bot.py`)
```python
async def cleanup_expired_orders(context: ContextTypes.DEFAULT_TYPE):
    """定期清理过期的闲鱼订单"""
    cleaned_count = db.cleanup_expired_xianyu_orders(XIANYU_ORDER_TIMEOUT_MINUTES)
    if cleaned_count > 0:
        logger.info(f"🧹 Auto-cleanup: {cleaned_count} xianyu order(s) expired")

# 注册定时任务
application.job_queue.run_repeating(
    cleanup_expired_orders,
    interval=ORDER_CLEANUP_INTERVAL_MINUTES * 60,
    first=30  # 启动后30秒开始
)
```

## 📊 工作流程

```
用户创建闲鱼订单
    ↓
状态: pending
    ↓
后台定时任务 (每5分钟)
    ↓
检查: created_at < (now - 30分钟)
    ↓
是 → 更新状态为 expired
    ↓
释放待支付订单名额
    ↓
用户可以创建新订单
```

## 🎉 预期效果

### 用户体验改善
- ✅ 不再因旧订单堆积而无法创建新订单
- ✅ 更清晰的订单状态提示
- ✅ 自动清理过期订单，无需手动干预

### 管理员体验改善
- ✅ 减少无效的待审核订单
- ✅ 更准确的订单统计数据
- ✅ 系统自动维护，降低管理成本

### 系统稳定性提升
- ✅ 防止订单表无限增长
- ✅ 有效的防刷单机制
- ✅ 自动化的订单生命周期管理

## 📝 日志示例

### 正常清理日志
```
2025-10-27 10:05:30 - database - INFO - Cleaned up 3 expired xianyu orders (timeout: 30 min)
2025-10-27 10:05:30 - database - DEBUG -   - Order XY_8068014765_1730023456789 (user 8068014765) expired
2025-10-27 10:05:30 - database - DEBUG -   - Order XY_8068014765_1730023567890 (user 8068014765) expired
2025-10-27 10:05:30 - database - DEBUG -   - Order XY_8068014765_1730023678901 (user 8068014765) expired
2025-10-27 10:05:30 - __main__ - INFO - 🧹 Auto-cleanup: 3 xianyu order(s) expired and cleaned up
```

### 无过期订单
```
2025-10-27 10:10:30 - database - INFO - Cleaned up 0 expired xianyu orders (timeout: 30 min)
```

## 🔍 测试验证

### 测试步骤
1. 创建闲鱼订单但不回填订单号
2. 等待超时时间（默认30分钟）
3. 观察日志，确认订单被自动清理
4. 验证可以创建新订单

### 快速测试（临时修改）
在 `.env` 中设置：
```env
XIANYU_ORDER_TIMEOUT_MINUTES=1        # 1分钟超时
ORDER_CLEANUP_INTERVAL_MINUTES=1      # 1分钟运行一次
```

测试完成后改回生产环境配置。

## ⚠️ 注意事项

1. **订单超时时间建议**
   - 测试环境：1-5 分钟（快速验证）
   - 生产环境：30-60 分钟（给用户充足时间）

2. **清理间隔建议**
   - 测试环境：1 分钟
   - 生产环境：5-10 分钟

3. **防刷配置建议**
   - `MAX_PENDING_ORDERS_PER_USER`: 3-5 个
   - `MIN_ORDER_INTERVAL_SECONDS`: 60-120 秒

## 🚀 部署步骤

### 1. 更新代码
```bash
git pull
```

### 2. 更新 `.env` 配置
添加上述配置项（如果没有则使用默认值）

### 3. 重启 Bot
```bash
# 使用 PM2
pm2 restart payment-bot

# 或直接运行
python3 bot.py
```

### 4. 验证启动
查看日志确认清理任务已启动：
```bash
pm2 logs payment-bot
```

应该看到：
```
Order cleanup task started (running every 5 minutes)
```

## 📚 相关文档
- `README.md` - 完整功能说明
- `QUICKSTART.md` - 快速开始指南
- `CONFIG_GUIDE.md` - 配置指南

## ✅ 完成清单
- [x] 添加闲鱼订单超时配置
- [x] 实现数据库清理方法
- [x] 添加定时清理任务
- [x] 更新文档和配置说明
- [x] 添加详细日志记录
- [x] 修复导入错误

## 🎯 后续优化建议

1. **用户通知**
   - 订单即将过期时发送提醒（例如剩余5分钟）
   - 订单过期后发送通知

2. **管理员统计**
   - 每日过期订单统计
   - 订单转化率分析

3. **灵活的超时策略**
   - 根据套餐类型设置不同超时时间
   - VIP用户延长超时时间

4. **订单恢复机制**
   - 允许用户申请恢复过期订单
   - 管理员可手动恢复订单

---

💡 **提示**: 如有任何问题，请查看日志文件 `bot.log` 或使用 `pm2 logs payment-bot` 查看实时日志。

