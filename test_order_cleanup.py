#!/usr/bin/env python3
"""
闲鱼订单自动清理功能测试脚本

使用方法：
    python3 test_order_cleanup.py
"""

import sys
from datetime import datetime, timedelta
from database import Database

def test_cleanup():
    """测试订单自动清理功能"""
    
    print("=" * 60)
    print("🧪 闲鱼订单自动清理功能测试")
    print("=" * 60)
    print()
    
    db = Database('payment_bot.db')
    
    # 1. 显示当前所有待支付的闲鱼订单
    print("📋 当前所有待支付闲鱼订单：")
    print("-" * 60)
    
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT order_id, user_id, amount, currency, created_at 
        FROM orders
        WHERE payment_method='xianyu' AND status='pending'
        ORDER BY created_at DESC
    """)
    
    pending_orders = cursor.fetchall()
    
    if not pending_orders:
        print("   ✅ 没有待支付的闲鱼订单")
    else:
        for order in pending_orders:
            order_id, user_id, amount, currency, created_at = order
            created_time = datetime.fromisoformat(created_at)
            age_minutes = (datetime.now() - created_time).total_seconds() / 60
            print(f"   • {order_id}")
            print(f"     用户: {user_id}")
            print(f"     金额: {amount} {currency}")
            print(f"     创建于: {created_at}")
            print(f"     已存在: {age_minutes:.1f} 分钟")
            print()
    
    print()
    
    # 2. 测试不同超时时间的清理效果
    test_timeouts = [1, 5, 10, 30, 60]
    
    print("🔍 模拟不同超时时间的清理效果：")
    print("-" * 60)
    
    for timeout in test_timeouts:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM orders
            WHERE payment_method='xianyu' 
            AND status='pending'
            AND created_at < ?
        """, (datetime.now() - timedelta(minutes=timeout),))
        
        count = cursor.fetchone()[0]
        print(f"   超时 {timeout:3d} 分钟：将清理 {count} 个订单")
    
    conn.close()
    print()
    
    # 3. 询问是否执行清理
    print("💡 提示：")
    print("   - 清理不会真正删除订单，只是将状态改为 'expired'")
    print("   - Bot 运行时会自动执行清理，无需手动操作")
    print("   - 如需手动测试清理功能，请输入超时时间（分钟）")
    print()
    
    try:
        response = input("是否执行手动清理测试？(输入超时分钟数，或直接回车跳过): ").strip()
        
        if response:
            timeout = int(response)
            print()
            print(f"🧹 执行清理：超时时间 {timeout} 分钟")
            print("-" * 60)
            
            cleaned_count = db.cleanup_expired_xianyu_orders(timeout)
            
            if cleaned_count > 0:
                print(f"   ✅ 成功清理 {cleaned_count} 个过期订单")
            else:
                print(f"   ℹ️ 没有需要清理的订单")
            
            print()
            
            # 显示清理后的状态
            print("📊 清理后的订单统计：")
            print("-" * 60)
            
            conn = db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT status, COUNT(*) as count
                FROM orders
                WHERE payment_method='xianyu'
                GROUP BY status
            """)
            
            stats = cursor.fetchall()
            for status, count in stats:
                emoji = {'pending': '⏳', 'paid': '✅', 'cancelled': '❌', 'expired': '⏰'}.get(status, '❓')
                print(f"   {emoji} {status:10s}: {count} 个")
            
            conn.close()
        else:
            print("⏭️  跳过手动清理测试")
    
    except ValueError:
        print("❌ 输入无效，跳过清理测试")
    except KeyboardInterrupt:
        print("\n\n⏹️  测试中断")
        sys.exit(0)
    
    print()
    print("=" * 60)
    print("✅ 测试完成！")
    print()
    print("💡 下一步：")
    print("   1. Bot 运行时会自动执行清理（每 5 分钟一次）")
    print("   2. 查看日志: pm2 logs payment-bot")
    print("   3. 调整配置: 编辑 .env 文件中的 XIANYU_ORDER_TIMEOUT_MINUTES")
    print("=" * 60)

if __name__ == '__main__':
    try:
        test_cleanup()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

