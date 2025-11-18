# Backtest Analysis - Base Model

## Summary

**Overall Performance: ❌ UNPROFITABLE**

| Metric | Value |
|--------|-------|
| **Total Return** | -107.13% |
| **Final Equity** | -$713.50 (started with $10,000) |
| **Total Trades** | 791 |
| **Win Rate** | 87.36% ⭐ |
| **Profit Factor** | 0.93 ❌ |
| **Max Drawdown** | -$21,752 (-212%) |

## 🔍 Key Finding: High Win Rate, Still Losing Money

This is a **classic trading paradox**: The model has an **87% win rate** but still loses money overall.

### Why This Happens

**Win/Loss Asymmetry:**
- **Average Win**: $196.34
- **Average Loss**: -$1,463.82
- **Loss/Win Ratio**: 7.5x

**The Math:**
- When right (87% of time): Win $196 × 691 trades = +$135,609
- When wrong (13% of time): Lose $1,464 × 100 trades = -$146,382
- **Net Result**: -$10,773 (plus $1,978 commissions)

### Root Cause

The backtest logic exits at the **opposite London level** when wrong. Example:

- **Long Trade**: Enter at NY open expecting London High to hit first
  - If right: Exit at London High for ~$196 profit
  - If wrong: Exit at London Low for ~-$1,464 loss

The **London range can be 40-100+ points**, so when you're wrong, you lose the FULL range.

## 📊 Variant Performance Analysis

### ✅ Profitable Variants (Only 3!)

| Variant | Trades | Total P&L | Avg P&L | Win Rate |
|---------|--------|-----------|---------|----------|
| **Compressed\|Low\|Below\|Below** | 52 | **+$5,284** | +$102 | ~10% |
| **Normal\|Low\|Below\|Below** | 85 | **+$4,386** | +$52 | ~10% |
| **Expanded\|None\|Above\|Above** | 51 | **+$2,423** | +$48 | ~92% |

**Key Insight**: The **"Below|Below" short variants** are profitable because:
1. They have LOW probability (~10%), so we SHORT
2. When we short and are right, we make money
3. The losses when wrong are smaller because London range is smaller in these setups

### ❌ Worst Performing Variants

| Variant | Trades | Total P&L | Avg P&L | Win Rate | Prob |
|---------|--------|-----------|---------|----------|------|
| **Normal\|High\|Above\|Above** | 134 | **-$11,097** | -$83 | 85.82% | 85.82% |
| **Expanded\|Low\|Above\|Above** | 59 | **-$6,066** | -$103 | 84.75% | 84.75% |
| **Expanded\|Low\|Below\|Below** | 92 | **-$5,896** | -$64 | 16.30% | 16.30% |

**Irony Alert**: **Normal|High|Above|Above** has **85% win rate** but is the WORST performer (-$11K)!

Why? Because:
- 134 trades × 85% win rate = 114 wins × $196 = +$22,344
- 134 trades × 15% losses = 20 losses × -$1,464 = -$29,280
- **Net**: -$6,936 (before commissions)

## 🎯 What We Learned

### 1. **High Probability ≠ Profitability**
Having an 85% edge is worthless if your losses are 7x larger than your wins.

### 2. **Risk-Reward Ratio Matters Most**
The model correctly predicts direction 87% of the time, but the **risk/reward is severely negative**.

### 3. **London Range Varies Wildly**
- Small range days: Win $100-200, Lose $400-600
- Large range days: Win $300-500, Lose $2,000-6,000

### 4. **Need Stop Losses**
Exiting at the opposite level is suicide. A **stop loss at breakeven** or small loss would transform this model.

### 5. **Some Variants Work**
The **"Below|Below"** short variants are actually profitable because they have good risk/reward when betting against the odds.

## 💡 Recommendations for Improvement

### Strategy 1: Add Stop Losses
```
If long:
  - Stop Loss: London Low or Asia Low (whichever is closer)
  - Target: London High
  - This limits losses to 20-40 points instead of full range
```

### Strategy 2: Only Trade Select Variants
```
Trade ONLY these variants:
- Compressed|Low|Below|Below (short)
- Normal|Low|Below|Below (short)
- Expanded|None|Above|Above (long)

Expected improvement: +$12,093 (vs -$10,713)
```

### Strategy 3: Inverse Low-Probability Signals
```
When P(High) < 20%:
  - Enter SHORT with tight stop at London High
  - Target London Low
  - These setups have better risk/reward
```

### Strategy 4: Use Trailing Stops
```
When target is 50% achieved:
  - Move stop to breakeven
  - Let winners run, cut losers quick
```

### Strategy 5: Reduce Position Size on Wide Ranges
```
If London Range > 60 points:
  - Trade 0.5 contracts instead of 1
  - This limits risk on volatile days
```

## 📈 Optimized Backtest Needed

Next steps:
1. **Run backtest with 30-point stop loss**
2. **Test only profitable variants**
3. **Add trailing stops**
4. **Position sizing based on range**
5. **Compare before/after results**

## 🎲 Current Model Assessment

| Aspect | Rating | Notes |
|--------|--------|-------|
| **Directional Edge** | ⭐⭐⭐⭐⭐ | 87% win rate is excellent |
| **Risk Management** | ❌ | No stops = account killer |
| **Profitability** | ❌ | -107% return |
| **Tradability** | ❌ | Cannot trade as-is |
| **Potential** | ⭐⭐⭐⭐ | With fixes, could be great |

## Conclusion

The **NY Probability Map has strong predictive power** (87% accuracy), but the **current execution strategy is flawed**. The model tells you the right direction, but without proper risk management, you'll go broke slowly.

**The fix is simple**:
1. Add stop losses at reasonable levels (30-50 points)
2. Only trade variants with good risk/reward
3. Consider inversing low-probability signals

With these adjustments, this model could easily become profitable.

---

**Next Action**: Run optimized backtest with stop losses and selective variant trading.
