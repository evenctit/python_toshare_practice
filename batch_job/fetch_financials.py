# -*- coding: utf-8 -*-
# 批处理任务：通过 tushare 拉取股票 000066 的利润表、资产负债表、现金流量表，
# 在 PostgreSQL 的 tushare schema 下创建对应的三张表并把数据全量写入。
import pandas as pd
import psycopg2
import tushare as ts

# tushare pro 接口的 token
TUSHARE_TOKEN = '163cf77f52eeee719c54184f8e39f0bc9b219df7c1066f55f5fc6e1a'
# 股票代码，SZ 后缀表示深圳交易所
TS_CODE = '000066.SZ'

# PostgreSQL 连接配置
DB_CONFIG = dict(
    host='192.168.31.215',
    port=5432,
    dbname='postgres',
    user='postgres',
    password='westlife',
)
# 数据库 schema 名称
SCHEMA = 'tushare'

# 三张财务报表：tushare 接口名 -> 数据库表名
REPORTS = [
    ('income', 'income'),              # 利润表
    ('balancesheet', 'balancesheet'),  # 资产负债表
    ('cashflow', 'cashflow'),          # 现金流量表
]


def pandas_type_to_pg(dtype) -> str:
    # 根据 pandas 字段类型映射 PostgreSQL 字段类型
    dtype = str(dtype)
    if 'int' in dtype:
        return 'BIGINT'
    if 'float' in dtype:
        return 'DOUBLE PRECISION'
    if 'bool' in dtype:
        return 'BOOLEAN'
    if 'datetime' in dtype:
        return 'TIMESTAMP'
    return 'TEXT'


def create_table_sql(table: str, df: pd.DataFrame) -> str:
    # 根据 DataFrame 的字段生成建表语句，附带自增主键 id
    cols = ['id BIGSERIAL PRIMARY KEY']
    for col in df.columns:
        cols.append('"%s" %s' % (col, pandas_type_to_pg(df[col].dtype)))
    return 'CREATE TABLE %s.%s (%s)' % (SCHEMA, table, ', '.join(cols))


def save_to_db(conn, table: str, df: pd.DataFrame) -> None:
    # 每次运行全量重建表，保证表结构与接口返回字段一致
    with conn.cursor() as cur:
        cur.execute('DROP TABLE IF EXISTS %s.%s' % (SCHEMA, table))
        cur.execute(create_table_sql(table, df))
        # NaN 统一替换为 None，写入数据库后为 NULL
        rows = df.astype(object).where(pd.notnull(df), None).values.tolist()
        cols = ', '.join('"%s"' % c for c in df.columns)
        placeholders = ', '.join(['%s'] * len(df.columns))
        cur.executemany(
            'INSERT INTO %s.%s (%s) VALUES (%s)' % (SCHEMA, table, cols, placeholders),
            rows,
        )
    conn.commit()


def main():
    # 设置 tushare pro 的 token 并建立接口连接
    ts.set_token(TUSHARE_TOKEN)
    pro = ts.pro_api()

    # 建立 PostgreSQL 连接并确保 schema 存在
    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor() as cur:
        cur.execute('CREATE SCHEMA IF NOT EXISTS %s' % SCHEMA)
    conn.commit()

    # 依次拉取三张财务报表并保存
    for api_name, table in REPORTS:
        df = getattr(pro, api_name)(ts_code=TS_CODE)
        print('接口 %s 返回 %d 行, %d 列' % (api_name, df.shape[0], df.shape[1]))
        save_to_db(conn, table, df)
        print('表 %s.%s 已重建并写入 %d 行' % (SCHEMA, table, df.shape[0]))

    conn.close()
    print('All Finished!')


if __name__ == '__main__':
    main()
