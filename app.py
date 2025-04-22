import streamlit as st
import tkinter as tk
from tkinter import scrolledtext, messagebox
import re
from collections import defaultdict, deque

class ThreeAddressCodeOptimizer:
    def __init__(self):
        self.variables = set()
        self.dag = defaultdict(list)
        self.in_degree = defaultdict(int)
        self.statements = []
        self.var_to_statement = {}
        
    def parse_three_address_code(self, code):
        """Parse the three address code and build the DAG."""
        self.variables = set()
        self.dag = defaultdict(list)
        self.in_degree = defaultdict(int)
        self.statements = []
        self.var_to_statement = {}
        
        # Split the code into lines and process each statement
        lines = code.strip().split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            # Parse the statement based on common three-address code patterns
            # Pattern for x = y op z
            binary_op_match = re.match(r'(\w+)\s*=\s*(\w+)\s*([+\-*/])\s*(\w+)', line)
            # Pattern for x = op y (unary operations)
            unary_op_match = re.match(r'(\w+)\s*=\s*([+\-])\s*(\w+)', line)
            # Pattern for x = y (assignment)
            assign_match = re.match(r'(\w+)\s*=\s*(\w+)', line)
            # Pattern for x = constant
            const_match = re.match(r'(\w+)\s*=\s*(\d+)', line)
            
            if binary_op_match:
                result, op1, operator, op2 = binary_op_match.groups()
                self.process_statement(result, op1, op2, operator, i)
            elif unary_op_match:
                result, operator, op1 = unary_op_match.groups()
                self.process_statement(result, op1, None, operator, i)
            elif assign_match:
                result, op1 = assign_match.groups()
                self.process_statement(result, op1, None, "=", i)
            elif const_match:
                result, constant = const_match.groups()
                self.process_statement(result, constant, None, "const", i)
            else:
                raise ValueError(f"Unsupported statement format: {line}")
                
            self.statements.append(line)
    
    def process_statement(self, result, op1, op2, operator, stmt_index):
        """Process a statement and update the DAG."""
        self.variables.add(result)
        self.var_to_statement[result] = stmt_index
        
        # For non-constant operands, add edges in the DAG
        if operator != "const":
            if op1.isalpha() or (op1.isalnum() and not op1.isdigit()):
                self.variables.add(op1)
                self.dag[op1].append(result)
                self.in_degree[result] += 1
                
        if op2 and (op2.isalpha() or (op2.isalnum() and not op2.isdigit())):
            self.variables.add(op2)
            self.dag[op2].append(result)
            self.in_degree[result] += 1
    
    def get_optimal_sequence(self):
        """Generate an optimal execution sequence using topological sort."""
        # Create a copy of the in-degree dictionary for topological sort
        in_degree_copy = self.in_degree.copy()
        queue = deque([var for var in self.variables if in_degree_copy.get(var, 0) == 0])
        result = []
        
        while queue:
            var = queue.popleft()
            
            # If this variable is the result of a statement, add the statement to the result
            if var in self.var_to_statement:
                stmt_index = self.var_to_statement[var]
                result.append((stmt_index, self.statements[stmt_index]))
            
            # Process neighbors
            for neighbor in self.dag[var]:
                in_degree_copy[neighbor] -= 1
                if in_degree_copy[neighbor] == 0:
                    queue.append(neighbor)
        
        # Sort by original statement index to maintain proper order
        result.sort(key=lambda x: x[0])
        return [stmt for _, stmt in result]

class ThreeAddressCodeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Three Address Code Optimizer")
        self.root.geometry("800x600")
        
        self.optimizer = ThreeAddressCodeOptimizer()
        
        self.create_widgets()
        
    def create_widgets(self):
        # Input area
        input_frame = tk.Frame(self.root)
        input_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(input_frame, text="Enter Three Address Code:").pack(anchor=tk.W)
        
        self.input_text = scrolledtext.ScrolledText(input_frame, height=10)
        self.input_text.pack(fill=tk.BOTH, expand=True)
        
        # Example button
        example_button = tk.Button(input_frame, text="Load Example", command=self.load_example)
        example_button.pack(anchor=tk.W, pady=5)
        
        # Button area
        button_frame = tk.Frame(self.root)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        optimize_button = tk.Button(button_frame, text="Generate Optimal Sequence", command=self.optimize)
        optimize_button.pack(side=tk.LEFT, padx=5)
        
        clear_button = tk.Button(button_frame, text="Clear All", command=self.clear_all)
        clear_button.pack(side=tk.LEFT, padx=5)
        
        # Output area
        output_frame = tk.Frame(self.root)
        output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(output_frame, text="Optimal Sequence:").pack(anchor=tk.W)
        
        self.output_text = scrolledtext.ScrolledText(output_frame, height=10)
        self.output_text.pack(fill=tk.BOTH, expand=True)
        
    def load_example(self):
        example = """# Example three address code
t1 = a + b
t2 = c * d
t3 = t1 - t2
t4 = e / f
result = t3 + t4"""
        self.input_text.delete(1.0, tk.END)
        self.input_text.insert(tk.END, example)
        
    def optimize(self):
        try:
            code = self.input_text.get(1.0, tk.END)
            self.optimizer.parse_three_address_code(code)
            optimal_sequence = self.optimizer.get_optimal_sequence()
            
            # Display the result
            self.output_text.delete(1.0, tk.END)
            if optimal_sequence:
                self.output_text.insert(tk.END, "# Optimal execution sequence:\n")
                for stmt in optimal_sequence:
                    self.output_text.insert(tk.END, stmt + "\n")
            else:
                self.output_text.insert(tk.END, "No valid sequence found. Check your input.")
                
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            
    def clear_all(self):
        self.input_text.delete(1.0, tk.END)
        self.output_text.delete(1.0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = ThreeAddressCodeGUI(root)
    root.mainloop()
