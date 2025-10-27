import requests
import qrcode
from io import BytesIO
import time
import sqlite3
from datetime import datetime, timedelta
from threading import Thread, Lock
from collections import defaultdict
import logging
from typing import Optional, Callable, List, Dict, Any
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class TronPayment:
    """
    TRON TRC20-USDT 支付系统
    
    功能：
    - 生成支付订单和二维码
    - 自动监控收款
    - 订单状态查询
    - 回调通知机制
    - 手动退款管理（不暴露私钥）
    - 订单统计和管理
    
    适用场景：Telegram Bot, Discord Bot, Web 应用等
    """
    
    # TRC20-USDT 合约地址
    USDT_CONTRACT = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"
    
    def __init__(
        self, 
        wallet_address: str, 
        tronscan_api_key: str, 
        db_path: str = 'orders.db',
        poll_interval: int = 15,  # 轮询间隔（秒）
        default_timeout: int = 30,  # 默认订单超时（分钟）
        min_confirmations: int = 1,  # 最小确认数
    ):
        """
        初始化支付系统
        
        Args:
            wallet_address: 收款地址（T 开头）
            tronscan_api_key: TronScan API Key
            db_path: 数据库文件路径
            poll_interval: 轮询间隔（秒）
            default_timeout: 默认订单超时时间（分钟）
            min_confirmations: 最小区块确认数
        """
        if not self._validate_address(wallet_address):
            raise ValueError(f"Invalid TRON address: {wallet_address}")
        
        self.wallet_address = wallet_address
        self.api_key = tronscan_api_key
        self.base_url = "https://apilist.tronscanapi.com/api"
        self.poll_interval = poll_interval
        self.default_timeout = default_timeout
        self.min_confirmations = min_confirmations
        
        self.logger = logging.getLogger(f"TronPayment-{wallet_address[:8]}")
        self.db_lock = Lock()  # 数据库操作锁
        self.init_db(db_path)
        
        self.pending_orders = defaultdict(dict)
        self.monitoring_threads = {}
        
        # 回调函数
        self.on_payment_received: Optional[Callable] = None
        self.on_order_timeout: Optional[Callable] = None
        self.on_order_cancelled: Optional[Callable] = None
        
        self.logger.info(f"TronPayment initialized for wallet {wallet_address}")
    
    def _validate_address(self, address: str) -> bool:
        """验证 TRON 地址格式"""
        return isinstance(address, str) and address.startswith('T') and len(address) == 34
    
    def _validate_amount(self, amount: float) -> bool:
        """验证金额"""
        return isinstance(amount, (int, float)) and amount > 0 and amount <= 1000000
    
    def init_db(self, db_path: str):
        """初始化数据库"""
        self.db_path = db_path
        with Lock():
            conn = sqlite3.connect(db_path, check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    amount REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    paid_at TIMESTAMP,
                    cancelled_at TIMESTAMP,
                    timeout_at TIMESTAMP,
                    memo TEXT,
                    tx_hash TEXT,
                    refund_address TEXT,
                    refund_status TEXT,
                    refund_tx_hash TEXT,
                    notes TEXT
                )
            ''')
            
            # 创建索引以提高查询性能
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON orders(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON orders(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON orders(created_at)')
            
            conn.commit()
            conn.close()
    
    def _get_db_connection(self):
        """获取线程安全的数据库连接"""
        return sqlite3.connect(self.db_path, check_same_thread=False)
    
    def set_callback(self, event: str, callback: Callable):
        """
        设置回调函数
        
        Args:
            event: 事件类型 ('payment_received', 'order_timeout', 'order_cancelled')
            callback: 回调函数
        
        Example:
            def on_payment(order_id, order_info):
                print(f"Payment received for {order_id}")
                # 发送 Telegram 消息、解锁功能等
            
            payment.set_callback('payment_received', on_payment)
        """
        if event == 'payment_received':
            self.on_payment_received = callback
        elif event == 'order_timeout':
            self.on_order_timeout = callback
        elif event == 'order_cancelled':
            self.on_order_cancelled = callback
        else:
            raise ValueError(f"Unknown event type: {event}")
        
        self.logger.info(f"Callback set for event: {event}")
    
    def create_order(
        self, 
        user_id: str, 
        amount_usdt: float, 
        timeout_minutes: Optional[int] = None,
        notes: str = ""
    ) -> Dict[str, Any]:
        """
        生成支付订单
        
        Args:
            user_id: 用户 ID
            amount_usdt: USDT 金额
            timeout_minutes: 订单超时时间（分钟），None 使用默认值
            notes: 订单备注
        
        Returns:
            {
                'order_id': str,
                'qr_code': BytesIO,  # QR 码图片
                'pay_uri': str,      # 支付 URI
                'amount': float,
                'wallet_address': str,
                'timeout_at': datetime,
                'memo': str
            }
        """
        if not self._validate_amount(amount_usdt):
            raise ValueError(f"Invalid amount: {amount_usdt}")
        
        timeout_minutes = timeout_minutes or self.default_timeout
        order_id = f"order_{user_id}_{int(time.time() * 1000)}"
        memo = order_id
        timeout_at = datetime.now() + timedelta(minutes=timeout_minutes)
        
        # 生成支付 URI
        pay_uri = f"tron:{self.wallet_address}?amount={amount_usdt}&token=USDT&memo={memo}"
        
        # 生成 QR 码
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(pay_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        qr_bio = BytesIO()
        img.save(qr_bio, 'PNG')
        qr_bio.seek(0)
        
        # 存入数据库
        with self.db_lock:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """INSERT INTO orders 
                    (order_id, user_id, amount, status, created_at, timeout_at, memo, notes) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (order_id, user_id, amount_usdt, 'pending', datetime.now(), timeout_at, memo, notes)
                )
                conn.commit()
            except Exception as e:
                self.logger.error(f"Failed to create order: {e}")
                raise
            finally:
                conn.close()
        
        # 缓存订单信息
        self.pending_orders[order_id] = {
            'user_id': user_id,
            'amount': amount_usdt,
            'status': 'pending',
            'timeout': timeout_at.timestamp(),
            'memo': memo
        }
        
        # 启动监控线程
        thread = Thread(target=self._monitor_order, args=(order_id,), daemon=True)
        thread.start()
        self.monitoring_threads[order_id] = thread
        
        self.logger.info(f"Order created: {order_id} for user {user_id}, amount {amount_usdt} USDT")
        
        return {
            'order_id': order_id,
            'qr_code': qr_bio,
            'pay_uri': pay_uri,
            'amount': amount_usdt,
            'wallet_address': self.wallet_address,
            'timeout_at': timeout_at,
            'memo': memo,
            'usdt_contract': self.USDT_CONTRACT
        }
    
    def _monitor_order(self, order_id: str):
        """后台监控订单支付状态"""
        order = self.pending_orders.get(order_id)
        if not order:
            self.logger.warning(f"Order {order_id} not found in pending orders")
            return
        
        self.logger.info(f"Start monitoring order: {order_id}")
        
        while order.get('status') == 'pending':
            try:
                # 检查超时
                if time.time() > order['timeout']:
                    self.logger.info(f"Order {order_id} timeout")
                    self._handle_timeout(order_id)
                    break
                
                # 查询最近交易
                if self._check_payment(order_id, order):
                    break
                
                time.sleep(self.poll_interval)
                
            except Exception as e:
                self.logger.error(f"Error monitoring order {order_id}: {e}")
                time.sleep(self.poll_interval)
        
        # 清理
        if order_id in self.monitoring_threads:
            del self.monitoring_threads[order_id]
        
        self.logger.info(f"Stop monitoring order: {order_id}")
    
    def _check_payment(self, order_id: str, order: Dict) -> bool:
        """检查支付是否完成"""
        try:
            # 查询 TRC20 转账记录
            url = f"{self.base_url}/token_trc20/transfers"
            params = {
                'toAddress': self.wallet_address,
                'contractAddress': self.USDT_CONTRACT,
                'limit': 20,
                'sort': '-timestamp'
            }
            headers = {'TRON-PRO-API-KEY': self.api_key}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'token_transfers' in data:
                for tx in data['token_transfers']:
                    # 检查金额
                    amount_received = float(tx.get('quant', 0)) / 1e6  # USDT 6 位小数
                    
                    # 检查是否匹配（可以通过 memo 或金额+时间窗口）
                    if amount_received >= order['amount']:
                        tx_time = tx.get('block_timestamp', 0) / 1000
                        order_time = order['timeout'] - (self.default_timeout * 60)
                        
                        # 交易时间在订单创建之后
                        if tx_time > order_time:
                            tx_hash = tx.get('transaction_id')
                            self.logger.info(f"Payment found for order {order_id}: {tx_hash}")
                            self._handle_payment_received(order_id, tx_hash, amount_received)
                            return True
            
        except Exception as e:
            self.logger.error(f"Error checking payment for {order_id}: {e}")
        
        return False
    
    def _handle_payment_received(self, order_id: str, tx_hash: str, amount: float):
        """处理支付成功"""
        with self.db_lock:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE orders SET status='paid', paid_at=?, tx_hash=? WHERE order_id=?",
                    (datetime.now(), tx_hash, order_id)
                )
                conn.commit()
            finally:
                conn.close()
        
        # 更新缓存
        if order_id in self.pending_orders:
            self.pending_orders[order_id]['status'] = 'paid'
        
        # 触发回调
        if self.on_payment_received:
            try:
                order_info = self.get_order_status(order_id)
                self.on_payment_received(order_id, order_info)
            except Exception as e:
                self.logger.error(f"Error in payment callback: {e}")
        
        self.logger.info(f"Order {order_id} marked as paid, tx: {tx_hash}")
    
    def _handle_timeout(self, order_id: str):
        """处理订单超时"""
        with self.db_lock:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE orders SET status='timeout', cancelled_at=? WHERE order_id=? AND status='pending'",
                    (datetime.now(), order_id)
                )
                conn.commit()
            finally:
                conn.close()
        
        # 更新缓存
        if order_id in self.pending_orders:
            self.pending_orders[order_id]['status'] = 'timeout'
        
        # 触发回调
        if self.on_order_timeout:
            try:
                order_info = self.get_order_status(order_id)
                self.on_order_timeout(order_id, order_info)
            except Exception as e:
                self.logger.error(f"Error in timeout callback: {e}")
        
        self.logger.info(f"Order {order_id} timeout")
    
    def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        查询订单状态
        
        Returns:
            订单信息字典，如果不存在返回 None
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM orders WHERE order_id=?", (order_id,))
            row = cursor.fetchone()
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            return None
        finally:
            conn.close()
    
    def get_user_orders(
        self, 
        user_id: str, 
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        查询用户的所有订单
        
        Args:
            user_id: 用户 ID
            status: 订单状态筛选 ('pending', 'paid', 'timeout', 'cancelled')
            limit: 返回数量限制
        
        Returns:
            订单列表
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()
        try:
            if status:
                cursor.execute(
                    "SELECT * FROM orders WHERE user_id=? AND status=? ORDER BY created_at DESC LIMIT ?",
                    (user_id, status, limit)
                )
            else:
                cursor.execute(
                    "SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC LIMIT ?",
                    (user_id, limit)
                )
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        finally:
            conn.close()
    
    def get_all_orders(
        self, 
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        查询所有订单（管理功能）
        
        Args:
            status: 状态筛选
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回数量限制
        
        Returns:
            订单列表
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()
        try:
            query = "SELECT * FROM orders WHERE 1=1"
            params = []
            
            if status:
                query += " AND status=?"
                params.append(status)
            
            if start_date:
                query += " AND created_at >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND created_at <= ?"
                params.append(end_date)
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        finally:
            conn.close()
    
    def get_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取订单统计信息
        
        Args:
            user_id: 指定用户 ID，None 表示全局统计
        
        Returns:
            统计信息字典
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()
        try:
            if user_id:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_orders,
                        SUM(CASE WHEN status='paid' THEN 1 ELSE 0 END) as paid_orders,
                        SUM(CASE WHEN status='paid' THEN amount ELSE 0 END) as total_paid_amount,
                        SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) as pending_orders,
                        SUM(CASE WHEN status='timeout' THEN 1 ELSE 0 END) as timeout_orders,
                        SUM(CASE WHEN status='cancelled' THEN 1 ELSE 0 END) as cancelled_orders
                    FROM orders WHERE user_id=?
                """, (user_id,))
            else:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_orders,
                        SUM(CASE WHEN status='paid' THEN 1 ELSE 0 END) as paid_orders,
                        SUM(CASE WHEN status='paid' THEN amount ELSE 0 END) as total_paid_amount,
                        SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) as pending_orders,
                        SUM(CASE WHEN status='timeout' THEN 1 ELSE 0 END) as timeout_orders,
                        SUM(CASE WHEN status='cancelled' THEN 1 ELSE 0 END) as cancelled_orders,
                        COUNT(DISTINCT user_id) as total_users
                    FROM orders
                """)
            
            row = cursor.fetchone()
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        finally:
            conn.close()
    
    def cancel_order(self, order_id: str, reason: str = 'manual') -> bool:
        """
        取消订单
        
        Args:
            order_id: 订单 ID
            reason: 取消原因
        
        Returns:
            是否成功
        """
        with self.db_lock:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE orders SET status='cancelled', cancelled_at=?, notes=? WHERE order_id=? AND status='pending'",
                    (datetime.now(), f"Cancelled: {reason}", order_id)
                )
                conn.commit()
                success = cursor.rowcount > 0
            finally:
                conn.close()
        
        if success:
            # 更新缓存
            if order_id in self.pending_orders:
                self.pending_orders[order_id]['status'] = 'cancelled'
            
            # 触发回调
            if self.on_order_cancelled:
                try:
                    order_info = self.get_order_status(order_id)
                    self.on_order_cancelled(order_id, order_info)
                except Exception as e:
                    self.logger.error(f"Error in cancel callback: {e}")
            
            self.logger.info(f"Order {order_id} cancelled: {reason}")
        
        return success
    
    def request_refund(self, order_id: str, refund_address: str, notes: str = "") -> Dict[str, Any]:
        """
        申请退款（不需要私钥，手动处理）
        
        这个方法只记录退款请求，不执行实际转账。
        管理员可以通过 get_pending_refunds() 查看待处理退款，
        然后手动使用钱包转账。
        
        Args:
            order_id: 订单 ID
            refund_address: 退款地址
            notes: 退款备注
        
        Returns:
            退款信息
        """
        # 验证订单状态
        order = self.get_order_status(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        if order['status'] != 'paid':
            raise ValueError(f"Order {order_id} is not paid, cannot refund")
        
        if not self._validate_address(refund_address):
            raise ValueError(f"Invalid refund address: {refund_address}")
        
        # 记录退款请求
        with self.db_lock:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """UPDATE orders 
                    SET refund_address=?, refund_status='pending', notes=? 
                    WHERE order_id=?""",
                    (refund_address, f"Refund requested: {notes}", order_id)
                )
                conn.commit()
            finally:
                conn.close()
        
        self.logger.info(f"Refund requested for order {order_id} to {refund_address}")
        
        return {
            'order_id': order_id,
            'amount': order['amount'],
            'refund_address': refund_address,
            'usdt_contract': self.USDT_CONTRACT,
            'memo': f"Refund for {order_id}",
            'notes': notes
        }
    
    def confirm_refund(self, order_id: str, tx_hash: str) -> bool:
        """
        确认退款已完成（手动转账后调用）
        
        Args:
            order_id: 订单 ID
            tx_hash: 退款交易哈希
        
        Returns:
            是否成功
        """
        with self.db_lock:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """UPDATE orders 
                    SET status='refunded', refund_status='completed', refund_tx_hash=? 
                    WHERE order_id=? AND refund_status='pending'""",
                    (tx_hash, order_id)
                )
                conn.commit()
                success = cursor.rowcount > 0
            finally:
                conn.close()
        
        if success:
            self.logger.info(f"Refund confirmed for order {order_id}, tx: {tx_hash}")
        
        return success
    
    def get_pending_refunds(self) -> List[Dict[str, Any]]:
        """
        获取待处理的退款请求（管理功能）
        
        Returns:
            待退款订单列表
        """
        conn = self._get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT * FROM orders WHERE refund_status='pending' ORDER BY created_at DESC"
            )
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        finally:
            conn.close()
    
    def verify_transaction(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """
        验证交易是否存在且有效
        
        Args:
            tx_hash: 交易哈希
        
        Returns:
            交易信息，如果无效返回 None
        """
        try:
            url = f"{self.base_url}/transaction-info"
            params = {'hash': tx_hash}
            headers = {'TRON-PRO-API-KEY': self.api_key}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('confirmed'):
                return {
                    'tx_hash': tx_hash,
                    'confirmed': True,
                    'timestamp': data.get('timestamp'),
                    'block': data.get('block')
                }
        except Exception as e:
            self.logger.error(f"Error verifying transaction {tx_hash}: {e}")
        
        return None
    
    def cleanup_old_orders(self, days: int = 90) -> int:
        """
        清理旧订单（管理功能）
        
        Args:
            days: 保留最近多少天的订单
        
        Returns:
            删除的订单数量
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with self.db_lock:
            conn = self._get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """DELETE FROM orders 
                    WHERE created_at < ? AND status IN ('timeout', 'cancelled')""",
                    (cutoff_date,)
                )
                conn.commit()
                deleted = cursor.rowcount
            finally:
                conn.close()
        
        self.logger.info(f"Cleaned up {deleted} old orders")
        return deleted
    
    def export_orders(self, filepath: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
        """
        导出订单到 JSON 文件
        
        Args:
            filepath: 导出文件路径
            start_date: 开始日期
            end_date: 结束日期
        """
        orders = self.get_all_orders(start_date=start_date, end_date=end_date, limit=10000)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(orders, f, indent=2, ensure_ascii=False, default=str)
        
        self.logger.info(f"Exported {len(orders)} orders to {filepath}")
    
    def close(self):
        """关闭支付系统，清理资源"""
        # 等待所有监控线程结束
        for thread in self.monitoring_threads.values():
            if thread.is_alive():
                thread.join(timeout=5)
        
        self.logger.info("TronPayment closed")


if __name__ == "__main__":
    # 使用示例
    print("=== TRON Payment System ===\n")
    
    # 1. 初始化支付系统
    payment = TronPayment(
        wallet_address="TYourWalletAddress123456789",  # 替换为你的地址
        tronscan_api_key="your-api-key-here",  # 替换为你的 API Key
        poll_interval=15,  # 15秒轮询一次
        default_timeout=30  # 默认30分钟超时
    )
    
    # 2. 设置回调函数
    def on_payment_received(order_id, order_info):
        print(f"\n✅ 支付成功！")
        print(f"订单 ID: {order_id}")
        print(f"用户: {order_info['user_id']}")
        print(f"金额: {order_info['amount']} USDT")
        print(f"交易哈希: {order_info['tx_hash']}")
        
        # 这里可以：
        # - 发送 Telegram 通知
        # - 解锁 Discord 权限
        # - 激活会员功能等
    
    def on_order_timeout(order_id, order_info):
        print(f"\n⏰ 订单超时: {order_id}")
        # 可以通知用户订单已过期
    
    payment.set_callback('payment_received', on_payment_received)
    payment.set_callback('order_timeout', on_order_timeout)
    
    # 3. 创建订单
    order = payment.create_order(
        user_id="telegram_user_123",
        amount_usdt=10.5,
        timeout_minutes=30,
        notes="购买 VIP 会员"
    )
    
    print(f"订单创建成功！")
    print(f"订单 ID: {order['order_id']}")
    print(f"金额: {order['amount']} USDT")
    print(f"收款地址: {order['wallet_address']}")
    print(f"支付 URI: {order['pay_uri']}")
    print(f"过期时间: {order['timeout_at']}")
    
    # QR 码可以这样使用：
    # order['qr_code'].save('payment_qr.png')  # 保存为文件
    # 或发送到 Telegram/Discord
    
    # 4. 查询订单状态
    status = payment.get_order_status(order['order_id'])
    print(f"\n订单状态: {status['status']}")
    
    # 5. 查询用户所有订单
    user_orders = payment.get_user_orders("telegram_user_123")
    print(f"\n用户订单数: {len(user_orders)}")
    
    # 6. 获取统计信息
    stats = payment.get_statistics()
    print(f"\n系统统计:")
    print(f"总订单数: {stats['total_orders']}")
    print(f"已支付: {stats['paid_orders']}")
    print(f"总收入: {stats['total_paid_amount']} USDT")
    
    # 7. 申请退款（不需要私钥）
    # refund_info = payment.request_refund(
    #     order_id=order['order_id'],
    #     refund_address="TUserWalletAddress",
    #     notes="用户申请退款"
    # )
    # print(f"\n退款信息:")
    # print(f"金额: {refund_info['amount']} USDT")
    # print(f"地址: {refund_info['refund_address']}")
    
    # 8. 管理员查看待退款订单
    # pending_refunds = payment.get_pending_refunds()
    # for refund in pending_refunds:
    #     print(f"订单 {refund['order_id']} 需退款 {refund['amount']} USDT 到 {refund['refund_address']}")
    #     # 手动转账后确认
    #     # payment.confirm_refund(refund['order_id'], 'transaction_hash_here')
    
    # 9. 取消订单
    # payment.cancel_order(order['order_id'], reason="用户取消")
    
    # 10. 清理旧订单
    # payment.cleanup_old_orders(days=90)
    
    print("\n系统运行中... (Ctrl+C 退出)")
    
    try:
        # 保持程序运行，监控支付
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在关闭...")
        payment.close()
