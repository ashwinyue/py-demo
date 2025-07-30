import random
import string
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from app.core.database import Base


class VerificationCode(Base):
    """验证码模型"""
    __tablename__ = 'verification_codes'
    
    id = Column(Integer, primary_key=True)
    
    # 验证码信息
    code = Column(String(10), nullable=False, index=True)
    code_type = Column(String(20), nullable=False, index=True)  # email_verify, password_reset, login_verify, phone_verify
    
    # 用户信息
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # 可为空，支持注册前验证
    email = Column(String(120), nullable=True, index=True)
    phone = Column(String(20), nullable=True, index=True)
    
    # 验证码状态
    is_used = Column(Boolean, default=False, nullable=False)
    is_expired = Column(Boolean, default=False, nullable=False)
    
    # 使用信息
    used_at = Column(DateTime, nullable=True)
    used_ip = Column(String(45), nullable=True)
    
    # 发送信息
    send_method = Column(String(10), default='email', nullable=False)  # email, sms
    send_count = Column(Integer, default=1, nullable=False)  # 发送次数
    last_send_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 验证尝试
    verify_attempts = Column(Integer, default=0, nullable=False)
    max_attempts = Column(Integer, default=5, nullable=False)
    
    # 时间字段
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 索引
    __table_args__ = (
        Index('idx_verification_codes_email_type', 'email', 'code_type'),
        Index('idx_verification_codes_phone_type', 'phone', 'code_type'),
        Index('idx_verification_codes_expires', 'expires_at'),
    )
    
    def __repr__(self):
        return f'<VerificationCode {self.code_type} for {self.email or self.phone}>'
    
    def is_valid(self):
        """检查验证码是否有效"""
        if self.is_used or self.is_expired:
            return False
        if datetime.utcnow() > self.expires_at:
            self.is_expired = True
            return False
        if self.verify_attempts >= self.max_attempts:
            return False
        return True
    
    def verify(self, code, ip_address=None):
        """验证验证码"""
        self.verify_attempts += 1
        self.updated_at = datetime.utcnow()
        
        if not self.is_valid():
            return False, 'Verification code is invalid or expired'
        
        if self.code != code:
            if self.verify_attempts >= self.max_attempts:
                return False, 'Too many failed attempts'
            return False, 'Invalid verification code'
        
        # 验证成功
        self.is_used = True
        self.used_at = datetime.utcnow()
        self.used_ip = ip_address
        
        return True, 'Verification successful'
    
    def mark_expired(self):
        """标记为已过期"""
        self.is_expired = True
        self.updated_at = datetime.utcnow()
    
    def can_resend(self, cooldown_minutes=1):
        """检查是否可以重新发送"""
        if not self.last_send_at:
            return True
        
        cooldown = timedelta(minutes=cooldown_minutes)
        return datetime.utcnow() - self.last_send_at >= cooldown
    
    def mark_resent(self):
        """标记为已重新发送"""
        self.send_count += 1
        self.last_send_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self, include_code=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'code_type': self.code_type,
            'user_id': self.user_id,
            'email': self.email,
            'phone': self.phone,
            'is_used': self.is_used,
            'is_expired': self.is_expired,
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'send_method': self.send_method,
            'send_count': self.send_count,
            'last_send_at': self.last_send_at.isoformat() if self.last_send_at else None,
            'verify_attempts': self.verify_attempts,
            'max_attempts': self.max_attempts,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_valid': self.is_valid()
        }
        
        if include_code:
            data['code'] = self.code
        
        return data
    
    @staticmethod
    def generate_code(length=6, code_type='numeric'):
        """生成验证码"""
        if code_type == 'numeric':
            return ''.join(random.choices(string.digits, k=length))
        elif code_type == 'alpha':
            return ''.join(random.choices(string.ascii_uppercase, k=length))
        elif code_type == 'alphanumeric':
            return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))
        else:
            return ''.join(random.choices(string.digits, k=length))
    
    @classmethod
    def create_verification_code(cls, code_type, email=None, phone=None, user_id=None,
                               send_method='email', expires_minutes=15, 
                               code_length=6, max_attempts=5):
        """创建验证码"""
        if not email and not phone:
            raise ValueError('Email or phone must be provided')
        
        # 生成验证码
        code = cls.generate_code(length=code_length)
        
        # 设置过期时间
        expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)
        
        verification_code = cls(
            code=code,
            code_type=code_type,
            user_id=user_id,
            email=email,
            phone=phone,
            send_method=send_method,
            expires_at=expires_at,
            max_attempts=max_attempts
        )
        
        return verification_code
    
    @classmethod
    def get_valid_code(cls, code_type, email=None, phone=None, user_id=None):
        """获取有效的验证码"""
        query = cls.query.filter(
            cls.code_type == code_type,
            cls.is_used == False,
            cls.is_expired == False,
            cls.expires_at > datetime.utcnow()
        )
        
        if email:
            query = query.filter_by(email=email)
        if phone:
            query = query.filter_by(phone=phone)
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        return query.order_by(cls.created_at.desc()).first()
    
    @classmethod
    def invalidate_existing_codes(cls, code_type, email=None, phone=None, user_id=None):
        """使现有验证码失效"""
        query = cls.query.filter(
            cls.code_type == code_type,
            cls.is_used == False,
            cls.is_expired == False
        )
        
        if email:
            query = query.filter_by(email=email)
        if phone:
            query = query.filter_by(phone=phone)
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        codes = query.all()
        for code in codes:
            code.mark_expired()
        
        return len(codes)
    
    @classmethod
    def verify_code(cls, code, code_type, email=None, phone=None, user_id=None, ip_address=None):
        """验证验证码"""
        verification_code = cls.get_valid_code(code_type, email, phone, user_id)
        
        if not verification_code:
            return False, 'No valid verification code found', None
        
        success, message = verification_code.verify(code, ip_address)
        return success, message, verification_code
    
    @classmethod
    def can_send_code(cls, code_type, email=None, phone=None, user_id=None, 
                     max_per_hour=5, max_per_day=20):
        """检查是否可以发送验证码"""
        # 检查1小时内发送次数
        hour_ago = datetime.utcnow() - timedelta(hours=1)
        hour_count = cls.query.filter(
            cls.code_type == code_type,
            cls.created_at >= hour_ago
        )
        
        if email:
            hour_count = hour_count.filter_by(email=email)
        if phone:
            hour_count = hour_count.filter_by(phone=phone)
        if user_id:
            hour_count = hour_count.filter_by(user_id=user_id)
        
        if hour_count.count() >= max_per_hour:
            return False, f'Too many verification codes sent in the last hour (max: {max_per_hour})'
        
        # 检查24小时内发送次数
        day_ago = datetime.utcnow() - timedelta(days=1)
        day_count = cls.query.filter(
            cls.code_type == code_type,
            cls.created_at >= day_ago
        )
        
        if email:
            day_count = day_count.filter_by(email=email)
        if phone:
            day_count = day_count.filter_by(phone=phone)
        if user_id:
            day_count = day_count.filter_by(user_id=user_id)
        
        if day_count.count() >= max_per_day:
            return False, f'Too many verification codes sent in the last 24 hours (max: {max_per_day})'
        
        return True, 'Can send verification code'
    
    @classmethod
    def cleanup_expired_codes(cls, days=7):
        """清理过期的验证码"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted_count = cls.query.filter(
            db.or_(
                cls.expires_at < datetime.utcnow(),
                cls.created_at < cutoff_date
            )
        ).delete()
        return deleted_count
    
    @classmethod
    def get_statistics(cls, days=30):
        """获取验证码统计"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        total_codes = cls.query.filter(cls.created_at >= start_date).count()
        used_codes = cls.query.filter(
            cls.created_at >= start_date,
            cls.is_used == True
        ).count()
        expired_codes = cls.query.filter(
            cls.created_at >= start_date,
            cls.is_expired == True
        ).count()
        
        # 按类型统计
        type_stats = db.session.query(
            cls.code_type,
            db.func.count(cls.id).label('count'),
            db.func.sum(db.case([(cls.is_used == True, 1)], else_=0)).label('used_count')
        ).filter(
            cls.created_at >= start_date
        ).group_by(cls.code_type).all()
        
        return {
            'total_codes': total_codes,
            'used_codes': used_codes,
            'expired_codes': expired_codes,
            'unused_codes': total_codes - used_codes - expired_codes,
            'usage_rate': (used_codes / total_codes * 100) if total_codes > 0 else 0,
            'type_statistics': [
                {
                    'type': code_type,
                    'total': count,
                    'used': used_count or 0,
                    'usage_rate': (used_count / count * 100) if count > 0 and used_count else 0
                }
                for code_type, count, used_count in type_stats
            ],
            'period_days': days
        }