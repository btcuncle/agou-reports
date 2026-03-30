import tushare as ts
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 初始化Tushare
pro = ts.pro_api()

# 获取今日日期
today = datetime.now()
end_date = today.strftime('%Y%m%d')
start_date = (today - timedelta(days=90)).strftime('%Y%m%d')

print(f"数据获取区间: {start_date} - {end_date}")

# 007研报股票池
stocks = {
    '潍柴动力': '000338.SZ',
    '海星股份': '603115.SH',
    '腾景科技': '688195.SH',
    '德科立': '688205.SH',
    '海亮股份': '002203.SZ',
    '诺德股份': '600110.SH',
    '铜冠铜箔': '301217.SZ',
    '德福科技': '301511.SZ',
    '嘉元科技': '688388.SH',
    '中一科技': '301150.SZ',
    '江南新材': '603124.SH',
    '宁德时代': '300750.SZ',
    '天赐材料': '002709.SZ',
    '恩捷股份': '002812.SZ',
    '光迅科技': '002281.SZ',
}

def calculate_ma(prices, window):
    """计算移动平均"""
    return prices.rolling(window=window).mean()

def calculate_macd(prices, fast=12, slow=26, signal=9):
    """计算MACD"""
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    dif = ema_fast - ema_slow
    dea = dif.ewm(span=signal, adjust=False).mean()
    macd = 2 * (dif - dea)
    return dif, dea, macd

