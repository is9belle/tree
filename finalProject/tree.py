import subprocess
import platform
import sys
import re
import os
from textx import metamodel_from_file
sys.tracebacklimit = 1  # hide internal traceback for cleaner error messages

# ─────────────────────────────────────────────
# STEP 1: Run tree and collect raw output
# ─────────────────────────────────────────────

if len(sys.argv) < 2:
    sys.argv.append(".")

path = sys.argv[1]

if platform.system() == "Windows":
    command = ["cmd", "/c", "tree", "/F", path]
else:
    command = ["tree", "-a", path]
raw = subprocess.run(command, capture_output=True, text=True)

# ─────────────────────────────────────────────
# STEP 2: Strip tree-drawing characters, preserve depth
# ─────────────────────────────────────────────

TREE_PREFIX = re.compile(r'^[\+\-\|\¦│├└─\s]+')

def parse_tree_output(output):
    """
    Returns list of (depth, name) tuples.
    Strips all tree-drawing chars (├──, └──, │, spaces used for indentation).
    Depth is calculated from prefix length (every 4 chars = 1 level).
    Skips Windows tree header lines and empty lines.
    Also skips the root folder line itself (depth 0 header).
    """
    lines = output.splitlines()
    parsed = []

    path_to_skip = path if path != "." else "C:"  # Windows tree output shows the root folder as "C:\path\to\folder"

    for line in lines:
        if not line.strip():
            continue
        # Skip tree header/footer lines
        if re.match(r'^[A-Za-z]:.', line) or path_to_skip in line or 'Folder PATH listing' in line or 'Volume serial number' in line or ('directories,' in line and 'files' in line):
            continue

        # Calculate depth from prefix length
        match = TREE_PREFIX.match(line)
        prefix_len = len(match.group()) if match else 0
        depth = prefix_len // 4  # each level = 4 chars on Windows

        name = TREE_PREFIX.sub('', line).strip()
        
        if name:
            parsed.append((depth, name))
        
    return parsed

# ─────────────────────────────────────────────
# STEP 3: Convert (depth, name) list → bracket-nested text
# ─────────────────────────────────────────────

def extract_op_and_args(node_name):
    """
    Strip the numeric ordering prefix from a node name.
    '1.assign' -> 'assign'
    '2.100'    -> '100'    (numeric literal)
    '1.i'      -> 'i'      (variable reference)
    """
    parts = node_name.split('.', 1)
    return parts[1] if len(parts) == 2 else node_name

def build_tree(nodes, index=0, parent_depth=-1):
    """
    Recursively build a nested list structure:
    [('assign', [('i', []), ('1', [])]), ...]
    """
    result = []
    while index < len(nodes):
        depth, raw_name = nodes[index]
        name = extract_op_and_args(raw_name)

        if depth <= parent_depth:
            break  # back up to parent

        children, index = build_tree(nodes, index + 1, depth)
        result.append((name, children))

    return result, index

def encode_leaf_value(value):
    """Return a leaf value as valid program text."""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value

    if re.fullmatch(r'-?\d+(?:\.\d+)?', value):
        return value

    if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', value):
        return value

    escaped = value.replace('\\', '\\\\').replace('"', '\\"')
    return f'"{escaped}"'

def tree_to_text(node_name, children):
    """
    Convert a node and its children into bracketed text.
    e.g. assign with children ['i', '1'] -> assign(i, 1)
    """
    if not children:
        # Leaf node — emit plain identifiers/numbers, quote everything else.
        return encode_leaf_value(node_name)

    child_texts = [tree_to_text(c_name, c_children) for c_name, c_children in children]
    return f"{node_name}({', '.join(child_texts)})"

def nodes_to_program_text(nodes):
    """
    Top-level conversion: list of (depth, name) -> full program string.
    """
    tree, _ = build_tree(nodes)
    parts = [tree_to_text(name, children) for name, children in tree]
    return ', '.join(parts)

# ─────────────────────────────────────────────
# STEP 4: Parse with TextX
# ─────────────────────────────────────────────

def interpret_value(val):
    """Return the numeric or variable value from a Value node."""
    if hasattr(val, 'value'):       # NumberLiteral
        return float(val.value)
    elif hasattr(val, 'name'):      # VarRef
        return val.name
    return val


def resolve_value(value, env):
    """Evaluate a Value node or raw literal into a concrete runtime value."""
    evaluated = interpret(value, env)
    if evaluated is None:
        return None
    return env.get(evaluated, evaluated) if isinstance(evaluated, str) else evaluated


