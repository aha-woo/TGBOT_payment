# Telegram 会员收款 Bot

一个功能完整的 Telegram Bot 会员支付系统，支持 TRON USDT 自动收款和闲鱼手动审核支付。

## ✨ 核心功能

### 1. 双支付通道
- **TRON USDT (TRC20)**: 自动监控链上支付，无需人工干预
- **闲鱼支付**: 用户提交订单号，管理员手动审核

### 2. 自动会员管理
- ✅ 支付成功后自动激活会员
- ✅ 自动邀请用户加入私有频道
- ✅ 会员到期自动检测
- ✅ 支持续费延期

### 3. 完整的订单系统
- 📋 订单追踪和查询
- 📊 订单统计和报表
- ⏰ 订单超时自动处理
- 🔒 防刷机制

### 4. 管理员面板
- 👑 待审核订单管理
- 👥 用户列表和会员状态
- 📊 收入统计和数据分析
- 🔔 实时通知

## 📦 技术栈

- **语言**: Python 3.8+
- **Bot 框架**: python-telegram-bot
- **数据库**: SQLite (轻量级，无需额外配置)
- **支付**: TRON Network (TRC20-USDT)
- **二维码**: qrcode + Pillow

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# Telegram Bot Token (从 @BotFather 获取)
BOT_TOKEN=your_bot_token_here

# 管理员 Telegram User ID (可以多个，逗号分隔)
ADMIN_USER_IDS=123456789,987654321

# 私有频道 ID (以 -100 开头)
PRIVATE_CHANNEL_ID=-1001234567890

# TRON 收款地址
TRON_WALLET_ADDRESS=TYourWalletAddressHere

# TronScan API Key (从 https://tronscan.org 申请)
TRONSCAN_API_KEY=your_tronscan_api_key

