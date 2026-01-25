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
        self.player_index = -1
        self.labels = [] # Cached display names for the graph
        
        # Interaction State
        self.show_all = True 
        self.show_network = False # New Toggle state
        self.drag_index = -1# Index of node being dragged
        self.hover_index = -1 # Index of node being hovered
        self.pan_offset = np.array([0.0, 0.0])
        self.is_panning = False
        self.last_mouse = (0, 0)

    def handle_event(self, event, rel_mouse_pos):
        """
        Handles mouse events for the graph.
        rel_mouse_pos: (x, y) relative to the center panel top-left.
        Returns: True if event consumed, False otherwise.
        """
        mx, my = rel_mouse_pos
        # Adjust for Pan
        world_mx = mx - self.pan_offset[0]
        world_my = my - self.pan_offset[1]
        
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
                
            # 3. Handle Hover
            # Simple distance check (brute force is fine for <1000 nodes)
            self.hover_index = -1
            if self.count > 0:
                # Vectorized distance check
                dists = np.sqrt(np.sum((self.pos - np.array([world_mx, world_my]))**2, axis=1))
                # Find closest within radius
                closest = np.argmin(dists)
                if dists[closest] < (self.radii[closest] + 5):
                    self.hover_index = closest

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left Click
                if self.hover_index != -1:
                    self.drag_index = self.hover_index
                else:
                    self.is_panning = True
                    self.last_mouse = (mx, my)
                return True

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.drag_index = -1
                self.is_panning = False
                return True
                
        return False

    def get_hover_info(self, sim_state):
        """Returns dict of info for the hovered node."""
        if self.hover_index == -1: return None
        
        uid = self.uids[self.hover_index]
        agent = sim_state.player if uid == sim_state.player.uid else sim_state.npcs.get(uid)
        
        if not agent: return None
        
        info = {
            "name": f"{agent.first_name} {agent.last_name}",
            "age": f"Age: {agent.age}",
            "job": agent.job['title'] if agent.job else "Unemployed",
            "rel_type": "Self",
            "rel_val": None
        }
        
        if uid != sim_state.player.uid:
            rel = sim_state.player.relationships.get(uid)
            if rel:
                info["rel_type"] = rel['type']
                info["rel_val"] = rel['value']
            else:
                info["rel_type"] = "Stranger"
                info["rel_val"] = 0
                
        return info

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
        self.labels = [] # Reset labels
        
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
                val = rel['value']
                if val > 60:
                    col = constants.COLOR_LOG_POSITIVE # Greenish
                elif val < 40:
                    col = constants.COLOR_LOG_NEGATIVE # Reddish
                else:
                    col = constants.COLOR_ACCENT # Blueish/Neutral
            else:
                col = constants.COLOR_TEXT_DIM # Gray (Stranger)
                
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
            add_edge(sim_state.player.uid, target_uid, rel['value'])
            
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
                        add_edge(uid, target_uid, rel['value'])

        # Convert to NumPy
        self.count = len(self.uids)
        self.pos = np.array(temp_pos, dtype=np.float64)
        self.vel = np.zeros((self.count, 2), dtype=np.float64)

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
        
        # 2. Center Gravity (Pull towards screen center)
        to_center = self.center - self.pos
        total_force += to_center * constants.GRAPH_CENTER_GRAVITY
        
        # 2b. Spring Attraction (Generic Edges)
        for u, v, rel_val in self.edges:
            # Vector from V to U
            delta = self.pos[u] - self.pos[v]
            
            # Strength factor
            # Base attraction for any link is 1.0.
            # A relationship of 100 adds 1.0 (Total 2.0, which is 2x of 0).
            # A relationship of -100 adds -2.0 (Total -1.0, which is repulsion).
            if rel_val >= 0:
                factor = 1.0 + (rel_val / 100.0)
            else:
                factor = -2.0 + (rel_val / 100.0)
            
            force = delta * constants.GRAPH_ATTRACTION * factor
            
            # Pull V towards U (or push away if factor is negative)
            total_force[v] += force
            # Pull U towards V
            total_force[u] -= force

        # 3. Integration (Euler)
        self.vel += total_force * constants.GRAPH_SPEED * 0.01 # Time step factor
        self.vel *= constants.GRAPH_FRICTION # Damping
        self.pos += self.vel
        
        # 4. Hard Boundary Constraint (Bounce)
        # Left/Right
        np.clip(self.pos[:, 0], self.bounds.left + 10, self.bounds.right - 10, out=self.pos[:, 0])
        # Top/Bottom
        np.clip(self.pos[:, 1], self.bounds.top + 10, self.bounds.bottom - 10, out=self.pos[:, 1])

    def draw(self, screen, font):
        """Draws the nodes and edges with pan offset."""
        if self.count == 0: return

        # Apply Pan Offset for drawing
        draw_pos = (self.pos + self.pan_offset).astype(int)
        
        # 1. Draw Edges
        for u, v, rel_val in self.edges:
            p1 = draw_pos[u]
            p2 = draw_pos[v]
            
            # Color Logic
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
            
            # Thickness Logic (Based purely on intensity)
            # 0-100 maps to 1px-4px width
            width = max(1, int((abs(rel_val) / 100.0) * 4))
                
            pygame.draw.line(screen, color, p1, p2, width)

        # 2. Draw Nodes & Labels
        # ... (Rest of draw method remains identical)
        for i in range(self.count):
            x, y = draw_pos[i]
            color = self.colors[i]
            radius = self.radii[i]
            
            # Highlight Hover
            if i == self.hover_index:
                pygame.draw.circle(screen, (255, 255, 0), (x, y), radius + 2)
            
            pygame.draw.circle(screen, color, (x, y), radius)
            pygame.draw.circle(screen, constants.COLOR_BG, (x, y), radius, 1)
            
            # Draw Label
            label_surf = font.render(self.labels[i], True, constants.COLOR_TEXT)
            label_rect = label_surf.get_rect(center=(x, y - radius - 10))
            screen.blit(label_surf, label_rect)