# 部署指南

详细的部署步骤和注意事项。

## 📋 部署前准备

### 1. 服务器要求

- **操作系统**: Linux (Ubuntu 20.04+ / CentOS 7+) / Windows 10+
- **Python**: 3.8 或更高版本
- **内存**: 至少 512MB
- **存储**: 至少 1GB
- **网络**: 需要访问 Telegram API 和 TronScan API

### 2. 准备材料

- [ ] Telegram Bot Token
- [ ] 管理员 User ID
- [ ] 私有频道 ID
- [ ] TRON 钱包地址
- [ ] TronScan API Key
- [ ] 闲鱼商品链接

## 🚀 部署步骤

### Linux/Mac 部署

#### 1. 安装 Python 3.8+

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv

# CentOS
sudo yum install python3 python3-pip
```

#### 2. 克隆或上传代码

```bash
cd /opt
mkdir tgbot_payment
cd tgbot_payment
# 上传所有文件到此目录
```

#### 3. 创建虚拟环境

```bash
python3 -m venv venv
source venv/bin/activate
```

#### 4. 安装依赖

```bash
pip install -r requirements.txt
```

#### 5. 配置环境变量

```bash
cp .env.example .env
nano .env  # 或使用 vim
```

编辑 `.env` 文件，填写所有必需的配置。

#### 6. 测试运行

```bash
python bot.py
```

如果一切正常，按 Ctrl+C 停止。

#### 7. 使用 systemd 设置开机自启

创建服务文件：

```bash
sudo nano /etc/systemd/system/tgbot-payment.service
```

内容：

```ini
[Unit]
Description=Telegram Payment Bot
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/opt/tgbot_payment
Environment="PATH=/opt/tgbot_payment/venv/bin"
ExecStart=/opt/tgbot_payment/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用并启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable tgbot-payment
sudo systemctl start tgbot-payment
```

查看状态：

```bash
sudo systemctl status tgbot-payment
```

查看日志：

```bash
sudo journalctl -u tgbot-payment -f
```

### Windows 部署

#### 1. 安装 Python

从 [python.org](https://www.python.org/downloads/) 下载 Python 3.8+ 安装包。

安装时勾选 "Add Python to PATH"。

#### 2. 安装依赖

```powershell
cd E:\TGBOT_payment
pip install -r requirements.txt
```

#### 3. 配置环境变量

复制 `.env.example` 为 `.env`，然后编辑填写配置。

#### 4. 测试运行

```powershell
python bot.py
```

#### 5. 设置开机自启（使用任务计划程序）

1. 创建启动脚本 `start_bot.bat`：

```batch
@echo off
cd /d E:\TGBOT_payment
python bot.py
```

2. 打开任务计划程序
3. 创建基本任务
4. 触发器：计算机启动时
5. 操作：启动程序
6. 程序：`E:\TGBOT_payment\start_bot.bat`
7. 完成

或使用 NSSM（推荐）：

```powershell
# 下载 NSSM: https://nssm.cc/download
nssm install TGBotPayment "C:\Python39\python.exe" "E:\TGBOT_payment\bot.py"
nssm set TGBotPayment AppDirectory "E:\TGBOT_payment"
nssm start TGBotPayment
```

### Docker 部署（可选）

#### 1. 创建 Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
```

#### 2. 创建 docker-compose.yml

```yaml
version: '3.8'

services:
  bot:
    build: .
    container_name: tgbot-payment
    restart: always
    env_file:
      - .env
    volumes:
      - ./data:/app/data
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

#### 3. 启动

```bash
docker-compose up -d
```

查看日志：

```bash
docker-compose logs -f
```

## 🔧 配置详解

### 获取 Bot Token

1. 在 Telegram 中找 @BotFather
2. 发送 `/newbot`
3. 按提示设置 Bot 名称和用户名
4. 复制 Token

### 获取 User ID

方法1：使用 @userinfobot
1. 找 @userinfobot
2. 发送 `/start`
3. 记录你的 ID

方法2：使用 @RawDataBot
1. 找 @RawDataBot
2. 发送任意消息
3. 在返回的 JSON 中找到 `"id"` 字段

### 获取频道 ID

1. 创建私有频道
2. 将 Bot 添加为管理员（需要有邀请用户权限）
3. 使用 @getidsbot 或 @RawDataBot
4. 将 bot 添加到频道
5. 获取 ID（格式：-1001234567890）

或使用代码获取：

```python
import asyncio
from telegram import Bot

async def get_chat_id():
    bot = Bot(token="YOUR_BOT_TOKEN")
    updates = await bot.get_updates()
    for update in updates:
        if update.my_chat_member:
            print(update.my_chat_member.chat.id)

