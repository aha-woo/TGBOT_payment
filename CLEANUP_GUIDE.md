# 测试数据清理工具使用指南

## 🧹 功能概述

`cleanup_test_data.py` 是一个交互式的数据清理工具，用于清除测试数据。

---

## 🚀 使用方法

### 基础使用

```bash
cd /root/TGBOT_payment
source venv/bin/activate  # 如果使用了虚拟环境
python3 cleanup_test_data.py
```

---

## 📋 功能菜单

### 启动后会看到：

```
============================================================
  🧹 测试数据清理工具
============================================================

------------------------------------------------------------
  📊 当前数据库统计
------------------------------------------------------------

📦 订单: 15 个
   💎 tron     ⏰ timeout   : 3 个
   🏪 xianyu   ⏰ expired   : 4 个
   🏪 xianyu   ❌ cancelled : 3 个
   ...

👥 用户: 5 个
📝 日志: 120 条
📨 邀请记录: 8 条
📢 广告模板: 2 个
⏰ 定时任务: 1 个
📊 广告日志: 10 条

------------------------------------------------------------
  📋 选择操作
------------------------------------------------------------

1. 清除所有订单
2. 清除所有用户（保留管理员）
3. 清除所有日志
4. 清除所有邀请记录
5. 清除所有广告数据
6. 🔥 清除所有数据（保留管理员）
7. 💾 备份数据库
0. 退出

请选择 (0-7):
```

---

## 🎯 选项说明

### 选项 1：清除所有订单
- 清除 `orders` 表中的所有订单
- 包括 pending、paid、cancelled、expired、timeout 等所有状态
- **不影响**：用户数据、日志

### 选项 2：清除所有用户（保留管理员）
- 清除 `users` 表中的所有用户
- **自动保留** `.env` 中配置的管理员账户
- **不影响**：订单数据、日志

### 选项 3：清除所有日志
- 清除 `system_logs` 表中的所有日志记录
- **不影响**：订单、用户、业务数据

### 选项 4：清除所有邀请记录
- 清除 `channel_invites` 表中的所有邀请记录
- **不影响**：订单、用户

### 选项 5：清除所有广告数据
- 清除 `promo_templates` 表中的广告模板
- 清除 `scheduled_tasks` 表中的定时任务
- 清除 `promo_logs` 表中的广告日志
- **不影响**：订单、用户

### 选项 6：🔥 清除所有数据（保留管理员）
- **一次性清除所有测试数据**
- 清除：订单、用户、日志、邀请、广告
- **保留**：管理员账户
- **需要输入 `DELETE ALL` 确认**

### 选项 7：💾 备份数据库
- 创建数据库备份文件
- 文件名格式：`payment_bot.db.backup_20251028_120530`
- **建议在清除前先备份！**

---

## ⚠️ 安全特性

### 1. 交互式确认
- 所有删除操作都需要确认
- 输入 `yes` 确认删除
- 输入其他内容取消操作

### 2. 管理员保护
- 自动保护 `.env` 中配置的管理员
- 清除用户时不会删除管理员账户

### 3. 清除所有数据需要特殊确认
- 需要输入 `DELETE ALL`（区分大小写）
- 防止误操作

### 4. 数据库备份
- 提供备份功能
- 建议在大规模清除前先备份

---

## 📝 使用场景

### 场景 1：清除测试订单

```bash
python3 cleanup_test_data.py
# 选择 1
# 输入 yes 确认
```

**效果**：清除所有订单，但保留用户数据

---

### 场景 2：完全重置（保留管理员）

```bash
python3 cleanup_test_data.py
# 选择 7 - 先备份
# 选择 6 - 清除所有数据
# 输入 DELETE ALL 确认
```

**效果**：
- ✅ 数据库已备份
- ✅ 所有测试数据已清除
- ✅ 管理员账户保留
- ✅ 可以重新开始测试

---

### 场景 3：只清理日志

```bash
python3 cleanup_test_data.py
# 选择 3
# 输入 yes 确认
```

**效果**：清除所有日志，不影响业务数据

---

