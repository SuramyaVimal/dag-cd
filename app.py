import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import re
import io
import json

# -------------------------------
# UI Setup
# -------------------------------
st.set_page_config(page_title="TAC to DAG Visualizer", layout="centered")
st.markdown("""
    <style>
        .main {
            background-color: #f5f7fa;
        }
        h1, h2 {
            color: #1f4e79;
        }
        .stButton button {
            background-color: #1f77b4;
            color: white;
            border-radius: 8px;
            padding: 0.5em 1em;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🔁 TAC to DAG Visualizer")
st.markdown("Visualize your **Three Address Code (TAC)** as a Directed Acyclic Graph and get heuristic and optimal sequences.")

# -------------------------------
# TAC Input
# -------------------------------
tac_code = st.text_area("✍️ Enter TAC Code", height=200, placeholder="Example:\nt1 = a + b\nt2 = c + d\nt3 = t1 + t2")

# -------------------------------
# TAC Parser
# -------------------------------
@st.cache_data
def parse_tac_to_dag(_tac_code):
    lines = _tac_code.strip().split('\n')
    G = nx.DiGraph()
    expr_map = {}
    count = 0
    lhs_vars = []

    assignment_pattern = re.compile(r'^\s*(\w+)\s*=\s*(.+)\s*$')

    for line in lines:
        if '=' not in line:
            continue

        match = assignment_pattern.match(line)
        if not match:
            continue

        target, expr = match.groups()
        lhs_vars.append(target)
        tokens = expr.strip().split()

        if len(tokens) == 1:
            G.add_node(target, label=target)
            expr_map[target] = target

        elif len(tokens) == 3:
            op1, operator, op2 = tokens
            node_name = f'{operator}_{count}'
            count += 1

            G.add_node(node_name, label=operator)

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

    return G, lhs_vars

# -------------------------------
# Sequence Generators
# -------------------------------
@st.cache_data
def get_heuristic_sequence(_G):
    succ_count = {node: len(list(_G.successors(node))) for node in _G.nodes()}
    topo = list(nx.topological_sort(_G))
    topo.sort(key=lambda n: succ_count.get(n, 0))
    return topo

@st.cache_data
def get_optimal_sequence(_G, _lhs_vars):
    topo = list(nx.topological_sort(_G))
    return [n for n in topo if n in _lhs_vars]

# -------------------------------
# DAG Visualizer
# -------------------------------
@st.cache_data
def prepare_layout(_G):
    return nx.spring_layout(_G, seed=42)

def draw_dag(_G, pos=None):
    if pos is None:
        pos = prepare_layout(_G)
    labels = nx.get_node_attributes(_G, 'label')
    plt.figure(figsize=(10, 6))
    nx.draw(_G, pos, with_labels=True, labels=labels,
            node_size=2200, node_color="#90caf9", font_size=10,
            font_weight='bold', edge_color="#546e7a")
    st.pyplot(plt.gcf())
    plt.close()

# -------------------------------
# DAG + Sequences Generation
# -------------------------------
if st.button("🚀 Generate DAG and Sequences"):
    if not tac_code.strip():
        st.error("Please enter TAC code.")
    else:
        try:
            with st.spinner("Parsing TAC and generating graph..."):
                G, lhs_vars = parse_tac_to_dag(tac_code)

            if G.number_of_nodes() == 0:
                st.error("DAG generation failed. Check your TAC format.")
            else:
                st.subheader("📈 DAG Visualization")
                draw_dag(G)

                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("📋 Heuristic Sequence")
                    heuristic_seq = get_heuristic_sequence(G)
                    st.code(" → ".join(heuristic_seq), language="text")

                with col2:
                    st.subheader("📋 Optimal Sequence (LHS only)")
                    optimal_seq = get_optimal_sequence(G, lhs_vars)
                    st.code(" → ".join(optimal_seq), language="text")

                st.subheader("📤 Export Options")
                exp1, exp2 = st.columns(2)

                with exp1:
                    export_text = f"Optimal Sequence:\n{' → '.join(optimal_seq)}\n\nHeuristic Sequence:\n{' → '.join(heuristic_seq)}"
                    st.download_button("⬇️ Download Sequences", data=export_text,
                                       file_name="tac_sequences.txt", mime="text/plain")

                with exp2:
                    st.download_button("⬇️ Download Graph (JSON)",
                                       data=json.dumps(nx.node_link_data(G)),
                                       file_name="dag_data.json", mime="application/json")

        except Exception as e:
            st.exception(f"An error occurred: {e}")

# -------------------------------
# Help Section
# -------------------------------
with st.expander("ℹ️ Help - How to Use"):
    st.markdown("""
    ### 💻 Input Format:
    ```
    result = operand1 operator operand2
    ```
    - Example:
        ```
        t1 = a + b
        t2 = c + d
        t3 = t1 + t2
        ```

    ### 🚀 Features:
    - DAG visualization of TAC
    - Two sequences:
        - **Heuristic:** Based on dependency count
        - **Optimal:** Topological sort (LHS only)
    - Export graph & sequence results

    ### 🧠 Tip:
    Reuse expressions (e.g. `t4 = a + b`) to test common subexpression optimization!
    """)

# Footer
st.markdown("---")
st.caption("Made with ❤️ using Streamlit | TAC to DAG Visualizer v2.1")
