# -*- coding: utf-8 -*-
# 验证任务：使用当前 token 有权限的 daily（日线行情）接口拉取配置的股票列表全量历史数据，
# 按接口返回字段在 PostgreSQL 的 tushare schema 下建表并把数据写入。
# 建表与写库逻辑、配置加载复用 fetch_financials 中已验证的实现。
import pandas as pd
import psycopg2
import tushare as ts

from fetch_financials import DB_CONFIG, SCHEMA, TS_CODES, TUSHARE_TOKEN, save_to_db


def main():
    # 设置 tushare pro 的 token 并建立接口连接
    ts.set_token(TUSHARE_TOKEN)
    pro = ts.pro_api()

    # 建立 PostgreSQL 连接并确保 schema 存在
    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor() as cur:
        cur.execute('CREATE SCHEMA IF NOT EXISTS %s' % SCHEMA)
    conn.commit()

    # 按配置的股票代码列表逐个拉取日线行情并合并
    dfs = []
    for ts_code in TS_CODES:
        df = pro.daily(ts_code=ts_code)
        print('接口 daily 股票 %s 返回 %d 行, %d 列' % (ts_code, df.shape[0], df.shape[1]))
        dfs.append(df)
    all_df = pd.concat(dfs, ignore_index=True)

    # 合并后一次性建表写入
    save_to_db(conn, 'daily', all_df)
    print('表 %s.daily 已重建并写入 %d 行' % (SCHEMA, all_df.shape[0]))

    conn.close()
    print('All Finished!')


if __name__ == '__main__':
    main()
