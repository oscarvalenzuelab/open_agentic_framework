import json
import ast
from typing import Dict, Any
from .base_tool import BaseTool
import logging

logger = logging.getLogger(__name__)

class DataSerializerTool(BaseTool):
    """Tool for serializing and deserializing data between Python objects and JSON strings"""
    
    def __init__(self):
        super().__init__()
    
    @property
    def name(self) -> str:
        return "data_serializer"
    
    @property
    def description(self) -> str:
        return "Serialize Python objects to JSON strings or deserialize JSON strings to Python objects"
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["serialize", "deserialize"],
                    "description": "The action to perform: serialize (Python object to JSON) or deserialize (JSON to Python object)"
                },
                "data": {
                    "type": "string",
                    "description": "The data to process. For serialize: Python object as string. For deserialize: JSON string"
                },
                "indent": {
                    "type": "integer",
                    "default": 2,
                    "description": "Number of spaces for JSON indentation (serialize only)"
                },
                "ensure_ascii": {
                    "type": "boolean",
                    "default": False,
                    "description": "Whether to escape non-ASCII characters (serialize only)"
                }
            },
            "required": ["action", "data"]
        }
    
    async def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the data serialization/deserialization"""
        action = parameters.get("action")
        data = parameters.get("data")
        indent = parameters.get("indent", 2)
        ensure_ascii = parameters.get("ensure_ascii", False)
        
        if not action:
            raise Exception("action is required")
        
        if data is None:
            raise Exception("data is required")
        
        try:
            if action == "serialize":
                return await self._serialize(data, indent, ensure_ascii)
            elif action == "deserialize":
                return await self._deserialize(data)
            else:
                raise Exception(f"Unknown action: {action}")
                
        except Exception as e:
            error_msg = f"Data serialization failed: {e}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    async def _serialize(self, data: str, indent: int, ensure_ascii: bool) -> Dict[str, Any]:
        """Serialize Python object to JSON string"""
        try:
            # Parse the Python object string
            if data.startswith("'") or data.startswith('"'):
                # Handle string representation
                python_obj = ast.literal_eval(data)
            else:
                # Try to evaluate as Python literal
                python_obj = ast.literal_eval(data)
            
            # Serialize to JSON
            json_string = json.dumps(python_obj, indent=indent, ensure_ascii=ensure_ascii)
            
            return {
                "action": "serialized",
                "input_type": "python_object",
                "output_type": "json_string",
                "result": json_string,
                "size": len(json_string),
                "message": f"Successfully serialized Python object to JSON string ({len(json_string)} characters)"
            }
            
        except (ValueError, SyntaxError) as e:
            raise Exception(f"Failed to parse Python object: {e}")
        except Exception as e:
            raise Exception(f"Serialization failed: {e}")
    
    async def _deserialize(self, data: str) -> Dict[str, Any]:
        """Deserialize JSON string to Python object"""
        try:
            # Parse JSON string
            python_obj = json.loads(data)
            
            return {
                "action": "deserialized",
                "input_type": "json_string",
                "output_type": "python_object",
                "result": python_obj,
                "size": len(data),
                "message": f"Successfully deserialized JSON string to Python object ({len(data)} characters)"
            }
            
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse JSON: {e}")
        except Exception as e:
            raise Exception(f"Deserialization failed: {e}") 