### 场景 4：分步清理

```bash
python3 cleanup_test_data.py
# 选择 1 - 清除订单
# 选择 4 - 清除邀请记录
# 选择 3 - 清除日志
# 选择 0 - 退出
```

**效果**：精细控制清理范围

---

## 🔍 查看数据库状态

脚本启动后会自动显示当前数据库统计：

```
📦 订单: 15 个
   💎 tron     ⏰ timeout   : 3 个
   🏪 xianyu   ⏰ expired   : 4 个
   🏪 xianyu   ❌ cancelled : 3 个
   🏪 xianyu   ⏳ pending   : 2 个
   💎 tron     ✅ paid      : 3 个

👥 用户: 5 个
📝 日志: 120 条
📨 邀请记录: 8 条
📢 广告模板: 2 个
⏰ 定时任务: 1 个
📊 广告日志: 10 条
```

每次操作后都会刷新显示，方便确认结果。

---

## 💡 最佳实践

### 定期清理建议

**开发测试阶段**：
- 每天清理一次订单和日志
- 保留少量测试用户

**压力测试后**：
- 完全清除所有数据
- 重新开始测试

**上线前**：
- 清除所有测试数据
- 只保留管理员账户
- 创建数据库备份

---

## 🛡️ 数据恢复

### 从备份恢复

如果误删了数据：

```bash
# 停止 Bot
pm2 stop payment-bot

# 恢复备份
cp payment_bot.db.backup_20251028_120530 payment_bot.db

# 重启 Bot
pm2 restart payment-bot
```

---

## ⚙️ 高级用法

### 命令行直接清理（无交互）

如果需要在脚本中调用，可以修改代码：

```python
from cleanup_test_data import clear_orders, clear_logs
from database import Database

db = Database('payment_bot.db')
clear_orders(db)
clear_logs(db)
```

---

## 🐛 故障排除

### Q1: 权限错误
```bash
PermissionError: [Errno 13] Permission denied: 'payment_bot.db'
```

**解决**：停止 Bot 后再运行清理脚本
```bash
pm2 stop payment-bot
python3 cleanup_test_data.py
pm2 restart payment-bot
```

---

### Q2: 找不到数据库文件
```bash
FileNotFoundError: [Errno 2] No such file or directory: 'payment_bot.db'
```

**解决**：确认在正确的目录运行
```bash
cd /root/TGBOT_payment
python3 cleanup_test_data.py
```

---

### Q3: 导入错误
```bash
ModuleNotFoundError: No module named 'database'
```

**解决**：激活虚拟环境
```bash
source venv/bin/activate
python3 cleanup_test_data.py
```

---

## 📊 清理后验证

### 检查数据是否清除

```bash
# 进入数据库
sqlite3 payment_bot.db

# 检查订单
SELECT COUNT(*) FROM orders;

# 检查用户
SELECT COUNT(*) FROM users;

# 退出
.quit
```

### 检查 Bot 是否正常

```bash
# 重启 Bot
pm2 restart payment-bot

# 查看日志
pm2 logs payment-bot --lines 20

# 测试功能
# 在 Telegram 中发送 /start
```

---

## 🎯 快速参考

| 需求 | 操作 | 确认方式 |
|-----|------|---------|
| 清除测试订单 | 选项 1 | `yes` |
| 完全重置 | 选项 6 | `DELETE ALL` |
| 备份数据库 | 选项 7 | 无需确认 |
| 只清理日志 | 选项 3 | `yes` |
| 查看统计 | 启动脚本 | 自动显示 |

---

## ✅ 总结

**优点**：
- ✅ 交互式操作，安全可控
- ✅ 实时显示数据统计
- ✅ 自动保护管理员账户
- ✅ 支持数据库备份
- ✅ 支持分步清理

**注意事项**：
- ⚠️ 清除前建议先备份
- ⚠️ 停止 Bot 后再清理
- ⚠️ 清除操作不可逆（除非有备份）

---

💡 **现在就试试吧！运行 `python3 cleanup_test_data.py` 开始清理测试数据！** 🧹

