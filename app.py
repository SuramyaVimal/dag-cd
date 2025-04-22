import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import re
import io
import json

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
# TAC Parser (with common subexpression handling)
# -------------------------------
@st.cache_data
def parse_tac_to_dag(tac_code):
    lines = tac_code.strip().split('\n')
    G = nx.DiGraph()
    expr_map = {}  # maps expression tuples to node names
    var_map = {}   # maps variable names to node names
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
            var_map[target] = target

        elif len(tokens) == 3:
            op1, operator, op2 = tokens

            left = var_map.get(op1, op1)
            right = var_map.get(op2, op2)

            key = (left, operator, right)

            if key in expr_map:
                op_node = expr_map[key]
            else:
                op_node = f'{operator}_{count}'
                G.add_node(op_node, label=f"{op1} {operator} {op2}")
                G.add_edge(left, op_node)
                G.add_edge(right, op_node)
                expr_map[key] = op_node
                count += 1

            G.add_node(target, label=target)
            G.add_edge(op_node, target)
            var_map[target] = target

        else:
            st.warning(f"⚠️ Invalid TAC line skipped: `{line}`")

    return G

# -------------------------------
# Sequence Generators
# -------------------------------
@st.cache_data
def get_heuristic_sequence(G):
    successor_counts = {node: len(list(G.successors(node))) for node in G.nodes()}
    topo = list(nx.topological_sort(G))
    topo.sort(key=lambda n: successor_counts.get(n, 0))
    return topo

@st.cache_data
def get_optimal_sequence(G):
    if not nx.is_directed_acyclic_graph(G):
        return []
    try:
        return list(nx.topological_sort(G))
    except nx.NetworkXUnfeasible:
        return []

# -------------------------------
# DAG Visualizer
# -------------------------------
@st.cache_data
def prepare_layout(G):
    return nx.spring_layout(G, seed=42)

def draw_dag(G, pos=None):
    if pos is None:
        pos = prepare_layout(G)

    labels = nx.get_node_attributes(G, 'label')
    plt.figure(figsize=(12, 8))

    nx.draw(G, pos, with_labels=True, labels=labels,
            node_size=2500, node_color='#6BAED6',
            font_size=11, font_weight='bold', edge_color='#636363')

    st.pyplot(plt.gcf())
    plt.close()

# -------------------------------
# Generate DAG and Display
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
                # Summary
                st.subheader("📊 DAG Summary")
                col1, col2, col3 = st.columns(3)
                col1.metric("Nodes", G.number_of_nodes())
                col2.metric("Edges", G.number_of_edges())
                col3.metric("Complexity", f"{G.number_of_edges() / max(1, G.number_of_nodes()):.2f}")

                # Show node-labels mapping
                with st.expander("📌 DAG Nodes and Labels"):
                    node_labels = nx.get_node_attributes(G, 'label')
                    for node in G.nodes():
                        st.markdown(f"- `{node}` : **{node_labels.get(node, 'N/A')}**")

                # Show edge list
                with st.expander("🔍 Edges in DAG"):
                    for u, v in G.edges():
                        st.text(f"{u} → {v}")

                # DAG + Sequences
                col_vis, col_seq = st.columns([2, 1])
                with col_vis:
                    st.subheader("📈 DAG Visualization")
                    pos = prepare_layout(G)
                    draw_dag(G, pos)

                with col_seq:
                    st.subheader("📋 Sequences")
                    optimal = get_optimal_sequence(G)
                    heuristic = get_heuristic_sequence(G)

                    if not optimal:
                        st.error("❌ Graph is not a DAG. Cannot generate optimal sequence.")
                    else:
                        st.markdown("**✅ Heuristic Sequence:**")
                        st.code(" → ".join(heuristic), language='text')

                        st.markdown("**✅ Optimal Sequence:**")
                        st.code(" → ".join(optimal), language='text')

                        if heuristic != optimal:
                            st.info("📝 Sequences differ: Heuristic uses dependency counts; Optimal is purely topological.")
                        else:
                            st.success("✅ Both sequences are the same.")

                # Export buttons
                st.subheader("📤 Export Options")
                exp_col1, exp_col2 = st.columns(2)

                with exp_col1:
                    if st.button("Export Sequences as Text"):
                        export_text = f"Optimal Sequence:\n{' → '.join(optimal)}\n\nHeuristic Sequence:\n{' → '.join(heuristic)}"
                        st.download_button("Download Sequences", data=export_text, file_name="tac_sequences.txt", mime="text/plain")

                with exp_col2:
                    if st.button("Export Graph Data"):
                        graph_data = nx.node_link_data(G)
                        st.download_button("Download Graph JSON", data=json.dumps(graph_data), file_name="dag_data.json", mime="application/json")

        except Exception as e:
            st.exception(f"An error occurred: {e}")

# -------------------------------
# Help Section
# -------------------------------
with st.expander("ℹ️ How to Use This Tool"):
    st.markdown("""
    ### Input Format:
    ```
    a = b + c
    d = a + e
    f = d + g
    ```

    ### Features:
    - 📈 Visualize DAG from TAC
    - 📋 Generate heuristic & optimal sequences
    - 📤 Export sequences or DAG as JSON
    """)

# Footer
st.markdown("---")
st.markdown("TAC to DAG Visualizer v2.0 - Optimized for Performance and Accuracy")
