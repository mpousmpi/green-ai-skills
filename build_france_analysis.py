"""Build the thesis-ready analytical dataset for the French EURES sample."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd


INPUT_PATH = Path("files/extracted/extracted_skills_fr.csv")
ESCO_PATH = Path("ESCO_Mapping_csv 2.csv")
OUTPUT_PATH = Path("files/cleaned/fr_analysis.csv")
VALIDATION_PATH = Path("files/cleaned/fr_validation_sample.csv")
RANDOM_STATE = 42


TECH_TAXONOMY = {
    "ai_ml": {
        "artificial intelligence", "machine learning", "deep learning",
        "natural language processing", "computer vision", "neural network",
        "reinforcement learning", "generative ai", "large language model",
        "tensorflow", "pytorch", "keras", "scikit-learn", "mlops",
        "data mining", "predictive modelling", "predictive modeling",
    },
    "data_analysis": {
        "data analysis", "data analytics", "data science", "business intelligence",
        "data visualisation", "data visualization", "power bi", "tableau",
        "python", "pandas", "numpy", "sql",
    },
    "data_engineering": {
        "data engineering", "data warehouse", "database", "database design",
        "database administration", "etl", "postgresql", "mysql", "sql server",
        "oracle database", "mongodb", "nosql",
    },
    "software": {
        "software development", "software engineering", "software architecture",
        "object-oriented programming", "application development", "web development",
        "frontend", "front-end", "backend", "back-end", "full stack", "full-stack",
        "java", "javascript", "typescript", "c++", "c#", "php", "ruby", "golang",
        "rust", "swift", "kotlin", "scala", "spring", "node.js", "angular",
        "vue", "django", "flask", "fastapi", "rest api", "graphql", "microservices",
    },
    "cloud_devops": {
        "cloud computing", "aws", "azure", "google cloud", "devops", "docker",
        "kubernetes", "jenkins", "ci/cd", "git",
    },
    "cybersecurity": {
        "cybersecurity", "cyber security", "network security", "information security",
        "computer security", "data security",
    },
    "networks_systems": {
        "computer network", "network administration", "system administration",
        "systems administration", "linux", "computer hardware", "ict hardware",
        "digital hardware", "information network hardware", "ict networking hardware",
    },
}


SOFT_TAXONOMY = {
    "communication": {
        "communication", "communicate", "active listening", "present information",
        "negotiate", "persuade", "write reports",
    },
    "teamwork": {
        "teamwork", "work in a team", "work in teams", "collaborate",
        "multidisciplinary team", "cooperate with colleagues",
    },
    "adaptability": {
        "adapt to change", "adaptability", "flexibility", "cope with pressure",
        "work under pressure",
    },
    "problem_solving": {
        "problem solving", "solve problems", "solve technical problems",
        "critical thinking", "think analytically", "decision making", "make decisions",
    },
    "creativity": {
        "creative", "creativity", "develop creative ideas", "innovation processes",
        "show curiosity", "demonstrate curiosity",
    },
    "initiative_responsibility": {
        "show initiative", "assume responsibility", "meet deadlines", "meet commitments",
        "work independently", "professional responsibility",
    },
    "leadership": {
        "lead a team", "manage a team", "lead others", "motivate others",
        "supervise employees", "leadership principles",
    },
    "customer_interaction": {
        "communicate with customers", "satisfy customers", "customer service",
        "customer relationship", "identify customer's needs", "consult with business clients",
    },
}


# High-precision text patterns complement ESCO. Title patterns describe roles;
# description patterns require named methods or technologies rather than broad
# words such as "data", "IT", "digital" or "automation" on their own.
TITLE_TECH_PATTERNS = {
    "ai_ml": r"\b(?:ai|ia|machine learning|deep learning|nlp|computer vision|llm|mlops|data scientist)\b",
    "data_analysis": r"\b(?:data analyst|data scientist|bi analyst|business intelligence|analyste de donn[ée]es|data analytics?)\b",
    "data_engineering": r"\b(?:data engineer|data architect|database administrator|dba|ing[ée]nieur data|etl developer)\b",
    "software": r"\b(?:software engineer|software developer|d[ée]veloppeur|full[ -]?stack|front[ -]?end|back[ -]?end|web developer|application developer|embedded developer|firmware engineer|erp developer|java developer|python developer|c\+\+ developer|c# developer|\.net developer|architecte logiciel|software architect|computer programmer|application programmer)\b",
    "cloud_devops": r"\b(?:cloud engineer|cloud architect|devops|site reliability engineer|sre)\b",
    "cybersecurity": r"\b(?:cybersecurity|cyber security|cybers[ée]curit[ée]|security engineer|security analyst|soc analyst)\b",
    "networks_systems": r"\b(?:system administrator|it systems? engineer|linux systems? engineer|network administrator|network engineer|administrateur syst[èe]mes?|administrateur r[ée]seaux?|it support|helpdesk)\b",
}


DESCRIPTION_TECH_PATTERNS = {
    "ai_ml": r"\b(?:artificial intelligence|intelligence artificielle|machine learning|deep learning|natural language processing|computer vision|generative ai|ia g[ée]n[ée]rative|large language models?|llms?|tensorflow|pytorch|scikit-learn|hugging face|mlops|openai api|chatgpt)\b",
    "data_analysis": r"\b(?:data analysis|data analytics|data science|analyse de donn[ée]es|science des donn[ée]es|business intelligence|power bi|pandas|numpy)\b",
    "data_engineering": r"\b(?:data engineering|data warehouse|etl|postgresql|mysql|sql server|oracle database|mongodb|nosql|database administration)\b",
    "software": r"(?<![a-z0-9])(?:java|javascript|typescript|c\+\+|c#|\.net|php|ruby|golang|rust|swift|kotlin|scala|spring boot|node\.js|react\.js|angular|vue\.js|django|flask|fastapi|graphql|microservices)(?![a-z0-9])",
    "cloud_devops": r"\b(?:aws|microsoft azure|google cloud|gcp|devops|docker|kubernetes|jenkins|ci/cd|terraform)\b",
    "cybersecurity": r"\b(?:cybersecurity|cyber security|cybers[ée]curit[ée]|network security|information security|penetration testing|soc analyst|siem)\b",
    "networks_systems": r"\b(?:linux|network administration|system administration|administration syst[èe]me|administration r[ée]seau)\b",
}


def parse_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if pd.isna(value):
        return []
    try:
        parsed = ast.literal_eval(str(value))
    except (SyntaxError, ValueError):
        return []
    return [str(item) for item in parsed] if isinstance(parsed, list) else []


def normalise(value: object) -> str:
    return re.sub(r"\s+", " ", str(value).lower().strip())


def phrase_present(label: str, phrase: str) -> bool:
    pattern = r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])"
    return re.search(pattern, label) is not None


def classify_label(label: str, taxonomy: dict[str, set[str]]) -> list[str]:
    clean_label = normalise(label)
    return [
        category
        for category, phrases in taxonomy.items()
        if any(phrase_present(clean_label, normalise(phrase)) for phrase in phrases)
    ]


def combine_categories(labels: list[str], label_map: dict[str, list[str]]) -> list[str]:
    return sorted({category for label in labels for category in label_map.get(label, [])})


def matched_labels(labels: list[str], label_map: dict[str, list[str]]) -> list[str]:
    return sorted({label for label in labels if label_map.get(label)})


def categories_from_flags(row: pd.Series, prefix: str, categories: list[str]) -> list[str]:
    return [category for category in categories if row[f"{prefix}{category}"]]


def extract_isco(value: object) -> str | None:
    values = parse_list(value)
    if not values:
        return None
    return values[0].rstrip("/").split("/")[-1]


def seniority_from_title(title: object) -> str:
    value = normalise(title)
    if re.search(r"\b(intern|internship|trainee|apprentice|alternance|stage|stagiaire)\b", value):
        return "entry_training"
    if re.search(r"\b(junior|débutant|debutant|graduate)\b", value):
        return "junior"
    if re.search(r"\b(senior|sr\.?|experienced|expérimenté|experimente|confirmed|confirmé)\b", value):
        return "senior"
    if re.search(r"\b(head|lead|manager|director|directeur|responsable|chief)\b", value):
        return "management"
    return "unspecified"


def to_json_list(values: list[str]) -> str:
    return json.dumps(values, ensure_ascii=False)


def main() -> None:
    df = pd.read_csv(INPUT_PATH, sep=";", low_memory=False)
    esco = pd.read_csv(
        ESCO_PATH,
        sep=";",
        encoding="utf-8-sig",
        usecols=["conceptUri", "preferredLabel"],
        on_bad_lines="skip",
    )
    concept_to_label = dict(zip(esco["conceptUri"], esco["preferredLabel"]))

    df["extracted_skill_uris"] = df["Extracted Skills"].apply(parse_list)
    df["mapped_skills"] = df["extracted_skill_uris"].apply(
        lambda values: sorted({concept_to_label.get(value, "Unknown") for value in values})
    )

    unique_labels = sorted({label for values in df["mapped_skills"] for label in values})
    tech_label_map = {label: classify_label(label, TECH_TAXONOMY) for label in unique_labels}
    soft_label_map = {label: classify_label(label, SOFT_TAXONOMY) for label in unique_labels}

    df["tech_skills"] = df["mapped_skills"].apply(lambda x: matched_labels(x, tech_label_map))
    df["soft_skills"] = df["mapped_skills"].apply(lambda x: matched_labels(x, soft_label_map))
    df["esco_tech_categories"] = df["mapped_skills"].apply(lambda x: combine_categories(x, tech_label_map))
    df["soft_categories"] = df["mapped_skills"].apply(lambda x: combine_categories(x, soft_label_map))

    # "IA RECRUTEMENT/RECRUITMENT" is an agency name in this source, not
    # evidence that the advertised role requires artificial intelligence.
    agency_name_pattern = r"\bIA\s+RECRU(?:I|)T(?:EMENT|MENT)\b"
    title_text = (
        df["profile_title"].fillna("").astype(str)
        .str.replace(agency_name_pattern, "", case=False, regex=True)
    )
    description_text = (
        df["profile_description"].fillna("").astype(str)
        .str.replace(agency_name_pattern, "", case=False, regex=True)
    )
    tech_category_names = list(TECH_TAXONOMY)
    for category in tech_category_names:
        df[f"esco_has_{category}"] = df["esco_tech_categories"].apply(
            lambda values, c=category: int(c in values)
        )
        df[f"title_has_{category}"] = title_text.str.contains(
            TITLE_TECH_PATTERNS[category], case=False, regex=True, na=False
        ).astype(int)
        df[f"description_has_{category}"] = description_text.str.contains(
            DESCRIPTION_TECH_PATTERNS[category], case=False, regex=True, na=False
        ).astype(int)
        df[f"broad_has_{category}"] = df[
            [f"esco_has_{category}", f"title_has_{category}", f"description_has_{category}"]
        ].max(axis=1)
        # Primary high-confidence definition: an explicit role title, or
        # agreement between an ESCO skill and a specific description mention.
        df[f"has_{category}"] = (
            df[f"title_has_{category}"].eq(1)
            | (
                df[f"esco_has_{category}"].eq(1)
                & df[f"description_has_{category}"].eq(1)
            )
        ).astype(int)

    df["title_tech_categories"] = df.apply(
        categories_from_flags, axis=1, prefix="title_has_", categories=tech_category_names
    )
    df["description_tech_categories"] = df.apply(
        categories_from_flags, axis=1, prefix="description_has_", categories=tech_category_names
    )
    df["broad_tech_categories"] = df.apply(
        lambda row: sorted(
            set(row["esco_tech_categories"])
            | set(row["title_tech_categories"])
            | set(row["description_tech_categories"])
        ), axis=1,
    )
    df["tech_categories"] = df.apply(
        categories_from_flags, axis=1, prefix="has_", categories=tech_category_names
    )
    df["tech_detection_sources"] = df.apply(
        lambda row: [source for source, column in (
            ("esco", "esco_tech_categories"),
            ("title", "title_tech_categories"),
            ("description", "description_tech_categories"),
        ) if row[column]],
        axis=1,
    )
    for category in SOFT_TAXONOMY:
        df[f"has_soft_{category}"] = df["soft_categories"].apply(lambda x, c=category: int(c in x))

    df["tech_skill_count"] = df["tech_skills"].apply(len)
    df["tech_category_count"] = df["tech_categories"].apply(len)
    df["broad_has_tech_skills"] = df["broad_tech_categories"].map(bool).astype(int)
    df["soft_skill_count"] = df["soft_skills"].apply(len)
    df["has_tech_skills"] = df["tech_category_count"].gt(0).astype(int)
    df["has_soft_skills"] = df["soft_skill_count"].gt(0).astype(int)
    df["skill_mix"] = np.select(
        [
            df["has_tech_skills"].eq(1) & df["has_soft_skills"].eq(1),
            df["has_tech_skills"].eq(1),
            df["has_soft_skills"].eq(1),
        ],
        ["technical_and_soft", "technical_only", "soft_only"],
        default="neither",
    )
    df["isco_code"] = df["profile_jobCategories"].apply(extract_isco)
    df["seniority"] = df["profile_title"].apply(seniority_from_title)

    duplicate_key = [
        "profile_title", "profile_description", "profile_company",
        "profile_addresses", "annual_salary",
    ]
    df["duplicate_group_size"] = df.groupby(duplicate_key, dropna=False)["documentId"].transform("size")
    df = df.drop_duplicates(duplicate_key, keep="first").copy()

    df["validation_stratum"] = np.select(
        [
            df["has_ai_ml"].eq(1),
            df[["has_data_analysis", "has_data_engineering"]].max(axis=1).eq(1),
            df["has_software"].eq(1),
            df["has_tech_skills"].eq(1),
            df["has_soft_skills"].eq(1),
        ],
        ["ai_ml", "data", "software", "other_technical", "soft_only"],
        default="neither",
    )
    validation_parts = [
        group.sample(min(50, len(group)), random_state=RANDOM_STATE)
        for _, group in df.groupby("validation_stratum", sort=False)
    ]
    validation = pd.concat(validation_parts, ignore_index=True)
    validation["manual_is_technical"] = ""
    validation["manual_categories_correct"] = ""
    validation["manual_soft_skills_correct"] = ""
    validation["manual_notes"] = ""

    list_columns = [
        "mapped_skills", "tech_skills", "soft_skills", "esco_tech_categories",
        "title_tech_categories", "description_tech_categories", "broad_tech_categories", "tech_categories",
        "tech_detection_sources", "soft_categories",
    ]
    for column in list_columns:
        df[column] = df[column].apply(to_json_list)
        validation[column] = validation[column].apply(to_json_list)

    output_columns = [
        "documentId", "euresId", "creationDate", "profile_title", "profile_description",
        "profile_company", "profile_addresses", "profile_jobCategories", "isco_code",
        "profile_contractType", "profile_workSchedule", "profile_requiredEducationLevel",
        "source", "salary.currency", "salary.period", "salary_final", "annual_salary",
        "seniority", "mapped_skills", "tech_skills", "soft_skills", "esco_tech_categories",
        "title_tech_categories", "description_tech_categories", "broad_tech_categories", "tech_categories",
        "tech_detection_sources", "soft_categories", "tech_skill_count", "tech_category_count",
        "soft_skill_count", "broad_has_tech_skills", "has_tech_skills",
        "has_soft_skills", "skill_mix", "duplicate_group_size",
        *[f"has_{category}" for category in TECH_TAXONOMY],
        *[f"broad_has_{category}" for category in TECH_TAXONOMY],
        *[f"has_soft_{category}" for category in SOFT_TAXONOMY],
    ]
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df[output_columns].to_csv(OUTPUT_PATH, sep=";", index=False, encoding="utf-8-sig")
    validation_columns = [
        "validation_stratum", "documentId", "profile_title", "profile_description",
        "annual_salary", "isco_code", "mapped_skills", "tech_skills", "soft_skills",
        "esco_tech_categories", "title_tech_categories", "description_tech_categories", "broad_tech_categories",
        "tech_categories", "tech_detection_sources", "soft_categories",
        "manual_is_technical", "manual_categories_correct",
        "manual_soft_skills_correct", "manual_notes",
    ]
    validation[validation_columns].to_csv(
        VALIDATION_PATH, sep=";", index=False, encoding="utf-8-sig"
    )

    print(f"Input rows: {len(pd.read_csv(INPUT_PATH, sep=';', usecols=['documentId'])):,}")
    print(f"Analytical rows: {len(df):,}")
    print("Skill mix:")
    print(df["skill_mix"].value_counts().to_string())
    print(f"Output: {OUTPUT_PATH}")
    print(f"Validation sample: {VALIDATION_PATH} ({len(validation):,} rows)")


if __name__ == "__main__":
    main()
