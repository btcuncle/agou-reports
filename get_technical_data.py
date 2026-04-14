#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
技术分析日报生成脚本 - 2026年4月11日
获取142只A股的技术指标数据
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings('ignore')

# 股票池 - 142只A股（排除港股和未上市）
STOCKS = [
    # 核心标的
    ("中际旭创", "300308"),
    ("天孚通信", "300394"),
    # 重要标的
    ("新易盛", "300502"),
    ("罗博特科", "300757"),
    ("英维克", "002837"),
    ("长芯博创", "300548"),
    ("申菱环境", "301018"),
    ("工业富联", "601138"),
    ("剑桥科技", "603083"),
    ("芯源微", "688037"),
    ("拓荆科技", "688072"),
    ("炬光科技", "688167"),
    ("寒武纪", "688256"),
    ("仕佳光子", "688313"),
    ("芯原股份", "688521"),
    ("优利德", "688628"),
    ("芯碁微装", "688630"),
    # 补充标的
    ("德明利", "001309"),
    ("航天电器", "002025"),
    ("通富微电", "002156"),
    ("福晶科技", "002222"),
    ("光迅科技", "002281"),
    ("杰瑞股份", "002353"),
    ("中恒电气", "002364"),
    ("北方华创", "002371"),
    ("东山精密", "002384"),
    ("云南锗业", "002428"),
    ("沪电股份", "002463"),
    ("鹏鼎控股", "002938"),
    ("华盛昌", "002980"),
    ("胜宏科技", "300476"),
    ("精测电子", "300567"),
    ("太辰光", "300570"),
    ("光库科技", "300620"),
    ("中国巨石", "600176"),
    ("生益科技", "600183"),
    ("中国动力", "600482"),
    ("长电科技", "600584"),
    ("东方电气", "600875"),
    ("长飞光纤", "601869"),
    ("宏和科技", "603256"),
    ("应流股份", "603308"),
    ("联德股份", "605060"),
    ("杰普特", "688025"),
    ("海光信息", "688041"),
    ("长光华芯", "688048"),
    ("腾景科技", "688195"),
    ("德科立", "688205"),
    ("普源精电", "688337"),
    ("骄成超声", "688392"),
    ("源杰科技", "688498"),
    ("广钢气体", "688548"),
    ("金盘科技", "688676"),
    ("特发信息", "000070"),
    ("潍柴动力", "000338"),
    ("万泽股份", "000534"),
    ("华工科技", "000988"),
    ("汇绿生态", "001267"),
    ("中材科技", "002080"),
    ("利欧股份", "002131"),
    ("川润股份", "002272"),
    ("信立泰", "002294"),
    ("科华数据", "002335"),
    ("科士达", "002518"),
    ("飞龙股份", "002536"),
    ("豪迈科技", "002595"),
    ("海思科", "002653"),
    ("世嘉科技", "002796"),
    ("麦格米特", "002851"),
    ("深南电路", "002916"),
    ("兴瑞科技", "002937"),
    ("博杰股份", "002975"),
    ("鼎龙股份", "300054"),
    ("南方泵业", "300145"),
    ("阳光电源", "300274"),
    ("光环新网", "300383"),
    ("菲利华", "300395"),
    ("高澜股份", "300499"),
    ("长川科技", "300604"),
    ("佰维存储", "300667"),
    ("科创新源", "300731"),
    ("宁德时代", "300750"),
    ("康龙化成", "300759"),
    ("金现代", "300830"),
    ("协创数据", "300857"),
    ("同飞股份", "300990"),
    ("联特科技", "301205"),
    ("鸿日达", "301220"),
    ("蘅东光", "301252"),
    ("斯菱股份", "301511"),
    ("国际复材", "301526"),
    ("恒瑞医药", "600276"),
    ("泰豪科技", "600590"),
    ("东阳光", "600673"),
    ("博威合金", "601137"),
    ("金海通", "603061"),
    ("禾望电气", "603063"),
    ("药明康德", "603259"),
    ("华懋科技", "603306"),
    ("大位科技", "603316"),
    ("科森科技", "603626"),
    ("大元泵业", "603757"),
    ("数据港", "603881"),
    ("长源东谷", "603950"),
    ("兆易创新", "603986"),
    ("新炬网络", "605398"),
    ("中微公司", "688012"),
    ("毕得医药", "688073"),
    ("鼎阳科技", "688112"),
    ("华海清科", "688120"),
    ("皓元医药", "688131"),
    ("莱特光电", "688150"),
    ("优刻得", "688158"),
    ("君实生物", "688180"),
    ("生益电子", "688183"),
    ("百济神州", "688235"),
    ("卓易信息", "688258"),
    ("泽璟制药", "688266"),
    ("华丰科技", "688312"),
    ("奥比中光", "688322"),
    ("荣昌生物", "688331"),
    ("三生国健", "688336"),
    ("益方生物", "688382"),
    ("嘉元科技", "688388"),
    ("凌云光", "688400"),
    ("汇成股份", "688403"),
    ("富创精密", "688409"),
    ("智翔金泰", "688443"),
    ("百利天恒", "688506"),
    ("航亚科技", "688510"),
    ("奥特维", "688516"),
    ("京仪装备", "688652"),
]

