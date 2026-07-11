import pandas as pd
import ast
import json
from esco_skill_extractor import SkillExtractor
import os

files = os.listdir('files/raw')
files = [f for f in os.listdir('files/raw') if f.endswith('.parquet')]


salary_limits_dict = {
    #  'fr': {'hour': {'min': 10, 'max': 500}, 'month': {'min': 1500, 'max': 20000}, 'year': {'min': 21600, 'max': 300000}},
     #'be': {'hour': {'min': 12, 'max': 600}, 'month': {'min': 1800, 'max': 25000}, 'year': {'min': 25000, 'max': 350000}},
     #'cs': {'hour': {'min': 5, 'max': 200}, 'month': {'min': 800, 'max': 10000}, 'year': {'min': 10000, 'max': 150000}},
    #'de': {'hour': {'min': 12, 'max': 600}, 'month': {'min': 1900, 'max': 25000}, 'year': {'min': 26000, 'max': 350000}},
     #'el': {'hour': {'min': 6, 'max': 300}, 'month': {'min': 900, 'max': 12000}, 'year': {'min': 12000, 'max': 180000}},
     #'sv': {'hour': {'min': 15, 'max': 700}, 'month': {'min': 2000, 'max': 28000}, 'year': {'min': 28000, 'max': 400000}},
    'nl': {'hour': {'min': 12, 'max': 600}, 'month': {'min': 2300, 'max': 25000}, 'year': {'min': 27600, 'max': 350000}},

}

def calculate_salary(row, country_code):
    # country = row.get('country')
    period = row.get('salary.period')
    salary_val = row.get('salary.min')
    
    if country_code not in salary_limits_dict or period not in salary_limits_dict[country_code]:
        return None
    
    limits = salary_limits_dict[country_code][period]
    
    # Validate against min/max defined in dict
    if not (limits['min'] <= salary_val <= limits['max']):
        return None
    
    # Calculation logic
    if period == 'month':
        return salary_val * 12
    elif period == 'hour':
        # Assuming standard full-time: 35 hours/week * 4.33 weeks/month * 12 months
        return salary_val * 35 * 4.33 * 12
    elif period == 'year':
        return salary_val
        
    return None


for file in files:
    print(file) 
    country_code = file.split('_')[2].split('.')[0]
    print(f'COUNTRY CODE: {country_code}')
    INPUT_PARQUET_FILE = f'files/raw/eures_jobs_{country_code}.parquet'
    OUTPUT_CSV_FILE = f'extracted_skills_{country_code}.csv'

    if country_code not in salary_limits_dict.keys():
        continue

    df = pd.read_parquet(INPUT_PARQUET_FILE)
    # print(df.shape)
    # print(df.isna().sum())


    df = df[~df['profile_remunerationPackage'].isna()]
    # print(df.shape)

    df['profile_remunerationPackage_dict'] = df['profile_remunerationPackage'].apply(json.loads)
    df_remuneration = pd.json_normalize(df['profile_remunerationPackage_dict'])
    df = df.reset_index(drop=True)
    df_remuneration = df_remuneration.reset_index(drop=True)

    print(df_remuneration.columns)


    df_extended = pd.concat([df, df_remuneration], axis=1)
    print(df_extended.shape)
    df_extended.drop(['profile_remunerationPackage', 'profile_remunerationPackage_dict'], axis=1, inplace=True)
    print(df_extended.shape)

    df_extended = df_extended[~df_extended['salary.min'].isna()]
    print(df_extended.shape)
    df_extended = df_extended[~df_extended['salary.period'].isna()]
    print(df_extended.shape)
    df_extended = df_extended[df_extended['salary.period'] != 'once']
    print(df_extended.shape)
    df_extended = df_extended[df_extended['profile_workSchedule'] == '["fulltime"]']
    print(df_extended.shape)
    df_extended = df_extended[df_extended['salary.period'] != 'hour']
    print(df_extended.shape)

    # df_extended['annual_salary'] = df_extended.apply(calculate_salary, axis=1)
    df_extended['annual_salary'] = df_extended.apply(lambda row: calculate_salary(row, country_code), axis=1)

    print(df_extended.shape)
    df_extended.dropna(subset=['annual_salary'], inplace=True)
    print(df_extended.shape)
    df_extended['profile_skills_list'] = df_extended['profile_skills'].apply(json.loads)
    print(df_extended.shape)
    df_extended[df_extended['profile_skills_list'].apply(len) >=  1]
    print(df_extended.shape)


    #df_extended_sample  = df_extended.sample(n=500, random_state=42)

    skill_extractor = SkillExtractor()

    batch_size = 1000
    processed_batches = []

    for i in range(0, len(df_extended), batch_size):
        print(f'Processing batch {i // batch_size + 1} of {len(df_extended) // batch_size + 1}')
        batch = df_extended.iloc[i:i + batch_size].copy()
        batch['Extracted Skills'] = skill_extractor.get_skills(batch['profile_description'].tolist())
        processed_batches.append(batch)

    df_final = pd.concat(processed_batches, ignore_index=True)

    df_final.to_csv(f'files/extracted/{OUTPUT_CSV_FILE}', index=False, sep=';')