"""
数据库迁移脚本：为 articles 表添加 category_id 字段
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/eleven_blog_tuner")

def migrate():
    print("开始数据库迁移...")

    # 连接到数据库
    conn = psycopg2.connect(DATABASE_URL)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    try:
        # 检查字段是否已存在
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'articles' AND column_name = 'category_id'
        """)
        exists = cursor.fetchone()

        if exists:
            print("字段 category_id 已存在，跳过迁移")
        else:
            # 添加 category_id 字段
            cursor.execute("""
                ALTER TABLE articles
                ADD COLUMN category_id UUID REFERENCES note_categories(id) ON DELETE SET NULL
            """)
            print("成功添加 category_id 字段到 articles 表")

        # 检查 note_categories 表的 type 字段
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'note_categories' AND column_name = 'type'
        """)
        type_exists = cursor.fetchone()

        if type_exists:
            print("字段 type 已存在于 note_categories 表，跳过迁移")
        else:
            # 添加 type 字段
            cursor.execute("""
                ALTER TABLE note_categories
                ADD COLUMN type VARCHAR(20) DEFAULT 'all'
            """)
            print("成功添加 type 字段到 note_categories 表")

        print("数据库迁移完成！")

    except Exception as e:
        print(f"迁移失败: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    migrate()
