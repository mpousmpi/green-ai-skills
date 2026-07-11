
import pandas as pd
import ast
import numpy as np
import re

from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold, cross_val_score
from collections import Counter


from scipy.stats import zscore
from utils import *

import os


esco_mapping_file_path = 'ESCO_Mapping_csv 2.csv'

try:
    esco_mapping_df = pd.read_csv(esco_mapping_file_path, encoding='utf-8', delimiter=';', on_bad_lines='skip')
except UnicodeDecodeError:
    esco_mapping_df = pd.read_csv(esco_mapping_file_path, encoding='latin1', delimiter=';', on_bad_lines='skip')

print("Columns in esco_mapping_df:", esco_mapping_df.columns.tolist())

# Verify required columns are present
if 'conceptUri' in esco_mapping_df.columns and 'preferredLabel' in esco_mapping_df.columns:
    concept_to_label = esco_mapping_df.set_index('conceptUri')['preferredLabel'].to_dict()
else:
    print("Error: Required columns ('conceptUri', 'preferredLabel') not found in esco_mapping_df.")

def map_skills_to_labels(skills_column):
    return [concept_to_label.get(skill, 'Unknown') for skill in skills_column]


TARGET_COL = "annual_salary"
SKILL_COL = "matched_mapped_skills"

files = os.listdir('files/extracted')
files = [f for f in os.listdir('files/extracted') if f.endswith('.csv')]
print("Files in 'files/extracted':", files)
for file in files:
    print(f"Processing file: {file}")
    df = pd.read_csv(os.path.join('files/extracted', file), sep=';')
    print(f"Columns in {file}:", df.columns.tolist())
    print(f"First few rows of {file}:\n", df.head())

    df['Extracted Skills'] = df['Extracted Skills'].apply(ast.literal_eval)
    df['Mapped Skills'] = df['Extracted Skills'].apply(map_skills_to_labels)
    df.reset_index(drop=True, inplace=True)

    df['profile_jobCategories'].unique()

    print(df.columns)

    candidate_df, mapped_col = make_candidate_dataset(df)
    # candidate_df.to_csv(CANDIDATE_OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print("Rows loaded:", len(candidate_df))
    print("Columns:")
    print(candidate_df.columns.tolist())

    candidate_df[[SKILL_COL, TARGET_COL]].head()

    candidate_df['Z-score'] = zscore(candidate_df['annual_salary'])
    candidate_df = candidate_df[candidate_df['Z-score'].abs() < 3]

    candidate_df['annual_salary'].describe()

    candidate_df.boxplot(column=['annual_salary'])

    candidate_df['annual_salary'].hist(bins=30)

    # Parse και καθάρισμα
    candidate_df["skills_list"] = candidate_df[SKILL_COL].apply(parse_list_cell)
    candidate_df["skills_list_clean"] = candidate_df["skills_list"].apply(clean_strict_skills)

    # Μετατροπή μισθού σε αριθμό
    candidate_df[TARGET_COL] = pd.to_numeric(candidate_df[TARGET_COL], errors="coerce")

    # Κρατάμε μόνο rows με μισθό και τουλάχιστον ένα καθαρό skill
    df_skills_reg = candidate_df[
        candidate_df[TARGET_COL].notna() &
        candidate_df["skills_list_clean"].apply(lambda x: len(x) > 0)
    ].copy()

    print("Rows before cleaning:", len(candidate_df))
    print("Rows after removing noisy/general skills:", len(df_skills_reg))
    
    df_skills_reg[[SKILL_COL, "skills_list_clean", TARGET_COL]].head(20)
    df_skills_reg.to_csv(f'files/cleaned/{file.split("_")[2].split(".")[0]}_final.csv', index=False, sep=';') 
# INPUT_FILE = 'extracted_skills_France.csv'


# df = pd.read_csv(INPUT_FILE, sep=';')







