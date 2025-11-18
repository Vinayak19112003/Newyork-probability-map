#!/usr/bin/env python3
"""
Backtesting Framework for NY Probability Map

Tests trading performance using historical probability signals.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import json
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# BACKTEST CONFIGURATION
# ============================================================================

# Trading rules
ENTRY_THRESHOLD_HIGH = 70.0  # Enter long if P(High First) >= 70%
ENTRY_THRESHOLD_LOW = 30.0   # Enter short if P(High First) <= 30%
MIN_SAMPLE_SIZE = 50         # Only trade variants with n >= 50 samples
MIN_RELIABILITY = 'Medium'   # Only trade Medium or High reliability

# Position sizing
POSITION_SIZE = 1            # Number of contracts per trade
POINTS_TO_DOLLARS = 20       # NQ: $20 per point

# Risk management
STOP_LOSS_POINTS = None      # None = no stop loss, or specify points
PROFIT_TARGET_POINTS = None  # None = exit at opposite level, or specify points

# Execution assumptions
SLIPPAGE_POINTS = 0.25       # Assume 0.25 points slippage per side
COMMISSION_PER_CONTRACT = 2.50  # Round-trip commission

# ============================================================================
# BACKTESTING ENGINE
# ============================================================================

class Trade:
    """Represents a single trade."""
    def __init__(self, date, direction, entry_price, variant, prob, sample_size):
        self.date = date
        self.direction = direction  # 'long' or 'short'
        self.entry_price = entry_price
        self.exit_price = None
        self.target_level = None
        self.variant = variant
        self.probability = prob
        self.sample_size = sample_size
        self.points = None
        self.pnl_gross = None
        self.pnl_net = None
        self.outcome = None  # 'win', 'loss', 'fail'
        self.exit_reason = None

class BacktestEngine:
    """Backtesting engine for NY Probability Map."""

    def __init__(self, daily_data, prob_map):
        self.daily_data = daily_data
        self.prob_map = prob_map
        self.trades = []
        self.equity_curve = []
        self.initial_capital = 10000  # Starting capital

    def should_enter_trade(self, row):
        """Determine if we should enter a trade based on variant probability."""
        variant = row['variant']

        # Find variant in probability map
        variant_data = self.prob_map[self.prob_map['variant'] == variant]

        if len(variant_data) == 0:
            return None, None

        variant_data = variant_data.iloc[0]

        # Check reliability filters
        if variant_data['n'] < MIN_SAMPLE_SIZE:
            return None, None

        reliability = 'High' if variant_data['n'] >= 150 else 'Medium' if variant_data['n'] >= 50 else 'Low'
        if reliability == 'Low':
            return None, None

        p_high = variant_data['first_high_pct']

        # Check entry thresholds
        if p_high >= ENTRY_THRESHOLD_HIGH:
            return 'long', variant_data
        elif p_high <= ENTRY_THRESHOLD_LOW:
            return 'short', variant_data
        else:
            return None, None

    def calculate_trade_outcome(self, trade, row):
        """Calculate trade outcome based on actual market behavior."""
        # Set target based on direction
        if trade.direction == 'long':
            trade.target_level = row['london_high']
            opposite_level = row['london_low']
        else:  # short
            trade.target_level = row['london_low']
            opposite_level = row['london_high']

        # Determine what happened
        first_sweep = row['first_sweep_side']
        both_hit = row['both_flag']

        if trade.direction == 'long':
            if first_sweep == 'High':
                # Target hit first - WIN
                trade.exit_price = trade.target_level
                trade.outcome = 'win'
                trade.exit_reason = 'target'
            elif both_hit:
                # Both hit, but low first - LOSS (stopped out then target hit)
                trade.exit_price = opposite_level
                trade.outcome = 'loss'
                trade.exit_reason = 'stop'
            else:
                # Only low hit - LOSS
                trade.exit_price = opposite_level
                trade.outcome = 'loss'
                trade.exit_reason = 'opposite_level'
        else:  # short
            if first_sweep == 'Low':
                # Target hit first - WIN
                trade.exit_price = trade.target_level
                trade.outcome = 'win'
                trade.exit_reason = 'target'
            elif both_hit:
                # Both hit, but high first - LOSS
                trade.exit_price = opposite_level
                trade.outcome = 'loss'
                trade.exit_reason = 'stop'
            else:
                # Only high hit - LOSS
                trade.exit_price = opposite_level
                trade.outcome = 'loss'
                trade.exit_reason = 'opposite_level'

        # Calculate P&L
        if trade.direction == 'long':
            trade.points = trade.exit_price - trade.entry_price
        else:
            trade.points = trade.entry_price - trade.exit_price

        # Apply slippage (both entry and exit)
        trade.points -= (SLIPPAGE_POINTS * 2)

        # Calculate dollar P&L
        trade.pnl_gross = trade.points * POINTS_TO_DOLLARS * POSITION_SIZE
        trade.pnl_net = trade.pnl_gross - (COMMISSION_PER_CONTRACT * POSITION_SIZE)

        return trade

    def run_backtest(self):
        """Execute backtest on all historical data."""
        print("\n" + "="*80)
        print("RUNNING BACKTEST")
        print("="*80)

        print(f"\nTrading Rules:")
        print(f"  Enter Long: P(High First) >= {ENTRY_THRESHOLD_HIGH}%")
        print(f"  Enter Short: P(High First) <= {ENTRY_THRESHOLD_LOW}%")
        print(f"  Min Sample Size: {MIN_SAMPLE_SIZE}")
        print(f"  Position Size: {POSITION_SIZE} contract(s)")
        print(f"  Slippage: {SLIPPAGE_POINTS} pts per side")
        print(f"  Commission: ${COMMISSION_PER_CONTRACT} round-trip")

        cumulative_pnl = 0

        for idx, row in self.daily_data.iterrows():
            # Skip if no first sweep (no trade outcome)
            if pd.isna(row['first_sweep_side']):
                continue

            # Check if we should enter trade
            direction, variant_data = self.should_enter_trade(row)

            if direction is None:
                continue

            # Create trade
            # Entry at NY open (08:00)
            entry_price = row['ny_open']

            trade = Trade(
                date=row['date'],
                direction=direction,
                entry_price=entry_price,
                variant=row['variant'],
                prob=variant_data['first_high_pct'],
                sample_size=variant_data['n']
            )

            # Calculate outcome
            trade = self.calculate_trade_outcome(trade, row)

            # Track P&L
            cumulative_pnl += trade.pnl_net

            # Store trade
            self.trades.append(trade)

            # Track equity
            self.equity_curve.append({
                'date': row['date'],
                'pnl': trade.pnl_net,
                'cumulative_pnl': cumulative_pnl,
                'equity': self.initial_capital + cumulative_pnl
            })

        print(f"\n✓ Backtest complete: {len(self.trades)} trades executed")

    def calculate_statistics(self):
        """Calculate comprehensive performance statistics."""
        if len(self.trades) == 0:
            print("\n⚠ No trades executed")
            return {}

        # Convert trades to DataFrame for analysis
        trade_data = []
        for t in self.trades:
            trade_data.append({
                'date': t.date,
                'direction': t.direction,
                'entry': t.entry_price,
                'exit': t.exit_price,
                'points': t.points,
                'pnl_gross': t.pnl_gross,
                'pnl_net': t.pnl_net,
                'outcome': t.outcome,
                'variant': t.variant,
                'probability': t.probability,
                'sample_size': t.sample_size
            })

        trades_df = pd.DataFrame(trade_data)

        # Basic statistics
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['outcome'] == 'win'])
        losing_trades = len(trades_df[trades_df['outcome'] == 'loss'])

        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        # P&L statistics
        total_pnl_net = trades_df['pnl_net'].sum()
        total_pnl_gross = trades_df['pnl_gross'].sum()
        total_commissions = total_pnl_gross - total_pnl_net

        avg_win = trades_df[trades_df['outcome'] == 'win']['pnl_net'].mean() if winning_trades > 0 else 0
        avg_loss = trades_df[trades_df['outcome'] == 'loss']['pnl_net'].mean() if losing_trades > 0 else 0

        largest_win = trades_df['pnl_net'].max()
        largest_loss = trades_df['pnl_net'].min()

        # Profit factor
        gross_profit = trades_df[trades_df['pnl_net'] > 0]['pnl_net'].sum()
        gross_loss = abs(trades_df[trades_df['pnl_net'] < 0]['pnl_net'].sum())
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf')

        # Drawdown calculation
        equity_df = pd.DataFrame(self.equity_curve)
        equity_df['peak'] = equity_df['equity'].cummax()
        equity_df['drawdown'] = equity_df['equity'] - equity_df['peak']
        equity_df['drawdown_pct'] = (equity_df['drawdown'] / equity_df['peak'] * 100)

        max_drawdown = equity_df['drawdown'].min()
        max_drawdown_pct = equity_df['drawdown_pct'].min()

        # Points statistics
        avg_points = trades_df['points'].mean()

        # Direction breakdown
        long_trades = len(trades_df[trades_df['direction'] == 'long'])
        short_trades = len(trades_df[trades_df['direction'] == 'short'])
        long_win_rate = (len(trades_df[(trades_df['direction'] == 'long') & (trades_df['outcome'] == 'win')]) / long_trades * 100) if long_trades > 0 else 0
        short_win_rate = (len(trades_df[(trades_df['direction'] == 'short') & (trades_df['outcome'] == 'win')]) / short_trades * 100) if short_trades > 0 else 0

        # Time period
        date_range = f"{trades_df['date'].min()} to {trades_df['date'].max()}"

        stats = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_pnl_net': total_pnl_net,
            'total_pnl_gross': total_pnl_gross,
            'total_commissions': total_commissions,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'max_drawdown_pct': max_drawdown_pct,
            'avg_points': avg_points,
            'long_trades': long_trades,
            'short_trades': short_trades,
            'long_win_rate': long_win_rate,
            'short_win_rate': short_win_rate,
            'date_range': date_range,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss,
            'final_equity': self.initial_capital + total_pnl_net,
            'return_pct': (total_pnl_net / self.initial_capital * 100)
        }

        return stats, trades_df, equity_df

    def generate_report(self, stats, trades_df, equity_df):
        """Generate comprehensive backtest report."""
        print("\n" + "="*80)
        print("BACKTEST RESULTS")
        print("="*80)

        print(f"\n📅 Trading Period: {stats['date_range']}")
        print(f"💰 Initial Capital: ${self.initial_capital:,.2f}")
        print(f"💰 Final Equity: ${stats['final_equity']:,.2f}")
        print(f"📈 Total Return: {stats['return_pct']:.2f}%")

        print(f"\n📊 Trade Statistics:")
        print(f"  Total Trades: {stats['total_trades']}")
        print(f"  Winning Trades: {stats['winning_trades']} ({stats['win_rate']:.2f}%)")
        print(f"  Losing Trades: {stats['losing_trades']} ({100 - stats['win_rate']:.2f}%)")
        print(f"  Long Trades: {stats['long_trades']} (Win Rate: {stats['long_win_rate']:.2f}%)")
        print(f"  Short Trades: {stats['short_trades']} (Win Rate: {stats['short_win_rate']:.2f}%)")

        print(f"\n💵 P&L Analysis:")
        print(f"  Total P&L (Net): ${stats['total_pnl_net']:,.2f}")
        print(f"  Total P&L (Gross): ${stats['total_pnl_gross']:,.2f}")
        print(f"  Total Commissions: ${stats['total_commissions']:,.2f}")
        print(f"  Average Win: ${stats['avg_win']:,.2f}")
        print(f"  Average Loss: ${stats['avg_loss']:,.2f}")
        print(f"  Largest Win: ${stats['largest_win']:,.2f}")
        print(f"  Largest Loss: ${stats['largest_loss']:,.2f}")
        print(f"  Profit Factor: {stats['profit_factor']:.2f}")

        print(f"\n📉 Risk Metrics:")
        print(f"  Max Drawdown: ${stats['max_drawdown']:,.2f} ({stats['max_drawdown_pct']:.2f}%)")
        print(f"  Average Points per Trade: {stats['avg_points']:.2f}")

        # Top performing variants
        print(f"\n🏆 Top 10 Variants by P&L:")
        variant_pnl = trades_df.groupby('variant')['pnl_net'].agg(['sum', 'count', 'mean']).sort_values('sum', ascending=False)
        for i, (variant, row) in enumerate(variant_pnl.head(10).iterrows(), 1):
            print(f"  {i}. {variant}")
            print(f"     Trades: {int(row['count'])}, Total P&L: ${row['sum']:,.2f}, Avg: ${row['mean']:.2f}")

        # Worst performing variants
        print(f"\n❌ Bottom 5 Variants by P&L:")
        for i, (variant, row) in enumerate(variant_pnl.tail(5).iterrows(), 1):
            print(f"  {i}. {variant}")
            print(f"     Trades: {int(row['count'])}, Total P&L: ${row['sum']:,.2f}, Avg: ${row['mean']:.2f}")

        # Monthly/Yearly breakdown
        try:
            trades_df_copy = trades_df.copy()
            trades_df_copy['date'] = pd.to_datetime(trades_df_copy['date'], errors='coerce')
            trades_df_copy['year'] = trades_df_copy['date'].dt.year
            yearly_pnl = trades_df_copy.groupby('year')['pnl_net'].sum()

            print(f"\n📅 Yearly P&L:")
            for year, pnl in yearly_pnl.items():
                print(f"  {year}: ${pnl:,.2f}")
        except Exception as e:
            print(f"\n⚠ Could not generate yearly breakdown: {e}")

        # Export results
        trades_df.to_csv('output/backtest_trades.csv', index=False)
        equity_df.to_csv('output/backtest_equity_curve.csv', index=False)

        with open('output/backtest_statistics.json', 'w') as f:
            # Convert non-serializable types
            stats_export = stats.copy()
            stats_export['profit_factor'] = float(stats_export['profit_factor']) if stats_export['profit_factor'] != float('inf') else 'Infinity'
            json.dump(stats_export, f, indent=2, default=str)

        print(f"\n✓ Exported results:")
        print(f"  - backtest_trades.csv")
        print(f"  - backtest_equity_curve.csv")
        print(f"  - backtest_statistics.json")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main backtest execution."""
    print("\n" + "="*80)
    print("NY PROBABILITY MAP - BACKTEST")
    print("="*80)

    # Load data
    print("\nLoading data...")
    daily_data = pd.read_csv('output/daily_sessions_with_labels.csv')
    prob_map = pd.read_csv('output/ny_probability_map.csv')

    print(f"  Daily data: {len(daily_data):,} rows")
    print(f"  Probability map: {len(prob_map)} variants")

    # Initialize backtest engine
    engine = BacktestEngine(daily_data, prob_map)

    # Run backtest
    engine.run_backtest()

    # Calculate statistics
    stats, trades_df, equity_df = engine.calculate_statistics()

    # Generate report
    engine.generate_report(stats, trades_df, equity_df)

    print("\n" + "="*80)
    print("✓ BACKTEST COMPLETE")
    print("="*80)

if __name__ == '__main__':
    main()
