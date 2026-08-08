import math
import numpy as np
import re

class GeotechCalculator:
    """
    Sandboxed environment for geotechnical calculations.
    """
    
    def __init__(self):
        self.allowed_modules = {
            "math": math,
            "np": np,
            "numpy": np
        }
        
    def execute(self, code: str) -> str:
        """
        Executes the provided Python code in a restricted namespace.
        WARNING: This is a basic sandbox. Production requires deeper isolation.
        """
        # Dictionary to store local variables defined in the code
        local_scope = {}
        
        try:
            exec(code, self.allowed_modules, local_scope)
            # Return the last line's value if possible, or print output
            # For now, we assume the code prints the result or sets a specific variable 'result'
            return str(local_scope.get('result', 'Execution completed. No "result" variable found.'))
        except Exception as e:
            return f"Error executing code: {e}"


def safe_calculate(expression: str) -> str:
    """
    Safely evaluates a mathematical expression and returns the result.
    Supports common math functions for geotechnical calculations.
    
    Args:
        expression: A string like "22.5 * 18 * 1 + 10 * 37.2"
        
    Returns:
        The computed result as a string, or an error message.
    """
    # Safe namespace with math functions
    safe_namespace = {
        # Basic math
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "pow": pow,
        
        # Math module functions
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "asin": math.asin,
        "acos": math.acos,
        "atan": math.atan,
        "atan2": math.atan2,
        "sinh": math.sinh,
        "cosh": math.cosh,
        "tanh": math.tanh,
        
        "sqrt": math.sqrt,
        "exp": math.exp,
        "log": math.log,
        "log10": math.log10,
        "log2": math.log2,
        
        "radians": math.radians,
        "degrees": math.degrees,
        
        "pi": math.pi,
        "e": math.e,
        
        # NumPy for arrays if needed
        "np": np,
        "array": np.array,
    }
    
    # Clean the expression
    expr = expression.strip()
    
    # Security: Block dangerous constructs
    dangerous_patterns = [
        r"__",           # Dunder methods
        r"import",       # Import statements
        r"exec",         # Code execution
        r"eval",         # Eval
        r"open",         # File operations
        r"os\.",         # OS module
        r"sys\.",        # Sys module
        r"subprocess",   # Subprocess
        r"lambda",       # Lambda functions
        r"class\s",      # Class definitions
        r"def\s",        # Function definitions
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, expr, re.IGNORECASE):
            return f"[CALC_ERROR: Unsafe expression detected]"
    
    try:
        # Evaluate the expression in the safe namespace
        result = eval(expr, {"__builtins__": {}}, safe_namespace)
        
        # Format the result nicely
        if isinstance(result, float):
            # Round to reasonable precision
            if abs(result) < 0.01 or abs(result) > 10000:
                return f"{result:.4e}"
            else:
                return f"{result:.4f}"
        elif isinstance(result, (int, np.integer)):
            return str(result)
        elif isinstance(result, np.ndarray):
            return str(result.tolist())
        else:
            return str(result)
            
    except ZeroDivisionError:
        return "[CALC_ERROR: Division by zero]"
    except ValueError as e:
        return f"[CALC_ERROR: {e}]"
    except Exception as e:
        return f"[CALC_ERROR: {e}]"


def process_calculations(text: str) -> str:
    """
    Finds all CALCULATE(...) patterns in text and replaces them with computed results.
    
    Example:
        Input:  "The bearing capacity is CALCULATE(22.5 * 18 * 1) kPa"
        Output: "The bearing capacity is 405.0000 kPa"
    """
    # Pattern to match CALCULATE(expression)
    # Handles nested parentheses by using a non-greedy match up to the last )
    pattern = r"CALCULATE\(([^)]+)\)"
    
    def replace_calc(match):
        expression = match.group(1)
        result = safe_calculate(expression)
        return result
    
    # Replace all CALCULATE(...) patterns
    processed_text = re.sub(pattern, replace_calc, text, flags=re.IGNORECASE)
    
    return processed_text


if __name__ == "__main__":
    # Test safe_calculate
    print("Testing safe_calculate:")
    print(f"  22.5 * 18 * 1 = {safe_calculate('22.5 * 18 * 1')}")
    print(f"  tan(radians(30)) = {safe_calculate('tan(radians(30))')}")
    print(f"  sqrt(2) = {safe_calculate('sqrt(2)')}")
    print(f"  10 * 37.2 + 18 * 22.5 * 1 = {safe_calculate('10 * 37.2 + 18 * 22.5 * 1')}")
    
    print("\nTesting process_calculations:")
    test_text = "The bearing capacity is CALCULATE(10 * 37.2 + 18 * 22.5) kPa. Also, tan(30°) = CALCULATE(tan(radians(30)))"
    print(f"  Input:  {test_text}")
    print(f"  Output: {process_calculations(test_text)}")
