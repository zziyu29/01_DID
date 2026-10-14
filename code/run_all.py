
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats

# ==================================================
# STEP 1: LOAD AND INSPECT DATA
# ==================================================

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "raw" / "public.csv"

df = pd.read_csv(DATA_PATH)

print("Dataset shape:", df.shape)

print("\nRestaurants by state:")
print(df["STATE"].value_counts())

print("\nMissing values in key variables:")
key_vars = [
    "STATE", "STATUS2",
    "EMPFT", "NMGRS", "EMPPT",
    "EMPFT2", "NMGRS2", "EMPPT2"
]
print(df[key_vars].isna().sum())

print("\nWave 2 restaurant status:")
print(df["STATUS2"].value_counts(dropna=False).sort_index())


# ==================================================
# STEP 2: DATA CLEANING AND FTE CONSTRUCTION
# ==================================================

# Full-time-equivalent employment
df["FTE1"] = (
    df["EMPFT"] + df["NMGRS"] + 0.5 * df["EMPPT"]
)

df["FTE2"] = (
    df["EMPFT2"] + df["NMGRS2"] + 0.5 * df["EMPPT2"]
)

# Permanently closed restaurants: zero employment
df.loc[df["STATUS2"] == 3, "FTE2"] = 0

# Temporarily closed restaurants: missing employment
df.loc[df["STATUS2"].isin([2, 4, 5]), "FTE2"] = np.nan

df["DELTA_FTE"] = df["FTE2"] - df["FTE1"]

print("\nMean FTE employment by state:")
print(
    df.groupby("STATE")[["FTE1", "FTE2", "DELTA_FTE"]]
    .mean()
    .round(4)
)

print("\nValid observations:")
print(df[["FTE1", "FTE2", "DELTA_FTE"]].count())


# ==========================================================
# STEP 3: TABLE 2 REPLICATION
# Card & Krueger (1994), Table 2, p. 776
# Requires: df, ROOT, FTE1, FTE2 from Steps 1-2
# ==========================================================

import numpy as np
import pandas as pd
from scipy import stats

# ----------------------------------------------------------
# 3.1 Validate inputs
# ----------------------------------------------------------

required = [
    "STATE", "CHAIN", "CO_OWNED", "STATUS2",
    "EMPFT", "EMPPT", "NMGRS",
    "EMPFT2", "EMPPT2", "NMGRS2",
    "WAGE_ST", "WAGE_ST2",
    "PSODA", "PFRY", "PENTREE",
    "PSODA2", "PFRY2", "PENTREE2",
    "HRSOPEN", "HRSOPEN2",
    "BONUS", "SPECIAL2",
    "FTE1", "FTE2"
]

missing = [c for c in required if c not in df.columns]
if missing:
    raise ValueError(f"Missing variables: {missing}")

# ----------------------------------------------------------
# 3.2 Construct variables
# ----------------------------------------------------------

# Full-time share among non-managerial employees
# Definition differs from the original Table 2 values.
for suffix, target in [
    ("", "FULLTIME_PCT1"),
    ("2", "FULLTIME_PCT2")
]:
    ft = df["EMPFT" + suffix]
    pt = df["EMPPT" + suffix]
    denom = ft + pt

    df[target] = np.where(
        denom > 0,
        100 * ft / denom,
        np.nan
    )

# Full meal price, tax included
df["MEAL1"] = df[
    ["PSODA", "PFRY", "PENTREE"]
].sum(axis=1, min_count=3)

df["MEAL2"] = df[
    ["PSODA2", "PFRY2", "PENTREE2"]
].sum(axis=1, min_count=3)

# Wage indicators, with missing wages coded as 0
# for the all-store denominator.
for source, target, value in [
    ("WAGE_ST", "WAGE425_1", 4.25),
    ("WAGE_ST2", "WAGE425_2", 4.25),
    ("WAGE_ST2", "WAGE505_2", 5.05)
]:
    df[target] = (
        np.isclose(
            df[source].fillna(-999),
            value
        ).astype(float) * 100
    )

# Company ownership
df["OWNED_PCT"] = df["CO_OWNED"] * 100

# Wave 1: cash recruiting bonus
df["BONUS_PCT"] = df["BONUS"] * 100

# Wave 2: special recruiting program proxy
# NOT identical to cash recruiting bonus.
df["SPECIAL2_PCT"] = df["SPECIAL2"] * 100

# ----------------------------------------------------------
# 3.3 Summary statistics
# ----------------------------------------------------------

def summarize(variable):

    nj = df.loc[df["STATE"] == 1, variable].dropna()
    pa = df.loc[df["STATE"] == 0, variable].dropna()

    nj_mean = nj.mean()
    pa_mean = pa.mean()

    nj_se = nj.sem()
    pa_se = pa.sem()

    if len(nj) >= 2 and len(pa) >= 2:
        t_value = stats.ttest_ind(
            nj, pa, equal_var=False
        ).statistic
    else:
        t_value = np.nan

    return {
        "NJ": nj_mean,
        "NJ_SE": nj_se,
        "PA": pa_mean,
        "PA_SE": pa_se,
        "t": t_value,
        "NJ_N": len(nj),
        "PA_N": len(pa)
    }

results = []

def add_row(section, label, variable, note="Direct"):
    row = summarize(variable)
    row["Section"] = section
    row["Variable"] = label
    row["Definition"] = note
    results.append(row)

# ----------------------------------------------------------
# 3.4 Part 1: Store types
# ----------------------------------------------------------

chains = {
    1: "Burger King",
    2: "KFC",
    3: "Roy Rogers",
    4: "Wendy's"
}

for code, name in chains.items():
    col = f"CHAIN_{code}"
    df[col] = np.where(
        df["CHAIN"].isna(),
        np.nan,
        (df["CHAIN"] == code).astype(float) * 100
    )
    add_row("Part 1", name, col)

add_row(
    "Part 1", "Company-owned", "OWNED_PCT"
)

# ----------------------------------------------------------
# 3.5 Part 2: Wave 1
# ----------------------------------------------------------

wave1 = [
    ("FTE employment", "FTE1", "Direct"),
    (
        "Percentage full-time employees",
        "FULLTIME_PCT1",
        "Alternative: excludes managers"
    ),
    ("Starting wage", "WAGE_ST", "Direct"),
    (
        "Wage = $4.25 (%)",
        "WAGE425_1",
        "All-store denominator"
    ),
    ("Price of full meal", "MEAL1", "Direct"),
    ("Hours open (weekday)", "HRSOPEN", "Direct"),
    ("Recruiting bonus", "BONUS_PCT", "Cash bonus")
]

for label, variable, note in wave1:
    add_row("Part 2: Wave 1", label, variable, note)

# ----------------------------------------------------------
# 3.6 Part 3: Wave 2
# ----------------------------------------------------------

wave2 = [
    ("FTE employment", "FTE2", "Direct"),
    (
        "Percentage full-time employees",
        "FULLTIME_PCT2",
        "Alternative: excludes managers"
    ),
    ("Starting wage", "WAGE_ST2", "Direct"),
    (
        "Wage = $4.25 (%)",
        "WAGE425_2",
        "All-store denominator"
    ),
    (
        "Wage = $5.05 (%)",
        "WAGE505_2",
        "All-store denominator"
    ),
    ("Price of full meal", "MEAL2", "Direct"),
    ("Hours open (weekday)", "HRSOPEN2", "Direct"),
    (
        "Special recruiting program (proxy)",
        "SPECIAL2_PCT",
        "Proxy only: not equivalent to cash bonus"
    )
]

