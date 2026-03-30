import tushare as ts
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time

# 读取token
token = open('/Users/forsafe/.openclaw/tushare_token.txt').read().strip()
ts.set_token(token)
pro = ts.pro_api()

# 股票列表
stocks = [
    # 核心标的（5次以上）
    ("中际旭创", "300308.SZ"),
    ("新易盛", "300502.SZ"),
    ("天孚通信", "300394.SZ"),
    ("阳光电源", "300274.SZ"),
    ("源杰科技", "688498.SH"),
    ("烽火通信", "600498.SH"),
    ("润泽科技", "300442.SZ"),
    ("沪电股份", "002463.SZ"),
    ("长光华芯", "688048.SH"),
    ("光库科技", "300620.SZ"),
    ("海光信息", "688041.SH"),
    ("胜宏科技", "300476.SZ"),
    ("汇绿生态", "001267.SZ"),
    ("嘉元科技", "688388.SH"),
    ("华工科技", "000988.SZ"),
    ("长飞光纤", "601869.SH"),
    ("罗博特科", "300757.SZ"),
    ("东山精密", "002384.SZ"),
    ("数据港", "603881.SH"),
    ("腾景科技", "688195.SH"),
    # 重要标的（4次）
    ("东方电气", "600875.SH"),
    ("北方华创", "002371.SZ"),
    ("剑桥科技", "603083.SH"),
    ("兆易创新", "603986.SH"),
    ("北京君正", "300223.SZ"),
    ("江波龙", "301308.SZ"),
    ("光迅科技", "002281.SZ"),
    ("仕佳光子", "688313.SH"),
    ("协创数据", "300857.SZ"),
    ("东阳光", "600673.SH"),
    ("奥飞数据", "300738.SZ"),
    ("大位科技", "603316.SH"),
    ("光环新网", "300383.SZ"),
    ("迈为股份", "300751.SZ"),
    ("永鼎股份", "600105.SH"),
    # 补充标的（3次）
    ("应流股份", "603308.SH"),
    ("鹏鼎控股", "002938.SZ"),
    ("深南电路", "002916.SZ"),
    ("生益科技", "600183.SH"),
    ("拓荆科技", "688072.SH"),
]

def get_stock_data(ts_code, name):
    """获取股票日线数据"""
    try:
        # 获取最近60个交易日数据
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=120)).strftime('%Y%m%d')
        
        df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        if df is None or len(df) < 30:
            print(f"  {name}({ts_code}): 数据不足")
            return None
        
        df = df.sort_values('trade_date', ascending=True).reset_index(drop=True)
        return df
    except Exception as e:
        print(f"  {name}({ts_code}): 获取失败 - {e}")
        return None

def calculate_ma(df, window):
    """计算移动平均线"""
    return df['close'].rolling(window=window).mean()

def calculate_macd(df, fast=12, slow=26, signal=9):
    """计算MACD指标"""
    exp1 = df['close'].ewm(span=fast, adjust=False).mean()
    exp2 = df['close'].ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    return macd, signal_line, histogram

def calculate_rsi(df, period=14):
    """计算RSI指标"""
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_obv(df):
    """计算OBV指标"""
    obv = [0]
    for i in range(1, len(df)):
        if df['close'].iloc[i] > df['close'].iloc[i-1]:
            obv.append(obv[-1] + df['vol'].iloc[i])
        elif df['close'].iloc[i] < df['close'].iloc[i-1]:
            obv.append(obv[-1] - df['vol'].iloc[i])
        else:
            obv.append(obv[-1])
    return pd.Series(obv, index=df.index)

