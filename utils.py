import numpy as np
import pandas as pd
import ast
import re

strong_ai_skills = {
    "artificial intelligence", "machine learning", "deep learning",
    "natural language processing", "nlp", "computer vision",
    "large language models", "large language model", "llm", "llms",
    "generative ai", "gen ai", "transformers", "hugging face", "openai api",
    "langchain", "rag", "retrieval-augmented generation", "fine-tuning",
    "fine tuning", "ai agents", "mlops", "neural networks", "neural network",
    "reinforcement learning", "tensorflow", "pytorch", "keras", "scikit-learn",
    "sklearn", "predictive modelling", "predictive modeling", "data mining",
    "knowledge discovery",
}


strict_it_skills = {
    "software development", "software engineering", "software architecture",
    "computer science", "object-oriented programming", "backend", "back-end",
    "frontend", "front-end", "full stack", "full-stack", "web development",
    "mobile application development", "application development", "java", "javascript",
    "typescript", "c++", "c#", "php", "ruby", "go", "golang", "rust", "swift",
    "kotlin", "scala", "spring", "spring boot", "hibernate", "jakarta ee", "java ee",
    ".net", "asp.net", "node.js", "nodejs", "react", "angular", "vue", "django",
    "flask", "fastapi", "laravel", "symfony", "rest api", "graphql", "microservices",
    "docker", "kubernetes", "devops", "ci/cd", "jenkins", "git", "linux",
    "database administration", "database design", "data engineering", "data warehouse",
    "etl", "mysql", "postgresql", "sql server", "oracle database", "mongodb", "nosql",
    "cybersecurity", "cyber security", "network security", "information security",
    "cloud computing", "aws", "azure", "google cloud", "gcp",
}

# Specific data skills. Broad terms such as "analytics", "automation",
# "statistics" and "Excel" are intentionally excluded because on their own
# they do not reliably identify an IT/data role.
data_skills = {
    "python", "sql", "data analysis", "data analytics", "data science", "pandas",
    "numpy", "power bi", "tableau", "business intelligence",
    "data visualisation", "data visualization", "database querying",
}


excluded_skills = {
    "automation technology",
    "statistics",
    "healthcare analytics",
    "excel",
    "analytics",
    "r",

    # πολύ γενικά / όχι αυστηρά IT
    "teach electronics and automation principles",
    "implement front-end website design",
    "set up cybersecurity training programmes",

    # green / non-IT, αν εμφανιστούν
    "energy efficiency",
    "renewable energy",
    "sustainability",
    "environmental",
    "waste management",
    "pollution",
    "climate",
    "carbon footprint"
}



def skill_exact_or_phrase_match(skill, skill_set):
    s = str(skill).lower().strip()
    # print(f'skill: {skill}')
    for target in skill_set:
        # print(f'> target: {target}')
        target = target.lower().strip()
        if target == "react":
            if s in {"react", "react.js", "reactjs"} or "react (javascript" in s or "react framework" in s:
                return True
            continue
        if target in ["c++", "c#", ".net", "node.js", "ci/cd"]:
            if target in s:
                return True
            continue
        pattern = r"\b" + re.escape(target) + r"\b"
        if re.search(pattern, s):
            print(f'>>> match found: {s} matches {target}')
            return True
    return False


def collect_candidate_matches(skills_value):
    skills = parse_list_cell(skills_value)
    matched = []
    for skill in skills:
        if (
            skill_exact_or_phrase_match(skill, strong_ai_skills)
            or skill_exact_or_phrase_match(skill, strict_it_skills)
            or skill_exact_or_phrase_match(skill, data_skills)
        ):
            matched.append(skill)
    return sorted(set(matched))


def make_candidate_dataset(df):
    possible_mapped_cols = [c for c in df.columns if "mapped" in c.lower() and "skill" in c.lower()]
    if not possible_mapped_cols:
        raise ValueError("Δεν βρέθηκε στήλη mapped skills.")
    mapped_col = possible_mapped_cols[0]

    df = df.copy()
    df["matched_mapped_skills"] = df[mapped_col].apply(collect_candidate_matches)

    # Keep every job, including jobs with no AI/IT match. Empty matches are
    # useful as a separate comparison group and should not remove the row.
    groups = df["matched_mapped_skills"].apply(get_match_groups)
    df["strong_ai_matches"] = groups.apply(lambda x: x[0])
    df["strict_it_matches"] = groups.apply(lambda x: x[1])
    df["weak_general_matches"] = groups.apply(lambda x: x[2])
    df["matched_skill_count"] = df["matched_mapped_skills"].apply(len)
    df["strong_ai_count"] = df["strong_ai_matches"].apply(len)
    df["strict_it_count"] = df["strict_it_matches"].apply(len)
    df["weak_general_count"] = df["weak_general_matches"].apply(len)
    return df, mapped_col

def get_match_groups(skills):
    strong_ai_matches, strict_it_matches, weak_matches = [], [], []
    for skill in parse_list_cell(skills):
        if skill_exact_or_phrase_match(skill, strong_ai_skills):
            strong_ai_matches.append(skill)
        if skill_exact_or_phrase_match(skill, strict_it_skills):
            strict_it_matches.append(skill)
        if skill_exact_or_phrase_match(skill, data_skills):
            weak_matches.append(skill)
    return (
        sorted(set(strong_ai_matches)),
        sorted(set(strict_it_matches)),
        sorted(set(weak_matches)),
    )


def parse_list_cell(x):
    if isinstance(x, (list, tuple, set, np.ndarray)):
        return [str(i).strip() for i in list(x) if str(i).strip()]

    if x is None:
        return []

    try:
        if pd.isna(x):
            return []
    except Exception:
        pass

    x = str(x).strip()

    if x == "" or x.lower() in ["nan", "none", "null"]:
        return []

    try:
        val = ast.literal_eval(x)
        if isinstance(val, (list, tuple, set, np.ndarray)):
            return [str(i).strip() for i in list(val) if str(i).strip()]
    except Exception:
        pass

    return [s.strip() for s in re.split(r",|;|\|", x) if s.strip()]


def clean_strict_skills(skills):
    cleaned = []

    for skill in skills:
        skill_clean = str(skill).strip()
        skill_lower = skill_clean.lower()

        if skill_clean and skill_lower not in excluded_skills:
            cleaned.append(skill_clean)

    return sorted(set(cleaned))