for label, variable, note in wave2:
    add_row("Part 3: Wave 2", label, variable, note)

# ----------------------------------------------------------
# 3.7 Create and save replication table
# ----------------------------------------------------------

table2 = pd.DataFrame(results)

table2 = table2[
    [
        "Section", "Variable",
        "NJ", "NJ_SE", "PA", "PA_SE",
        "t", "NJ_N", "PA_N", "Definition"
    ]
]

print("\n========== TABLE 2 REPLICATION ==========")
print(table2.round(3).to_string(index=False))

output_dir = ROOT / "outputs" / "tables"
output_dir.mkdir(parents=True, exist_ok=True)

table2.to_csv(
    output_dir / "table2_replication.csv",
    index=False
)

# ----------------------------------------------------------
# 3.8 Comparison with original Table 2
# ----------------------------------------------------------

original = [
    ("Part 1", "Burger King", 41.1, 44.3),
    ("Part 1", "KFC", 20.5, 15.2),
    ("Part 1", "Roy Rogers", 24.8, 21.5),
    ("Part 1", "Wendy's", 13.6, 19.0),
    ("Part 1", "Company-owned", 34.1, 35.4),

    ("Part 2: Wave 1", "FTE employment", 20.4, 23.3),
    ("Part 2: Wave 1", "Percentage full-time employees", 32.8, 35.0),
    ("Part 2: Wave 1", "Starting wage", 4.61, 4.63),
    ("Part 2: Wave 1", "Wage = $4.25 (%)", 30.5, 32.9),
    ("Part 2: Wave 1", "Price of full meal", 3.35, 3.04),
    ("Part 2: Wave 1", "Hours open (weekday)", 14.4, 14.5),
    ("Part 2: Wave 1", "Recruiting bonus", 23.6, 29.1),

    ("Part 3: Wave 2", "FTE employment", 21.0, 21.2),
    ("Part 3: Wave 2", "Percentage full-time employees", 35.9, 30.4),
    ("Part 3: Wave 2", "Starting wage", 5.08, 4.62),
    ("Part 3: Wave 2", "Wage = $4.25 (%)", 0.0, 25.3),
    ("Part 3: Wave 2", "Wage = $5.05 (%)", 85.2, 1.3),
    ("Part 3: Wave 2", "Price of full meal", 3.41, 3.03),
    ("Part 3: Wave 2", "Hours open (weekday)", 14.4, 14.7),
    ("Part 3: Wave 2", "Special recruiting program (proxy)", 20.3, 23.4)
]

original_df = pd.DataFrame(
    original,
    columns=["Section", "Variable", "Original_NJ", "Original_PA"]
)

comparison = table2.merge(
    original_df,
    on=["Section", "Variable"],
    how="left"
)

comparison["Difference_NJ"] = (
    comparison["NJ"] - comparison["Original_NJ"]
)

comparison["Difference_PA"] = (
    comparison["PA"] - comparison["Original_PA"]
)

comparison.to_csv(
    output_dir / "table2_comparison.csv",
    index=False
)

print("\n========== COMPARISON WITH ORIGINAL ==========")
print(
    comparison[
        [
            "Variable", "NJ", "Original_NJ",
            "Difference_NJ", "PA", "Original_PA",
            "Difference_PA", "Definition"
        ]
    ].round(3).to_string(index=False)
)

print("\nSaved: outputs/tables/table2_replication.csv")
print("Saved: outputs/tables/table2_comparison.csv")
print("IMPORTANT: Wave 2 recruiting program is a proxy.")

# ==========================================================
# 3.9 SAVE PROCESSED DATA FOR TABLE 2
# ==========================================================

# Create processed data directory
processed_dir = ROOT / "data" / "processed"
processed_dir.mkdir(parents=True, exist_ok=True)

# Select variables used in Table 2
table2_columns = [
    "STATE", "CHAIN", "CO_OWNED", "STATUS2",

    # Employment
    "EMPFT", "EMPPT", "NMGRS",
    "EMPFT2", "EMPPT2", "NMGRS2",
    "FTE1", "FTE2",

    # Full-time employee percentages
    "FULLTIME_PCT1", "FULLTIME_PCT2",

    # Starting wages and wage indicators
    "WAGE_ST", "WAGE_ST2",
    "WAGE425_1", "WAGE425_2", "WAGE505_2",

    # Meal prices
    "MEAL1", "MEAL2",

    # Operating hours
    "HRSOPEN", "HRSOPEN2",

    # Recruiting incentives
    "BONUS", "SPECIAL2",
    "BONUS_PCT", "SPECIAL2_PCT",

    # Ownership
    "OWNED_PCT",

    # Restaurant chain indicators
    "CHAIN_1", "CHAIN_2", "CHAIN_3", "CHAIN_4"
]

# Create processed dataset
table2_processed = df[table2_columns].copy()

# Save processed data
table2_processed.to_csv(
    processed_dir / "table2_analysis.csv",
    index=False
)

print("\n========== TABLE 2 PROCESSED DATA SAVED ==========")
print("Saved: data/processed/table2_analysis.csv")
print("Number of observations:", len(table2_processed))
print("Number of variables:", len(table2_processed.columns))


# ==========================================================
# STEP 4: FIGURE 1 REPLICATION
# Card & Krueger (1994), Figure 1, p. 777
# Distribution of Starting Wage Rates
# ==========================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ----------------------------------------------------------
# 4.1 Prepare wage data
# ----------------------------------------------------------

# STATE = 1: New Jersey
# STATE = 0: Pennsylvania

wage1 = df[["STATE", "WAGE_ST"]].copy()
wage2 = df[["STATE", "WAGE_ST2"]].copy()

wage1["WAGE_ST"] = pd.to_numeric(
    wage1["WAGE_ST"],
    errors="coerce"
)

wage2["WAGE_ST2"] = pd.to_numeric(
    wage2["WAGE_ST2"],
    errors="coerce"
)

# ----------------------------------------------------------
# 4.2 Define wage ranges based on the original figure
# ----------------------------------------------------------

# Original figure labels:
# $4.25, $4.35, $4.45, ..., $5.55
# Bin width = $0.10

centers = np.round(
    np.arange(4.25, 5.56, 0.10),
    2
)

# Boundaries are halfway between adjacent wage labels.
bins = np.round(
    np.arange(4.20, 5.61, 0.10),
    2
)

# Width of each individual bar
bar_width = 0.04

# ----------------------------------------------------------
# 4.3 Create Figure 1
# ----------------------------------------------------------

fig, axes = plt.subplots(
    2,
    1,
    figsize=(12, 9),
    sharex=True
)

periods = [
    ("February 1992", wage1, "WAGE_ST"),
    ("November 1992", wage2, "WAGE_ST2")
]

