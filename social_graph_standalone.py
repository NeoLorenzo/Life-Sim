#!/usr/bin/env python3
"""
Social Graph Standalone Script.
Creates a window with agents that all know each other and displays their social network.
"""
import sys
import json
import logging
import pygame
import random
import numpy as np
import cProfile
import pstats
import io
import time
from pathlib import Path

# ============================================================================
# EASY CONFIGURATION - Change this value to adjust the number of agents
# ============================================================================
NUM_AGENTS = 10  # <-- CHANGE THIS NUMBER TO SET AGENT COUNT (recommended: 5-50)
# ============================================================================

# Add the life_sim package to the path
sys.path.insert(0, str(Path(__file__).parent))

from life_sim import constants, logging_setup
from life_sim.simulation.state import SimState
from life_sim.simulation import affinity
from life_sim.rendering.social_graph import SocialGraphLayout

# Profiling setup
profiler = cProfile.Profile()
profile_stats = {}  # Will store (timestamp, execution_time) tuples

# Real-time profiling display
class RealTimeProfiler:
    def __init__(self, font):
        self.font = font
        self.frame_times = []
        self.max_frames = 60  # Track last 60 frames for FPS
        self.last_frame_time = time.perf_counter()
        self.enabled = True
        self.time_window = 10.0  # Show stats from last 10 seconds only
        
    def update_frame_time(self):
        """Update frame timing for FPS calculation."""
        current_time = time.perf_counter()
        frame_time = current_time - self.last_frame_time
        self.last_frame_time = current_time
        
        self.frame_times.append(frame_time)
        if len(self.frame_times) > self.max_frames:
            self.frame_times.pop(0)
    
    def get_fps(self):
        """Calculate current FPS."""
        if len(self.frame_times) < 2:
            return 0
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        return 1.0 / avg_frame_time if avg_frame_time > 0 else 0
    
    def draw(self, screen, social_graph):
        """Draw real-time profiling information."""
        if not self.enabled:
            return
            
        # Calculate FPS
        fps = self.get_fps()
        
        # Get current time for filtering
        current_time = time.perf_counter()
        cutoff_time = current_time - self.time_window
        
        # Filter and calculate function statistics from last 10 seconds
        total_time = 0
        func_stats = []
        
        for func_name, time_data in profile_stats.items():
            # Filter out old data
            recent_times = [t for timestamp, t in time_data if timestamp >= cutoff_time]
            if recent_times:
                avg_time = sum(recent_times) / len(recent_times)
                total_time += avg_time
                func_stats.append((func_name, avg_time, len(recent_times)))
        
        # Sort by time (descending)
        func_stats.sort(key=lambda x: x[1], reverse=True)
        
        # Position on right side of screen
        overlay_width = 450  # Increased from 350 to prevent truncation
        overlay_height = 220  # Increased height for time window info
        overlay_x = screen.get_width() - overlay_width - 10
        overlay_y = 10
        
        # Draw semi-transparent background
        overlay_rect = pygame.Rect(overlay_x, overlay_y, overlay_width, overlay_height)
        overlay_surface = pygame.Surface((overlay_rect.width, overlay_rect.height))
        overlay_surface.set_alpha(200)
        overlay_surface.fill((40, 40, 40))
        screen.blit(overlay_surface, overlay_rect)
        
        # Draw border
        pygame.draw.rect(screen, (100, 100, 100), overlay_rect, 2)
        
        # Draw title
        title_text = self.font.render("REAL-TIME PROFILER (10s window)", True, (100, 255, 100))
        screen.blit(title_text, (overlay_x + 10, overlay_y + 5))
        
        # Draw FPS
        fps_color = (100, 255, 100) if fps >= 55 else (255, 255, 100) if fps >= 30 else (255, 100, 100)
        fps_text = self.font.render(f"FPS: {fps:.1f}", True, fps_color)
        screen.blit(fps_text, (overlay_x + 10, overlay_y + 30))
        
        # Draw graph info
        graph_text = self.font.render(f"Nodes: {social_graph.count}, Edges: {len(social_graph.edges)}", True, (200, 200, 200))
        screen.blit(graph_text, (overlay_x + 10, overlay_y + 50))
        
        # Draw function timing
        y_offset = 75
        for func_name, avg_time, calls in func_stats[:6]:  # Show top 6 functions
            if total_time > 0:
                percentage = (avg_time / total_time) * 100
            else:
                percentage = 0
            
            # Color code by performance
            if percentage > 40:
                color = (255, 100, 100)  # Red - high load
            elif percentage > 20:
                color = (255, 255, 100)  # Yellow - medium load
            else:
                color = (100, 255, 100)  # Green - low load
            
            # Truncate function name if too long
            display_name = func_name[:25] + "..." if len(func_name) > 25 else func_name
            
            func_text = self.font.render(f"{display_name}: {avg_time*1000:.1f}ms ({percentage:.1f}%)", True, color)
            screen.blit(func_text, (overlay_x + 10, overlay_y + y_offset))
            y_offset += 18
        
        # Draw controls hint
        hint_text = self.font.render("Press P to toggle profiler", True, (150, 150, 150))
        screen.blit(hint_text, (overlay_x + 10, overlay_y + 205))

