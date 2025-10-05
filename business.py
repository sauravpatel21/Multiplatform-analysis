import streamlit as st
import pandas as pd
import sqlalchemy
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from fpdf import FPDF
import base64

# Function to create a PDF report
def create_pdf(analysis_results):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Add a title
    pdf.cell(200, 10, txt="Business Analytics Report", ln=True, align="C")

    # Add analysis results to the PDF
    for section, content in analysis_results.items():
        pdf.set_font("Arial", size=12, style="B")
        pdf.cell(200, 10, txt=section, ln=True)
        pdf.set_font("Arial", size=10)
        if isinstance(content, str):
            pdf.multi_cell(0, 10, txt=content)
        elif isinstance(content, pd.DataFrame):
            # Convert DataFrame to string without index
            table_content = content.to_string(index=False)
            # Add table headers
            headers = " | ".join(content.columns)
            pdf.multi_cell(0, 10, txt=headers)
            pdf.multi_cell(0, 10, txt=table_content)
        pdf.ln(5)

    # Save the PDF to a file
    pdf_output = pdf.output(dest="S")  # Returns a bytearray
    return pdf_output  # Return the bytearray directly

# Function to generate a download link for the PDF
def get_download_link(pdf_output, filename="report.pdf"):
    b64 = base64.b64encode(pdf_output).decode()  # Encode bytes to base64
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">Download PDF Report</a>'
    return href