def calculate_rsi(prices, period=14):
    """计算RSI"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_obv(close, volume):
    """计算OBV"""
    obv = [0]
    for i in range(1, len(close)):
        if close.iloc[i] > close.iloc[i-1]:
            obv.append(obv[-1] + volume.iloc[i])
        elif close.iloc[i] < close.iloc[i-1]:
            obv.append(obv[-1] - volume.iloc[i])
        else:
            obv.append(obv[-1])
    return pd.Series(obv, index=close.index)

def get_stock_data(ts_code, start_date, end_date):
    """获取股票日线数据"""
    try:
        df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        if df is None or len(df) < 20:
            return None
        df = df.sort_values('trade_date')
        return df
    except Exception as e:
        print(f"获取{ts_code}数据失败: {e}")
        return None

def analyze_stock(name, ts_code, start_date, end_date):
    """分析单只股票"""
    df = get_stock_data(ts_code, start_date, end_date)
    if df is None or len(df) < 26:
        return None
    
    close = df['close']
    volume = df['vol']
    
    # 计算指标
    ma20 = calculate_ma(close, 20).iloc[-1]
    ma60 = calculate_ma(close, 60).iloc[-1] if len(close) >= 60 else ma20
    dif, dea, macd = calculate_macd(close)
    rsi = calculate_rsi(close)
    obv = calculate_obv(close, volume)
    
    # 最新值
    latest_close = close.iloc[-1]
    prev_close = close.iloc[-2] if len(close) > 1 else latest_close
    change_pct = (latest_close - prev_close) / prev_close * 100
    
    # MACD信号
    macd_signal = "金叉" if dif.iloc[-1] > dea.iloc[-1] and dif.iloc[-2] <= dea.iloc[-2] else \
                  "死叉" if dif.iloc[-1] < dea.iloc[-1] and dif.iloc[-2] >= dea.iloc[-2] else \
                  "多头" if dif.iloc[-1] > dea.iloc[-1] else "空头"
    
    # OBV趋势
    obv_trend = "上升" if obv.iloc[-1] > obv.iloc[-5] else "下降"
    obv_change = obv.iloc[-1] - obv.iloc[-5]
    
    # RSI
    rsi_val = rsi.iloc[-1]
    rsi_status = "超买" if rsi_val > 70 else "超卖" if rsi_val < 30 else "正常"
    
    # 趋势判断
    trend = "上升" if ma20 > ma60 else "下降" if ma20 < ma60 * 0.98 else "震荡"
    
    # 成交量分析
    vol_today = volume.iloc[-1]
    vol_avg5 = volume.iloc[-5:].mean()
    vol_status = "放量" if vol_today > vol_avg5 * 1.2 else "缩量" if vol_today < vol_avg5 * 0.8 else "正常"
    
    # 评分
    score = 0
    score += 1 if macd_signal in ["金叉", "多头"] else 0
    score += 1 if obv_trend == "上升" else 0
    score += 1 if 30 <= rsi_val <= 70 else 0
    score += 1 if trend == "上升" else 0
    score += 1 if vol_status in ["放量", "正常"] else 0
    
    stars = "⭐" * score + "☆" * (5 - score)
    
    # 交易信号
    if score >= 4:
        signal = "买入"
    elif score <= 2 and trend == "下降":
        signal = "卖出"
    else:
        signal = "观察"
    
    return {
        'name': name,
        'code': ts_code.split('.')[0],
        'close': round(latest_close, 2),
        'change_pct': round(change_pct, 2),
        'macd': f"{macd_signal} (DIF:{dif.iloc[-1]:.2f}, DEA:{dea.iloc[-1]:.2f})",
        'obv': f"{obv_trend} (5日变化:{obv_change:.0f})",
        'rsi': f"{rsi_val:.1f} ({rsi_status})",
        'trend': trend,
        'volume': vol_status,
        'score': score,
        'stars': stars,
        'signal': signal,
        'ma20': round(ma20, 2),
        'ma60': round(ma60, 2)
    }

# 获取指数数据
print("\n=== 市场指数 ===")
indices = {
    '上证指数': '000001.SH',
    '深证成指': '399001.SZ',
    '创业板指': '399006.SZ',
    '科创50': '000688.SH'
}

for name, code in indices.items():
    try:
        df = pro.index_daily(ts_code=code, start_date=start_date, end_date=end_date)
        if df is not None and len(df) > 0:
            df = df.sort_values('trade_date')
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            change_pct = (latest['close'] - prev['close']) / prev['close'] * 100
            print(f"{name}: {latest['close']:.2f} ({change_pct:+.2f}%)")
    except Exception as e:
        print(f"{name}: 获取失败 - {e}")

# 分析股票池
print("\n=== 股票分析 ===")
results = []
for name, code in stocks.items():
    result = analyze_stock(name, code, start_date, end_date)
    if result:
        results.append(result)
        print(f"{name}({result['code']}): {result['stars']} {result['signal']}")

# 按评分排序
results_sorted = sorted(results, key=lambda x: x['score'], reverse=True)

print("\n=== 详细结果 ===")
for r in results_sorted:
    print(f"\n【{r['name']} {r['code']}】")
    print(f"  收盘价: {r['close']} ({r['change_pct']:+.2f}%)")
    print(f"  MACD: {r['macd']}")
    print(f"  OBV: {r['obv']}")
    print(f"  RSI: {r['rsi']}")
    print(f"  趋势: {r['trend']} (MA20:{r['ma20']}, MA60:{r['ma60']})")
    print(f"  成交量: {r['volume']}")
    print(f"  评分: {r['stars']} ({r['score']}/5)")
    print(f"  信号: {r['signal']}")

# 分类统计
buy_signals = [r for r in results if r['signal'] == '买入']
sell_signals = [r for r in results if r['signal'] == '卖出']
watch_signals = [r for r in results if r['signal'] == '观察']

print(f"\n=== 信号汇总 ===")
print(f"买入信号: {len(buy_signals)}只")
print(f"卖出信号: {len(sell_signals)}只")
print(f"观察信号: {len(watch_signals)}只")

# 保存结果
import json
with open('/Users/forsafe/.openclaw/workspace-agou/reports/technical_analysis_2026-03-27.json', 'w', encoding='utf-8') as f:
    json.dump({
        'date': '2026-03-27',
        'stocks': results_sorted,
        'summary': {
            'buy': len(buy_signals),
            'sell': len(sell_signals),
            'watch': len(watch_signals)
        }
    }, f, ensure_ascii=False, indent=2)

print("\n数据已保存到 technical_analysis_2026-03-27.json")
