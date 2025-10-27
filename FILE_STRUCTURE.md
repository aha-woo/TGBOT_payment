# 📁 项目文件结构

```
TGBOT_payment/
│
├── 📄 核心代码文件
│   ├── bot.py                    # Bot 主程序（700+ 行）
│   ├── database.py               # 数据库操作（400+ 行）
│   ├── tron_payment.py           # TRON 支付模块（846 行）
│   ├── config.py                 # 配置管理（100+ 行）
│   └── manage.py                 # 管理工具（300+ 行）
│
├── ⚙️ 配置文件
│   ├── .env                      # 环境变量（需手动创建）
│   ├── .env.example              # 环境变量模板
│   ├── requirements.txt          # Python 依赖
│   └── .gitignore                # Git 忽略文件
│
├── 🚀 启动脚本
│   ├── start.sh                  # Linux/Mac 启动脚本
│   └── start.bat                 # Windows 启动脚本
│
├── 📚 文档文件
│   ├── README.md                 # 完整使用说明
│   ├── QUICKSTART.md             # 5分钟快速上手
│   ├── DEPLOY.md                 # 详细部署指南
│   ├── ARCHITECTURE.md           # 系统架构文档
│   ├── PROJECT_SUMMARY.md        # 项目总结
│   └── FILE_STRUCTURE.md         # 文件结构说明（本文件）
│
└── 🗄️ 运行时文件（自动生成）
    ├── payment_bot.db            # 主数据库
    ├── tron_orders.db            # TRON 订单数据库
    ├── bot.log                   # 日志文件
    ├── backups/                  # 备份目录
    │   ├── payment_bot_backup_*.db
    │   └── tron_orders_backup_*.db
    └── exports/                  # 导出目录
        └── orders_export_*.json
```

## 📋 文件说明

### 核心代码（必需）

#### bot.py
- **功能**: Telegram Bot 主程序
- **大小**: 约 700+ 行
- **职责**: 
  - 处理所有 Telegram 命令和回调
  - 业务逻辑协调
  - 用户交互界面
  - 支付流程管理
- **关键函数**:
  - `start_command()` - 启动命令
  - `buy_command()` - 购买会员
  - `admin_command()` - 管理员面板
  - `button_callback()` - 按钮回调处理
  - `invite_user_to_channel()` - 邀请到频道

#### database.py
- **功能**: 数据库操作封装
- **大小**: 约 400+ 行
- **职责**:
  - 数据库初始化
  - CRUD 操作
  - 事务管理
  - 统计查询
- **核心类**:
  - `Database` - 数据库管理类
- **主要方法**:
  - `get_or_create_user()` - 用户管理
  - `create_order()` - 创建订单
  - `update_order_status()` - 更新订单
  - `get_statistics()` - 获取统计

#### tron_payment.py
- **功能**: TRON TRC20-USDT 支付系统
- **大小**: 846 行
- **职责**:
  - 生成支付订单和二维码
  - 自动监控收款
  - 订单状态查询
  - 回调通知机制
- **核心类**:
  - `TronPayment` - TRON 支付管理
- **特点**: 
  - 您的原始代码，完美保留
  - 后台线程监控
  - 自动确认支付

#### config.py
- **功能**: 配置管理
- **大小**: 约 100+ 行
- **内容**:
  - 环境变量加载
  - Bot 配置
  - TRON 配置
  - 会员套餐定义
  - 消息模板
  - 系统参数
- **可配置项**:
  - 套餐价格和时长
  - 超时时间
  - 防刷参数

#### manage.py
- **功能**: 数据库管理 CLI 工具
- **大小**: 约 300+ 行
- **功能**:
  - 查看统计信息
  - 查看订单列表
  - 查看待审核订单
  - 查看会员列表
  - 检查过期会员
  - 备份数据库
  - 导出订单数据
  - 清理旧数据
- **使用方式**:
  ```bash
  python manage.py stats        # 查看统计
  python manage.py orders 20    # 查看20个订单
  python manage.py backup       # 备份数据
  ```

### 配置文件

#### .env（需要创建）
- **功能**: 存储敏感配置
- **创建方式**: 复制 `.env.example`
- **必填项**:
  - BOT_TOKEN
  - ADMIN_USER_IDS
  - PRIVATE_CHANNEL_ID
  - TRON_WALLET_ADDRESS
  - TRONSCAN_API_KEY
  - XIANYU_PRODUCT_URL

#### .env.example
- **功能**: 环境变量模板
- **用途**: 展示需要配置的项目

#### requirements.txt
- **功能**: Python 依赖包列表
- **包含**:
  - python-telegram-bot==20.7
  - requests==2.31.0
  - qrcode==7.4.2
  - Pillow==10.1.0
  - python-dotenv==1.0.0

#### .gitignore
- **功能**: Git 忽略文件
- **忽略内容**:
  - .env（敏感信息）
  - *.db（数据库文件）
  - *.log（日志文件）
  - __pycache__/
  - venv/

### 启动脚本

#### start.sh
- **平台**: Linux / Mac
- **功能**:
  - 自动创建虚拟环境
  - 自动安装依赖
  - 检查配置文件
  - 启动 Bot
