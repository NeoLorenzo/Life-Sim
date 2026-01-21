# life_sim/rendering/family_tree.py
"""
Family Tree Layout Module.
Handles graph traversal and positioning for the family tree visualization.
"""
import logging

class FamilyTreeLayout:
    """
    Calculates the structure and geometry of a family tree.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.nodes = {} # uid -> {agent, gen, x, y, width, height}
        self.edges = [] # (start_uid, end_uid, color_type)
        self.min_gen = 0
        self.max_gen = 0
        
        # Layout Constants
        self.NODE_WIDTH = 140
        self.NODE_HEIGHT = 60
        self.GAP_X = 40
        self.GAP_Y = 100

    def build(self, focus_agent, all_agents_lookup):
        """
        Constructs the tree graph starting from focus_agent.
        """
        self.nodes = {}
        self.edges = []
        
        # 1. BFS Traversal to find the "Clan"
        # Queue: (uid, generation_index)
        queue = [(focus_agent.uid, 0)]
        visited = {focus_agent.uid}
        
        # Store raw generation data before layout
        gen_map = {0: [focus_agent.uid]} # gen -> list of uids
        
        # Helper to add to gen_map
        def add_to_gen(uid, gen):
            if gen not in gen_map: gen_map[gen] = []
            if uid not in gen_map[gen]: gen_map[gen].append(uid)

        while queue:
            current_uid, current_gen = queue.pop(0)
            agent = all_agents_lookup.get(current_uid)
            if not agent: continue
            
            # Store Node Data (Position calculated later)
            self.nodes[current_uid] = {
                "agent": agent,
                "gen": current_gen,
                "x": 0, "y": 0,
                "width": self.NODE_WIDTH,
                "height": self.NODE_HEIGHT
            }
            
            # Check Relationships
            for rel_uid, rel_data in agent.relationships.items():
                if rel_uid not in all_agents_lookup:
                    continue
                
                rel_type = rel_data["type"]
                next_gen = current_gen
                
                # Determine Generation Shift
                if rel_type in ["Father", "Mother"]:
                    next_gen = current_gen + 1
                elif rel_type == "Child":
                    next_gen = current_gen - 1
                elif rel_type in ["Spouse", "Sibling", "Half-Sibling"]:
                    next_gen = current_gen
                else:
                    # Ignore non-family (Friends, Bosses, etc.)
                    continue
                
                # Add Edge (Visual connection)
                # We only add edge if we haven't processed this link yet to avoid duplicates
                # Sort UIDs to make a unique key for the edge
                edge_key = tuple(sorted((current_uid, rel_uid)))
                edge_exists = any(tuple(sorted((e[0], e[1]))) == edge_key for e in self.edges)
                
                if not edge_exists:
                    self.edges.append((current_uid, rel_uid, rel_type))

                # Add to Queue if not visited
                if rel_uid not in visited:
                    visited.add(rel_uid)
                    queue.append((rel_uid, next_gen))
                    add_to_gen(rel_uid, next_gen)

        # 2. Layout Calculation (Simple Layered Grid)
        if not gen_map:
            return

        self.min_gen = min(gen_map.keys())
        self.max_gen = max(gen_map.keys())
        
        # Iterate generations from Top (Oldest) to Bottom
        # We sort generations descending (e.g., 2, 1, 0, -1)
        sorted_gens = sorted(gen_map.keys(), reverse=True)
        
        for gen in sorted_gens:
            uids = gen_map[gen]
            
            # Sort UIDs within generation for better clustering
            # Heuristic: Sort by Age (Older on left)
            uids.sort(key=lambda u: all_agents_lookup[u].age, reverse=True)
            
            # Calculate Row Width
            count = len(uids)
            total_w = count * self.NODE_WIDTH + (count - 1) * self.GAP_X
            start_x = -(total_w / 2) + (self.NODE_WIDTH / 2)
            
            # Assign Positions
            # Y is inverted because Gen +1 is "Up" (Negative Y in screen coords relative to center)
            # Let's make Gen 0 be Y=0. Gen 1 is Y = -100. Gen -1 is Y = +100.
            y_pos = -1 * gen * self.GAP_Y
            
            for i, uid in enumerate(uids):
                self.nodes[uid]["x"] = start_x + (i * (self.NODE_WIDTH + self.GAP_X))
                self.nodes[uid]["y"] = y_pos

    def get_node_at(self, rel_x, rel_y):
        """Returns the agent at the given relative coordinates, or None."""
        for uid, node in self.nodes.items():
            # Check bounding box centered at node['x'], node['y']
            left = node['x'] - node['width'] // 2
            right = node['x'] + node['width'] // 2
            top = node['y'] - node['height'] // 2
            bottom = node['y'] + node['height'] // 2
            
            if left <= rel_x <= right and top <= rel_y <= bottom:
                return node['agent']
        return None