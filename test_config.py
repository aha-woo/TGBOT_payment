#!/usr/bin/env python3
"""
配置诊断脚本
"""
import sys
import os

print("=" * 50)
print("Bot 配置诊断")
print("=" * 50)

try:
    from config import (
        ENABLE_MULTIPLE_PLANS, 
        DEFAULT_PLAN, 
        MEMBERSHIP_PLANS,
        XIANYU_PRODUCT_URL,
        BOT_TOKEN,
        ADMIN_USER_IDS
    )
    
    print("\n✅ 配置文件加载成功\n")
    
    print(f"1. 套餐模式:")
    print(f"   ENABLE_MULTIPLE_PLANS = {ENABLE_MULTIPLE_PLANS}")
    print(f"   类型: {type(ENABLE_MULTIPLE_PLANS)}")
    
    print(f"\n2. 默认套餐配置:")
    print(f"   DEFAULT_PLAN = {DEFAULT_PLAN}")
    
    print(f"\n3. 多套餐配置:")
    for key, plan in MEMBERSHIP_PLANS.items():
        print(f"   {key}: {plan['name']} - ¥{plan['price_cny']}")
    
    print(f"\n4. 闲鱼链接:")
    print(f"   XIANYU_PRODUCT_URL = {XIANYU_PRODUCT_URL}")
    
    print(f"\n5. Bot Token:")
    if BOT_TOKEN and len(BOT_TOKEN) > 20:
        print(f"   ✅ 已配置 (长度: {len(BOT_TOKEN)})")
    else:
        print(f"   ❌ 未正确配置")
    
    print(f"\n6. 管理员 ID:")
    print(f"   ADMIN_USER_IDS = {ADMIN_USER_IDS}")
    
    print("\n" + "=" * 50)
    print("✅ 所有配置项检查完成！")
    print("=" * 50)
    
except ImportError as e:
    print(f"\n❌ 错误：无法导入配置")
    print(f"详细信息: {e}")
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ 错误：{e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 测试数据库
print("\n" + "=" * 50)
print("数据库检查")
print("=" * 50)

try:
    from database import Database
    db = Database('payment_bot.db')
    print("✅ 数据库连接成功")
    
    # 测试数据库操作
    test_user_id = 999999999
    db.get_or_create_user(test_user_id, 'test_user', 'Test', 'User')
    print("✅ 数据库写入测试成功")
    
except Exception as e:
    print(f"❌ 数据库错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("诊断完成")
print("=" * 50)

