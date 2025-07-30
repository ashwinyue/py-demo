from datetime import datetime, timedelta
from ..extensions import db


class LoginLog(db.Model):
    """登录日志模型"""
    __tablename__ = 'login_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # 可为空，支持记录失败的登录尝试
    username = db.Column(db.String(80), nullable=True)  # 记录尝试登录的用户名
    email = db.Column(db.String(120), nullable=True)  # 记录尝试登录的邮箱
    
    # 登录信息
    login_type = db.Column(db.String(20), nullable=False, default='web')  # web, mobile, api
    login_method = db.Column(db.String(20), nullable=False, default='password')  # password, oauth, sms
    
    # 登录结果
    is_successful = db.Column(db.Boolean, nullable=False, default=False)
    failure_reason = db.Column(db.String(100), nullable=True)  # 失败原因
    
    # 网络信息
    ip_address = db.Column(db.String(45), nullable=True)  # 支持IPv6
    user_agent = db.Column(db.Text, nullable=True)
    device_info = db.Column(db.JSON, nullable=True)  # 设备信息
    location_info = db.Column(db.JSON, nullable=True)  # 地理位置信息
    
    # 安全信息
    is_suspicious = db.Column(db.Boolean, default=False, nullable=False)  # 是否可疑登录
    risk_score = db.Column(db.Integer, default=0, nullable=False)  # 风险评分 0-100
    security_flags = db.Column(db.JSON, nullable=True)  # 安全标记
    
    # 会话信息
    session_id = db.Column(db.String(128), nullable=True)
    token_id = db.Column(db.String(128), nullable=True)  # JWT token ID
    logout_time = db.Column(db.DateTime, nullable=True)
    session_duration = db.Column(db.Integer, nullable=True)  # 会话持续时间（秒）
    
    # 时间字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # 关联关系
    user = db.relationship('User', backref='login_logs')
    
    # 索引
    __table_args__ = (
        db.Index('idx_login_logs_user_created', 'user_id', 'created_at'),
        db.Index('idx_login_logs_ip_created', 'ip_address', 'created_at'),
        db.Index('idx_login_logs_suspicious', 'is_suspicious', 'created_at'),
    )
    
    def __repr__(self):
        return f'<LoginLog user_id={self.user_id} ip={self.ip_address} success={self.is_successful}>'
    
    def calculate_session_duration(self):
        """计算会话持续时间"""
        if self.logout_time and self.created_at:
            duration = (self.logout_time - self.created_at).total_seconds()
            self.session_duration = int(duration)
            return self.session_duration
        return None
    
    def mark_logout(self, logout_time=None):
        """标记登出"""
        self.logout_time = logout_time or datetime.utcnow()
        self.calculate_session_duration()
    
    def is_recent(self, minutes=30):
        """检查是否为最近的登录"""
        if not self.created_at:
            return False
        return datetime.utcnow() - self.created_at <= timedelta(minutes=minutes)
    
    def get_device_type(self):
        """获取设备类型"""
        if not self.user_agent:
            return 'unknown'
        
        user_agent = self.user_agent.lower()
        if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
            return 'mobile'
        elif 'tablet' in user_agent or 'ipad' in user_agent:
            return 'tablet'
        else:
            return 'desktop'
    
    def get_browser_info(self):
        """获取浏览器信息"""
        if not self.user_agent:
            return {'browser': 'unknown', 'version': 'unknown'}
        
        user_agent = self.user_agent.lower()
        
        # 简单的浏览器检测
        if 'chrome' in user_agent:
            browser = 'Chrome'
        elif 'firefox' in user_agent:
            browser = 'Firefox'
        elif 'safari' in user_agent and 'chrome' not in user_agent:
            browser = 'Safari'
        elif 'edge' in user_agent:
            browser = 'Edge'
        elif 'opera' in user_agent:
            browser = 'Opera'
        else:
            browser = 'Unknown'
        
        return {'browser': browser, 'user_agent': self.user_agent}
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'login_type': self.login_type,
            'login_method': self.login_method,
            'is_successful': self.is_successful,
            'failure_reason': self.failure_reason,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'device_info': self.device_info,
            'location_info': self.location_info,
            'is_suspicious': self.is_suspicious,
            'risk_score': self.risk_score,
            'security_flags': self.security_flags,
            'session_id': self.session_id,
            'token_id': self.token_id,
            'logout_time': self.logout_time.isoformat() if self.logout_time else None,
            'session_duration': self.session_duration,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'device_type': self.get_device_type(),
            'browser_info': self.get_browser_info()
        }
    
    @classmethod
    def create_login_log(cls, user_id=None, username=None, email=None, 
                        is_successful=False, failure_reason=None,
                        ip_address=None, user_agent=None, 
                        login_type='web', login_method='password',
                        session_id=None, token_id=None,
                        device_info=None, location_info=None):
        """创建登录日志"""
        log = cls(
            user_id=user_id,
            username=username,
            email=email,
            is_successful=is_successful,
            failure_reason=failure_reason,
            ip_address=ip_address,
            user_agent=user_agent,
            login_type=login_type,
            login_method=login_method,
            session_id=session_id,
            token_id=token_id,
            device_info=device_info,
            location_info=location_info
        )
        
        # 计算风险评分
        log.risk_score = log._calculate_risk_score()
        log.is_suspicious = log.risk_score > 70
        
        return log
    
    def _calculate_risk_score(self):
        """计算风险评分"""
        score = 0
        
        # 登录失败增加风险
        if not self.is_successful:
            score += 30
        
        # 检查是否为新IP
        if self.ip_address and self.user_id:
            recent_ips = LoginLog.query.filter(
                LoginLog.user_id == self.user_id,
                LoginLog.ip_address == self.ip_address,
                LoginLog.is_successful == True,
                LoginLog.created_at > datetime.utcnow() - timedelta(days=30)
            ).count()
            
            if recent_ips == 0:
                score += 40  # 新IP地址
        
        # 检查短时间内多次失败尝试
        if self.ip_address:
            recent_failures = LoginLog.query.filter(
                LoginLog.ip_address == self.ip_address,
                LoginLog.is_successful == False,
                LoginLog.created_at > datetime.utcnow() - timedelta(hours=1)
            ).count()
            
            if recent_failures > 3:
                score += 50
        
        return min(score, 100)
    
    @classmethod
    def get_user_login_history(cls, user_id, limit=50, successful_only=False):
        """获取用户登录历史"""
        query = cls.query.filter_by(user_id=user_id)
        if successful_only:
            query = query.filter_by(is_successful=True)
        return query.order_by(cls.created_at.desc()).limit(limit).all()
    
    @classmethod
    def get_failed_login_attempts(cls, ip_address=None, username=None, hours=24):
        """获取失败的登录尝试"""
        query = cls.query.filter(
            cls.is_successful == False,
            cls.created_at > datetime.utcnow() - timedelta(hours=hours)
        )
        
        if ip_address:
            query = query.filter_by(ip_address=ip_address)
        if username:
            query = query.filter_by(username=username)
        
        return query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_suspicious_logins(cls, hours=24):
        """获取可疑登录"""
        return cls.query.filter(
            cls.is_suspicious == True,
            cls.created_at > datetime.utcnow() - timedelta(hours=hours)
        ).order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_active_sessions(cls, user_id=None):
        """获取活跃会话"""
        query = cls.query.filter(
            cls.is_successful == True,
            cls.logout_time.is_(None)
        )
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        return query.order_by(cls.created_at.desc()).all()
    
    @classmethod
    def get_login_statistics(cls, user_id=None, days=30):
        """获取登录统计"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        query = cls.query.filter(cls.created_at >= start_date)
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        total_attempts = query.count()
        successful_logins = query.filter_by(is_successful=True).count()
        failed_attempts = total_attempts - successful_logins
        suspicious_logins = query.filter_by(is_suspicious=True).count()
        
        # 获取最常用的IP地址
        ip_stats = db.session.query(
            cls.ip_address,
            db.func.count(cls.id).label('count')
        ).filter(
            cls.created_at >= start_date,
            cls.is_successful == True
        )
        
        if user_id:
            ip_stats = ip_stats.filter_by(user_id=user_id)
        
        ip_stats = ip_stats.group_by(cls.ip_address).order_by(
            db.func.count(cls.id).desc()
        ).limit(5).all()
        
        return {
            'total_attempts': total_attempts,
            'successful_logins': successful_logins,
            'failed_attempts': failed_attempts,
            'suspicious_logins': suspicious_logins,
            'success_rate': (successful_logins / total_attempts * 100) if total_attempts > 0 else 0,
            'top_ips': [{'ip': ip, 'count': count} for ip, count in ip_stats],
            'period_days': days
        }
    
    @classmethod
    def cleanup_old_logs(cls, days=90):
        """清理旧的登录日志"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted_count = cls.query.filter(cls.created_at < cutoff_date).delete()
        return deleted_count