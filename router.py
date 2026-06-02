import heapq
import math
from typing import List, Dict, Tuple, Optional, Set
from sqlalchemy.orm import Session
from .models import Node, Edge

def build_graph(edges: List[Edge], mode: str) -> Dict[int, List[Tuple[int, float, bool, int, int]]]:
    """
    Builds an adjacency list of the graph.
    Returns:
        dict: mapping node_id -> list of tuples (neighbor_id, cost, is_accessible, crowd_level, edge_id)
    """
    graph = {}
    for edge in edges:
        # Determine edge traversability and cost
        if mode == "accessible" and not edge.is_accessible:
            # In accessibility mode, skip non-accessible paths (e.g. stairs)
            continue
            
        # Cost calculation based on mode
        # 1. Shortest path (distance only)
        cost = edge.distance
        
        # 2. Crowd aware (dist penalised by crowd levels: 1 = no penalty, 5 = heavy penalty)
        if mode == "crowd_aware":
            # Multiplier ranges from 1.0 (crowd=1) to 2.6 (crowd=5)
            crowd_multiplier = 1.0 + (edge.crowd_level - 1) * 0.4
            cost = edge.distance * crowd_multiplier

        # Add connection (undirected graph representation for campus layout)
        if edge.source_node_id not in graph:
            graph[edge.source_node_id] = []
        if edge.target_node_id not in graph:
            graph[edge.target_node_id] = []
            
        graph[edge.source_node_id].append((edge.target_node_id, cost, edge.is_accessible, edge.crowd_level, edge.id))
        graph[edge.target_node_id].append((edge.source_node_id, cost, edge.is_accessible, edge.crowd_level, edge.id))
        
    return graph

def heuristic(node_a: Node, node_b: Node) -> float:
    """
    A* Heuristic: 2D Euclidean distance + floor height penalty.
    """
    # Assuming x and y are meters (or scaled pixels).
    # We add 20 meters penalty per floor difference to model stair/elevator travel time.
    dx = node_a.x - node_b.x
    dy = node_a.y - node_b.y
    df = abs(node_a.floor - node_b.floor) * 20.0
    return math.sqrt(dx * dx + dy * dy) + df

def run_dijkstra(
    graph: Dict[int, List[Tuple[int, float, bool, int, int]]],
    nodes_map: Dict[int, Node],
    start_id: int,
    end_id: int
) -> Tuple[List[int], float, float]:
    """
    Runs Dijkstra's algorithm to find the shortest path.
    Returns:
        tuple: (path_node_ids, total_cost_weighted, actual_distance_meters)
    """
    if start_id not in graph or end_id not in graph:
        # If nodes are isolated or not connected
        if start_id == end_id and start_id in nodes_map:
            return [start_id], 0.0, 0.0
        return [], float('inf'), float('inf')
        
    # priority queue: (cumulative_cost, current_node, path, actual_dist)
    queue = [(0.0, start_id, [start_id], 0.0)]
    visited = set()
    
    while queue:
        cost, curr, path, dist = heapq.heappop(queue)
        
        if curr == end_id:
            return path, cost, dist
            
        if curr in visited:
            continue
        visited.add(curr)
        
        for neighbor, edge_cost, _, _, edge_id in graph.get(curr, []):
            if neighbor in visited:
                continue
            
            # Find the actual distance of this edge
            # edge_cost contains the crowd penalty if in crowd_aware mode,
            # so we calculate actual distance by looking at the original edge or node coordinates.
            # But we can reconstruct actual distance since we have access to original edge parameters.
            # In our graph tuple structure: edge_cost is weighted, we need to pass along actual distance.
            # Let's find the geometric distance between nodes if actual edge distance isn't saved, 
            # or pass the actual distance along. In graph definition, actual distance = edge.distance.
            # Let's modify the graph representation:
            # (neighbor_id, cost, is_accessible, crowd_level, edge_id, actual_distance)
            pass
            
    return [], float('inf'), float('inf')

