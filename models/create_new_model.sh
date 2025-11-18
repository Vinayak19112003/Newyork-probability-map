#!/bin/bash
# Create New Model Variation Script

if [ -z "$1" ]; then
    echo "Usage: ./create_new_model.sh <model_name>"
    echo ""
    echo "Examples:"
    echo "  ./create_new_model.sh extended_ny/short_ny"
    echo "  ./create_new_model.sh four_factor/transition_30min"
    echo "  ./create_new_model.sh alt_sessions/traditional"
    exit 1
fi

MODEL_NAME=$1
MODEL_DIR="$MODEL_NAME"

echo "Creating new model: $MODEL_NAME"
echo "Directory: $MODEL_DIR"

# Create directory structure
mkdir -p "$MODEL_DIR/output"

# Copy base model scripts as template
echo "Copying template scripts from base_model..."
cp base_model/run_analysis.py "$MODEL_DIR/"
cp base_model/generate_pinescript.py "$MODEL_DIR/"
cp base_model/validation_analysis.py "$MODEL_DIR/"
cp base_model/config.py "$MODEL_DIR/"

# Create README template
cat > "$MODEL_DIR/README.md" << 'EOF'
# Model: [MODEL_NAME]

## Configuration

**Session Boundaries (America/New_York):**
- **Asia**: [TIME] - [TIME]
- **London**: [TIME] - [TIME]
- **NY**: [TIME] - [TIME]

[Add session description here]

## Variant Factors

### Factor 1: [Name]
- **Calculation**: [Description]
- **Classes**: [List classes]

### Factor 2: [Name]
- **Calculation**: [Description]
- **Classes**: [List classes]

[Add more factors as needed]

## Expected Variants

**Theoretical Maximum**: [X] × [Y] × [Z] = [Total] variants

## Configuration Changes from Base Model

```python
# List key changes to session times or parameters
SESSION_TIMES = {
    'asia_start': time(XX, XX),
    # ...
}

# Other changes
PARAMETER_NAME = VALUE
```

## Hypothesis

[What are you testing with this variation?]

## Expected Outcomes

[What do you expect to see different from base model?]

## Analysis Results

[Run analysis and fill in results]

### Data Coverage
- **Trading Days Analyzed**:
- **Date Range**:
- **Unique Variants**:

### Performance Metrics
- **Directional Edge**:
- **Mean Fail Rate**:
- **Stability Rate**:
- **Mean Drift**:

### Top Variants
1. [Variant name]: [samples], [P(High)]%
2. [Variant name]: [samples], [P(High)]%
3. [Variant name]: [samples], [P(High)]%

## Comparison to Base Model

| Metric | Base Model | This Model | Δ |
|--------|-----------|------------|---|
| Variants | 36 | ? | ? |
| Dir Edge | 5.52% | ? | ? |
| Fail Rate | 46.13% | ? | ? |
| Stability | 53.8% | ? | ? |

## Conclusions

[What did you learn?]

## Recommendation

[ ] Use in production
[ ] Needs refinement
[ ] Abandon approach

---

**Model Version**: 1.0
**Date Created**: [DATE]
**Status**: 🚧 Experimental
EOF

# Update README with model name
sed -i "s/\[MODEL_NAME\]/$MODEL_NAME/g" "$MODEL_DIR/README.md"
sed -i "s/\[DATE\]/$(date +%Y-%m-%d)/g" "$MODEL_DIR/README.md"

# Create placeholder config with reminder
cat >> "$MODEL_DIR/config.py" << EOF

# ============================================================================
# TODO: CUSTOMIZE THIS CONFIGURATION FOR $MODEL_NAME
# ============================================================================

# 1. Update SESSION_TIMES with your session boundaries
# 2. Update FACTOR_COUNT and FACTORS if adding/removing factors
# 3. Update EXPECTED_VARIANTS calculation
# 4. Update MODEL_INFO metadata
# 5. Modify run_analysis.py if logic changes are needed

EOF

echo ""
echo "✓ Model template created: $MODEL_DIR"
echo ""
echo "Next steps:"
echo "1. cd $MODEL_DIR"
echo "2. Edit config.py with your session times and parameters"
echo "3. Edit run_analysis.py if you need custom logic"
echo "4. Run: python3 run_analysis.py"
echo "5. Run: python3 validation_analysis.py"
echo "6. Run: python3 generate_pinescript.py"
echo "7. Document results in README.md"
echo "8. Compare to base: cd .. && python3 compare_models.py"
echo ""
echo "Happy experimenting! 🚀"
