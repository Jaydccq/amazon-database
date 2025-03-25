import psycopg2
from psycopg2 import OperationalError


def test_connection(db_name, db_user, db_password, db_host, db_port):
    """
    测试与PostgreSQL数据库的连接

    参数:
        db_name (str): 数据库名称
        db_user (str): 数据库用户名
        db_password (str): 数据库密码
        db_host (str): 数据库主机地址
        db_port (str): 数据库端口

    返回:
        bool: 连接成功返回True，失败返回False
    """
    connection = None
    try:
        # 尝试建立连接
        connection = psycopg2.connect(
            database=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        )

        # 获取游标
        cursor = connection.cursor()

        # 执行简单查询以验证连接
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()

        print(f"连接成功！PostgreSQL 数据库版本: {db_version[0]}")
        return True

    except OperationalError as e:
        print(f"连接失败: {e}")
        return False
    finally:
        # 如果连接已建立，关闭连接
        if connection:
            cursor.close()
            connection.close()
            print("数据库连接已关闭")


if __name__ == "__main__":
    # 替换以下参数为您自己的数据库连接信息
    db_name = "miniamazon"
    db_user = "miniamazon"
    db_password = "amazon"
    db_host = "localhost"  # 数据库服务器地址，本地通常为localhost
    db_port = "5432"  # PostgreSQL默认端口为5432

    test_connection(db_name, db_user, db_password, db_host, db_port)