"""Mail merge data shared by the Mailings dialogs and native/mailmerge.py:
envelope and label sizes, reading a recipient list, and the address block's
columns."""
import csv

ENVELOPES = [  # name, width, height (1/100 mm, landscape)
    ("Size 10  (4 1/8 x 9 1/2 in)", 24130, 10477),
    ("DL  (110 x 220 mm)", 22000, 11000),
    ("C5  (162 x 229 mm)", 22900, 16200),
    ("C6  (114 x 162 mm)", 16200, 11400),
    ("Monarch  (3 7/8 x 7 1/2 in)", 19050, 9843),
]

LABELS = [  # name, page w, h, label w, h, cols, rows, top, side, hpitch, vpitch (mm100)
    ("Address, 30 per page (2.625\" x 1\")", 21590, 27940, 6668, 2540, 3, 10,
     1270, 476, 6985, 2540),
    ("Shipping, 10 per page (4\" x 2\")", 21590, 27940, 10160, 5080, 2, 5,
     1270, 397, 10795, 5080),
    ("Address, 14 per page (4\" x 1.33\")", 21590, 27940, 10160, 3387, 2, 7,
     2117, 397, 10795, 3387),
    ("Shipping, 6 per page (4\" x 3.33\")", 21590, 27940, 10160, 8467, 2, 3,
     1270, 397, 10795, 8467),
    ("Return address, 80 per page (1.75\" x 0.5\")", 21590, 27940, 4445, 1270, 4, 20,
     1270, 762, 5207, 1270),
    ("A4 address, 21 per page (63.5 x 38.1 mm)", 21000, 29700, 6350, 3810, 3, 7,
     1515, 720, 6604, 3810),
    ("A4 address, 24 per page (64 x 33.9 mm)", 21000, 29700, 6400, 3390, 3, 8,
     1290, 700, 6600, 3390),
    ("A4 parcel, 8 per page (99.1 x 67.7 mm)", 21000, 29700, 9910, 6770, 2, 4,
     1310, 470, 10160, 6770),
]



def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig", errors="replace") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        rows = list(csv.reader(f, dialect))
    rows = [r for r in rows if any(c.strip() for c in r)]
    if not rows:
        return [], []
    head = [h.strip() or "Column%d" % (i + 1) for i, h in enumerate(rows[0])]
    data = []
    for r in rows[1:]:
        r = r + [""] * (len(head) - len(r))
        data.append(dict(zip(head, r[:len(head)])))
    return head, data


def _find(cols, *names):
    low = {c.lower().replace(" ", "").replace("_", ""): c for c in cols}
    for n in names:
        c = low.get(n.lower().replace(" ", "").replace("_", ""))
        if c:
            return c
    return None


def address_columns(cols, m=None):
    """Lines of an address block as lists of columns (Match Fields decides
    which column is which)."""
    if m is not None:
        from .mailrules import matched_column
        mc = lambda f: matched_column(m, f, cols)   # noqa: E731
        title, first, last = mc("Courtesy Title"), mc("First Name"), mc("Last Name")
        company, a1, a2 = mc("Company"), mc("Address 1"), mc("Address 2")
        city, state, zipc = mc("City"), mc("State"), mc("Postal Code")
        country = mc("Country or Region")
        name = _find(cols, "Name", "Full Name")
    else:
        title = _find(cols, "Title", "Salutation")
        first = _find(cols, "First Name", "FirstName", "Given Name", "First")
        last = _find(cols, "Last Name", "LastName", "Surname", "Family Name", "Last")
        name = _find(cols, "Name", "Full Name")
        company = _find(cols, "Company", "Company Name", "Organization")
        a1 = _find(cols, "Address Line 1", "Address1", "Address", "Street")
        a2 = _find(cols, "Address Line 2", "Address2")
        city = _find(cols, "City", "Town")
        state = _find(cols, "State", "Province", "Region")
        zipc = _find(cols, "ZIP Code", "Zip", "Postal Code", "Postcode", "ZIP")
        country = _find(cols, "Country", "Country or Region")
    lines = []
    who = [c for c in (title, first, last) if c] or ([name] if name else [])
    if who:
        lines.append(who)
    for c in (company, a1, a2):
        if c:
            lines.append([c])
    tail = [c for c in (city, state, zipc) if c]
    if tail:
        lines.append(tail)
    if country:
        lines.append([country])
    return lines or [[c] for c in cols[:4]]
