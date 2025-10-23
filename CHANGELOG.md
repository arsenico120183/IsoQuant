# Changelog

All notable changes to IsoQuant will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.1.0] - 2024-10

### Added

- **Configurable Reference Standards System**
  - Standards are now loaded from external Excel file (`standards.xlsx`)
  - Users can add, modify, or remove standards without changing code
  - Standards persist across application restarts
  - Automatic detection of executable vs script mode for file paths

- **Documentation**
  - Comprehensive README.md for GitHub
  - USAGE.md with detailed user instructions
  - DEVELOPMENT.md for contributors
  - QUICKSTART.md for new users
  - Inline code documentation

### Changed

- Standards are no longer hardcoded in the application
- Application now searches for `standards.xlsx` in executable directory
- Improved error handling for missing or corrupted standards file
- Enhanced console output for debugging standards loading

### Fixed

- PyInstaller executable now correctly reads external `standards.xlsx`
- Path resolution works correctly in both development and production modes

---

## [1.0.0] - Earlier

### Initial Release

- CSV data import with auto-detection of format
- Raw data processing and statistics
- Calibration curve calculation for δ18O and δ2H
- Sample quantification with error propagation
- Data visualization with matplotlib
- Excel export functionality
- Built-in reference standards (NIVOLET, ORMEA, H2OPI, SSW)

---

## Future Plans

### Planned Features

- [ ] Additional export formats (CSV, JSON)
- [ ] Batch processing of multiple files
- [ ] Advanced plotting options
- [ ] Quality control reports
- [ ] Configuration file for application settings
- [ ] Support for additional isotope systems

### Under Consideration

- [ ] Database integration for sample tracking
- [ ] Cloud storage integration
- [ ] Multi-language support
- [ ] Automated standard library updates
- [ ] Web-based version

---

## Version History

- **1.1.0** - Configurable standards system
- **1.0.0** - Initial release

---

**Note:** For detailed commit history, see the [GitHub repository](https://github.com/YOUR_USERNAME/IsoQuant/commits/).
