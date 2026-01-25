# life_sim/rendering/family_tree.py
"""
Family Tree Layout Module.
Handles graph traversal, rank assignment, and geometry calculation 
using a layered graph drawing approach with virtual marriage nodes.
"""
import logging

class LayoutNode:
    """Represents an entity in the layout graph (Agent or Marriage Hub)."""
    def __init__(self, uid, generation, is_hub=False, agent=None):
        self.uid = uid
        self.generation = generation
        self.is_hub = is_hub
        self.agent = agent # None if is_hub is True
        self.is_blood = False # True if blood relative of focus agent
        
        # Geometry (Virtual Coordinates)
        self.x = 0
        self.y = 0
        self.width = 140 if not is_hub else 20
        self.height = 60 if not is_hub else 20
        
        # Graph Links
        self.parents = []   # Nodes above
        self.children = []  # Nodes below
        self.spouses = []   # Nodes on same rank (only for Agents)

class FamilyTreeLayout:
    """
    Calculates the structure and geometry of a family tree.
    Uses a 'Marriage Node' topology to handle half-siblings and divorces cleanly.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.nodes = {} # uid -> LayoutNode
        self.edges = [] # List of (start_node, end_node, type)
        
        # Layout Constants
        self.GAP_X = 40
        self.GAP_Y = 120
        self.LAYER_HEIGHT = 150

    def get_node_at(self, rel_x, rel_y):
        """Returns the agent at the given relative coordinates, or None."""
        for node in self.nodes.values():
            if node.is_hub: continue
            
            left = node.x - node.width // 2
            right = node.x + node.width // 2
            top = node.y - node.height // 2
            bottom = node.y + node.height // 2
            
            if left <= rel_x <= right and top <= rel_y <= bottom:
                return node.agent
        return None

    def build(self, focus_agent, all_agents_lookup):
        """
        Constructs the tree graph starting from focus_agent.
        """
        self.nodes = {}
        self.edges = []
        
        # --- Phase 1: Harvest (BFS) ---
        # Collect all related agents and assign Generations relative to Focus
        visited_uids = set()
        queue = [(focus_agent, 0)] # (Agent, Generation)
        visited_uids.add(focus_agent.uid)
        
        # Temporary storage for rank assignment
        agent_gen_map = {focus_agent.uid: 0}
        
        while queue:
            current_agent, gen = queue.pop(0)
            
            # Create Node
            if current_agent.uid not in self.nodes:
                self.nodes[current_agent.uid] = LayoutNode(current_agent.uid, gen, agent=current_agent)
            
            # Traverse Relationships
            for rel_uid, rel in current_agent.relationships.items():
                if rel_uid not in all_agents_lookup: continue
                
                rel_type = rel.rel_type
                next_gen = gen
                
                if rel_type in ["Father", "Mother"]: next_gen = gen + 1
                elif rel_type == "Child": next_gen = gen - 1
                
                # Add to queue if new
                if rel_uid not in visited_uids:
                    visited_uids.add(rel_uid)
                    agent_gen_map[rel_uid] = next_gen
                    queue.append((all_agents_lookup[rel_uid], next_gen))
                    
                    # Ensure node exists
                    if rel_uid not in self.nodes:
                        self.nodes[rel_uid] = LayoutNode(rel_uid, next_gen, agent=all_agents_lookup[rel_uid])

        # --- Phase 2: Topology (Marriage Nodes) ---
        # Identify unions and insert Hub Nodes
        # Key: tuple(sorted(spouse_uids)) -> hub_node
        marriage_hubs = {}
        
        # Iterate over a static list of items to allow modifying self.nodes inside the loop
        for uid, node in list(self.nodes.items()):
            agent = node.agent
            if not agent: continue
            
            # 1. Link to Parents via Marriage Hub
            # Find parents in the harvested set
            parents = [r_uid for r_uid, r in agent.relationships.items() 
                       if r["type"] in ["Father", "Mother"] and r_uid in self.nodes]
            
            if parents:
                parents.sort()
                pkey = tuple(parents)
                
                # Create Hub if missing
                if pkey not in marriage_hubs:
                    # Hub generation is parents' generation
                    p_gen = self.nodes[parents[0]].generation
                    hub_uid = f"HUB_{'-'.join(parents)}"
                    hub = LayoutNode(hub_uid, p_gen, is_hub=True)
                    self.nodes[hub_uid] = hub
                    marriage_hubs[pkey] = hub
                    
                    # Link Parents -> Hub
                    for p_uid in parents:
                        p_node = self.nodes[p_uid]
                        p_node.spouses.append(hub) # Link parent to hub
                        hub.parents.append(p_node) # Link hub to parent (upstream)
                
                # Link Hub -> Child
                hub = marriage_hubs[pkey]
                hub.children.append(node)
                node.parents.append(hub)

        # --- Phase 3: Layout (Iterative Sweep) ---
        # Group nodes by generation
        layers = {}
        for node in self.nodes.values():
            if node.generation not in layers: layers[node.generation] = []
            layers[node.generation].append(node)
            
        sorted_gens = sorted(layers.keys(), reverse=True) # Top to Bottom
        
        # Initial X Assignment: Group Spouses together
        for gen in sorted_gens:
            raw_nodes = layers[gen]
            ordered_nodes = []
            processed = set()
            
            # 1. Process Hubs (and pull their spouses next to them)
            hubs = [n for n in raw_nodes if n.is_hub]
            
            def hub_ancestor_sort_key(h):
                # Calculate the average X position of the *parents* of the spouses in this hub.
                # This ensures that if a spouse comes from a specific Grandparent block, 
                # this marriage hub stays close to that block.
                total_x = 0
                count = 0
                
                # h.parents contains the Spouses (e.g., James, Linda)
                for spouse in h.parents:
                    # spouse.parents contains the Origin Hubs (e.g., Pat_GP_Hub)
                    # These origin hubs are in the generation above (already placed).
                    for origin_hub in spouse.parents:
                        total_x += origin_hub.x
                        count += 1
                
                if count > 0:
                    return total_x / count
                return 0 # Default for top-level ancestors or unconnected in-laws

            # Sort hubs by Ancestry X, then by UID for stability
            hubs.sort(key=lambda n: (hub_ancestor_sort_key(n), n.uid))
            
            for hub in hubs:
                if hub in processed: continue
                
                # Find Spouses (Parents of this hub)
                spouses = [p for p in hub.parents if p in raw_nodes]
                
                # Add Spouse 1
                if spouses and spouses[0] not in processed:
                    ordered_nodes.append(spouses[0])
                    processed.add(spouses[0])
                
                # Add Hub
                ordered_nodes.append(hub)
                processed.add(hub)
                
                # Add Spouse 2 (if exists)
                if len(spouses) > 1 and spouses[1] not in processed:
                    ordered_nodes.append(spouses[1])
                    processed.add(spouses[1])
            
            # 2. Add anyone left over (Unmarried / Single nodes / Children)
            remaining = [n for n in raw_nodes if n not in processed]
            
            def child_sort_key(n):
                # Primary: Group by Family (Parent Hub Position)
                # Since we iterate Top-Down, parents (Gen+1) are already placed.
                family_pos = 0
                if n.parents:
                    # Average X of parent hubs
                    family_pos = sum(p.x for p in n.parents) / len(n.parents)
                else:
                    # No parents (Roots): Sort by Age only (via secondary key)
                    # We use a constant to treat them as one "group"
                    family_pos = -99999 
                
                # Secondary: Age (Descending -> Eldest on Left)
                # Use negative age because sort is Ascending
                age = n.agent.age if n.agent else 0
                return (family_pos, -age)

            remaining.sort(key=child_sort_key)
            ordered_nodes.extend(remaining)
            
            # 3. Assign X
            current_x = 0
            for node in ordered_nodes:
                node.x = current_x
                node.y = -1 * node.generation * self.LAYER_HEIGHT
                current_x += node.width + self.GAP_X
            
            # Update the layer list for the subsequent sweep steps
            layers[gen] = ordered_nodes
                
        # Relaxation Loop (Iterative Force-Directed Layout)
        # We alternate between centering nodes (Springs) and preventing overlap (Collisions).
        for _ in range(5): # Increased iterations for stability
            
            # --- 1. Down Sweep (Parents pull Children) ---
            for gen in sorted_gens:
                for node in layers[gen]:
                    if node.is_hub and node.parents:
                        # Hub snaps to center of parents
                        avg_p = sum(p.x for p in node.parents) / len(node.parents)
                        node.x = avg_p
                    elif not node.is_hub and node.parents:
                        # Child pulls towards Parent Hub
                        avg_p = sum(p.x for p in node.parents) / len(node.parents)
                        node.x = (node.x + avg_p) / 2

            # --- 2. Collision Resolution (Down) ---
            for gen in sorted_gens:
                self._resolve_collisions(layers[gen])

            # --- 3. Up Sweep (Children pull Parents) ---
            for gen in reversed(sorted_gens):
                for node in layers[gen]:
                    if node.is_hub and node.children:
                        # Hub pulls towards center of children
                        avg_c = sum(c.x for c in node.children) / len(node.children)
                        node.x = avg_c
                    elif not node.is_hub and node.spouses:
                        # Parent pulls towards their Marriage Hubs
                        avg_s = sum(s.x for s in node.spouses) / len(node.spouses)
                        node.x = (node.x + avg_s) / 2

            # --- 4. Collision Resolution (Up) ---
            for gen in sorted_gens:
                self._resolve_collisions(layers[gen])

        # --- Phase 3b: Final Polish ---
        # Collision resolution shifts agents, which might de-center the Marriage Hubs.
        # We force-snap Hubs back to the exact center of their spouses to ensure perfect T-shapes.
        for node in self.nodes.values():
            if node.is_hub and node.parents:
                avg_p = sum(p.x for p in node.parents) / len(node.parents)
                node.x = avg_p

        # --- Phase 4: Edge Generation ---
        # Convert node links to renderable edges
        for node in self.nodes.values():
            # Parent -> Hub
            if node.is_hub:
                for p in node.parents:
                    self.edges.append((p, node, "SpouseLink"))
            # Hub -> Child
            else:
                for p in node.parents: # p is a Hub
                    self.edges.append((p, node, "ChildLink"))

        # --- Phase 5: Bloodline Tagging ---
        self._mark_blood_relatives(focus_agent.uid)
    def _resolve_collisions(self, layer_nodes):
        """Enforces minimum spacing between nodes in a layer."""
        # Sort by current X to find neighbors
        layer_nodes.sort(key=lambda n: n.x)
        
        # Push Right (A -> B)
        for i in range(len(layer_nodes) - 1):
            n1 = layer_nodes[i]
            n2 = layer_nodes[i+1]
            min_dist = (n1.width / 2) + (n2.width / 2) + self.GAP_X
            if n2.x < n1.x + min_dist:
                n2.x = n1.x + min_dist
        
        # Re-center layer around 0 to prevent drift
        if layer_nodes:
            center = (layer_nodes[0].x + layer_nodes[-1].x) / 2
            for node in layer_nodes:
                node.x -= center

    def _mark_blood_relatives(self, focus_uid):
        """
        Tags nodes as blood relatives if they share a common ancestor with the focus agent.
        """
        # 1. Helper to get all ancestors (Parents, GPs, etc.) of a specific agent
        def get_ancestors(start_uid):
            ancestors = set()
            queue = [start_uid]
            while queue:
                curr = queue.pop(0)
                if curr in ancestors: continue
                ancestors.add(curr)
                
                if curr in self.nodes and self.nodes[curr].agent:
                    agent = self.nodes[curr].agent
                    for rel_uid, rel in agent.relationships.items():
                        if rel.rel_type in ["Father", "Mother"]:
                            queue.append(rel_uid)
            return ancestors

        # 2. Get Focus Agent's Ancestors
        focus_ancestors = get_ancestors(focus_uid)
        
        # 3. Check every node in the graph
        for uid, node in self.nodes.items():
            if node.is_hub or not node.agent:
                continue
                
            # Get this node's ancestors
            my_ancestors = get_ancestors(uid)
            
            # Intersection check: Do we share ANY ancestor?
            # (Note: get_ancestors includes self, so if I am the focus, I share myself)
            common = focus_ancestors.intersection(my_ancestors)
            
            if common:
                node.is_blood = True
            else:
                node.is_blood = False