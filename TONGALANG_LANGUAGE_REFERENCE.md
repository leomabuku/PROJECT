# TongaLang Language Reference

This document explains the TongaLang language features implemented in this project. It covers every keyword, native function, operator, literal type, comment style, program rule, and important behavior, with a small example for each.

TongaLang programs are normally saved with the `.tg` extension.

## 1. Basic Program Structure

Every executable TongaLang program must contain a main entry point:

```tg
mulimo matalikilo() {
    amba("Program starts here")
}
```

Explanation:

- `mulimo` declares a function.
- `matalikilo` is the required main function name.
- Execution starts inside `mulimo matalikilo()`.
- Braces `{ ... }` contain the function body.

## 2. Statement Rules

TongaLang does not use semicolons.

Correct:

```tg
mulimo matalikilo() {
    zina age = 20
    amba(age)
}
```

Incorrect:

```tg
mulimo matalikilo() {
    zina age = 20;
}
```

The incorrect example raises a bilingual lexical error because `;` is not part of TongaLang syntax.

## 3. Comments

### Line Comments: `//`

Use `//` for a one-line comment.

```tg
mulimo matalikilo() {
    // This line explains the next statement
    amba("Hello")
}
```

### Block Comments: `/* ... */`

Use `/* ... */` for a multi-line comment.

```tg
/*
   This program prints a greeting.
   Block comments can span multiple lines.
*/
mulimo matalikilo() {
    amba("Hello")
}
```

## 4. Identifiers

Identifiers are names for variables and functions.

Rules:

- Must start with a letter or underscore.
- Can contain letters, digits, and underscores.
- Are case-insensitive in the current implementation.

Example:

```tg
mulimo matalikilo() {
    zina Age = 20
    amba(age)
}
```

`Age` and `age` refer to the same variable because the lexer converts identifiers to lowercase.

## 5. Literals

### Integer Numbers

```tg
mulimo matalikilo() {
    zina count = 10
    amba(count)
}
```

### Decimal Numbers

```tg
mulimo matalikilo() {
    zina price = 12.5
    amba(price)
}
```

### Strings

Strings use double quotes.

```tg
mulimo matalikilo() {
    zina name = "TongaLang"
    amba(name)
}
```

### String Escape Sequences

Common escape sequences such as `\n`, `\t`, `\\`, and `\"` are supported.

```tg
mulimo matalikilo() {
    amba("Line one\nLine two")
    amba("He said \"Hello\"")
}
```

### String Interpolation

Strings can include variables using `$name` or `${name}`.

```tg
mulimo matalikilo() {
    zina name = "Leo"
    zina age = 20

    amba("Name: $name")
    amba("Age: ${age}")
}
```

If an interpolated variable does not exist, TongaLang raises an undefined variable error.

### Boolean Literals: `iiyi` and `pepe`

`iiyi` means true.

```tg
mulimo matalikilo() {
    zina active = iiyi
    amba(active)
}
```

`pepe` means false.

```tg
mulimo matalikilo() {
    zina active = pepe
    amba(active)
}
```

Current note: boolean output uses Python-style `True` and `False` because the interpreter converts output using `str(value)`.

## 6. Variables

### `zina` - Declare a Variable

Use `zina` to create a new variable.

```tg
mulimo matalikilo() {
    zina name = "Leo"
    zina age = 20
    zina isStudent = iiyi

    amba(name)
    amba(age)
    amba(isStudent)
}
```

Explanation:

- `zina name = "Leo"` creates a variable called `name`.
- A variable cannot be declared twice in the same scope.

### Assignment - Change an Existing Variable

After a variable has been declared, assign a new value without `zina`.

```tg
mulimo matalikilo() {
    zina age = 20
    age = age + 1
    amba(age)
}
```

Explanation:

- `age = age + 1` updates the existing variable.
- Assigning to a variable that has not been declared raises an undefined variable error.

### Global Variables

Variables declared outside `matalikilo()` are global.

```tg
zina appName = "TongaLang"

mulimo matalikilo() {
    amba(appName)
}
```

Explanation:

- `appName` is declared globally.
- `matalikilo()` can read it because the main environment has access to the global environment.