# 板块分类
SECTORS = {
    "光模块/光通信": ["中际旭创", "天孚通信", "新易盛", "剑桥科技", "光迅科技", "太辰光", "光库科技", "长飞光纤", "仕佳光子", "源杰科技", "联特科技", "腾景科技", "德科立", "杰普特", "长光华芯"],
    "数据中心/AIDC": ["英维克", "申菱环境", "工业富联", "数据港", "光环新网", "同飞股份", "高澜股份", "科华数据", "科士达", "麦格米特", "大位科技", "优刻得"],
    "PCB/CCL": ["沪电股份", "深南电路", "鹏鼎控股", "胜宏科技", "东山精密", "生益科技", "生益电子", "宏和科技", "金海通", "博杰股份"],
    "存储": ["德明利", "佰维存储", "兆易创新", "协创数据", "精测电子"],
    "半导体设备": ["北方华创", "芯源微", "拓荆科技", "长川科技", "华海清科", "中微公司", "芯碁微装", "京仪装备", "骄成超声", "富创精密", "汇成股份"],
    "AI芯片": ["寒武纪", "海光信息", "芯原股份", "龙芯中科", "景嘉微"],
    "机器人/自动化": ["罗博特科", "机器人", "埃斯顿", "汇川技术", "绿的谐波"],
    "储能/锂电": ["宁德时代", "阳光电源", "金盘科技", "禾望电气", "科创新源", "鼎龙股份"],
    "光伏": ["奥特维", "金盘科技"],
    "风电": ["东方电气", "中国动力", "应流股份", "豪迈科技", "通裕重工"],
    "燃机/电力": ["东方电气", "中国动力", "应流股份", "豪迈科技", "联德股份", "长源东谷", "飞龙股份", "川润股份", "泰豪科技"],
    "材料/化工": ["中国巨石", "云南锗业", "福晶科技", "菲利华", "中材科技", "国际复材", "华懋科技", "博威合金", "嘉元科技", "广钢气体"],
    "仪器仪表": ["优利德", "华盛昌", "普源精电", "鼎阳科技", "奥比中光", "凌云光"],
    "医药": ["恒瑞医药", "药明康德", "百济神州", "信达生物", "康方生物", "荣昌生物", "君实生物", "泽璟制药", "三生国健", "益方生物", "智翔金泰", "百利天恒", "信立泰", "海思科", "康龙化成", "皓元医药", "毕得医药", "药明生物", "药明合联", "科伦博泰", "康诺亚", "映恩生物", "三生制药", "石药集团"],
    "其他": []
}

def get_stock_data(stock_code, stock_name):
    """获取单只股票历史数据"""
    try:
        # 根据股票代码判断交易所
        if stock_code.startswith('6'):
            symbol = f"sh{stock_code}"
        elif stock_code.startswith('0') or stock_code.startswith('3'):
            symbol = f"sz{stock_code}"
        elif stock_code.startswith('68'):
            symbol = f"sh{stock_code}"
        else:
            symbol = f"sz{stock_code}"
        
        # 获取历史数据
        df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", 
                                start_date="20260101", end_date="20260411",
                                adjust="qfq")
        
        if df is None or len(df) < 30:
            return None
        
        df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount', 
                      'amplitude', 'pct_change', 'change_amount', 'turnover']
        return df
    except Exception as e:
        print(f"获取 {stock_name}({stock_code}) 数据失败: {e}")
        return None

def calculate_ma(prices, period):
    """计算移动平均线"""
    return prices.rolling(window=period).mean()

