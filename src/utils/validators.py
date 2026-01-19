"""
Input Validators
Utility functions for validating API inputs.
"""

import re
from typing import List

from src.core.config import settings


# Valid instance type pattern
INSTANCE_TYPE_PATTERN = re.compile(
    r'^[a-z][a-z0-9]*\d*[a-z]*\.(nano|micro|small|medium|large|xlarge|\d*xlarge|metal)$'
)


def validate_instance_type(instance_type: str) -> bool:
    """
    Validate EC2 instance type format.
    
    Args:
        instance_type: Instance type string (e.g., t3.large)
        
    Returns:
        True if valid format
    """
    if not instance_type:
        return False
    
    return bool(INSTANCE_TYPE_PATTERN.match(instance_type.lower()))


def validate_region(region: str) -> bool:
    """
    Validate AWS region code.
    
    Args:
        region: AWS region code (e.g., us-east-1)
        
    Returns:
        True if valid region
    """
    if not region:
        return False
    
    return region in settings.aws_regions


def validate_regions(regions: List[str]) -> List[str]:
    """
    Validate and filter list of regions.
    
    Args:
        regions: List of region codes
        
    Returns:
        List of valid regions
    """
    return [r for r in regions if validate_region(r)]


def validate_availability_zone(az: str) -> bool:
    """
    Validate availability zone format.
    
    Args:
        az: Availability zone (e.g., us-east-1a)
        
    Returns:
        True if valid format
    """
    if not az:
        return False
    
    # AZ is region + single letter suffix
    pattern = re.compile(r'^[a-z]{2}-[a-z]+-\d[a-z]$')
    return bool(pattern.match(az.lower()))

