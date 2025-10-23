# IsoQuant

**Raw Means, Calibration & Quantification for Isotope Analysis**

IsoQuant is a desktop application for processing and analyzing stable isotope data with configurable reference standards.

---

## 🌟 Features

- **Configurable Reference Standards** - Manage standards via Excel file without modifying code
- **Raw Data Processing** - Import and process isotope measurements from CSV files
- **Calibration Curves** - Automatic calculation of calibration curves (δ18O and δ2H)
- **Sample Quantification** - Apply calibration to unknown samples
- **Data Visualization** - Interactive plots with matplotlib
- **Export Results** - Export processed data to Excel format

---

## 📋 Requirements

- Python 3.11 or higher
- Dependencies listed in `requirements.txt`:
  - pandas
  - numpy
  - matplotlib
  - openpyxl

---

## 🚀 Installation

### Option 1: Run from Source

1. Clone this repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/IsoQuant.git
   cd IsoQuant
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python src/iso_quant_app.py
   ```

### Option 2: Build Executable

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Build the executable:
   ```bash
   # On Windows
   build.bat

   # On Linux/Mac
   pyinstaller IsoQuant.spec
   ```

3. Find the executable in the `dist/` folder

---

## 📖 Usage

### Configurable Standards

IsoQuant uses an Excel file (`standards.xlsx`) to manage reference standards. This allows you to:

- **Modify existing standards** without changing code
- **Add new standards** by simply editing the Excel file
- **Share standard configurations** across different labs

#### How to Add/Modify Standards:

1. Open `standards.xlsx` in Excel
2. Go to the "Standards" sheet
3. Add or modify rows with your standard data:
   - Column A: Standard Name (e.g., "ORMEA")
   - Column B: δ18O value (‰)
   - Column C: δ2H value (‰)
4. Save the file
5. Restart IsoQuant

The application will automatically load your standards at startup!

#### Default Standards Included:

| Standard | δ18O (‰) | δ2H (‰) |
|----------|----------|---------|
| NIVOLET  | -22.47   | -171.6  |
| ORMEA    | -11.52   | -77.9   |
| H2OPI    | -6.68    | -39.4   |
| SSW      | -0.54    | -2.2    |

---

## 📁 Project Structure

```
IsoQuant/
├── src/
│   └── iso_quant_app.py      # Main application
├── assets/                    # Images and resources
├── standards.xlsx             # Configurable reference standards
├── requirements.txt           # Python dependencies
├── IsoQuant.spec             # PyInstaller configuration
├── build.bat                 # Build script (Windows)
├── LICENSE                   # License file
└── README.md                 # This file
```

---

## 🔧 Building from Source

### Prerequisites

- Python 3.11+
- All requirements from `requirements.txt`
- PyInstaller for building executables

### Build Steps

```bash
# Install dependencies
pip install -r requirements.txt

# Install PyInstaller
pip install pyinstaller

# Build executable
python -m PyInstaller IsoQuant.spec --clean
```

The compiled executable will be in the `dist/` folder along with `standards.xlsx`.

---

## 📚 Documentation

### For Users

See `USAGE.md` for detailed instructions on:
- Loading data files
- Configuring standards
- Running calibrations
- Exporting results

### For Developers

See `DEVELOPMENT.md` for:
- Code architecture
- Contributing guidelines
- Building and testing

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

---

## 👤 Author

**Francesco Norelli**

---

## 🙏 Acknowledgments

- Built with Python, Tkinter, Pandas, NumPy, and Matplotlib
- Packaged with PyInstaller

---

## 📮 Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Version:** 1.1.0
**Last Updated:** October 2024
