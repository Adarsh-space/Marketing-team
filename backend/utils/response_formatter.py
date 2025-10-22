"""
Utility functions to format agent responses for natural conversation.
Converts JSON/structured responses to human-friendly text.
"""

import json
import re
from typing import Any, Dict

def clean_agent_response(response: Any) -> str:
    """
    Clean agent response to show only natural text.
    Removes JSON formatting, ** symbols, and extracts meaningful content.
    
    Args:
        response: Agent response (can be str, dict, or any type)
        
    Returns:
        Cleaned natural language string
    """
    # If already a clean string, return it
    if isinstance(response, str):
        # Check if it's JSON
        if response.strip().startswith('{') or response.strip().startswith('['):
            try:
                parsed = json.loads(response)
                return extract_natural_text_from_dict(parsed)
            except:
                # Not valid JSON, clean the string
                return clean_text_formatting(response)
        else:
            return clean_text_formatting(response)
    
    # If it's a dict, extract natural text
    elif isinstance(response, dict):
        return extract_natural_text_from_dict(response)
    
    # For other types, convert to string and clean
    else:
        return clean_text_formatting(str(response))


def extract_natural_text_from_dict(data: Dict) -> str:
    """
    Extract natural language content from dictionary responses.
    Prioritizes content, text, response fields over structural data.
    """
    # Priority fields that contain natural language
    priority_fields = [
        'response', 'text', 'content', 'message', 
        'description', 'copy', 'body', 'generated_content'
    ]
    
    # Try priority fields first
    for field in priority_fields:
        if field in data and data[field]:
            content = data[field]
            if isinstance(content, str):
                return clean_text_formatting(content)
            elif isinstance(content, list):
                return '\n\n'.join([clean_text_formatting(str(item)) for item in content])
    
    # Special handling for social media posts
    if 'content_type' in data and data['content_type'] == 'social_post':
        parts = []
        if 'text' in data:
            parts.append(clean_text_formatting(data['text']))
        if 'hashtags' in data and isinstance(data['hashtags'], list):
            parts.append(' '.join(data['hashtags']))
        if 'cta' in data:
            parts.append(f"\n{data['cta']}")
        return '\n\n'.join(parts)
    
    # Special handling for emails
    if 'content_type' in data and data['content_type'] == 'email':
        parts = []
        if 'subject_line' in data:
            parts.append(f"Subject: {data['subject_line']}")
        if 'body' in data:
            parts.append(f"\n{clean_text_formatting(data['body'])}")
        return '\n\n'.join(parts)
    
    # Special handling for ad copy
    if 'content_type' in data and data['content_type'] == 'ad_copy':
        parts = []
        if 'headline' in data:
            parts.append(data['headline'])
        if 'description' in data:
            parts.append(data['description'])
        if 'cta' in data:
            parts.append(f"\n{data['cta']}")
        return '\n\n'.join(parts)
    
    # Fallback: convert entire dict to readable text
    return format_dict_as_text(data)


def clean_text_formatting(text: str) -> str:
    """
    Remove markdown symbols, excessive formatting, and clean up text.
    """
    if not text:
        return ""
    
    # Remove ** bold markers
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    
    # Remove * italic markers
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    
    # Remove __ underline markers
    text = re.sub(r'__(.*?)__', r'\1', text)
    
    # Remove markdown headers
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    
    # Remove code blocks
    text = re.sub(r'```[a-z]*\n(.*?)\n```', r'\1', text, flags=re.DOTALL)
    text = re.sub(r'`(.*?)`', r'\1', text)
    
    # Clean up extra whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = text.strip()
    
    return text


def format_dict_as_text(data: Dict, indent: int = 0) -> str:
    """
    Format a dictionary as readable text (not JSON).
    """
    lines = []
    indent_str = "  " * indent
    
    for key, value in data.items():
        # Skip technical fields
        if key in ['agent', 'generated_at', 'content_type', 'status', 'task_id']:
            continue
        
        # Format key nicely
        nice_key = key.replace('_', ' ').title()
        
        if isinstance(value, dict):
            lines.append(f"{indent_str}{nice_key}:")
            lines.append(format_dict_as_text(value, indent + 1))
        elif isinstance(value, list):
            lines.append(f"{indent_str}{nice_key}:")
            for item in value:
                if isinstance(item, str):
                    lines.append(f"{indent_str}  - {item}")
                else:
                    lines.append(f"{indent_str}  - {str(item)}")
        else:
            lines.append(f"{indent_str}{nice_key}: {value}")
    
    return '\n'.join(lines)


def format_as_table(data: Dict) -> str:
    """
    Format structured data as a text table.
    Useful for displaying analytics, stats, etc.
    """
    if not data:
        return ""
    
    # Find max key length for alignment
    max_key_len = max(len(str(k)) for k in data.keys())
    
    lines = []
    lines.append("=" * (max_key_len + 30))
    
    for key, value in data.items():
        nice_key = key.replace('_', ' ').title()
        lines.append(f"{nice_key:<{max_key_len}} | {value}")
    
    lines.append("=" * (max_key_len + 30))
    
    return '\n'.join(lines)
