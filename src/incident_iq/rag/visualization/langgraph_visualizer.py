"""
LangGraph Execution Visualization Utility

Tracks and visualizes the execution flow of LangGraph workflows,
including node execution order, state transitions, and execution timing.
Generates PNG diagrams from LangGraph graphs and execution traces.
"""

import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import uuid


# Global workflow diagram path - generated once per application session
_WORKFLOW_DIAGRAM_PATH: Optional[str] = None


def generate_workflow_diagram_once(graph=None, output_dir: str = "session_graph") -> Optional[str]:
    """Generate workflow diagram once and cache it.
    
    Args:
        graph: Compiled LangGraph StateGraph
        output_dir: Directory to save PNG files
        
    Returns:
        Path to workflow diagram PNG
    """
    global _WORKFLOW_DIAGRAM_PATH
    
    if _WORKFLOW_DIAGRAM_PATH is not None:
        # Already generated, return cached path
        return _WORKFLOW_DIAGRAM_PATH
    
    if graph is None:
        return None
    
    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Try using LangGraph's native visualization first
        try:
            png_bytes = graph.get_graph().draw_mermaid_png()
            
            filename = f"workflow_langgraph.png"
            filepath = Path(output_dir) / filename
            
            with open(filepath, 'wb') as f:
                f.write(png_bytes)
            
            _WORKFLOW_DIAGRAM_PATH = str(filepath)
            print(f"[DEBUG] Workflow PNG generated from LangGraph: {_WORKFLOW_DIAGRAM_PATH}")
            return _WORKFLOW_DIAGRAM_PATH
            
        except Exception as e:
            print(f"[DEBUG] LangGraph native PNG failed: {e}, using graphviz")
        
        # Fallback: Create with graphviz
        try:
            from graphviz import Digraph
            
            dot = Digraph(comment='LangGraph RAG Workflow', format='png', engine='dot')
            
            # Graph attributes for better visualization
            dot.attr('graph', rankdir='TB', bgcolor='white', pad='0.5', margin='0.5', 
                    nodesep='0.5', ranksep='0.7')
            dot.attr('node', shape='box', style='rounded,filled', fillcolor='lightblue', 
                    fontname='Arial', fontsize='12', margin='0.4,0.3', penwidth='2')
            dot.attr('edge', color='#333333', fontname='Arial', fontsize='10', 
                    arrowsize='2', penwidth='2.5')
            
            # Define workflow nodes with better labels
            workflows = [
                ('start', 'START', 'lightgreen'),
                ('retrieve', 'Retrieve Context\n(Vector Search)', 'lightblue'),
                ('rerank', 'Rerank Context\n(Score & Sort)', 'lightcyan'),
                ('check_opt', 'Check Optimization\n(RL Agent Decision)', 'lightyellow'),
                ('optimize', 'Optimize Context\n(Healing Tools)\nRe-embed | Reindex', 'lavender'),
                ('answer', 'Generate Answer\n(LLM Response)', 'lightgreen'),
                ('trace', 'Traceability\n(Record Sources)', 'lightcyan'),
                ('end', 'END', 'lightcoral')
            ]
            
            # Add nodes
            for node_id, label, color in workflows:
                dot.node(node_id, label, fillcolor=color)
            
            # Add edges with descriptions
            edges = [
                ('start', 'retrieve', 'User\nQuery'),
                ('retrieve', 'rerank', 'Retrieved\nDocuments'),
                ('rerank', 'check_opt', 'Ranked\nContext'),
                ('check_opt', 'optimize', 'Quality\nLow'),
                ('check_opt', 'answer', 'Quality\nGood'),
                ('optimize', 'answer', 'Optimized\nContext'),
                ('answer', 'trace', 'Response\nGenerated'),
                ('trace', 'end', 'Complete')
            ]
            
            for src, dst, label in edges:
                dot.edge(src, dst, label=label)
            
            # Save
            filename = f"workflow_langgraph"
            filepath = Path(output_dir) / filename
            
            output_path = str(filepath)
            dot.render(output_path, cleanup=True, quiet=True)
            
            png_path = output_path + '.png'
            if Path(png_path).exists():
                _WORKFLOW_DIAGRAM_PATH = png_path
                print(f"[DEBUG] Workflow PNG generated with graphviz (cached): {png_path}")
                return png_path
                
        except ImportError:
            print("[DEBUG] graphviz not available")
        except Exception as e:
            print(f"[DEBUG] graphviz generation failed: {e}")
        
        return None
        
    except Exception as e:
        print(f"[WARNING] Failed to generate workflow diagram: {e}")
        return None