- **使用**: `chmod +x start.sh && ./start.sh`

#### start.bat
- **平台**: Windows
- **功能**: 同 start.sh
- **使用**: 双击运行

### 文档文件

#### README.md
- **内容**: 完整的使用说明
- **章节**:
  - 核心功能介绍
  - 技术栈
  - 快速开始
  - 使用指南
  - 配置说明
  - 常见问题
  - 高级功能
  - 扩展思路

#### QUICKSTART.md
- **内容**: 5分钟快速上手指南
- **适合**: 快速部署和测试
- **包含**:
  - 3步极速部署
  - 配置参数获取
  - 功能测试
  - 常见问题

#### DEPLOY.md
- **内容**: 详细部署指南
- **章节**:
  - 服务器要求
  - 部署前准备
  - Linux/Mac 部署
  - Windows 部署
  - Docker 部署
  - 配置详解
  - 安全配置
  - 监控维护
  - 故障排查

#### ARCHITECTURE.md
- **内容**: 系统架构设计文档
- **章节**:
  - 整体架构图
  - 模块设计
  - 数据库设计
  - 业务流程
  - 安全设计
  - 性能优化
  - 扩展接口
  - 监控指标

#### PROJECT_SUMMARY.md
- **内容**: 项目交付总结
- **章节**:
  - 已完成功能清单
  - 技术亮点
  - 数据库设计说明
  - 使用流程
  - 安全特性
  - 部署建议
  - 代码质量
  - 未来扩展方向

#### FILE_STRUCTURE.md
- **内容**: 文件结构说明（本文件）
- **用途**: 快速了解项目结构

### 运行时文件（自动生成）

#### payment_bot.db
- **类型**: SQLite 数据库
- **内容**: 用户、订单、日志等数据
- **大小**: 约 1MB/1000 订单
- **备份**: 使用 `python manage.py backup`

#### tron_orders.db
- **类型**: SQLite 数据库
- **内容**: TRON 支付订单
- **管理**: 由 tron_payment.py 管理

#### bot.log
- **类型**: 日志文件
- **内容**: 运行日志
- **级别**: INFO/WARNING/ERROR
- **查看**: `tail -f bot.log`

#### backups/
- **类型**: 目录
- **内容**: 数据库备份文件
- **命名**: `*_backup_YYYYMMDD_HHMMSS.db`

#### exports/
- **类型**: 目录
- **内容**: 导出的 JSON 订单数据
- **命名**: `orders_export_YYYYMMDD_HHMMSS.json`

## 📊 文件大小统计

| 类型 | 文件数 | 总大小（估算） |
|------|--------|---------------|
| 核心代码 | 5 | 约 2500+ 行代码 |
| 配置文件 | 4 | < 1KB |
| 启动脚本 | 2 | < 5KB |
| 文档文件 | 6 | 约 50KB |
| **总计** | **17** | **约 60KB（源代码）** |

运行时数据：
- 数据库: 1MB/1000 订单
- 日志: 取决于日志级别和时间

## 🔄 文件依赖关系

```
bot.py
├── config.py          (配置)
├── database.py        (数据库)
└── tron_payment.py    (TRON 支付)

database.py
└── config.py          (数据库路径)

manage.py
├── database.py        (数据库操作)
└── config.py          (配置)

所有文件
└── .env               (环境变量)
```

## 📝 开发建议

### 修改配置
1. 编辑 `config.py` - 套餐、消息模板等
2. 编辑 `.env` - 敏感信息

### 添加功能
1. 在 `bot.py` 添加命令处理器
2. 在 `database.py` 添加数据库操作
3. 在 `config.py` 添加配置项

### 调试
1. 查看 `bot.log` 日志
2. 使用 `python manage.py` 查看数据
3. 设置 `LOG_LEVEL=DEBUG`

### 备份
```bash
python manage.py backup  # 备份数据库
cp .env .env.backup      # 备份配置
```

## ✅ 快速检查清单

部署前检查：
- [ ] 所有文件都已上传
- [ ] 已创建 `.env` 文件
- [ ] 已填写所有必需配置
- [ ] 已安装 Python 3.8+
- [ ] 已安装依赖 `pip install -r requirements.txt`

运行时检查：
- [ ] bot.py 正常启动
- [ ] 能响应 /start 命令
- [ ] 数据库文件已创建
- [ ] 日志正常记录

## 🎓 学习路径

1. **快速上手**: 阅读 QUICKSTART.md
2. **了解功能**: 阅读 README.md
3. **部署上线**: 阅读 DEPLOY.md
4. **深入理解**: 阅读 ARCHITECTURE.md
5. **代码修改**: 查看源代码注释

## 📞 文件位置速查

需要修改套餐价格？
→ `config.py` 第 45 行 `MEMBERSHIP_PLANS`

需要查看订单？
→ `python manage.py orders`

需要备份数据？
→ `python manage.py backup`

需要查看日志？
→ `bot.log` 或 `tail -f bot.log`

需要修改超时时间？
→ `.env` 中的 `ORDER_TIMEOUT_MINUTES`

---

**提示**: 所有文件都有详细的中文注释，直接打开阅读即可！


