"""Embedded interface-design guidance, by topic."""
from __future__ import annotations

_HEURISTICS = """# The ten usability heuristics

Jakob Nielsen's heuristics (1994): broad rules of thumb for judging an interface, not a
checklist to tick. Each one is a question to ask of the screen in front of you.

1. Visibility of system status. Does the interface keep the user informed about what is
   going on, through feedback in reasonable time? A request with no indicator is the most
   common breach.
2. Match between the system and the real world. Does it speak the user's language, with
   their words and concepts, rather than internal jargon? An enum value shown raw fails here.
3. User control and freedom. Is there a clearly marked way out of a wrong turn, an undo and
   a redo, without having to go through a whole dialogue?
4. Consistency and standards. Do the same words, the same icons and the same places mean the
   same thing everywhere, and does it follow the platform's conventions?
5. Error prevention. Does the design remove the conditions for the mistake, or confirm
   before a committing action, instead of only reporting the error afterwards?
6. Recognition rather than recall. Are the options visible, so nothing has to be remembered
   from one part of the interface to another?
7. Flexibility and efficiency of use. Are there accelerators for the frequent user that stay
   out of the novice's way?
8. Aesthetic and minimalist design. Does every element carry information the user needs?
   What is merely present competes with what matters.
9. Help users recognise, diagnose and recover from errors. Is the message in plain language,
   does it say what went wrong, and does it offer the way forward?
10. Help and documentation. When it is needed, is it findable, specific to the task and
    concrete about the steps?

Source: Nielsen, J. (1994), Nielsen Norman Group. Use them as a review pass over a built
screen; they describe what to look for, not a value to measure.
"""

_LAWS = """# Design heuristics from psychology

Published findings, each from its own primary source. They explain why an interface feels
fast or heavy; none of them is a number you can assert about a component.

- Fitts's law (Fitts, 1954). The time to reach a target grows with its distance and shrinks
  with its size. Make the important control bigger, or bring it nearer: a destructive action
  earns distance on purpose.
- Hick-Hyman law (Hick, 1952; Hyman, 1953). Decision time grows with the number and
  complexity of the choices. Splitting a long menu into groups beats listing everything.
- Miller's law (Miller, 1956). Working memory holds a handful of items, so chunk what the
  user has to carry: a phone number, an id, a code.
- Von Restorff effect (1933). The item that differs is the one that is remembered. One
  emphasis per view; a screen where everything shouts says nothing.
- Serial position effect (Ebbinghaus). The first and last items of a list are recalled best;
  put the weakest options in the middle.
- Peak-end rule (Kahneman). An experience is remembered by its most intense moment and its
  end, not its average. Polish the error state and the confirmation.
- Jakob's law (Nielsen). People spend most of their time on other interfaces, so they expect
  yours to work the same way. A novel pattern must earn its novelty.
- Gestalt grouping (Wertheimer, Koffka, Kohler, 1920s). Proximity, similarity, continuity
  and closure decide what reads as a group. Spacing does more grouping work than borders do.
"""

_CONTRAST = """# Contrast, as WCAG defines it

The ratio runs from 1 (identical) to 21 (black on white) and is computed from relative
luminance, not from how different two colors look.

| What | WCAG 2.2 AA | AAA |
|---|---|---|
| Body text | 4.5:1 | 7:1 |
| Large text (>=24px, or >=18.66px bold) | 3:1 | 4.5:1 |
| User interface components and graphical objects | 3:1 | - |
| Decorative elements, disabled controls, logos | exempt | exempt |

Rules that follow from the definition:
- Measure the pair the user actually sees. A translucent color is composited onto what is
  behind it first; a token measured on its own means nothing.
- A border that only decorates is exempt; a border that is the only thing identifying a
  control or its state is a user interface component and owes 3:1.
- Disabled controls are exempt, which is not a licence to make every muted token
  unreadable: placeholder text is not disabled.
- Light and dark are two different themes and both have to pass. A palette inverted by hand
  usually fails in the darker one, where soft tints sit close to their ink.
- The ratio is symmetric: swapping foreground and background does not change it.

Source: W3C, Web Content Accessibility Guidelines 2.2.
"""

_TARGETS = """# Size, spacing and reading comfort

Numbers with a published source, worth checking rather than arguing about.

- Pointer targets: WCAG 2.2 AA (2.5.8) asks for 24x24 CSS pixels, AAA (2.5.5) for 44x44.
  Material Design asks for 48dp. A small glyph can keep its size if its hit area is padded.
- Line length: 45-75 characters is the long-standing range for comfortable reading, with 66
  as the usual target; a layout with no max width breaks it on a wide screen.
- Line height: around 1.5 for body text (WCAG 1.4.12 asks that 1.5 be possible without loss
  of content), tighter as the type gets larger.
- Text must reflow to 320 CSS pixels wide without a horizontal scrollbar (WCAG 1.4.10), and
  survive 200% zoom (1.4.4).
- A type scale is a ratio, not a list of sizes somebody liked. Pick one (1.125, 1.2, 1.25,
  1.333) and let the steps fall where it says.
- Spacing lives on one grid, usually of 4 or 8. The grid matters more than the number: a
  value used once is the thing to look at.

Sources: W3C WCAG 2.2; Material Design 3 (CC BY 4.0).
"""

_TOKENS = """# Tokens and theming

- One definition per fact. A color, a radius, a spacing step and a type size each live in
  exactly one file, and every component reads from it. A hex in a screen is a second source
  of truth that nobody will update.
- Name a token for its role, never its value: `surface`, `text-muted`, `danger` age well,
  `blue-500` and `gray-dark` do not survive a theme change.
- Pair the ink with the surface in the name. A token called `on-surface` says where it
  belongs, so the contrast pair is declared instead of guessed, and a tool can check it.
- A theme is data. Adding one is a file, never a code change, the same rule i18n follows
  for a language.
- Semantic colors come in pairs: the fill and the ink that goes on it. A `danger` with no
  `on-danger` means every caller invents one.
- Light and dark are not inverses. Deriving one from the other by flipping lightness is what
  produces soft tints that fail contrast in the dark theme.
"""

_GUIDES = {
    "heuristics": _HEURISTICS,
    "laws": _LAWS,
    "contrast": _CONTRAST,
    "targets": _TARGETS,
    "tokens": _TOKENS,
}

_ALIASES = {
    "nielsen": "heuristics",
    "usability": "heuristics",
    "psychology": "laws",
    "ux": "laws",
    "wcag": "contrast",
    "color": "contrast",
    "a11y": "contrast",
    "accessibility": "contrast",
    "sizing": "targets",
    "spacing": "targets",
    "typography": "targets",
    "theme": "tokens",
    "theming": "tokens",
    "design-tokens": "tokens",
}


def guide_topics() -> list[str]:
    return list(_GUIDES)


def design_guide(topic: str = "") -> str:
    """Render the embedded guidance, all of it or one topic."""
    key = topic.strip().lower()
    if not key:
        body = "\n\n".join(_GUIDES[name] for name in _GUIDES)
        return f"Interface guide topics: {', '.join(_GUIDES)}\n\n{body}"
    if key in _GUIDES:
        return _GUIDES[key]
    if key in _ALIASES:
        return _GUIDES[_ALIASES[key]]
    return f"Unknown topic '{topic}'. Available: {', '.join(_GUIDES)}"
