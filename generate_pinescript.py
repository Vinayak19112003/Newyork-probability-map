#!/usr/bin/env python3
"""
TradingView PineScript v5 Generator (With Better Diagnostics)

Shows debug info about why probability table may not appear.
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

def filter_top_variants(prob_map, top_n=25):
    """Filter to only the most reliable variants."""
    sorted_variants = sorted(prob_map, key=lambda x: x['n'], reverse=True)
    top_variants = sorted_variants[:top_n]

    print(f"\nFiltered to top {len(top_variants)} variants by sample size")
    print(f"Sample size range: {top_variants[0]['n']} to {top_variants[-1]['n']}")

    return top_variants

def generate_pinescript(prob_map, output_file='NY_Probability_Map.pine'):
    """Generate the complete PineScript v5 indicator."""
    print("\n" + "="*80)
    print("GENERATING PINESCRIPT V5 INDICATOR")
    print("="*80)

    top_variants = filter_top_variants(prob_map, top_n=25)

    # Build variant data
    variant_strings = []
    variant_n = []
    variant_p_high = []
    variant_p_fail = []
    variant_pen_high = []
    variant_pen_low = []

    for v in top_variants:
        variant_strings.append(v['variant'])
        variant_n.append(v['n'])
        variant_p_high.append(v['first_high_pct'])
        variant_p_fail.append(v['fail_pct'])
        variant_pen_high.append(v['median_pen_high'] if v['median_pen_high'] is not None else 0.0)
        variant_pen_low.append(v['median_pen_low'] if v['median_pen_low'] is not None else 0.0)

    pine_script = '''// This source code is subject to the terms of the Mozilla Public License 2.0 at https://mozilla.org/MPL/2.0/
// © NY Probability Map - Top 25 Variants

//@version=5
indicator("NY Probability Map", overlay=true, max_boxes_count=500, max_labels_count=500)

// ============================================================================
// USER INPUTS
// ============================================================================

show_sessions = input.bool(true, "Show Session Boxes", group="Display")
show_london_levels = input.bool(true, "Show London Levels", group="Display")
show_prob_table = input.bool(true, "Show Probability Table", group="Display")
show_debug = input.bool(true, "Show Debug Info", group="Display")

asia_color = input.color(color.new(color.blue, 85), "Asia", group="Colors")
london_color = input.color(color.new(color.orange, 85), "London", group="Colors")
ny_color = input.color(color.new(color.green, 85), "NY", group="Colors")

asia_range_window = input.int(200, "Asia Range Window", minval=50, maxval=500, group="Analysis")

// ============================================================================
// TIME SESSIONS - Use exchange timezone
// ============================================================================

is_asia = not na(time(timeframe.period, "2000-0000:1234567", "America/New_York"))
is_london = not na(time(timeframe.period, "0200-0500:12345", "America/New_York"))
is_transition = not na(time(timeframe.period, "0500-0830:12345", "America/New_York"))
is_ny = not na(time(timeframe.period, "0830-1100:12345", "America/New_York"))

// ============================================================================
// VARIANT DATABASE (TOP 25 BY SAMPLE SIZE)
// ============================================================================

var int DB_SIZE = ''' + str(len(variant_strings)) + '''

var string[] db_variant = array.from('''

    # Add variants
    chunk_size = 5
    for i in range(0, len(variant_strings), chunk_size):
        chunk = variant_strings[i:i+chunk_size]
        if i > 0:
            pine_script += ',\n     '
        pine_script += ', '.join([f'"{v}"' for v in chunk])

    pine_script += ')\n\n'

    # Add numeric arrays
    pine_script += f'''var int[] db_n = array.from({', '.join(map(str, variant_n))})
var float[] db_p_high = array.from({', '.join(f'{x:.2f}' for x in variant_p_high)})
var float[] db_p_fail = array.from({', '.join(f'{x:.2f}' for x in variant_p_fail)})
var float[] db_pen_high = array.from({', '.join(f'{x:.2f}' for x in variant_pen_high)})
var float[] db_pen_low = array.from({', '.join(f'{x:.2f}' for x in variant_pen_low)})

// ============================================================================
// STATE VARIABLES
// ============================================================================

var float asia_h = na
var float asia_l = na
var float asia_r = na
var float london_h = na
var float london_l = na
var float london_m = na
var float london_r = na
var float trans_open = na
var float ny_open = na
var string current_variant = ""
var int variant_idx = -1
var float[] asia_history = array.new_float()

// Track session states
var bool asia_started = false
var bool london_started = false
var bool ny_started = false

// Debug info
var string debug_msg = ""

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

f_asia_regime(range_val) =>
    result = "Normal"
    if array.size(asia_history) >= 50
        sorted = array.copy(asia_history)
        array.sort(sorted)
        size = array.size(sorted)
        q33 = array.get(sorted, math.floor(size * 0.33))
        q66 = array.get(sorted, math.floor(size * 0.66))
        result := range_val < q33 ? "Compressed" : range_val > q66 ? "Expanded" : "Normal"
    result

f_london_sweep(lh, ll, ah, al) =>
    swept_h = lh > ah
    swept_l = ll < al
    swept_h and swept_l ? "Both" : swept_h ? "High" : swept_l ? "Low" : "None"

f_open_vs_london(open_price, lm, lr) =>
    tol = lr * 0.25
    open_price > lm + tol ? "Above" : open_price < lm - tol ? "Below" : "Within"

f_find_variant(var_str) =>
    idx = -1
    for i = 0 to DB_SIZE - 1
        if array.get(db_variant, i) == var_str
            idx := i
            break
    idx

// ============================================================================
// SESSION TRACKING
// ============================================================================

// Detect new trading day
new_day = ta.change(dayofweek)

// Reset on new day
if new_day
    asia_h := na
    asia_l := na
    asia_r := na
    london_h := na
    london_l := na
    london_m := na
    london_r := na
    trans_open := na
    ny_open := na
    current_variant := ""
    variant_idx := -1
    asia_started := false
    london_started := false
    ny_started := false
    debug_msg := ""

// Track Asia session
if is_asia
    asia_started := true
    asia_h := na(asia_h) ? high : math.max(asia_h, high)
    asia_l := na(asia_l) ? low : math.min(asia_l, low)

// Calculate Asia range at end of session
if not is_asia and asia_started and na(asia_r)
    asia_r := asia_h - asia_l
    if not na(asia_r) and asia_r > 0
        array.push(asia_history, asia_r)
        if array.size(asia_history) > asia_range_window
            array.shift(asia_history)

// Track London session
if is_london
    london_started := true
    london_h := na(london_h) ? high : math.max(london_h, high)
    london_l := na(london_l) ? low : math.min(london_l, low)

// Calculate London stats at end
if not is_london and london_started and na(london_m)
    if not na(london_h) and not na(london_l)
        london_m := (london_h + london_l) / 2
        london_r := london_h - london_l

// Capture Transition open (first bar at 05:00)
if is_transition and not is_transition[1] and na(trans_open)
    trans_open := open

// NY open and calculate variant
if is_ny and not is_ny[1] and na(ny_open)
    ny_started := true
    ny_open := open

    // Debug: Check what data we have
    debug_msg := "NY START:\\n"
    debug_msg := debug_msg + "Asia: " + (na(asia_r) ? "MISSING" : str.tostring(asia_r, "#.#")) + "\\n"
    debug_msg := debug_msg + "London H: " + (na(london_h) ? "MISSING" : str.tostring(london_h)) + "\\n"
    debug_msg := debug_msg + "London L: " + (na(london_l) ? "MISSING" : str.tostring(london_l)) + "\\n"
    debug_msg := debug_msg + "London M: " + (na(london_m) ? "MISSING" : str.tostring(london_m)) + "\\n"
    debug_msg := debug_msg + "Trans Open: " + (na(trans_open) ? "MISSING" : str.tostring(trans_open)) + "\\n"
    debug_msg := debug_msg + "Asia Hist: " + str.tostring(array.size(asia_history)) + " days\\n"

    // Calculate variant if all data available
    if not na(asia_r) and not na(london_h) and not na(london_l) and not na(london_m) and not na(trans_open) and not na(asia_h) and not na(asia_l) and london_r > 0

        asia_regime = f_asia_regime(asia_r)
        london_sweep = f_london_sweep(london_h, london_l, asia_h, asia_l)
        trans_vs_london = f_open_vs_london(trans_open, london_m, london_r)
        ny_vs_london = f_open_vs_london(ny_open, london_m, london_r)

        current_variant := asia_regime + "|" + london_sweep + "|" + trans_vs_london + "|" + ny_vs_london
        variant_idx := f_find_variant(current_variant)

        debug_msg := debug_msg + "\\nVariant: " + current_variant + "\\n"
        debug_msg := debug_msg + "Found: " + (variant_idx >= 0 ? "YES (idx=" + str.tostring(variant_idx) + ")" : "NO - Not in Top 25")
    else
        debug_msg := debug_msg + "\\nERROR: Missing required data!"

// ============================================================================
// VISUALIZATION
// ============================================================================

// Plot London levels (always visible during NY)
plot(is_ny and not na(london_h) ? london_h : na, "London High", color=color.red, linewidth=2, style=plot.style_line)
plot(is_ny and not na(london_l) ? london_l : na, "London Low", color=color.green, linewidth=2, style=plot.style_line)

// Background colors for sessions (more visible)
bgcolor(is_asia ? color.new(color.blue, 95) : na, title="Asia Session")
bgcolor(is_london ? color.new(color.orange, 95) : na, title="London Session")
bgcolor(is_ny ? color.new(color.green, 95) : na, title="NY Session")

// Debug label at NY open
if show_debug and is_ny and not is_ny[1]
    label.new(bar_index, high, debug_msg, style=label.style_label_down, color=color.blue, textcolor=color.white, size=size.small, textalign=text.align_left)

// ============================================================================
// PROBABILITY TABLE
// ============================================================================

var table info_table = table.new(position.top_right, 2, 10, border_width=1)

if show_prob_table and is_ny
    if variant_idx >= 0
        // Show probabilities
        n = array.get(db_n, variant_idx)
        p_high = array.get(db_p_high, variant_idx)
        p_low = 100.0 - p_high
        p_fail = array.get(db_p_fail, variant_idx)
        pen_h = array.get(db_pen_high, variant_idx)
        pen_l = array.get(db_pen_low, variant_idx)

        reliability = n >= 150 ? "High" : n >= 50 ? "Medium" : "Low"
        rel_color = n >= 150 ? color.green : n >= 50 ? color.orange : color.red

        table.cell(info_table, 0, 0, "NY PROBABILITY MAP", bgcolor=color.new(color.gray, 70), text_color=color.white, text_size=size.normal)
        table.merge_cells(info_table, 0, 0, 1, 0)

        table.cell(info_table, 0, 1, "P(High First):", bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.small)
        table.cell(info_table, 1, 1, str.tostring(p_high, "#.#") + "%", bgcolor=color.new(color.red, 80), text_color=color.white, text_size=size.large)

        table.cell(info_table, 0, 2, "P(Low First):", bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.small)
        table.cell(info_table, 1, 2, str.tostring(p_low, "#.#") + "%", bgcolor=color.new(color.green, 80), text_color=color.white, text_size=size.large)

        table.cell(info_table, 0, 3, "P(Fail):", bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.small)
        table.cell(info_table, 1, 3, str.tostring(p_fail, "#.#") + "%", bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.small)

        table.cell(info_table, 0, 4, "Penetration:", bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.small)
        table.cell(info_table, 1, 4, str.tostring(p_high > 50 ? pen_h : pen_l, "#.#") + " pts", bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.small)

        table.cell(info_table, 0, 5, "Sample Size:", bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.small)
        table.cell(info_table, 1, 5, str.tostring(n), bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.small)

        table.cell(info_table, 0, 6, "Reliability:", bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.small)
        table.cell(info_table, 1, 6, reliability, bgcolor=color.new(color.gray, 90), text_color=rel_color, text_size=size.small)

        table.cell(info_table, 0, 7, "London High:", bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.small)
        table.cell(info_table, 1, 7, str.tostring(london_h, format.mintick), bgcolor=color.new(color.red, 90), text_color=color.white, text_size=size.small)

        table.cell(info_table, 0, 8, "London Low:", bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.small)
        table.cell(info_table, 1, 8, str.tostring(london_l, format.mintick), bgcolor=color.new(color.green, 90), text_color=color.white, text_size=size.small)

        table.cell(info_table, 0, 9, "Variant:", bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.tiny)
        table.cell(info_table, 1, 9, current_variant, bgcolor=color.new(color.gray, 90), text_color=color.yellow, text_size=size.tiny)

    else
        // Show error message
        table.clear(info_table, 0, 0, 1, 9)
        table.cell(info_table, 0, 0, "DEBUG INFO", bgcolor=color.new(color.red, 70), text_color=color.white, text_size=size.normal)
        table.merge_cells(info_table, 0, 0, 1, 0)

        if current_variant != ""
            // Variant not found in top 25
            table.cell(info_table, 0, 1, "Status:", bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.small)
            table.cell(info_table, 1, 1, "Variant Not in Top 25", bgcolor=color.new(color.orange, 90), text_color=color.white, text_size=size.small)

            table.cell(info_table, 0, 2, "Variant:", bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.tiny)
            table.cell(info_table, 1, 2, current_variant, bgcolor=color.new(color.gray, 90), text_color=color.yellow, text_size=size.tiny)

            table.cell(info_table, 0, 3, "Note:", bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.tiny)
            table.cell(info_table, 1, 3, "This setup has <34 samples", bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.tiny)
        else
            // Missing data
            table.cell(info_table, 0, 1, "Status:", bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.small)
            table.cell(info_table, 1, 1, "Missing Data", bgcolor=color.new(color.red, 90), text_color=color.white, text_size=size.small)

            table.cell(info_table, 0, 2, "Check:", bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.tiny)
            table.cell(info_table, 1, 2, "See blue label below", bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.tiny)

else if not is_ny and show_prob_table
    table.clear(info_table, 0, 0, 1, 9)
    table.cell(info_table, 0, 0, "Waiting for NY Session (08:30 ET)...", bgcolor=color.new(color.gray, 90), text_color=color.white, text_size=size.small)
    table.merge_cells(info_table, 0, 0, 1, 0)
'''

    with open(output_file, 'w') as f:
        f.write(pine_script)

    print(f"\n✓ PineScript generated: {output_file}")
    print(f"  Variants: {len(top_variants)}")
    print(f"  Lines: {len(pine_script.splitlines())}")
    print(f"  Size: {len(pine_script) / 1024:.2f} KB")

def main():
    """Main execution."""
    print("\n" + "="*80)
    print("PINESCRIPT GENERATOR - WITH DIAGNOSTICS")
    print("="*80)

    prob_map = load_probability_map()
    generate_pinescript(prob_map)

    print("\n" + "="*80)
    print("✓ GENERATION COMPLETE")
    print("="*80)

    print("\n📊 DEBUG MODE IS NOW ENABLED BY DEFAULT")
    print("\nWhat you'll see at 08:30 ET:")
    print("  1. Blue label showing what data is available")
    print("  2. If variant found: Full probability table")
    print("  3. If variant NOT found: Reason why (missing data or not in top 25)")
    print("\nMost common issues:")
    print("  - Missing Asia session data (need prior day)")
    print("  - Missing London session data")
    print("  - Variant has <34 samples (not in top 25)")

if __name__ == '__main__':
    main()
