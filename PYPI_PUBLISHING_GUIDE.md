# 📦 PyPI Publishing Guide for SB Sync

This guide will help you publish the SB Sync package to PyPI (Python Package Index).

## 🚀 Quick Start

### 1. Prerequisites

- **PyPI Account**: Create an account at [pypi.org](https://pypi.org)
- **TestPyPI Account**: Create an account at [test.pypi.org](https://test.pypi.org) for testing
- **API Tokens**: Generate API tokens for both PyPI and TestPyPI

### 2. Install Publishing Tools

```bash
pip install --upgrade build twine
```

### 3. Build the Package

```bash
python -m build
```

This creates:
- `dist/sb_sync-1.5.3.tar.gz` (source distribution)
- `dist/sb_sync-1.5.3-py3-none-any.whl` (wheel distribution)

### 4. Check the Package

```bash
twine check dist/*
```

### 5. Test Upload to TestPyPI

```bash
# Upload to TestPyPI first
twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ sb-sync
```

### 6. Upload to PyPI

```bash
# Upload to PyPI
twine upload dist/*
```

## 🔧 Configuration

### PyPI API Token Setup

1. **Create API Token**:
   - Go to [pypi.org](https://pypi.org)
   - Login to your account
   - Go to Account Settings → API tokens
   - Create a new token with "Entire account" scope

2. **Configure Credentials**:
   ```bash
   # Create .pypirc file in your home directory
   cat > ~/.pypirc << EOF
   [distutils]
   index-servers =
       pypi
       testpypi

   [pypi]
   repository = https://upload.pypi.org/legacy/
   username = __token__
   password = pypi-<your-token-here>

   [testpypi]
   repository = https://test.pypi.org/legacy/
   username = __token__
   password = pypi-<your-test-token-here>
   EOF
   ```

### Environment Variables (Alternative)

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-<your-token-here>
```

## 📋 Publishing Checklist

### Before Publishing

- [ ] **Version Updated**: Check `sb_sync/__init__.py` and `setup.py`
- [ ] **Changelog Updated**: Update README.md with new version
- [ ] **Tests Pass**: Run `python -m pytest`
- [ ] **Package Builds**: Run `python -m build`
- [ ] **Package Checks**: Run `twine check dist/*`
- [ ] **TestPyPI Upload**: Upload to TestPyPI first
- [ ] **TestPyPI Installation**: Test installation from TestPyPI

### Publishing Steps

1. **Update Version**:
   ```bash
   # Update version in __init__.py and setup.py
   # Commit changes
   git add .
   git commit -m "bump: Version X.Y.Z"
   git tag vX.Y.Z
   git push origin main --tags
   ```

2. **Build Package**:
   ```bash
   python -m build
   ```

3. **Check Package**:
   ```bash
   twine check dist/*
   ```

4. **Test Upload**:
   ```bash
   twine upload --repository testpypi dist/*
   ```

5. **Test Installation**:
   ```bash
   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ sb-sync
   ```

6. **Upload to PyPI**:
   ```bash
   twine upload dist/*
   ```

## 🎯 Package Information

### Current Package Details

- **Name**: `sb-sync`
- **Version**: `1.5.3`
- **Author**: TheSocialBytes
- **License**: MIT
- **Homepage**: https://github.com/TheSocialBytes/sync
- **Documentation**: https://github.com/TheSocialBytes/sync/blob/main/README.md

### Package Features

- **Django Integration**: Full Django app with models, views, admin
- **Web Interface**: Bootstrap 5-based configuration interface
- **Audit Trails**: Django Simple History integration
- **Multi-tenant**: Organization-based data isolation
- **RBAC**: Role-based access control
- **Management Commands**: Custom Django commands
- **Templates**: HTML templates for web interface
- **Tests**: Comprehensive test suite

### Dependencies

**Core Dependencies**:
- Django>=3.2,<5.3
- djangorestframework>=3.14.0
- PyJWT>=2.6.0
- django-simple-history>=3.4.0
- celery>=5.2.0
- redis>=4.0.0

**Optional Dependencies**:
- `[dev]`: Development tools (pytest, black, flake8, etc.)
- `[test]`: Testing tools
- `[docs]`: Documentation tools
- `[security]`: Security tools
- `[performance]`: Performance monitoring tools
- `[monitoring]`: Monitoring tools

## 🔍 Troubleshooting

### Common Issues

1. **Authentication Errors**:
   ```bash
   # Check your .pypirc file
   cat ~/.pypirc
   
   # Or use environment variables
   export TWINE_USERNAME=__token__
   export TWINE_PASSWORD=pypi-<your-token>
   ```

2. **Package Name Conflicts**:
   - Check if `sb-sync` is available on PyPI
   - If not, consider alternative names like `django-sb-sync`

3. **Build Errors**:
   ```bash
   # Clean build artifacts
   rm -rf build/ dist/ *.egg-info/
   
   # Rebuild
   python -m build
   ```

4. **Upload Errors**:
   ```bash
   # Check package metadata
   twine check dist/*
   
   # Test upload to TestPyPI first
   twine upload --repository testpypi dist/*
   ```

### Version Management

```bash
# Update version in multiple files
sed -i '' 's/version=.*/version="1.5.4",/' setup.py
sed -i '' 's/version = .*/version = "1.5.4"/' pyproject.toml
sed -i '' "s/__version__ = .*/__version__ = '1.5.4'/" sb_sync/__init__.py

# Commit and tag
git add .
git commit -m "bump: Version 1.5.4"
git tag v1.5.4
git push origin main --tags
```

## 📊 Post-Publishing

### Verification

1. **Check PyPI Page**: Visit https://pypi.org/project/sb-sync/
2. **Test Installation**: `pip install sb-sync`
3. **Test Import**: `python -c "import sb_sync; print(sb_sync.__version__)"`

### Monitoring

- **Download Statistics**: Check PyPI download stats
- **User Feedback**: Monitor GitHub issues
- **Version Compatibility**: Test with different Django versions

### Maintenance

- **Regular Updates**: Keep dependencies updated
- **Security Updates**: Monitor for security vulnerabilities
- **Documentation**: Keep README and docs updated
- **Changelog**: Maintain comprehensive changelog

## 🎉 Success!

Once published, users can install your package with:

```bash
# Basic installation
pip install sb-sync

# With optional dependencies
pip install sb-sync[dev]
pip install sb-sync[test]
pip install sb-sync[docs]
```

The package will be available at: https://pypi.org/project/sb-sync/ 