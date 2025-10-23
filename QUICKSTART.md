# IsoQuant - Quick Start Guide

Get up and running with IsoQuant in 5 minutes!

---

## For Users

### Option 1: Download Pre-built Executable (Easiest)

1. **Download** the latest release from GitHub
2. **Extract** the ZIP file
3. **Ensure** `IsoQuant.exe` and `standards.xlsx` are in the same folder
4. **Double-click** `IsoQuant.exe` to launch

That's it! 🎉

---

### Option 2: Run from Source

1. **Install Python 3.11+** if not already installed

2. **Download the source code:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/IsoQuant.git
   cd IsoQuant
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python src/iso_quant_app.py
   ```

---

## First Steps

### 1. Verify Standards are Loaded

When you launch IsoQuant, you should see a message:
```
Caricati 4 standard da ...standards.xlsx
```

This confirms the application loaded your reference standards.

---

### 2. Add Your Own Standard (Optional)

**Try this to test the system:**

1. **Close IsoQuant**
2. **Open `standards.xlsx`** in Excel
3. **Go to "Standards" sheet**
4. **Add a new row:**
   - Column A: `TEST`
   - Column B: `-10.0`
   - Column C: `-70.0`
5. **Save and close** Excel
6. **Restart IsoQuant**
7. **Check** - you should now see 5 standards loaded!

---

### 3. Load Your Data

1. Click **"Load CSV"** or **File → Open**
2. Select your isotope data file
3. The application will:
   - Auto-detect the file format
   - Process raw data
   - Show statistics in the first tab

---

### 4. View Calibration

1. Click the **"Calibration"** tab
2. Review:
   - Calibration curves for δ18O and δ2H
   - R² values (should be > 0.99)
   - Regression equations

---

### 5. Get Results

1. Click the **"Quantification"** tab
2. View calibrated values for your samples
3. Click **"Export"** to save results as Excel

---

## Common Questions

### Where do I put my data files?

Anywhere! Use the "Load CSV" button to browse to your files.

### Can I use my own reference standards?

**Yes!** That's the whole point of the configurable system. Just edit `standards.xlsx`.

### What file format should my data be in?

CSV files with headers. The application auto-detects:
- Separators (comma, semicolon, tab)
- Encoding (UTF-8, Latin-1, etc.)

### Do I need to rebuild the executable when I change standards?

**No!** Just edit `standards.xlsx` and restart the application.

---

## Next Steps

- Read [USAGE.md](USAGE.md) for detailed instructions
- Check [DEVELOPMENT.md](DEVELOPMENT.md) if you want to modify the code
- See [README.md](README.md) for complete documentation

---

## Getting Help

- Check the [Troubleshooting section](USAGE.md#troubleshooting) in USAGE.md
- Open an issue on GitHub
- Review console output for error messages

---

**Enjoy using IsoQuant!** 🚀
