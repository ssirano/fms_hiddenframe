import os
from datetime import timedelta

class Config:
    """기본 설정 클래스"""
    
    # Flask 기본 설정
    SECRET_KEY = 'd4ab3fc03bbf22ffeb3b3f6d6dffa8e6'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:quad8080@localhost:3308/migrated_db'
    
    # 세션 설정
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)  
    SESSION_COOKIE_SECURE = False  # HTTPS에서만 True로 설정
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # 데이터베이스 설정
    DB_HOST = os.environ.get('DB_HOST', 'localhost')
    DB_PORT = os.environ.get('DB_PORT', '3308')
    DB_NAME = os.environ.get('DB_NAME', 'migrated_db')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'quad8080')
    DB_CHARSET = os.environ.get('DB_CHARSET', 'utf8mb4')
    
    # 파일 업로드 설정
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'xlsx', 'xls', 'doc', 'docx'}
    
    # 로깅 설정
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'fms.log')
    
    # 캐시 설정
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300  # 5분
    
    # 페이징 설정
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # API 설정
    API_TIMEOUT = 30  # 30초
    
    @staticmethod
    def init_app(app):
        """애플리케이션 초기화"""
        pass

class DevelopmentConfig(Config):
    """개발환경 설정"""
    DEBUG = True
    TESTING = False
    
    # 개발환경에서는 더 자세한 로깅
    LOG_LEVEL = 'DEBUG'
    
    # 세션 쿠키 보안 설정 (개발환경)
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    """운영환경 설정"""
    DEBUG = False
    TESTING = False
    
    # 운영환경 보안 설정
    SESSION_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = 'https'
    
    def __init__(self):
        # 운영환경에서만 SECRET_KEY 환경변수 체크
        env_secret_key = os.environ.get('SECRET_KEY')
        if env_secret_key:
            self.SECRET_KEY = env_secret_key
        # 환경변수가 없어도 기본값 사용 (개발용)
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # 운영환경 실제 배포 시에만 SECRET_KEY 체크 (선택사항)
        # if not os.environ.get('SECRET_KEY'):
        #     print("⚠️  운영환경에서는 SECRET_KEY 환경변수 설정을 권장합니다.")
        
        # 운영환경 로깅 설정
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not app.debug:
            file_handler = RotatingFileHandler(
                cls.LOG_FILE, 
                maxBytes=10240000, 
                backupCount=10
            )
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('FMS 애플리케이션 시작')

class TestingConfig(Config):
    """테스트환경 설정"""
    TESTING = True
    DEBUG = True
    
    # 테스트용 인메모리 데이터베이스
    DB_NAME = 'test_fms_db'
    
    # 빠른 테스트를 위한 설정
    WTF_CSRF_ENABLED = False
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=5)

# 환경별 설정 매핑
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """현재 환경에 맞는 설정 반환"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, DevelopmentConfig)