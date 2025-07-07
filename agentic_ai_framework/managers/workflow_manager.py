"""
managers/workflow_manager.py - Debug Version with Enhanced Logging
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class WorkflowManager:
    """Debug workflow manager with enhanced logging"""
    
    def __init__(self, agent_manager, tool_manager, memory_manager):
        self.agent_manager = agent_manager
        self.tool_manager = tool_manager
        self.memory_manager = memory_manager
        logger.info("Initialized debug workflow manager")
    
    async def execute_workflow(
        self, 
        workflow_name: str, 
        context: Dict[str, Any] = {},
        agent_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute workflow with input schema support"""
    
        workflow = self.memory_manager.get_workflow(workflow_name)
        if not workflow:
            raise ValueError(f"Workflow {workflow_name} not found")

        if not workflow.get("enabled", True):
            raise ValueError(f"Workflow {workflow_name} is disabled")

        logger.info(f"Starting workflow {workflow_name} with initial context: {context}")
        if agent_name:
            logger.info(f"Workflow execution associated with agent: {agent_name}")
    
        # NEW: Validate input against schema if present
        input_schema = workflow.get("input_schema")
        if input_schema:
            validation_error = self._validate_input_schema(input_schema, context)
            if validation_error:
                raise ValueError(f"Input validation failed: {validation_error}")
            logger.info("Input validation passed")
    
        results = []
        workflow_context = context.copy()
        previous_step_result = None  # NEW: Track previous step result
    
        for i, step in enumerate(workflow["steps"]):
            try:
                logger.info(f"=== STEP {i+1}/{len(workflow['steps'])} ===")
                logger.info(f"Step definition: {step}")
                logger.info(f"Current context keys: {list(workflow_context.keys())}")
            
                # NEW: Handle input source for this step
                step_input_context = self._prepare_step_input(
                    step, workflow_context, previous_step_result, i
                )
            
                # Resolve variables in step parameters
                resolved_step = self._resolve_variables(step, step_input_context)
                logger.info(f"Resolved step: {resolved_step}")
            
                if resolved_step["type"] == "agent":
                    result = await self._execute_agent_step(resolved_step, step_input_context)
                    # Try to parse JSON from agent response
                    result = self._parse_agent_result(result)
                
                elif resolved_step["type"] == "tool":
                    result = await self._execute_tool_step(resolved_step, step_input_context, agent_name)
                    logger.info(f"Tool result type: {type(result)}")
                    logger.info(f"Tool result: {result}")
                else:
                    raise ValueError(f"Unknown step type: {resolved_step['type']}")
            
                # Store result in context if context_key is specified
                if resolved_step.get("context_key"):
                    context_key = resolved_step["context_key"]
                    workflow_context[context_key] = result
                    logger.info(f"Stored result in context key '{context_key}'")
            
                # Update previous step result
                previous_step_result = result
            
                results.append({
                    "step": i + 1,
                    "type": resolved_step["type"],
                    "name": resolved_step["name"],
                    "result": result,
                    "context_key": resolved_step.get("context_key")
                })
            
                logger.info(f"Step {i+1} completed successfully")
            
            except Exception as e:
                error_msg = f"Error in workflow step {i+1}: {e}"
                logger.error(error_msg)
                results.append({
                    "step": i + 1,
                    "type": step["type"],
                    "name": step["name"],
                    "error": str(e)
                })
                raise Exception(f"Workflow {workflow_name} failed at step {i+1}: {e}")
    
        # --- Output filtering logic ---
        output_spec = workflow.get("output_spec")
        if isinstance(output_spec, dict) and output_spec.get("extractions"):
            # Use data extraction logic directly
            extracted_data = self._extract_output_data(workflow_context, output_spec.get("extractions", []))
            return {
                "workflow_name": workflow_name,
                "status": "completed",
                "steps_executed": len(results),
                "output": extracted_data,
                "message": f"Extracted {len(extracted_data)} values"
            }
        # ---
        return {
            "workflow_name": workflow_name,
            "status": "completed",
            "steps_executed": len(results),
            "results": results,
            "final_context": workflow_context
        }
    
    def _validate_input_schema(self, input_schema: Dict[str, Any], input_data: Dict[str, Any]) -> Optional[str]:
        """Validate input data against schema"""
        try:
            # Check required fields
            required_fields = input_schema.get("required", [])
            for field in required_fields:
                if field not in input_data:
                    return f"Required field '{field}' is missing"
            
                value = input_data[field]
                if value is None or (isinstance(value, str) and value.strip() == ""):
                    return f"Required field '{field}' cannot be empty"
        
            # Basic type validation
            properties = input_schema.get("properties", {})
            for field_name, field_schema in properties.items():
                if field_name in input_data:
                    expected_type = field_schema.get("type")
                    value = input_data[field_name]
                
                    if expected_type and not self._validate_field_type(value, expected_type):
                        return f"Field '{field_name}' should be of type {expected_type}"
        
            return None
        
        except Exception as e:
            return f"Validation error: {str(e)}"

    def _validate_field_type(self, value: Any, expected_type: str) -> bool:
        """Validate field type against JSON schema type"""
        type_mapping = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict
        }
    
        if expected_type in type_mapping:
            expected_python_type = type_mapping[expected_type]
            return isinstance(value, expected_python_type)
    
        return True
    
    def _parse_agent_result(self, result: str) -> Any:
        """Parse agent result, trying to extract JSON if possible"""
        logger.info(f"Agent result type: {type(result)}")
        logger.info(f"Agent result (raw): {repr(result)}")
    
        original_result = result
        try:
            if isinstance(result, str):
                # Try to extract JSON from the response
                json_match = re.search(r'\{.*\}', result.strip(), re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    logger.info(f"Extracted JSON string: {json_str}")
                    parsed_result = json.loads(json_str)
                    logger.info(f"Successfully parsed JSON: {parsed_result}")
                    return parsed_result
                elif result.strip().startswith('{') and result.strip().endswith('}'):
                    parsed_result = json.loads(result.strip())
                    logger.info(f"Successfully parsed full response as JSON: {parsed_result}")
                    return parsed_result
                else:
                    logger.info("Agent result doesn't look like JSON, keeping as string")
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse agent result as JSON: {e}")
            logger.warning(f"Original result: {repr(original_result)}")
    
        return original_result
    
    def _prepare_step_input(
        self, 
        step: Dict[str, Any], 
        workflow_context: Dict[str, Any], 
        previous_step_result: Any, 
        step_index: int
    ) -> Dict[str, Any]:
        """Prepare input context for a step based on its configuration"""
    
        use_previous_output = step.get("use_previous_output", False)
    
        if use_previous_output and step_index > 0 and previous_step_result is not None:
            logger.info(f"Step {step_index + 1} using previous step output as input")
        
            # If previous result is a dict, merge it with workflow context
            if isinstance(previous_step_result, dict):
                step_context = {**workflow_context, **previous_step_result}
            else:
                # If previous result is not a dict, put it in a special key
                step_context = workflow_context.copy()
                step_context["previous_result"] = previous_step_result
        
            logger.info(f"Step input context: {step_context}")
            return step_context
        else:
            logger.info(f"Step {step_index + 1} using workflow input context")
            return workflow_context
    
    async def _execute_agent_step(
        self, 
        step: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> str:
        """Execute an agent step in the workflow"""
        agent_name = step["name"]
        
        # Extract task from parameters if available, otherwise from step directly
        parameters = step.get("parameters", {})
        task = parameters.get("task") or step.get("task", "Complete the assigned task")
        
        # Extract context from parameters if available
        agent_context = parameters.get("context", context)
        
        logger.info(f"Executing agent {agent_name} with task: {task}")
        
        return await self.agent_manager.execute_agent(agent_name, task, agent_context)
    
    async def _execute_tool_step(
        self, 
        step: Dict[str, Any], 
        context: Dict[str, Any],
        agent_name: Optional[str] = None
    ) -> Any:
        """Execute a tool step with enhanced debugging"""
        tool_name = step.get("tool") or step["name"]  # Use 'tool' field if available, fallback to 'name'
        parameters = step.get("parameters", {})
        
        logger.info(f"Tool step parameters before execution: {parameters}")
        
        # Check for None values in parameters
        for param_name, param_value in parameters.items():
            if param_value is None:
                logger.error(f"Parameter '{param_name}' is None! This will cause the tool to fail.")
                logger.error(f"Full parameters: {parameters}")
                raise ValueError(f"Tool parameter '{param_name}' resolved to None")
        
        logger.info(f"Executing tool {tool_name} with parameters: {parameters}")
        
        return await self.tool_manager.execute_tool(tool_name, parameters, agent_name)
    
    def _substitute_variables(self, text: str, context: Dict[str, Any], preserve_objects: bool = False) -> Any:
        """Enhanced variable substitution with debugging and optional object preservation"""
        if not isinstance(text, str):
            return text
        
        logger.debug(f"Substituting variables in: '{text}'")
        logger.debug(f"Available context: {context}")
        logger.debug(f"Preserve objects: {preserve_objects}")
        
        # Pattern to match {{variable}} or {{object.property}} or {{array[0].property}}
        pattern = r'\{\{([^}]+)\}\}'
        
        def replace_var(match):
            var_path = match.group(1).strip()
            logger.debug(f"Processing variable: {var_path}")
            
            try:
                # Handle nested property access with array indexing (e.g., attachments.vault_files[0].vault_filename)
                if '.' in var_path or '[' in var_path:
                    # Split by dots but preserve array indices
                    parts = []
                    current_part = ""
                    in_bracket = False
                    
                    for char in var_path:
                        if char == '[':
                            if current_part:
                                parts.append(current_part)
                                current_part = ""
                            in_bracket = True
                            current_part += char
                        elif char == ']':
                            current_part += char
                            parts.append(current_part)
                            current_part = ""
                            in_bracket = False
                        elif char == '.' and not in_bracket:
                            if current_part:
                                parts.append(current_part)
                                current_part = ""
                        else:
                            current_part += char
                    
                    if current_part:
                        parts.append(current_part)
                    
                    value = context
                    logger.debug(f"Navigating path: {parts}")
                    
                    for i, part in enumerate(parts):
                        part = str(part)
                        logger.debug(f"  Step {i}: accessing '{part}' in {type(value)}")
                        # Handle array indexing
                        if part.startswith('[') and part.endswith(']'):
                            try:
                                index = int(part[1:-1])  # Remove brackets and convert to int
                                if isinstance(value, list) and 0 <= index < len(value):
                                    value = value[index]
                                    logger.debug(f"  Found array element at index {index}: {repr(value)}")
                                else:
                                    logger.error(f"Cannot access array index {index} in {type(value)}")
                                    return match.group(0)  # Return original if not found
                            except (ValueError, IndexError):
                                logger.error(f"Invalid array index: {part}")
                                return match.group(0)
                            continue  # Always continue to next part after array indexing
                        # Only use string keys for dicts, skip if part is an array index
                        if not (part.startswith('[') and part.endswith(']')) and isinstance(value, dict):
                            key = str(part)
                            if key in value:
                                value = value[key]
                                logger.debug(f"  Found: {repr(value)}")
                            else:
                                logger.error(f"Cannot access {var_path}: '{key}' not found in {type(value)}")
                                logger.error(f"Available keys: {list(value.keys())}")
                                return match.group(0)  # Return original if not found
                        elif isinstance(value, list):
                            # If we hit an array but part is not a digit, try to find by key
                            found = False
                            for item in value:
                                if isinstance(part, str) and not (part.startswith('[') and part.endswith(']')) and isinstance(item, dict) and part in item:
                                    value = item[part]
                                    found = True
                                    break
                            if not found:
                                logger.error(f"Cannot access {var_path}: '{part}' not found in {type(value)}")
                                return match.group(0)  # Return original if not found
                        else:
                            logger.error(f"Cannot access {var_path}: '{part}' not found in {type(value)}")
                            if isinstance(value, dict):
                                logger.error(f"Available keys: {list(value.keys())}")
                            elif isinstance(value, list):
                                logger.error(f"Array length: {len(value)}")
                            return match.group(0)  # Return original if not found
                    
                    # Always return string for re.sub compatibility
                    result = str(value) if not isinstance(value, str) else value
                    logger.debug(f"Variable {var_path} resolved to string: {repr(result)}")
                    return result
                
                # Simple variable access
                elif var_path in context:
                    value = context[var_path]
                    # Always return string for re.sub compatibility
                    result = str(value) if not isinstance(value, str) else value
                    logger.debug(f"Variable {var_path} resolved to string: {repr(result)}")
                    return result
                else:
                    logger.error(f"Variable {var_path} not found in context")
                    logger.error(f"Available variables: {list(context.keys())}")
                    return match.group(0)  # Keep original if not found
                    
            except Exception as e:
                logger.error(f"Error resolving variable {var_path}: {e}")
                return match.group(0)  # Keep original on error
        
        # Check if the entire text is a single variable reference
        if re.match(pattern, text.strip()):
            # Single variable reference - return the object directly if preserve_objects is True
            match = re.match(pattern, text.strip())
            if match:
                var_path = match.group(1).strip()
                
                # Handle nested property access with array indexing
                if '.' in var_path or '[' in var_path:
                    parts = []
                    current_part = ""
                    in_bracket = False
                    
                    for char in var_path:
                        if char == '[':
                            if current_part:
                                parts.append(current_part)
                                current_part = ""
                            in_bracket = True
                            current_part += char
                        elif char == ']':
                            current_part += char
                            parts.append(current_part)
                            current_part = ""
                            in_bracket = False
                        elif char == '.' and not in_bracket:
                            if current_part:
                                parts.append(current_part)
                                current_part = ""
                        else:
                            current_part += char
                    
                    if current_part:
                        parts.append(current_part)
                    
                    value = context
                    for part in parts:
                        part = str(part)
                        # Handle array indexing
                        if part.startswith('[') and part.endswith(']'):
                            try:
                                index = int(part[1:-1])
                                if isinstance(value, list) and 0 <= index < len(value):
                                    value = value[index]
                                else:
                                    return text  # Return original if not found
                            except (ValueError, IndexError):
                                return text
                            continue  # Always continue to next part after array indexing
                        # Only use string keys for dicts, skip if part is an array index
                        if not (part.startswith('[') and part.endswith(']')) and isinstance(value, dict):
                            key = str(part)
                            if key in value:
                                value = value[key]
                            else:
                                return text  # Return original if not found
                        elif isinstance(value, list):
                            found = False
                            for item in value:
                                if isinstance(part, str) and not (part.startswith('[') and part.endswith(']')) and isinstance(item, dict) and part in item:
                                    value = item[part]
                                    found = True
                                    break
                            if not found:
                                return text  # Return original if not found
                        else:
                            return text  # Return original if not found
                elif var_path in context:
                    value = context[var_path]
                else:
                    return text  # Return original if not found
                
                if preserve_objects:
                    logger.debug(f"Single variable {var_path} resolved to object: {repr(value)}")
                    return value
                else:
                    result = str(value) if not isinstance(value, str) else value
                    logger.debug(f"Single variable {var_path} resolved to string: {repr(result)}")
                    return result
        
        # Multiple variables or mixed content - use regex substitution (always returns string)
        result = re.sub(pattern, replace_var, text)
        logger.debug(f"Final substitution result: '{result}'")
        return result
    
    def _resolve_variables(
        self, 
        step: Dict[str, Any], 
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve variables in step definition with debugging"""
        logger.debug(f"Resolving variables in step: {step}")
        resolved_step = {}
        
        # Check if this step should preserve objects
        preserve_objects = step.get("preserve_objects", False)
        logger.debug(f"Step preserve_objects flag: {preserve_objects}")
        
        for key, value in step.items():
            if isinstance(value, str):
                resolved_step[key] = self._substitute_variables(value, context, preserve_objects)
            elif isinstance(value, dict):
                resolved_step[key] = self._resolve_dict_variables(value, context, preserve_objects)
            elif isinstance(value, list):
                resolved_step[key] = self._resolve_list_variables(value, context, preserve_objects)
            else:
                resolved_step[key] = value
        
        logger.debug(f"Resolved step result: {resolved_step}")
        return resolved_step
    
    def _resolve_dict_variables(
        self, 
        data: Dict[str, Any], 
        context: Dict[str, Any],
        preserve_objects: bool = False
    ) -> Dict[str, Any]:
        """Recursively resolve variables in dictionary"""
        resolved = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                resolved[key] = self._substitute_variables(value, context, preserve_objects)
            elif isinstance(value, dict):
                resolved[key] = self._resolve_dict_variables(value, context, preserve_objects)
            elif isinstance(value, list):
                resolved[key] = self._resolve_list_variables(value, context, preserve_objects)
            else:
                resolved[key] = value
        
        return resolved
    
    def _resolve_list_variables(
        self, 
        data: List[Any], 
        context: Dict[str, Any],
        preserve_objects: bool = False
    ) -> List[Any]:
        """Recursively resolve variables in list"""
        resolved = []
        
        for item in data:
            if isinstance(item, str):
                resolved.append(self._substitute_variables(item, context, preserve_objects))
            elif isinstance(item, dict):
                resolved.append(self._resolve_dict_variables(item, context, preserve_objects))
            elif isinstance(item, list):
                resolved.append(self._resolve_list_variables(item, context, preserve_objects))
            else:
                resolved.append(item)
        
        return resolved
    
    def validate_workflow(self, workflow_definition: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a workflow definition"""
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ["name", "description", "steps"]
        for field in required_fields:
            if field not in workflow_definition:
                errors.append(f"Missing required field: {field}")
        
        # Validate steps
        steps = workflow_definition.get("steps", [])
        if not steps:
            errors.append("Workflow must have at least one step")
        
        for i, step in enumerate(steps):
            step_errors = self._validate_step(step, i + 1)
            errors.extend(step_errors)
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _validate_step(self, step: Dict[str, Any], step_number: int) -> List[str]:
        """Validate a single workflow step"""
        errors = []
        
        if "type" not in step:
            errors.append(f"Step {step_number}: Missing 'type' field")
            return errors
        
        if "name" not in step:
            errors.append(f"Step {step_number}: Missing 'name' field")
            return errors
        
        step_type = step["type"]
        if step_type not in ["agent", "tool"]:
            errors.append(f"Step {step_number}: Invalid type '{step_type}'. Must be 'agent' or 'tool'")
        
        # Validate agent steps
        if step_type == "agent":
            agent_name = step["name"]
            agent = self.memory_manager.get_agent(agent_name)
            if not agent:
                errors.append(f"Step {step_number}: Agent '{agent_name}' not found")
        
        # Validate tool steps
        elif step_type == "tool":
            tool_name = step.get("tool") or step["name"]  # Use 'tool' field if available, fallback to 'name'
            tool = self.memory_manager.get_tool(tool_name)
            if not tool:
                errors.append(f"Step {step_number}: Tool '{tool_name}' not found")
        
        return errors
    
    def get_workflow_status(self, workflow_name: str) -> Dict[str, Any]:
        """Get status of a workflow"""
        workflow = self.memory_manager.get_workflow(workflow_name)
        if not workflow:
            return {"status": "not_found"}
        
        validation = self.validate_workflow(workflow)
        
        return {
            "status": "active" if workflow["enabled"] else "disabled",
            "name": workflow["name"],
            "description": workflow["description"],
            "steps_count": len(workflow["steps"]),
            "valid": validation["valid"],
            "errors": validation["errors"],
            "warnings": validation["warnings"],
            "last_update": workflow["updated_at"]
        }
    
    def _extract_output_data(self, data: Dict[str, Any], extractions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract data from workflow context using extraction specifications"""
        results = {}
        
        for extraction in extractions:
            try:
                name = extraction.get("name", "unknown")
                ext_type = extraction.get("type", "path")
                query = extraction.get("query", "")
                default_val = extraction.get("default", "")
                format_type = extraction.get("format", "text")
                find_criteria = extraction.get("find_criteria", {})
                
                # Extract value based on type
                if ext_type == "path":
                    value = self._extract_path_safe(data, query, default_val)
                elif ext_type == "find":
                    value = self._find_in_data(data, find_criteria, default_val)
                elif ext_type == "regex":
                    value = self._extract_regex_safe(json.dumps(data), query, default_val)
                elif ext_type == "literal":
                    value = query
                elif ext_type == "join_field":
                    field = extraction.get("field", "")
                    separator = extraction.get("separator", ",")
                    value = self._extract_join_field(data, query, field, separator, default_val)
                else:
                    value = default_val
                
                # Format value
                formatted_value = self._format_safe(value, format_type)
                results[str(name)] = formatted_value
                
            except Exception as e:
                logger.warning(f"Extraction failed for {extraction.get('name', 'unknown')}: {e}")
                results[str(extraction.get("name", "unknown"))] = extraction.get("default", "")
        
        return results
    
    def _extract_path_safe(self, data: Any, path: str, default: str) -> str:
        """Safe path extraction that always returns a string"""
        try:
            if not path or not isinstance(data, dict):
                return default
            
            current = data
            parts = str(path).split('.')
            
            for part in parts:
                if not part:
                    continue
                
                # Handle array indices
                if part.isdigit():
                    index = int(part)
                    if isinstance(current, list) and 0 <= index < len(current):
                        current = current[index]
                    else:
                        return default
                elif isinstance(current, dict):
                    current = current.get(part)
                elif isinstance(current, list):
                    # If we hit an array but part is not a digit, try to find by key
                    found = False
                    for item in current:
                        if isinstance(item, dict) and part in item:
                            current = item[part]
                            found = True
                            break
                    if not found:
                        return default
                else:
                    return default
                    
                if current is None:
                    return default
            
            # Convert result to string
            return self._convert_to_string(current, default)
                
        except Exception as e:
            logger.debug(f"Path extraction error: {e}")
            return default
    
    def _find_in_data(self, data: Any, criteria: Dict[str, str], default: str) -> str:
        """Find data using flexible criteria"""
        try:
            array_path = criteria.get("array_path", "")
            match_field = criteria.get("match_field", "")
            match_value = criteria.get("match_value", "")
            extract_field = criteria.get("extract_field", "")
            
            if not all([array_path, match_field, match_value, extract_field]):
                return default
            
            # Get the array
            array_data = self._extract_path_safe(data, array_path, "")
            if array_data == default:  # Failed to get array
                return default
            
            # Parse array_data if it's a string representation
            if isinstance(array_data, str) and array_data.startswith('['):
                try:
                    array_data = json.loads(array_data)
                except:
                    return default
            
            # Find matching item
            if isinstance(array_data, list):
                for item in array_data:
                    if isinstance(item, dict):
                        if str(item.get(match_field, "")) == match_value:
                            result = item.get(extract_field)
                            return self._convert_to_string(result, default)
            
            return default
            
        except Exception as e:
            logger.debug(f"Find in data error: {e}")
            return default
    
    def _convert_to_string(self, value: Any, default: str) -> Any:
        """Convert any value to string safely, but preserve dicts and lists"""
        if value is None:
            return default
        elif isinstance(value, (str, int, float, bool)):
            return str(value)
        elif isinstance(value, (list, tuple)):
            return list(value)  # Return as list, not string
        elif isinstance(value, dict):
            return value  # Return as dict, not JSON string
        else:
            return str(value)
    
    def _extract_regex_safe(self, text: str, pattern: str, default: str) -> str:
        """Safe regex extraction"""
        try:
            if not text or not pattern:
                return default
            
            matches = re.findall(str(pattern), str(text))
            if not matches:
                return default
            elif len(matches) == 1:
                match = matches[0]
                return str(match) if isinstance(match, str) else str(match[0]) if match else default
            else:
                return ", ".join(str(m) for m in matches if m)
                
        except Exception as e:
            logger.debug(f"Regex extraction error: {e}")
            return default
    
    def _format_safe(self, value: str, format_type: str) -> Any:
        """Safe formatting that handles type conversion"""
        try:
            if format_type == "number":
                try:
                    if '.' in str(value):
                        return float(value)
                    else:
                        return int(value)
                except (ValueError, TypeError):
                    return 0
            elif format_type == "boolean":
                return str(value).lower() in ('true', '1', 'yes', 'on')
            else:
                return str(value)
        except Exception:
            return str(value)
    
    def _extract_join_field(self, data: Any, array_path: str, field: str, separator: str, default: str) -> str:
        """Extract an array at array_path, join all values of field with separator"""
        try:
            # Get the actual data object, not a string representation
            current = data
            if not array_path or not isinstance(current, dict):
                return default
            
            parts = str(array_path).split('.')
            
            for part in parts:
                if not part:
                    continue
                
                # Handle array indices
                if part.isdigit():
                    index = int(part)
                    if isinstance(current, list) and 0 <= index < len(current):
                        current = current[index]
                    else:
                        return default
                elif isinstance(current, dict):
                    current = current.get(part)
                elif isinstance(current, list):
                    # If we hit an array but part is not a digit, try to find by key
                    found = False
                    for item in current:
                        if isinstance(item, dict) and part in item:
                            current = item[part]
                            found = True
                            break
                    if not found:
                        return default
                else:
                    return default
                    
                if current is None:
                    return default
            
            # Now current should be the array we want to process
            if not isinstance(current, list):
                return default
            
            values = [str(item.get(field, "")) for item in current if isinstance(item, dict) and field in item]
            return separator.join(values)
        except Exception as e:
            logger.warning(f"join_field extraction failed: {e}")
            return default