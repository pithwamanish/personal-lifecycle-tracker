from __future__ import annotations

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.auth import get_current_user_optional
from app.models import User
from app.telemetry import record_canvas_component_created

logger = logging.getLogger("canvas")

router = APIRouter()


class CanvasComponentCreateDTO(BaseModel):
    name: str = Field(..., min_length=1, description="Human-readable name or label of the canvas component")
    componentType: str = Field(default="card", description="Canvas component type (e.g. card, node, panel, widget)")
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom canvas component properties and layout options")


class CanvasComponent(BaseModel):
    id: str
    name: str
    componentType: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    createdAt: str


# In-memory store for canvas components
_CANVAS_COMPONENTS: List[CanvasComponent] = []


def _reset_canvas_components_store() -> None:
    """Helper for test suites to reset component store."""
    global _CANVAS_COMPONENTS
    _CANVAS_COMPONENTS = []


@router.get("/components", response_model=List[CanvasComponent], status_code=status.HTTP_200_OK)
async def list_canvas_components(
    componentType: Optional[str] = Query(None, description="Filter by component type"),
) -> List[CanvasComponent]:
    """Retrieve all canvas components, optionally filtered by component type."""
    if componentType:
        return [c for c in _CANVAS_COMPONENTS if c.componentType == componentType]
    return list(_CANVAS_COMPONENTS)


@router.post("/components", response_model=CanvasComponent, status_code=status.HTTP_201_CREATED)
async def create_canvas_component(
    payload: CanvasComponentCreateDTO,
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> CanvasComponent:
    """Create a new canvas component and track telemetry metrics."""
    comp_type = payload.componentType or "card"
    try:
        if not payload.name or not payload.name.strip():
            record_canvas_component_created(component_type=comp_type, success=False)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Component name cannot be empty",
            )

        component_id = str(uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        component = CanvasComponent(
            id=component_id,
            name=payload.name.strip(),
            componentType=comp_type,
            properties=payload.properties or {},
            createdAt=created_at,
        )
        _CANVAS_COMPONENTS.append(component)
        record_canvas_component_created(component_type=comp_type, success=True)
        return component
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to create canvas component: %s", exc)
        record_canvas_component_created(component_type=comp_type, success=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Canvas component creation failed: {exc}",
        )


@router.get("/components/{id}", response_model=CanvasComponent, status_code=status.HTTP_200_OK)
async def get_canvas_component(id: str) -> CanvasComponent:
    """Retrieve a single canvas component by ID."""
    for comp in _CANVAS_COMPONENTS:
        if comp.id == id:
            return comp
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canvas component not found")


@router.delete("/components/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_canvas_component(id: str) -> None:
    """Delete a canvas component by ID."""
    global _CANVAS_COMPONENTS
    initial_len = len(_CANVAS_COMPONENTS)
    _CANVAS_COMPONENTS = [c for c in _CANVAS_COMPONENTS if c.id != id]
    if len(_CANVAS_COMPONENTS) == initial_len:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canvas component not found")
