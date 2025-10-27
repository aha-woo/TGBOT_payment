# 配置指南

## 套餐模式配置 🆕

Bot 支持两种套餐模式，可根据实际需求灵活切换。

### 模式对比

| 特性 | 单套餐模式 | 多套餐模式 |
|-----|----------|----------|
| 配置值 | `ENABLE_MULTIPLE_PLANS=false` | `ENABLE_MULTIPLE_PLANS=true` |
| 适用场景 | 只有一个固定价格的会员 | 有多个套餐选择（月/季/年） |
| 用户体验 | 点击支付按钮直接跳转支付 | 先选择套餐再支付 |
| 按钮显示 | 显示价格（如"USDT 支付 - 10 USDT"） | 不显示价格 |
| 操作步骤 | 2 步（选择支付方式 → 支付） | 3 步（选择支付方式 → 选择套餐 → 支付） |

---

## 配置方法

### 1. 选择模式

在 `.env` 文件中设置：

```env
# 单套餐模式（推荐：只有一个套餐时）
ENABLE_MULTIPLE_PLANS=false

# 或

# 多套餐模式（推荐：有多个套餐时）
ENABLE_MULTIPLE_PLANS=true
```

### 2. 配置套餐

编辑 `config.py`：

#### 单套餐模式配置

```python
DEFAULT_PLAN = {
    'name': '会员',           # 套餐名称
    'days': 30,               # 会员天数
    'price_usdt': 10.0,       # USDT 价格
    'price_cny': 68.0         # 人民币价格
}
```

#### 多套餐模式配置

```python
MEMBERSHIP_PLANS = {
    'month': {
        'name': '月度会员',
        'days': 30,
        'price_usdt': 10.0,
        'price_cny': 68.0
    },
    'quarter': {
        'name': '季度会员',
        'days': 90,
        'price_usdt': 25.0,
        'price_cny': 178.0
    },
    'year': {
        'name': '年度会员',
        'days': 365,
        'price_usdt': 88.0,
        'price_cny': 588.0
    }
}
```

### 3. 重启 Bot

```bash
pm2 restart payment-bot
```

---

## 界面效果

### 单套餐模式

**欢迎页面按钮**：
```
┌────────────────────────────────┐
│ [💎 USDT 支付 - 10 USDT]        │
│ [🏪 闲鱼支付 - ¥68]             │
└────────────────────────────────┘
```

**用户流程**：
```
点击 [💎 USDT 支付 - 10 USDT]
  ↓
直接显示支付二维码（无需再选择套餐）
```

---

### 多套餐模式

**欢迎页面按钮**：
```
┌────────────────────────────────┐
│ [💎 USDT 支付]                  │
│ [🏪 闲鱼支付]                   │
└────────────────────────────────┘
```

**用户流程**：
```
点击 [💎 USDT 支付]
  ↓
选择套餐（月度/季度/年度）
  ↓
显示支付二维码
```

---

## 其他配置

### 自定义欢迎页面

在 `.env` 中配置：

```env
# 客服链接
CUSTOMER_SERVICE_URL=https://t.me/your_service

# 欢迎图片（留空则不显示）
WELCOME_IMAGE=

# 欢迎消息
WELCOME_MESSAGE="🎉 欢迎！立即购买会员"
```

### 获取图片 file_id

1. 向 Bot 发送图片
2. 在广告管理中上传图片会显示 file_id
3. 或在日志中查找 file_id

---

## 常见问题

**Q: 可以随时切换模式吗？**

A: 可以。修改 `.env` 中的 `ENABLE_MULTIPLE_PLANS` 并重启 Bot 即可。不影响现有数据。

**Q: 单套餐模式下如何修改价格？**

A: 修改 `config.py` 中的 `DEFAULT_PLAN`，然后重启 Bot。

**Q: 多套餐模式下可以添加更多套餐吗？**

A: 可以。在 `config.py` 的 `MEMBERSHIP_PLANS` 中添加新的套餐配置即可。

---

## 推荐配置

### 场景 1: 个人频道，固定价格

```env
ENABLE_MULTIPLE_PLANS=false
```

```python
DEFAULT_PLAN = {
    'name': '会员',
    'days': 30,
    'price_usdt': 10.0,
    'price_cny': 68.0
}
```

### 场景 2: 商业频道，多种选择

```env
ENABLE_MULTIPLE_PLANS=true
```

保持 `MEMBERSHIP_PLANS` 的默认配置，根据需要调整价格。

---

查看更多：[README.md](README.md) | [QUICKSTART.md](QUICKSTART.md)

