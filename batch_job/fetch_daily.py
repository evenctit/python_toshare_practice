# -*- coding: utf-8 -*-
# 验证任务：使用当前 token 有权限的 daily（日线行情）接口拉取 000066 全量历史数据，
# 按接口返回字段在 PostgreSQL 的 tushare schema 下建表并把数据写入。
# 建表与写库逻辑复用 fetch_financials 中已验证的实现。
import psycopg2
import tushare as ts

from fetch_financials import DB_CONFIG, SCHEMA, TS_CODE, TUSHARE_TOKEN, save_to_db


def main():
    # 设置 tushare pro 的 token 并建立接口连接
    ts.set_token(TUSHARE_TOKEN)
    pro = ts.pro_api()

    # 建立 PostgreSQL 连接并确保 schema 存在
    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor() as cur:
        cur.execute('CREATE SCHEMA IF NOT EXISTS %s' % SCHEMA)
    conn.commit()

    # 拉取 000066 的日线行情全量历史并保存
    df = pro.daily(ts_code=TS_CODE)
    print('接口 daily 返回 %d 行, %d 列' % (df.shape[0], df.shape[1]))
    save_to_db(conn, 'daily', df)
    print('表 %s.daily 已重建并写入 %d 行' % (SCHEMA, df.shape[0]))

    conn.close()
    print('All Finished!')


if __name__ == '__main__':
    main()
