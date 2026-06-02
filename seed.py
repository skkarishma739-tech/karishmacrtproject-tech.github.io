from sqlalchemy.orm import Session
from .models import Building, Node, Edge

def seed_campus_data(db: Session):
    # 1. CREATE BUILDINGS
    eng = Building(
        name="Engineering Hall",
        code="ENG",
        description="Home to the Faculty of Engineering, Computer Labs, and Tech Centers."
    )
    lib = Building(
        name="Main Library",
        code="LIB",
        description="University central library, study rooms, and reference desk."
    )
    sci = Building(
        name="Science Center",
        code="SCI",
        description="Physics, Chemistry labs, and science lecture theatres."
    )
    
    db.add_all([eng, lib, sci])
    db.commit()
    db.refresh(eng)
    db.refresh(lib)
    db.refresh(sci)

    # 2. CREATE NODES (Campus Locations)
    # Types: "room", "junction", "entrance", "elevator", "stairs", "gate"
    
    # --- Engineering Hall Floor 0 ---
    n1 = Node(name="Engineering Main Entrance", type="entrance", building_id=eng.id, floor=0, x=150.0, y=180.0)
    n2 = Node(name="Engineering Floor 0 Lobby", type="junction", building_id=eng.id, floor=0, x=180.0, y=210.0)
    n3 = Node(name="Computer Science Lab 101", type="room", building_id=eng.id, floor=0, x=100.0, y=250.0)
    n4 = Node(name="Lecture Hall 102", type="room", building_id=eng.id, floor=0, x=260.0, y=250.0)
    n5 = Node(name="Engineering Stairs A (F0)", type="stairs", building_id=eng.id, floor=0, x=180.0, y=280.0)
    n6 = Node(name="Engineering Elevator (F0)", type="elevator", building_id=eng.id, floor=0, x=140.0, y=280.0)
    
    # --- Engineering Hall Floor 1 ---
    n7 = Node(name="Engineering Stairs A (F1)", type="stairs", building_id=eng.id, floor=1, x=180.0, y=280.0)
    n8 = Node(name="Engineering Elevator (F1)", type="elevator", building_id=eng.id, floor=1, x=140.0, y=280.0)
    n9 = Node(name="Engineering Floor 1 Lobby", type="junction", building_id=eng.id, floor=1, x=180.0, y=210.0)
    n10 = Node(name="Professor's Office 201", type="room", building_id=eng.id, floor=1, x=100.0, y=250.0)
    n11 = Node(name="Seminar Room 202", type="room", building_id=eng.id, floor=1, x=260.0, y=250.0)
    
    # --- Library Floor 0 ---
    n12 = Node(name="Library Main Entrance", type="entrance", building_id=lib.id, floor=0, x=450.0, y=180.0)
    n13 = Node(name="Library Central Atrium", type="junction", building_id=lib.id, floor=0, x=450.0, y=220.0)
    n14 = Node(name="Main Reading Room A", type="room", building_id=lib.id, floor=0, x=390.0, y=260.0)
    n15 = Node(name="IT Help Desk & Checkout", type="room", building_id=lib.id, floor=0, x=510.0, y=260.0)
    n17 = Node(name="Library Elevator (F0)", type="elevator", building_id=lib.id, floor=0, x=450.0, y=140.0)

    # --- Library Floor 1 ---
    n16 = Node(name="Quiet Study Zone B", type="room", building_id=lib.id, floor=1, x=450.0, y=260.0)
    n18 = Node(name="Library Elevator (F1)", type="elevator", building_id=lib.id, floor=1, x=450.0, y=140.0)

    # --- Science Center Floor 0 ---
    n19 = Node(name="Science Main Entrance", type="entrance", building_id=sci.id, floor=0, x=300.0, y=420.0)
    n20 = Node(name="Science Center Lobby", type="junction", building_id=sci.id, floor=0, x=300.0, y=380.0)
    n21 = Node(name="Physics Lab 10", type="room", building_id=sci.id, floor=0, x=220.0, y=350.0)
    n22 = Node(name="Chemistry Lab 12", type="room", building_id=sci.id, floor=0, x=380.0, y=350.0)

    # --- Outdoor Nodes ---
    n23 = Node(name="Central Plaza (Quad)", type="junction", floor=0, x=300.0, y=300.0)
    n24 = Node(name="North Campus Gate", type="gate", floor=0, x=300.0, y=80.0)
    n25 = Node(name="South Entrance Gate", type="gate", floor=0, x=300.0, y=520.0)

    nodes = [
        n1, n2, n3, n4, n5, n6, n7, n8, n9, n10, n11, 
        n12, n13, n14, n15, n16, n17, n18, 
        n19, n20, n21, n22, 
        n23, n24, n25
    ]
    
    db.add_all(nodes)
    db.commit()
    
    for n in nodes:
        db.refresh(n)

    # 3. CREATE EDGES (Map Connections)
    # Fields: source_node_id, target_node_id, distance, is_accessible, crowd_level
    edges = [
        # --- Outdoor Walkways ---
        Edge(source_node_id=n24.id, target_node_id=n23.id, distance=220.0, is_accessible=True, crowd_level=2),
        Edge(source_node_id=n25.id, target_node_id=n19.id, distance=100.0, is_accessible=True, crowd_level=1),
        Edge(source_node_id=n19.id, target_node_id=n20.id, distance=40.0, is_accessible=True, crowd_level=2),
        Edge(source_node_id=n20.id, target_node_id=n23.id, distance=80.0, is_accessible=True, crowd_level=3),
        Edge(source_node_id=n1.id, target_node_id=n23.id, distance=170.0, is_accessible=True, crowd_level=2),
        Edge(source_node_id=n12.id, target_node_id=n23.id, distance=170.0, is_accessible=True, crowd_level=3),
        
        # --- Engineering Hall Floor 0 ---
        Edge(source_node_id=n1.id, target_node_id=n2.id, distance=30.0, is_accessible=True, crowd_level=2),
        Edge(source_node_id=n2.id, target_node_id=n3.id, distance=85.0, is_accessible=True, crowd_level=1),
        Edge(source_node_id=n2.id, target_node_id=n4.id, distance=85.0, is_accessible=True, crowd_level=4), # Heavy student traffic outside CS 102
        Edge(source_node_id=n2.id, target_node_id=n5.id, distance=70.0, is_accessible=False, crowd_level=1), # Stairs!
        Edge(source_node_id=n2.id, target_node_id=n6.id, distance=80.0, is_accessible=True, crowd_level=1), # Elevator
        
        # --- Engineering Inter-Floor ---
        Edge(source_node_id=n5.id, target_node_id=n7.id, distance=15.0, is_accessible=False, crowd_level=2), # Stairs Floor connection
        Edge(source_node_id=n6.id, target_node_id=n8.id, distance=15.0, is_accessible=True, crowd_level=1), # Elevator Floor connection

        # --- Engineering Hall Floor 1 ---
        Edge(source_node_id=n7.id, target_node_id=n9.id, distance=70.0, is_accessible=False, crowd_level=1),
        Edge(source_node_id=n8.id, target_node_id=n9.id, distance=80.0, is_accessible=True, crowd_level=1),
        Edge(source_node_id=n9.id, target_node_id=n10.id, distance=85.0, is_accessible=True, crowd_level=1),
        Edge(source_node_id=n9.id, target_node_id=n11.id, distance=85.0, is_accessible=True, crowd_level=2),

        # --- Library Floor 0 ---
        Edge(source_node_id=n12.id, target_node_id=n13.id, distance=40.0, is_accessible=True, crowd_level=2),
        Edge(source_node_id=n13.id, target_node_id=n14.id, distance=70.0, is_accessible=True, crowd_level=1),
        Edge(source_node_id=n13.id, target_node_id=n15.id, distance=70.0, is_accessible=True, crowd_level=3),
        Edge(source_node_id=n13.id, target_node_id=n17.id, distance=80.0, is_accessible=True, crowd_level=1),

        # --- Library Inter-Floor ---
        Edge(source_node_id=n17.id, target_node_id=n18.id, distance=15.0, is_accessible=True, crowd_level=1),

        # --- Library Floor 1 ---
        Edge(source_node_id=n18.id, target_node_id=n16.id, distance=120.0, is_accessible=True, crowd_level=1),

        # --- Science Center ---
        Edge(source_node_id=n20.id, target_node_id=n21.id, distance=90.0, is_accessible=True, crowd_level=2),
        Edge(source_node_id=n20.id, target_node_id=n22.id, distance=90.0, is_accessible=True, crowd_level=2)
    ]
    
    db.add_all(edges)
    db.commit()