### Local Variables

Variables declared inside a function or block are local to that scope.

```tg
mulimo matalikilo() {
    zina message = "Inside main"
    amba(message)
}
```

### Loop-Local Variables

Variables declared inside loop bodies are local to that loop iteration.

```tg
mulimo matalikilo() {
    induluka i kuzwa 1 kusika 3 {
        zina doubled = i * 2
        amba(doubled)
    }
}
```

## 7. Output

### `amba` - Print Output

Use `amba(expression)` to print a value.

```tg
mulimo matalikilo() {
    amba("Hello TongaLang")
}
```

Print a variable:

```tg
mulimo matalikilo() {
    zina name = "Leo"
    amba(name)
}
```

Print a calculated expression:

```tg
mulimo matalikilo() {
    amba(10 + 20)
}
```

### `amba()` - Print a Blank Line

```tg
mulimo matalikilo() {
    amba("Before blank line")
    amba()
    amba("After blank line")
}
```

## 8. Input

### `bala()` - Read Input

Use `bala()` to read input from the user.

```tg
mulimo matalikilo() {
    zina name = bala()
    amba("Hello " + name)
}
```

### `bala("prompt")` - Read Input With a Prompt

```tg
mulimo matalikilo() {
    zina name = bala("Enter your name: ")
    amba("Hello " + name)
}
```

Explanation:

- In the command-line runner, `bala()` uses normal terminal input.
- In the GUI, execution pauses until the user submits input.
- Numeric input is converted automatically when possible.

Example of numeric input:

```tg
mulimo matalikilo() {
    zina age = bala("Enter age: ")
    amba(age + 1)
}
```

If the user enters `20`, TongaLang stores it as number `20`, so `age + 1` prints `21`.

Implementation note:

- `bala()` is implemented as a call expression.
- The project contains an `InputStmt` AST class, but that statement form is not currently used by the parser or interpreter.

## 9. Arithmetic Operators

### `+` - Addition or String Concatenation

Number addition:

```tg
mulimo matalikilo() {
    amba(10 + 5)
}
```

String concatenation:

```tg
mulimo matalikilo() {
    amba("Hello " + "TongaLang")
}
```

Mixed string and number:

```tg
mulimo matalikilo() {
    zina age = 20
    amba("Age: " + age)
}
```

Explanation:

- If both values are numbers, `+` performs addition.
- If either value is text, TongaLang converts both to text and joins them.

### `-` - Subtraction

```tg
mulimo matalikilo() {
    amba(10 - 3)
}
```

### `*` - Multiplication

```tg
mulimo matalikilo() {
    amba(4 * 5)
}
```

### `/` - Division

```tg
mulimo matalikilo() {
    amba(20 / 4)
}
```

Division by zero raises a runtime error.

### `%` - Modulo / Remainder

```tg
mulimo matalikilo() {
    amba(10 % 3)
}
```

This prints the remainder after division.

### Unary `-` - Negative Number

```tg
mulimo matalikilo() {
    zina x = -10
    amba(x)
}
```

Unary minus only works on numbers.

## 10. Comparison Operators

Comparison operators produce boolean values.

### `inda` or `>` - Greater Than

```tg
mulimo matalikilo() {
    kuti (10 inda 5) {
        amba("10 is greater than 5")
    }
}
```

Symbol version:

```tg
mulimo matalikilo() {
    kuti (10 > 5) {
        amba("10 is greater than 5")
    }
}
```

### `ceya` or `<` - Less Than

```tg
mulimo matalikilo() {
    kuti (3 ceya 8) {
        amba("3 is less than 8")
    }
}
```

Symbol version:

```tg
mulimo matalikilo() {
    kuti (3 < 8) {
        amba("3 is less than 8")
    }
}
```

### `eelana` or `==` - Equal To

```tg
mulimo matalikilo() {
    kuti (5 eelana 5) {
        amba("Equal")
    }
}
```

Symbol version:

```tg
mulimo matalikilo() {
    kuti (5 == 5) {
        amba("Equal")
    }
}
```

### `>=` - Greater Than or Equal To

