"""API client for Streamlit to communicate with FastAPI backend."""

from decimal import Decimal
from typing import Any

import requests
import streamlit as st


class APIClient:
    """Client for communicating with the FastAPI backend."""

    def __init__(self, base_url: str = "http://localhost:8000") -> None:
        self.base_url = base_url
        self.session = requests.Session()
        # Set timeout for all requests
        self.session.timeout = 10

    def is_api_available(self) -> bool:
        """Check if the FastAPI server is available."""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=2)
            return response.status_code == 200
        except requests.RequestException:
            return False

    # Customer endpoints
    def create_customer(self, name: str, email: str, preferences: dict[str, Any]) -> dict[str, Any] | None:
        """Create a new customer."""
        try:
            payload = {"name": name, "email": email, "preferences": preferences}
            response = self.session.post(f"{self.base_url}/api/v1/customers/", json=payload)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            st.error(f"Failed to create customer: {str(e)}")
            return None

    def list_customers(self) -> list[dict[str, Any]] | None:
        """Get all customers."""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/customers/")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            st.error(f"Failed to fetch customers: {str(e)}")
            return None

    def get_customer(self, customer_id: str) -> dict[str, Any] | None:
        """Get a specific customer by ID."""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/customers/{customer_id}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            st.error(f"Failed to fetch customer: {str(e)}")
            return None

    def search_customers(
        self,
        name_contains: str | None = None,
        email_contains: str | None = None,
        is_active: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]] | None:
        """Search customers with filters."""
        try:
            params: dict[str, Any] = {"limit": limit, "offset": offset}
            if name_contains:
                params["name_contains"] = name_contains
            if email_contains:
                params["email_contains"] = email_contains
            if is_active is not None:
                params["is_active"] = is_active

            response = self.session.get(f"{self.base_url}/api/v1/customers/search", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            st.error(f"Failed to search customers: {str(e)}")
            return None

    # Order endpoints
    def create_order(
        self,
        customer_id: str,
        total_amount: Decimal,
        currency: str = "USD",
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Create a new order."""
        try:
            payload = {
                "customer_id": customer_id,
                "total_amount": str(total_amount),
                "currency": currency,
                "details": details or {},
            }
            response = self.session.post(f"{self.base_url}/api/v1/orders/", json=payload)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            st.error(f"Failed to create order: {str(e)}")
            return None

    def list_orders(self) -> list[dict[str, Any]] | None:
        """Get all orders."""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/orders/")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            st.error(f"Failed to fetch orders: {str(e)}")
            return None

    def get_order(self, order_id: str) -> dict[str, Any] | None:
        """Get a specific order by ID."""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/orders/{order_id}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            st.error(f"Failed to fetch order: {str(e)}")
            return None

    def get_customer_orders(self, customer_id: str) -> list[dict[str, Any]] | None:
        """Get all orders for a specific customer."""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/orders/customer/{customer_id}")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            st.error(f"Failed to fetch customer orders: {str(e)}")
            return None
