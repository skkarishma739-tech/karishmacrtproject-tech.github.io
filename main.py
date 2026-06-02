from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from .database import engine, Base, get_db
from  . import  models, schemas, router
from  .seed import seed_campus_data

# Create Database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart Campus Navigation API",
    description="REST API for shortest path, accessible routing, and crowd-aware campus navigation.",
    version="1.0.0"
)

# Enable CORS for frontend API calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Seed database on startup if empty
@app.on_event("startup")
def startup_event():
    db = next(get_db())
    try:
        # Check if buildings exist. If not, seed the data
        if db.query(models.Building).count() == 0:
            print("Database is empty. Seeding initial campus data...")
            seed_campus_data(db)
            print("Seeding completed successfully!")
    except Exception as e:
        print(f"Error seeding database: {e}")
    finally:
        db.close()


# --- DATABASE RESET & RE-SEED ENDPOINT ---
@app.post("/api/reset-db", tags=["Crowd Control"])
def reset_database(db: Session = Depends(get_db)):
    """
    Clears the entire database and seeds the default campus map configuration.
    """
    try:
        # Disable constraints or delete in order of dependencies (edges -> nodes -> buildings)
        db.query(models.Edge).delete()
        db.query(models.Node).delete()
        db.query(models.Building).delete()
        db.commit()
        
        # Seed fresh data
        seed_campus_data(db)
        return {"message": "Database reset and seeded successfully!"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database reset failed: {str(e)}"
        )



# --- ROOT / API DOCS REDIRECT ---
# We will host the static frontend files under the root `/` path.
# We'll mount the static files at the end of the file.

# --- BUILDING ENDPOINTS ---
@app.post("/api/buildings", response_model=schemas.Building, tags=["Buildings"])
def create_building(building: schemas.BuildingCreate, db: Session = Depends(get_db)):
    db_building = db.query(models.Building).filter(models.Building.code == building.code).first()
    if db_building:
        raise HTTPException(status_code=400, detail="Building code already registered")
    
    new_building = models.Building(**building.dict())
    db.add(new_building)
    db.commit()
    db.refresh(new_building)
    return new_building

@app.get("/api/buildings", response_model=List[schemas.Building], tags=["Buildings"])
def get_buildings(db: Session = Depends(get_db)):
    return db.query(models.Building).all()

