import streamlit as st
import ast
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from streamlit_extras.metric_cards import style_metric_cards
import plotly.express as px

# Function to analyze the Python code
def analyze_code(code):
    try:
        # Parse the code into an Abstract Syntax Tree (AST)
        tree = ast.parse(code)

        # Initialize counters
        num_lines = len(code.splitlines())
        num_functions = 0
        num_classes = 0
        num_imports = 0
        function_names = []
        class_names = []
        dependencies = set()  # To store unique dependencies

        # Traverse the AST to count functions, classes, and imports
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                num_functions += 1
                function_names.append(node.name)
            elif isinstance(node, ast.ClassDef):
                num_classes += 1
                class_names.append(node.name)
            elif isinstance(node, ast.Import):
                # Handle `import xyz` statements
                for alias in node.names:
                    dependencies.add(alias.name)
                    num_imports += 1
            elif isinstance(node, ast.ImportFrom):
                # Handle `from xyz import abc` statements
                module = node.module
                if module:
                    dependencies.add(module)
                    num_imports += 1

        # Calculate code composition percentages
        total_components = num_functions + num_classes + num_imports
        if total_components > 0:
            func_percent = (num_functions / total_components) * 100
            class_percent = (num_classes / total_components) * 100
            import_percent = (num_imports / total_components) * 100
        else:
            func_percent = class_percent = import_percent = 0

        # Return the analysis results
        return {
            "num_lines": num_lines,
            "num_functions": num_functions,
            "num_classes": num_classes,
            "num_imports": num_imports,
            "function_names": function_names,
            "class_names": class_names,
            "dependencies": sorted(dependencies),
            "composition": {
                "functions": func_percent,
                "classes": class_percent,
                "imports": import_percent
            }
        }
    except Exception as e:
        st.error(f"Error analyzing code: {e}")
        return None

# Function to generate a PDF file
def generate_pdf(analysis_result):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setFont("Helvetica-Bold", 16)
    
    # Title
    pdf.drawString(72, 750, "Python Code Analysis Report")
    pdf.line(72, 745, 540, 745)
    
    pdf.setFont("Helvetica", 12)
    
    # Summary section
    pdf.drawString(72, 720, "Code Summary:")
    pdf.drawString(100, 700, f"Number of Lines: {analysis_result['num_lines']}")
    pdf.drawString(100, 680, f"Number of Functions: {analysis_result['num_functions']}")
    pdf.drawString(100, 660, f"Number of Classes: {analysis_result['num_classes']}")
    pdf.drawString(100, 640, f"Number of Imports: {analysis_result['num_imports']}")
    
    # Functions section
    if analysis_result["function_names"]:
        pdf.drawString(72, 610, "Functions:")
        y = 590
        for i, func in enumerate(analysis_result["function_names"], 1):
            pdf.drawString(100, y, f"{i}. {func}")
            y -= 20
            if y < 50:
                pdf.showPage()
                pdf.setFont("Helvetica", 12)
                y = 750

    # Classes section
    if analysis_result["class_names"]:
        pdf.drawString(72, y, "Classes:")
        y -= 20
        for i, cls in enumerate(analysis_result["class_names"], 1):
            pdf.drawString(100, y, f"{i}. {cls}")
            y -= 20
            if y < 50:
                pdf.showPage()
                pdf.setFont("Helvetica", 12)
                y = 750

    # Dependencies section
    if analysis_result["dependencies"]:
        pdf.drawString(72, y, "Dependencies:")
        y -= 20
        for i, dep in enumerate(analysis_result["dependencies"], 1):
            pdf.drawString(100, y, f"{i}. {dep}")
            y -= 20
            if y < 50:
                pdf.showPage()
                pdf.setFont("Helvetica", 12)
                y = 750

    pdf.save()
    buffer.seek(0)
    return buffer

# Helper function to create DataFrames with index starting from 1
def create_indexed_dataframe(data, column_name):
    df = pd.DataFrame(data, columns=[column_name])
    df.index = df.index + 1
    return df

