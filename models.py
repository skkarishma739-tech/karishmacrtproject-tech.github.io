from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Building(Base):
    __tablename__ = "buildings"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    code = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)

    # Relationships
    nodes = relationship("Node", back_populates="building", cascade="all, delete-orphan")


class Node(Base):
    __tablename__ = "nodes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    type = Column(String, nullable=False, default="room")  # room, junction, entrance, elevator, stairs, toilet, gates
    building_id = Column(Integer, ForeignKey("buildings.id", ondelete="SET NULL"), nullable=True)
    floor = Column(Integer, default=0)
    x = Column(Float, nullable=False)  # X-coordinate on custom map
    y = Column(Float, nullable=False)  # Y-coordinate on custom map

    # Relationships
    building = relationship("Building", back_populates="nodes")
    
    # We can fetch edges associated with this node, but we'll query Edges table directly for pathfinding.


class Edge(Base):
    __tablename__ = "edges"

    id = Column(Integer, primary_key=True, index=True)
    source_node_id = Column(Integer, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False)
    target_node_id = Column(Integer, ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False)
    distance = Column(Float, nullable=False)  # in meters
    is_accessible = Column(Boolean, default=True)  # stair-free, wheelchair friendly
    crowd_level = Column(Integer, default=1)  # 1 (clear) to 5 (extremely crowded)

    # Relationships to access node info if needed
    source_node = relationship("Node", foreign_keys=[source_node_id])
    target_node = relationship("Node", foreign_keys=[target_node_id])
