import streamlit as st
import ast
import networkx as nx
import graphviz

# --- Backend: CFG Builder Logic ---
class CFGBuilder(ast.NodeVisitor):
    def __init__(self):
        self.graph = nx.DiGraph()
        self.counter = 0
        self.last_nodes = [] 

    def new_node(self, label, shape="rect", color="#ffffff"):
        self.counter += 1
        node_id = f"node_{self.counter}"
        self.graph.add_node(node_id, label=label, shape=shape, fillcolor=color, style="filled")
        return node_id

    def add_edge(self, source, target, label=""):
        self.graph.add_edge(source, target, label=label)

    def build(self, code):
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return None, f"Syntax Error: {e}"
        
        start = self.new_node("START", shape="ellipse", color="#DAF7A6")
        self.last_nodes = [start]
        
        for node in tree.body:
            self.visit(node)
            
        end = self.new_node("STOP", shape="ellipse", color="#FFC300")
        for node in self.last_nodes:
            self.add_edge(node, end)
        return self.graph, None

    def visit_Assign(self, node):
        label = ast.unparse(node)
        curr = self.new_node(label)
        for prev in self.last_nodes:
            self.add_edge(prev, curr)
        self.last_nodes = [curr]

    def visit_Expr(self, node):
        label = ast.unparse(node)
        curr = self.new_node(label)
        for prev in self.last_nodes:
            self.add_edge(prev, curr)
        self.last_nodes = [curr]

    def visit_If(self, node):
        label = f"if {ast.unparse(node.test)}:"
        cond = self.new_node(label, shape="diamond", color="#AED6F1")
        for prev in self.last_nodes:
            self.add_edge(prev, cond)
        
        # True Path
        self.last_nodes = [cond]
        for child in node.body: self.visit(child)
        if_exits = self.last_nodes
        
        # False Path
        self.last_nodes = [cond]
        if node.orelse:
            for child in node.orelse: self.visit(child)
            else_exits = self.last_nodes
        else:
            else_exits = [cond]
        
        self.last_nodes = if_exits + else_exits

    def visit_While(self, node):
        label = f"while {ast.unparse(node.test)}:"
        cond = self.new_node(label, shape="diamond", color="#F9E79F")
        for prev in self.last_nodes:
            self.add_edge(prev, cond)
        
        self.last_nodes = [cond]
        for child in node.body: self.visit(child)
        
        for node_exit in self.last_nodes:
            self.add_edge(node_exit, cond, label="Loop")
        
        self.last_nodes = [cond]

# --- Streamlit UI Design ---
st.set_page_config(page_title="Direct CFG Analyzer", layout="wide")

st.title("Control Flow Diagram Visualizer")
st.divider()

# 1. Setup Columns
col_code, col_graph = st.columns([1, 1.2], gap="medium")

# 2. Input Section (This triggers the update)
with col_code:
    st.subheader("📝 Code Editor")
    default_code = """x = 10
if x > 5:
    print('Greater')
else:
    x = 0
print('Final x:', x)"""
    
    # Standard text_area directly updates the variable 'code_input' on change
    code_input = st.text_area("Python Code:", value=default_code, height=400)

# 3. Processing Section
builder = CFGBuilder()
graph, error = builder.build(code_input)

# 4. Display Metrics & Graph
if not error:
    # Calculations happen after input is received
    n = graph.number_of_nodes()
    e = graph.number_of_edges()
    p = len([node for node in graph.nodes() if graph.out_degree(node) > 1])
    cc = e - n + 2 # Cyclomatic Complexity formula

    # Metrics Display
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Nodes", n)
    m2.metric("Edges", e)
    m3.metric("Predicates", p)
    m4.metric("Cyclomatic Complexity", cc)
    
    st.divider()

    with col_graph:
        st.subheader("🎨 Flow Structure")
        dot = graphviz.Digraph()
        dot.attr(rankdir='TB', nodesep='0.5', ranksep='0.5')
        dot.attr('node', fontname='Arial', fontsize='10')
        
        for node, data in graph.nodes(data=True):
            dot.node(node, label=data['label'], shape=data['shape'], 
                     fillcolor=data['fillcolor'], style=data['style'])
        
        for u, v, data in graph.edges(data=True):
            edge_label = data.get('label', '')
            dot.edge(u, v, label=edge_label, color="#2E4053")
            
        st.graphviz_chart(dot, use_container_width=True)
else:
    with col_graph:
        st.error(error)