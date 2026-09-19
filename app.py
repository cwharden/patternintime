import streamlit as st
import re
import csv
from io import StringIO

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
    "sc": "dc", "hdc": "htr", "dc": "tr", "tr": "dtr",
    "dtr": "trtr", "trtr": "qtr",
    "sk": "miss", "skip": "miss", "gauge": "tension",
}

UK_TO_US = {
    "double crochet": "single crochet",
    "half treble crochet": "half double crochet",
    "treble crochet": "double crochet",
    "double treble crochet": "treble crochet",
    "triple treble crochet": "double treble crochet",
    "quadruple treble crochet": "triple treble crochet",
    "dc": "sc", "htr": "hdc", "tr": "dc", "dtr": "tr",
    "trtr": "dtr", "qtr": "trtr",
    "miss": "skip", "tension": "gauge",
}

# ---------- Translation Engine ----------
def build_regex(mapping):
    keys = sorted(mapping.keys(), key=len, reverse=True)
    pattern = r'(?<![a-zA-Z])(' + '|'.join(re.escape(k) for k in keys) + r')(?![a-zA-Z])'
    return re.compile(pattern, re.IGNORECASE)

def translate_text(text, mapping):
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
if 'yarn_stash' not in st.session_state:
    st.session_state.yarn_stash = []

FREE_LIMIT = 2
UNLOCK_CODE = "PLARN2026"

# ---------- URL-based unlock ----------
try:
    url_code = st.query_params.get("code", "")
    if isinstance(url_code, list):
        url_code = url_code[0] if url_code else ""
    if url_code and url_code.strip().upper() == UNLOCK_CODE:
        st.session_state.unlimited = True
except Exception:
    pass

# ---------- Header ----------
st.title("🧶 PatternInTime")
st.markdown("**Tools for crocheters, plarn makers, and fiber artists.**")
st.caption("Translate patterns between US & UK · Track your yarn and plarn stash")

# ---------- Top-Level Tabs ----------
tab_trans, tab_stash = st.tabs(["🔄 Pattern Translator", "🧶 Yarn & Plarn Stash"])

