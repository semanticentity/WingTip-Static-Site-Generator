# Math Examples

WingTip supports LaTeX math rendering using KaTeX. You can write both inline and display math expressions.

## Inline Math

Use `\(...\)` for inline math. For example:

The area of a circle is \(A = \pi r^2\) and its circumference is \(C = 2\pi r\).

The quadratic formula is \(x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}\).

## Display Math

Use `\[...\]` for display math. For example:

The Pythagorean theorem:

\[a^2 + b^2 = c^2\]

Maxwell's equations in differential form:

\[ \begin{aligned} \nabla \cdot \mathbf{E} &= \frac{\rho}{\varepsilon_0} \\ \nabla \cdot \mathbf{B} &= 0 \\ \nabla \times \mathbf{E} &= -\frac{\partial \mathbf{B}}{\partial t} \\ \nabla \times \mathbf{B} &= \mu_0\left(\mathbf{J} + \varepsilon_0\frac{\partial \mathbf{E}}{\partial t}\right) \end{aligned} \]

## Matrix Examples

A 2x2 matrix:

\[ \begin{pmatrix} a & b \\ c & d \end{pmatrix} \]

## Chemical Equations

Chemical equations can be written using math mode:

\[\ce{CO2 + H2O \rightleftharpoons H2CO3}\]

## Accessibility

Math expressions are rendered with proper semantic markup for screen readers. When using a screen reader:

1. Inline math is announced naturally within the text flow
2. Display math is treated as a distinct block with appropriate ARIA labels
3. Complex expressions are broken down into meaningful parts

## Dark Mode Support

Math expressions automatically adapt to dark mode when the theme is switched, maintaining readability and consistent styling with the rest of the content.