# 闲鱼商品链接
XIANYU_PRODUCT_URL=https://your-xianyu-product-link
```

### 3. 配置会员套餐

编辑 `config.py` 中的 `MEMBERSHIP_PLANS`：

```python
MEMBERSHIP_PLANS = {
    'month': {
        'name': '月度会员',
        'days': 30,
        'price_usdt': 10.0,
        'price_cny': 68.0
    },
    # ... 更多套餐
}
```

### 4. 设置 Bot 权限

确保你的 Bot 在私有频道有以下权限：
- ✅ 邀请用户
- ✅ 发送消息

### 5. 启动 Bot

```bash
python bot.py
```

## 📖 使用指南

### 用户操作

1. **开始使用**: `/start` - 打开主菜单
2. **购买会员**: `/buy` 或点击"购买会员"按钮
3. **选择套餐**: 月度/季度/年度
4. **选择支付方式**:
   - **USDT**: 扫码支付，自动到账
   - **闲鱼**: 跳转闲鱼支付，提交订单号
5. **查看订单**: `/orders` - 查看所有订单
6. **会员状态**: `/status` - 查看会员到期时间

### 管理员操作

1. **管理面板**: `/admin` - 打开管理员面板
2. **待审核订单**: `/pending` - 查看闲鱼待审核订单
3. **审核流程**:
   - 查看订单详情
   - 前往闲鱼确认支付
   - 点击"✅ 通过"或"❌ 拒绝"
4. **用户管理**: 查看所有用户和会员状态
5. **统计数据**: 查看收入、订单等统计

## 🔧 配置说明

### 获取 Telegram Bot Token

1. 找 @BotFather 对话
2. 发送 `/newbot`
3. 按提示设置 Bot 名称
4. 获取 Token

### 获取 User ID

1. 找 @userinfobot 对话
2. 发送任意消息
3. 获取你的 User ID

### 获取频道 ID

1. 创建私有频道
2. 将 Bot 添加为管理员
3. 找 @getidsbot，将它添加到频道
4. 获取频道 ID（格式：-1001234567890）

### 获取 TRON 地址

1. 下载 TronLink 钱包
2. 创建钱包
3. 复制 TRON 地址（T 开头）

### 获取 TronScan API Key

1. 访问 https://tronscan.org
2. 注册账号
3. 进入 API Keys 页面
4. 创建 API Key

### 闲鱼商品设置

1. 在闲鱼发布商品（设置不同价格对应不同套餐）
2. 复制商品链接
3. 填入配置文件

## 📂 项目结构

```
TGBOT_payment/
├── bot.py              # Bot 主程序
├── config.py           # 配置文件
├── database.py         # 数据库操作
├── tron_payment.py     # TRON 支付模块
├── requirements.txt    # 依赖包
├── .env               # 环境变量（需手动创建）
├── .env.example       # 环境变量模板
├── README.md          # 说明文档
├── payment_bot.db     # 主数据库（自动创建）
├── tron_orders.db     # TRON 订单库（自动创建）
└── bot.log           # 日志文件（自动创建）
```

## 💾 数据库设计

### users 表
- 用户基本信息
- 会员状态和到期时间
- 消费统计

### orders 表
- 订单详情
- 支付信息（TRON 交易哈希、闲鱼订单号）
- 订单状态流转

### channel_invites 表
- 频道邀请记录
- 邀请状态

### system_logs 表
- 系统操作日志
- 便于审计和调试

## 🔒 安全建议

1. ✅ **私钥保护**: TRON 私钥不存储在代码中
2. ✅ **环境变量**: 敏感信息使用 `.env` 文件
3. ✅ **管理员验证**: 所有管理操作需验证权限
4. ✅ **防刷机制**: 限制下单频率和数量
5. ✅ **日志记录**: 所有关键操作都有日志

## 🛠️ 高级功能

### 自定义欢迎消息

编辑 `config.py` 中的 `WELCOME_MESSAGE`

### 修改轮询间隔

```python
POLL_INTERVAL_SECONDS = 15  # TRON 支付轮询间隔
```

### 订单超时设置

```python
ORDER_TIMEOUT_MINUTES = 30  # 订单30分钟后超时
```

### 防刷限制

```python
MAX_PENDING_ORDERS_PER_USER = 3  # 每用户最多3个待支付订单
MIN_ORDER_INTERVAL_SECONDS = 60  # 最小下单间隔60秒
```

## 📊 监控和维护

### 查看日志

```bash
tail -f bot.log
```

### 备份数据库

```bash
cp payment_bot.db payment_bot_backup_$(date +%Y%m%d).db
cp tron_orders.db tron_orders_backup_$(date +%Y%m%d).db
```

### 导出订单数据

在 Python 中：

```python
from database import Database
db = Database('payment_bot.db')
stats = db.get_statistics()
print(stats)
```

## ❓ 常见问题

### Q: Bot 无法邀请用户到频道？
A: 确保：
1. Bot 在频道中是管理员
2. Bot 有"邀请用户"权限
3. 频道 ID 正确（包含 -100 前缀）

### Q: TRON 支付不能自动确认？
A: 检查：
1. TronScan API Key 是否正确
2. 收款地址是否正确
3. 网络连接是否正常

### Q: 如何添加新的套餐？
A: 编辑 `config.py` 中的 `MEMBERSHIP_PLANS`，添加新套餐配置

### Q: 如何更换数据库为 MySQL/MariaDB？
A: 修改 `database.py`，将 SQLite 连接改为 MySQL 连接（需要 pymysql）

### Q: 如何支持多语言？
A: 将所有文本提取到独立的语言文件，根据用户语言加载

## 🤝 支持

如有问题或建议，请：
- 提交 Issue
- 联系开发者

## 📄 许可

MIT License

## 🎯 TODO / 改进建议

- [ ] 支持更多加密货币（ETH, BTC）
- [ ] 多语言支持（英文、中文）
- [ ] Web 管理后台
- [ ] 优惠券系统
- [ ] 推荐返利
- [ ] 自动提醒续费
- [ ] 会员等级系统
- [ ] 数据可视化图表
- [ ] 导出报表（Excel）
- [ ] Webhook 通知
- [ ] 邮件通知
- [ ] 自动备份数据库

## 💡 扩展思路

### 1. 推荐返利系统

```python
# 添加推荐表
CREATE TABLE referrals (
    referrer_id INTEGER,
    referee_id INTEGER,
    reward_amount REAL,
    created_at TIMESTAMP
)

# 用户邀请链接
/start?ref=USER_ID
```

### 2. 多频道支持

```python
# 不同套餐对应不同频道
MEMBERSHIP_PLANS = {
    'basic': {
        'channel_id': '-100111111',
        ...
    },
    'premium': {
        'channel_id': '-100222222',
        ...
    }
}
```

### 3. 优惠券系统

```python
# 优惠券表
CREATE TABLE coupons (
    code TEXT PRIMARY KEY,
    discount_percent INTEGER,
    max_uses INTEGER,
    expires_at TIMESTAMP
)
```

### 4. 自动提醒续费

```python
# 定时任务：到期前3天提醒
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()
scheduler.add_job(check_expiring_members, 'interval', hours=24)
```

## 🌟 最佳实践

1. **定期备份数据库**（每天自动备份）
2. **监控日志文件**（防止异常错误）
3. **测试环境验证**（生产前充分测试）
4. **用户反馈收集**（持续优化体验）
5. **安全更新**（及时更新依赖包）

---

**祝您使用愉快！** 🎉