for ax, (period, data, wage_col) in zip(
    axes, periods
):

    # Extract NJ wages
    nj = data.loc[
        data["STATE"] == 1,
        wage_col
    ].dropna()

    # Extract PA wages
    pa = data.loc[
        data["STATE"] == 0,
        wage_col
    ].dropna()

    # Count restaurants in each wage range
    nj_counts, _ = np.histogram(
        nj,
        bins=bins
    )

    pa_counts, _ = np.histogram(
        pa,
        bins=bins
    )

    # Convert counts into percentages
    # Denominator = all valid wage observations
    # in each state and survey wave.
    nj_pct = nj_counts / len(nj) * 100
    pa_pct = pa_counts / len(pa) * 100

    # ------------------------------------------------------
    # New Jersey: solid black bars
    # ------------------------------------------------------

    ax.bar(
        centers - bar_width / 2,
        nj_pct,
        width=bar_width,
        color="black",
        edgecolor="black",
        linewidth=0.5,
        label="New Jersey"
    )

    # ------------------------------------------------------
    # Pennsylvania: hatched bars
    # ------------------------------------------------------

    ax.bar(
        centers + bar_width / 2,
        pa_pct,
        width=bar_width,
        color="white",
        edgecolor="black",
        linewidth=0.5,
        hatch="////",
        label="Pennsylvania"
    )

    # ------------------------------------------------------
    # Formatting
    # ------------------------------------------------------

    ax.set_title(
        period,
        fontsize=13
    )

    ax.set_ylabel(
        "Percent of Stores",
        fontsize=11
    )

    ax.grid(
        axis="y",
        alpha=0.15
    )

    ax.set_axisbelow(True)

    # Match the original figure's approximate
    # vertical axis ranges.
    if period == "February 1992":
        ax.set_ylim(0, 35)
        ax.set_yticks(np.arange(0, 36, 5))
    else:
        ax.set_ylim(0, 100)
        ax.set_yticks(np.arange(0, 101, 10))

    # ------------------------------------------------------
    # Print validation information
    # ------------------------------------------------------

    print(f"\n========== {period} ==========")

    print(
        "NJ valid wage observations:",
        len(nj)
    )

    print(
        "PA valid wage observations:",
        len(pa)
    )

    print(
        "NJ observations outside plotted range:",
        len(nj) - nj_counts.sum()
    )

    print(
        "PA observations outside plotted range:",
        len(pa) - pa_counts.sum()
    )

    # Print percentages at important wage rates
    for wage in [4.25, 5.05]:

        index = np.argmin(
            np.abs(centers - wage)
        )

        print(
            f"Wage range centered at ${wage:.2f}: "
            f"NJ = {nj_pct[index]:.2f}%, "
            f"PA = {pa_pct[index]:.2f}%"
        )

# ----------------------------------------------------------
# 4.4 Format x-axis and legend
# ----------------------------------------------------------

for ax in axes:

    ax.set_xticks(centers)

    ax.set_xlim(
        4.18,
        5.62
    )

    ax.set_xlabel(
        "Wage Range ($ per hour)",
        fontsize=11
    )

    ax.tick_params(
        axis="x",
        labelbottom=True
    )

    ax.set_xticklabels(
        [f"{x:.2f}" for x in centers],
        rotation=45,
        fontsize=8
    )

# Shared legend
handles, labels = axes[0].get_legend_handles_labels()

fig.legend(
    handles,
    labels,
    loc="lower center",
    ncol=2,
    frameon=False,
    bbox_to_anchor=(0.5, 0.005)
)

fig.suptitle(
    "Figure 1: Distribution of Starting Wage Rates",
    fontsize=15,
    y=0.99
)

fig.tight_layout(
    rect=[0, 0.055, 1, 0.965]
)

# ----------------------------------------------------------
# 4.5 Save Figure 1
# ----------------------------------------------------------

figure_dir = ROOT / "outputs" / "figures"

figure_dir.mkdir(
    parents=True,
    exist_ok=True
)

png_path = figure_dir / "figure1_replication.png"
pdf_path = figure_dir / "figure1_replication.pdf"

fig.savefig(
    png_path,
    dpi=300,
    bbox_inches="tight"
)

fig.savefig(
    pdf_path,
    bbox_inches="tight"
)

plt.close(fig)

print("\n========== FIGURE 1 COMPLETED ==========")

print("Saved:", png_path)
print("Saved:", pdf_path)

# ==========================================================
# 4.6 SAVE PROCESSED DATA FOR FIGURE 1
# ==========================================================

# Create processed data directory
figure1_processed_dir = ROOT / "data" / "processed"

figure1_processed_dir.mkdir(
    parents=True,
    exist_ok=True
)

# ----------------------------------------------------------
# A. Save store-level wage data
# ----------------------------------------------------------

figure1_analysis = df[
    ["STATE", "WAGE_ST", "WAGE_ST2"]
].copy()

figure1_analysis.to_csv(
    figure1_processed_dir / "figure1_analysis.csv",
    index=False
)

# ----------------------------------------------------------
# B. Save wage distribution used in Figure 1
# ----------------------------------------------------------

distribution_results = []

periods_processed = [
    ("February 1992", "WAGE_ST"),
    ("November 1992", "WAGE_ST2")
]

for period, wage_col in periods_processed:

    for state_code, state_name in [
        (1, "New Jersey"),
        (0, "Pennsylvania")
    ]:

        wages = pd.to_numeric(
            df.loc[df["STATE"] == state_code, wage_col],
            errors="coerce"
        ).dropna()

        counts, _ = np.histogram(
            wages,
            bins=bins
        )

        total_valid = len(wages)

        if total_valid > 0:
            percentages = (
                counts / total_valid * 100
            )
        else:
            percentages = np.full(
                len(counts), np.nan
            )

        for i, center in enumerate(centers):

            distribution_results.append({
                "Period": period,
                "State": state_name,
                "Wage_Center": center,
                "Bin_Lower": bins[i],
                "Bin_Upper": bins[i + 1],
                "Count": int(counts[i]),
                "Percent": percentages[i],
                "Total_Valid_Wages": total_valid
            })

figure1_distribution = pd.DataFrame(
    distribution_results
)

figure1_distribution.to_csv(
    figure1_processed_dir / "figure1_wage_distribution.csv",
    index=False
)

# ----------------------------------------------------------
# C. Validation
# ----------------------------------------------------------

print("\n========== FIGURE 1 PROCESSED DATA ==========")

print("Store-level observations:",
      len(figure1_analysis))

print("Distribution rows:",
      len(figure1_distribution))

print("\nSaved: data/processed/figure1_analysis.csv")

print(
    "Saved: data/processed/figure1_wage_distribution.csv"
)

print("\n========== FIGURE 1 DATA SAVED ==========")

# ==========================================================
# STEP 5: TABLE 3 REPLICATION
# Card & Krueger (1994), Table 3, p. 780
# Employment Before and After Minimum Wage Increase
# ==========================================================

import numpy as np
import pandas as pd

# ----------------------------------------------------------
# 5.1 Prepare data
# ----------------------------------------------------------

t3 = df.copy()

required_t3 = [
    "STATE", "WAGE_ST", "STATUS2",
    "FTE1", "FTE2"
]

missing_t3 = [
    col for col in required_t3
    if col not in t3.columns
]

if missing_t3:
    raise ValueError(
        f"Missing columns: {missing_t3}"
    )

for col in required_t3:
    t3[col] = pd.to_numeric(
        t3[col], errors="coerce"
    )

# ----------------------------------------------------------
# 5.2 Wage groups based on Wave 1
# ----------------------------------------------------------

t3["WAGE_GROUP"] = pd.Series(
    pd.NA, index=t3.index, dtype="object"
)

nj = t3["STATE"] == 1

t3.loc[
    nj & np.isclose(
        t3["WAGE_ST"].fillna(-999), 4.25
    ),
    "WAGE_GROUP"
] = "Low"

t3.loc[
    nj &
    (t3["WAGE_ST"] > 4.25) &
    (t3["WAGE_ST"] < 5.00),
    "WAGE_GROUP"
] = "Midrange"

t3.loc[
    nj & (t3["WAGE_ST"] >= 5.00),
    "WAGE_GROUP"
] = "High"

print("\n========== WAGE GROUP CHECK ==========")
print(
    t3.loc[nj, "WAGE_GROUP"]
    .value_counts(dropna=False)
)