```tg
mulimo matalikilo() {
    kuti (70 >= 50) {
        amba("Pass")
    }
}
```

There is currently no Tonga word equivalent for `>=`.

### `<=` - Less Than or Equal To

```tg
mulimo matalikilo() {
    kuti (40 <= 50) {
        amba("Within limit")
    }
}
```

There is currently no Tonga word equivalent for `<=`.

### `!=` - Not Equal To

```tg
mulimo matalikilo() {
    kuti (5 != 3) {
        amba("Not equal")
    }
}
```

There is currently no Tonga word equivalent for `!=`.

## 11. Logical Operators

Logical operators use truthy/falsy values.

Current truthiness:

- `pepe` is false.
- `0` is false.
- Empty string `""` is false.
- Other values are true.

### `aa` or `&&` - Logical AND

```tg
mulimo matalikilo() {
    zina paid = iiyi
    zina registered = iiyi

    kuti (paid aa registered) {
        amba("Allowed")
    }
}
```

Symbol version:

```tg
mulimo matalikilo() {
    kuti (iiyi && iiyi) {
        amba("Both are true")
    }
}
```

### `naa` or `||` - Logical OR

```tg
mulimo matalikilo() {
    zina paid = pepe
    zina hasPass = iiyi

    kuti (paid naa hasPass) {
        amba("Allowed by at least one condition")
    }
}
```

Symbol version:

```tg
mulimo matalikilo() {
    kuti (pepe || iiyi) {
        amba("At least one is true")
    }
}
```

### `tee` or `!` - Logical NOT

```tg
mulimo matalikilo() {
    zina blocked = pepe

    kuti (tee blocked) {
        amba("Not blocked")
    }
}
```

Symbol version:

```tg
mulimo matalikilo() {
    kuti (!pepe) {
        amba("Not false is true")
    }
}
```

## 12. Grouping and Separators

### Parentheses: `(` and `)`

Parentheses are used for:

- Function calls.
- Conditions.
- Grouped expressions.

Function call:

```tg
mulimo matalikilo() {
    amba("Hello")
}
```

Condition:

```tg
mulimo matalikilo() {
    kuti (10 inda 5) {
        amba("Yes")
    }
}
```

Grouped expression:

```tg
mulimo matalikilo() {
    amba((10 + 5) * 2)
}
```

### Braces: `{` and `}`

Braces define blocks.

```tg
mulimo matalikilo() {
    kuti (iiyi) {
        amba("Inside a block")
    }
}
```

### Comma: `,`

Commas separate function parameters and arguments.

```tg
mulimo add(a, b) {
    pilula a + b
}

mulimo matalikilo() {
    amba(add(10, 20))
}
```

## 13. Conditionals

### `kuti` - If

```tg
mulimo matalikilo() {
    zina age = 20

    kuti (age inda 18) {
        amba("Adult")
    }
}
```

### `naaba` - Else If

```tg
mulimo matalikilo() {
    zina mark = 60

    kuti (mark >= 70) {
        amba("Distinction")
    } naaba (mark >= 50) {
        amba("Pass")
    }
}
```

### `nakunyina` - Else

```tg
mulimo matalikilo() {
    zina mark = 40

    kuti (mark >= 50) {
        amba("Pass")
    } nakunyina {
        amba("Repeat")
    }
}
```

### Full Conditional Chain

```tg
mulimo matalikilo() {
    zina age = 18

    kuti (age inda 18) {
        amba("Older than 18")
    } naaba (age eelana 18) {
        amba("Exactly 18")
    } nakunyina {
        amba("Younger than 18")
    }
}
```

## 14. Loops

### `kufumbwa` - While Loop

`kufumbwa` repeats while the condition is true.

```tg
mulimo matalikilo() {
    zina x = 0

    kufumbwa (x ceya 3) {
        amba(x)
        x = x + 1
    }
}
```

Explanation:

- The condition is checked before each iteration.
- A loop safety limit prevents accidental infinite loops.

### `induluka`, `kuzwa`, `kusika` - Inclusive Range Loop

`induluka` creates a range loop.

```tg
mulimo matalikilo() {
    induluka i kuzwa 1 kusika 5 {
        amba(i)
    }
}
```