# Global profiler instance
real_time_profiler = None

def profile_function(func_name):
    """Decorator to profile individual functions."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            
            if func_name not in profile_stats:
                profile_stats[func_name] = []
            
            # Store (timestamp, execution_time) tuple
            profile_stats[func_name].append((end_time, end_time - start_time))
            
            # Clean old data to prevent memory leak (keep last 30 seconds)
            cutoff_time = end_time - 30.0
            profile_stats[func_name] = [(ts, t) for ts, t in profile_stats[func_name] if ts >= cutoff_time]
            
            return result
        return wrapper
    return decorator

def print_profile_stats():
    """Print detailed profiling statistics."""
    print("\n" + "="*80)
    print("DETAILED PROFILING STATISTICS")
    print("="*80)
    
    # Get current time for filtering
    current_time = time.perf_counter()
    cutoff_time = current_time - 10.0  # Last 10 seconds
    
    # Function call statistics
    print("\nFUNCTION CALL TIMING (Last 10 seconds):")
    print("-" * 50)
    for func_name, time_data in profile_stats.items():
        # Filter out old data
        recent_times = [t for timestamp, t in time_data if timestamp >= cutoff_time]
        if recent_times:
            avg_time = sum(recent_times) / len(recent_times)
            total_time = sum(recent_times)
            min_time = min(recent_times)
            max_time = max(recent_times)
            print(f"{func_name}:")
            print(f"  Calls: {len(recent_times)}")
            print(f"  Total: {total_time:.4f}s")
            print(f"  Average: {avg_time:.4f}s")
            print(f"  Min: {min_time:.4f}s")
            print(f"  Max: {max_time:.4f}s")
            print()
    
    # cProfile statistics
    print("\nCPROFILE STATISTICS:")
    print("-" * 50)
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(20)  # Top 20 functions
    print(s.getvalue())
    
    print("="*80)

@profile_function("load_config")
def load_config():
    """Load configuration from config.json."""
    try:
        with open(constants.CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"CRITICAL: {constants.CONFIG_FILE} not found.")
        sys.exit(1)

# Global variables for dynamic agent management
current_agents = []  # Track current agents

@profile_function("add_agent")
def add_agent(sim_state, social_graph, bounds):
    """Add a new agent to the simulation."""
    global current_agents
    
    # Create new agent
    new_agent = sim_state._create_npc()
    current_agents.append(new_agent)
    
    # Create relationships with all existing agents
    for existing_agent in current_agents:
        if existing_agent.uid != new_agent.uid:
            sim_state._link_agents(
                new_agent, existing_agent,
                "Acquaintance", "Acquaintance",
                "Network_Connection", random.uniform(-20, 80)
            )
    
    # Rebuild the graph
    social_graph.build(sim_state, bounds)
    
    print(f"Added agent {new_agent.first_name} {new_agent.last_name}. Total agents: {len(current_agents)}")
    return new_agent

@profile_function("remove_agent")
def remove_agent(sim_state, social_graph, bounds, agent_uid=None):
    """Remove an agent from the simulation."""
    global current_agents
    
    if not current_agents:
        print("No agents to remove")
        return None
    
    # If no specific agent specified, remove the last one added
    if agent_uid is None:
        agent_to_remove = current_agents[-1]
    else:
        # Find the agent with the specified UID
        agent_to_remove = None
        for agent in current_agents:
            if agent.uid == agent_uid:
                agent_to_remove = agent
                break
        
        if agent_to_remove is None:
            print(f"Agent with UID {agent_uid} not found")
            return None
    
    # Remove relationships from other agents
    for other_agent in current_agents:
        if other_agent.uid != agent_to_remove.uid:
            other_agent.relationships.pop(agent_to_remove.uid, None)
    
    # Remove from simulation state
    sim_state.npcs.pop(agent_to_remove.uid, None)
    
    # Remove from current agents list
    current_agents.remove(agent_to_remove)
    
    # Rebuild the graph
    social_graph.build(sim_state, bounds)
    
    print(f"Removed agent {agent_to_remove.first_name} {agent_to_remove.last_name}. Total agents: {len(current_agents)}")
    return agent_to_remove

@profile_function("create_fully_connected_agents")
def create_fully_connected_agents(sim_state, num_agents=None):
    """Create agents that all know each other."""
    global current_agents
    
    if num_agents is None:
        num_agents = NUM_AGENTS
    
    print(f"Creating {num_agents} fully connected agents...")
    
    # Create the agents
    agents = []
    for i in range(num_agents):
        agent = sim_state._create_npc()
        agents.append(agent)
    
    # Store in global variable
    current_agents = agents
    
    # Create fully connected network
    print("Creating fully connected relationships...")
    for i, agent_a in enumerate(agents):
        for j, agent_b in enumerate(agents):
            if i < j:  # Avoid duplicate relationships
                # Create bidirectional relationships
                sim_state._link_agents(
                    agent_a, agent_b, 
                    "Acquaintance", "Acquaintance",
                    "Network_Connection", random.uniform(-20, 80)
                )
    
    print(f"Created {len(agents)} agents with {len(agents) * (len(agents) - 1) // 2} relationships")
    return agents

@profile_function("SocialGraph.update_physics")
def profiled_update_physics(social_graph):
    """Profile wrapper for physics updates."""
    return social_graph.update_physics()

@profile_function("SocialGraph.draw")
def profiled_draw_graph(social_graph, screen, font):
    """Profile wrapper for drawing operations."""
    return social_graph.draw(screen, font)

@profile_function("SocialGraph.handle_event")
def profiled_handle_events(social_graph, events, mouse_pos):
    """Profile wrapper for event handling."""
    for event in events:
        social_graph.handle_event(event, mouse_pos)

def main():
    """Main function to run the standalone social graph."""
    # Start global profiling
    profiler.enable()
    
    # 1. Load Config
    config = load_config()
    
    # 2. Setup Logging
    logging_setup.setup_logging(config)
    logger = logging.getLogger("social_graph_standalone")
    
    # 3. Initialize RNG
    seed = config.get("seed", 42)
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Social Graph Standalone started. Seed: {seed}")
    
    # 4. Initialize Pygame
    pygame.init()
    screen = pygame.display.set_mode((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
    pygame.display.set_caption(f"Social Graph - {NUM_AGENTS} Fully Connected Agents")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 20)
    
    # 5. Initialize Simulation State
    sim_state = SimState(config)
    
    # 6. Create fully connected agents
    agents = create_fully_connected_agents(sim_state, NUM_AGENTS)
    
    # 7. Initialize Social Graph
    social_graph = SocialGraphLayout()
    social_graph.show_all = True
    social_graph.show_network = True  # Show all relationships
    
    # 8. Initialize Real-time Profiler
    global real_time_profiler
    real_time_profiler = RealTimeProfiler(font)
    
    # 9. Build the graph with full screen bounds
    bounds = pygame.Rect(0, 0, constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT)
    social_graph.build(sim_state, bounds)
    
    # 10. Main Loop
    running = True
    frame_count = 0
    loop_start_time = time.perf_counter()
    
    while running:
        # Update frame timing for FPS
        real_time_profiler.update_frame_time()
        
        # Event Handling
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    # Reset zoom and pan
                    social_graph.zoom_level = 1.0
                    social_graph.pan_offset = np.array([0.0, 0.0])
                elif event.key == pygame.K_r:
                    # Rebuild graph
                    social_graph.build(sim_state, bounds)
                elif event.key == pygame.K_p:
                    # Toggle profiler
                    real_time_profiler.enabled = not real_time_profiler.enabled
                elif event.key == pygame.K_a:
                    # Add a new agent
                    add_agent(sim_state, social_graph, bounds)
                elif event.key == pygame.K_d:
                    # Remove an agent
                    remove_agent(sim_state, social_graph, bounds)
                elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                    # Add multiple agents (5 at a time)
                    for _ in range(5):
                        add_agent(sim_state, social_graph, bounds)
                elif event.key == pygame.K_MINUS:
                    # Remove multiple agents (5 at a time)
                    for _ in range(5):
                        if len(current_agents) > 0:
                            remove_agent(sim_state, social_graph, bounds)
        
        # Handle mouse events for the social graph
        mouse_pos = pygame.mouse.get_pos()
        profiled_handle_events(social_graph, events, mouse_pos)
        
        # Update physics periodically
        if frame_count % 2 == 0:  # Update every 2 frames for performance
            profiled_update_physics(social_graph)
        
        # Clear screen
        screen.fill(constants.COLOR_BG)
        
        # Draw social graph
        profiled_draw_graph(social_graph, screen, font)
        
        # Draw real-time profiler overlay
        real_time_profiler.draw(screen, social_graph)
        
        # Draw UI text
        info_texts = [
            f"Social Graph - {len(current_agents)} Fully Connected Agents",
            "Controls:",
            "  Mouse Wheel: Zoom in/out",
            "  Left Click + Drag: Pan view or drag nodes",
            "  Space: Reset view",
            "  R: Rebuild graph",
            "  P: Toggle profiler",
            "  A: Add 1 agent",
            "  D: Remove 1 agent",
            "  +: Add 5 agents",
            "  -: Remove 5 agents",
            "  ESC: Exit",
            f"Nodes: {social_graph.count}",
            f"Edges: {len(social_graph.edges)}",
            f"Zoom: {social_graph.zoom_level:.2f}x"
        ]
        
        y_offset = 10
        for text in info_texts:
            text_surface = font.render(text, True, constants.COLOR_TEXT)
            screen.blit(text_surface, (10, y_offset))
            y_offset += 25
        
        # Show hover info
        hover_info = social_graph.get_hover_info(sim_state)
        if hover_info:
            if hover_info["type"] == "node":
                hover_text = f"{hover_info['name']} ({hover_info['age']}) - {hover_info['job']}"
            else:  # edge
                hover_text = f"{hover_info['agent_a']} - {hover_info['agent_b']}: {hover_info['total']}"
            
            text_surface = font.render(hover_text, True, constants.COLOR_ACCENT)
            screen.blit(text_surface, (10, constants.SCREEN_HEIGHT - 30))
        
        # Update display
        pygame.display.flip()
        clock.tick(constants.FPS)
        frame_count += 1
        
        # Print profiling info every 60 frames (1 second at 60 FPS)
        if frame_count % 60 == 0:
            current_time = time.perf_counter()
            elapsed = current_time - loop_start_time
            fps = frame_count / elapsed
            print(f"Frame {frame_count}: FPS={fps:.1f}, Nodes={social_graph.count}, Edges={len(social_graph.edges)}")
    
    # Stop profiling and print results
    profiler.disable()
    print_profile_stats()
    
    # Cleanup
    pygame.quit()
    logger.info("Social Graph Standalone ended cleanly.")

if __name__ == "__main__":
    main()
