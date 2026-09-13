import streamlit as st
import re

# ---------- Page Setup ----------
st.set_page_config(page_title="PatternInTime", page_icon="🧶", layout="wide")

# ---------- Translation Dictionaries ----------
US_TO_UK = {
    "single crochet": "double crochet",
    "half double crochet": "half treble crochet",
    "double crochet": "treble crochet",
    "treble crochet": "double treble crochet",
    "double treble crochet": "triple treble crochet",
    "triple treble crochet": "quadruple treble crochet",
    "sc": "dc",
    "hdc": "htr",
    "dc": "tr",
    "tr": "dtr",
    "dtr": "trtr",
    "trtr": "qtr",
    "sk": "miss",
    "skip": "miss",
    "gauge": "tension",
}

UK_TO_US = {
    "double crochet": "single crochet",
    "half treble crochet": "half double crochet",
    "treble crochet": "double crochet",
    "double treble crochet": "treble crochet",
    "triple treble crochet": "double treble crochet",
    "quadruple treble crochet": "triple treble crochet",
    "dc": "sc",
    "htr": "hdc",
    "tr": "dc",
    "dtr": "tr",
    "trtr": "dtr",
    "qtr": "trtr",
    "miss": "skip",
    "tension": "gauge",
}

# ---------- Translation Engine ----------
def build_regex(mapping):
    """Build a single regex that matches all keys, longest first."""
    keys = sorted(mapping.keys(), key=len, reverse=True)
    pattern = r'(?<![a-zA-Z])(' + '|'.join(re.escape(k) for k in keys) + r')(?![a-zA-Z])'
    return re.compile(pattern, re.IGNORECASE)

def translate_text(text, mapping):
    """Translate text; return (result, num_replacements, unique_changes)."""
    regex = build_regex(mapping)
    count = [0]
    unique_changes = {}

    def replacer(match):
        original = match.group(0)
        replacement = mapping.get(original.lower())
        if replacement is None or replacement.lower() == original.lower():
            return original
        count[0] += 1
        key = original.lower()
        if key not in unique_changes:
            unique_changes[key] = [key, replacement, 0]
        unique_changes[key][2] += 1
        # Preserve case
        if original.isupper():
            return replacement.upper()
        elif original[0].isupper():
            return replacement.capitalize()
        return replacement

    result = regex.sub(replacer, text)
    return result, count[0], unique_changes

# ---------- Sample Patterns ----------
SAMPLE_US = """Row 1: Ch 21, sc in 2nd ch from hook, sc in each ch across. (20 sc)
Row 2: Ch 1, turn. Sc in first st, *dc in next st, sc in next st*, repeat across. (10 dc, 10 sc)
Row 3: Ch 3 (counts as dc), turn. Dc in each st across. (20 dc)
Fasten off. Gauge: 4 sc = 1 inch."""

SAMPLE_UK = """Row 1: Ch 21, dc in 2nd ch from hook, dc in each ch across. (20 dc)
Row 2: Ch 1, turn. Dc in first st, *tr in next st, dc in next st*, repeat across. (10 tr, 10 dc)
Row 3: Ch 3 (counts as tr), turn. Tr in each st across. (20 tr)
Fasten off. Tension: 4 dc = 1 inch."""

# ---------- Session State ----------
if 'translations_used' not in st.session_state:
    st.session_state.translations_used = 0
if 'last_result' not in st.session_state:
    st.session_state.last_result = None
if 'pattern_input' not in st.session_state:
    st.session_state.pattern_input = ""
if 'unlimited' not in st.session_state:
    st.session_state.unlimited = False

FREE_LIMIT = 2
UNLOCK_CODE = "PLARN2026"  # ← Change this to your own secret code

# ---------- Header ----------
st.title("🧶 PatternInTime")
st.markdown("**Convert crochet patterns between US and UK terminology — instantly.**")
st.caption("Paste any pattern. Pick a direction. Get a translated version in seconds.")
st.caption("💡 *Fun fact: a US 'single crochet' is a UK 'double crochet'. Same stitch, different name.*")

# ---------- Direction Toggle ----------
direction = st.radio(
    "**Direction**",
    ["🇺🇸 US → 🇬🇧 UK", "🇬🇧 UK → 🇺🇸 US"],
    horizontal=True,
    key="direction"
)

# ---------- Sample & Clear Buttons ----------
col_s1, col_s2, _ = st.columns([1, 1, 3])
with col_s1:
    if st.button("📋 Try a sample", use_container_width=True):
        st.session_state.pattern_input = SAMPLE_US if "US →" in direction else SAMPLE_UK
        st.rerun()
with col_s2:
    if st.button("🗑️ Clear", use_container_width=True):
        st.session_state.pattern_input = ""
        st.rerun()

# ---------- Input ----------
st.subheader("📝 Paste Your Pattern")
input_text = st.text_area(
    "Pattern text",
    height=200,
    key="pattern_input",
    label_visibility="collapsed",
    placeholder="Paste your crochet pattern here..."
)

