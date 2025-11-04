# Acknowledgments

## Third-Party Software

This project builds upon and includes software from the following open-source projects:

### PySDA - Python interface to USDA-NRCS Soil Data Access

**Author:** Charles Ferguson  
**Repository:** https://github.com/ncss-tech/pysda  
**License:** GNU General Public License v3.0  
**Location in this project:** `external/pysda/`

PySDA is a Python library that provides programmatic access to the USDA Natural Resources Conservation Service (NRCS) Soil Data Access (SDA) web service. This project vendors PySDA to enable live queries of SSURGO soil data directly from the NRCS servers without requiring manual data downloads.

**Key features used:**
- Spatial query functionality (`sdapoly.py`) for fetching SSURGO map unit polygons by area of interest
- Tabular query functionality (`sdatab.py`) for retrieving soil component and horizon data

**Integration approach:**  
PySDA is vendored in the `external/pysda/` directory as a complete copy of the source code, maintaining its original license and attribution. This approach was chosen to:
- Simplify installation by avoiding external dependencies
- Ensure compatibility with specific PySDA functionality needed for this toolkit
- Make the project immediately usable without additional setup steps

**Citation:**  
When using the PySDA data source in this toolkit, please acknowledge both this project and PySDA:

```
This analysis used the Green-Ampt Estimation Toolkit (https://github.com/ddivittorio/green-ampt-estimation), 
which incorporates PySDA (https://github.com/ncss-tech/pysda) for accessing USDA-NRCS Soil Data Access.
```

## Data Sources

### USDA-NRCS Soil Survey Geographic (SSURGO) Database

This toolkit processes data from the USDA Natural Resources Conservation Service Soil Survey Geographic (SSURGO) database, which is the most detailed level of soil mapping produced by the National Cooperative Soil Survey.

**Data provider:** USDA Natural Resources Conservation Service  
**Website:** https://www.nrcs.usda.gov/resources/data-and-reports/soil-survey-geographic-database-ssurgo  
**Access:** https://sdmdataaccess.nrcs.usda.gov/

Users should cite SSURGO data appropriately in their work:

```
Soil Survey Staff, Natural Resources Conservation Service, United States Department of Agriculture. 
Soil Survey Geographic (SSURGO) Database. Available online. Accessed [date].
```

## License Compatibility

This project is licensed under the GNU General Public License v3.0 (GPL-3.0), which is compatible with PySDA's GPL-3.0 license. All vendored code maintains its original licensing and copyright notices.
