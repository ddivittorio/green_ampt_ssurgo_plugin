# Contributing to Green-Ampt Parameter Generator QGIS Plugin

Thank you for your interest in contributing to the Green-Ampt Parameter Generator QGIS Plugin!

## 🏗️ Project Structure

This project consists of two main components:

1. **QGIS Plugin** (`green_ampt_plugin/`): The QGIS integration layer
2. **Core Tool** (`green-ampt-estimation/`): The underlying parameter estimation logic

## 🤝 How to Contribute

### Reporting Issues

- Use the [GitHub Issues](https://github.com/ddivittorio/green_ampt_ssurgo_plugin/issues) tracker
- Include QGIS version, operating system, and error messages
- Provide steps to reproduce the issue
- If possible, include a minimal test case

### Contributing Code

1. **Fork the Repository**
   ```bash
   git clone --recursive https://github.com/YOUR_USERNAME/green_ampt_ssurgo_plugin.git
   cd green_ampt_ssurgo_plugin
   ```

2. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Your Changes**
   - Follow the existing code style
   - Add docstrings to new functions/classes
   - Test your changes in QGIS

4. **Verify Your Changes**
   ```bash
   python3 verify_plugin.py
   ```

5. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "Add: your descriptive commit message"
   ```

6. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a pull request on GitHub.

## 📝 Contribution Guidelines

### Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add comments for complex logic
- Keep functions focused and small

### QGIS Plugin Guidelines

- Use QGIS Processing framework conventions
- Properly handle CRS transformations
- Use QgsProcessingFeedback for user feedback
- Handle errors gracefully with QgsProcessingException

### Documentation

- Update README.md if you add new features
- Add docstrings to new classes and methods
- Update help text in the algorithm if needed
- Consider adding examples for new functionality

### Testing

- Test your changes in QGIS 3.18+ (minimum version)
- Test with both PySDA and local SSURGO sources
- Test all three parameter estimation methods
- Test edge cases (empty AOI, invalid CRS, etc.)

## 🔍 Where to Contribute

### Plugin Improvements (This Repository)

Suitable contributions include:
- New QGIS Processing algorithms
- UI/UX improvements
- Parameter validation enhancements
- Error handling improvements
- Documentation updates
- Installation scripts
- Test data and examples

### Core Functionality (green-ampt-estimation Repository)

For changes to the core parameter estimation logic, contribute to:
[green-ampt-estimation repository](https://github.com/ddivittorio/green-ampt-estimation)

Examples:
- New parameter estimation methods
- New soil data sources
- Calculation improvements
- Performance optimizations
- Bug fixes in core processing

## 🧪 Testing Your Plugin Changes

### Manual Testing

1. Install your modified plugin:
   ```bash
   ./install_plugin.sh  # or install_plugin.bat on Windows
   ```

2. Restart QGIS

3. Test the algorithm with sample data:
   - Use `green-ampt-estimation/test_aoi/test_aoi.shp` as AOI
   - Try different parameter methods
   - Verify outputs are generated correctly

### Verification Script

Run the verification script to check plugin structure:
```bash
python3 verify_plugin.py
```

## 📦 Release Process

For maintainers releasing new versions:

1. Update version in `green_ampt_plugin/metadata.txt`
2. Update changelog in `green_ampt_plugin/metadata.txt`
3. Update README.md if needed
4. Create a git tag:
   ```bash
   git tag -a v1.0.1 -m "Release version 1.0.1"
   git push origin v1.0.1
   ```
5. Create a GitHub release with the tag
6. Package the plugin:
   ```bash
   zip -r green_ampt_plugin_v1.0.1.zip green_ampt_plugin/ -x "*.pyc" -x "*__pycache__*"
   ```
7. Upload to QGIS Plugin Repository (if applicable)

## 🐛 Known Issues and TODOs

Check the [Issues](https://github.com/ddivittorio/green_ampt_ssurgo_plugin/issues) page for:
- Known bugs
- Feature requests
- Enhancement ideas
- Good first issues for new contributors

## 💬 Questions?

- Open a [GitHub Discussion](https://github.com/ddivittorio/green_ampt_ssurgo_plugin/discussions)
- Email: damien.divittorio@gmail.com

## 📄 License

By contributing, you agree that your contributions will be licensed under the same license as the project (GPL-3.0).

Thank you for contributing! 🎉