# ----------------------------------------------------------
# 5.3 Closure classification
# ----------------------------------------------------------

# STATUS2:
# 0 = refused
# 1 = answered
# 2 = renovation closure
# 3 = permanent closure
# 4 = highway-construction closure
# 5 = mall-fire closure

temporary = t3["STATUS2"].isin([2, 4, 5])
permanent = t3["STATUS2"] == 3

print("\n========== CLOSURE CHECK ==========")
print(t3["STATUS2"].value_counts().sort_index())

# Use original Wave 2 FTE for responding stores.
# Assign zero to permanently closed stores.
# Temporary closures remain missing.

t3["FTE2_BASE"] = t3["FTE2"].copy()

t3.loc[permanent, "FTE2_BASE"] = 0.0
t3.loc[temporary, "FTE2_BASE"] = np.nan

# ----------------------------------------------------------
# 5.4 Employment change definitions
# ----------------------------------------------------------

# ROW 3:
# Difference between group-level Wave 2 and Wave 1
# means using all available observations.
# This may use different samples across waves.

# ROW 4:
# Paired sample with valid Wave 1 and Wave 2 employment.
# Temporary closures are excluded.
# Permanent closures with employment = 0 are retained.

balanced = (
    t3["FTE1"].notna()
    & t3["FTE2_BASE"].notna()
)

t3["CHANGE_ROW4"] = (
    t3["FTE2_BASE"] - t3["FTE1"]
).where(balanced)

# ROW 5:
# Treat temporarily closed stores as zero.
# Keep permanent closures at zero.

t3["FTE2_ZERO_TEMP"] = t3["FTE2_BASE"].copy()

t3.loc[temporary, "FTE2_ZERO_TEMP"] = 0.0

t3["CHANGE_ROW5"] = (
    t3["FTE2_ZERO_TEMP"] - t3["FTE1"]
)

# ----------------------------------------------------------
# 5.5 Statistical functions
# ----------------------------------------------------------

def mean_se(x):
    x = pd.to_numeric(x, errors="coerce").dropna()
    n = len(x)

    if n == 0:
        return np.nan, np.nan, 0

    mean = x.mean()
    se = x.sem() if n > 1 else np.nan

    return mean, se, n


def diff_se(a, b):

    a = pd.to_numeric(a, errors="coerce").dropna()
    b = pd.to_numeric(b, errors="coerce").dropna()

    if len(a) < 2 or len(b) < 2:
        return np.nan, np.nan

    diff = a.mean() - b.mean()

    se = np.sqrt(
        a.var(ddof=1) / len(a)
        + b.var(ddof=1) / len(b)
    )

    return diff, se


# ----------------------------------------------------------
# 5.6 Group definitions
# ----------------------------------------------------------

groups = {
    "PA": t3["STATE"] == 0,
    "NJ": t3["STATE"] == 1,
    "Low": t3["WAGE_GROUP"] == "Low",
    "Midrange": t3["WAGE_GROUP"] == "Midrange",
    "High": t3["WAGE_GROUP"] == "High"
}

# ----------------------------------------------------------
# 5.7 Construct Table 3
# ----------------------------------------------------------

rows = []

row_definitions = [
    ("1. FTE before", "FTE1"),
    ("2. FTE after", "FTE2_BASE"),
    ("4. Balanced sample change", "CHANGE_ROW4"),
    ("5. Temporary closures = 0", "CHANGE_ROW5")
]

for label, variable in row_definitions:

    result = {"Variable": label}

    for group_name, mask in groups.items():

        mean, se, n = mean_se(
            t3.loc[mask, variable]
        )

        result[group_name] = mean
        result[group_name + "_SE"] = se
        result[group_name + "_N"] = n

    # Group differences and their standard errors
    for name, a, b in [
        ("NJ_minus_PA", "NJ", "PA"),
        ("Low_minus_High", "Low", "High"),
        ("Mid_minus_High", "Midrange", "High")
    ]:

        diff, se = diff_se(
            t3.loc[groups[a], variable],
            t3.loc[groups[b], variable]
        )

        result[name] = diff
        result[name + "_SE"] = se

    rows.append(result)

# ----------------------------------------------------------
# 5.8 Row 3: Change in group means
# ----------------------------------------------------------

row1 = rows[0]
row2 = rows[1]

row3 = {"Variable": "3. Change in mean FTE"}

for group in groups:

    row3[group] = row2[group] - row1[group]

    # Approximation for difference in means
    # based on two cross-sectional standard errors.
    # This ignores within-store covariance.
    row3[group + "_SE"] = np.sqrt(
        row1[group + "_SE"] ** 2
        + row2[group + "_SE"] ** 2
    )

    row3[group + "_N"] = np.nan

for name, a, b in [
    ("NJ_minus_PA", "NJ", "PA"),
    ("Low_minus_High", "Low", "High"),
    ("Mid_minus_High", "Midrange", "High")
]:

    row3[name] = row3[a] - row3[b]

    row3[name + "_SE"] = np.sqrt(
        row3[a + "_SE"] ** 2
        + row3[b + "_SE"] ** 2
    )

rows.insert(2, row3)

table3 = pd.DataFrame(rows)

# ----------------------------------------------------------
# 5.9 Original Table 3 values
# ----------------------------------------------------------

original_values = [
    [23.33, 20.44, -2.89, 19.56, 20.08, 22.25, -2.69, -2.17],
    [21.17, 21.03, -0.14, 20.88, 20.96, 20.21, 0.67, 0.75],
    [-2.16, 0.59, 2.76, 1.32, 0.87, -2.04, 3.36, 2.91],
    [-2.28, 0.47, 2.75, 1.21, 0.71, -2.16, 3.36, 2.87],
    [-2.28, 0.23, 2.51, 0.90, 0.49, -2.39, 3.29, 2.88]
]

comparison_cols = [
    "PA", "NJ", "NJ_minus_PA",
    "Low", "Midrange", "High",
    "Low_minus_High", "Mid_minus_High"
]

original = pd.DataFrame(
    original_values,
    columns=comparison_cols
)

original.insert(
    0, "Variable", table3["Variable"].values
)

# ----------------------------------------------------------
# 5.10 Compare with original
# ----------------------------------------------------------

comparison = table3[
    ["Variable"] + comparison_cols
].copy()

for col in comparison_cols:

    comparison["Original_" + col] = original[col]

    comparison["Difference_" + col] = (
        comparison[col] - original[col]
    )

# ----------------------------------------------------------
# 5.11 Save outputs
# ----------------------------------------------------------

output_dir_t3 = ROOT / "outputs" / "tables"
output_dir_t3.mkdir(parents=True, exist_ok=True)

table3.to_csv(
    output_dir_t3 / "table3_replication.csv",
    index=False
)

comparison.to_csv(
    output_dir_t3 / "table3_comparison.csv",
    index=False
)

sample_cols = [
    "Variable",
    "PA_N", "NJ_N",
    "Low_N", "Midrange_N", "High_N"
]

table3[sample_cols].to_csv(
    output_dir_t3 / "table3_sample_sizes.csv",
    index=False
)

# ----------------------------------------------------------
# 5.12 Diagnostics
# ----------------------------------------------------------

print("\n========== TABLE 3 REPLICATION ==========")

print(
    table3[
        ["Variable"] + comparison_cols
    ].round(3).to_string(index=False)
)

print("\n========== TABLE 3 SAMPLE SIZES ==========")

print(
    table3[sample_cols].to_string(index=False)
)

