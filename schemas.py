from pydantic import BaseModel, Field
from typing import List, Optional

# --- BUILDING SCHEMAS ---
class BuildingBase(BaseModel):
    name: str = Field(..., example="Computer Science Building")
    code: str = Field(..., example="CS")
    description: Optional[str] = Field(None, example="Home to the CS Department and main computing labs")

class BuildingCreate(BuildingBase):
    pass

class BuildingUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None

class Building(BuildingBase):
    id: int

    class Config:
        from_attributes = True


# --- NODE SCHEMAS ---
class NodeBase(BaseModel):
    name: Optional[str] = Field(None, example="Room 101")
    type: str = Field("room", example="room")  # room, junction, entrance, elevator, stairs, gate
    building_id: Optional[int] = Field(None, example=1)
    floor: int = Field(0, example=0)
    x: float = Field(..., example=150.0)
    y: float = Field(..., example=220.0)

class NodeCreate(NodeBase):
    pass

class NodeUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    building_id: Optional[int] = None
    floor: Optional[int] = None
    x: Optional[float] = None
    y: Optional[float] = None

class Node(NodeBase):
    id: int

    class Config:
        from_attributes = True


# --- EDGE SCHEMAS ---
class EdgeBase(BaseModel):
    source_node_id: int = Field(..., example=1)
    target_node_id: int = Field(..., example=2)
    distance: float = Field(..., example=15.5)  # in meters
    is_accessible: bool = Field(True, example=True)
    crowd_level: int = Field(1, ge=1, le=5, example=1)  # 1 to 5

class EdgeCreate(EdgeBase):
    pass

class EdgeUpdate(BaseModel):
    source_node_id: Optional[int] = None
    target_node_id: Optional[int] = None
    distance: Optional[float] = None
    is_accessible: Optional[bool] = None
    crowd_level: Optional[int] = Field(None, ge=1, le=5)

class Edge(EdgeBase):
    id: int

    class Config:
        from_attributes = True


# --- PATHFINDING & NAVIGATION SCHEMAS ---
class RouteRequest(BaseModel):
    start_node_id: int
    end_node_id: int
    mode: str = Field("shortest", example="shortest")  # shortest, accessible, crowd_aware

class RouteStep(BaseModel):
    instruction: str
    distance: float
    estimated_time: float
    node: Node

class RouteResult(BaseModel):
    path: List[Node]
    steps: List[RouteStep]
    distance: float  # total distance in meters
    estimated_time: float  # total time in seconds
    crowd_level_info: str  # text summary of the crowd level along the path
    mode: str

class AlternativeRoute(BaseModel):
    mode: str
    distance: float
    estimated_time: float
    path: List[Node]

class RouteResponse(BaseModel):
    optimal_route: RouteResult
    alternatives: List[AlternativeRoute]


# --- CROWD UPDATE SCHEMA ---
class CrowdUpdate(BaseModel):
    edge_id: int
    crowd_level: int = Field(..., ge=1, le=5)
