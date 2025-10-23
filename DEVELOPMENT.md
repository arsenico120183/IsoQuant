# IsoQuant - Developer Guide

Guide for developers who want to contribute to or modify IsoQuant.

---

## Table of Contents

1. [Architecture](#architecture)
2. [Setup Development Environment](#setup-development-environment)
3. [Code Structure](#code-structure)
4. [Key Components](#key-components)
5. [Building](#building)
6. [Contributing](#contributing)

---

## Architecture

### Tech Stack

- **Language**: Python 3.11+
- **GUI**: Tkinter (built-in with Python)
- **Data Processing**: pandas, numpy
- **Visualization**: matplotlib
- **Excel I/O**: openpyxl
- **Packaging**: PyInstaller

### Design Pattern

IsoQuant uses a single-file GUI application pattern with:
- Class-based architecture for the main app window
- Functional programming for data processing utilities
- Event-driven GUI with Tkinter

---

## Setup Development Environment

### 1. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/IsoQuant.git
cd IsoQuant
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Development Tools

```bash
pip install pytest black flake8 mypy
```

### 5. Run Application

```bash
python src/iso_quant_app.py
```

---

## Code Structure

```
IsoQuant/
├── src/
│   └── iso_quant_app.py          # Main application (all code)
├── assets/                        # Icons, images
├── standards.xlsx                 # Reference standards data
├── requirements.txt               # Runtime dependencies
├── IsoQuant.spec                 # PyInstaller build config
├── build.bat                     # Windows build script
└── tests/                        # Unit tests (if added)
```

---

## Key Components

### Main Application Class

Located in `src/iso_quant_app.py`:

```python
class IsoQuantApp(tk.Tk):
    """Main application window"""

    def __init__(self):
        # Initialize GUI
        # Setup tabs
        # Load standards
```

### Standards Loading System

The configurable standards system:

```python
def load_standards_from_excel(excel_path="standards.xlsx"):
    """
    Loads standards from Excel file.

    Key features:
    - Searches in executable directory (PyInstaller compatible)
    - Falls back to defaults if file not found
    - Returns dict of {name: {18O: value, 2H: value}}
    """
```

**Important for PyInstaller:**
```python
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    application_path = os.path.dirname(sys.executable)
else:
    # Running as Python script
    application_path = os.path.dirname(os.path.abspath(__file__))
```

### Data Processing Pipeline

1. **CSV Loading**: `read_csv_robust()`
   - Handles multiple encodings
   - Auto-detects separators
   - Robust error handling

2. **Statistics Calculation**: `compute_stats()`
   - Calculates means and std dev
   - Applies quality control thresholds

3. **Calibration**: `fit_linear_with_r2()`
   - Linear regression for calibration curves
   - Returns slope, intercept, and R²

4. **Quantification**: Applies calibration to unknowns
   - Error propagation
   - Multi-curve averaging

---

## Building

### Building Executable

#### Windows

```bash
# Using batch file
build.bat

# Or manually
python -m PyInstaller IsoQuant.spec --clean
```

#### Linux/Mac

```bash
pyinstaller IsoQuant.spec --clean
```

### PyInstaller Configuration

Key settings in `IsoQuant.spec`:

```python
a = Analysis(
    ['src\\iso_quant_app.py'],
    datas=[('src', 'src'), ('standards.xlsx', '.')],  # Include data files
    hiddenimports=[],
    ...
)

exe = EXE(
    ...
    console=False,  # No console window (GUI only)
    ...
)
```

### Post-Build Steps

1. Copy `standards.xlsx` to `dist/` folder
2. Test executable with standard modifications
3. Verify all dependencies are included

---

## Contributing

### Coding Standards

- **Style**: Follow PEP 8
- **Formatting**: Use `black` for auto-formatting
- **Type Hints**: Add type hints where possible
- **Documentation**: Docstrings for all functions

### Before Submitting PR

1. **Format code:**
   ```bash
   black src/iso_quant_app.py
   ```

2. **Check style:**
   ```bash
   flake8 src/iso_quant_app.py
   ```

3. **Test manually:**
   - Run from source
   - Build executable
   - Test standards loading
   - Test data processing

### Pull Request Guidelines

1. Create feature branch from `main`
2. Make focused, atomic commits
3. Write clear commit messages
4. Update documentation if needed
5. Test thoroughly before submitting

---

## Common Development Tasks

### Adding a New Feature

1. Identify where in the code to add feature
2. Test with Python script first
3. Rebuild executable to test
4. Update documentation

### Modifying Standards System

The standards loading is in `load_standards_from_excel()`. Key points:

- Must work both in script and executable mode
- Should handle missing files gracefully
- Defaults are hardcoded as fallback

### Adding Dependencies

1. Add to `requirements.txt`
2. Test installation: `pip install -r requirements.txt`
3. Update README if it's a major dependency
4. Rebuild with PyInstaller to ensure it's packaged

### Debugging PyInstaller Builds

If executable doesn't work:

1. **Enable console output:**
   ```python
   # In IsoQuant.spec
   exe = EXE(..., console=True, ...)
   ```

2. **Check for missing imports:**
   - Look at `build/IsoQuant/warn-IsoQuant.txt`

3. **Test data file paths:**
   - Print paths at runtime
   - Verify `sys.frozen` detection works

---

## Testing

### Manual Testing Checklist

- [ ] Application launches
- [ ] Standards load from Excel
- [ ] Can modify standards in Excel
- [ ] CSV files load correctly
- [ ] Calibration curves calculate
- [ ] Quantification works
- [ ] Export to Excel works
- [ ] Modified standards persist across restarts

### Future: Automated Testing

Consider adding:
- Unit tests for data processing functions
- Integration tests for full pipeline
- Test fixtures with sample data

---

## Troubleshooting Development Issues

### Import Errors

**Problem**: Module not found when running script

**Solution**: Ensure virtual environment is activated and dependencies installed

### PyInstaller Build Fails

**Problem**: Build errors or warnings

**Solution**:
1. Clear build cache: `python -m PyInstaller --clean`
2. Check `warn-IsoQuant.txt` for missing modules
3. Add hidden imports to `.spec` file if needed

### Standards Not Loading in Executable

**Problem**: Exe uses defaults, ignores Excel file

**Solution**:
1. Verify `standards.xlsx` is in same folder as .exe
2. Check `sys.frozen` detection in code
3. Add debug prints to see what path is being checked

---

## Resources

- [Tkinter Documentation](https://docs.python.org/3/library/tkinter.html)
- [PyInstaller Manual](https://pyinstaller.org/)
- [pandas Documentation](https://pandas.pydata.org/)
- [matplotlib Documentation](https://matplotlib.org/)

---

**Last Updated:** October 2024
