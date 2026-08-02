# TongaLang UI Audit and Improvements

Audit date: 21 July 2026

Evidence: the seven supplied screenshots, the running Tkinter application, and the implemented source.

## Journey review

1. **Open the editor — Healthy.** The primary action and learner source are immediately visible. The dark editor has clear syntax colour and line numbers.
2. **Run a program — Healthy.** Run is visually dominant, execution moves off the UI thread, and Stop now cancels running or input-waiting work cooperatively.
3. **Provide input — Healthy.** The dedicated Input / I/O view explains the wait state and returns entered data without losing previous output.
4. **Read results — Healthy with a minor opportunity.** Output and internal console are separated, reducing confusion. A future revision could add a compact “copy result” action.
5. **Inspect the AST — Healthy after redesign.** The old view repeated the same hierarchy as an outline and raw text. The new view uses a parent-child node-link diagram, readable zoom, pan, fit, search, colour-coded roles, source excerpts, and go-to-source navigation. The outline remains as an accessible alternative.
6. **Correct an error — Healthy after redesign.** Diagnostics now have stable codes, bilingual/Tonga modes, exact line and column, source excerpts, a caret, and actionable hints. Misspelled entry points and keywords receive suggestions.
7. **Change settings — Usable with a future layout opportunity.** Safety limits are exposed, including loop iterations and call depth. Colour choices remain a long vertical form; grouping them into collapsible cards would reduce scanning effort.

## Strengths

- Consistent navigation, restrained colour palette, and large page titles.
- Clear separation of editor, learner output, input, diagnostics, AST, and internal console.
- Direct safety controls for runaway loops, recursion, and cancellation.
- AST diagram and outline serve visual and keyboard-oriented users without duplicating the inspector logic.
- The Test Lab exposes pass/fail status, timing, coverage, category counts, and test-level details.

## Remaining risks and recommendations

- Runtime keyboard and screen-reader testing is still needed with NVDA or Narrator; Tkinter exposes limited accessible names for some custom controls.
- Add visible focus styling and verify every workflow without a mouse.
- Group Settings into “Appearance”, “Execution safety”, and “Syntax colours” sections.
- Add a resizable divider between the AST diagram and inspector and remember its last position.
- Add a small legend for AST colours and optional collapse/expand on diagram nodes.
- Validate Chitonga learner copy with a teacher or fluent speaker before classroom deployment.

## Screenshot index

- `01`–`07`: supplied baseline journey screenshots.
- `08-polished-ast.png`: implemented node-link AST with source inspector.
- `09-test-lab.png`: automated failure-discovery dashboard.

