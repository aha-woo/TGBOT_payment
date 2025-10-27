# 快速开始指南

5分钟快速上手 Telegram 支付 Bot！

## ⚡ 极速部署（3步）

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境

复制 `.env.example` 为 `.env`，填写以下必填项：

```env
BOT_TOKEN=从 @BotFather 获取
ADMIN_USER_IDS=你的 Telegram User ID
PRIVATE_CHANNEL_ID=你的频道 ID（-100 开头）
TRON_WALLET_ADDRESS=你的 TRON 地址（T 开头）
TRONSCAN_API_KEY=从 tronscan.org 获取
XIANYU_PRODUCT_URL=你的闲鱼商品链接
```

### 3. 启动

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

**Windows:**
```bash
start.bat
```

或直接：
```bash
python bot.py
```

## 📝 获取配置参数

### Bot Token（必须）

1. 打开 Telegram，搜索 @BotFather
2. 发送 `/newbot`
3. 按提示设置名称
4. 复制获得的 Token

### User ID（必须）

1. 搜索 @userinfobot
2. 发送 `/start`
3. 复制你的 ID

### 频道 ID（必须）

1. 创建一个私有频道
2. 将你的 Bot 添加为管理员（需要"邀请用户"权限）
3. 搜索 @getidsbot，将它添加到频道
4. 复制频道 ID（格式：-1001234567890）

### TRON 地址（USDT 支付必须）

1. 下载 TronLink 钱包
2. 创建钱包并备份助记词
3. 复制你的 TRON 地址（T 开头）

### TronScan API Key（USDT 支付必须）

1. 访问 https://tronscan.org
2. 注册并登录
3. 进入 Profile → API Keys
4. 创建并复制 API Key

### 闲鱼链接（闲鱼支付必须）

1. 在闲鱼发布商品
2. 点击分享，复制链接

## 🎯 测试功能

### 1. 测试 Bot 连接

启动后，在 Telegram 找到你的 Bot，发送：
```
/start
```

应该看到欢迎消息和菜单。

### 2. 测试购买流程

```
/buy
```

选择套餐 → 选择支付方式 → 查看支付信息

### 3. 测试管理员功能

```
/admin
```

应该看到管理员面板（需要配置 ADMIN_USER_IDS）

## 🔧 自定义套餐

编辑 `config.py`：

```python
MEMBERSHIP_PLANS = {
    'month': {
        'name': '月度会员',
        'days': 30,
        'price_usdt': 10.0,  # 修改价格
        'price_cny': 68.0
    },
    # 添加新套餐
    'week': {
        'name': '周会员',
        'days': 7,
        'price_usdt': 3.0,
        'price_cny': 20.0
    }
}
```

## 📊 管理工具

### 查看统计

```bash
python manage.py stats
```

### 查看订单

```bash
python manage.py orders 20  # 查看最近20个订单
```

### 查看待审核订单

```bash
python manage.py pending
```

### 备份数据

```bash
python manage.py backup
```

## 🐛 常见问题

### Bot 无响应？

1. 检查 Token 是否正确
2. 检查网络连接
3. 查看 `bot.log` 日志文件

### 无法邀请用户到频道？

1. 确认 Bot 是频道管理员
2. 确认 Bot 有"邀请用户"权限
3. 确认频道 ID 格式正确（包含 -100 前缀）

### TRON 支付不自动确认？

1. 确认 TronScan API Key 正确
2. 确认收款地址正确
3. 等待 1-3 分钟（区块确认时间）

## 📚 下一步

- 📖 阅读 [README.md](README.md) 了解完整功能
- 🚀 阅读 [DEPLOY.md](DEPLOY.md) 学习生产部署
- 🏗️ 阅读 [ARCHITECTURE.md](ARCHITECTURE.md) 理解系统架构

## 💡 快速配置模板

### 最小配置（仅 TRON 支付）

```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_USER_IDS=123456789
PRIVATE_CHANNEL_ID=-1001234567890
TRON_WALLET_ADDRESS=TYourAddress123456789
TRONSCAN_API_KEY=your-api-key
XIANYU_PRODUCT_URL=https://example.com
```

### 完整配置（所有功能）

```env
# Telegram
BOT_TOKEN=your_bot_token
ADMIN_USER_IDS=123456789,987654321
PRIVATE_CHANNEL_ID=-1001234567890

# TRON
TRON_WALLET_ADDRESS=TYourAddress
TRONSCAN_API_KEY=your-api-key

# 闲鱼
XIANYU_PRODUCT_URL=https://your-xianyu-link

# 可选配置
DATABASE_PATH=payment_bot.db
ORDER_TIMEOUT_MINUTES=30
POLL_INTERVAL_SECONDS=15
LOG_LEVEL=INFO
MAX_PENDING_ORDERS_PER_USER=3
MIN_ORDER_INTERVAL_SECONDS=60
```

## 🎉 完成！

现在你的支付 Bot 已经可以正常工作了！

用户使用流程：
1. 用户发送 `/start`
2. 点击"购买会员"
3. 选择套餐和支付方式
4. 完成支付
5. 自动收到频道邀请链接

管理员使用流程：
1. 发送 `/admin` 查看面板
2. 发送 `/pending` 查看待审核订单
3. 点击"通过"或"拒绝"

祝您使用愉快！🚀