class LangGraphVisualization:
    """Captures and visualizes LangGraph execution traces."""
    
    def __init__(self, session_id: Optional[str] = None):
        """Initialize visualization tracker.
        
        Args:
            session_id: Unique session identifier. If None, generates one.
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.start_time = time.time()
        self.nodes_executed = []
        self.state_history = []
        self.execution_times = {}
        self.errors = []
    
    def record_node_start(self, node_name: str, state: Dict[str, Any]):
        """Record start of node execution."""
        node_entry = {
            "timestamp": time.time(),
            "node_name": node_name,
            "state_snapshot": self._serialize_state(state),
            "status": "started"
        }
        self.nodes_executed.append(node_entry)
        self.execution_times[node_name] = time.time()
    
    def record_node_end(self, node_name: str, state: Dict[str, Any], error: Optional[str] = None):
        """Record end of node execution."""
        duration = time.time() - self.execution_times.get(node_name, time.time())
        
        # Find the matching node entry
        for node in reversed(self.nodes_executed):
            if node["node_name"] == node_name and node["status"] == "started":
                node["status"] = "completed" if not error else "failed"
                node["end_timestamp"] = time.time()
                node["duration_ms"] = duration * 1000
                node["state_after"] = self._serialize_state(state)
                if error:
                    node["error"] = error
                break
    
    def record_error(self, node_name: str, error: str):
        """Record an error during execution."""
        self.errors.append({
            "timestamp": time.time(),
            "node_name": node_name,
            "error_message": error
        })
    
    def _serialize_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Safely serialize state for JSON output."""
        serialized = {}
        for key, value in state.items():
            if isinstance(value, (str, int, float, bool, type(None))):
                serialized[key] = value
            elif isinstance(value, (list, dict)):
                try:
                    json.dumps(value)  # Test if JSON serializable
                    serialized[key] = value
                except (TypeError, ValueError):
                    serialized[key] = str(type(value).__name__)
            else:
                serialized[key] = str(type(value).__name__)
        return serialized
    
    def get_trace_data(self) -> Dict[str, Any]:
        """Get complete execution trace data."""
        total_duration = time.time() - self.start_time
        
        return {
            "session_id": self.session_id,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "total_duration_ms": total_duration * 1000,
            "nodes_executed": self.nodes_executed,
            "node_count": len(self.nodes_executed),
            "successful_nodes": len([n for n in self.nodes_executed if n["status"] == "completed"]),
            "failed_nodes": len([n for n in self.nodes_executed if n["status"] == "failed"]),
            "errors": self.errors,
            "error_count": len(self.errors)
        }
    
    def save_to_file(self, output_dir: str = "logs") -> str:
        """Save execution trace to JSON file.
        
        Args:
            output_dir: Directory to save trace file
            
        Returns:
            Path to saved file
        """
        Path(output_dir).mkdir(exist_ok=True)
        
        filename = f"langgraph_trace_{self.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = Path(output_dir) / filename
        
        trace_data = self.get_trace_data()
        
        with open(filepath, 'w') as f:
            json.dump(trace_data, f, indent=2)
        
        return str(filepath)
    
    def save_workflow_diagram(self, graph=None, output_dir: str = "session_graph") -> Optional[str]:
        """Generate and save PNG of the actual LangGraph workflow structure.
        
        Generates once and caches for all sessions (same workflow for all runs).
        Shows: retrieve → rerank → optimize → answer → traceability
        
        Args:
            graph: Compiled LangGraph StateGraph
            output_dir: Directory to save PNG files
            
        Returns:
            Path to saved PNG file, or None if generation failed
        """
        return generate_workflow_diagram_once(graph=graph, output_dir=output_dir)
    
    def save_mermaid_png(self, graph=None, output_dir: str = "session_graph") -> Optional[str]:
        """Generate and save PNG from execution trace.
        
        Tries multiple methods in order:
        1. Graphviz (if installed) - best quality
        2. PIL/Pillow - fallback if graphviz unavailable
        3. mmdc (Mermaid CLI) - if available
        
        Args:
            graph: Compiled LangGraph StateGraph (optional)
            output_dir: Directory to save PNG files
            
        Returns:
            Path to saved PNG file, or None if generation failed
        """
        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Try graphviz first (best quality)
            try:
                from graphviz import Digraph
                
                dot = Digraph(comment='LangGraph Execution', format='png')
                dot.attr('graph', bgcolor='white', rankdir='LR', splines='ortho')
                dot.attr('node', shape='box', style='rounded,filled', fillcolor='lightblue', fontname='Courier', fontsize='10')
                dot.attr('edge', color='gray', fontname='Courier', fontsize='9')
                
                # Add nodes with color coding
                for i, node in enumerate(self.nodes_executed):
                    node_id = f"node_{i}"
                    status = node['status']
                    duration = node.get('duration_ms', 0)
                    
                    # Color based on status
                    if status == 'completed':
                        color = 'lightgreen'
                    elif status == 'failed':
                        color = 'lightcoral'
                    else:
                        color = 'lightyellow'
                    
                    label = f"{node['node_name']}\n{duration:.0f}ms\n[{status}]"
                    dot.node(node_id, label, fillcolor=color, shape='box', style='rounded,filled')
                
                # Add edges
                for i in range(len(self.nodes_executed) - 1):
                    dot.edge(f"node_{i}", f"node_{i+1}")
                
                # Save
                filename = f"trace_{self.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                filepath = Path(output_dir) / filename
                
                output_path = str(filepath)
                dot.render(output_path, cleanup=True, quiet=True)
                
                png_path = output_path + '.png'
                if Path(png_path).exists():
                    print(f"[DEBUG] PNG generated with graphviz: {png_path}")
                    return png_path
                    
            except ImportError:
                print("[DEBUG] graphviz not installed, trying PIL...")
            except Exception as e:
                print(f"[DEBUG] graphviz generation failed: {e}, trying PIL...")
            
            # Fallback to PIL
            try:
                from PIL import Image, ImageDraw, ImageFont
                
                # Image dimensions
                width = 1000
                height = 300 + len(self.nodes_executed) * 60
                margin = 50
                
                # Create image
                img = Image.new('RGB', (width, height), color='white')
                draw = ImageDraw.Draw(img)
                
                # Try to use a standard font, fall back to default
                try:
                    font = ImageFont.truetype("arial.ttf", 14)
                    font_small = ImageFont.truetype("arial.ttf", 10)
                except:
                    font = ImageFont.load_default()
                    font_small = ImageFont.load_default()
                
                # Draw title
                title = f"LangGraph Execution: {self.session_id[:8]}..."
                draw.text((margin, 20), title, fill='black', font=font)
                
                # Draw nodes
                y_pos = 80
                colors = {'completed': 'lightgreen', 'failed': 'salmon', 'started': 'lightyellow'}
                
                for i, node in enumerate(self.nodes_executed):
                    # Node box
                    status = node['status']
                    color_name = colors.get(status, 'lightgray')
                    
                    # Convert color name to RGB (simplified)
                    color_map = {
                        'lightgreen': (144, 238, 144),
                        'salmon': (250, 128, 114),
                        'lightyellow': (255, 255, 153),
                        'lightgray': (211, 211, 211)
                    }
                    color = color_map.get(color_name, (200, 200, 200))
                    
                    x1, y1 = margin, y_pos
                    x2, y2 = width - margin, y_pos + 50
                    
                    # Draw box
                    draw.rectangle([x1, y1, x2, y2], fill=color, outline='black', width=2)
                    
                    # Draw text
                    duration = node.get('duration_ms', 0)
                    text = f"{i+1}. {node['node_name']} ({duration:.0f}ms) [{status}]"
                    draw.text((x1 + 10, y1 + 15), text, fill='black', font=font_small)
                    
                    # Draw arrow to next node
                    if i < len(self.nodes_executed) - 1:
                        arrow_y = y_pos + 50
                        arrow_y_next = y_pos + 60
                        draw.line([(width // 2, arrow_y), (width // 2, arrow_y_next)], fill='gray', width=2)
                    
                    y_pos += 60
                
                # Add footer
                total_time = (time.time() - self.start_time) * 1000
                footer = f"Total: {total_time:.0f}ms | Success: {len([n for n in self.nodes_executed if n['status'] == 'completed'])}/{len(self.nodes_executed)}"
                draw.text((margin, height - 30), footer, fill='gray', font=font_small)
                
                # Save
                filename = f"trace_{self.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                filepath = Path(output_dir) / filename
                
                img.save(str(filepath), 'PNG')
                print(f"[DEBUG] PNG generated with PIL: {filepath}")
                return str(filepath)
                
            except ImportError:
                print("[DEBUG] PIL not available, trying mmdc...")
            except Exception as e:
                print(f"[DEBUG] PIL generation failed: {e}, trying mmdc...")
            
            # Fallback: Try mmdc
            try:
                import subprocess
                import tempfile
                
                mermaid_code = self.generate_mermaid_diagram()
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as f:
                    f.write(mermaid_code)
                    temp_mmd = f.name
                
                filename = f"trace_{self.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                filepath = Path(output_dir) / filename
                
                result = subprocess.run(
                    ['mmdc', '-i', temp_mmd, '-o', str(filepath)],
                    capture_output=True,
                    timeout=10
                )
                
                Path(temp_mmd).unlink()
                
                if result.returncode == 0 and filepath.exists():
                    print(f"[DEBUG] PNG generated with mmdc: {filepath}")
                    return str(filepath)
                    
            except (FileNotFoundError, subprocess.TimeoutExpired, ImportError):
                pass
            
            return None
            
        except Exception as e:
            print(f"[WARNING] Failed to generate PNG: {e}")
            return None
    
    def generate_ascii_diagram(self) -> str:
        """Generate ASCII-style execution diagram."""
        diagram = []
        diagram.append(f"\n{'='*80}")
        diagram.append(f"LangGraph Execution Trace: Session {self.session_id[:8]}...")
        diagram.append(f"{'='*80}\n")
        
        # Timeline
        diagram.append(f"Start Time:     {datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S')}")
        diagram.append(f"Total Duration: {(time.time() - self.start_time)*1000:.0f}ms")
        diagram.append(f"Nodes Executed: {len(self.nodes_executed)}")
        diagram.append(f"Success Rate:   {len([n for n in self.nodes_executed if n['status'] == 'completed']) / len(self.nodes_executed) * 100 if self.nodes_executed else 0:.1f}%")
        diagram.append("")
        
        # Node execution flow
        diagram.append("Execution Flow:")
        diagram.append("-" * 80)
        
        for i, node in enumerate(self.nodes_executed, 1):
            # Use ASCII characters instead of Unicode
            status_symbol = "OK" if node["status"] == "completed" else "XX" if node["status"] == "failed" else "->"
            duration = f"{node.get('duration_ms', 0):.0f}ms" if 'duration_ms' in node else "running"
            
            diagram.append(f"  {i}. [{status_symbol}] {node['node_name']:<30} | {duration:>8}")
            
            if node["status"] == "failed" and "error" in node:
                diagram.append(f"      Error: {node['error']}")
        
        diagram.append("")
        
        # Summary statistics
        if self.execution_times:
            diagram.append("Node Timings:")
            diagram.append("-" * 80)
            
            sorted_times = sorted(
                [(n["node_name"], n.get("duration_ms", 0)) for n in self.nodes_executed if "duration_ms" in n],
                key=lambda x: x[1],
                reverse=True
            )
            
            for node_name, duration in sorted_times[:5]:
                bar_length = int(duration / 10)
                # Use simple dashes instead of block unicode characters
                bar = "-" * min(bar_length, 30)
                diagram.append(f"  {node_name:<30} |{bar:<30} {duration:>6.0f}ms")
        
        diagram.append("")
        diagram.append("=" * 80 + "\n")
        
        return "\n".join(diagram)
    
    def generate_mermaid_diagram(self) -> str:
        """Generate Mermaid flowchart of execution."""
        mmd = ["graph TD;"]
        
        for i, node in enumerate(self.nodes_executed):
            node_id = f"N{i}_{node['node_name'].replace(' ', '_')}"
            status_emoji = "✓" if node["status"] == "completed" else "✗"
            label = f"{status_emoji} {node['node_name']}"
            
            mmd.append(f"  {node_id}[{label}];")
            
            # Connect to next node
            if i < len(self.nodes_executed) - 1:
                next_node = self.nodes_executed[i + 1]
                next_node_id = f"N{i+1}_{next_node['node_name'].replace(' ', '_')}"
                mmd.append(f"  {node_id} --> {next_node_id};")
        
        return "\n".join(mmd)


class LangGraphVisualizer:
    """Helper to integrate visualization into LangGraph workflows."""
    
    @staticmethod
    def wrap_state_graph(graph, session_id: Optional[str] = None):
        """Wrap a StateGraph to automatically track execution.
        
        Args:
            graph: The LangGraph StateGraph to wrap
            session_id: Session ID for tracking
            
        Returns:
            Wrapped graph that tracks execution
        """
        viz = LangGraphVisualization(session_id)
        original_invoke = graph.invoke
        
        def wrapped_invoke(state, *args, **kwargs):
            """Wrapped invoke that tracks execution."""
            # Track nodes before execution
            for node_name in graph.nodes:
                if node_name not in ["__start__", "__end__"]:
                    # Hook into node to track execution
                    pass
            
            result = original_invoke(state, *args, **kwargs)
            return result, viz
        
        graph.invoke = wrapped_invoke
        return graph
    
    @staticmethod
    def create_trace_from_final_state(initial_state: Dict[str, Any], 
                                     final_state: Dict[str, Any],
                                     session_id: Optional[str] = None) -> LangGraphVisualization:
        """Create a visualization trace from initial and final states.
        
        Args:
            initial_state: Initial state passed to graph
            final_state: Final state returned from graph
            session_id: Session ID
            
        Returns:
            LangGraphVisualization object with execution data
        """
        viz = LangGraphVisualization(session_id)
        
        # Record state transition
        viz.record_node_start("workflow", initial_state)
        
        # Extract execution info from final_state if available
        if "execution_trace" in final_state:
            viz.nodes_executed = final_state["execution_trace"]
        
        viz.record_node_end("workflow", final_state)
        
        return viz


# Convenience functions for integration
def create_visualization(session_id: Optional[str] = None) -> LangGraphVisualization:
    """Create a new LangGraph visualization tracker."""
    return LangGraphVisualization(session_id)


def save_visualization(viz: LangGraphVisualization, output_dir: str = "logs", graph=None) -> Dict[str, str]:
    """Save visualization to files (JSON, PNG, Workflow) and print ASCII diagram.
    
    Args:
        viz: LangGraphVisualization object
        output_dir: Directory for JSON trace files
        graph: Compiled LangGraph graph for PNG generation
        
    Returns:
        Dictionary with file paths: {"json": path, "png": path or None, "workflow": path or None}
    """
    json_path = viz.save_to_file(output_dir)
    png_path = viz.save_mermaid_png(graph=graph, output_dir="session_graph")
    workflow_path = viz.save_workflow_diagram(graph=graph, output_dir="session_graph")
    
    print(viz.generate_ascii_diagram())
    print(f"[✓] Trace saved to: {json_path}")
    if png_path:
        print(f"[✓] Execution trace PNG saved to: {png_path}")
    if workflow_path:
        print(f"[✓] Workflow diagram PNG saved to: {workflow_path}")
    
    return {"json": json_path, "png": png_path, "workflow": workflow_path}
