import streamlit as st
import pandas as pd
import pyodbc
import plotly.express as px
import plotly.graph_objects as go

# Page configuration
st.set_page_config(
    page_title="Banggood Product Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database connection function
@st.cache_resource
def init_connection():
    try:
        conn = pyodbc.connect(
            'DRIVER={SQL Server};'
            'SERVER=DESKTOP-Q5EPGSU;'
            'DATABASE=BanggoodAnalysis;'
            'Trusted_Connection=yes;'
        )
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

# Load data with caching
@st.cache_data
def load_data():
    conn = init_connection()
    if conn:
        query = "SELECT * FROM products"
        return pd.read_sql_query(query, conn)
    return None

@st.cache_data
def load_category_summary():
    conn = init_connection()
    if conn:
        query = """
        SELECT 
            category,
            COUNT(*) as product_count,
            AVG(price) as avg_price,
            AVG(rating) as avg_rating,
            SUM(review_count) as total_reviews,
            AVG(value_score) as avg_value_score
        FROM products 
        GROUP BY category
        """
        return pd.read_sql_query(query, conn)
    return None

def main():
    # Title and description
    st.title("📊 Banggood Product Analytics Dashboard")
    st.markdown("Real-time analysis of product data from Banggood SQL Database")
    
    # Load data
    df = load_data()
    if df is None:
        st.error("Failed to load data from database")
        return
    
    category_df = load_category_summary()
    
    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    
    # Category filter
    categories = ['All'] + sorted(df['category'].unique().tolist())
    selected_category = st.sidebar.selectbox("Select Category", categories)
    
    # Price range filter
    min_price, max_price = st.sidebar.slider(
        "Price Range ($)",
        float(df['price'].min()),
        float(df['price'].max()),
        (float(df['price'].min()), float(df['price'].max()))
    )
    
    # Rating filter
    min_rating, max_rating = st.sidebar.slider(
        "Rating Range",
        0.0, 5.0, (3.0, 5.0)
    )
    
    # Apply filters
    filtered_df = df.copy()
    if selected_category != 'All':
        filtered_df = filtered_df[filtered_df['category'] == selected_category]
    
    filtered_df = filtered_df[
        (filtered_df['price'] >= min_price) & 
        (filtered_df['price'] <= max_price) &
        (filtered_df['rating'] >= min_rating) & 
        (filtered_df['rating'] <= max_rating)
    ]
    
    # KPI Metrics
    st.header("📈 Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Products",
            value=f"{len(filtered_df):,}",
            delta=f"{len(filtered_df) - len(df)}" if selected_category != 'All' else None
        )
    
    with col2:
        avg_price = filtered_df['price'].mean()
        st.metric(
            label="Average Price",
            value=f"${avg_price:.2f}",
            delta=f"${avg_price - df['price'].mean():.2f}" if selected_category != 'All' else None
        )
    
    with col3:
        avg_rating = filtered_df['rating'].mean()
        st.metric(
            label="Average Rating",
            value=f"{avg_rating:.2f}/5",
            delta=f"{avg_rating - df['rating'].mean():.2f}" if selected_category != 'All' else None
        )
    
    with col4:
        total_reviews = filtered_df['review_count'].sum()
        st.metric(
            label="Total Reviews",
            value=f"{total_reviews:,}",
            delta=f"{total_reviews - df['review_count'].sum():,}" if selected_category != 'All' else None
        )
    
    # Charts Row 1
    st.header("📊 Product Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Price distribution by category
        fig_price = px.box(
            filtered_df, 
            x='category', 
            y='price',
            title='Price Distribution by Category',
            color='category'
        )
        fig_price.update_layout(showlegend=False)
        st.plotly_chart(fig_price, use_container_width=True)
    
    with col2:
        # Rating distribution
        fig_rating = px.histogram(
            filtered_df, 
            x='rating',
            title='Rating Distribution',
            nbins=20,
            color_discrete_sequence=['#FF4B4B']
        )
        st.plotly_chart(fig_rating, use_container_width=True)
    
    # Charts Row 2
    col1, col2 = st.columns(2)
    
    with col1:
        # Price vs Rating scatter plot
        fig_scatter = px.scatter(
            filtered_df,
            x='price',
            y='rating',
            color='category',
            size='review_count',
            hover_data=['name'],
            title='Price vs Rating Correlation',
            size_max=20
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
    
    with col2:
        # Products by price category
        price_cat_count = filtered_df['price_category'].value_counts().reset_index()
        price_cat_count.columns = ['price_category', 'count']
        
        fig_pie = px.pie(
            price_cat_count,
            values='count',
            names='price_category',
            title='Products by Price Category'
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Category Performance
    st.header("🏆 Category Performance")
    
    if category_df is not None:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Products by category
            fig_bar = px.bar(
                category_df.sort_values('product_count', ascending=True),
                y='category',
                x='product_count',
                title='Products by Category',
                orientation='h',
                color='product_count'
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            # Average price by category
            fig_price_bar = px.bar(
                category_df.sort_values('avg_price', ascending=True),
                y='category',
                x='avg_price',
                title='Average Price by Category',
                orientation='h',
                color='avg_price'
            )
            st.plotly_chart(fig_price_bar, use_container_width=True)
        
        with col3:
            # Average rating by category
            fig_rating_bar = px.bar(
                category_df.sort_values('avg_rating', ascending=True),
                y='category',
                x='avg_rating',
                title='Average Rating by Category',
                orientation='h',
                color='avg_rating'
            )
            st.plotly_chart(fig_rating_bar, use_container_width=True)
    
    # Top Products Section
    st.header("🎯 Top Performing Products")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🏆 Best Rated", "🔥 Most Reviewed", "💰 Best Value", "📈 Most Popular"])
    
    with tab1:
        # Best rated products
        best_rated = filtered_df.nlargest(10, 'rating')[['name', 'category', 'price', 'rating', 'review_count']]
        st.dataframe(best_rated, use_container_width=True)
    
    with tab2:
        # Most reviewed products
        most_reviewed = filtered_df.nlargest(10, 'review_count')[['name', 'category', 'price', 'rating', 'review_count']]
        st.dataframe(most_reviewed, use_container_width=True)
    
    with tab3:
        # Best value products
        best_value = filtered_df.nlargest(10, 'value_score')[['name', 'category', 'price', 'rating', 'value_score']]
        st.dataframe(best_value, use_container_width=True)
    
    with tab4:
        # Most popular products
        most_popular = filtered_df.nlargest(10, 'popularity_index')[['name', 'category', 'price', 'rating', 'popularity_index']]
        st.dataframe(most_popular, use_container_width=True)
    
    # Raw Data Section
    st.header("📋 Raw Data Explorer")
    
    with st.expander("View Raw Data"):
        st.dataframe(filtered_df, use_container_width=True)
        
        # Data download
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=csv,
            file_name="banggood_filtered_data.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