# ---------- Usage Indicator ----------
remaining = FREE_LIMIT - st.session_state.translations_used
if st.session_state.unlimited:
    st.caption("✨ **Unlimited access** — thank you for your support!")
elif remaining > 0:
    st.caption(f"✨ You have **{remaining}** free translation{'s' if remaining != 1 else ''} remaining.")
else:
    st.caption("🔒 Free limit reached. Unlock unlimited access below.")

# ---------- Translate Button ----------
translate_clicked = st.button(
    "🔄 Translate",
    type="primary",
    use_container_width=True,
    disabled=(not st.session_state.unlimited and remaining <= 0)
)

if translate_clicked:
    if not input_text.strip():
        st.warning("Please paste a pattern first.")
    else:
        mapping = US_TO_UK if "US →" in direction else UK_TO_US
        result, num_changes, unique_changes = translate_text(input_text, mapping)
        st.session_state.translations_used += 1
        st.session_state.last_result = {
            'text': result,
            'num_changes': num_changes,
            'changes': unique_changes,
            'direction': direction,
        }

# ---------- Output ----------
if st.session_state.last_result:
    r = st.session_state.last_result
    st.markdown("---")
    st.subheader("✅ Translated Pattern")
    st.caption(f"Direction: {r['direction']}  ·  {r['num_changes']} term{'s' if r['num_changes'] != 1 else ''} translated")

    st.text_area(
        "Translated output",
        value=r['text'],
        height=250,
        key="output_area"
    )
    st.caption("💡 Select all (Ctrl+A / Cmd+A) and copy (Ctrl+C / Cmd+C) to grab the translated text.")

    st.download_button(
        label="📥 Download translated pattern (.txt)",
        data=r['text'].encode('utf-8'),
        file_name="PatternInTime_translated.txt",
        mime="text/plain"
    )

    if r['changes']:
        with st.expander(f"📋 See what changed ({len(r['changes'])} unique term{'s' if len(r['changes']) != 1 else ''})"):
            for key, (orig, repl, cnt) in sorted(r['changes'].items()):
                st.write(f"- **{orig}** → **{repl}**  ({cnt}×)")

# ---------- Upgrade Prompt ----------
if not st.session_state.unlimited and remaining <= 0:
    st.markdown("---")
    st.subheader("🚀 Unlock Unlimited Translations")
    st.markdown("""
    You've used your 2 free translations. Love the tool? Get **unlimited access** and support a fellow maker.

    **What you get:**
    - ♾️ Unlimited pattern translations
    - 📥 Download translated patterns
    - 🧶 Support a small handmade business

    **$5 one-time** — no subscription, no expiration.
    """)
    st.link_button(
        "💳 Get Unlimited Access — $5",
        "https://www.etsy.com/shop/PlarnThings",
        type="primary",
        use_container_width=True
    )

    st.markdown("---")
    st.markdown("**Already purchased? Enter your unlock code:**")
    col_code, col_btn = st.columns([3, 1])
    with col_code:
        code_input = st.text_input(
            "Unlock code",
            key="unlock_code_input",
            label_visibility="collapsed",
            placeholder="Enter your unlock code"
        )
    with col_btn:
        if st.button("Unlock", use_container_width=True):
            if code_input.strip().upper() == UNLOCK_CODE:
                st.session_state.unlimited = True
                st.success("🎉 Unlimited access unlocked! Enjoy!")
                st.rerun()
            else:
                st.error("Invalid code.")

# ---------- Hook Size Reference ----------
st.markdown("---")
with st.expander("📏 Hook Size Conversion Chart (US ↔ UK ↔ Metric)"):
    st.markdown("""
| US Size | Metric | UK Size |
|---|---|---|
| B/1 | 2.25 mm | 13 |
| C/2 | 2.75 mm | 12 |
| D/3 | 3.25 mm | 10 |
| E/4 | 3.50 mm | 9 |
| F/5 | 3.75 mm | 8 |
| G/6 | 4.00 mm | 7 |
| H/8 | 5.00 mm | 6 |
| I/9 | 5.50 mm | 5 |
| J/10 | 6.00 mm | 4 |
| K/10.5 | 6.50 mm | 3 |
| L/11 | 8.00 mm | 0 |
| M/13 | 9.00 mm | 00 |
| N/15 | 10.00 mm | 000 |

*Hook sizing can vary by manufacturer. When in doubt, use the metric (mm) measurement.*
""")

with st.expander("🔧 Developer Options — remove before public launch"):
    if st.button("Reset translation counter"):
        st.session_state.translations_used = 0
        st.session_state.unlimited = False
        st.success("Counter and unlock reset.")

# ---------- Footer ----------
st.markdown("---")
st.markdown(
    "**PatternInTime** — built by a crocheter, for crocheters. 🧶  "
    "Questions or feedback? [Contact me](mailto:cwhstier@gmail.com)."
)
st.caption("Made in Memphis, Tennessee · Powered by Streamlit")