def analyze_stock(name, ts_code):
    """分析单只股票"""
    df = get_stock_data(ts_code, name)
    if df is None:
        return None
    
    if len(df) < 30:
        return None
    
    # 计算指标
    df['MA5'] = calculate_ma(df, 5)
    df['MA10'] = calculate_ma(df, 10)
    df['MA20'] = calculate_ma(df, 20)
    df['MACD'], df['MACD_Signal'], df['MACD_Hist'] = calculate_macd(df)
    df['RSI14'] = calculate_rsi(df, 14)
    df['OBV'] = calculate_obv(df)
    
    # 获取最新数据
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    
    close = latest['close']
    prev_close = prev['close']
    change_pct = (close - prev_close) / prev_close * 100
    
    # MACD分析
    macd = latest['MACD']
    macd_signal = latest['MACD_Signal']
    macd_hist = latest['MACD_Hist']
    prev_macd = prev['MACD']
    prev_signal = prev['MACD_Signal']
    
    if macd > macd_signal and prev_macd <= prev_signal:
        macd_status = "金叉"
    elif macd < macd_signal and prev_macd >= prev_signal:
        macd_status = "死叉"
    elif macd > macd_signal:
        macd_status = "多头"
    else:
        macd_status = "空头"
    
    # RSI分析
    rsi = latest['RSI14']
    if rsi > 70:
        rsi_status = f"{rsi:.1f}(超买)"
    elif rsi < 30:
        rsi_status = f"{rsi:.1f}(超卖)"
    else:
        rsi_status = f"{rsi:.1f}(中性)"
    
    # OBV分析
    obv_now = latest['OBV']
    obv_5days = df['OBV'].iloc[-6:-1].mean() if len(df) >= 6 else obv_now
    if obv_now > obv_5days * 1.02:
        obv_status = "上升"
    elif obv_now < obv_5days * 0.98:
        obv_status = "下降"
    else:
        obv_status = "走平"
    
    # 均线分析
    ma5 = latest['MA5']
    ma10 = latest['MA10']
    ma20 = latest['MA20']
    
    if ma5 > ma10 > ma20:
        ma_status = "多头排列"
    elif ma5 < ma10 < ma20:
        ma_status = "空头排列"
    elif ma5 > ma10:
        ma_status = "5上穿10"
    else:
        ma_status = "5下穿10"
    
    # 星级评定
    stars = 3  # 默认3星
    
    if macd_status == "金叉" and rsi < 50 and obv_status == "上升":
        stars = 5
    elif macd_status == "金叉" or (rsi < 30 and change_pct > 0):
        stars = 4
    elif macd_status == "死叉" or rsi > 70:
        stars = 2
    elif macd_status == "空头" and rsi > 70:
        stars = 1
    
    # 信号描述
    signals = []
    if macd_status in ["金叉", "多头"]:
        signals.append("MACD多")
    elif macd_status in ["死叉", "空头"]:
        signals.append("MACD空")
    
    if rsi < 30:
        signals.append("RSI超卖")
    elif rsi > 70:
        signals.append("RSI超买")
    
    if obv_status == "上升":
        signals.append("OBV升")
    elif obv_status == "下降":
        signals.append("OBV降")
    
    signal_str = "+".join(signals) if signals else "中性"
    
    return {
        'name': name,
        'ts_code': ts_code,
        'close': close,
        'change_pct': change_pct,
        'macd': macd_status,
        'rsi': rsi_status,
        'obv': obv_status,
        'ma': ma_status,
        'stars': stars,
        'signal': signal_str
    }

# 获取指数数据
def get_index_data():
    """获取主要指数数据"""
    indices = [
        ("上证指数", "000001.SH"),
        ("深证成指", "399001.SZ"),
        ("创业板指", "399006.SZ"),
        ("科创50", "000688.SH"),
    ]
    
    index_data = []
    for name, code in indices:
        try:
            df = pro.index_daily(ts_code=code, limit=2)
            if df is not None and len(df) >= 2:
                df = df.sort_values('trade_date', ascending=True)
                latest = df.iloc[-1]
                prev = df.iloc[-2]
                change_pct = (latest['close'] - prev['close']) / prev['close'] * 100
                index_data.append({
                    'name': name,
                    'close': latest['close'],
                    'change_pct': change_pct
                })
        except Exception as e:
            print(f"  {name}获取失败: {e}")
    
    return index_data

# 主程序
print("="*60)
print("007研报股票技术分析")
print("="*60)

# 获取指数数据
print("\n【获取市场指数】")
index_data = get_index_data()

# 分析所有股票
results = []
print("\n【分析股票】")
for i, (name, ts_code) in enumerate(stocks):
    print(f"[{i+1}/{len(stocks)}] {name}({ts_code})")
    result = analyze_stock(name, ts_code)
    if result:
        results.append(result)
    time.sleep(0.3)  # 避免请求过快

print(f"\n成功获取 {len(results)} 只股票数据")

# 保存结果
import json
with open('/Users/forsafe/.openclaw/workspace-agou/reports/tech_analysis_data.json', 'w', encoding='utf-8') as f:
    json.dump({'indices': index_data, 'stocks': results}, f, ensure_ascii=False, indent=2)

print("数据已保存到 tech_analysis_data.json")