def as_statements(body):
    """Normalize a body node into a list of statements."""
    if body is None:
        return []
    if isinstance(body, list):
        return body
    return [body]

def interpret(node, env):
    """Walk the AST and execute nodes."""
    if node is None:
        return None
    
    # Handle the special case where textX parsed 'input' as a string
    if isinstance(node, str):
        if node == 'input':
            return input()
        else:
            raise ValueError(f"interpret() expected a node object, got unexpected string: {repr(node)}")
    
    cls = node.__class__.__name__
    
    if cls == 'Assignment':
        env[node.var] = resolve_value(node.value, env)
        return None

    elif cls == 'Comment':
        return None

    elif cls == 'Input':
        return input()

    elif cls == 'Add':
        if not node.values:
            return 0
        
        # Resolve all values
        resolved = [resolve_value(val, env) for val in node.values]
        
        # Check if any value is a string
        has_string = any(isinstance(v, str) for v in resolved)
        
        if has_string:
            # Convert all to strings and concatenate
            return ''.join(str(v) for v in resolved)
        else:
            # Sum as numbers
            return sum(resolved)

    elif cls == 'Sub':
        left = resolve_value(node.minuend, env)
        right = resolve_value(node.subtrahend, env)
        return left - right

    elif cls == 'Mul':
        if not node.values:
            return 1
        
        # Resolve all values and multiply
        result = resolve_value(node.values[0], env)
        for val in node.values[1:]:
            result = result * resolve_value(val, env)
        return result

    elif cls == 'Div':
        left = resolve_value(node.dividend, env)
        right = resolve_value(node.divisor, env)
        return left / right

    elif cls == 'Mod':
        left = resolve_value(node.dividend, env)
        right = resolve_value(node.modulus, env)
        return left % right

    elif cls == 'Print':
        output = ""
        for value in node.value:
            val = resolve_value(value, env)
            output += str(val) + " "
        print(output.strip())
        return None

    elif cls == 'IfStatement':
        if eval_condition(node.condition, env):
            for stmt in as_statements(node.then_body):
                interpret(stmt, env)
        else:
            matched = False
            for elif_cond, elif_stmts in zip(node.elif_condition, node.elif_body):
                if eval_condition(elif_cond, env):
                    for stmt in as_statements(elif_stmts):
                        interpret(stmt, env)
                    matched = True
                    break
            if not matched and node.else_body:
                for stmt in as_statements(node.else_body):
                    interpret(stmt, env)
        return None

    elif cls == 'WhileLoop':
        while eval_condition(node.condition, env):
            for stmt in as_statements(node.body):
                interpret(stmt, env)
        return None

    elif cls == 'ForLoop':
        interpret(node.init, env)
        while eval_condition(node.condition, env):
            for stmt in as_statements(node.body):
                interpret(stmt, env)
            interpret(node.step, env)
        return None

    elif cls == 'StringLiteral':
        return node.value

    elif cls == 'NumberLiteral':
        return node.value

    elif cls == 'VarRef':
        return env.get(node.name, node.name)

    # Fallback for unhandled node types
    raise ValueError(f"Unhandled node type: {cls}")

def eval_condition(cond, env):
    def resolve(v):
        val = interpret(v, env)
        return env.get(val, val) if isinstance(val, str) else val

    left = resolve(cond.left)
    right = resolve(cond.right) if hasattr(cond, 'right') else None

    ops = {
        'not':                lambda a: not a,
        'and':                lambda a, b: a and b,
        'or':                 lambda a, b: a or b,
        'lessthan':           lambda a, b: a < b,
        'greaterthan':        lambda a, b: a > b,
        'equals':             lambda a, b: a == b,
        'notequals':          lambda a, b: a != b,
        'lessthanorequal':    lambda a, b: a <= b,
        'greaterthanorequal': lambda a, b: a >= b,
    }
    return ops[cond.op](left, right)

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

nodes = parse_tree_output(raw.stdout)

print("=== Parsed tree nodes ===")
for depth, name in nodes:
    print(f"  {'  ' * depth}{name}")

program_text = nodes_to_program_text(nodes)
print("\n=== Generated program text ===")
print(program_text)

print("\n=== Running program ===")
script_dir = os.path.dirname(os.path.abspath(__file__))
mm = metamodel_from_file(os.path.join(script_dir, 'fslang.tx'))
model = mm.model_from_str(program_text)

env = {}
for stmt in model.statements:
    interpret(stmt, env)

print("\n=== Final environment ===")
for k, v in env.items():
    print(f"  {k} = {v}")