# Streamlit app
def main():
    # Custom CSS for better styling
    st.markdown("""
    <style>
        .main {
            padding: 2rem;
        }
        .sidebar .sidebar-content {
            padding: 1.5rem;
        }
        .stMetric {
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 15px;
            background-color: #097969;
        }
        .stDataFrame {
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .stButton>button {
            width: 100%;
            border-radius: 8px;
            padding: 10px;
            font-weight: bold;
        }
        .css-1v0mbdj {
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.title("🐍 Python Code Analytics")
        st.markdown("""
        Upload a Python file to analyze its structure, metrics, and dependencies.
        """)
        
        st.markdown("---")
        st.markdown("### How to Use")
        st.markdown("""
        1. Upload a Python file using the file uploader
        2. View the analysis results
        3. Download the report as PDF
        """)
        
        st.markdown("---")
        st.markdown("### About")
        st.markdown("""
        This tool analyzes Python code to provide:
        - Code metrics (lines, functions, classes)
        - Dependencies analysis
        - Code composition visualization
        """)
        
        
    
    # Main content
    st.title("Python Code Analytics Dashboard")
    st.write("Analyze your Python code structure and dependencies with this interactive tool.")
    
    # File uploader with drag and drop
    uploaded_file = st.file_uploader(
        "Upload a Python file", 
        type=["py"],
        help="Drag and drop your Python file here or click to browse"
    )

    if uploaded_file is not None:
        # Read the file content
        code = uploaded_file.read().decode("utf-8")
        
        # Display the file name
        st.success(f"File uploaded successfully: {uploaded_file.name}")
        
        # Add an expander to view the code
        with st.expander("View Uploaded Code", expanded=False):
            st.code(code, language='python')

        # Analyze the code
        with st.spinner("Analyzing code..."):
            analysis_result = analyze_code(code)

        if analysis_result:
            # Display metrics in columns
            st.subheader("📊 Code Metrics")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Lines of Code", analysis_result["num_lines"])
            col2.metric("Functions", analysis_result["num_functions"])
            col3.metric("Classes", analysis_result["num_classes"])
            col4.metric("Dependencies", analysis_result["num_imports"])
           
            
            st.markdown("---")
            
            # Two-column layout for visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                # Bar chart using Plotly for better interactivity
                st.write("### 📈 Code Metrics Visualization")
                metrics_data = {
                    "Metric": ["Lines", "Functions", "Classes", "Imports"],
                    "Count": [
                        analysis_result["num_lines"],
                        analysis_result["num_functions"],
                        analysis_result["num_classes"],
                        analysis_result["num_imports"],
                    ],
                }
                metrics_df = pd.DataFrame(metrics_data)
                
                fig = px.bar(
                    metrics_df,
                    x="Metric",
                    y="Count",
                    color="Metric",
                    text="Count",
                    height=400
                )
                fig.update_traces(textposition='outside')
                fig.update_layout(
                    showlegend=False,
                    xaxis_title=None,
                    yaxis_title="Count",
                    margin=dict(l=20, r=20, t=30, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)
                
            with col2:
                # Interactive pie chart using Plotly
                st.write("### 🍰 Code Composition")
                composition_data = {
                    "Component": ["Functions", "Classes", "Imports"],
                    "Percentage": [
                        analysis_result["composition"]["functions"],
                        analysis_result["composition"]["classes"],
                        analysis_result["composition"]["imports"],
                    ],
                }
                composition_df = pd.DataFrame(composition_data)
                
                fig = px.pie(
                    composition_df,
                    values="Percentage",
                    names="Component",
                    hole=0.3,
                    height=400
                )
                fig.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    hoverinfo='label+percent'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # Three-column layout for detailed information
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if analysis_result["function_names"]:
                    st.write("### 🛠️ Functions")
                    st.dataframe(
                        create_indexed_dataframe(analysis_result["function_names"], "Function Name"),
                        height=300,
                        use_container_width=True
                    )
                else:
                    st.write("### 🛠️ Functions")
                    st.info("No functions found in the code.")

            with col2:
                if analysis_result["class_names"]:
                    st.write("### 🏛️ Classes")
                    st.dataframe(
                        create_indexed_dataframe(analysis_result["class_names"], "Class Name"),
                        height=300,
                        use_container_width=True
                    )
                else:
                    st.write("### 🏛️ Classes")
                    st.info("No classes found in the code.")

            with col3:
                if analysis_result["dependencies"]:
                    st.write("### 📦 Dependencies")
                    st.dataframe(
                        create_indexed_dataframe(analysis_result["dependencies"], "Dependency"),
                        height=300,
                        use_container_width=True
                    )
                else:
                    st.write("### 📦 Dependencies")
                    st.info("No dependencies found in the code.")
            
            st.markdown("---")
            
            # Export section
            st.write("### 📤 Export Analysis Report")
            st.write("Download a comprehensive PDF report of your code analysis.")
            
            # Generate and download PDF
            pdf_buffer = generate_pdf(analysis_result)
            st.download_button(
                label="📄 Download PDF Report",
                data=pdf_buffer,
                file_name=f"{uploaded_file.name.split('.')[0]}_analysis.pdf",
                mime="application/pdf",
                help="Click to download a PDF version of this analysis"
            )

# Run the app
if __name__ == "__main__":
    main()