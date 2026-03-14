"""
均线交叉策略 (MA Crossover Strategy)

策略逻辑:
- 短期均线上穿长期均线 → 买入信号 (Golden Cross)
- 短期均线下穿长期均线 → 卖出信号 (Death Cross)
"""

import pandas as pd
import numpy as np
from typing import Tuple


class MACrossoverStrategy:
    """均线交叉策略"""
    
    def __init__(self, short_window: int = 20, long_window: int = 50):
        self.short_window = short_window
        self.long_window = long_window
    
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成交易信号"""
        signals = pd.DataFrame(index=data.index)
        signals['price'] = data['Close']
        
        # 计算均线
        signals['SMA_short'] = data['Close'].rolling(window=self.short_window).mean()
        signals['SMA_long'] = data['Close'].rolling(window=self.long_window).mean()
        
        # 初始化信号
        signals['signal'] = 0
        
        # 金叉买入 (短期上穿长期)
        signals.loc[signals['SMA_short'] > signals['SMA_long'], 'signal'] = 1
        
        # 死叉卖出 (短期下穿长期)
        signals.loc[signals['SMA_short'] < signals['SMA_long'], 'signal'] = -1
        
        # 生成持仓信号 (持仓 = 前一时刻信号)
        signals['position'] = signals['signal'].shift(1).fillna(0)
        
        return signals
    
    def backtest(self, data: pd.DataFrame, initial_capital: float = 100000) -> dict:
        """简单回测"""
        signals = self.generate_signals(data)
        
        # 计算收益率
        signals['returns'] = signals['price'].pct_change()
        signals['strategy_returns'] = signals['position'] * signals['returns']
        
        # 计算累计收益
        signals['cumulative_returns'] = (1 + signals['strategy_returns']).cumprod()
        signals['portfolio_value'] = initial_capital * signals['cumulative_returns']
        
        # 计算指标
        total_return = signals['cumulative_returns'].iloc[-1] - 1
        annual_return = (1 + total_return) ** (252 / len(data)) - 1
        
        # 夏普比率 (简化)
        daily_returns = signals['strategy_returns'].dropna()
        sharpe_ratio = np.sqrt(252) * daily_returns.mean() / daily_returns.std()
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'final_value': signals['portfolio_value'].iloc[-1]
        }


if __name__ == '__main__':
    import yfinance as yf
    
    # 获取数据
    data = yf.download('AAPL', start='2020-01-01', end='2024-01-01')
    
    # 运行策略
    strategy = MACrossoverStrategy(short_window=20, long_window=50)
    results = strategy.backtest(data)
    
    print(f"总收益率: {results['total_return']:.2%}")
    print(f"年化收益率: {results['annual_return']:.2%}")
    print(f"夏普比率: {results['sharpe_ratio']:.2f}")
    print(f"最终市值: ¥{results['final_value']:,.2f}")
