import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
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

# -------------------------------
# TAC Parser (Optimized with caching)
# -------------------------------
@st.cache_data
def parse_tac_to_dag(tac_code):
    lines = tac_code.strip().split('\n')
    G = nx.DiGraph()
    expr_map = {}
    count = 0

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

            node_name = f'{operator}_{count}'
            G.add_node(node_name, label=operator)
            count += 1

            for op in [op1, op2]:
                if op not in expr_map and op not in G:
                    G.add_node(op, label=op)

            left = expr_map.get(op1, op1)
            right = expr_map.get(op2, op2)

            G.add_edge(left, node_name)
            G.add_edge(right, node_name)

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
    successor_counts = {node: len(list(G.successors(node))) for node in G.nodes()}
    topo = list(nx.topological_sort(G))
    topo.sort(key=lambda n: successor_counts.get(n, 0))
    return topo

@st.cache_data
def get_optimal_sequence(G):
    return list(nx.topological_sort(G))

# -------------------------------
# DAG Visualizer (Matplotlib with fix)
# -------------------------------
@st.cache_data
def prepare_layout(_G):  # FIXED: Added underscore so Streamlit ignores hashing
    if _G.number_of_nodes() > 100:
        return nx.kamada_kawai_layout(_G)
    else:
        return nx.spring_layout(_G, seed=42)

def draw_dag(G, pos=None):
    if pos is None:
        pos = prepare_layout(G)

    labels = nx.get_node_attributes(G, 'label')
    plt.figure(figsize=(12, 8))

    if G.number_of_nodes() > 500:
        batches = [list(G.nodes())[i:i+100] for i in range(0, G.number_of_nodes(), 100)]
        for batch in batches:
            nx.draw_networkx_nodes(G, pos, nodelist=batch, node_color='#6BAED6', node_size=1500)

        nx.draw_networkx_edges(G, pos, edge_color='#636363', alpha=0.7)
        nx.draw_networkx_labels(G, pos, labels=labels, font_weight='bold')
    else:
        nx.draw(G, pos, with_labels=True, labels=labels,
                node_size=2500, node_color='#6BAED6', font_size=11,
                font_weight='bold', edge_color='#636363')

    if G.number_of_nodes() > 1000:
        img_bytes = io.BytesIO()
        plt.savefig(img_bytes, format='png', dpi=100)
        img_bytes.seek(0)
        st.image(img_bytes)
    else:
        st.pyplot(plt.gcf())

    plt.close()

# -------------------------------
# Generate Button with Error Handling
# -------------------------------
if st.button("🚀 Generate DAG and Sequences"):
    if not tac_code.strip():
        st.error("Please enter TAC code before generating.")
    else:
        try:
            with st.spinner("Parsing TAC code..."):
                G = parse_tac_to_dag(tac_code)

            if G.number_of_nodes() == 0:
                st.error("DAG generation failed. Please check TAC input.")
            else:
                num_nodes = G.number_of_nodes()
                num_edges = G.number_of_edges()

                st.subheader("📊 DAG Summary")
                col_stats1, col_stats2, col_stats3 = st.columns(3)
                col_stats1.metric("Nodes", num_nodes)
                col_stats2.metric("Edges", num_edges)
                col_stats3.metric("Complexity", f"{num_edges/max(1, num_nodes):.2f}")

                with st.expander("📌 DAG Nodes and Labels"):
                    node_labels = nx.get_node_attributes(G, 'label')
                    for node in G.nodes():
                        label = node_labels.get(node, "N/A")
                        st.markdown(f"- `{node}` : **{label}**")

                col1, col2 = st.columns([2, 1])

                with col1:
                    st.subheader("📈 DAG Visualization")
                    pos = prepare_layout(G)
                    draw_dag(G, pos)

                with col2:
                    st.subheader("📋 Sequences")

                    with st.spinner("Generating optimal sequence..."):
                        optimal = get_optimal_sequence(G)

                    with st.spinner("Generating heuristic sequence..."):
                        heuristic = get_heuristic_sequence(G)

                    st.markdown("**✅ Heuristic Sequence:**")
                    st.code(" → ".join(heuristic), language='text')

                    st.markdown("**✅ Optimal Sequence:**")
                    st.code(" → ".join(optimal), language='text')

                    if heuristic != optimal:
                        st.info("📝 The heuristic and optimal sequences differ.")
                    else:
                        st.success("✅ The heuristic and optimal sequences are identical.")

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
    """)

st.markdown("---")
st.markdown("TAC to DAG Visualizer v2.0 - Optimized for Performance")
