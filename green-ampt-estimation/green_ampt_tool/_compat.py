from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Any

if TYPE_CHECKING:  # pragma: no cover - only for type checkers
    import geopandas as gpd  # type: ignore
    import pandas as pd  # type: ignore
    GEOPANDAS_IMPORT_ERROR: Optional[ImportError] = None
    PANDAS_IMPORT_ERROR: Optional[ImportError] = None
else:  # pragma: no cover - runtime import with graceful failure messages
    try:
        import geopandas as gpd  # type: ignore
    except ImportError as exc:  # pragma: no cover
        gpd = None  # type: ignore
        GEOPANDAS_IMPORT_ERROR = exc
    else:  # pragma: no cover
        GEOPANDAS_IMPORT_ERROR = None

    try:
        import pandas as pd  # type: ignore
    except ImportError as exc:  # pragma: no cover
        pd = None  # type: ignore
        PANDAS_IMPORT_ERROR = exc
    else:  # pragma: no cover
        PANDAS_IMPORT_ERROR = None


def require_geopandas() -> Any:
    if gpd is None:  # type: ignore[name-defined]
        raise ModuleNotFoundError("geopandas is required for this operation") from GEOPANDAS_IMPORT_ERROR
    return gpd  # type: ignore[return-value]


def require_pandas() -> Any:
    if pd is None:  # type: ignore[name-defined]
        raise ModuleNotFoundError("pandas is required for this operation") from PANDAS_IMPORT_ERROR
    return pd  # type: ignore[return-value]