Explanation:

- `i` is the loop variable.
- `kuzwa` introduces the start value.
- `kusika` introduces the end value.
- The range is inclusive, so this prints `1` through `5`.

### Descending `induluka` Range

```tg
mulimo matalikilo() {
    induluka i kuzwa 5 kusika 1 {
        amba(i)
    }
}
```

Explanation:

- Descending ranges work automatically.
- There is no custom step syntax yet.

### `cita` and `kusikila` - Do-Until Loop

`cita ... kusikila` runs the body first, then stops when the condition becomes true.

```tg
mulimo matalikilo() {
    zina x = 0

    cita {
        amba(x)
        x = x + 1
    } kusikila (x eelana 3)
}
```

Explanation:

- The body runs at least once.
- After each run, the condition is checked.
- When the condition is true, the loop stops.

### `leka` - Break Out of a Loop

```tg
mulimo matalikilo() {
    induluka i kuzwa 1 kusika 10 {
        amba(i)

        kuti (i eelana 3) {
            leka
        }
    }
}
```

Explanation:

- `leka` exits the nearest active loop.
- Using `leka` outside a loop raises an error.

## 15. Functions

### `mulimo` - Declare a Function

```tg
mulimo greet() {
    amba("Hello")
}

mulimo matalikilo() {
    greet()
}
```

Explanation:

- `mulimo greet()` defines a function named `greet`.
- `greet()` calls the function.

### Function Parameters

```tg
mulimo greet(name) {
    amba("Hello " + name)
}

mulimo matalikilo() {
    greet("Leo")
}
```

### Multiple Parameters

```tg
mulimo add(a, b) {
    pilula a + b
}

mulimo matalikilo() {
    amba(add(10, 20))
}
```

### Functions Can Be Called Before Declaration

```tg
mulimo matalikilo() {
    amba(add(7, 8))
}

mulimo add(a, b) {
    pilula a + b
}
```

Explanation:

- The interpreter collects function declarations before running `matalikilo()`.

### `matalikilo` - Main Entry Point

```tg
mulimo matalikilo() {
    amba("This is the starting point")
}
```

Rules:

- `matalikilo` is required.
- `matalikilo` must not have parameters.
- Returning from `matalikilo` is allowed, but the returned value is ignored.

### `pilula` - Return From a Function

```tg
mulimo square(x) {
    pilula x * x
}

mulimo matalikilo() {
    amba(square(5))
}
```

Return without a value:

```tg
mulimo stopEarly() {
    amba("Before return")
    pilula
    amba("This will not run")
}

mulimo matalikilo() {
    stopEarly()
}
```

Explanation:

- `pilula` exits the current function.
- `pilula expression` returns a value.
- `pilula` outside a function is an error.

## 16. Native Functions

Native functions are built into TongaLang in `tongalang/native_functions.py`.

### `mpati(a, b)` - Maximum Value

Returns the bigger value.

```tg
mulimo matalikilo() {
    amba(mpati(10, 20))
}
```

Output:

```text
20
```

### `inini(a, b)` - Minimum Value

Returns the smaller value.

```tg
mulimo matalikilo() {
    amba(inini(10, 20))
}
```

Output:

```text
10
```

### `ngamabala(x)` - Is Text/String

Returns true if the value is text.

```tg
mulimo matalikilo() {
    amba(ngamabala("Leo"))
    amba(ngamabala(20))
}
```

Current output:

```text
True
False
```

### `ninamba(x)` - Is Number

Returns true if the value is a number.

```tg
mulimo matalikilo() {
    amba(ninamba(20))
    amba(ninamba("20"))
}
```

Current output:

```text
True
False
```

Note:

- Booleans are not treated as numbers, even though Python internally treats `bool` as a subclass of `int`.

### `namba(x)` - Convert to Number

Converts text to a number if possible.

```tg
mulimo matalikilo() {
    zina x = namba("20")
    amba(x + 5)
}
```

Output:

```text
25
```

Decimal conversion:

```tg
mulimo matalikilo() {
    zina price = namba("12.5")
    amba(price + 2)
}
```

If conversion is impossible, TongaLang raises a conversion error.

