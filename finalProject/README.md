cat > /mnt/user-data/outputs/README.md << 'EOF'
# tree 🌲

> A programming language where your **folder structure is the source code**.

tree is an esoteric programming language built on a simple idea: instead of writing text files, you arrange folders and files in your filesystem. The `tree` command becomes your parser input, folder names are statements, and file names are values.

---

## How It Works

tree programs are directories saved with the `.tree` extension. The interpreter runs `tree /F` on the folder, strips the tree-drawing characters, reads the nesting depth to determine scope, and executes the result.

Every construct follows this pattern:
- **Folders** = statements and operations (e.g. `1.for\`, `2.if\`, `3.assign\`)
- **Files** = values and variables (e.g. `1.i`, `2.100`, `3.'hello'`)
- **Numbers** = execution order within a scope (`1.` runs before `2.`)

So a program that counts from 1 to 10 looks like this on disk:

```
Countdown.tree\
├── 1.for
│   ├── 1.assign
│   │   ├── C 1.i
│   │   └── ≡ 2.1
│   ├── 2.lessthanorequal
│   │   ├── C 1.i
│   │   └── ≡ 2.10
│   ├── 3.assign
│   │   ├── C 1.i
│   │   └── 2.add
│   │       ├── C 1.i
│   │       └── ≡ 2.1
│   └── 4.do
│       └── 1.print
│           └── C 1.i
```

---

## Installation

**Requirements:** Python 3.8+, pip

```bash
git clone https://github.com/is9belle/tree
cd tree
pip install textx
```

---

## Usage

```bash
py tree.py Countdown.tree
```

Point the interpreter at any `.tree` folder. It will print the parsed tree structure, the generated intermediate text, and the program output.

---

## Language Reference

### Statements

| Construct | Folder Name | Children |
|-----------|-------------|----------|
| Assign | `assign` | `1.varname`, `2.value` |
| For loop | `for` | `1.assign`, `2.condition`, `3.assign`, `4.do` |
| If / elif / else | `if` | `1.condition`, `2.do`, `[3.elif]`, `[4.else]` |
| Print | `print` | `1.value` |

### Expressions (usable as values)

| Operation | Folder Name | Children |
|-----------|-------------|----------|
| Add / concat | `add` | `1.left`, `2.right` |
| Subtract | `sub` | `1.left`, `2.right` |
| Multiply | `mul` | `1.left`, `2.right` |
| Divide | `div` | `1.left`, `2.right` |
| Modulo | `mod` | `1.left`, `2.right` |

### Conditions

| Condition | Folder Name |
|-----------|-------------|
| Equal | `equals` |
| Not equal | `notequals` |
| Less than | `lessthan` |
| Greater than | `greaterthan` |
| Less than or equal | `lessthanorequal` |
| Greater than or equal | `greaterthanorequal` |

### Values

| Type | Example filename | Notes |
|------|-----------------|-------|
| Variable | `1.i` | Any letter or word |
| Number | `2.42` | Integer or decimal |
| String | `3.'hello'` | Wrapped in single quotes |

---

## Programs

| File | Description |
|------|-------------|
| `Countdown.tree` | Counts down from 10 to 1 |
| `EvenOddCheck.tree` | Prints whether each number 1–10 is even or odd |
| `FizzBuzz.tree` | Classic FizzBuzz from 1 to 100 |
| `MultTable.tree` | Prints a 10×10 multiplication table |
| `SimpleInput.tree` | Demonstrates basic assignment and printing |
| `SumNums.tree` | Sums numbers 1 to 100 and prints the result |
| `Concat.tree` | Demonstrates string concatenation using `add` |

---

## Example: FizzBuzz

```
FizzBuzz.tree\
└── 1.for
    ├── 1.assign → i = 1
    ├── 2.lessthanorequal → i <= 100
    ├── 3.assign → i = add(i, 1)
    └── 4.do
        └── 1.if
            ├── 1.equals(0, mod(i, 15)) → 2.do → print('FizzBuzz')
            ├── 3.elif equals(0, mod(i, 3)) → 4.do → print('Fizz')
            ├── 5.elif equals(0, mod(i, 5)) → 6.do → print('Buzz')
            └── 7.else → print(i)
```

---

## Project Structure

```
tree/
├── Concat.tree/
├── Countdown.tree/
├── EvenOddCheck.tree/
├── FizzBuzz.tree/
├── MultTable.tree/
├── SimpleInput.tree/
├── SumNums.tree/
├── tests/
├── fslang.tx          # TextX grammar
├── tree.py            # Interpreter
├── index.html         # GitHub Pages website
└── README.md
```

---

## Implementation Notes

The interpreter works in four stages:

1. **Run `tree /F`** on the target `.tree` directory
2. **Strip tree-drawing characters** (`├──`, `└──`, `│`) and calculate nesting depth from prefix length
3. **Sort siblings** by numeric prefix so execution order is always deterministic regardless of how the OS orders files vs folders
4. **Convert to bracketed text** — e.g. `for(assign(i, 1), lessthan(i, 100), ...)`
5. **Parse with TextX** using `fslang.tx`, then walk the AST and execute

---

## Built With

- [Python 3](https://python.org)
- [TextX](https://textx.github.io/textX/) — grammar and parser generation

---

*tree — because why write code when you can just make folders?*
EOF