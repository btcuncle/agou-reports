import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

# 获取今日日期
today = datetime(2026, 3, 30)
end_date = today.strftime('%Y%m%d')
start_date = (today - timedelta(days=90)).strftime('%Y%m%d')

print(f"数据获取区间: {start_date} - {end_date}")
print(f"数据源: AKShare (Tushare降级)")

# 007研报股票池 - 从daily-intel-2026-03-30.md提取的核心标的
stocks = {
    # 锂电/储能
    '宁德时代': '300750',
    '亿纬锂能': '300014',
    '阳光电源': '300274',
    '德业股份': '605117',
    '湖南裕能': '301358',
    '富临精工': '300432',
    '龙蟠科技': '603906',
    '德方纳米': '300769',
    '恩捷股份': '002812',
    '石大胜华': '603026',
    '海科新源': '301292',
    # 光通信
    '长飞光纤': '601869',
    '杰普特': '688025',
    # AIDC/电源
    '金盘科技': '688676',
    '四方股份': '601126',
    '伊戈尔': '002922',
    '新风光': '688663',
    '泰豪科技': '600590',
    '潍柴动力': '000338',
    # PCB/CCL
    '鼎泰高科': '301377',
    '宏和科技': '603256',
    '菲利华': '300395',
    '生益科技': '600183',
    # 铜箔/材料
    '海亮股份': '002203',
    '诺德股份': '600110',
    '德福科技': '301511',
    # 光模块/芯片
    '中际旭创': '300308',
    '新易盛': '300502',
    '天孚通信': '300394',
    '盛科通信': '688702',
    # 风电
    '大金重工': '002487',
    '金风科技': '002202',
    '振江股份': '603507',
    # 其他
    '万泽股份': '000534',
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

def get_stock_data_akshare(symbol):
    """使用AKShare获取股票日线数据"""
    try:
        # 判断市场
        if symbol.startswith('6'):
            symbol_full = f"{symbol}.SH"
        else:
            symbol_full = f"{symbol}.SZ"
        
        # 获取历史数据
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
        if df is None or len(df) < 20:
            return None, symbol_full
        
        # 重命名列以兼容
        df = df.rename(columns={
            '日期': 'trade_date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'vol'
        })
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df = df.sort_values('trade_date')
        return df, symbol_full
    except Exception as e:
        print(f"  AKShare获取失败: {e}")
        return None, symbol

def analyze_stock(name, symbol):
    """分析单只股票"""
    df, ts_code = get_stock_data_akshare(symbol)
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
        'code': symbol,
        'close': round(float(latest_close), 2),
        'change_pct': round(float(change_pct), 2),
        'macd': f"{macd_signal} (DIF:{dif.iloc[-1]:.2f}, DEA:{dea.iloc[-1]:.2f})",
        'macd_signal': macd_signal,
        'obv': f"{obv_trend} (5日变化:{obv_change:.0f})",
        'obv_trend': obv_trend,
        'rsi': f"{rsi_val:.1f} ({rsi_status})",
        'rsi_val': round(float(rsi_val), 1),
        'trend': trend,
        'volume': vol_status,
        'score': score,
        'stars': stars,
        'signal': signal,
        'ma20': round(float(ma20), 2),
        'ma60': round(float(ma60), 2)
    }

# 获取指数数据
print("\n=== 市场指数 ===")
indices = {
    '上证指数': 'sh000001',
    '深证成指': 'sz399001',
    '创业板指': 'sz399006',
    '科创50': 'sh000688'
}

index_data = {}
for name, symbol in indices.items():
    try:
        # 使用AKShare获取指数数据
        if symbol.startswith('sh'):
            df = ak.index_zh_a_hist(symbol=symbol.replace('sh', ''), period="daily", start_date=start_date, end_date=end_date)
        else:
            df = ak.index_zh_a_hist(symbol=symbol.replace('sz', ''), period="daily", start_date=start_date, end_date=end_date)
        
        if df is not None and len(df) > 0:
            df = df.rename(columns={
                '日期': 'date',
                '收盘': 'close',
                '成交量': 'vol'
            })
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            change_pct = (latest['close'] - prev['close']) / prev['close'] * 100
            index_data[name] = {
                'close': round(float(latest['close']), 2),
                'change_pct': round(float(change_pct), 2),
                'volume': int(latest['vol']) if 'vol' in latest else 0
            }
            print(f"{name}: {latest['close']:.2f} ({change_pct:+.2f}%)")
    except Exception as e:
        print(f"{name}: 获取失败 - {e}")

# 分析股票池
print("\n=== 股票分析 ===")
results = []
failed_stocks = []
for name, code in stocks.items():
    print(f"分析 {name}({code})...", end=" ")
    result = analyze_stock(name, code)
    if result:
        results.append(result)
        print(f"{result['stars']} {result['signal']}")
    else:
        failed_stocks.append(name)
        print("失败")

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
print(f"获取失败: {len(failed_stocks)}只")

# 板块分组
sectors = {
    '锂电/储能': ['宁德时代', '亿纬锂能', '阳光电源', '德业股份', '湖南裕能', '富临精工', '龙蟠科技', '德方纳米', '恩捷股份', '石大胜华', '海科新源'],
    '光通信': ['长飞光纤', '杰普特'],
    'AIDC/电源': ['金盘科技', '四方股份', '伊戈尔', '新风光', '泰豪科技', '潍柴动力'],
    'PCB/CCL': ['鼎泰高科', '宏和科技', '菲利华', '生益科技'],
    '铜箔/材料': ['海亮股份', '诺德股份', '德福科技'],
    '光模块/芯片': ['中际旭创', '新易盛', '天孚通信', '盛科通信'],
    '风电': ['大金重工', '金风科技', '振江股份'],
    '其他': ['万泽股份']
}

sector_analysis = {}
for sector, stock_names in sectors.items():
    sector_stocks = [r for r in results if r['name'] in stock_names]
    if sector_stocks:
        avg_score = sum(s['score'] for s in sector_stocks) / len(sector_stocks)
        best = max(sector_stocks, key=lambda x: x['score'])
        worst = min(sector_stocks, key=lambda x: x['score'])
        sector_analysis[sector] = {
            'avg_score': round(avg_score, 2),
            'count': len(sector_stocks),
            'best': best['name'],
            'worst': worst['name']
        }

print("\n=== 板块分析 ===")
for sector, data in sector_analysis.items():
    print(f"{sector}: 平均评分{data['avg_score']}⭐ | 最强:{data['best']} | 最弱:{data['worst']}")

# 保存结果
output_data = {
    'date': '2026-03-30',
    'index_data': index_data,
    'stocks': results_sorted,
    'sectors': sector_analysis,
    'summary': {
        'buy': len(buy_signals),
        'sell': len(sell_signals),
        'watch': len(watch_signals),
        'failed': failed_stocks
    },
    'data_source': 'AKShare + 本地计算',
    'calc_time': datetime.now().strftime('%Y-%m-%d %H:%M')
}

output_file = '/Users/forsafe/.openclaw/workspace-agou/reports/technical_analysis_2026-03-30.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

print(f"\n数据已保存到 {output_file}")