print("\n========== TABLE 3 COMPARISON ==========")

print(
    comparison.round(3).to_string(index=False)
)

print("\n========== CLOSURE DIAGNOSTICS ==========")

for status in sorted(t3["STATUS2"].dropna().unique()):

    sub = t3[t3["STATUS2"] == status]

    print(f"\nSTATUS2 = {int(status)}")
    print("Stores:", len(sub))
    print("Valid FTE1:", sub["FTE1"].notna().sum())
    print("Valid FTE2:", sub["FTE2"].notna().sum())
    print("Valid FTE2_BASE:", sub["FTE2_BASE"].notna().sum())

print("\n========== TABLE 3 COMPLETED ==========")
print("Saved: outputs/tables/table3_replication.csv")
print("Saved: outputs/tables/table3_comparison.csv")
print("Saved: outputs/tables/table3_sample_sizes.csv")

# ==========================================================
# 5.13 SAVE PROCESSED DATA FOR TABLE 3
# ==========================================================

# Create processed data directory
table3_processed_dir = ROOT / "data" / "processed"

table3_processed_dir.mkdir(
    parents=True,
    exist_ok=True
)

# Select variables used in Table 3
table3_columns = [
    # Restaurant location and wage classification
    "STATE",
    "WAGE_ST",
    "WAGE_GROUP",

    # Restaurant status in Wave 2
    "STATUS2",

    # Employment before and after
    "FTE1",
    "FTE2",

    # Baseline employment after closure adjustment
    "FTE2_BASE",

    # Balanced-sample employment change
    "CHANGE_ROW4",

    # Employment after temporary-closure adjustment
    "FTE2_ZERO_TEMP",

    # Employment change with temporary closures set to zero
    "CHANGE_ROW5"
]

# Create processed dataset
table3_processed = t3[table3_columns].copy()

# Save processed data
table3_processed.to_csv(
    table3_processed_dir / "table3_analysis.csv",
    index=False
)

# Validation
print("\n========== TABLE 3 PROCESSED DATA SAVED ==========")

print("Saved: data/processed/table3_analysis.csv")
print("Number of observations:", len(table3_processed))
print("Number of variables:", len(table3_processed.columns))

print("\nWage group distribution:")
print(
    table3_processed["WAGE_GROUP"]
    .value_counts(dropna=False)
)


# ==========================================================
# STEP 6: TABLE 4 REPLICATION
# Card & Krueger (1994)
# Reduced-Form Models for Change in Employment
# ==========================================================

from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm

# ==========================================================
# 6.1 LOAD ORIGINAL DATA
# ==========================================================

ROOT_T4 = Path(__file__).resolve().parents[1]
DATA_PATH_T4 = ROOT_T4 / "data" / "raw" / "public.csv"

t4 = pd.read_csv(DATA_PATH_T4)

required = [
    "STATE", "CHAIN", "CO_OWNED", "STATUS2",
    "WAGE_ST", "WAGE_ST2",
    "EMPFT", "EMPPT", "NMGRS",
    "EMPFT2", "EMPPT2", "NMGRS2",
    "SOUTHJ", "CENTRALJ", "PA1", "PA2"
]

missing = [c for c in required if c not in t4.columns]

if missing:
    raise ValueError(f"Missing columns: {missing}")

for col in required:
    t4[col] = pd.to_numeric(t4[col], errors="coerce")

print("\n========== STEP 6: TABLE 4 ==========")
print("Raw observations:", len(t4))


# ==========================================================
# 6.2 CONSTRUCT FTE EMPLOYMENT
# ==========================================================

# FTE = Full-time + Managers + 0.5 * Part-time

t4["FTE1_T4"] = (
    t4["EMPFT"]
    + t4["NMGRS"]
    + 0.5 * t4["EMPPT"]
)

t4["FTE2_T4"] = (
    t4["EMPFT2"]
    + t4["NMGRS2"]
    + 0.5 * t4["EMPPT2"]
)

# Permanent closures: employment = 0
permanent = t4["STATUS2"] == 3

# Temporary closures: missing in baseline
temporary = t4["STATUS2"].isin([2, 4, 5])

t4.loc[permanent, "FTE2_T4"] = 0.0
t4.loc[temporary, "FTE2_T4"] = np.nan

# Employment change
t4["DELTA_FTE_T4"] = (
    t4["FTE2_T4"] - t4["FTE1_T4"]
)


# ==========================================================
# 6.3 CONSTRUCT INITIAL WAGE GAP
# ==========================================================

# Proportional increase needed to reach $5.05.
# PA stores have wage gap = 0.

t4["WAGE_GAP"] = np.nan

t4.loc[t4["STATE"] == 0, "WAGE_GAP"] = 0.0

nj_valid = (
    (t4["STATE"] == 1)
    & t4["WAGE_ST"].notna()
    & (t4["WAGE_ST"] > 0)
)

t4.loc[nj_valid, "WAGE_GAP"] = (
    (5.05 - t4.loc[nj_valid, "WAGE_ST"])
    .clip(lower=0)
    / t4.loc[nj_valid, "WAGE_ST"]
)


# ==========================================================
# 6.4 CHAIN AND OWNERSHIP CONTROLS
# ==========================================================

# Burger King is the omitted reference category.

for chain_id, name in [
    (2, "KFC"),
    (3, "ROY"),
    (4, "WENDYS")
]:
    t4[name] = np.where(
        t4["CHAIN"].notna(),
        (t4["CHAIN"] == chain_id).astype(float),
        np.nan
    )

t4["OWNED"] = t4["CO_OWNED"]

chain_controls = [
    "KFC", "ROY", "WENDYS", "OWNED"
]


# ==========================================================
# 6.5 REGIONAL CONTROLS
# ==========================================================

region_controls = [
    "SOUTHJ", "CENTRALJ", "PA1", "PA2"
]


# ==========================================================
# 6.6 CONSTRUCT REPLICATION SAMPLE
# ==========================================================

# Require valid employment change and Wave 1 wage.
base_mask = (
    t4["DELTA_FTE_T4"].notna()
    & t4["WAGE_ST"].notna()
    & (t4["WAGE_ST"] > 0)
)

# Valid Wave 2 starting wage
valid_wage2 = (
    t4["WAGE_ST2"].notna()
    & (t4["WAGE_ST2"] > 0)
)

# Candidate sample:
# Valid Wave 2 wage OR permanently closed store.
candidate_mask = (
    base_mask
    & (valid_wage2 | permanent)
)

all_controls = (
    ["STATE", "WAGE_GAP"]
    + chain_controls
    + region_controls
)

sample = t4.loc[candidate_mask].dropna(
    subset=all_controls
).copy()

print("\n========== TABLE 4 SAMPLE CONSTRUCTION ==========")

print("Valid employment + Wave 1 wage:",
      int(base_mask.sum()))

print("Valid Wave 2 wage:",
      int((base_mask & valid_wage2).sum()))

print("Permanent closures added:",
      int((base_mask & permanent & ~valid_wage2).sum()))

print("Final sample:", len(sample))


# ==========================================================
# 6.7 SAMPLE VALIDATION
# ==========================================================

sample_n = len(sample)

sample_mean = sample["DELTA_FTE_T4"].mean()

sample_sd = sample["DELTA_FTE_T4"].std(ddof=1)

print("\n========== TABLE 4 SAMPLE VALIDATION ==========")

print(f"Replication N: {sample_n}")
print("Original N: 357")

print(f"Replication mean: {sample_mean:.4f}")
print("Original mean: -0.237")

print(f"Replication SD: {sample_sd:.4f}")
print("Original SD: 8.825")

