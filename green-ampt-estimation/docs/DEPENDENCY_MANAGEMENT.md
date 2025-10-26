# Dependency Management Strategy

This document explains the dependency management approach used in the Green-Ampt Estimation Toolkit and how it follows industry best practices.

## Overview

The project uses a **hybrid dependency management strategy**:

1. **Standard Python dependencies** (geopandas, rasterio, etc.) are specified in `requirements.txt` and installed via pip/conda
2. **PySDA** is vendored (included directly) in `external/pysda/`

## Why Vendor PySDA?

### Problem Context

PySDA is a critical dependency for this toolkit's live SSURGO data access feature, but it presents several challenges:

- **Not available on PyPI**: PySDA must be manually cloned from GitHub
- **No versioning**: No tagged releases or version numbers
- **Installation complexity**: Requires users to manually add to Python path
- **Maintenance**: GitHub repository may change or become unavailable

### Industry-Standard Solutions

The Python community recognizes several valid approaches for handling such dependencies:

#### 1. **Vendoring (Our Approach)** ✅

**Definition**: Including a complete copy of the dependency's source code in the project repository.

**Industry Examples**:
- **pip** vendors six, colorama, and other libraries
- **requests** vendors urllib3, chardet, idna
- **setuptools** vendors packaging, pyparsing
- Many Django apps vendor JavaScript libraries

**Benefits**:
- ✅ Simplified installation (works out-of-the-box)
- ✅ Version stability (guaranteed compatibility)
- ✅ Offline capability (no internet required after clone)
- ✅ Reliability (doesn't depend on external availability)

**Best Practices Followed**:
- ✅ Complete LICENSE file preserved (`external/pysda/LICENSE`)
- ✅ Original README maintained (`external/pysda/README.md`)
- ✅ Clear documentation of vendoring (`external/README.md`)
- ✅ Proper attribution in code comments
- ✅ License compatibility verified (GPL-3.0 ↔ GPL-3.0)
- ✅ Fallback logic that prefers system installations

#### Alternative Approaches Considered

**Git Submodules**: ❌ Not chosen because:
- Requires extra commands (`git submodule update --init`)
- Breaks ZIP downloads from GitHub
- Complicates CI/CD pipelines
- Users frequently forget to initialize submodules

**Direct Git Dependency**: ❌ Not chosen because:
- Requires internet connection during installation
- No version pinning (upstream changes can break compatibility)
- More complex installation instructions
- Doesn't work well with conda environments

**Require Manual Installation**: ❌ Not chosen because:
- Poor user experience (multi-step setup)
- Frequent support requests
- Barrier to adoption
- Inconsistent across environments

## License Compliance

### Compatibility Analysis

**This Project**: GNU GPL v3.0  
**PySDA**: GNU GPL v3.0

✅ **Fully Compatible**: GPL-3.0 allows:
- Using GPL code in GPL projects
- Distributing modified versions (with source)
- Commercial use
- Vendoring (explicit inclusion of source)

### Attribution Requirements Met

Per GPL-3.0 Section 5, we maintain:

1. ✅ **Prominent notices** of PySDA's license
2. ✅ **Intact copyright notices** (preserved in `external/pysda/`)
3. ✅ **Clear indication** of vendored status (README, ACKNOWLEDGMENTS)
4. ✅ **Source code availability** (included in repository)

## Implementation Details

### Import Strategy

The import logic in `green_ampt_tool/data_access._import_pysda_modules()`:

```python
def _import_pysda_modules():
    try:
        # Prefer system-installed version
        from pysda import sdapoly, sdatab
        return sdapoly, sdatab
    except ImportError:
        # Fall back to vendored copy
        fallback = Path(__file__).parent.parent / "external" / "pysda"
        if fallback.exists():
            sys.path.insert(0, str(fallback.parent))
            import importlib
            sdapoly = importlib.import_module("pysda.sdapoly")
            sdatab = importlib.import_module("pysda.sdatab")
            return sdapoly, sdatab
        raise
```

**Benefits of this approach**:
- Users with system-installed PySDA use their version (respects user choice)
- New users get working installation immediately
- Explicit fallback mechanism (transparent behavior)
- No hidden modifications to sys.path

### Updating Vendored PySDA

When PySDA upstream updates:

1. Download latest from https://github.com/ncss-tech/pysda
2. Replace contents of `external/pysda/`
3. Verify LICENSE and README are current
4. Test imports: `python -c "from green_ampt_tool.data_access import _import_pysda_modules; _import_pysda_modules()"`
5. Run full test suite: `pytest green_ampt_tool/tests/`
6. Update `external/README.md` if API changes
7. Commit with clear message: "Update vendored PySDA to [date/commit]"

## References

- [Python Packaging Guide on Vendoring](https://packaging.python.org/guides/single-sourcing-package-version/)
- [Vendoring Practices in Major Projects](https://www.b-list.org/weblog/2020/jan/05/packaging/)
- [GPL-3.0 License Requirements](https://www.gnu.org/licenses/gpl-3.0.en.html)
- [Software Heritage - Ensuring Code Availability](https://www.softwareheritage.org/)

## Summary

The vendoring approach used in this project:

✅ **Follows industry standards** from major Python projects  
✅ **Complies with licensing requirements** (GPL-3.0)  
✅ **Provides excellent user experience** (works immediately)  
✅ **Maintains proper attribution** (CITATION.cff, ACKNOWLEDGMENTS.md)  
✅ **Documents the approach** (this file, external/README.md)  
✅ **Respects user choice** (prefers system installations)  

This is a **best-practice implementation** of dependency vendoring for Python projects.
