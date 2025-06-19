from sqlalchemy import create_engine, pool
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import os

# 환경변수에서 데이터베이스 설정 가져오기 (기본값 포함)
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '3308')
DB_NAME = os.environ.get('DB_NAME', 'migrated_db')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'quad8080')
DB_CHARSET = os.environ.get('DB_CHARSET', 'utf8mb4')

# 데이터베이스 URL 구성
DATABASE_URL = 'mysql+pymysql://root:quad8080@localhost:3308/migrated_db'

# SQLAlchemy 엔진 생성
engine = create_engine(
    DATABASE_URL,
    poolclass=pool.QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False  # 운영환경에서는 False로 설정
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_session():
    """데이터베이스 세션 컨텍스트 매니저"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"데이터베이스 세션 오류: {str(e)}")
        raise
    finally:
        session.close()

def get_db_session():
    """세션 의존성 주입용 함수"""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

def test_connection():
    """데이터베이스 연결 테스트"""
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1 as test")
            print("✅ 데이터베이스 연결 성공")
            return True
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {str(e)}")
        return False

def init_database():
    """데이터베이스 초기화 (필요시 테이블 생성 등)"""
    try:
        # 여기에 필요한 초기화 로직 추가
        # 예: 테이블 생성, 기본 데이터 삽입 등
        print("데이터베이스 초기화 완료")
        return True
    except Exception as e:
        print(f"데이터베이스 초기화 실패: {str(e)}")
        return False

if __name__ == "__main__":
    # 직접 실행시 연결 테스트
    test_connection()