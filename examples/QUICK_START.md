# Quick Start: Running Examples

## ✅ Simple 3-Step Process

### Step 1: Build the Project
```bash
npm run build
```

### Step 2: Install ts-node (if needed)
```bash
npm install --save-dev ts-node
```

### Step 3: Run Any Example
```bash
npx ts-node examples/01-basic-extraction.ts
```

## 📝 All Available Examples

```bash
# Basic Examples
npx ts-node examples/01-basic-extraction.ts          # Basic usage
npx ts-node examples/02-detailed-extraction.ts        # Detailed metadata
npx ts-node examples/03-batch-extraction.ts           # Batch processing

# Advanced Features
npx ts-node examples/04-address-validation.ts         # Validation
npx ts-node examples/05-address-formatting.ts       # Formatting
npx ts-node examples/06-address-comparison.ts        # Comparison
npx ts-node examples/07-address-suggestions.ts       # Autocomplete
npx ts-node examples/09-address-enrichment.ts         # Enrichment
npx ts-node examples/10-statistics-analytics.ts      # Statistics

# Configuration
npx ts-node examples/11-confidence-thresholds.ts     # Thresholds
npx ts-node examples/12-strict-thresholds-090.ts    # Strict mode (0.90)
```

## 🎯 Example Output

When you run `01-basic-extraction.ts`, you'll see:

```
=== Example 1: Simple Address ===
Input: House 12, Road 5, Mirpur, Dhaka-1216
Extracted Components:
  House Number: 12
  Road: Road 5
  Area: Mirpur
  District: Dhaka
  Postal Code: 1216
  Confidence: 98.2%
  Extraction Time: 108.29ms
```

## 🔧 Troubleshooting

**Error: "Cannot find module"**
- Make sure you ran `npm run build` first
- Check that `dist/index.js` exists

**Error: "ts-node not found"**
- Run: `npm install --save-dev ts-node`
- Or use: `npx ts-node` (works without installation)

**Error: "Python script not found"**
- Install Python dependencies: `npm run install-python-deps`

## 💡 Tips

- **Run from project root**: Always run commands from the project root directory
- **Build first**: Always run `npm run build` after making changes
- **Check Python**: Make sure Python 3.9+ is installed and accessible

## 📚 More Information

- See [examples/README.md](./README.md) for detailed documentation
- See [../README.md](../README.md) for complete package documentation
