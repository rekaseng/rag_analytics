import os
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import timedelta
from dotenv import load_dotenv

# Load .env
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'), override=True)

# Get DATABASE_URL with fallback
#DATABASE_URL = os.getenv('POSTGRES_URL_RAG')
DATABASE_URL = "postgresql://postgres:postgres@127.0.0.1:5433/wise_rag"


def get_engine():
    if not DATABASE_URL:
        raise ValueError("错误: 未找到 POSTGRES_URL_RAG 环境变量。请检查 .env 文件。")
    return create_engine(DATABASE_URL)


def get_week_range_for_date(input_date):
    """根据传入的日期计算该周的周一和周日"""
    monday = input_date - timedelta(days=input_date.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def generate_table_name(input_date):
    """生成表名：yymmdd_yymmddlog"""
    monday, sunday = get_week_range_for_date(input_date)
    mon_str = monday.strftime('%y%m%d')
    sun_str = sunday.strftime('%y%m%d')
    table_name = f"{mon_str}_{sun_str}log"
    return table_name, monday, sunday


def fetch_logs(table_name, schema=None):
    """读取指定表的所有数据，并打印详细错误"""
    try:
        engine = get_engine()
        
        # Try multiple query formats
        queries_to_try = []
        if schema:
            queries_to_try.append(f'"{schema}"."{table_name}"')
            queries_to_try.append(f'{schema}.{table_name}')
        queries_to_try.append(f'"{table_name}"')
        queries_to_try.append(f'{table_name}')
        
        last_error = None
        for full_table_name in queries_to_try:
            try:
                query = text(f'SELECT * FROM {full_table_name}')
                print(f"🔍 Trying: {full_table_name}")
                
                with engine.connect() as conn:
                    df = pd.read_sql(query, conn)
                    print(f"✅ Success! Fetched {len(df)} rows from {full_table_name}")
                    return df
            except Exception as e:
                last_error = e
                print(f"   ❌ Failed: {type(e).__name__}")
                continue
        
        # If all attempts failed, raise the last error
        raise last_error

    except Exception as e:
        print("\n" + "=" * 50)
        print(f"❌ 数据库查询失败!")
        print(f"目标表名: {table_name}")
        print(f"DATABASE_URL: {DATABASE_URL[:30]}..." if DATABASE_URL else "未设置")
        print(f"错误类型: {type(e).__name__}")
        print(f"具体错误信息: {e}")
        print("\n💡 建议:")
        print("   1. 运行 'python find_tables.py' 检查连接")
        print("   2. 确认表是否存在于正确的 schema 中")
        print("   3. 检查 .env 文件中的 POSTGRES_URL_RAG")
        print("=" * 50 + "\n")
        return None
