"""Streamlit application - API-first Clean Architecture demo."""

from datetime import datetime
from decimal import Decimal

import streamlit as st

from src.streamlit_api_client import APIClient

# Configure page
st.set_page_config(page_title="Clean Architecture Python", page_icon="🏗️", layout="wide")

# Initialize API client
if "api_client" not in st.session_state:
    st.session_state.api_client = APIClient()

api = st.session_state.api_client

# Main header
st.title("🏗️ Clean Architecture Python")
st.markdown("*API-First Clean Architecture Demo*")

# API Status check
st.sidebar.header("⚙️ System Status")
api_status = api.is_api_available()

if api_status:
    st.sidebar.success("✅ API Connected")
    st.sidebar.info(f"📡 Backend: {api.base_url}")
    st.sidebar.markdown(f"[📖 API Docs]({api.base_url}/docs)")
else:
    st.sidebar.error("❌ API Unavailable")
    st.sidebar.info(f"📡 Trying: {api.base_url}")
    if "localhost" in api.base_url:
        st.sidebar.warning("Start backend with: `make run-api`")
    else:
        st.sidebar.warning("Backend server is not responding")
    st.error("⚠️ **Backend API is not running!** Please check the API server status.")
    st.stop()

# Navigation tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["👤 Customers", "🛒 Orders", "🔍 Search", "📊 Dashboard", "🔧 API Explorer"])

# Tab 1: Customer Management
with tab1:
    st.header("👤 Customer Management")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Create Customer")
        with st.form("create_customer_form"):
            name = st.text_input("Full Name", placeholder="e.g., John Doe")
            email = st.text_input("Email", placeholder="e.g., john@example.com")

            st.write("**Preferences:**")
            theme = st.selectbox("Theme", ["light", "dark", "auto"])
            notifications = st.checkbox("Enable Notifications", value=True)
            newsletter = st.checkbox("Subscribe to Newsletter", value=False)

            submitted = st.form_submit_button("Create Customer", type="primary")

            if submitted and name and email:
                preferences = {"theme": theme, "notifications": notifications, "newsletter": newsletter}

                result = api.create_customer(name, email, preferences)
                if result:
                    st.success(f"✅ Created customer: **{result['name']}**")
                    st.json(result)
                    st.rerun()

    with col2:
        st.subheader("All Customers")
        customers = api.list_customers()

        if customers:
            for customer in customers:
                status_icon = "✅" if customer["is_active"] else "❌"
                with st.expander(f"{status_icon} {customer['name']} ({customer['email']})"):
                    col_info, col_actions = st.columns([2, 1])

                    with col_info:
                        st.write(f"**ID:** `{customer['id']}`")
                        st.write(f"**Status:** {'Active' if customer['is_active'] else 'Inactive'}")
                        st.write(
                            f"**Created:** {datetime.fromisoformat(customer['created_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')}"
                        )

                        if customer.get("preferences"):
                            st.write("**Preferences:**")
                            st.json(customer["preferences"])

                    with col_actions:
                        if st.button("View Orders", key=f"orders_{customer['id']}"):
                            st.session_state.selected_customer_id = customer["id"]
                            st.session_state.selected_customer_name = customer["name"]
        else:
            st.info("No customers found. Create some customers to get started!")

# Tab 2: Order Management
with tab2:
    st.header("🛒 Order Management")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Create Order")

        # Get customers for dropdown
        customers = api.list_customers()
        if not customers:
            st.warning("No customers available. Create customers first!")
        else:
            with st.form("create_order_form"):
                customer_options = {f"{c['name']} ({c['email']})": c["id"] for c in customers if c["is_active"]}

                if not customer_options:
                    st.warning("No active customers available!")
                    st.form_submit_button("Create Order", disabled=True)
                else:
                    selected_customer = st.selectbox("Customer", list(customer_options.keys()))
                    amount = st.number_input("Order Amount ($)", min_value=0.01, step=0.01, value=99.99)
                    currency = st.selectbox("Currency", ["USD", "EUR", "GBP"], index=0)

                    st.write("**Order Details:**")
                    product = st.text_input("Product", placeholder="e.g., Premium Widget")
                    category = st.selectbox("Category", ["electronics", "clothing", "books", "home", "other"])
                    priority = st.selectbox("Priority", ["normal", "high", "urgent"])

                    submitted = st.form_submit_button("Create Order", type="primary")

                    if submitted and selected_customer:
                        customer_id = customer_options[selected_customer]
                        details = {}
                        if product:
                            details["product"] = product
                        details["category"] = category
                        details["priority"] = priority

                        result = api.create_order(customer_id, Decimal(str(amount)), currency, details)
                        if result:
                            st.success(f"✅ Created order: **${result['total_amount']} {result['currency']}**")
                            st.json(result)
                            st.rerun()

    with col2:
        st.subheader("Recent Orders")
        orders = api.list_orders()

        if orders:
            # Sort by creation date (newest first)
            orders_sorted = sorted(orders, key=lambda x: x["created_at"], reverse=True)

            for order in orders_sorted[:10]:  # Show latest 10
                # Get customer info
                customer = api.get_customer(order["customer_id"])
                customer_name = customer["name"] if customer else "Unknown"

                status_color = {
                    "pending": "🟡",
                    "confirmed": "🟢",
                    "shipped": "🔵",
                    "delivered": "✅",
                    "cancelled": "❌",
                }
                status_icon = status_color.get(order["status"], "⚪")

                with st.expander(f"{status_icon} ${order['total_amount']} - {customer_name}"):
                    col_info, col_details = st.columns([1, 1])

                    with col_info:
                        st.write(f"**Order ID:** `{order['id']}`")
                        st.write(f"**Customer:** {customer_name}")
                        st.write(f"**Amount:** ${order['total_amount']} {order['currency']}")
                        st.write(f"**Status:** {order['status'].title()}")

                    with col_details:
                        st.write(
                            f"**Created:** {datetime.fromisoformat(order['created_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')}"
                        )
                        if order.get("details"):
                            st.write("**Details:**")
                            st.json(order["details"])
        else:
            st.info("No orders found. Create some orders to get started!")

