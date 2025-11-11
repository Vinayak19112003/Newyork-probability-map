#!/usr/bin/env python3
"""
TradingView PineScript v5 Generator

Generates a complete, self-contained TradingView indicator that embeds
the 108-variant probability map and displays live probabilities on the chart.
"""

import json
import pandas as pd

def load_probability_map(filepath='ny_probability_map.json'):
    """Load the probability map from JSON."""
    print("="*80)
    print("LOADING PROBABILITY MAP")
    print("="*80)

    with open(filepath, 'r') as f:
        prob_map = json.load(f)

    print(f"\nLoaded {len(prob_map)} variants")
    return prob_map

def generate_pinescript(prob_map, output_file='NY_Probability_Map.pine'):
    """Generate the complete PineScript v5 indicator."""
    print("\n" + "="*80)
    print("GENERATING PINESCRIPT V5 INDICATOR")
    print("="*80)

    # Start building the script
    pine_script = '''// This source code is subject to the terms of the Mozilla Public License 2.0 at https://mozilla.org/MPL/2.0/
// © NY Probability Map - 108-Variant Context Engine

//@version=5
indicator("NY Probability Map (108-Variant)", overlay=true, max_boxes_count=500, max_labels_count=500)

// ============================================================================
// USER INPUTS
// ============================================================================

// Session Display
show_asia = input.bool(true, "Show Asia Session", group="Sessions")
show_london = input.bool(true, "Show London Session", group="Sessions")
show_ny = input.bool(true, "Show NY Session", group="Sessions")

// Session Colors
asia_color = input.color(color.new(color.blue, 90), "Asia Session", group="Colors")
london_color = input.color(color.new(color.orange, 90), "London Session", group="Colors")
ny_color = input.color(color.new(color.green, 90), "NY Session", group="Colors")

// Lines
show_london_levels = input.bool(true, "Show London High/Low", group="Display")
show_prob_table = input.bool(true, "Show Probability Table", group="Display")

// Analysis Parameters
asia_range_window = input.int(200, "Asia Range Rolling Window", minval=50, group="Analysis")

// ============================================================================
// SESSION TIME DEFINITIONS (America/New_York)
// ============================================================================

// Asia: 20:00 (prev day) - 00:00
asia_session = time(timeframe.period, "2000-0000:1234567")

// London: 02:00 - 05:00
london_session = time(timeframe.period, "0200-0500:1234567")

// Transition: 05:00 - 08:30
transition_session = time(timeframe.period, "0500-0830:1234567")

// NY: 08:30 - 11:00
ny_session = time(timeframe.period, "0830-1100:1234567")

// ============================================================================
// PROBABILITY MAP DATA (EMBEDDED)
// ============================================================================

'''

    # Generate arrays for probability map
    print("\nGenerating probability map arrays...")

    # Create arrays for each field
    variants = []
    n_samples = []
    first_high_pcts = []
    first_low_pcts = []
    sweep_both_pcts = []
    fail_pcts = []
    median_pen_highs = []
    median_pen_lows = []
    reliabilities = []

    # Also create arrays for the 4 factors
    asia_regimes = []
    london_sweeps = []
    transition_vs_londons = []
    ny_open_vs_londons = []

    for variant_data in prob_map:
        variants.append(variant_data['variant'])
        n_samples.append(variant_data['n'])
        first_high_pcts.append(variant_data['first_high_pct'])
        first_low_pcts.append(variant_data['first_low_pct'])
        sweep_both_pcts.append(variant_data['sweep_both_pct'])
        fail_pcts.append(variant_data['fail_pct'])

        median_pen_highs.append(variant_data['median_pen_high'] if variant_data['median_pen_high'] is not None else 0.0)
        median_pen_lows.append(variant_data['median_pen_low'] if variant_data['median_pen_low'] is not None else 0.0)

        reliabilities.append(1 if variant_data['reliability'] == 'High' else (2 if variant_data['reliability'] == 'Medium' else 3))

        asia_regimes.append(variant_data['asia_regime'])
        london_sweeps.append(variant_data['london_sweep'])
        transition_vs_londons.append(variant_data['transition_vs_london'])
        ny_open_vs_londons.append(variant_data['ny_open_vs_london'])

    # Add the arrays to the script
    pine_script += f'''// Probability Map Data ({len(variants)} variants)
var string[] map_variants = array.from({', '.join([f'"{v}"' for v in variants])})

var int[] map_n = array.from({', '.join(map(str, n_samples))})

var float[] map_first_high_pct = array.from({', '.join(map(str, first_high_pcts))})

var float[] map_fail_pct = array.from({', '.join(map(str, fail_pcts))})

var float[] map_median_pen_high = array.from({', '.join(map(str, median_pen_highs))})

var float[] map_median_pen_low = array.from({', '.join(map(str, median_pen_lows))})

var int[] map_reliability = array.from({', '.join(map(str, reliabilities))})

// ============================================================================
// SESSION TRACKING VARIABLES
// ============================================================================

var float asia_high = na
var float asia_low = na
var float asia_range = na

var float london_high = na
var float london_low = na
var float london_mid = na
var float london_range = na

var float transition_open = na
var float ny_open = na

var string current_variant = na
var int variant_index = -1

var box asia_box = na
var box london_box = na
var box ny_box = na

var line london_high_line = na
var line london_low_line = na

var table prob_table = na

// Arrays for rolling Asia range calculation
var float[] asia_range_history = array.new_float(0)

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

// Get Asia Range Regime based on rolling quantiles
get_asia_regime(range_val) =>
    if array.size(asia_range_history) < 50
        "Normal"  // Default until we have enough data
    else
        sorted = array.copy(asia_range_history)
        array.sort(sorted)

        size = array.size(sorted)
        q33_idx = int(size * 0.33)
        q66_idx = int(size * 0.66)

        q33 = array.get(sorted, q33_idx)
        q66 = array.get(sorted, q66_idx)

        if range_val < q33
            "Compressed"
        else if range_val > q66
            "Expanded"
        else
            "Normal"

// Get London Sweep pattern
get_london_sweep(l_high, l_low, a_high, a_low) =>
    swept_high = l_high > a_high
    swept_low = l_low < a_low

    if swept_high and swept_low
        "Both"
    else if swept_high
        "High"
    else if swept_low
        "Low"
    else
        "None"

// Get open position vs London midpoint
get_open_vs_london(open_price, l_mid, l_range) =>
    tolerance = l_range * 0.25
    upper_band = l_mid + tolerance
    lower_band = l_mid - tolerance

    if open_price > upper_band
        "Above"
    else if open_price < lower_band
        "Below"
    else
        "Within"

// Find variant in map
find_variant_index(variant_str) =>
    idx = -1
    for i = 0 to array.size(map_variants) - 1
        if array.get(map_variants, i) == variant_str
            idx := i
            break
    idx

// ============================================================================
// SESSION DETECTION & DATA COLLECTION
// ============================================================================

// Detect new day
new_day = ta.change(dayofweek)

// Reset on new day
if new_day
    asia_high := na
    asia_low := na
    asia_range := na
    london_high := na
    london_low := na
    london_mid := na
    london_range := na
    transition_open := na
    ny_open := na
    current_variant := na
    variant_index := -1

// Track Asia session
if asia_session
    if na(asia_high) or high > asia_high
        asia_high := high
    if na(asia_low) or low < asia_low
        asia_low := low

// Calculate Asia range at end of Asia session
if not na(asia_session[1]) and na(asia_session)
    asia_range := asia_high - asia_low
    // Add to rolling history
    array.push(asia_range_history, asia_range)
    if array.size(asia_range_history) > asia_range_window
        array.shift(asia_range_history)

// Track London session
if london_session
    if na(london_high) or high > london_high
        london_high := high
    if na(london_low) or low < london_low
        london_low := low

// Calculate London stats at end of London session
if not na(london_session[1]) and na(london_session)
    london_mid := (london_high + london_low) / 2
    london_range := london_high - london_low

// Capture Transition open (05:00 candle)
if transition_session and na(transition_session[1])
    transition_open := open

// Capture NY open and calculate variant
if ny_session and na(ny_session[1])
    ny_open := open

    // Calculate variant if all data is available
    if not na(asia_range) and not na(london_high) and not na(london_low) and not na(london_mid) and not na(transition_open)
        // Factor 1: Asia Range Regime
        asia_regime = get_asia_regime(asia_range)

        // Factor 2: London Sweep
        london_sweep = get_london_sweep(london_high, london_low, asia_high, asia_low)

        // Factor 3: Transition Open vs London Mid
        transition_vs_london = get_open_vs_london(transition_open, london_mid, london_range)

        // Factor 4: NY Open vs London Mid
        ny_open_vs_london = get_open_vs_london(ny_open, london_mid, london_range)

        // Create variant string
        current_variant := asia_regime + "|" + london_sweep + "|" + transition_vs_london + "|" + ny_open_vs_london

        // Find in map
        variant_index := find_variant_index(current_variant)

// ============================================================================
// VISUALIZATION
// ============================================================================

// Draw session boxes
if show_asia and asia_session and na(asia_session[1])
    asia_box := box.new(bar_index, high, bar_index, low, bgcolor=asia_color, border_color=color.new(color.blue, 50))

if not na(asia_box) and asia_session
    box.set_right(asia_box, bar_index)
    box.set_top(asia_box, math.max(box.get_top(asia_box), high))
    box.set_bottom(asia_box, math.min(box.get_bottom(asia_box), low))

if show_london and london_session and na(london_session[1])
    london_box := box.new(bar_index, high, bar_index, low, bgcolor=london_color, border_color=color.new(color.orange, 50))

if not na(london_box) and london_session
    box.set_right(london_box, bar_index)
    box.set_top(london_box, math.max(box.get_top(london_box), high))
    box.set_bottom(london_box, math.min(box.get_bottom(london_box), low))

if show_ny and ny_session and na(ny_session[1])
    ny_box := box.new(bar_index, high, bar_index, low, bgcolor=ny_color, border_color=color.new(color.green, 50))

if not na(ny_box) and ny_session
    box.set_right(ny_box, bar_index)
    box.set_top(ny_box, math.max(box.get_top(ny_box), high))
    box.set_bottom(ny_box, math.min(box.get_bottom(ny_box), low))

// Draw London High/Low lines during NY session
if show_london_levels and ny_session and not na(london_high) and not na(london_low)
    if na(london_high_line) or not na(ny_session[1]) and na(ny_session)
        london_high_line := line.new(bar_index, london_high, bar_index, london_high, color=color.new(color.red, 0), width=2, style=line.style_dashed)
        london_low_line := line.new(bar_index, london_low, bar_index, london_low, color=color.new(color.green, 0), width=2, style=line.style_dashed)

    if not na(london_high_line)
        line.set_x2(london_high_line, bar_index)
        line.set_x2(london_low_line, bar_index)

// ============================================================================
// PROBABILITY TABLE
// ============================================================================

if show_prob_table
    if na(prob_table)
        prob_table := table.new(position.top_right, 2, 10, border_width=1)

    if ny_session and variant_index >= 0
        // Get probability data
        n = array.get(map_n, variant_index)
        p_high = array.get(map_first_high_pct, variant_index)
        p_low = 100.0 - p_high
        p_fail = array.get(map_fail_pct, variant_index)
        med_pen_high = array.get(map_median_pen_high, variant_index)
        med_pen_low = array.get(map_median_pen_low, variant_index)
        reliability_code = array.get(map_reliability, variant_index)
        reliability_str = reliability_code == 1 ? "High" : (reliability_code == 2 ? "Medium" : "Low")

        // Update table
        table.cell(prob_table, 0, 0, "NY PROBABILITY MAP", bgcolor=color.new(color.gray, 70), text_color=color.white, text_size=size.normal)
        table.merge_cells(prob_table, 0, 0, 1, 0)

        table.cell(prob_table, 0, 1, "Variant:", bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.small)
        table.cell(prob_table, 1, 1, str.tostring(current_variant), bgcolor=color.new(color.gray, 90), text_color=color.yellow, text_size=size.small)

        table.cell(prob_table, 0, 2, "P(High First):", bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.small)
        table.cell(prob_table, 1, 2, str.tostring(p_high, "#.##") + "%", bgcolor=color.new(color.red, 80), text_color=color.white, text_size=size.normal)

        table.cell(prob_table, 0, 3, "P(Low First):", bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.small)
        table.cell(prob_table, 1, 3, str.tostring(p_low, "#.##") + "%", bgcolor=color.new(color.green, 80), text_color=color.white, text_size=size.normal)

        table.cell(prob_table, 0, 4, "P(Fail):", bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.small)
        table.cell(prob_table, 1, 4, str.tostring(p_fail, "#.##") + "%", bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.small)

        table.cell(prob_table, 0, 5, "Med Pen (High):", bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.small)
        table.cell(prob_table, 1, 5, str.tostring(med_pen_high, "#.##") + " pts", bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.small)

        table.cell(prob_table, 0, 6, "Med Pen (Low):", bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.small)
        table.cell(prob_table, 1, 6, str.tostring(med_pen_low, "#.##") + " pts", bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.small)

        table.cell(prob_table, 0, 7, "Sample Size:", bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.small)
        table.cell(prob_table, 1, 7, str.tostring(n), bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.small)

        table.cell(prob_table, 0, 8, "Reliability:", bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.small)
        rel_color = reliability_str == "High" ? color.green : (reliability_str == "Medium" ? color.orange : color.red)
        table.cell(prob_table, 1, 8, reliability_str, bgcolor=color.new(color.gray, 90), text_color=rel_color, text_size=size.small)

        table.cell(prob_table, 0, 9, "London High:", bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.small)
        table.cell(prob_table, 1, 9, str.tostring(london_high, "#.##"), bgcolor=color.new(color.red, 90), text_color=color.white, text_size=size.small)

    else if not ny_session
        // Clear table when not in NY session
        table.clear(prob_table, 0, 0, 1, 9)
'''

    # Write the script to file
    with open(output_file, 'w') as f:
        f.write(pine_script)

    print(f"\n✓ PineScript generated: {output_file}")
    print(f"  Variants embedded: {len(variants)}")
    print(f"  Total lines: {len(pine_script.splitlines())}")
    print(f"  File size: {len(pine_script) / 1024:.2f} KB")

def main():
    """Main execution."""
    print("\n" + "="*80)
    print("TRADINGVIEW PINESCRIPT V5 GENERATOR")
    print("="*80)

    # Load probability map
    prob_map = load_probability_map()

    # Generate PineScript
    generate_pinescript(prob_map)

    print("\n" + "="*80)
    print("✓ PINESCRIPT GENERATION COMPLETE")
    print("="*80)

    print("\nUsage Instructions:")
    print("1. Open TradingView (tradingview.com)")
    print("2. Click 'Pine Editor' at the bottom")
    print("3. Copy the contents of NY_Probability_Map.pine")
    print("4. Paste into the Pine Editor")
    print("5. Click 'Add to Chart'")
    print("\nThe indicator will display:")
    print("  - Session boxes for Asia, London, and NY")
    print("  - London High/Low target lines")
    print("  - Live probability table during NY session (08:30-11:00)")
    print("  - Variant-specific probabilities based on real-time context")

if __name__ == '__main__':
    main()
