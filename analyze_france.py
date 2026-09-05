"""Run descriptive, inferential and predictive analyses for the France pilot."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import statsmodels.formula.api as smf
from scipy.stats import norm
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.dummy import DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


DATA_PATH = Path("files/cleaned/fr_analysis.csv")
REPORT_DIR = Path("reports/france")
RANDOM_STATE = 42

TECH_COLUMNS = [
    "has_ai_ml", "has_data_analysis", "has_data_engineering", "has_software",
    "has_cloud_devops", "has_cybersecurity", "has_networks_systems",
]
SOFT_COLUMNS = [
    "has_soft_communication", "has_soft_teamwork", "has_soft_adaptability",
    "has_soft_problem_solving", "has_soft_creativity",
    "has_soft_initiative_responsibility", "has_soft_leadership",
    "has_soft_customer_interaction",
]


def extract_region(value: object) -> str:
    if pd.isna(value):
        return "missing"
    try:
        addresses = json.loads(str(value))
    except (TypeError, ValueError):
        return "missing"
    if not isinstance(addresses, list) or not addresses:
        return "missing"
    region = addresses[0].get("regionCode") if isinstance(addresses[0], dict) else None
    return str(region) if region else "missing"


def prepare_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, sep=";", low_memory=False)
    df["annual_salary"] = pd.to_numeric(df["annual_salary"], errors="coerce")
    df = df.loc[
        df["annual_salary"].gt(0) & df["salary.currency"].eq("EUR")
    ].copy()
    df["log_salary"] = np.log(df["annual_salary"])
    df["creation_year"] = pd.to_datetime(df["creationDate"], errors="coerce", utc=True).dt.year
    df["tech_soft_interaction"] = df["has_tech_skills"] * df["has_soft_skills"]

    occupation_frequency = df["isco_code"].value_counts(dropna=False)
    frequent_occupations = set(occupation_frequency[occupation_frequency.ge(100)].index)
    df["occupation_group"] = df["isco_code"].where(
        df["isco_code"].isin(frequent_occupations), "other_or_rare"
    ).fillna("missing")
    contract_frequency = df["profile_contractType"].value_counts(dropna=False)
    frequent_contracts = set(contract_frequency[contract_frequency.ge(100)].index)
    df["contract_group"] = df["profile_contractType"].where(
        df["profile_contractType"].isin(frequent_contracts), "other_or_rare"
    ).fillna("missing")
    df["schedule_group"] = df["profile_workSchedule"].fillna("missing")
    df["region_group"] = df["profile_addresses"].apply(extract_region)
    source_frequency = df["source"].value_counts(dropna=False)
    frequent_sources = set(source_frequency[source_frequency.ge(100)].index)
    df["source_group"] = df["source"].where(
        df["source"].isin(frequent_sources), "other_or_rare"
    ).fillna("missing")

    # The builder's primary flag already enforces category-level agreement
    # (title evidence OR ESCO-and-description evidence for the same category).
    df["strict_has_tech"] = df["has_tech_skills"].astype(int)
    df["strict_skill_mix"] = np.select(
        [
            df["strict_has_tech"].eq(1) & df["has_soft_skills"].eq(1),
            df["strict_has_tech"].eq(1),
            df["has_soft_skills"].eq(1),
        ],
        ["technical_and_soft", "technical_only", "soft_only"],
        default="neither",
    )
    df["broad_skill_mix"] = np.select(
        [
            df["broad_has_tech_skills"].eq(1) & df["has_soft_skills"].eq(1),
            df["broad_has_tech_skills"].eq(1),
            df["has_soft_skills"].eq(1),
        ],
        ["technical_and_soft", "technical_only", "soft_only"],
        default="neither",
    )
    return df


def salary_summary(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("skill_mix", observed=True)["annual_salary"]
        .agg(count="size", mean="mean", median="median", std="std")
        .assign(
            q25=df.groupby("skill_mix", observed=True)["annual_salary"].quantile(0.25),
            q75=df.groupby("skill_mix", observed=True)["annual_salary"].quantile(0.75),
        )
        .sort_index()
    )


def fit_clustered_ols(formula: str, df: pd.DataFrame):
    model = smf.ols(formula, data=df).fit()
    return model.get_robustcov_results(
        cov_type="cluster", groups=df.loc[model.model.data.row_labels, "occupation_group"]
    )


def tidy_terms(model, selected_terms: list[str], model_name: str) -> pd.DataFrame:
    names = model.model.exog_names
    table = pd.DataFrame({
        "term": names,
        "coefficient": model.params,
        "std_error": model.bse,
        "p_value": model.pvalues,
        "ci_low": model.conf_int()[:, 0],
        "ci_high": model.conf_int()[:, 1],
    })
    table = table.loc[table["term"].isin(selected_terms)].copy()
    table["percent_association"] = 100 * np.expm1(table["coefficient"])
    table["percent_ci_low"] = 100 * np.expm1(table["ci_low"])
    table["percent_ci_high"] = 100 * np.expm1(table["ci_high"])
    table.insert(0, "model", model_name)
    return table


def coefficient_contrast(model, first_term: str, second_term: str, name: str) -> pd.DataFrame:
    names = model.model.exog_names
    first_index, second_index = names.index(first_term), names.index(second_term)
    contrast = np.zeros(len(names))
    contrast[first_index] = 1
    contrast[second_index] = -1
    estimate = float(contrast @ model.params)
    variance = float(contrast @ model.cov_params() @ contrast)
    standard_error = variance ** 0.5
    z_value = estimate / standard_error
    p_value = 2 * norm.sf(abs(z_value))
    ci_low, ci_high = estimate - 1.96 * standard_error, estimate + 1.96 * standard_error
    return pd.DataFrame([{
        "contrast": name,
        "coefficient_difference": estimate,
        "std_error": standard_error,
        "p_value": p_value,
        "percent_difference": 100 * np.expm1(estimate),
        "percent_ci_low": 100 * np.expm1(ci_low),
        "percent_ci_high": 100 * np.expm1(ci_high),
    }])


def predictive_models(df: pd.DataFrame) -> pd.DataFrame:
    categorical_controls = [
        "occupation_group", "seniority", "contract_group", "schedule_group",
        "region_group", "source_group", "creation_year",
    ]
    skill_features = TECH_COLUMNS + SOFT_COLUMNS
    def ridge_pipeline(numeric_features: list[str], categorical_features: list[str]):
        transformer = ColumnTransformer([
            ("numeric", SimpleImputer(strategy="most_frequent"), numeric_features),
            ("categorical", Pipeline([
                ("imputer", SimpleImputer(strategy="most_frequent")),
                ("onehot", OneHotEncoder(handle_unknown="ignore")),
            ]), categorical_features),
        ])
        return TransformedTargetRegressor(
            regressor=Pipeline([
                ("features", transformer),
                ("ridge", Ridge(alpha=10.0)),
            ]),
            func=np.log,
            inverse_func=np.exp,
        )

    rows = []
    random_train, random_test = train_test_split(df, test_size=0.20, random_state=RANDOM_STATE)
    ordered = df.sort_values("creationDate")
    temporal_cut = int(len(ordered) * 0.80)
    splits = {
        "random_80_20": (random_train, random_test),
        "temporal_80_20": (ordered.iloc[:temporal_cut], ordered.iloc[temporal_cut:]),
    }
    for split_name, (train, test) in splits.items():
        specifications = {
            "median_baseline": DummyRegressor(strategy="median"),
            "skills_only_ridge": ridge_pipeline(skill_features, []),
            "controls_only_ridge": ridge_pipeline([], categorical_controls),
            "skills_and_controls_ridge": ridge_pipeline(skill_features, categorical_controls),
        }
        for name, estimator in specifications.items():
            features = skill_features + categorical_controls
            estimator.fit(train[features], train["annual_salary"])
            prediction = estimator.predict(test[features])
            rows.append({
                "split": split_name,
                "model": name,
                "train_n": len(train),
                "test_n": len(test),
                "mae_eur": mean_absolute_error(test["annual_salary"], prediction),
                "rmse_eur": mean_squared_error(test["annual_salary"], prediction) ** 0.5,
                "r2": r2_score(test["annual_salary"], prediction),
            })
    return pd.DataFrame(rows)


def save_figures(df: pd.DataFrame, category_summary: pd.DataFrame, coefficient_table: pd.DataFrame) -> None:
    sns.set_theme(style="whitegrid")

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    df["annual_salary"].clip(upper=df["annual_salary"].quantile(0.99)).hist(bins=40, ax=axes[0])
    axes[0].set(title="Annual salary (capped at 99th percentile)", xlabel="EUR", ylabel="Adverts")
    order = ["neither", "soft_only", "technical_only", "technical_and_soft"]
    plot_data = category_summary.reindex(order).reset_index()
    sns.barplot(data=plot_data, x="skill_mix", y="median", ax=axes[1], color="#3B82F6")
    axes[1].tick_params(axis="x", rotation=25)
    axes[1].set(title="Median salary by skill mix", xlabel="", ylabel="EUR")
    fig.tight_layout()
    fig.savefig(REPORT_DIR / "salary_overview.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    tech_prevalence = df[TECH_COLUMNS].mean().mul(100).sort_values()
    fig, ax = plt.subplots(figsize=(8, 5))
    tech_prevalence.plot.barh(ax=ax, color="#2563EB")
    ax.set(title="Prevalence of technical skill categories", xlabel="Percent of adverts", ylabel="")
    fig.tight_layout()
    fig.savefig(REPORT_DIR / "technical_skill_prevalence.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    adjusted = coefficient_table.loc[coefficient_table["model"].eq("adjusted_trimmed")].copy()
    adjusted = adjusted.sort_values("percent_association")
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.errorbar(
        adjusted["percent_association"], adjusted["term"],
        xerr=[
            adjusted["percent_association"] - adjusted["percent_ci_low"],
            adjusted["percent_ci_high"] - adjusted["percent_association"],
        ],
        fmt="o", color="#1D4ED8", ecolor="#93C5FD", capsize=3,
    )
    ax.axvline(0, color="black", linewidth=1)
    ax.set(title="Adjusted salary associations (99% trimmed sample)", xlabel="Approximate percent association", ylabel="")
    fig.tight_layout()
    fig.savefig(REPORT_DIR / "adjusted_coefficients.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    df = prepare_data()
    lower, upper = df["annual_salary"].quantile([0.01, 0.99])
    trimmed = df.loc[df["annual_salary"].between(lower, upper)].copy()

    summary = salary_summary(df)
    summary.to_csv(REPORT_DIR / "salary_by_skill_mix.csv")
    category_summary = pd.DataFrame({
        "advert_count": df[TECH_COLUMNS + SOFT_COLUMNS].sum(),
        "prevalence_percent": df[TECH_COLUMNS + SOFT_COLUMNS].mean() * 100,
        "median_salary_when_present": [
            df.loc[df[column].eq(1), "annual_salary"].median()
            for column in TECH_COLUMNS + SOFT_COLUMNS
        ],
    })
    category_summary.to_csv(REPORT_DIR / "skill_category_summary.csv")

    controls = (
        " + C(seniority) + C(contract_group) + C(schedule_group)"
        " + C(occupation_group) + C(region_group) + C(source_group) + C(creation_year)"
    )
    mix_terms = [
        "C(skill_mix, Treatment(reference='neither'))[T.soft_only]",
        "C(skill_mix, Treatment(reference='neither'))[T.technical_only]",
        "C(skill_mix, Treatment(reference='neither'))[T.technical_and_soft]",
    ]
    unadjusted = fit_clustered_ols(
        "log_salary ~ C(skill_mix, Treatment(reference='neither'))", df
    )
    adjusted = fit_clustered_ols(
        "log_salary ~ C(skill_mix, Treatment(reference='neither'))" + controls, df
    )
    adjusted_trimmed = fit_clustered_ols(
        "log_salary ~ C(skill_mix, Treatment(reference='neither'))" + controls, trimmed
    )
    broad = fit_clustered_ols(
        "log_salary ~ C(broad_skill_mix, Treatment(reference='neither'))" + controls, trimmed
    )
    broad_terms = [term.replace("skill_mix", "broad_skill_mix") for term in mix_terms]

    coefficient_parts = [
        tidy_terms(unadjusted, mix_terms, "unadjusted_full"),
        tidy_terms(adjusted, mix_terms, "adjusted_full"),
        tidy_terms(adjusted_trimmed, mix_terms, "adjusted_trimmed"),
        tidy_terms(broad, broad_terms, "broad_detection_trimmed"),
    ]

    category_formula = "log_salary ~ " + " + ".join(TECH_COLUMNS + SOFT_COLUMNS) + controls
    category_model = fit_clustered_ols(category_formula, trimmed)
    coefficient_parts.append(
        tidy_terms(category_model, TECH_COLUMNS + SOFT_COLUMNS, "category_adjusted_trimmed")
    )
    coefficients = pd.concat(coefficient_parts, ignore_index=True)
    coefficients.to_csv(REPORT_DIR / "regression_coefficients.csv", index=False)
    mix_contrast = coefficient_contrast(
        adjusted_trimmed,
        "C(skill_mix, Treatment(reference='neither'))[T.technical_and_soft]",
        "C(skill_mix, Treatment(reference='neither'))[T.technical_only]",
        "technical_and_soft minus technical_only",
    )
    mix_contrast.to_csv(REPORT_DIR / "skill_mix_contrast.csv", index=False)

    model_fit = pd.DataFrame([
        {"model": "unadjusted_full", "n": int(unadjusted.nobs), "r2": unadjusted.rsquared},
        {"model": "adjusted_full", "n": int(adjusted.nobs), "r2": adjusted.rsquared},
        {"model": "adjusted_trimmed", "n": int(adjusted_trimmed.nobs), "r2": adjusted_trimmed.rsquared},
        {"model": "broad_detection_trimmed", "n": int(broad.nobs), "r2": broad.rsquared},
        {"model": "category_adjusted_trimmed", "n": int(category_model.nobs), "r2": category_model.rsquared},
    ])
    model_fit.to_csv(REPORT_DIR / "regression_model_fit.csv", index=False)

    prediction = predictive_models(trimmed)
    prediction.to_csv(REPORT_DIR / "prediction_metrics.csv", index=False)
    save_figures(df, summary, coefficients)

    quality = pd.DataFrame([{
        "analysis_rows": len(df),
        "trimmed_rows": len(trimmed),
        "salary_p01": lower,
        "salary_median": df["annual_salary"].median(),
        "salary_p99": upper,
        "technical_rows": int(df["has_tech_skills"].sum()),
        "strict_technical_rows": int(df["strict_has_tech"].sum()),
        "soft_rows": int(df["has_soft_skills"].sum()),
        "missing_education_rows": int(df["profile_requiredEducationLevel"].isna().sum()),
    }])
    quality.to_csv(REPORT_DIR / "quality_summary.csv", index=False)

    print("Quality summary")
    print(quality.to_string(index=False))
    print("\nSalary by skill mix")
    print(summary.round(1).to_string())
    print("\nRegression coefficients")
    print(coefficients.round(3).to_string(index=False))
    print("\nPrediction metrics")
    print(prediction.round(3).to_string(index=False))
    print("\nDirect skill-mix contrast")
    print(mix_contrast.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
