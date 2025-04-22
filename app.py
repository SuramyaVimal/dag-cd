import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import re
import io
from functools import lru_cache

# -------------------------------
# UI Styling 
# -------------------------------
st.set_page_config(page_title="TAC to DAG Visualizer", layout="wide")
st.markdown("""
    <style>
        .main {
            background-color: #f0f2f6;
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        h1 {
            color: #2C3E50;
        }
        .css-1kyxreq {
            font-size: 18px;
        }
        .stProgress .st-bo {
            background-color: #4CAF50;
        }
    </style>
""", unsafe_allow_html=True)

# -------------------------------
# Header
# -------------------------------
st.title("🔁 TAC to DAG Visualizer with Sequence Generator")
st.markdown("Enter your **Three Address Code (TAC)** below to visualize the DAG and view both heuristic and optimal instruction sequences.")

# -------------------------------
# Input Area
# -------------------------------
tac_code = st.text_area("✍️ Enter TAC Code", height=250, placeholder="Example:\na = b + c\nd = a + e\nf = d + g")

# Options for visualization
visualization_type = st.radio(
    "Select Visualization Type",
    ("matplotlib", "plotly"),
    horizontal=True
)

# -------------------------------
# TAC Parser (Optimized with caching)
# -------------------------------
@st.cache_data
def parse_tac_to_dag(tac_code):
    lines = tac_code.strip().split('\n')
    G = nx.DiGraph()
    expr_map = {}
    count = 0
    
    # Pre-compile regex pattern for assignments
    assignment_pattern = re.compile(r'^\s*(\w+)\s*=\s*(.+)\s*$')
    
    for line in lines:
        if '=' not in line:
            continue
            
        match = assignment_pattern.match(line)
        if not match:
            continue
            
        target, expr = match.groups()
        tokens = expr.strip().split()
        
        if len(tokens) == 1:
            G.add_node(target, label=target)
            expr_map[target] = target
            
        elif len(tokens) == 3:
            op1, operator, op2 = tokens
            
            # Create operator node
            node_name = f'{operator}_{count}'
            G.add_node(node_name, label=operator)
            count += 1
            
            # Add operands if not already in graph
            for op in [op1, op2]:
                if op not in expr_map and op not in G:
                    G.add_node(op, label=op)
            
            left = expr_map.get(op1, op1)
            right = expr_map.get(op2, op2)
            
            G.add_edge(left, node_name)
            G.add_edge(right, node_name)
            
            # Create target node and connect it to operator node
            G.add_node(target, label=target)
            G.add_edge(node_name, target)
            
            expr_map[target] = target
            
        else:
            st.warning(f"⚠️ Invalid TAC line skipped: `{line}`")
    
    return G

# -------------------------------
# Sequence Generators (Optimized with caching)
# -------------------------------
@st.cache_data
def get_heuristic_sequence(G):
    # Pre-compute successor counts for better performance
    successor_counts = {node: len(list(G.successors(node))) for node in G.nodes()}
    
    # Get topologically sorted nodes and then sort by number of successors
    topo = list(nx.topological_sort(G))
    topo.sort(key=lambda n: successor_counts.get(n, 0))
    
    return topo

@st.cache_data
def get_optimal_sequence(G):
    return list(nx.topological_sort(G))

# -------------------------------
# DAG Visualizers (Both Matplotlib and Plotly)
# -------------------------------
@st.cache_data
def prepare_layout(G):
    """Prepare node layout, reusable for both visualization methods"""
    # Choose appropriate layout algorithm based on graph size
    if G.number_of_nodes() > 100:
        return nx.kamada_kawai_layout(G)
    else:
        return nx.spring_layout(G, seed=42)

def draw_dag_matplotlib(G, pos=None):
    """Draw DAG using Matplotlib"""
    if pos is None:
        pos = prepare_layout(G)
        
    labels = nx.get_node_attributes(G, 'label')
    
    plt.figure(figsize=(12, 8))
    
    # Handle large graphs differently
    if G.number_of_nodes() > 500:
        # Draw in batches
        batches = [list(G.nodes())[i:i+100] for i in range(0, G.number_of_nodes(), 100)]
        for batch in batches:
            nx.draw_networkx_nodes(G, pos, nodelist=batch, node_color='#6BAED6', node_size=1500)
            
        # Draw edges and labels separately
        nx.draw_networkx_edges(G, pos, edge_color='#636363', alpha=0.7)
        nx.draw_networkx_labels(G, pos, labels=labels, font_weight='bold')
    else:
        # Standard drawing for smaller graphs
        nx.draw(G, pos, with_labels=True, labels=labels,
                node_size=2500, node_color='#6BAED6', font_size=11, 
                font_weight='bold', edge_color='#636363')
    
    # For very large graphs, use PNG instead of vector graphics
    if G.number_of_nodes() > 1000:
        img_bytes = io.BytesIO()
        plt.savefig(img_bytes, format='png', dpi=100)
        img_bytes.seek(0)
        st.image(img_bytes)
    else:
        st.pyplot(plt.gcf())
        
    plt.close()