sample_validation = pd.DataFrame({
    "Statistic": [
        "Sample size",
        "Mean change in FTE",
        "SD of change in FTE"
    ],
    "Replication": [
        sample_n, sample_mean, sample_sd
    ],
    "Original": [
        357, -0.237, 8.825
    ]
})

sample_validation["Difference"] = (
    sample_validation["Replication"]
    - sample_validation["Original"]
)

if sample_n != 357:
    print("WARNING: Sample size differs from original.")


# ==========================================================
# 6.8 RUN FIVE OLS MODELS
# ==========================================================

specifications = [
    ("i", "STATE", []),

    ("ii", "STATE", chain_controls),

    ("iii", "WAGE_GAP", []),

    ("iv", "WAGE_GAP", chain_controls),

    (
        "v",
        "WAGE_GAP",
        chain_controls + region_controls
    )
]

results = []
models = {}

for name, main_var, controls in specifications:

    X = sample[
        [main_var] + controls
    ].astype(float)

    X = sm.add_constant(
        X, has_constant="add"
    )

    y = sample["DELTA_FTE_T4"].astype(float)

    model = sm.OLS(y, X).fit()

    models[name] = model

    # Joint F-test for included controls
    if controls:

        hypotheses = [
            f"{c} = 0" for c in controls
        ]

        f_test = model.f_test(hypotheses)

        p_control = float(f_test.pvalue)

    else:
        p_control = np.nan

    results.append({
        "Model": name,
        "Main_variable": main_var,
        "Coefficient": model.params[main_var],
        "Standard_Error": model.bse[main_var],
        "SER": np.sqrt(model.mse_resid),
        "Control_F_pvalue": p_control,
        "N": int(model.nobs),
        "R_squared": model.rsquared
    })

table4 = pd.DataFrame(results).set_index("Model")


# ==========================================================
# 6.9 ORIGINAL PAPER VALUES
# ==========================================================

original = pd.DataFrame({
    "Model": ["i", "ii", "iii", "iv", "v"],

    "Coefficient": [
        2.33, 2.30, 15.65, 14.92, 11.91
    ],

    "Standard_Error": [
        1.19, 1.20, 6.08, 6.21, 7.39
    ],

    "SER": [
        8.79, 8.78, 8.76, 8.76, 8.75
    ],

    "Control_F_pvalue": [
        np.nan, 0.34, np.nan, 0.44, 0.40
    ],

    "N": [357] * 5
}).set_index("Model")


# ==========================================================
# 6.10 FORMAT TABLES LIKE ORIGINAL PAPER
# ==========================================================

model_ids = ["i", "ii", "iii", "iv", "v"]

model_columns = [
    "(i)", "(ii)", "(iii)", "(iv)", "(v)"
]

def fmt(value, parentheses=False):

    if pd.isna(value):
        return "—"

    text = f"{value:.2f}"

    if parentheses:
        return f"({text})"

    return text


def build_paper_table(source):

    rows = [
        [
            "1. New Jersey dummy",
            fmt(source.loc["i", "Coefficient"]),
            fmt(source.loc["ii", "Coefficient"]),
            "—", "—", "—"
        ],

        [
            "   Standard error",
            fmt(source.loc["i", "Standard_Error"], True),
            fmt(source.loc["ii", "Standard_Error"], True),
            "—", "—", "—"
        ],

        [
            "2. Initial wage gap",
            "—", "—",
            fmt(source.loc["iii", "Coefficient"]),
            fmt(source.loc["iv", "Coefficient"]),
            fmt(source.loc["v", "Coefficient"])
        ],

        [
            "   Standard error",
            "—", "—",
            fmt(source.loc["iii", "Standard_Error"], True),
            fmt(source.loc["iv", "Standard_Error"], True),
            fmt(source.loc["v", "Standard_Error"], True)
        ],

        [
            "3. Controls for chain and ownership",
            "no", "yes", "no", "yes", "yes"
        ],

        [
            "4. Controls for region",
            "no", "no", "no", "no", "yes"
        ],

        [
            "5. Standard error of regression"
        ] + [
            fmt(source.loc[m, "SER"])
            for m in model_ids
        ],

        [
            "6. Probability value for controls"
        ] + [
            fmt(source.loc[m, "Control_F_pvalue"])
            for m in model_ids
        ],

        [
            "Number of observations"
        ] + [
            str(int(source.loc[m, "N"]))
            for m in model_ids
        ]
    ]

    return pd.DataFrame(
        rows,
        columns=[
            "Independent variable"
        ] + model_columns
    )


replication_formatted = build_paper_table(table4)

original_formatted = build_paper_table(original)


# ==========================================================
# 6.11 COMPARISON WITH ORIGINAL PAPER
# ==========================================================

# A. Numerical comparison of all statistics

comparison = table4.copy()

for col in [
    "Coefficient",
    "Standard_Error",
    "SER",
    "Control_F_pvalue"
]:

    comparison["Original_" + col] = original[col]

    comparison["Difference_" + col] = (
        comparison[col] - original[col]
    )

# B. Main coefficient comparison

coefficient_comparison = pd.DataFrame({
    "Model": model_columns,

    "Variable": [
        "New Jersey dummy",
        "New Jersey dummy",
        "Initial wage gap",
        "Initial wage gap",
        "Initial wage gap"
    ],

    "Original": [
        original.loc[m, "Coefficient"]
        for m in model_ids
    ],

    "Replication": [
        table4.loc[m, "Coefficient"]
        for m in model_ids
    ]
})

coefficient_comparison["Difference"] = (
    coefficient_comparison["Replication"]
    - coefficient_comparison["Original"]
)

# C. Full comparison in original paper layout

full_comparison = pd.DataFrame({
    "Independent variable":
        replication_formatted["Independent variable"]
})

for model in model_columns:

    full_comparison[f"{model} Replication"] = (
        replication_formatted[model]
    )

    full_comparison[f"{model} Original"] = (
        original_formatted[model]
    )


# ==========================================================
# 6.12 SAVE AND PRINT ALL RESULTS
# ==========================================================

output_dir = ROOT_T4 / "outputs" / "tables"

output_dir.mkdir(
    parents=True, exist_ok=True
)

# Save full numerical results
table4.reset_index().to_csv(
    output_dir / "table4_replication.csv",
    index=False
)

# Save numerical comparison
comparison.reset_index().to_csv(
    output_dir / "table4_comparison.csv",
    index=False
)

# Save formatted replication table
replication_formatted.to_csv(
    output_dir / "table4_formatted.csv",
    index=False,
    encoding="utf-8-sig"
)

# Save original paper table
original_formatted.to_csv(
    output_dir / "table4_original_formatted.csv",
    index=False,
    encoding="utf-8-sig"
)

# Save main coefficient comparison
coefficient_comparison.to_csv(
    output_dir / "table4_coefficient_comparison.csv",
    index=False,
    encoding="utf-8-sig"
)

# Save full comparison
full_comparison.to_csv(
    output_dir / "table4_full_comparison.csv",
    index=False,
    encoding="utf-8-sig"
)

# Save sample validation
sample_validation.to_csv(
    output_dir / "table4_sample_validation.csv",
    index=False
)

# Save sample audit
sample[[
    "STATE", "STATUS2",
    "WAGE_ST", "WAGE_ST2",
    "FTE1_T4", "FTE2_T4",
    "DELTA_FTE_T4", "WAGE_GAP"
]].to_csv(
    output_dir / "table4_sample_audit.csv",
    index=True,
    index_label="Original_Row_Index"
)

