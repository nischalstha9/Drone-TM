from pydantic import BaseModel, computed_field, Field
from typing import Any, Optional, Union
from geojson_pydantic import Feature, FeatureCollection, Polygon
from app.models.enums import TaskSplitType
from shapely import wkb

from app.utils import (
    geojson_to_geometry,
    read_wkb,
    merge_multipolygon,
    write_wkb,
    geometry_to_geojson,
)


class ProjectInfo(BaseModel):
    """Basic project info."""

    name: str
    short_description: str
    description: str
    per_task_instructions: Optional[str] = None


class ProjectIn(BaseModel):
    """Upload new project."""

    name: str
    short_description: str
    description: str
    per_task_instructions: Optional[str] = None
    organisation_id: Optional[int] = None
    task_split_type: Optional[TaskSplitType] = None
    task_split_dimension: Optional[int] = None
    outline_geojson: Union[FeatureCollection, Feature, Polygon]

    @computed_field
    @property
    def outline(self) -> Optional[Any]:
        """Compute WKBElement geom from geojson."""
        if not self.outline_geojson:
            return None

        outline = merge_multipolygon(self.outline_geojson)
        return geojson_to_geometry(outline)

    @computed_field
    @property
    def centroid(self) -> Optional[Any]:
        """Compute centroid for project outline."""
        if not self.outline:
            return None
        return write_wkb(read_wkb(self.outline).centroid)


class ProjectOut(BaseModel):
    """Base project model."""

    id: int
    name: str
    short_description: str
    description: str
    per_task_instructions: Optional[str] = None
    outline: Any = Field(exclude=True)

    @computed_field
    @property
    def outline_geojson(self) -> Optional[Feature]:
        """Compute the geojson outline from WKBElement outline."""
        if not self.outline:
            return None
        geometry = wkb.loads(bytes(self.outline.data))
        bbox = geometry.bounds  # Calculate bounding box
        return geometry_to_geojson(self.outline, {"id": self.id, "bbox": bbox}, self.id)


class PresignedUrlRequest(BaseModel):
    image_name: str
    expiry: int  # Expiry time in seconds