### `mabala(x)` - Convert to Text

Converts a value to text.

```tg
mulimo matalikilo() {
    zina text = mabala(100)
    amba(text + " years")
}
```

Output:

```text
100 years
```

## 17. Expression Statements

A function call can be used as a statement when its return value is not needed.

```tg
mulimo greet() {
    amba("Hello")
}

mulimo matalikilo() {
    greet()
}
```

Explanation:

- `greet()` is parsed as an expression statement.
- It is executed for its side effect.

## 18. Operator Precedence

TongaLang uses precedence rules so expressions are evaluated in the expected order.

From lower to higher precedence:

1. `naa`, `||`
2. `aa`, `&&`
3. `eelana`, `==`, `!=`
4. `inda`, `>`, `>=`, `ceya`, `<`, `<=`
5. `+`, `-`
6. `*`, `/`, `%`
7. `tee`, `!`
8. unary `-`

Example:

```tg
mulimo matalikilo() {
    amba(2 + 3 * 4)
    amba((2 + 3) * 4)
}
```

Expected output:

```text
14
20
```

## 19. Error Behaviors

TongaLang errors are bilingual where possible. They may include:

- Line number.
- Column number.
- Tonga message.
- English message.
- Tonga hint.
- English hint.

### Undefined Variable

```tg
mulimo matalikilo() {
    amba(name)
}
```

This raises an undefined variable error because `name` was not declared.

### Duplicate Variable in Same Scope

```tg
mulimo matalikilo() {
    zina age = 20
    zina age = 21
}
```

This raises a variable-already-declared error.

### Division by Zero

```tg
mulimo matalikilo() {
    amba(10 / 0)
}
```

This raises a division-by-zero error.

### Wrong Number of Function Arguments

```tg
mulimo add(a, b) {
    pilula a + b
}

mulimo matalikilo() {
    amba(add(10))
}
```

This raises a wrong-argument-count error.

### Missing Main Function

```tg
amba("Hello")
```

This raises a missing main entry point error because `mulimo matalikilo()` is required.

### Break Outside Loop

```tg
mulimo matalikilo() {
    leka
}
```

This raises an error because `leka` can only be used inside a loop.

### Return Outside Function

```tg
pilula 10

mulimo matalikilo() {
    amba("Hello")
}
```

This raises an error because `pilula` is only valid inside a function body.

### Loop Limit Exceeded

```tg
mulimo matalikilo() {
    kufumbwa (iiyi) {
        amba("looping")
    }
}
```

This eventually raises a loop-limit error. The interpreter has a maximum iteration limit to prevent accidental infinite loops.

## 20. GUI-Supported Language Behaviors

The GUI does not define a separate language. It uses the same backend parser and interpreter.

### Syntax Highlighting

The GUI highlights:

- Keywords.
- Booleans.
- Strings.
- Comments.
- Numbers.
- Native functions.
- Operators.
- Function names.
- Identifiers.
- Braces.

Example to see many categories:

```tg
// GUI highlighting demo
mulimo matalikilo() {
    zina name = "Leo"
    zina age = 20

    kuti (age inda 18 aa name eelana "Leo") {
        amba("Hello " + name)
    }
}
```

### AST Visualization

Any valid program can be shown in the AST panel.

Example:

```tg
mulimo matalikilo() {
    zina x = 1
    amba(x + 2)
}
```

The GUI parses this into nodes such as:

- `Program`
- `FunctionDecl`
- `Block`
- `VarDecl`
- `OutputStmt`
- `Binary`
- `Variable`
- `Literal`

### GUI Input Pause/Resume

```tg
mulimo matalikilo() {
    zina name = bala("Enter your name: ")
    amba("Hello " + name)
}
```

In the GUI:

1. Execution reaches `bala()`.
2. The program waits for input.
3. The user types a value and presses Submit.
4. The interpreter resumes.

## 21. Features Not Included Yet

These are not currently implemented in the language:

- Semicolons.
- Arrays or lists.
- Dictionaries/maps.
- Classes or objects.
- Imports/modules inside `.tg` files.
- File input/output from TongaLang programs.
- Custom step values for `induluka`.
- Column-level GUI error highlighting.
- A step-by-step debugger.
- A graphical node-link AST.
- A GUI sample picker.
- Persistent GUI settings.

