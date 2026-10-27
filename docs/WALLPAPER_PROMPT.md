# Wallpaper Prompt + Design Spec

The reveal image in `assets/ehax-wallpaper.png` was generated locally with
Pillow (no AI, no external assets). Regenerate it any time:

```bash
python3 assets/make_wallpaper.py
```

Outputs:

- `assets/ehax-wallpaper.png` — 1920×1080, ~1.3 MB
- `assets/ehax-wallpaper.jpg` — 1920×1080, ~250 KB

Use the PNG for local network speed is fine; use the JPG if you need a smaller
file. Both are 16:9 and scale to 1366×768, 1920×1080, 2560×1440, etc.

---

## If you want an AI-generated version

AI image tools still garble text. Best results: generate a **text-free
background**, then add the words in Canva/Figma/Photopea. If you must generate
text in-image, use a model with strong typography (Ideogram, GPT-image, etc.)
and expect to fix it.

### Main prompt (background only, recommended)

```text
A cinematic cybersecurity event wallpaper, 16:9, 1920x1080, dark near-black
navy background (#04080E), subtle perspective grid and faint scanlines, a soft
neon mint-green (#39FF88) radial glow on the right and a cool cyan glow on the
left. On the right, a sleek dark terminal window with a thin green border and
tiny red/yellow/green window dots, filled with abstract green code lines (no
readable words). Behind it, a faint geometric shield outline. Bottom right:
three small isometric voxel cubes with glowing green wireframe edges, a subtle
nod to Minecraft without using any Minecraft logo or character. Large empty
space on the left for a headline. High contrast, clean, professional poster
design, projector-friendly, no clutter, no text, no letters, no logos, no
watermarks, no people, 35mm, crisp edges, subtle film grain.
```

### Negative prompt

```text
text, letters, words, typography, captions, watermark, signature, logo,
Minecraft logo, Creeper, Mojang, cartoon, anime, face, person, hoodie hacker,
green Matrix rain cliché, busy background, low contrast, blurry, distorted,
extra limbs, UI mockup with readable text, fake gibberish letters, neon
overload, rainbow colors
```

### Text-safe variant (for Canva/Figma overlay)

Generate the same background with even more empty space:

```text
... same as above, but keep the entire left two-thirds almost empty and dark,
with only the terminal card and shield on the right. No text anywhere. Leave
generous safe margins for a large headline.
```

Then overlay:

```text
Kicker:  EHAX  //  DTU CYBERSECURITY SOCIETY
Eyebrow: OPEN HOUSE  /  LOG4SHELL DEMO

Headline (3 lines, very large):
YOU'VE
BEEN
HACKED.

Subhead (mint green):
ETHICALLY.

Supporting line:
ONE CHAT MESSAGE. ONE OLD LIBRARY. ZERO PASSWORDS.

Footer:
CVE-2021-44228  /  PATCH. UPDATE. REPEAT.
EHAX // DTU  •  OPEN AIR THEATRE
```

### If the generator supports text (Ideogram-style prompt)

```text
1920x1080 cybersecurity poster wallpaper. Dark navy background with a subtle
green grid. Huge bold white sans-serif headline on the left, exactly:
"YOU'VE BEEN HACKED." with the final word in neon mint green. Below it in
smaller mint monospace: "ETHICALLY." Top-left small label: "EHAX // DTU
CYBERSECURITY SOCIETY". Right side: a dark terminal window with green code
lines and a thin green border; behind it a faint shield outline; bottom right
three small isometric voxel cubes. Footer: "CVE-2021-44228 / PATCH. UPDATE.
REPEAT." and "EHAX // DTU • OPEN AIR THEATRE". High contrast, clean, readable
from 3 metres, no extra text, no misspellings, no watermark, no logo errors.
```

**Always proofread AI text.** One misspelled “HACKED” ruins the reveal. Our
local asset is safer.

---

## Design spec (for a human designer)

### Canvas

- 1920×1080 px, 16:9, PNG or high-quality JPG.
- Safe area: keep all critical text within the central 80% (154–1766 px
  horizontally, 86–994 px vertically).
- Test on the actual victim laptop at max brightness, outdoors/shade. If it
  disappears in daylight, increase contrast; don't add more detail.

### Palette

| Role | Hex |
|---|---|
| Background deep | `#04080E` |
| Background panel | `#061016` |
| Mint green (primary) | `#39FF88` |
| Cyan (glitch accent) | `#40E0FF` |
| Magenta (glitch accent) | `#FF41A0` |
| Off-white text | `#EEF6F2` |
| Muted grey-green | `#7A9492` |

### Type

- Headline: **Arial Black / Archivo Black / Inter Black**, 150–180 px,
  tight leading, uppercase.
- Kicker: monospace bold, 22–26 px, mint.
- Terminal: **JetBrains Mono / SF Mono / Menlo**, 22–26 px.
- Footer: monospace, 18–20 px, muted.

### Composition

- Left 55–60%: headline stack.
- Right 35–40%: terminal card + shield outline + voxel cubes.
- Top-left: kicker and event label.
- Bottom: thin green rule, CVE + slogan on the left, event/venue on the right.
- Keep the center-left free of icons; desktop icons usually sit top-left or
  left edge. Don't put critical text under them.

### Mood

- “We broke in politely.”
- Clean security-poster energy, not Matrix rain, not a hooded hacker.
- A little Minecraft nod (voxel cubes) without using Mojang assets.
- The joke is “YOU'VE BEEN HACKED. ETHICALLY.” — keep it playful, not scary.

---

## Alternate concepts (if you want variants)

1. **“ACCESS GRANTED”** — giant green badge, tiny line “to a wallpaper, not your
   files.” Good for a second station.
2. **“PATCHED.”** — mostly black, one green word, small “this is why we update.”
   Good for the closing slide/wallpaper after the demo.
3. **“ONE MESSAGE.”** — a single chat bubble with a green check; minimal.
4. **“LOG4SHELL, 2021.”** — historical poster, timeline at the bottom.

Don't use the actual trigger syntax in the wallpaper. It invites screenshots
and copy-paste attempts. Keep the public image conceptual.