@app.get("/api/buildings/{building_id}", response_model=schemas.Building, tags=["Buildings"])
def get_building(building_id: int, db: Session = Depends(get_db)):
    building = db.query(models.Building).filter(models.Building.id == building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    return building

@app.put("/api/buildings/{building_id}", response_model=schemas.Building, tags=["Buildings"])
def update_building(building_id: int, building_data: schemas.BuildingUpdate, db: Session = Depends(get_db)):
    building = db.query(models.Building).filter(models.Building.id == building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    
    for key, value in building_data.dict(exclude_unset=True).items():
        setattr(building, key, value)
    
    db.commit()
    db.refresh(building)
    return building

@app.delete("/api/buildings/{building_id}", tags=["Buildings"])
def delete_building(building_id: int, db: Session = Depends(get_db)):
    building = db.query(models.Building).filter(models.Building.id == building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    
    db.delete(building)
    db.commit()
    return {"message": "Building deleted successfully"}


# --- NODE ENDPOINTS ---
@app.post("/api/nodes", response_model=schemas.Node, tags=["Nodes"])
def create_node(node: schemas.NodeCreate, db: Session = Depends(get_db)):
    if node.building_id:
        building = db.query(models.Building).filter(models.Building.id == node.building_id).first()
        if not building:
            raise HTTPException(status_code=404, detail="Building not found")
            
    new_node = models.Node(**node.dict())
    db.add(new_node)
    db.commit()
    db.refresh(new_node)
    return new_node

@app.get("/api/nodes", response_model=List[schemas.Node], tags=["Nodes"])
def get_nodes(
    building_id: Optional[int] = None,
    floor: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Node)
    if building_id is not None:
        query = query.filter(models.Node.building_id == building_id)
    if floor is not None:
        query = query.filter(models.Node.floor == floor)
    return query.all()

@app.get("/api/nodes/{node_id}", response_model=schemas.Node, tags=["Nodes"])
def get_node(node_id: int, db: Session = Depends(get_db)):
    node = db.query(models.Node).filter(models.Node.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node

@app.put("/api/nodes/{node_id}", response_model=schemas.Node, tags=["Nodes"])
def update_node(node_id: int, node_data: schemas.NodeUpdate, db: Session = Depends(get_db)):
    node = db.query(models.Node).filter(models.Node.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
        
    if node_data.building_id is not None:
        building = db.query(models.Building).filter(models.Building.id == node_data.building_id).first()
        if not building:
            raise HTTPException(status_code=404, detail="Building not found")
            
    for key, value in node_data.dict(exclude_unset=True).items():
        setattr(node, key, value)
        
    db.commit()
    db.refresh(node)
    return node

@app.delete("/api/nodes/{node_id}", tags=["Nodes"])
def delete_node(node_id: int, db: Session = Depends(get_db)):
    node = db.query(models.Node).filter(models.Node.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
        
    # Delete related edges to prevent foreign key issues
    db.query(models.Edge).filter(
        (models.Edge.source_node_id == node_id) | (models.Edge.target_node_id == node_id)
    ).delete()
    
    db.delete(node)
    db.commit()
    return {"message": "Node and its connections deleted successfully"}


# --- EDGE (CONNECTION) ENDPOINTS ---
@app.post("/api/edges", response_model=schemas.Edge, tags=["Edges"])
def create_edge(edge: schemas.EdgeCreate, db: Session = Depends(get_db)):
    # Check if nodes exist
    source = db.query(models.Node).filter(models.Node.id == edge.source_node_id).first()
    target = db.query(models.Node).filter(models.Node.id == edge.target_node_id).first()
    
    if not source or not target:
        raise HTTPException(status_code=404, detail="Source or Target node not found")
        
    # Prevent self-loop
    if edge.source_node_id == edge.target_node_id:
        raise HTTPException(status_code=400, detail="Cannot connect node to itself")
        
    # Check if connection already exists in either direction
    existing = db.query(models.Edge).filter(
        ((models.Edge.source_node_id == edge.source_node_id) & (models.Edge.target_node_id == edge.target_node_id)) |
        ((models.Edge.source_node_id == edge.target_node_id) & (models.Edge.target_node_id == edge.source_node_id))
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Connection already exists between these nodes")
        
    new_edge = models.Edge(**edge.dict())
    db.add(new_edge)
    db.commit()
    db.refresh(new_edge)
    return new_edge

@app.get("/api/edges", response_model=List[schemas.Edge], tags=["Edges"])
def get_edges(db: Session = Depends(get_db)):
    return db.query(models.Edge).all()

@app.get("/api/edges/{edge_id}", response_model=schemas.Edge, tags=["Edges"])
def get_edge(edge_id: int, db: Session = Depends(get_db)):
    edge = db.query(models.Edge).filter(models.Edge.id == edge_id).first()
    if not edge:
        raise HTTPException(status_code=404, detail="Edge not found")
    return edge

@app.put("/api/edges/{edge_id}", response_model=schemas.Edge, tags=["Edges"])
def update_edge(edge_id: int, edge_data: schemas.EdgeUpdate, db: Session = Depends(get_db)):
    edge = db.query(models.Edge).filter(models.Edge.id == edge_id).first()
    if not edge:
        raise HTTPException(status_code=404, detail="Edge not found")
        
    if edge_data.source_node_id is not None:
        n1 = db.query(models.Node).filter(models.Node.id == edge_data.source_node_id).first()
        if not n1:
            raise HTTPException(status_code=404, detail="Source node not found")
            
    if edge_data.target_node_id is not None:
        n2 = db.query(models.Node).filter(models.Node.id == edge_data.target_node_id).first()
        if not n2:
            raise HTTPException(status_code=404, detail="Target node not found")
            
    for key, value in edge_data.dict(exclude_unset=True).items():
        setattr(edge, key, value)
        
    db.commit()
    db.refresh(edge)
    return edge

@app.delete("/api/edges/{edge_id}", tags=["Edges"])
def delete_edge(edge_id: int, db: Session = Depends(get_db)):
    edge = db.query(models.Edge).filter(models.Edge.id == edge_id).first()
    if not edge:
        raise HTTPException(status_code=404, detail="Edge not found")
    db.delete(edge)
    db.commit()
    return {"message": "Edge deleted successfully"}


# --- NAVIGATION / ROUTE PLANNING ENDPOINTS ---
@app.post("/api/route", response_model=schemas.RouteResponse, tags=["Navigation"])
def get_route(req: schemas.RouteRequest, db: Session = Depends(get_db)):
    """
    Finds the shortest, accessible, or crowd-aware route between start and end nodes,
    and returns it along with alternative paths.
    """
    # 1. Solve optimal route
    optimal = router.find_route(db, req.start_node_id, req.end_node_id, mode=req.mode, algorithm="astar")
    if not optimal:
        raise HTTPException(status_code=404, detail="No route found between selected points with the requested criteria.")
        
    # 2. Gather alternatives
    alternatives = []
    other_modes = ["shortest", "accessible", "crowd_aware"]
    other_modes.remove(req.mode)
    
    for other_mode in other_modes:
        # Avoid running accessible solver if there is no accessible path
        alt_res = router.find_route(db, req.start_node_id, req.end_node_id, mode=other_mode, algorithm="astar")
        if alt_res and alt_res["distance"] != optimal["distance"]:
            alternatives.append({
                "mode": other_mode,
                "distance": alt_res["distance"],
                "estimated_time": alt_res["estimated_time"],
                "path": alt_res["path"]
            })
            
    return {
        "optimal_route": optimal,
        "alternatives": alternatives
    }


# --- SEARCH CAMPUS LOCATIONS ---
@app.get("/api/search", response_model=List[schemas.Node], tags=["Search"])
def search_campus(
    q: str = Query(..., min_length=1, description="Search term for room names, types, or building names"),
    db: Session = Depends(get_db)
):
    """
    Searches for campus locations. Matches room name, type, building name, or building code.
    """
    # Query nodes that match search criteria
    nodes = db.query(models.Node).join(models.Building, isouter=True).filter(
        (models.Node.name.ilike(f"%{q}%")) |
        (models.Node.type.ilike(f"%{q}%")) |
        (models.Building.name.ilike(f"%{q}%")) |
        (models.Building.code.ilike(f"%{q}%"))
    ).all()
    
    return nodes


# --- UPDATE CROWD DENSITY ---
@app.post("/api/crowd", tags=["Crowd Control"])
def update_crowd(update: schemas.CrowdUpdate, db: Session = Depends(get_db)):
    """
    Updates the crowd density of an edge in real time.
    """
    edge = db.query(models.Edge).filter(models.Edge.id == update.edge_id).first()
    if not edge:
        raise HTTPException(status_code=404, detail="Edge not found")
        
    edge.crowd_level = update.crowd_level
    db.commit()
    db.refresh(edge)
    return {"message": "Crowd level updated successfully", "edge_id": edge.id, "crowd_level": edge.crowd_level}


# --- STATIC FILES ---
# Create static directory if it doesn't exist
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

# Serve the static website at "/" root
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