## 22. Complete Keyword Summary

| Keyword | Category | Meaning | Minimal example |
| --- | --- | --- | --- |
| `zina` | Variable | Declare variable | `zina x = 10` |
| `iiyi` | Boolean | True | `zina ok = iiyi` |
| `pepe` | Boolean | False | `zina ok = pepe` |
| `amba` | Output | Print value | `amba("Hi")` |
| `bala` | Input | Read input | `zina x = bala()` |
| `kuti` | Conditional | If | `kuti (x inda 5) { amba(x) }` |
| `naaba` | Conditional | Else-if | `naaba (x eelana 5) { amba(x) }` |
| `nakunyina` | Conditional | Else | `nakunyina { amba("No") }` |
| `aa` | Logic | AND | `iiyi aa iiyi` |
| `naa` | Logic | OR | `iiyi naa pepe` |
| `tee` | Logic | NOT | `tee pepe` |
| `inda` | Comparison | Greater than | `x inda 5` |
| `ceya` | Comparison | Less than | `x ceya 5` |
| `eelana` | Comparison | Equal to | `x eelana 5` |
| `kufumbwa` | Loop | While | `kufumbwa (x ceya 5) { ... }` |
| `induluka` | Loop | Range loop | `induluka i kuzwa 1 kusika 5 { ... }` |
| `kuzwa` | Loop | Range start | `kuzwa 1` |
| `kusika` | Loop | Range end | `kusika 5` |
| `cita` | Loop | Do body | `cita { ... } kusikila (...)` |
| `kusikila` | Loop | Until condition | `kusikila (x eelana 5)` |
| `leka` | Loop | Break | `leka` |
| `mulimo` | Function | Declare function | `mulimo add(a, b) { ... }` |
| `matalikilo` | Function | Main entry point | `mulimo matalikilo() { ... }` |
| `pilula` | Function | Return | `pilula x + y` |

## 23. Complete Native Function Summary

| Function | Arguments | Meaning | Minimal example |
| --- | --- | --- | --- |
| `mpati` | 2 | Maximum | `mpati(10, 20)` |
| `inini` | 2 | Minimum | `inini(10, 20)` |
| `ngamabala` | 1 | Is text/string | `ngamabala("Leo")` |
| `ninamba` | 1 | Is number | `ninamba(20)` |
| `namba` | 1 | Convert to number | `namba("20")` |
| `mabala` | 1 | Convert to text | `mabala(20)` |

## 24. Complete Operator Summary

| Operator | Meaning | Minimal example |
| --- | --- | --- |
| `+` | Add or concatenate | `10 + 5`, `"Age: " + age` |
| `-` | Subtract | `10 - 5` |
| `*` | Multiply | `10 * 5` |
| `/` | Divide | `10 / 5` |
| `%` | Remainder | `10 % 3` |
| `=` | Assignment | `age = 21` |
| `>` | Greater than | `age > 18` |
| `inda` | Greater than | `age inda 18` |
| `<` | Less than | `age < 18` |
| `ceya` | Less than | `age ceya 18` |
| `>=` | Greater/equal | `mark >= 50` |
| `<=` | Less/equal | `mark <= 100` |
| `==` | Equal | `age == 18` |
| `eelana` | Equal | `age eelana 18` |
| `!=` | Not equal | `age != 18` |
| `&&` | AND | `a && b` |
| `aa` | AND | `a aa b` |
| `||` | OR | `a || b` |
| `naa` | OR | `a naa b` |
| `!` | NOT | `!a` |
| `tee` | NOT | `tee a` |
| unary `-` | Negative value | `-10` |

## 25. Complete Grouping Symbol Summary

| Symbol | Meaning | Example |
| --- | --- | --- |
| `(` | Start condition/call/group | `amba("Hi")` |
| `)` | End condition/call/group | `kuti (x inda 1)` |
| `{` | Start block | `mulimo matalikilo() {` |
| `}` | End block | `}` |
| `,` | Separate parameters/arguments | `add(10, 20)` |

