import streamlit as st

# FORMAT: (Title, Description, Link, Optional_Note)
ARTICLES = [
    (
        "I. Ban Congressional Stock Trading",
        "Prohibits Members, their spouses, and dependent children from owning or trading individual stocks. Requires full divestment or a qualified blind trust.",
        "https://www.congress.gov/bill/118th-congress/senate-bill/1171",
        None,
    ),
    (
        "II. End Forever Wars",
        "Repeal outdated authorizations (AUMFs) to return war powers to Congress.",
        "https://www.congress.gov/bill/118th-congress/senate-bill/316",
        None,
    ),
    (
        "III. Lifetime Lobbying Ban",
        "Former Members of Congress are banned for life from becoming registered lobbyists.",
        "https://www.congress.gov/bill/118th-congress/house-bill/1601",
        None,
    ),
    (
        "IV. Tax the Ultra-Wealthy",
        "Close tax loopholes and establish a minimum tax for billionaires.",
        "https://www.congress.gov/bill/118th-congress/house-bill/6498",
        None,
    ),
    (
        "V. Ban Corporate PACs",
        "Prohibit for-profit corporations from forming Political Action Committees.",
        "https://www.congress.gov/bill/118th-congress/house-bill/5941",
        "Note: This legislation includes a 'severability clause.' If the Supreme Court strikes down this specific ban, the rest of the 80% Bill remains law.",
    ),
    (
        "VI. Audit the Pentagon",
        "The Pentagon has never passed an audit. Require a full, independent audit to root out waste and fraud.",
        "https://www.congress.gov/bill/118th-congress/house-bill/2961",
        None,
    ),
    (
        "VII. Medicare Drug Negotiation",
        "1. H.R. 4895: Expands negotiation to 50 drugs/year and applies lower prices to private insurance.\\n2. H.R. 853: Closes the 'Orphan Drug' loophole.",
        "https://www.congress.gov/bill/118th-congress/house-bill/4895",
        "Note: This entry combines two bills to protect all Americans (not just seniors) and stop Big Pharma from gaming the 'rare disease' system.",
    ),
    (
        "VIII. Fair Elections & End Gerrymandering",
        "Pass the 'Freedom to Vote Act' to ban partisan gerrymandering and the 'John Lewis Act' to restore the Voting Rights Act.",
        "https://www.congress.gov/bill/117th-congress/house-bill/5746",
        None,
    ),
    (
        "IX. Protect US Farmland",
        "Ban adversarial foreign governments from buying American farmland. Includes a 'Beneficial Ownership' registry to stop shell companies.",
        "https://www.congress.gov/bill/118th-congress/house-bill/9456",
        None,
    ),
    (
        "X. Ban Corporate Purchase of Single Family Homes",
        "Imposes a massive tax penalty on corporations buying *existing* homes, making it unprofitable. Explicitly allows them to *build* new rental homes to increase supply.",
        "https://www.congress.gov/bill/118th-congress/senate-bill/3402",
        "Note: This uses an excise tax (not a ban) to bypass the 'Takings Clause' and forces hedge funds to sell existing homes over 10 years.",
    ),
    (
        "XI. Fund Social Security",
        "Lifts the cap on wages AND taxes investment income (Capital Gains) for earners over $400k. Prevents billionaires from dodging the tax by taking 'stock' instead of 'salary'.",
        "https://www.congress.gov/bill/118th-congress/senate-bill/1174",
        None,
    ),
    (
        "XII. Police Body Cameras",
        "Mandates cameras for federal officers and cuts funding to states that don't comply. Includes a 'Presumption of Release' clause so police can't hide footage.",
        "https://www.congress.gov/bill/117th-congress/house-bill/1280",
        None,
    ),
    (
        "XIII. Ban 'Dark Money' (Overturn Citizens United)",
        "A provision to overturn *Citizens United* and ban corporate dark money. Requires a 2/3rds vote to survive the Supreme Court.",
        "https://www.congress.gov/bill/118th-congress/house-joint-resolution/54",
        "Severability Note: This clause overturns Citizens United, but we acknowledge it will be struck down by the Court unless this bill passes with the votes required to amend the Constitution (2/3rds).",
    ),
    (
        "XIV. Paid Family Leave",
        "Guarantees 12 weeks of paid leave funded by a payroll insurance fund. Explicitly prohibits firing workers (of any company size) for taking this leave.",
        "https://www.congress.gov/bill/118th-congress/house-bill/3481",
        None,
    ),
    (
        "XV. Release the Epstein Files",
        "Mandates the full, unredacted release of all documents, including those hidden by previous partial releases.",
        "https://www.congress.gov/bill/119th-congress/house-resolution/577",
        "Note: While some files were released in late 2025, many names were redacted. This resolution demands the immediate release of ALL documents without hiding names.",
    ),
    (
        "XVI. Veterans Care Choice",
        "Codifies the right to private care but mandates strict network adequacy standards so doctors actually accept the coverage. Cuts the red tape on 'Pre-Authorization'.",
        "https://www.congress.gov/bill/118th-congress/house-bill/8371",
        None,
    ),
    (
        "XVII. The DISCLOSE Act",
        "Requires immediate disclosure of donors ($10k+) and includes 'Trace-Back' rules to follow money through shell companies to the original source.",
        "https://www.congress.gov/bill/118th-congress/senate-bill/512",
        None,
    ),
    (
        "XVIII. Close Tax Loopholes",
        "Reclassifies 'Carried Interest' as ordinary income, regardless of holding period. Ensures hedge fund managers pay the same tax rate as nurses and teachers.",
        "https://www.congress.gov/bill/118th-congress/senate-bill/4123",
        None,
    ),
    (
        "XIX. Right to Repair (Ban 'Parts Pairing')",
        "Guarantees access to parts/manuals for cars AND electronics. Explicitly bans 'software pairing' that blocks genuine 3rd-party repairs.",
        "https://www.congress.gov/bill/118th-congress/house-bill/906",
        "Note: This entry combines the automotive 'REPAIR Act' (H.R. 906) with the 'Fair Repair Act' standards to stop companies from using software to kill independent repair.",
    ),
    (
        "XX. Ban Junk Fees",
        "Requires 'all-in' price disclosure for travel, tickets, and utilities. Prohibits companies from raising the price (dynamic pricing) once it is shown to the consumer.",
        "https://www.congress.gov/bill/118th-congress/house-bill/2463",
        None,
    ),
]


def render_articles():
    """Render all 20 bill articles."""
    for title, desc, link, note in ARTICLES:
        note_html = f"<div class='note-text'>{note}</div>" if note else ""
        html_block = (
            f"<div class='article-box'>"
            f"<div class='article-title'>{title}</div>"
            f"<div class='article-desc'>{desc}</div>"
            f"{note_html}"
            f"<a href='{link}' target='_blank' class='bill-link'>🏛️ Read the Bill</a>"
            f"</div>"
        )
        st.markdown(html_block, unsafe_allow_html=True)