# Save detailed OLS regression outputs
with open(
    output_dir / "table4_regression_details.txt",
    "w",
    encoding="utf-8"
) as file:

    for name, model in models.items():

        file.write(
            f"\n========== MODEL {name} ==========\n"
        )

        file.write(model.summary().as_text())

        file.write("\n\n")

# Print tables
print("\n========== TABLE 4: REPLICATION ==========")

print(
    replication_formatted.to_string(index=False)
)

print("\n========== TABLE 4: ORIGINAL PAPER ==========")

print(
    original_formatted.to_string(index=False)
)

print("\n========== TABLE 4: COEFFICIENT COMPARISON ==========")

print(
    coefficient_comparison.round(4).to_string(index=False)
)

print("\n========== TABLE 4: FULL COMPARISON ==========")

print(
    full_comparison.to_string(index=False)
)

print("\n========== TABLE 4 COMPLETED ==========")

print("Saved: outputs/tables/table4_replication.csv")
print("Saved: outputs/tables/table4_comparison.csv")
print("Saved: outputs/tables/table4_formatted.csv")
print("Saved: outputs/tables/table4_original_formatted.csv")
print("Saved: outputs/tables/table4_coefficient_comparison.csv")
print("Saved: outputs/tables/table4_full_comparison.csv")
print("Saved: outputs/tables/table4_sample_validation.csv")
print("Saved: outputs/tables/table4_sample_audit.csv")
print("Saved: outputs/tables/table4_regression_details.txt")

# ==========================================================
# 6.13 SAVE PROCESSED DATA FOR TABLE 4
# ==========================================================

# Create processed data directory
table4_processed_dir = ROOT_T4 / "data" / "processed"

table4_processed_dir.mkdir(
    parents=True,
    exist_ok=True
)

# Select variables used in Table 4
table4_columns = [
    # Restaurant information
    "STATE",
    "STATUS2",
    "CHAIN",
    "CO_OWNED",

    # Starting wages
    "WAGE_ST",
    "WAGE_ST2",

    # Employment variables
    "FTE1_T4",
    "FTE2_T4",
    "DELTA_FTE_T4",

    # Initial wage gap
    "WAGE_GAP",

    # Chain and ownership controls
    "KFC",
    "ROY",
    "WENDYS",
    "OWNED",

    # Regional controls
    "SOUTHJ",
    "CENTRALJ",
    "PA1",
    "PA2"
]

# Save the exact regression sample
table4_processed = sample[table4_columns].copy()

# Preserve original row identifiers for auditing
table4_processed.insert(
    0,
    "Original_Row_Index",
    sample.index
)

# Export processed data
table4_processed.to_csv(
    table4_processed_dir / "table4_analysis.csv",
    index=False
)

# Validation
print("\n========== TABLE 4 PROCESSED DATA SAVED ==========")

print("Saved: data/processed/table4_analysis.csv")
print("Number of observations:", len(table4_processed))
print("Number of variables:", len(table4_processed.columns))

print("\nRestaurants by state:")
print(table4_processed["STATE"].value_counts().sort_index())

print("\nRestaurants by closure status:")
print(table4_processed["STATUS2"].value_counts().sort_index())

print("\nMissing values in regression variables:")
print(
    table4_processed[
        ["DELTA_FTE_T4", "STATE", "WAGE_GAP"]
        + chain_controls
        + region_controls
    ].isna().sum()
)


# ==========================================================
# STEP 7: INDEPENDENT EXTENSION
# Chain-Level Heterogeneity Analysis
# ==========================================================

# ----------------------------------------------------------
# 7.1 Data preparation and sample diagnostics
# ----------------------------------------------------------

import pandas as pd
from pathlib import Path

ROOT_EXT = Path(__file__).resolve().parents[1]

# Load processed Table 4 regression sample
extension = pd.read_csv(
    ROOT_EXT / "data" / "processed" / "table4_analysis.csv"
)

# Restaurant chain names
chain_names = {
    1: "Burger King",
    2: "KFC",
    3: "Roy Rogers",
    4: "Wendy's"
}

extension["CHAIN_NAME"] = (
    extension["CHAIN"].map(chain_names)
)

extension["STATE_NAME"] = (
    extension["STATE"].map({
        1: "New Jersey",
        0: "Pennsylvania"
    })
)

# Check missing observations
print("\n========== EXTENSION: DATA VALIDATION ==========")

print("Total observations:", len(extension))

print("\nMissing values:")
print(
    extension[
        ["STATE", "CHAIN", "DELTA_FTE_T4"]
    ].isna().sum()
)

# Count restaurants by chain and state
chain_counts = pd.crosstab(
    extension["CHAIN_NAME"],
    extension["STATE_NAME"]
)

print("\n========== RESTAURANTS BY CHAIN AND STATE ==========")
print(chain_counts)

# Mean employment change by chain and state
chain_means = extension.pivot_table(
    index="CHAIN_NAME",
    columns="STATE_NAME",
    values="DELTA_FTE_T4",
    aggfunc="mean"
)

print("\n========== MEAN EMPLOYMENT CHANGE ==========")
print(chain_means.round(3))

# NJ - PA difference for each chain
chain_means["NJ_minus_PA"] = (
    chain_means["New Jersey"]
    - chain_means["Pennsylvania"]
)

print("\n========== NJ - PA EMPLOYMENT DIFFERENCES ==========")
print(chain_means.round(3))

# Save outputs
extension_output = ROOT_EXT / "outputs" / "tables"
extension_output.mkdir(parents=True, exist_ok=True)

chain_counts.to_csv(
    extension_output / "extension_chain_sample_sizes.csv"
)

chain_means.to_csv(
    extension_output / "extension_chain_descriptive.csv"
)

print("\n========== STEP 7.1 COMPLETED ==========")
print("Saved: outputs/tables/extension_chain_sample_sizes.csv")
print("Saved: outputs/tables/extension_chain_descriptive.csv")


# ==========================================================
# STEP 7.2 - 7.4: CHAIN HETEROGENEITY REGRESSION
# ==========================================================

import numpy as np
import pandas as pd
import statsmodels.api as sm

# 7.2 Construct interaction terms
extension["NJ_KFC"] = extension["STATE"] * extension["KFC"]
extension["NJ_ROY"] = extension["STATE"] * extension["ROY"]
extension["NJ_WENDYS"] = extension["STATE"] * extension["WENDYS"]

# Burger King is the reference chain
regressors = [
    "STATE",
    "KFC", "ROY", "WENDYS",
    "NJ_KFC", "NJ_ROY", "NJ_WENDYS"
]

reg_data = extension[
    ["DELTA_FTE_T4"] + regressors
].dropna().copy()

# 7.3 Estimate OLS with heteroskedasticity-robust SE
X = sm.add_constant(
    reg_data[regressors].astype(float)
)
y = reg_data["DELTA_FTE_T4"].astype(float)

heterogeneity_model = sm.OLS(y, X).fit(cov_type="HC1")

print("\n========== EXTENSION: OLS REGRESSION ==========")
print(heterogeneity_model.summary())

# 7.4 Joint Wald test for all interaction terms
joint_test = heterogeneity_model.wald_test(
    "NJ_KFC = 0, NJ_ROY = 0, NJ_WENDYS = 0",
    scalar=True,
    use_f=True
)

joint_f = float(joint_test.statistic)
joint_p = float(joint_test.pvalue)

print("\n========== JOINT HETEROGENEITY TEST ==========")
print("H0: All three interaction coefficients equal zero")
print(f"Robust F-statistic: {joint_f:.4f}")
print(f"P-value: {joint_p:.4f}")