def main():
    # Title of the app
    st.title("Business Analytics Dashboard for Actionable Insights")

    # Sidebar for user inputs
    st.sidebar.header("Database Connection Details")

    # Input fields for database connection
    db_type = st.sidebar.selectbox("Select Database Type", ["MySQL", "PostgreSQL", "SQLite"])
    db_name = st.sidebar.text_input("Database Name")
    db_user = st.sidebar.text_input("Username")
    db_password = st.sidebar.text_input("Password", type="password")
    db_host = st.sidebar.text_input("Host", value="localhost")
    db_port = st.sidebar.text_input("Port", value="3306" if db_type == "MySQL" else "5432")

    # Create a connection string based on the database type
    if db_type == "MySQL":
        connection_string = f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    elif db_type == "PostgreSQL":
        connection_string = f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    elif db_type == "SQLite":
        connection_string = f"sqlite:///{db_name}.db"


    # Connect to the database
    try:
        engine = sqlalchemy.create_engine(connection_string)
        connection = engine.connect()
        st.sidebar.success("Connected to the database successfully!")
    except Exception as e:
        st.sidebar.error(f"Error connecting to the database: {e}")
        st.stop()

    # Fetch table names from the database
    tables = sqlalchemy.inspect(engine).get_table_names()
    if not tables:
        st.error("No tables found in the database.")
        st.stop()


    # Check for required tables
    required_tables = ["orders", "customers", "products"]
    missing_tables = [table for table in required_tables if table not in tables]

    if missing_tables:
        st.error(f"The following required tables are missing in the database: {', '.join(missing_tables)}")
        st.stop()
    
    # Fetch data from all tables
    dataframes = {}
    for table in tables:
        query = f"SELECT * FROM {table}"
        dataframes[table] = pd.read_sql(query, connection)
        st.write(f"Loaded {len(dataframes[table])} rows from table: {table}")

    # Display column names for each table
    for table, df_table in dataframes.items():
        st.write(f"Columns in {table}: {df_table.columns.tolist()}")
   
    # Drop the 'region' column from the 'customers' table to avoid redundancy
    if "customers" in dataframes:
        dataframes["customers"] = dataframes["customers"].drop(columns=["region"])

    # Check for missing keys
    df_orders = dataframes.get("orders")
    df_customers = dataframes.get("customers")
    df_products = dataframes.get("products")

    if df_orders is not None and df_customers is not None:
        df = pd.merge(df_orders, df_customers, on="customer_id", how="left")
    if df_products is not None:
        df = pd.merge(df, df_products, on="product_id", how="left")

    # Debug: Display the first few rows of the DataFrame
    st.subheader("Final Joined DataFrame")
    st.write(f"Total rows in final DataFrame: {len(df)}")
    st.dataframe(df, hide_index=True)  # Display DataFrame without index
   
        
    # Ensure the data has the required columns for business analytics
    required_columns = ["order_date", "revenue", "profit", "product_category", "region", "customer_id"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"The table is missing the following required columns: {missing_columns}")
        st.stop()

    # Convert date column to datetime
    df["order_date"] = pd.to_datetime(df["order_date"])

    # Business Analytics
    st.header("Business Performance Overview")

    # 1. Revenue and Profit Analysis
    st.subheader("Revenue and Profit Analysis")

    # Total Revenue and Profit
    total_revenue = df["revenue"].sum()
    total_profit = df["profit"].sum()
    profit_margin = (total_profit / total_revenue) * 100

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Revenue", f"${total_revenue:,.2f}")
    col2.metric("Total Profit", f"${total_profit:,.2f}")
    col3.metric("Profit Margin", f"{profit_margin:.2f}%")

    # Monthly Revenue Trend
    st.subheader("Monthly Revenue Trend")
    df["month"] = df["order_date"].dt.to_period("M")
    monthly_revenue = df.groupby("month")["revenue"].sum().reset_index()
    monthly_revenue["month"] = monthly_revenue["month"].astype(str)

    fig = px.line(monthly_revenue, x="month", y="revenue", title="Monthly Revenue Over Time")
    st.plotly_chart(fig)

    # 2. Customer Analysis
    st.subheader("Customer Analysis")

    # Repeat Customers vs. New Customers
    repeat_customers = df["customer_id"].value_counts().gt(1).sum()
    new_customers = df["customer_id"].nunique() - repeat_customers

    col1, col2 = st.columns(2)
    col1.metric("Repeat Customers", repeat_customers)
    col2.metric("New Customers", new_customers)

    # Customer Segmentation by Region
    st.subheader("Customer Segmentation by Region")
    region_counts = df["region"].value_counts().reset_index()
    region_counts.columns = ["Region", "Customer Count"]

    fig = px.bar(region_counts, x="Region", y="Customer Count", title="Customers by Region")
    st.plotly_chart(fig)

    # 3. Sales Analysis
    st.subheader("Sales Analysis")

    # Top-Selling Products
    st.subheader("Top-Selling Products")
    top_products = df["product_category"].value_counts().reset_index()
    top_products.columns = ["Product Category", "Sales Count"]

    fig = px.bar(top_products, x="Product Category", y="Sales Count", title="Top-Selling Products")
    st.plotly_chart(fig)

    # Sales Performance by Region
    st.subheader("Sales Performance by Region")
    region_sales = df.groupby("region")["revenue"].sum().reset_index()

    fig = px.pie(region_sales, values="revenue", names="region", title="Revenue by Region")
    st.plotly_chart(fig)

    # 4. Inventory Analysis
    st.subheader("Inventory Analysis")

    # Check if the required columns exist in the DataFrame
    if "stock_level" in df.columns and "product_name" in df.columns and "product_category" in df.columns:
        # Filter products with low stock levels
        low_stock_products = df[df["stock_level"] < 10][["product_name", "product_category"]].drop_duplicates()
        
        # Display low stock products
        if not low_stock_products.empty:
            st.warning("Products with low stock levels :")
            st.dataframe(low_stock_products, hide_index=True)  # Display without index
        else:
            st.info("No products with low stock levels.")
    else:
        st.warning("No stock level, product name, or product category data available.")

    # 5. Actionable Insights
    st.subheader("Actionable Insights")

    # Insight 1: Low-Performing Regions
    low_performing_regions = region_sales[region_sales["revenue"] < region_sales["revenue"].quantile(0.25)]
    st.warning(f"Low-performing regions : {', '.join(low_performing_regions['region'])}. Consider targeted marketing campaigns.")

    # Insight 2: High-Profit Products
    high_profit_products = df.groupby("product_category")["profit"].sum().idxmax()
    st.success(f"Highest profit-generating product category : {high_profit_products}. Focus on promoting this category.")

    # Insight 3: Declining Monthly Revenue
    if len(monthly_revenue) > 1:
        last_month_revenue = monthly_revenue.iloc[-1]["revenue"]
        second_last_month_revenue = monthly_revenue.iloc[-2]["revenue"]
        if last_month_revenue < second_last_month_revenue:
            st.error("Revenue declined last month. Investigate potential causes.")

    # Close the database connection
    connection.close()

    # Prepare analysis results for PDF export
    analysis_results = {
        "Revenue and Profit Analysis": f"""
        Total Revenue: ${total_revenue:,.2f}
        Total Profit: ${total_profit:,.2f}
        Profit Margin: {profit_margin:.2f}%
        """,
        "Customer Analysis": f"""
        Repeat Customers: {repeat_customers}
        New Customers: {new_customers}
        """,
        "Sales Analysis": f"""
        Top-Selling Products:
        {top_products.to_string(index=False)}
        """,
        "Inventory Analysis": f"""
        Products with low stock levels:
        {low_stock_products.to_string(index=False) if 'stock_level' in df.columns and not low_stock_products.empty else 'No products with low stock levels.'}
        """,
        "Actionable Insights": f"""
        Low-Performing Regions: {', '.join(low_performing_regions['region'])}
        Highest Profit-Generating Product Category: {high_profit_products}
        """
    }

    # Debug: Print the analysis results
    st.subheader("Analysis Results for PDF")
    st.write(analysis_results)

    # Generate PDF and provide download link
    pdf_output = create_pdf(analysis_results)
    st.markdown(get_download_link(pdf_output), unsafe_allow_html=True)


# Run the app
if __name__ == "__main__":
    main()