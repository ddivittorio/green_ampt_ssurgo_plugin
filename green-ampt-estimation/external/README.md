# External Dependencies

This directory contains vendored third-party libraries that are included directly in the repository.

## Vendoring Approach

Following industry best practices for dependency management, this project vendors certain critical dependencies rather than requiring separate installation. This approach:

1. **Simplifies installation** - Users don't need to install additional packages or manage complex dependency chains
2. **Ensures compatibility** - Specific versions are tested and guaranteed to work
3. **Improves reliability** - Eliminates issues with package availability or version conflicts
4. **Maintains transparency** - Full source code and licenses are included

## Included Libraries

### PySDA (pysda/)

**Project:** Python interface to USDA-NRCS Soil Data Access  
**Author:** Charles Ferguson  
**Repository:** https://github.com/ncss-tech/pysda  
**License:** GNU General Public License v3.0 (see pysda/LICENSE)  
**Version:** Vendored from upstream repository

#### What is PySDA?

PySDA provides programmatic access to the USDA Natural Resources Conservation Service (NRCS) Soil Data Access (SDA) web service, enabling Python applications to query SSURGO soil data directly from NRCS servers.

#### Why is it vendored?

- **Simplicity**: PySDA is not available on PyPI, requiring users to manually clone from GitHub
- **Stability**: Ensures a known-working version is always available
- **Integration**: Allows seamless fallback if PySDA isn't installed system-wide
- **Licensing**: GPL-3.0 is compatible with this project's GPL-3.0 license

#### How is it used?

The `green_ampt_tool.data_access` module imports PySDA for live SSURGO data queries:

```python
from pysda import sdapoly, sdatab

# Fetch map unit polygons for an area of interest
soils = sdapoly.gdf(aoi_geodataframe)

# Query component and horizon data
components = sdatab.tabular(sql_query)
```

See `green_ampt_tool/data_access.py` for the full implementation.

#### Updating the vendored copy

To update PySDA to a newer version:

1. Clone or download the latest version from https://github.com/ncss-tech/pysda
2. Replace the contents of `external/pysda/` with the new version
3. Ensure LICENSE and README.md are preserved
4. Test the integration thoroughly with `python -m pytest green_ampt_tool/tests/`
5. Update this README if the API or licensing changes

## License Compliance

All vendored libraries maintain their original license files and copyright notices. This project's GPL-3.0 license is compatible with all vendored dependencies. See [ACKNOWLEDGMENTS.md](../ACKNOWLEDGMENTS.md) for complete attribution information.

## Adding New Vendored Dependencies

If adding additional vendored libraries:

1. Ensure license compatibility (GPL-3.0 compatible)
2. Include the complete LICENSE file from the original project
3. Preserve all copyright notices and attributions
4. Document in this README and [ACKNOWLEDGMENTS.md](../ACKNOWLEDGMENTS.md)
5. Update [CITATION.cff](../CITATION.cff) to reference the dependency
6. Add loading logic that prefers system-installed versions over vendored copies
