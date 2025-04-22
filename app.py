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
        body {
            background-color: #f5f7fa;
        }
        .main {
            padding: 2rem;
        }
        h1, h2, h3 {
            color: #2c3e50;
        }
        .stTextArea textarea {
            font-family: monospace;
            font-size: 16px;
        }
    </style>
""", unsafe_allow_html=True)

# -------------------------------
# Header
# -------------------------------
st.title("🧠 TAC to DAG Visualizer")
st.markdown("Visualize your **Three Address Code (TAC)** as a Directed Acyclic Graph and view optimized instruction sequences.")

# -------------------------------
# Input Area
# -------------------------------
tac_code = st.text_area("📥 Enter TAC Code:", height=200, placeholder="Example:\na = b + c\nd = a + e\nf = d + g")

# -------------------------------
# TAC to DAG Conversion
# -------------------------------
@st.cache_data
def parse_tac_to_dag(tac_code):
    lines = tac_code.strip().split('\n')
    G = nx.DiGraph()
    expr_map = {}
    count = 0
    lhs_set = set()
    
    pattern = re.compile(r'^\s*(\w+)\s*=\s*(.+)$')

    for line in lines:
        if '=' not in line:
            continue

        match = pattern.match(line)
        if not match:
            continue

        target, expr = match.groups()
        tokens = expr.strip().split()
        lhs_set.add(target)

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

    return G, lhs_set

# -------------------------------
# Sequence Generators
# -------------------------------
@st.cache_data
def get_optimal_sequence(G, lhs_set):
    topo = list(nx.topological_sort(G))
    labels = nx.get_node_attributes(G, 'label')
    lhs_sequence = [node for node in topo if node in lhs_set and labels.get(node) == node]
    return lhs_sequence

@st.cache_data
def get_heuristic_sequence(G):
    succ_count = {n: len(list(G.successors(n))) for n in G.nodes()}
    topo = list(nx.topological_sort(G))
    topo.sort(key=lambda x: succ_count.get(x, 0))
    return topo

# -------------------------------
# Layout Generator
# -------------------------------
@st.cache_data
def prepare_layout(_G):
    return nx.spring_layout(_G, seed=42)

# -------------------------------
# DAG Drawer
# -------------------------------
def draw_dag(G, pos):
    labels = nx.get_node_attributes(G, 'label')
    plt.figure(figsize=(12, 8))
    nx.draw(G, pos, with_labels=True, labels=labels,
            node_size=2000, node_color="#74b9ff", font_size=11, font_weight='bold', edge_color="#636e72")
    st.pyplot(plt.gcf())
    plt.close()

# -------------------------------
# Main Logic
# -------------------------------
if st.button("🚀 Generate DAG and Sequences"):
    if not tac_code.strip():
        st.error("Please enter valid TAC code.")
    else:
        try:
            with st.spinner("Processing..."):
                G, lhs_vars = parse_tac_to_dag(tac_code)
                if G.number_of_nodes() == 0:
                    st.error("Empty or invalid TAC input.")
                else:
                    st.subheader("📈 DAG Visualization")
                    pos = prepare_layout(G)
                    draw_dag(G, pos)

                    st.subheader("📋 Instruction Sequences")
                    optimal_seq = get_optimal_sequence(G, lhs_vars)
                    heuristic_seq = get_heuristic_sequence(G)

                    st.markdown("**✅ Optimal Sequence (LHS variables only):**")
                    st.code(" → ".join(optimal_seq), language='text')

                    st.markdown("**🧠 Heuristic Sequence (All Nodes):**")
                    st.code(" → ".join(heuristic_seq), language='text')

                    if set(optimal_seq) != set(heuristic_seq):
                        st.info("Heuristic includes internal ops; Optimal only includes assignments.")

                    # Export
                    st.subheader("📤 Export")
                    export_col1, export_col2 = st.columns(2)

                    with export_col1:
                        export_text = f"Optimal Sequence:\n{' → '.join(optimal_seq)}\n\nHeuristic Sequence:\n{' → '.join(heuristic_seq)}"
                        st.download_button("📄 Download Sequences", export_text, "tac_sequences.txt", "text/plain")

                    with export_col2:
                        graph_data = nx.node_link_data(G)
                        st.download_button("🧬 Download DAG JSON", json.dumps(graph_data), "dag_data.json", "application/json")

        except Exception as e:
            st.error(f"An error occurred: {e}")

# -------------------------------
# Help Section
# -------------------------------
with st.expander("ℹ️ How to Use"):
    st.markdown("""
    - Write TAC code in the format: `result = operand1 operator operand2`
    - One instruction per line
    - Click **Generate** to view the DAG and sequences

    **Example:**
    ```
    a = b + c
    d = a + e
    f = d + g
    ```
    """)

st.markdown("---")
st.markdown("🔧 Made with 💙 by Suramya | TAC to DAG Visualizer v2.1")