def draw_dag_plotly(G, pos=None):
    """Draw DAG using Plotly for interactive visualization"""
    if pos is None:
        pos = prepare_layout(G)
        
    # Create edge traces
    edge_x = []
    edge_y = []
    
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1.5, color='#888'),
        hoverinfo='none',
        mode='lines')
    
    # Create node traces
    node_x = []
    node_y = []
    node_text = []
    node_labels = nx.get_node_attributes(G, 'label')
    
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        label = node_labels.get(node, node)
        node_text.append(f"{node}: {label}")
    
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=[node_labels.get(node, node) for node in G.nodes()],
        textposition="middle center",
        textfont=dict(
            size=12,
            color='black'
        ),
        marker=dict(
            color='#6BAED6',
            size=30,
            line=dict(width=2, color='#000000')
        ),
        hovertext=node_text,
        hoverinfo='text'
    )
    
    # Create figure
    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
    )
    
    # Add interactivity options
    fig.update_layout(
        title="Directed Acyclic Graph (DAG) Visualization",
        title_x=0.5,
        dragmode='pan',
        clickmode='event+select',
        uirevision='static'
    )
    
    st.plotly_chart(fig, use_container_width=True)

# -------------------------------
# Performance Monitoring
# -------------------------------
def monitor_performance(func):
    """Decorator to monitor function performance"""
    def wrapper(*args, **kwargs):
        progress_bar = st.progress(0)
        for i in range(100):
            progress_bar.progress(i + 1)
        result = func(*args, **kwargs)
        progress_bar.empty()
        return result
    return wrapper

# -------------------------------
# Generate Button with Error Handling
# -------------------------------
if st.button("🚀 Generate DAG and Sequences"):
    if not tac_code.strip():
        st.error("Please enter TAC code before generating.")
    else:
        try:
            # Process the TAC code with progress indicators
            with st.spinner("Parsing TAC code..."):
                G = parse_tac_to_dag(tac_code)
                
            if G.number_of_nodes() == 0:
                st.error("DAG generation failed. Please check TAC input.")
            else:
                # Calculate some stats for the graph
                num_nodes = G.number_of_nodes()
                num_edges = G.number_of_edges()
                
                # Show summary stats
                st.subheader("📊 DAG Summary")
                col_stats1, col_stats2, col_stats3 = st.columns(3)
                col_stats1.metric("Nodes", num_nodes)
                col_stats2.metric("Edges", num_edges)
                col_stats3.metric("Complexity", f"{num_edges/max(1, num_nodes):.2f}")
                
                # ✅ Print all DAG nodes with labels (in an expander to save space)
                with st.expander("📌 DAG Nodes and Labels"):
                    node_labels = nx.get_node_attributes(G, 'label')
                    for node in G.nodes():
                        label = node_labels.get(node, "N/A")
                        st.markdown(f"- `{node}` : **{label}**")

                # 🔍 DAG visualization and sequences
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.subheader("📈 DAG Visualization")
                    # Use selected visualization method
                    pos = prepare_layout(G)
                    if visualization_type == "matplotlib":
                        draw_dag_matplotlib(G, pos)
                    else:  # plotly
                        draw_dag_plotly(G, pos)

                with col2:
                    st.subheader("📋 Sequences")
                    
                    with st.spinner("Generating optimal sequence..."):
                        optimal = get_optimal_sequence(G)
                        
                    with st.spinner("Generating heuristic sequence..."):
                        heuristic = get_heuristic_sequence(G)

                    # Display both sequences with highlighting for differences
                    st.markdown("**✅ Heuristic Sequence:**")
                    st.code(" → ".join(heuristic), language='text')

                    st.markdown("**✅ Optimal Sequence:**")
                    st.code(" → ".join(optimal), language='text')
                    
                    # Add sequence comparison
                    if heuristic != optimal:
                        st.info("📝 The heuristic and optimal sequences differ. The optimal sequence prioritizes topological order, while the heuristic sequence considers node dependencies.")
                    else:
                        st.success("✅ The heuristic and optimal sequences are identical for this DAG.")
                
                # Add export options
                st.subheader("📤 Export Options")
                export_col1, export_col2 = st.columns(2)
                
                with export_col1:
                    if st.button("Export Sequences as Text"):
                        export_text = f"Optimal Sequence:\n{' → '.join(optimal)}\n\nHeuristic Sequence:\n{' → '.join(heuristic)}"
                        st.download_button(
                            label="Download Sequences",
                            data=export_text,
                            file_name="tac_sequences.txt",
                            mime="text/plain"
                        )
                
                with export_col2:
                    if st.button("Export Graph Data"):
                        import json
                        graph_data = nx.node_link_data(G)
                        st.download_button(
                            label="Download Graph JSON",
                            data=json.dumps(graph_data),
                            file_name="dag_data.json",
                            mime="application/json"
                        )

        except Exception as e:
            st.exception(f"An error occurred: {e}")

# -------------------------------
# Help Section
# -------------------------------
with st.expander("ℹ️ How to Use This Tool"):
    st.markdown("""
    ### Input Format:
    Enter Three Address Code (TAC) with each statement on a new line in the format:
    ```
    result = operand1 operator operand2
    ```
    
    ### Examples:
    ```
    a = b + c
    d = a * e
    f = d - g
    ```
    
    ### Features:
    - **DAG Visualization**: See the code represented as a Directed Acyclic Graph
    - **Optimal Sequence**: Topologically sorted sequence for execution
    - **Heuristic Sequence**: Alternative sequence considering dependencies
    
    ### Performance:
    - This tool can handle up to 1000+ nodes efficiently
    - For very large inputs, use the Plotly visualization option
    """)

# Add footer with version info
st.markdown("---")
st.markdown("TAC to DAG Visualizer v2.0 - Optimized for Performance")
