"""
    Contains all Enums used by ToDoFehrist application
"""
from enum import Enum


class UserSubscriptionTypesEnum(Enum):
    """
        Create Enums for UserSubscriptionTypes Model's attribute 'name'
    """

    FREEMIUM = 'FREEMIUM'
    PREMIUM = 'PREMIUM'
