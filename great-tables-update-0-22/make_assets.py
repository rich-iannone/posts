"""Generate the table images embedded in the Great Tables v0.22.0 post.

Each table below mirrors a (non-executing) code block in index.qmd. We build
the table and write it to assets/<name>.png with gtsave(), so the post can show
static code plus a rendered image rather than embedding live HTML (which Hugo's
Goldmark parser mishandles when Great Tables' inline <style> contains blank
lines).

Run from this directory with the project venv:

    ../.venv/bin/python make_assets.py
"""

from pathlib import Path

import pandas as pd
import polars as pl
from great_tables import GT, loc, md, vals, exibble
from great_tables.data import towny, gtcars, exibble as exibble_df

ASSETS = Path(__file__).parent / "assets"
ASSETS.mkdir(exist_ok=True)


def save(table: GT, name: str) -> None:
    path = ASSETS / f"{name}.png"
    table.gtsave(str(path))
    print(f"wrote {path} ({path.stat().st_size} bytes)")


# 1. Footnotes with tab_footnote()
towny_mini = (
    pl.from_pandas(towny)
    .filter(pl.col("csd_type") == "city")
    .select(["name", "density_2021", "population_2021"])
    .top_k(10, by="population_2021")
    .sort("population_2021", descending=True)
)
save(
    GT(towny_mini, rowname_col="name")
    .tab_header(
        title=md("The 10 Largest Municipalities in `towny`"),
        subtitle="Population values taken from the 2021 census.",
    )
    .fmt_integer()
    .cols_label(density_2021="Density", population_2021="Population")
    .tab_footnote(
        footnote="Part of the Greater Toronto Area.",
        locations=loc.stub(rows=["Toronto", "Mississauga", "Brampton", "Markham", "Vaughan"]),
    )
    .tab_footnote(
        footnote=md("Density is in terms of persons per {{km^2}}."),
        locations=loc.column_labels(columns="density_2021"),
    )
    .tab_footnote(
        footnote="Census results made public on February 9, 2022.",
        locations=loc.subtitle(),
    )
    .opt_footnote_marks(marks="letters"),
    "footnotes",
)

# 2. Group-wise summaries with summary_rows()
gtcars_mini = pl.from_pandas(gtcars).select(["mfr", "model", "hp", "trq"]).head(12)
save(
    GT(gtcars_mini, rowname_col="model", groupname_col="mfr").summary_rows(
        fns={"Min": pl.col("hp", "trq").min(), "Max": pl.col("hp", "trq").max()},
        fmt=vals.fmt_integer,
    ),
    "summary-rows",
)

# 3. cols_merge_uncert()
exibble_unc = pl.from_pandas(exibble_df).select("num", "currency").slice(0, 7)
save(
    GT(exibble_unc)
    .fmt_number(columns="num", decimals=3, use_seps=False)
    .cols_merge_uncert(col_val="currency", col_uncert="num")
    .cols_label(currency="value + uncert."),
    "cols-merge-uncert",
)

# 4. cols_merge_n_pct()
df_npct = pl.DataFrame({"category": ["A", "B", "C"], "n": [10, 20, 30], "pct": [0.167, 0.333, 0.500]})
save(
    GT(df_npct)
    .fmt_percent(columns="pct")
    .cols_merge_n_pct(col_n="n", col_pct="pct")
    .cols_label(n="Count (%)"),
    "cols-merge-n-pct",
)

# 5. cols_reorder()
exibble_reorder = exibble_df[["num", "char", "fctr", "date", "time"]]
save(GT(exibble_reorder).cols_reorder(["fctr", "date", "time", "char", "num"]), "cols-reorder")

# 6. text_transform()
save(
    GT(exibble_df[["num", "char"]].head(4))
    .fmt_number(columns="num", decimals=2)
    .text_transform(
        locations=[loc.body(columns="num"), loc.body(columns="char")],
        fn=lambda x: f"~ {x}",
    ),
    "text-transform",
)

# 7. text_replace()
df_replace = pd.DataFrame({"item": ["Column A (details)", "Column B (info)"], "value": [1, 2]})
save(
    GT(df_replace).text_replace(
        pattern=r"\((.+?)\)",
        replacement=r"(<em>\1</em>)",
        locations=loc.body(columns="item"),
    ),
    "text-replace",
)

# 8. text_case_when()
df_score = pd.DataFrame({"score": [95, 72, 88, 61, 100]})
save(
    GT(df_score)
    .fmt_number(columns="score", decimals=0)
    .text_case_when(
        (lambda x: int(x) >= 90, "A"),
        (lambda x: int(x) >= 80, "B"),
        (lambda x: int(x) >= 70, "C"),
        default="F",
        locations=loc.body(columns="score"),
    ),
    "text-case-when",
)

# 9. sub_small_vals()
neg_vals_df = pl.DataFrame({"i": range(1, 6), "numbers": [-0.0001, -0.005, -0.05, -1.0, -100.0]})
save(
    GT(neg_vals_df).fmt_number(columns="numbers").sub_small_vals(sign="-", threshold=0.01, small_pattern="~0"),
    "sub-small-vals",
)

# 10. fmt_duration()
df_dur = pd.DataFrame({"event": ["Marathon", "Half Marathon", "10K", "Mile"], "winning_time_s": [7377, 3542, 1620, 233]})
save(
    GT(df_dur).fmt_duration(
        columns="winning_time_s",
        input_units="seconds",
        duration_style="colon-sep",
        output_units=["hours", "minutes", "seconds"],
    ),
    "fmt-duration",
)

# 11. fmt_partsper()
concentrations = pl.DataFrame({"gas": ["CO", "NO2", "O3"], "conc": [1.5, 35.0, 120.0]})
save(
    GT(concentrations).fmt_partsper(columns="conc", to_units="ppb", scale_values=False, symbol="ppbV"),
    "fmt-partsper",
)

# 12. gtsave() section demo table
gtcars_msrp = pl.from_pandas(gtcars).select(["mfr", "model", "msrp"]).head(5)
save(
    GT(gtcars_msrp).tab_header(title="Some Cars from gtcars").fmt_currency(columns="msrp"),
    "gtsave-example",
)