def calculate_rsi(prices, period=14):
    """计算RSI指标"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """计算MACD指标"""
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False).mean()
    macd = 2 * (dif - dea)
    return dif, dea, macd

def calculate_obv(close, volume):
    """计算OBV指标"""
    obv = [0]
    for i in range(1, len(close)):
        if close.iloc[i] > close.iloc[i-1]:
            obv.append(obv[-1] + volume.iloc[i])
        elif close.iloc[i] < close.iloc[i-1]:
            obv.append(obv[-1] - volume.iloc[i])
        else:
            obv.append(obv[-1])
    return pd.Series(obv, index=close.index)

def analyze_stock(stock_name, stock_code):
    """分析单只股票技术指标"""
    df = get_stock_data(stock_code, stock_name)
    if df is None:
        return None
    
    # 获取最新数据
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    
    close = df['close']
    volume = df['volume']
    
    # 计算指标
    ma20 = calculate_ma(close, 20)
    ma60 = calculate_ma(close, 60)
    rsi = calculate_rsi(close, 14)
    dif, dea, macd = calculate_macd(close)
    obv = calculate_obv(close, volume)
    
    # 最新指标值
    latest_close = latest['close']
    latest_ma20 = ma20.iloc[-1]
    latest_ma60 = ma60.iloc[-1]
    latest_rsi = rsi.iloc[-1]
    latest_dif = dif.iloc[-1]
    latest_dea = dea.iloc[-1]
    latest_macd = macd.iloc[-1]
    latest_obv = obv.iloc[-1]
    prev_obv = obv.iloc[-2]
    
    # MACD信号
    prev_dif = dif.iloc[-2]
    prev_dea = dea.iloc[-2]
    macd_signal = "正常"
    if prev_dif <= prev_dea and latest_dif > latest_dea:
        macd_signal = "金叉"
    elif prev_dif >= prev_dea and latest_dif < latest_dea:
        macd_signal = "死叉"
    elif latest_dif > latest_dea:
        macd_signal = "多头"
    elif latest_dif < latest_dea:
        macd_signal = "空头"
    
    # OBV方向
    obv_direction = "↑" if latest_obv > prev_obv else "↓"
    
    # 趋势判断
    if latest_ma20 > latest_ma60 * 1.02:
        trend = "上升"
    elif latest_ma20 < latest_ma60 * 0.98:
        trend = "下降"
    else:
        trend = "震荡"
    
    # 成交量判断
    avg_volume = volume.tail(20).mean()
    latest_volume = latest['volume']
    if latest_volume > avg_volume * 1.5:
        volume_status = "放量"
    elif latest_volume < avg_volume * 0.7:
        volume_status = "缩量"
    else:
        volume_status = "正常"
    
    # 评分系统
    score = 0
    # MACD (+1)
    if macd_signal in ["金叉", "多头"]:
        score += 1
    # OBV (+1)
    if obv_direction == "↑":
        score += 1
    # RSI (+1) - 未超买超卖
    if 30 <= latest_rsi <= 70:
        score += 1
    # 趋势 (+1)
    if trend == "上升":
        score += 1
    # 成交量 (+1)
    if volume_status in ["放量", "正常"]:
        score += 1
    
    # 星级
    stars = "⭐" * score if score > 0 else "⭐"
    
    return {
        "name": stock_name,
        "code": stock_code,
        "close": round(latest_close, 2),
        "change": round(latest['pct_change'], 2),
        "macd": macd_signal,
        "obv": obv_direction,
        "rsi": round(latest_rsi, 1) if not pd.isna(latest_rsi) else 50,
        "trend": trend,
        "volume": volume_status,
        "score": score,
        "stars": stars,
        "ma20": round(latest_ma20, 2) if not pd.isna(latest_ma20) else latest_close,
        "ma60": round(latest_ma60, 2) if not pd.isna(latest_ma60) else latest_close,
    }

def get_sector_for_stock(stock_name):
    """获取股票所属板块"""
    for sector, stocks in SECTORS.items():
        if stock_name in stocks:
            return sector
    return "其他"

def main():
    print(f"开始获取 {len(STOCKS)} 只股票的技术数据...")
    print(f"分析日期: 2026-04-11")
    print("=" * 60)
    
    results = []
    failed_stocks = []
    
    for i, (name, code) in enumerate(STOCKS):
        print(f"[{i+1}/{len(STOCKS)}] 分析 {name}({code})...", end=" ")
        try:
            result = analyze_stock(name, code)
            if result:
                result['sector'] = get_sector_for_stock(name)
                results.append(result)
                print(f"✓ 星级: {result['stars']}")
            else:
                failed_stocks.append((name, code))
                print(f"✗ 数据获取失败")
        except Exception as e:
            failed_stocks.append((name, code))
            print(f"✗ 错误: {e}")
        
        time.sleep(0.3)  # 避免请求过快
    
    print("\n" + "=" * 60)
    print(f"成功: {len(results)} 只, 失败: {len(failed_stocks)} 只")
    
    # 保存结果
    df = pd.DataFrame(results)
    output_file = "/Users/forsafe/.openclaw/workspace-agou/reports/technical_data_2026-04-11.csv"
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"数据已保存到: {output_file}")
    
    # 统计
    print("\n星级分布:")
    for score in range(5, 0, -1):
        count = len([r for r in results if r['score'] == score])
        stars = "⭐" * score
        print(f"  {stars}: {count} 只")
    
    # 买入信号 (4-5星)
    buy_signals = [r for r in results if r['score'] >= 4]
    print(f"\n买入信号 (4-5星): {len(buy_signals)} 只")
    for r in buy_signals[:10]:
        print(f"  {r['name']}({r['code']}): {r['stars']} {r['change']}%")
    
    # 卖出信号 (1星)
    sell_signals = [r for r in results if r['score'] == 1]
    print(f"\n卖出信号 (1星): {len(sell_signals)} 只")
    for r in sell_signals[:10]:
        print(f"  {r['name']}({r['code']}): {r['stars']} {r['change']}%")

if __name__ == "__main__":
    main()
