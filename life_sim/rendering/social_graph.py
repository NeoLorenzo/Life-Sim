# life_sim/rendering/social_graph.py
"""
Social Graph Module.
Handles the visualization of the social network using force-directed physics.
"""
import pygame
import numpy as np
import random
from .. import constants

class SocialGraphLayout:
    """
    Manages the nodes and layout for the Social Map.
    Uses NumPy for vectorized physics calculations.
    """
    def __init__(self):
        self.bounds = None # pygame.Rect
        self.center = np.array([0.0, 0.0])
        
        # Physics State (NumPy Arrays)
        self.count = 0
        self.pos = np.zeros((0, 2), dtype=np.float64)
        self.vel = np.zeros((0, 2), dtype=np.float64)
        
        # Metadata (Lists aligned with arrays)
        self.uids = []
        self.colors = []
        self.radii = []
        self.is_player_mask = [] 
        self.edges = [] 
        self.edge_colors = [] # Cached edge colors
        self.edge_widths = [] # Cached edge widths
        self.player_index = -1
        self.labels = [] # Cached display names for the graph
        self.label_surfaces = {} # Cached font surfaces for labels
        
        # Spatial Indexing for Performance
        self.grid_size = 150  # Size of each grid cell in world coordinates
        self.spatial_grid = {}  # (grid_x, grid_y) -> [node_indices, edge_indices]
        
        # Interaction State
        self.show_all = True 
        self.show_network = False # New Toggle state
        self.drag_index = -1# Index of node being dragged
        self.hover_index = -1 # Index of node being hovered
        self.hover_edge_index = -1 # Index of edge being hovered
        self.pan_offset = np.array([0.0, 0.0])
        self.is_panning = False
        self.last_mouse = (0, 0)
        
        # Zoom State
        self.zoom_level = 1.0
        self.min_zoom = 0.7
        self.max_zoom = 5.0
        self.zoom_speed = 0.05
        
        # Label visibility based on zoom
        self.label_fade_start_zoom = 1.5  # Start fading labels at this zoom level
        self.label_fade_end_zoom = 1.3   # Labels completely invisible below this zoom level

    def _get_relationship_color(self, score):
        """
        Returns RGB color based on relationship score using gradient logic.
        0 -> Light Gray (200,200,200)
        +100 -> Bright Green (50, 255, 50)
        -100 -> Deep Red (220, 20, 20)
        """
        if score >= 0:
            # Green Interpolation (0 -> Light Gray, 100 -> Bright Green)
            t = score / 100.0
            # Light Gray (200,200,200) to Green (50, 255, 50)
            r = int(200 * (1-t) + 50 * t)
            g = int(200 * (1-t) + 255 * t)
            b = int(200 * (1-t) + 50 * t)
        else:
            # Red Interpolation (0 -> Light Gray, -100 -> Deep Red)
            t = abs(score) / 100.0
            # Light Gray (200,200,200) to Red (220, 20, 20)
            r = int(200 * (1-t) + 220 * t)
            g = int(200 * (1-t) + 20 * t)
            b = int(200 * (1-t) + 20 * t)
        return (r, g, b)
    
    def _get_edge_color_and_width(self, rel_val):
        """
        Returns cached color and width for edge based on relationship value.
        """
        if rel_val >= 0:
            # Green Interpolation (0 -> Gray, 100 -> Bright Green)
            t = rel_val / 100.0
            # Gray (150,150,150) to Green (50, 255, 50)
            r = int(150 * (1-t) + 50 * t)
            g = int(150 * (1-t) + 255 * t)
            b = int(150 * (1-t) + 50 * t)
        else:
            # Red Interpolation (0 -> Gray, -100 -> Deep Red)
            t = abs(rel_val) / 100.0
            # Gray (150,150,150) to Red (220, 20, 20)
            r = int(150 * (1-t) + 220 * t)
            g = int(150 * (1-t) + 20 * t)
            b = int(150 * (1-t) + 20 * t)
        
        color = (r, g, b)
        # Base width: 0-100 maps to 1px-4px width
        base_width = max(1, int((abs(rel_val) / 100.0) * 4))
        
        return color, base_width

    def handle_event(self, event, rel_mouse_pos):
        """
        Handles mouse events for the graph.
        rel_mouse_pos: (x, y) relative to the center panel top-left.
        Returns: True if event consumed, False otherwise.
        """
        mx, my = rel_mouse_pos
        
        # Convert mouse position to world coordinates (accounting for zoom and pan)
        world_mx = (mx - self.pan_offset[0] - self.center[0]) / self.zoom_level + self.center[0]
        world_my = (my - self.pan_offset[1] - self.center[1]) / self.zoom_level + self.center[1]
        
        if event.type == pygame.MOUSEMOTION:
            # 1. Handle Panning
            if self.is_panning:
                dx = mx - self.last_mouse[0]
                dy = my - self.last_mouse[1]
                self.pan_offset += np.array([dx, dy])
                self.last_mouse = (mx, my)
                return True
                
            # 2. Handle Node Dragging
            if self.drag_index != -1:
                self.pos[self.drag_index] = [world_mx, world_my]
                self.vel[self.drag_index] = [0, 0] # Stop physics while dragging
                return True
                
            # 3. Handle Hover (Nodes)
            self.hover_index = -1
            self.hover_edge_index = -1
            
            if self.count > 0:
                # Vectorized distance check for Nodes (in world coordinates)
                dists = np.sqrt(np.sum((self.pos - np.array([world_mx, world_my]))**2, axis=1))
                closest = np.argmin(dists)
                # Scale radius threshold by zoom for proper hover detection
                if dists[closest] < (self.radii[closest] + 5 / self.zoom_level):
                    self.hover_index = closest
            
            # 4. Handle Hover (Edges) - Only if not hovering a node
            if self.hover_index == -1 and self.count > 0:
                mouse_p = np.array([world_mx, world_my])
                
                for i, (u, v, val) in enumerate(self.edges):
                    p1 = self.pos[u]
                    p2 = self.pos[v]
                    
                    # Point to Line Segment Distance
                    # Project point onto line (clamped)
                    l2 = np.sum((p1 - p2)**2)
                    if l2 == 0: continue
                    
                    t = np.dot(mouse_p - p1, p2 - p1) / l2
                    t = max(0, min(1, t))
                    projection = p1 + t * (p2 - p1)
                    
                    dist = np.linalg.norm(mouse_p - projection)
                    
                    # Scale distance threshold by zoom for proper hover detection
                    if dist < (5 / self.zoom_level):
                        self.hover_edge_index = i
                        break

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left Click
                if self.hover_index != -1:
                    self.drag_index = self.hover_index
                else:
                    self.is_panning = True
                    self.last_mouse = (mx, my)
                return True
            elif event.button == 4: # Mouse wheel up (zoom in)
                self.zoom_level = min(self.max_zoom, self.zoom_level + self.zoom_speed)
                return True
            elif event.button == 5: # Mouse wheel down (zoom out)
                self.zoom_level = max(self.min_zoom, self.zoom_level - self.zoom_speed)
                return True

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.drag_index = -1
                self.is_panning = False
                return True
                
        return False

    def get_hover_info(self, sim_state):
        """Returns dict of info for the hovered node OR edge."""
        from ..simulation import affinity # Import here to avoid circular imports
        
        # Case A: Hovering Node
        if self.hover_index != -1:
            uid = self.uids[self.hover_index]
            agent = sim_state.player if uid == sim_state.player.uid else sim_state.npcs.get(uid)
            
            if not agent: return None
            
            info = {
                "type": "node",
                "name": f"{agent.first_name} {agent.last_name}",
                "age": f"Age: {agent.age}",
                "job": agent.job['title'] if agent.job else "Unemployed",
                "rel_type": "Self",
                "rel_val": None
            }
            
            if uid != sim_state.player.uid:
                rel = sim_state.player.relationships.get(uid)
                if rel:
                    info["rel_type"] = rel.rel_type
                    info["rel_val"] = rel.total_score
                else:
                    info["rel_type"] = "Stranger"
                    info["rel_val"] = 0
            return info

        # Case B: Hovering Edge
        if self.hover_edge_index != -1:
            u_idx, v_idx, val = self.edges[self.hover_edge_index]
            uid_a = self.uids[u_idx]
            uid_b = self.uids[v_idx]
            
            agent_a = sim_state.player if uid_a == sim_state.player.uid else sim_state.npcs.get(uid_a)
            agent_b = sim_state.player if uid_b == sim_state.player.uid else sim_state.npcs.get(uid_b)
            
            if not agent_a or not agent_b: return None
            
            # Get the actual Relationship object to access modifiers
            # We need to find the relationship object. It could be in A or B.
            rel_obj = agent_a.relationships.get(agent_b.uid)
            
            # Calculate Breakdown (Affinity)
            score, affinity_breakdown = affinity.get_affinity_breakdown(agent_a, agent_b)
            
            # Get Active Modifiers
            modifiers = []
            if rel_obj:
                for mod in rel_obj.modifiers:
                    modifiers.append((mod.name, mod.value))
            
            return {
                "type": "edge",
                "agent_a": agent_a.first_name,
                "agent_b": agent_b.first_name,
                "score": score, # Base Affinity
                "total": rel_obj.total_score if rel_obj else 0,
                "affinity_breakdown": affinity_breakdown,
                "modifiers": modifiers
            }
            
        return None

    def _get_label_opacity(self):
        """
        Calculate label opacity based on current zoom level.
        Returns opacity value (0-255) where 0 = fully transparent, 255 = fully opaque.
        """
        if self.zoom_level >= self.label_fade_start_zoom:
            return 255  # Fully visible
        elif self.zoom_level <= self.label_fade_end_zoom:
            return 0    # Fully invisible
        else:
            # Linear interpolation between fade start and end
            fade_range = self.label_fade_start_zoom - self.label_fade_end_zoom
            fade_progress = (self.zoom_level - self.label_fade_end_zoom) / fade_range
            return int(255 * fade_progress)

    def _build_spatial_grid(self):
        """
        Builds spatial indexing grid for efficient viewport culling.
        Divides world space into grid cells and registers nodes/edges.
        """
        self.spatial_grid.clear()
        
        # Register nodes in grid cells
        for i, (x, y) in enumerate(self.pos):
            grid_x = int(x / self.grid_size)
            grid_y = int(y / self.grid_size)
            key = (grid_x, grid_y)
            
            if key not in self.spatial_grid:
                self.spatial_grid[key] = [[], []]  # [nodes, edges]
            
            self.spatial_grid[key][0].append(i)  # Add node index
        
        # Register edges in grid cells (edges can span multiple cells)
        for edge_idx, (u, v, _) in enumerate(self.edges):
            x1, y1 = self.pos[u]
            x2, y2 = self.pos[v]
            
            # Calculate grid cells this edge passes through
            min_x, max_x = min(x1, x2), max(x1, x2)
            min_y, max_y = min(y1, y2), max(y1, y2)
            
            # Get grid cell range for this edge
            min_grid_x = int(min_x / self.grid_size)
            max_grid_x = int(max_x / self.grid_size)
            min_grid_y = int(min_y / self.grid_size)
            max_grid_y = int(max_y / self.grid_size)
            
            # Register edge in all grid cells it could intersect
            for gx in range(min_grid_x, max_grid_x + 1):
                for gy in range(min_grid_y, max_grid_y + 1):
                    key = (gx, gy)
                    if key not in self.spatial_grid:
                        self.spatial_grid[key] = [[], []]
                    
                    self.spatial_grid[key][1].append(edge_idx)  # Add edge index

    def build(self, sim_state, bounds):
        """
        Initializes nodes and relationship edges.
        """
        self.bounds = bounds
        self.center = np.array([bounds.centerx, bounds.centery], dtype=np.float64)
        
        temp_pos = []
        self.uids = []
        self.colors = []
        self.radii = []
        self.is_player_mask = []
        self.edges = []
        self.edge_colors = [] # Reset edge colors
        self.edge_widths = [] # Reset edge widths
        self.labels = [] # Reset labels
        self.label_surfaces.clear() # Clear cached label surfaces
        
        # Helper to track indices
        uid_to_index = {}
        
        pad = 50
        min_x, max_x = bounds.x + pad, bounds.right - pad
        min_y, max_y = bounds.y + pad, bounds.bottom - pad

        # 1. Add Player
        self.player_index = 0
        self.uids.append(sim_state.player.uid)
        uid_to_index[sim_state.player.uid] = 0
        temp_pos.append([random.uniform(min_x, max_x), random.uniform(min_y, max_y)])
        self.colors.append((255, 255, 255))
        self.radii.append(8)
        self.is_player_mask.append(True)
        self.labels.append("You")

        # 2. Add NPCs
        current_idx = 1
        known_uids = set(sim_state.player.relationships.keys())
        
        for uid, npc in sim_state.npcs.items():
            if not npc.is_alive: continue
            
            # Filter Check
            if not self.show_all and uid not in known_uids:
                continue
                
            self.uids.append(uid)
            uid_to_index[uid] = current_idx
            temp_pos.append([random.uniform(min_x, max_x), random.uniform(min_y, max_y)])
            
            # Create Label (First Name + Last Initial)
            label = f"{npc.first_name} {npc.last_name[0]}."
            self.labels.append(label)
            
            # Determine Color based on Relationship
            rel = sim_state.player.relationships.get(uid)
            if rel:
                col = self._get_relationship_color(rel.total_score)
            else:
                # Neutral light gray for strangers
                col = (200, 200, 200)
                
            self.colors.append(col)
            self.radii.append(5)
            self.is_player_mask.append(False)
            current_idx += 1

        # 3. Build Edges
        # We use a set to avoid duplicates (A->B and B->A are the same edge)
        seen_pairs = set()
        
        def add_edge(uid_a, uid_b, val):
            if uid_a not in uid_to_index or uid_b not in uid_to_index:
                return
            
            idx_a = uid_to_index[uid_a]
            idx_b = uid_to_index[uid_b]
            
            # Sort indices to ensure uniqueness
            if idx_a > idx_b:
                idx_a, idx_b = idx_b, idx_a
                
            pair = (idx_a, idx_b)
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                self.edges.append((idx_a, idx_b, val))

        # A. Player Edges (Always add these)
        for target_uid, rel in sim_state.player.relationships.items():
            add_edge(sim_state.player.uid, target_uid, rel.total_score)
            
        # B. Network Edges (If enabled)
        if self.show_network:
            # Iterate over all currently visible nodes
            for uid in self.uids:
                # Skip player (already handled)
                if uid == sim_state.player.uid: continue
                
                agent = sim_state.npcs.get(uid)
                if not agent: continue
                
                for target_uid, rel in agent.relationships.items():
                    # Only add if target is also visible
                    if target_uid in uid_to_index:
                        add_edge(uid, target_uid, rel.total_score)

        # Convert to NumPy
        self.count = len(self.uids)
        self.pos = np.array(temp_pos, dtype=np.float64)
        self.vel = np.zeros((self.count, 2), dtype=np.float64)
        
        # Pre-calculate edge colors and widths for optimization
        self.edge_colors = []
        self.edge_widths = []
        for _, _, rel_val in self.edges:
            color, width = self._get_edge_color_and_width(rel_val)
            self.edge_colors.append(color)
            self.edge_widths.append(width)
        
        # Cache radii as a numpy array — used every frame for visibility culling
        self._radii_arr = np.array(self.radii, dtype=np.float64)

        # Cache edge arrays as NumPy for vectorized physics
        if self.edges:
            edge_arr = np.array(self.edges, dtype=np.float64)
            self._edge_u   = edge_arr[:, 0].astype(np.intp)
            self._edge_v   = edge_arr[:, 1].astype(np.intp)
            self._edge_vals = edge_arr[:, 2]
            # Plain Python lists for the draw loop — avoids tuple unpack per iteration
            self._edge_u_list = self._edge_u.tolist()
            self._edge_v_list = self._edge_v.tolist()
        else:
            self._edge_u   = np.array([], dtype=np.intp)
            self._edge_v   = np.array([], dtype=np.intp)
            self._edge_vals = np.array([], dtype=np.float64)
            self._edge_u_list = []
            self._edge_v_list = []

        # Pre-allocate workspace arrays for edge visibility culling in draw()
        E = len(self.edges)
        self._edge_vis_u_pos  = np.empty((E, 2), dtype=np.float64)
        self._edge_vis_v_pos  = np.empty((E, 2), dtype=np.float64)
        self._edge_vis_min    = np.empty((E, 2), dtype=np.float64)
        self._edge_vis_max    = np.empty((E, 2), dtype=np.float64)
        self._edge_vis_mask   = np.empty(E, dtype=np.bool_)
        
        # Build spatial grid for efficient viewport culling
        self._build_spatial_grid()

        # Pre-render node surfaces for the current node set and zoom level
        self._rebuild_node_surfaces()

    def update_physics(self):
        """
        Applies force-directed graph logic:
        1. Repulsion (Coulomb's Law-ish)
        2. Center Gravity
        3. Friction
        """
        if self.count == 0: return

        # 1. Repulsion (Vectorized)
        # Calculate delta vectors between all pairs: shape (N, N, 2)
        # diff[i, j] = pos[i] - pos[j]
        diff = self.pos[:, np.newaxis, :] - self.pos[np.newaxis, :, :]
        
        # Distance squared: shape (N, N)
        dist_sq = np.sum(diff**2, axis=2)
        
        # Avoid division by zero (add epsilon to diagonal)
        np.fill_diagonal(dist_sq, np.inf)
        
        # Force magnitude: F = k / d^2
        # We clamp distance to avoid exploding forces for very close nodes
        dist_sq = np.maximum(dist_sq, 1.0)
        force_mag = constants.GRAPH_REPULSION / dist_sq
        
        forces = diff * force_mag[:, :, np.newaxis]
        
        # Sum forces acting on each node i (sum over j)
        total_force = np.sum(forces, axis=1)

        # 2a. Center Gravity (Pull towards center of bounds)
        center_vec = self.center - self.pos
        total_force += center_vec * constants.GRAPH_CENTER_GRAVITY

        # 2b. Spring Attraction (Vectorized)
        if len(self.edges) > 0:
            # Pre-built edge arrays (cache these in build() as self._edge_u, etc.)
            u_idx = self._edge_u          # shape (E,)
            v_idx = self._edge_v          # shape (E,)
            rel_vals = self._edge_vals    # shape (E,) float64

            # --- Geometry (all vectorized) ---
            delta = self.pos[u_idx] - self.pos[v_idx]          # (E, 2)
            dist  = np.linalg.norm(delta, axis=1)              # (E,)

            # Mask out edges shorter than min distance
            valid = dist >= constants.GRAPH_MIN_DISTANCE       # (E,) bool
            # Avoid division by zero on invalid entries
            safe_dist = np.where(valid, dist, 1.0)
            direction = delta / safe_dist[:, np.newaxis]       # (E, 2)

            # --- Piecewise factor calculation (vectorized) ---
            factor = np.zeros_like(rel_vals)

            # Negative relationships: linear repulsion
            neg = rel_vals < 0
            factor[neg] = -constants.GRAPH_NEGATIVE_REPULSION_MAX * (np.abs(rel_vals[neg]) / 100.0)

            # Weak bonds: 0 to WEAK_THRESHOLD
            w = constants.GRAPH_WEAK_BOND_THRESHOLD
            m = constants.GRAPH_MODERATE_BOND_THRESHOLD
            weak  = (~neg) & (rel_vals <= w)
            factor[weak] = (constants.GRAPH_WEAK_ATTRACTION_MIN +
                            (rel_vals[weak] / w) *
                            (constants.GRAPH_WEAK_ATTRACTION_MAX - constants.GRAPH_WEAK_ATTRACTION_MIN))

            # Moderate bonds: WEAK_THRESHOLD to MODERATE_THRESHOLD
            mod = (~neg) & (rel_vals > w) & (rel_vals <= m)
            factor[mod] = (constants.GRAPH_MODERATE_ATTRACTION_MIN +
                        ((rel_vals[mod] - w) / (m - w)) *
                        (constants.GRAPH_MODERATE_ATTRACTION_MAX - constants.GRAPH_MODERATE_ATTRACTION_MIN))

            # Strong bonds: MODERATE_THRESHOLD to 100
            strong = (~neg) & (rel_vals > m)
            factor[strong] = (constants.GRAPH_STRONG_ATTRACTION_MIN +
                            ((rel_vals[strong] - m) / (100.0 - m)) *
                            (constants.GRAPH_STRONG_ATTRACTION_MAX - constants.GRAPH_STRONG_ATTRACTION_MIN))

            # --- Force application (vectorized scatter) ---
            force_mag = (constants.GRAPH_ATTRACTION * factor * valid)[:, np.newaxis]  # (E, 1)
            force     = direction * force_mag                                          # (E, 2)

            # np.add.at handles duplicate indices correctly (unlike +=)
            np.add.at(total_force, v_idx,  force)   # Pull v toward u
            np.add.at(total_force, u_idx, -force)   # Pull u toward v (Newton's 3rd)

        # 3. Integration (Euler)
        self.vel += total_force * constants.GRAPH_SPEED * constants.GRAPH_TIME_STEP
        self.vel *= constants.GRAPH_FRICTION # Damping
        self.pos += self.vel

    # --- Call this once in build(), and again whenever zoom changes ---
    def _rebuild_node_surfaces(self):
        """
        Pre-renders every unique node appearance (color + scaled radius) to a small
        surface. A blit is a single memcpy; two draw.circle calls are not.
        Also caches the hover surface for each unique radius.
        """
        self._node_surfaces = {}        # (color, scaled_radius) -> Surface
        self._hover_surfaces = {}       # scaled_radius -> Surface
        self._scaled_radii = []         # flat list, one int per node

        for i in range(self.count):
            r = max(3, int(self.radii[i] * self.zoom_level))
            self._scaled_radii.append(r)

            color = self.colors[i]
            key = (color, r)
            if key not in self._node_surfaces:
                size = r * 2 + 2          # +1px border on each side
                surf = pygame.Surface((size, size), pygame.SRCALPHA)
                pygame.draw.circle(surf, color, (r + 1, r + 1), r)
                pygame.draw.circle(surf, constants.COLOR_BG, (r + 1, r + 1), r, 1)
                self._node_surfaces[key] = surf

            if r not in self._hover_surfaces:
                hr = r + 2
                size = hr * 2 + 2
                surf = pygame.Surface((size, size), pygame.SRCALPHA)
                pygame.draw.circle(surf, (255, 255, 0), (hr + 1, hr + 1), hr)
                self._hover_surfaces[r] = surf

        # Pre-scale edge widths for current zoom — recomputed only when zoom changes
        self._scaled_edge_widths = [max(1, int(w * self.zoom_level)) for w in self.edge_widths]

        # Pre-allocate label rects (one per node) — mutated in-place each frame
        self._label_rects = [pygame.Rect(0, 0, 1, 1) for _ in range(self.count)]

        # Cache the last zoom level used so draw() knows when to rebuild
        self._last_zoom_for_surfaces = self.zoom_level

    def draw(self, screen, font):
        """Draws the nodes and edges with pan offset and zoom."""
        if self.count == 0: return

        # Rebuild pre-rendered node surfaces only if zoom changed since last build
        if self._last_zoom_for_surfaces != self.zoom_level:
            self._rebuild_node_surfaces()

        # --- Transform all positions once, then drop into plain Python lists.
        #     Indexing a Python list with a Python int is a direct pointer lookup.
        #     Indexing a numpy array with anything triggers bounds-check + view overhead. ---
        center_offset = self.center
        scaled_pos = (self.pos - center_offset) * self.zoom_level + center_offset
        draw_pos_list = (scaled_pos + self.pan_offset).astype(int).tolist()  # list of [x, y]

        # --- Viewport bounds in world coordinates ---
        screen_width, screen_height = constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT
        culling_padding = 100 / self.zoom_level
        vp_left   = (-self.pan_offset[0] - center_offset[0]) / self.zoom_level + center_offset[0] - culling_padding
        vp_right  = (screen_width  - self.pan_offset[0] - center_offset[0]) / self.zoom_level + center_offset[0] + culling_padding
        vp_top    = (-self.pan_offset[1] - center_offset[1]) / self.zoom_level + center_offset[1] - culling_padding
        vp_bottom = (screen_height - self.pan_offset[1] - center_offset[1]) / self.zoom_level + center_offset[1] + culling_padding

        # --- Vectorized visibility masks (computed once in NumPy) ---
        node_visible = ((self.pos[:, 0] >= vp_left  - self._radii_arr) &
                        (self.pos[:, 0] <= vp_right + self._radii_arr) &
                        (self.pos[:, 1] >= vp_top   - self._radii_arr) &
                        (self.pos[:, 1] <= vp_bottom + self._radii_arr))
        # .tolist() converts to plain Python ints — fast path for all indexing below
        visible_indices = np.flatnonzero(node_visible).tolist()

        if len(self.edges) > 0:
            # Reuse pre-allocated workspace — zero allocations in this block
            np.take(self.pos, self._edge_u, axis=0, out=self._edge_vis_u_pos)
            np.take(self.pos, self._edge_v, axis=0, out=self._edge_vis_v_pos)
            np.minimum(self._edge_vis_u_pos, self._edge_vis_v_pos, out=self._edge_vis_min)
            np.maximum(self._edge_vis_u_pos, self._edge_vis_v_pos, out=self._edge_vis_max)
            np.greater_equal(self._edge_vis_max[:, 0], vp_left,  out=self._edge_vis_mask)
            self._edge_vis_mask &= (self._edge_vis_min[:, 0] <= vp_right)
            self._edge_vis_mask &= (self._edge_vis_max[:, 1] >= vp_top)
            self._edge_vis_mask &= (self._edge_vis_min[:, 1] <= vp_bottom)
            visible_edge_indices = np.flatnonzero(self._edge_vis_mask).tolist()
        else:
            visible_edge_indices = []

        # --- Local variable binds: pulls attribute lookups out of hot loops.
        #     `self.X` is a dict lookup (type.__getattribute__) every iteration;
        #     a local is a single LOAD_FAST bytecode op. ---
        edges           = self.edges
        edge_colors     = self.edge_colors
        scaled_edge_widths = self._scaled_edge_widths
        hover_edge      = self.hover_edge_index
        hover_node      = self.hover_index
        node_surfaces   = self._node_surfaces
        hover_surfaces  = self._hover_surfaces
        scaled_radii    = self._scaled_radii
        colors          = self.colors
        labels          = self.labels
        label_surfaces  = self.label_surfaces
        zoom            = self.zoom_level
        draw_line       = pygame.draw.line
        blit            = screen.blit

        # --- 1. Draw Edges ---
        edge_u_list     = self._edge_u_list
        edge_v_list     = self._edge_v_list

        for i in visible_edge_indices:
            color = edge_colors[i]
            width = scaled_edge_widths[i]   # pre-scaled, see change #4

            if i == hover_edge:
                color = (255, 255, 200)
                width += 2

            draw_line(screen, color, draw_pos_list[edge_u_list[i]], draw_pos_list[edge_v_list[i]], width)

        # --- 2. Draw Nodes (blit pre-rendered surfaces — no draw.circle in loop) ---
        for i in visible_indices:
            r = scaled_radii[i]
            pos = draw_pos_list[i]
            # blit rect top-left = center - (r+1) for the +1px border padding in surface
            blit_x = pos[0] - r - 1
            blit_y = pos[1] - r - 1

            if i == hover_node:
                hr = r + 2
                hover_surf = hover_surfaces[r]
                blit(hover_surf, (blit_x - 2, blit_y - 2))

            blit(node_surfaces[(colors[i], r)], (blit_x, blit_y))

        # --- 3. Draw Labels ---
        label_opacity = self._get_label_opacity()
        if label_opacity > 0:
            label_rects = self._label_rects

            for i in visible_indices:
                pos = draw_pos_list[i]
                label = labels[i]

                cache_key = (label, label_opacity)
                surf = label_surfaces.get(cache_key)
                if surf is None:
                    base = font.render(label, True, constants.COLOR_TEXT)
                    if label_opacity < 255:
                        base.set_alpha(label_opacity)
                    label_surfaces[cache_key] = base
                    surf = base

                # Mutate pre-allocated Rect in place — no allocation
                rect = label_rects[i]
                rect.width  = surf.get_width()
                rect.height = surf.get_height()
                rect.centerx = pos[0]
                rect.centery = pos[1] - scaled_radii[i] - 10
                blit(surf, rect)