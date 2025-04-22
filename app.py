import streamlit as st
import networkx as nx
import matplotlib.pyplot as plt
import io

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
# TAC Parser
# -------------------------------
def parse_tac_to_dag(tac_code):
    lines = tac_code.strip().split('\n')
    G = nx.DiGraph()
    expr_map = {}
    count = 0

    for line in lines:
        if '=' not in line:
            continue

        target, expr = line.split('=')
        target = target.strip()
        tokens = expr.strip().split()

        if len(tokens) == 1:
            G.add_node(target, label=tokens[0])
            expr_map[target] = target
        elif len(tokens) == 3:
            op1, operator, op2 = tokens

            node_name = f'{operator}_{count}'
            G.add_node(node_name, label=operator)
            count += 1

            left = expr_map.get(op1, op1)
            right = expr_map.get(op2, op2)

            G.add_edge(left, node_name)
            G.add_edge(right, node_name)
            expr_map[target] = node_name
        else:
            st.warning(f"⚠️ Invalid TAC line skipped: `{line}`")

    return G

# -------------------------------
# Sequence Generators
# -------------------------------
def get_heuristic_sequence(G):
    topo = list(nx.topological_sort(G))
    topo.sort(key=lambda n: len(list(G.successors(n))))
    return topo

def get_optimal_sequence(G):
    return list(nx.topological_sort(G))

# -------------------------------
# DAG Visualizer
# -------------------------------
def draw_dag(G):
    pos = nx.spring_layout(G, seed=42)
    labels = nx.get_node_attributes(G, 'label')
    plt.figure(figsize=(10, 7))
    nx.draw(G, pos, with_labels=True, labels=labels,
            node_size=2500, node_color='#6BAED6', font_size=11, font_weight='bold', edge_color='#636363')
    st.pyplot(plt.gcf())
    plt.close()

# -------------------------------
# Generate Button
# -------------------------------
if st.button("🚀 Generate DAG and Sequences"):
    if not tac_code.strip():
        st.error("Please enter TAC code before generating.")
    else:
        try:
            G = parse_tac_to_dag(tac_code)
            if G.number_of_nodes() == 0:
                st.error("DAG generation failed. Please check TAC input.")
            else:
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.subheader("📈 DAG Visualization")
                    draw_dag(G)

                with col2:
                    st.subheader("📋 Sequences")
                    heuristic = get_heuristic_sequence(G)
                    optimal = get_optimal_sequence(G)

                    st.markdown("**✅ Heuristic Sequence:**")
                    st.code(" → ".join(heuristic), language='text')

                    st.markdown("**✅ Optimal Sequence:**")
                    st.code(" → ".join(optimal), language='text')

        except Exception as e:
            st.exception(f"An error occurred: {e}")
