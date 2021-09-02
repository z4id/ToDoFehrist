"""
NAME
    todofehrist.enums.py

DESCRIPTION
    Contains all Enums used by ToDoFehrist application

AUTHOR
    Zaid Afzal
"""
from enum import Enum


class UserSubscriptionTypesEnum(Enum):
    """
    NAME
        UserSubscriptionTypesEnum

    DESCRIPTION
        Create Enums for UserSubscriptionTypes Model's attribute 'name'
    """

    FREEMIUM = 'FREEMIUM'
    PREMIUM = 'PREMIUM'