if joint_p < 0.05:
    print("Reject H0 at the 5% significance level.")
else:
    print("Do not reject H0 at the 5% significance level.")

# Chain-specific NJ-PA differences
linear_tests = {
    "Burger King": "STATE = 0",
    "KFC": "STATE + NJ_KFC = 0",
    "Roy Rogers": "STATE + NJ_ROY = 0",
    "Wendy's": "STATE + NJ_WENDYS = 0"
}

chain_effects = []

for chain, hypothesis in linear_tests.items():
    test = heterogeneity_model.t_test(hypothesis)
    ci = test.conf_int(alpha=0.05)[0]

    chain_effects.append({
        "Chain": chain,
        "NJ_minus_PA": float(test.effect.item()),
        "Robust_SE": float(test.sd.item()),
        "P_value": float(test.pvalue.item()),
        "CI_Lower": float(ci[0]),
        "CI_Upper": float(ci[1])
    })

effects_df = pd.DataFrame(chain_effects)

print("\n========== CHAIN-SPECIFIC EFFECTS ==========")
print(effects_df.round(4).to_string(index=False))

# Save results
extension_output.mkdir(parents=True, exist_ok=True)

effects_df.to_csv(
    extension_output / "extension_chain_effects.csv",
    index=False
)

with open(
    extension_output / "extension_regression_details.txt",
    "w",
    encoding="utf-8"
) as f:
    f.write(heterogeneity_model.summary().as_text())
    f.write("\n\nJOINT HETEROGENEITY TEST\n")
    f.write(f"Robust F-statistic: {joint_f:.6f}\n")
    f.write(f"P-value: {joint_p:.6f}\n")

print("\n========== STEP 7.4 COMPLETED ==========")
print("Saved: outputs/tables/extension_chain_effects.csv")
print("Saved: outputs/tables/extension_regression_details.txt")


# ==========================================================
# STEP 7.5: EXTENSION FIGURE
# Chain-specific NJ-PA Employment Differences
# ==========================================================

import matplotlib.pyplot as plt
import numpy as np

# Use estimated effects from Step 7.4
plot_data = effects_df.copy()

fig, ax = plt.subplots(figsize=(9, 5.5))

y_pos = np.arange(len(plot_data))

estimates = plot_data["NJ_minus_PA"].to_numpy()

lower_errors = (
    estimates - plot_data["CI_Lower"].to_numpy()
)

upper_errors = (
    plot_data["CI_Upper"].to_numpy() - estimates
)

# Plot estimates and 95% confidence intervals
ax.errorbar(
    estimates,
    y_pos,
    xerr=[lower_errors, upper_errors],
    fmt="o",
    color="black",
    ecolor="gray",
    elinewidth=1.5,
    capsize=5,
    markersize=7
)

# Zero reference line
ax.axvline(
    x=0,
    color="red",
    linestyle="--",
    linewidth=1.2,
    label="Zero effect"
)

ax.set_yticks(y_pos)
ax.set_yticklabels(plot_data["Chain"])

ax.invert_yaxis()

ax.set_xlabel(
    "NJ - PA Difference in Employment Change (FTE)"
)

ax.set_title(
    "Extension: Employment Responses Across Fast-Food Chains"
)

ax.grid(axis="x", alpha=0.2)
ax.set_axisbelow(True)

fig.text(
    0.5, 0.01,
    "Points represent estimated NJ-PA differences; "
    "bars show 95% HC1 robust confidence intervals.",
    ha="center",
    fontsize=9
)

fig.tight_layout(rect=[0, 0.05, 1, 1])

# Save figure
extension_figure_dir = ROOT_EXT / "outputs" / "figures"
extension_figure_dir.mkdir(parents=True, exist_ok=True)

fig.savefig(
    extension_figure_dir / "extension_chain_effects.png",
    dpi=300,
    bbox_inches="tight"
)

fig.savefig(
    extension_figure_dir / "extension_chain_effects.pdf",
    bbox_inches="tight"
)

plt.close(fig)

print("\n========== STEP 7.5 COMPLETED ==========")
print("Saved: outputs/figures/extension_chain_effects.png")
print("Saved: outputs/figures/extension_chain_effects.pdf")

# ==========================================================
# STEP 7.7: ROBUSTNESS CHECK
# Exclude permanently closed restaurants
# ==========================================================

import pandas as pd
import statsmodels.api as sm

# Baseline sample from Step 7
baseline_data = extension.copy()

# Exclude permanent closures (STATUS2 = 3)
robust_data = extension.loc[
    extension["STATUS2"] != 3
].copy()

print("\n========== ROBUSTNESS SAMPLE CHECK ==========")
print("Baseline N:", len(baseline_data))
print("Robustness N:", len(robust_data))
print("Permanent closures excluded:",
      len(baseline_data) - len(robust_data))

# Use the same explanatory variables as the baseline
regressors_robust = [
    "STATE",
    "KFC", "ROY", "WENDYS",
    "NJ_KFC", "NJ_ROY", "NJ_WENDYS"
]

# Ensure the regression sample is complete
robust_data = robust_data.dropna(
    subset=["DELTA_FTE_T4"] + regressors_robust
)

X_robust = sm.add_constant(
    robust_data[regressors_robust].astype(float)
)

y_robust = robust_data["DELTA_FTE_T4"].astype(float)

# Estimate OLS with HC1 robust standard errors
robust_model = sm.OLS(
    y_robust,
    X_robust
).fit(cov_type="HC1")

print("\n========== ROBUSTNESS REGRESSION ==========")
print(robust_model.summary())

# Joint heterogeneity test
robust_test = robust_model.wald_test(
    "NJ_KFC = 0, NJ_ROY = 0, NJ_WENDYS = 0",
    scalar=True,
    use_f=True
)

robust_f = float(robust_test.statistic)
robust_p = float(robust_test.pvalue)

print("\n========== ROBUSTNESS JOINT TEST ==========")
print(f"Robust F-statistic: {robust_f:.4f}")
print(f"P-value: {robust_p:.4f}")

# Compare baseline and robustness coefficients
comparison_rows = []

for variable in [
    "STATE", "NJ_KFC", "NJ_ROY", "NJ_WENDYS"
]:
    comparison_rows.append({
        "Variable": variable,
        "Baseline_Coefficient":
            heterogeneity_model.params[variable],
        "Robustness_Coefficient":
            robust_model.params[variable],
        "Baseline_SE":
            heterogeneity_model.bse[variable],
        "Robustness_SE":
            robust_model.bse[variable]
    })

robustness_comparison = pd.DataFrame(comparison_rows)

print("\n========== ROBUSTNESS COMPARISON ==========")
print(
    robustness_comparison.round(4).to_string(index=False)
)

print("\nBaseline joint p-value:", round(joint_p, 4))
print("Robustness joint p-value:", round(robust_p, 4))

# Save results
robustness_comparison.to_csv(
    extension_output / "extension_robustness.csv",
    index=False
)

with open(
    extension_output / "extension_robustness_details.txt",
    "w",
    encoding="utf-8"
) as f:
    f.write(robust_model.summary().as_text())
    f.write("\n\nJoint heterogeneity test\n")
    f.write(f"F-statistic: {robust_f:.6f}\n")
    f.write(f"P-value: {robust_p:.6f}\n")

print("\n========== STEP 7.7 COMPLETED ==========")
print("Saved: outputs/tables/extension_robustness.csv")
print("Saved: outputs/tables/extension_robustness_details.txt")