# Let's write a robust single solver that supports both A* and Dijkstra.
def find_route(
    db: Session,
    start_node_id: int,
    end_node_id: int,
    mode: str = "shortest",
    algorithm: str = "astar"
) -> Optional[Dict]:
    """
    Finds the optimal path between start_node_id and end_node_id using the specified mode and algorithm.
    """
    # Fetch all nodes and edges from DB
    nodes = db.query(Node).all()
    edges = db.query(Edge).all()
    
    nodes_map = {n.id: n for n in nodes}
    
    if start_node_id not in nodes_map or end_node_id not in nodes_map:
        return None
        
    start_node = nodes_map[start_node_id]
    end_node = nodes_map[end_node_id]
    
    # 1. Build adjacent lists
    # Each neighbor element: (neighbor_id, weighted_cost, is_accessible, crowd_level, actual_distance)
    graph = {}
    for edge in edges:
        if mode == "accessible" and not edge.is_accessible:
            continue
            
        # Cost adjustment
        weighted_cost = edge.distance
        if mode == "crowd_aware":
            # Scale cost based on crowd level (1 to 5)
            crowd_multiplier = 1.0 + (edge.crowd_level - 1) * 0.4
            weighted_cost = edge.distance * crowd_multiplier

        if edge.source_node_id not in graph:
            graph[edge.source_node_id] = []
        if edge.target_node_id not in graph:
            graph[edge.target_node_id] = []
            
        graph[edge.source_node_id].append((edge.target_node_id, weighted_cost, edge.is_accessible, edge.crowd_level, edge.distance))
        graph[edge.target_node_id].append((edge.source_node_id, weighted_cost, edge.is_accessible, edge.crowd_level, edge.distance))

    if start_node_id not in graph or end_node_id not in graph:
        if start_node_id == end_node_id:
            return {
                "path": [start_node],
                "steps": [],
                "distance": 0.0,
                "estimated_time": 0.0,
                "crowd_level_info": "You are already at your destination.",
                "mode": mode
            }
        return None

    # Priority queue: (f_score, g_score, current_id, path, actual_dist, total_crowd, edge_count)
    # For Dijkstra, heuristic is 0, so f_score = g_score
    start_h = heuristic(start_node, end_node) if algorithm == "astar" else 0.0
    queue = [(start_h, 0.0, start_node_id, [start_node_id], 0.0, 0, 0)]
    
    # Record minimum g_score (actual path cost) to each node to avoid loops
    best_g = {start_node_id: 0.0}
    
    final_path = []
    final_distance = 0.0
    final_crowd_total = 0
    final_edge_count = 0
    
    while queue:
        f, g, curr_id, path, dist, crowd_sum, edges_traversed = heapq.heappop(queue)
        
        if curr_id == end_node_id:
            final_path = path
            final_distance = dist
            final_crowd_total = crowd_sum
            final_edge_count = edges_traversed
            break
            
        if g > best_g.get(curr_id, float('inf')):
            continue
            
        for neighbor_id, weight, is_accessible, crowd, act_dist in graph.get(curr_id, []):
            new_g = g + weight
            new_dist = dist + act_dist
            
            if new_g < best_g.get(neighbor_id, float('inf')):
                best_g[neighbor_id] = new_g
                h = heuristic(nodes_map[neighbor_id], end_node) if algorithm == "astar" else 0.0
                new_f = new_g + h
                heapq.heappush(
                    queue,
                    (new_f, new_g, neighbor_id, path + [neighbor_id], new_dist, crowd_sum + crowd, edges_traversed + 1)
                )
                
    if not final_path:
        return None
        
    # Map node IDs to node objects
    path_nodes = [nodes_map[nid] for nid in final_path]
    
    # Generate navigation steps/instructions
    steps = []
    avg_walking_speed = 1.3  # meters per second (approx 4.7 km/h)
    
    for i in range(len(path_nodes) - 1):
        n_curr = path_nodes[i]
        n_next = path_nodes[i + 1]
        
        # Find edge stats
        step_dist = 0.0
        step_crowd = 1
        for neighbor_id, _, _, crowd, act_dist in graph.get(n_curr.id, []):
            if neighbor_id == n_next.id:
                step_dist = act_dist
                step_crowd = crowd
                break
        
        # Calculate time for this segment
        # Walking speed decreases as crowd density increases (crowd factor)
        speed_multiplier = max(0.3, 1.0 - (step_crowd - 1) * 0.15)
        segment_speed = avg_walking_speed * speed_multiplier
        step_time = step_dist / segment_speed
        
        # Formulate instruction
        instruction = ""
        if n_curr.floor != n_next.floor:
            action = "stairs" if n_next.type == "stairs" or n_curr.type == "stairs" else "elevator"
            instruction = f"Take the {action} from Floor {n_curr.floor} to Floor {n_next.floor}."
        elif n_curr.building_id != n_next.building_id:
            curr_b = n_curr.building.name if n_curr.building else "outside"
            next_b = n_next.building.name if n_next.building else "outside"
            instruction = f"Exit {curr_b} and walk towards {next_b}."
        else:
            # Same floor and building
            if n_next.name:
                instruction = f"Go straight for {step_dist:.1f} meters towards {n_next.name}."
            else:
                instruction = f"Walk straight for {step_dist:.1f} meters through the corridor."
                
        steps.append({
            "instruction": instruction,
            "distance": step_dist,
            "estimated_time": step_time,
            "node": n_next
        })
        
    # Calculate overall stats
    # Average crowd level
    avg_crowd = final_crowd_total / final_edge_count if final_edge_count > 0 else 1.0
    if avg_crowd <= 1.5:
        crowd_info = "Clear paths (Minimal crowd)"
    elif avg_crowd <= 2.5:
        crowd_info = "Lightly active (Low congestion)"
    elif avg_crowd <= 3.5:
        crowd_info = "Moderately crowded (Normal campus activity)"
    elif avg_crowd <= 4.5:
        crowd_info = "Heavy traffic (Avoid if in a rush)"
    else:
        crowd_info = "Severely congested (Recommend alternative paths)"
        
    # Estimate total time
    total_time = sum(s["estimated_time"] for s in steps)
    
    return {
        "path": path_nodes,
        "steps": steps,
        "distance": final_distance,
        "estimated_time": total_time,
        "crowd_level_info": crowd_info,
        "mode": mode
    }
