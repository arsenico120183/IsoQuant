# IsoQuant - User Guide

This guide explains how to use IsoQuant for isotope data analysis.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Configuring Standards](#configuring-standards)
3. [Loading Data](#loading-data)
4. [Running Analysis](#running-analysis)
5. [Exporting Results](#exporting-results)
6. [Troubleshooting](#troubleshooting)

---

## Getting Started

### First Launch

1. **Locate IsoQuant.exe** (or run `python src/iso_quant_app.py`)
2. **Ensure `standards.xlsx` is in the same folder** as the executable
3. **Double-click to launch**

At startup, you'll see a message indicating which standards were loaded:
```
Cerco il file Excel in: C:\...\standards.xlsx
Caricati 4 standard da C:\...\standards.xlsx
```

---

## Configuring Standards

### Understanding the Standards File

The `standards.xlsx` file contains reference standards used for calibration. Each standard has:
- **Name**: Identifier (e.g., "ORMEA", "SSW")
- **δ18O value**: Oxygen isotope ratio (‰)
- **δ2H value**: Hydrogen isotope ratio (‰)

### Adding a New Standard

1. **Close IsoQuant** (if running)
2. **Open `standards.xlsx`** in Excel
3. **Go to the "Standards" sheet**
4. **Add a new row** with your standard data:
   ```
   Standard Name  |  d18O (‰)  |  d2H (‰)
   ALPINE         |  -15.0     |  -110.0
   ```
5. **Save the file** (Ctrl+S)
6. **Restart IsoQuant**

Your new standard will appear in the application!

### Modifying Existing Standards

1. Open `standards.xlsx`
2. Locate the standard you want to modify
3. Change the δ18O and/or δ2H values
4. Save and restart IsoQuant

### Important Notes

- ✅ Standard names are automatically converted to UPPERCASE
- ✅ Spaces in names are removed automatically
- ✅ You can have as many standards as you need
- ❌ Don't modify the header row (row 1)
- ❌ Don't leave blank rows between standards

---

## Loading Data

### Supported File Formats

- **CSV files** with comma, semicolon, or tab separators
- Files must contain columns for isotope measurements

### Loading Your Data

1. Click **"Load CSV"** or use the File menu
2. Select your data file
3. IsoQuant will automatically detect:
   - File encoding (UTF-8, Latin-1, etc.)
   - Separator type
   - Column headers

### Expected Data Format

Your CSV should include columns for:
- Sample identifiers
- δ18O measurements
- δ2H measurements
- H2O concentrations (if applicable)

---

## Running Analysis

### Step 1: Raw Data Processing

After loading your CSV:
1. The application processes raw measurements
2. Calculates means and standard deviations
3. Groups measurements by sample

### Step 2: Calibration

1. Open the **Calibration** tab
2. The application automatically:
   - Identifies standard samples
   - Calculates calibration curves for δ18O and δ2H
   - Displays R² values and equations
3. Review the calibration plots

### Step 3: Quantification

1. Open the **Quantification** tab
2. Unknown samples are quantified using the calibration curves
3. Results include:
   - Calibrated δ18O and δ2H values
   - Standard deviations
   - Error propagation

---

## Exporting Results

### Export Options

1. Click **"Export"** button
2. Choose export location and filename
3. Results are saved as Excel (.xlsx) format

### Exported Data Includes

- **Raw Means**: Processed raw data with statistics
- **Calibration**: Curve parameters and standards used
- **Quantification**: Final calibrated values for unknowns

---

## Troubleshooting

### Problem: Standards Not Loading

**Symptoms:**
- Application shows "Uso valori di default"
- Your custom standards don't appear

**Solutions:**
1. Check that `standards.xlsx` is in the same folder as IsoQuant.exe
2. Verify the sheet name is "Standards" (with capital S)
3. Ensure there are no blank rows in the standards table
4. Check for Excel file corruption - try recreating it

---

### Problem: Data File Won't Load

**Symptoms:**
- Error message when loading CSV
- Blank screen after file selection

**Solutions:**
1. Check file encoding (try UTF-8)
2. Verify separator (comma, semicolon, tab)
3. Ensure column headers are present
4. Check for special characters in headers

---

### Problem: Calibration Curves Look Wrong

**Symptoms:**
- Very low R² values
- Curves don't fit the data

**Solutions:**
1. Verify standard values in `standards.xlsx` are correct
2. Check that standard samples are properly identified in your data
3. Ensure sufficient standard measurements (minimum 3 points)
4. Look for outliers in raw data

---

### Problem: Application Won't Start

**Symptoms:**
- Double-click does nothing
- Error message on launch

**Solutions:**
1. **If using .exe**: Ensure all DLLs are present (don't separate files from dist folder)
2. **If using Python**: Check all dependencies are installed (`pip install -r requirements.txt`)
3. Check for missing `standards.xlsx` - application will still run with defaults
4. Review console output for error messages

---

## Tips and Best Practices

### Data Organization

- ✅ Use consistent naming for standards in your data files
- ✅ Include sufficient replicate measurements
- ✅ Organize samples logically (standards first, then unknowns)

### Standards Management

- ✅ Keep a backup copy of `standards.xlsx`
- ✅ Document any changes to standard values
- ✅ Use meaningful names for custom standards

### Quality Control

- ✅ Always review calibration R² values (should be > 0.99)
- ✅ Check standard deviations are within acceptable limits
- ✅ Compare results with known reference materials

---

## Advanced Features

### Modifying Target Standards in Session

You can temporarily modify standard target values:
1. Go to menu option for target modification
2. Change values for the current session
3. Note: These changes are temporary unless you update `standards.xlsx`

### Multiple Calibration Curves

The application can handle multiple calibration curves if your data includes multiple standard sets.

---

## Getting Help

If you encounter issues not covered here:

1. Check the main [README.md](README.md)
2. Open an issue on GitHub
3. Review the application's console output for error messages

---

**Last Updated:** October 2024
