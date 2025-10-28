#!/usr/bin/env python3
"""
清理测试订单脚本
"""
from database import Database

# 您的 User ID
YOUR_USER_ID = 8068014765

db = Database('payment_bot.db')

print("=" * 50)
print("清理测试订单")
print("=" * 50)

# 查看当前订单
print(f"\n查询用户 {YOUR_USER_ID} 的待支付订单...")
conn = db.get_connection()
cursor = conn.cursor()

cursor.execute("""
    SELECT order_id, payment_method, amount, currency, created_at 
    FROM orders 
    WHERE user_id = ? AND status = 'pending'
    ORDER BY created_at DESC
""", (YOUR_USER_ID,))

orders = cursor.fetchall()

if not orders:
    print("✅ 没有待支付订单")
else:
    print(f"\n找到 {len(orders)} 个待支付订单：")
    for order in orders:
        print(f"  - {order[0]} | {order[1]} | {order[2]} {order[3]} | {order[4]}")
    
    # 取消所有待支付订单
    print(f"\n正在取消这些订单...")
    cursor.execute("""
        UPDATE orders 
        SET status = 'cancelled' 
        WHERE user_id = ? AND status = 'pending'
    """, (YOUR_USER_ID,))
    
    conn.commit()
    print(f"✅ 已取消 {len(orders)} 个订单")

conn.close()

print("\n" + "=" * 50)
print("清理完成！现在可以重新测试了")
print("=" * 50)