asyncio.run(get_chat_id())
```

### 获取 TRON 地址和 API Key

#### TRON 地址

1. 下载 TronLink 钱包 (浏览器插件或手机 App)
2. 创建新钱包
3. 备份助记词（非常重要！）
4. 复制接收地址（T 开头的地址）

⚠️ **安全提示**：
- 助记词务必安全保管
- 私钥永远不要泄露
- 本系统不需要私钥，只需要地址

#### TronScan API Key

1. 访问 [https://tronscan.org](https://tronscan.org)
2. 注册账号（右上角 Sign In）
3. 登录后进入 Profile
4. 找到 API Keys 部分
5. 点击 "Create API Key"
6. 复制 Key

免费额度：
- 每秒 5 次请求
- 每天 10,000 次请求
- 对于小规模使用完全足够

### 设置闲鱼商品

1. **发布商品**
   - 打开闲鱼 App
   - 发布商品（虚拟商品）
   - 设置不同价格对应不同套餐
   - 或者发布多个商品

2. **获取链接**
   - 点击商品
   - 点击分享
   - 复制链接

3. **注意事项**
   - 商品描述清楚说明是虚拟商品
   - 避免使用敏感词
   - 设置自动回复告知买家流程

## 🔒 安全配置

### 1. 文件权限

```bash
# Linux
chmod 600 .env
chmod 600 *.db
```

### 2. 防火墙

Bot 只需要访问外网，不需要开放端口。

### 3. 定期备份

设置定时任务自动备份：

```bash
# Linux cron
crontab -e

# 每天凌晨 2 点备份
0 2 * * * cd /opt/tgbot_payment && python manage.py backup
```

Windows 任务计划程序：
- 创建每日任务
- 运行 `python manage.py backup`

### 4. 日志轮转

避免日志文件过大：

```bash
# Linux logrotate
sudo nano /etc/logrotate.d/tgbot-payment

# 内容：
/opt/tgbot_payment/bot.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

## 📊 监控和维护

### 健康检查

创建 `healthcheck.py`：

```python
import os
import requests
from datetime import datetime, timedelta

def check_bot_health():
    # 检查进程是否运行
    if not os.path.exists('bot.pid'):
        return False, "Bot not running"
    
    # 检查数据库
    if not os.path.exists('payment_bot.db'):
        return False, "Database not found"
    
    # 检查日志更新时间
    if os.path.exists('bot.log'):
        mtime = datetime.fromtimestamp(os.path.getmtime('bot.log'))
        if datetime.now() - mtime > timedelta(minutes=30):
            return False, "Bot not active"
    
    return True, "Bot is healthy"

if __name__ == '__main__':
    is_healthy, message = check_bot_health()
    print(message)
    exit(0 if is_healthy else 1)
```

### 监控脚本

```bash
#!/bin/bash
# monitor.sh

cd /opt/tgbot_payment

# 检查服务状态
if ! systemctl is-active --quiet tgbot-payment; then
    echo "Bot is down, restarting..."
    systemctl restart tgbot-payment
    
    # 发送告警（可选）
    curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/sendMessage" \
         -d "chat_id=<ADMIN_ID>" \
         -d "text=⚠️ Bot was down and has been restarted"
fi
```

添加到 crontab（每 5 分钟检查）：

```bash
*/5 * * * * /opt/tgbot_payment/monitor.sh
```

### 性能优化

1. **数据库优化**

```python
# 定期 VACUUM
import sqlite3
conn = sqlite3.connect('payment_bot.db')
conn.execute('VACUUM')
conn.close()
```

2. **日志级别**

生产环境建议使用 `INFO` 或 `WARNING` 级别：

```python
LOG_LEVEL=WARNING
```

3. **清理旧数据**

定期运行：

```bash
python manage.py cleanup
```

## 🐛 故障排查

### Bot 无法启动

1. 检查 Token 是否正确
2. 检查网络连接
3. 查看日志文件 `bot.log`
4. 检查 Python 版本和依赖

### 无法邀请用户

1. 确认 Bot 是频道管理员
2. 确认 Bot 有邀请用户权限
3. 确认频道 ID 正确（包含 -100 前缀）
4. 检查用户是否已在频道中

### TRON 支付不自动确认

1. 检查 TronScan API Key
2. 检查收款地址
3. 查看 TRON 支付日志
4. 确认网络可以访问 TronScan API

### 数据库锁定

如果出现 "database is locked" 错误：

```python
# 增加超时时间
conn = sqlite3.connect('payment_bot.db', timeout=30.0)
```

## 📈 扩展部署

### 高可用部署

使用多个 Bot 实例（不同 Token）+ 负载均衡。

### 分布式部署

- Bot 服务器
- 数据库服务器（使用 MySQL/PostgreSQL）
- 缓存服务器（Redis）

### CDN 加速

如果有大量图片（QR码），可以考虑使用 CDN。

## 📞 获取帮助

- 查看 README.md
- 查看日志文件
- 提交 Issue

## ✅ 部署检查清单

部署完成后，检查以下项目：

- [ ] Bot 能正常启动
- [ ] 能响应 /start 命令
- [ ] 创建订单功能正常
- [ ] TRON 支付流程正常
- [ ] 闲鱼支付流程正常
- [ ] 管理员面板可以访问
- [ ] 能邀请用户到频道
- [ ] 数据库正常工作
- [ ] 日志正常记录
- [ ] 定时备份已设置
- [ ] 监控脚本已设置
- [ ] 服务自动重启已配置

全部完成后，您的 Bot 就可以正式运行了！🎉


