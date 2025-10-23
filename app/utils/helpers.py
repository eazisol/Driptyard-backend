"""
Helper functions for common operations.

This module contains utility functions used throughout the application
for common operations like formatting, data transformation, and calculations.
"""

import hashlib
import secrets
import string
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from decimal import Decimal


def generate_random_string(length: int = 32) -> str:
    """
    Generate a random string of specified length.
    
    Args:
        length: Length of the random string
        
    Returns:
        str: Random string
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_hash(data: str, algorithm: str = 'sha256') -> str:
    """
    Generate hash of the given data.
    
    Args:
        data: Data to hash
        algorithm: Hashing algorithm to use
        
    Returns:
        str: Hash of the data
    """
    hash_obj = hashlib.new(algorithm)
    hash_obj.update(data.encode('utf-8'))
    return hash_obj.hexdigest()


def format_currency(amount: Decimal, currency: str = 'USD') -> str:
    """
    Format decimal amount as currency string.
    
    Args:
        amount: Decimal amount
        currency: Currency code
        
    Returns:
        str: Formatted currency string
    """
    currency_symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'JPY': '¥',
    }
    
    symbol = currency_symbols.get(currency, currency)
    return f"{symbol}{amount:,.2f}"


def format_datetime(dt: datetime, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    Format datetime object as string.
    
    Args:
        dt: Datetime object
        format_str: Format string
        
    Returns:
        str: Formatted datetime string
    """
    return dt.strftime(format_str)


def parse_datetime(date_string: str, format_str: str = '%Y-%m-%d %H:%M:%S') -> Optional[datetime]:
    """
    Parse datetime string to datetime object.
    
    Args:
        date_string: Datetime string
        format_str: Format string
        
    Returns:
        Optional[datetime]: Parsed datetime object or None if parsing fails
    """
    try:
        return datetime.strptime(date_string, format_str)
    except ValueError:
        return None


def get_current_timestamp() -> datetime:
    """
    Get current UTC timestamp.
    
    Returns:
        datetime: Current UTC timestamp
    """
    return datetime.now(timezone.utc)


def calculate_age(birth_date: datetime) -> int:
    """
    Calculate age from birth date.
    
    Args:
        birth_date: Birth date
        
    Returns:
        int: Age in years
    """
    today = get_current_timestamp().date()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def paginate_results(
    items: List[Any], 
    skip: int, 
    limit: int
) -> Dict[str, Any]:
    """
    Paginate a list of items.
    
    Args:
        items: List of items to paginate
        skip: Number of items to skip
        limit: Number of items to return
        
    Returns:
        Dict[str, Any]: Paginated results with metadata
    """
    total = len(items)
    paginated_items = items[skip:skip + limit]
    
    return {
        'items': paginated_items,
        'total': total,
        'skip': skip,
        'limit': limit,
        'has_next': skip + limit < total,
        'has_prev': skip > 0,
        'page': (skip // limit) + 1,
        'total_pages': (total + limit - 1) // limit
    }


def remove_none_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove None values from dictionary.
    
    Args:
        data: Dictionary to clean
        
    Returns:
        Dict[str, Any]: Dictionary with None values removed
    """
    return {k: v for k, v in data.items() if v is not None}


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary
        
    Returns:
        Dict[str, Any]: Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def truncate_text(text: str, max_length: int, suffix: str = '...') -> str:
    """
    Truncate text to specified length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def extract_hashtags(text: str) -> List[str]:
    """
    Extract hashtags from text.
    
    Args:
        text: Text to extract hashtags from
        
    Returns:
        List[str]: List of hashtags
    """
    import re
    hashtag_pattern = r'#\w+'
    return re.findall(hashtag_pattern, text)


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula.
    
    Args:
        lat1: First latitude
        lon1: First longitude
        lat2: Second latitude
        lon2: Second longitude
        
    Returns:
        float: Distance in kilometers
    """
    import math
    
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    
    return c * r


def generate_slug(text: str) -> str:
    """
    Generate URL-friendly slug from text.
    
    Args:
        text: Text to convert to slug
        
    Returns:
        str: URL-friendly slug
    """
    import re
    import unicodedata
    
    # Convert to lowercase
    slug = text.lower()
    
    # Remove accents and special characters
    slug = unicodedata.normalize('NFD', slug)
    slug = ''.join(c for c in slug if unicodedata.category(c) != 'Mn')
    
    # Replace spaces and special characters with hyphens
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    return slug


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """
    Mask sensitive data showing only last few characters.
    
    Args:
        data: Sensitive data to mask
        visible_chars: Number of characters to show
        
    Returns:
        str: Masked data
    """
    if len(data) <= visible_chars:
        return '*' * len(data)
    
    return '*' * (len(data) - visible_chars) + data[-visible_chars:]
