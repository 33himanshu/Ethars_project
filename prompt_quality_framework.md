## HOW TO WRITE HIGH-QUALITY CODING PROMPTS
(Focused on Code Generation Prompts Only)

This framework evaluates the quality of the prompt itself, not the model's output.

---

### 1️⃣ Clarity

**Definition:**
How clearly the prompt describes what code should be written.

**The Prompt Must:**
- Clearly state the task (e.g., "Write a Python function that…")
- Specify input type and format
- Specify expected output format
- Avoid ambiguous words (e.g., "efficient", "proper", "optimized" without definition)

**Good Example:**
Write a Python function `find_second_largest(nums: List[int]) -> int` that returns the second largest unique integer. If fewer than two unique integers exist, return -1.

✔ Clear task  
✔ Clear input  
✔ Clear output  
✔ Defined edge case

---

### 2️⃣ Completeness

**Definition:**
Does the prompt provide all information needed to write the solution?

**The Prompt Must Include:**
- Function signature (if required)
- Constraints (e.g., input size, value range)
- Edge cases
- Environment/version if relevant (e.g., Python 3.9+)

**Weak Prompt:**
Write a function to sort numbers.

Missing:
- Input type
- Output format
- Constraints
- Sorting rule

---

### 3️⃣ Content Adherence

**Definition:**
Does the prompt focus strictly on the intended concept or algorithm?

**The Prompt Should:**
- Specify required approach if necessary (e.g., "Use recursion.")
- Restrict disallowed shortcuts (e.g., "Do not use built-in sort.")
- Avoid adding unrelated requirements

**Bad Example:**
Write a function to reverse a string and also explain how databases work.  
❌ Scope confusion

---

### 4️⃣ Efficiency

**Definition:**
Does the prompt define efficiency expectations clearly (if needed)?

**The Prompt Should:**
- Specify time complexity if important (e.g., O(n))
- Specify space limits if relevant
- Avoid vague demands like "make it very fast"

**Good Example:**
The solution must run in O(n) time and use O(1) additional space.  
✔ Specific  
✔ Measurable

---

### 5️⃣ Repeativeness (Text Quality – No Redundant Wording)

**Definition:**
Does the prompt avoid unnecessary repetition, duplicated instructions, or redundant wording? This refers to the clarity of the prompt text itself.

**The Prompt Should:**
- Avoid repeating the same requirement in multiple sentences
- Avoid rephrasing the same constraint unnecessarily
- Avoid circular restatements

**Bad Example:**
Write a function to calculate factorial. The function should calculate the factorial of a number. It must compute factorials properly.  
❌ Repeated wording  
❌ Redundant phrasing

**Good Example:**
Write a function that returns the factorial of a non-negative integer using recursion.  
✔ Concise  
✔ No repetition

---

### 6️⃣ Human Likeness (Natural, Professional Prompt Writing)

**Definition:**
Is the prompt written in a natural, structured, professional way like a real human engineer would write?

⚠ This refers to the prompt text, not the generated code.

**The Prompt Should:**
- Use clear, natural language
- Avoid robotic or template-like repetition
- Use logical structure (Context → Task → Constraints → Output)
- Avoid unnatural phrasing

**Robotic Example:**
Write code. Code should be efficient. Code should be correct. Code should be structured.  
❌ Mechanical  
❌ Poor flow

**Human-like Example:**
Develop a Python function that validates whether a given string is a palindrome. The function should ignore spaces and case sensitivity.  
✔ Natural tone  
✔ Professional phrasing  
✔ Structured

---

### 7️⃣ Accuracy

**Definition:**
Is the prompt logically correct and free from contradictions?

**The Prompt Must:**
- Have no conflicting instructions
- Ensure examples match requirements
- Avoid impossible constraints

**Contradiction Example:**
Write a recursive solution but do not use recursion.  
❌ Logically inconsistent
