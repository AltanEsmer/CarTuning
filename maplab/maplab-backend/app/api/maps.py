"""
ECU Map API endpoints.
"""

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.services.map_parser import MapParseError, load_and_parse_map

router = APIRouter()


@router.post("/maps/parse")
async def parse_map(file_path: str | None = None, file: UploadFile | None = None):
    """
    Parse an ECU map CSV file and return grid data.

    Accepts either:
    - A file path via query parameter: ?file_path=/path/to/file.csv
    - A file upload via multipart/form-data

    Returns:
        JSON with rpm_axis, load_axis, z_grid_flat, and shape information
    """
    # Determine file source
    temp_file_path = None

    try:
        if file_path:
            # Use provided file path
            resolved_path = Path(file_path).resolve()
            if not resolved_path.exists():
                raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
            final_path = resolved_path

        elif file:
            # Save uploaded file temporarily
            import tempfile

            suffix = Path(file.filename).suffix if file.filename else ".csv"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                content = await file.read()
                tmp.write(content)
                temp_file_path = tmp.name
            final_path = Path(temp_file_path)

        else:
            raise HTTPException(
                status_code=400, detail="Either 'file_path' query parameter or 'file' upload required"
            )

        # Parse the map
        try:
            X_grid, Y_grid, Z_grid = load_and_parse_map(final_path)
        except MapParseError as e:
            raise HTTPException(status_code=400, detail=f"Map parsing error: {str(e)}")

        # Extract unique axes (from grid)
        rpm_axis = X_grid[0, :].tolist()  # First row contains all RPM values
        load_axis = Y_grid[:, 0].tolist()  # First column contains all Load values

        # Flatten Z_grid for JSON serialization
        z_grid_flat = Z_grid.flatten().tolist()

        # Return response with shape information
        return JSONResponse(
            content={
                "rpm_axis": rpm_axis,
                "load_axis": load_axis,
                "z_grid_flat": z_grid_flat,
                "shape": {"rows": len(load_axis), "cols": len(rpm_axis)},
                "total_points": len(z_grid_flat),
            }
        )

    finally:
        # Clean up temporary file if created
        if temp_file_path and Path(temp_file_path).exists():
            Path(temp_file_path).unlink()


@router.get("/maps/parse")
async def parse_map_get(file_path: str):
    """
    Parse an ECU map CSV file by file path (GET method for convenience).

    Query parameters:
    - file_path: Path to the CSV file to parse

    Returns:
        JSON with rpm_axis, load_axis, z_grid_flat, and shape information
    """
    return await parse_map(file_path=file_path, file=None)