# ==========================================================
# TAB 1: TRANSLATOR
# ==========================================================
with tab_trans:
    st.caption("💡 *Fun fact: a US 'single crochet' is a UK 'double crochet'. Same stitch, different name.*")

    direction = st.radio(
        "**Direction**",
        ["🇺🇸 US → 🇬🇧 UK", "🇬🇧 UK → 🇺🇸 US"],
        horizontal=True,
        key="direction"
    )

    col_s1, col_s2, _ = st.columns([1, 1, 3])
    with col_s1:
        if st.button("📋 Try a sample", use_container_width=True):
            st.session_state.pattern_input = SAMPLE_US if "US →" in direction else SAMPLE_UK
            st.rerun()
    with col_s2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.pattern_input = ""
            st.rerun()

    st.subheader("📝 Paste Your Pattern")
    input_text = st.text_area(
        "Pattern text",
        height=200,
        key="pattern_input",
        label_visibility="collapsed",
        placeholder="Paste your crochet pattern here..."
    )

    remaining = FREE_LIMIT - st.session_state.translations_used
    if st.session_state.unlimited:
        st.caption("✨ **Unlimited access** — thank you for your support!")
    elif remaining > 0:
        st.caption(f"✨ You have **{remaining}** free translation{'s' if remaining != 1 else ''} remaining.")
    else:
        st.caption("🔒 Free limit reached. Unlock unlimited access below.")

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
        - 🧶 Free lifetime access to the Yarn & Plarn Stash tool
        - Support a small handmade business

        **$5 one-time** — no subscription, no expiration.
        """)
        st.link_button(
            "💳 Get Unlimited Access — $5",
            "https://plarnthings.etsy.com/listing/4574250200",
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
                    try:
                        st.query_params["code"] = UNLOCK_CODE
                    except Exception:
                        pass
                    st.success("🎉 Unlimited access unlocked! Bookmark this page to stay unlocked.")
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

# ==========================================================
# TAB 2: YARN & PLARN STASH
# ==========================================================
with tab_stash:
    st.subheader("🧶 Your Yarn & Plarn Stash")
    st.caption("Track yarn, plarn, thread, or any fiber — by yards, meters, inches, or feet.")

    with st.expander("➕ Add New Stash Item", expanded=not st.session_state.yarn_stash):
        with st.form("add_yarn_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                material = st.selectbox(
                    "Material Type",
                    ["Yarn", "Plarn", "Thread", "Other"]
                )
                brand = st.text_input("Brand or Name", placeholder="e.g. Red Heart, Grocery bag plarn")
                color = st.text_input("Color", placeholder="e.g. Teal, Mixed white/blue")
            with col_b:
                weight = st.selectbox(
                    "Weight (for yarn)",
                    ["—", "Lace (0)", "Fingering (1)", "Sport (2)", "DK (3)",
                     "Worsted (4)", "Bulky (5)", "Super Bulky (6)", "Jumbo (7)"]
                )
                qty = st.number_input("Quantity", min_value=0.0, step=0.1, value=0.0)
                unit = st.selectbox("Unit", ["yards", "meters", "inches", "feet"])

            is_scrap = st.checkbox("♻️ This is a scrap / partial piece")
            notes = st.text_area("Notes", height=68, placeholder="e.g. 2 grocery bags used, 1-inch strips")

            submitted = st.form_submit_button("✅ Save to Stash")

            if submitted:
                if not brand.strip():
                    st.warning("Please enter a brand or name.")
                elif qty <= 0:
                    st.warning("Please enter a quantity greater than 0.")
                else:
                    st.session_state.yarn_stash.append({
                        'material': material,
                        'brand': brand.strip(),
                        'color': color.strip(),
                        'weight': weight if weight != "—" else "",
                        'qty': qty,
                        'unit': unit,
                        'scrap': is_scrap,
                        'notes': notes.strip()
                    })
                    st.success(f"✅ Added {brand} ({qty} {unit}) to your stash!")

    # ---------- View / Filter ----------
    if st.session_state.yarn_stash:
        st.markdown("---")
        st.subheader("📋 Your Stash")

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filter_material = st.selectbox(
                "Filter by material",
                ["All", "Yarn", "Plarn", "Thread", "Other"]
            )
        with col_f2:
            filter_scrap = st.selectbox(
                "Show",
                ["All items", "Full skeins only", "Scraps only"]
            )
        with col_f3:
            search = st.text_input("Search", placeholder="brand or color")

        filtered = st.session_state.yarn_stash
        if filter_material != "All":
            filtered = [s for s in filtered if s['material'] == filter_material]
        if filter_scrap == "Full skeins only":
            filtered = [s for s in filtered if not s['scrap']]
        elif filter_scrap == "Scraps only":
            filtered = [s for s in filtered if s['scrap']]
        if search:
            s_lower = search.lower()
            filtered = [s for s in filtered
                        if s_lower in s['brand'].lower() or s_lower in s['color'].lower()]

        # Summary
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.metric("Total Items", len(st.session_state.yarn_stash))
        with col_m2:
            st.metric("Scraps", sum(1 for s in st.session_state.yarn_stash if s['scrap']))
        with col_m3:
            st.metric("Showing", len(filtered))

        # Length totals by unit
        if filtered:
            unit_totals = {}
            for s in filtered:
                unit_totals[s['unit']] = unit_totals.get(s['unit'], 0) + s['qty']
            totals_str = " · ".join(f"{v:,.1f} {u}" for u, v in unit_totals.items())
            st.caption(f"📏 Total length shown: **{totals_str}**")

        # Table
        if filtered:
            display_data = []
            for idx, s in enumerate(filtered):
                display_data.append({
                    'Material': s['material'],
                    'Brand/Name': s['brand'],
                    'Color': s['color'],
                    'Weight': s['weight'] if s['weight'] else '—',
                    'Quantity': s['qty'],
                    'Unit': s['unit'],
                    'Scrap': '♻️' if s['scrap'] else '',
                    'Notes': s['notes']
                })
            st.dataframe(display_data, use_container_width=True)
        else:
            st.info("No items match your filters.")

        # Delete individual entries
        with st.expander("🗑️ Delete individual items"):
            for idx, s in enumerate(st.session_state.yarn_stash):
                col_info, col_del = st.columns([4, 1])
                with col_info:
                    scrap_tag = " ♻️" if s['scrap'] else ""
                    st.write(f"**{s['brand']}** · {s['material']} · {s['color']} · {s['qty']} {s['unit']}{scrap_tag}")
                with col_del:
                    if st.button("Delete", key=f"del_yarn_{idx}"):
                        st.session_state.yarn_stash.pop(idx)
                        st.rerun()

        # Export / Import
        st.markdown("---")
        col_ex, col_im, col_cl = st.columns(3)
        with col_ex:
            output = StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=['material', 'brand', 'color', 'weight', 'qty', 'unit', 'scrap', 'notes']
            )
            writer.writeheader()
            for s in st.session_state.yarn_stash:
                row = dict(s)
                row['scrap'] = 'Yes' if s['scrap'] else 'No'
                writer.writerow(row)        
            st.download_button(
                label="📥 Export Stash CSV",
                data=output.getvalue().encode('utf-8'),
                file_name="PatternInTime_yarn_stash.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col_im:
            uploaded = st.file_uploader(
                "📤 Import Stash CSV",
                type="csv",
                key="stash_import",
                label_visibility="collapsed"
            )
            if uploaded is not None:
                try:
                    content = uploaded.getvalue().decode('utf-8')
                    reader = csv.DictReader(StringIO(content))
                    imported = []
                    for row in reader:
                        imported.append({
                            'material': row.get('material', 'Yarn'),
                            'brand': row.get('brand', ''),
                            'color': row.get('color', ''),
                            'weight': row.get('weight', '') or '—',
                            'qty': float(row.get('qty', 0) or 0),
                            'unit': row.get('unit', 'yards'),
                            'scrap': str(row.get('scrap', '')).strip().lower() in ('yes', 'true', '1'),
                            'notes': row.get('notes', '')
                        })
                    st.session_state.yarn_stash = imported
                    st.success(f"✅ Imported {len(imported)} items.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Import failed: {e}")

        with col_cl:
            if st.button("🗑️ Clear Entire Stash", type="primary", use_container_width=True):
                st.session_state.yarn_stash = []
                st.success("✅ Stash cleared.")
                st.rerun()

    else:
        st.info("🌱 Your stash is empty. Add your first item above!")

# ---------- Footer ----------
st.markdown("---")
st.markdown(
    "**PatternInTime** — built by a crocheter, for crocheters. 🧶  "
    "Questions or feedback? [Contact me](mailto:cwhstier@gmail.com)."
)
st.caption("Made in Memphis, Tennessee · Powered by Streamlit")