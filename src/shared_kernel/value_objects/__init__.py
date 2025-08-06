"""Common value objects for the shared kernel."""

from .address import Address
from .email import Email
from .money import Money
from .phone_number import PhoneNumber

__all__ = ["Address", "Email", "Money", "PhoneNumber"]