# Tab 3: Search & Analytics
with tab3:
    st.header("🔍 Search & Analytics")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Customer Search")

        with st.form("search_form"):
            name_search = st.text_input("Name contains:", placeholder="e.g., John")
            email_search = st.text_input("Email contains:", placeholder="e.g., @gmail.com")
            status_filter = st.selectbox("Status:", ["All", "Active Only", "Inactive Only"])
            max_results = st.slider("Max Results:", 1, 50, 10)

            search_clicked = st.form_submit_button("🔍 Search", type="primary")

        if search_clicked:
            is_active = None
            if status_filter == "Active Only":
                is_active = True
            elif status_filter == "Inactive Only":
                is_active = False

            results = api.search_customers(
                name_contains=name_search if name_search else None,
                email_contains=email_search if email_search else None,
                is_active=is_active,
                limit=max_results,
            )

            if results:
                st.success(f"Found {len(results)} customer(s)")
                st.session_state.search_results = results
            else:
                st.info("No customers match your search criteria")
                st.session_state.search_results = []

    with col2:
        st.subheader("Search Results")

        if hasattr(st.session_state, "search_results") and st.session_state.search_results:
            for customer in st.session_state.search_results:
                status_icon = "✅" if customer["is_active"] else "❌"

                with st.container():
                    st.markdown(f"**{status_icon} {customer['name']}**")
                    st.markdown(f"📧 {customer['email']}")

                    # Get orders for this customer
                    customer_orders = api.get_customer_orders(customer["id"])
                    order_count = len(customer_orders) if customer_orders else 0
                    total_spent = sum(float(o["total_amount"]) for o in customer_orders) if customer_orders else 0

                    col_stats1, col_stats2 = st.columns(2)
                    with col_stats1:
                        st.metric("Orders", order_count)
                    with col_stats2:
                        st.metric("Total Spent", f"${total_spent:.2f}")

                    st.divider()
        else:
            st.info("Use the search form to find customers")

# Tab 4: Dashboard
with tab4:
    st.header("📊 System Dashboard")

    # Get data
    customers = api.list_customers()
    orders = api.list_orders()

    if customers and orders:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Customers", len(customers))

        with col2:
            active_customers = len([c for c in customers if c["is_active"]])
            st.metric("Active Customers", active_customers)

        with col3:
            st.metric("Total Orders", len(orders))

        with col4:
            total_revenue = sum(float(o["total_amount"]) for o in orders)
            st.metric("Total Revenue", f"${total_revenue:.2f}")

        st.divider()

        # Recent activity
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Recent Customers")
            recent_customers = sorted(customers, key=lambda x: x["created_at"], reverse=True)[:5]
            for customer in recent_customers:
                st.write(f"• **{customer['name']}** - {customer['email']}")

        with col2:
            st.subheader("Recent Orders")
            recent_orders = sorted(orders, key=lambda x: x["created_at"], reverse=True)[:5]
            for order in recent_orders:
                customer = api.get_customer(order["customer_id"])
                customer_name = customer["name"] if customer else "Unknown"
                st.write(f"• **${order['total_amount']}** - {customer_name}")

    else:
        st.info("Create some customers and orders to see dashboard metrics!")

# Tab 5: API Explorer
with tab5:
    st.header("🔧 API Explorer")
    st.markdown("Direct API testing interface")

    endpoint = st.selectbox(
        "Select Endpoint:",
        [
            "GET /health",
            "GET /api/v1/customers",
            "POST /api/v1/customers",
            "GET /api/v1/customers/search",
            "GET /api/v1/orders",
            "POST /api/v1/orders",
        ],
    )

    if st.button("Test Endpoint", type="primary"):
        try:
            if endpoint == "GET /health":
                response = api.session.get(f"{api.base_url}/health")
            elif endpoint == "GET /api/v1/customers":
                response = api.session.get(f"{api.base_url}/api/v1/customers/")
            elif endpoint == "GET /api/v1/customers/search":
                response = api.session.get(f"{api.base_url}/api/v1/customers/search")
            elif endpoint == "GET /api/v1/orders":
                response = api.session.get(f"{api.base_url}/api/v1/orders/")
            else:
                st.warning("POST endpoints require request body - use the forms above")
                st.stop()

            st.write(f"**Status Code:** {response.status_code}")
            st.write(f"**Headers:** {dict(response.headers)}")
            st.write("**Response:**")
            st.json(response.json())

        except Exception as e:
            st.error(f"Request failed: {str(e)}")

    st.divider()
    st.markdown("**API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)")

# Show selected customer orders if any
if hasattr(st.session_state, "selected_customer_id"):
    st.sidebar.divider()
    st.sidebar.subheader("Customer Orders")
    st.sidebar.write(f"**{st.session_state.selected_customer_name}**")

    customer_orders = api.get_customer_orders(st.session_state.selected_customer_id)
    if customer_orders:
        st.sidebar.write(f"Orders: {len(customer_orders)}")
        for order in customer_orders[-3:]:  # Show last 3
            st.sidebar.write(f"• ${order['total_amount']} ({order['status']})")
    else:
        st.sidebar.write("No orders yet")

    if st.sidebar.button("Clear Selection"):
        del st.session_state.selected_customer_id
        del st.session_state.selected_customer_name
        st.rerun()
