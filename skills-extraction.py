# import pandas as pd
# import ast
# import json
# from esco_skill_extractor import SkillExtractor
# import os
# import numpy as np


# files = os.listdir('files/raw')
# files = [f for f in os.listdir('files/raw') if f.endswith('.parquet')]


# salary_limits_dict = {
#     # 'fr': {'hour': {'min': 10, 'max': 500}, 'month': {'min': 1500, 'max': 20000}, 'year': {'min': 21600, 'max': 300000}},
#     # 'be': {'hour': {'min': 12, 'max': 600}, 'month': {'min': 1800, 'max': 25000}, 'year': {'min': 25000, 'max': 350000}},
#     # 'cs': {'hour': {'min': 5, 'max': 200}, 'month': {'min': 800, 'max': 10000}, 'year': {'min': 10000, 'max': 150000}},
#     # 'de': {'hour': {'min': 12, 'max': 600}, 'month': {'min': 1900, 'max': 25000}, 'year': {'min': 26000, 'max': 350000}},
#     # 'el': {'hour': {'min': 6, 'max': 300}, 'month': {'min': 900, 'max': 12000}, 'year': {'min': 12000, 'max': 180000}},
#     # 'sv': {'hour': {'min': 15, 'max': 700}, 'month': {'min': 2000, 'max': 28000}, 'year': {'min': 28000, 'max': 400000}},
#     'nl': {'hour': {'min': 12, 'max': 600}, 'month': {'min': 2300, 'max': 25000}, 'year': {'min': 27600, 'max': 350000}},

# }

# def calculate_salary(row, country_code):
#     # country = row.get('country')
#     period = row.get('salary.period')
#     salary_val = row.get('salary_final')
    
#     if country_code not in salary_limits_dict or period not in salary_limits_dict[country_code]:
#         return None
    
#     limits = salary_limits_dict[country_code][period]
    
#     # Validate against min/max defined in dict
#     if not (limits['min'] <= salary_val <= limits['max']):
#         return None
    
#     # Calculation logic
#     if period == 'month':
#         return salary_val * 12
#     elif period == 'hour':
#         # Assuming standard full-time: 35 hours/week * 4.33 weeks/month * 12 months
#         return salary_val * 35 * 4.33 * 12
#     elif period == 'year':
#         return salary_val
        
#     return None


# def get_limit(country_code, period, key):
#     limits = salary_limits_dict.get(country_code)
#     if limits is None:
#         return np.nan
#     return limits[period][key]



# for file in files:
#     print(file) 
#     country_code = file.split('_')[2].split('.')[0]
#     print(f'COUNTRY CODE: {country_code}')
#     INPUT_PARQUET_FILE = f'files/raw/eures_jobs_{country_code}.parquet'
#     OUTPUT_CSV_FILE = f'extracted_skills_{country_code}.csv'

#     if country_code not in salary_limits_dict.keys():
#         continue

#     df = pd.read_parquet(INPUT_PARQUET_FILE)


#     df = df[~df['profile_remunerationPackage'].isna()]

#     df['profile_remunerationPackage_dict'] = df['profile_remunerationPackage'].apply(json.loads)
#     df_remuneration = pd.json_normalize(df['profile_remunerationPackage_dict'])
#     df = df.reset_index(drop=True)
#     df_remuneration = df_remuneration.reset_index(drop=True)

#     print(df_remuneration.columns)


#     df_extended = pd.concat([df, df_remuneration], axis=1)
#     print(df_extended.shape)
#     df_extended.drop(['profile_remunerationPackage', 'profile_remunerationPackage_dict'], axis=1, inplace=True)
#     print(df_extended.shape)

#     conditions = [
#     df_extended['salary.amount'].notna(),
#     df_extended['salary.min'].notna() & df_extended['salary.max'].notna(),
#     df_extended['salary.min'].notna(),
#     df_extended['salary.max'].notna(),
#     ]

#     choices = [
#         df_extended['salary.amount'],
#         (df_extended['salary.min'] + df_extended['salary.max']) / 2,
#         df_extended['salary.min'],
#         df_extended['salary.max'],
#     ]

#     df_extended['salary_final'] = np.select(conditions, choices, default=np.nan)

#     df_extended = df_extended[~df_extended['salary_final'].isna()]
#     print(df_extended.shape)

       

#     for period in ['hour', 'month', 'year']:
#         for key in ['min', 'max']:
#             df_extended[f'{period}_{key}'] = get_limit(country_code, period, key)

#     conditions = [
#         df_extended['salary_final'].between(df_extended['month_min'], df_extended['month_max']),
#         df_extended['salary_final'].between(df_extended['year_min'], df_extended['year_max']),
#         df_extended['salary_final'].between(df_extended['hour_min'], df_extended['hour_max']),
#     ]
#     choices = ['month', 'year', 'hour']

#     df_extended['salary.period'] = np.select(conditions, choices, default='UNK')

#     # df_extended = df_extended[~df_extended['salary.period'].isna()]
#     # df_extended['salary.period'].fillna('month')
#     df_extended = df_extended[df_extended['salary.period'] != 'once']
#     print(df_extended.shape)
#     df_extended = df_extended[df_extended['salary.period'] != 'hour']
#     print(df_extended.shape)
#     df_extended = df_extended[df_extended['salary.period'] != 'UNK']
#     print(df_extended.shape)

#     # df_extended = df_extended[df_extended['profile_workSchedule'] == '["fulltime"]']
#     # print(df_extended.shape)
   

#     df_extended['annual_salary'] = df_extended.apply(lambda row: calculate_salary(row, country_code), axis=1)

#     print(df_extended.shape)
#     df_extended.dropna(subset=['annual_salary', 'profile_description'], inplace=True)
#     print(df_extended.shape)
#     df_extended['profile_skills_list'] = df_extended['profile_skills'].apply(json.loads)
#     print(df_extended.shape)
#     df_extended[df_extended['profile_skills_list'].apply(len) >=  1]
#     print(df_extended.shape)


#     # df_extended_sample  = df_extended.sample(n=500, random_state=42)

#     skill_extractor = SkillExtractor()

#     batch_size = 5000   
#     processed_batches = []

#     for i in range(0, len(df_extended), batch_size):
#         print(f'Processing batch {i // batch_size + 1} of {len(df_extended) // batch_size + 1}')
#         batch = df_extended.iloc[i:i + batch_size].copy()
#         batch['Extracted Skills'] = skill_extractor.get_skills(batch['profile_description'].tolist())
#         processed_batches.append(batch)

#     df_final = pd.concat(processed_batches, ignore_index=True)

#     df_final.to_csv(f'files/extracted/{OUTPUT_CSV_FILE}', index=False, sep=';')
import os
import json
import numpy as np
import pandas as pd
import torch

from esco_skill_extractor import SkillExtractor #github 


# ============================================================
# ΡΥΘΜΙΣΕΙΣ
# ============================================================

RAW_DIRECTORY = "files/raw"
OUTPUT_DIRECTORY = "files/extracted"

# Ξεκίνα με 256.
# Αν λειτουργεί χωρίς πρόβλημα, μπορείς να δοκιμάσεις 512.
BATCH_SIZE = 256

# Εμφανίζει πρόοδο κάθε τόσα batches.
PROGRESS_EVERY = 10


# ============================================================
# ΕΠΙΛΟΓΗ GPU / CPU
# ============================================================

if torch.backends.mps.is_available():
    DEVICE = torch.device("mps")
elif torch.cuda.is_available():
    DEVICE = torch.device("cuda")
else:
    DEVICE = torch.device("cpu")

print(f"Συσκευή επεξεργασίας: {DEVICE}")


# ============================================================
# ΟΡΙΑ ΜΙΣΘΩΝ
# ============================================================

salary_limits_dict = {
    # Ενεργή μόνο η Ολλανδία.
    # Αφαίρεσε τα # από κάποια χώρα όταν θέλεις να την επεξεργαστείς.

    # "fr": {
    #     "hour": {"min": 10, "max": 500},
    #     "month": {"min": 1500, "max": 20000},
    #     "year": {"min": 21600, "max": 300000}
    # },

    # "be": {
    #     "hour": {"min": 12, "max": 600},
    #     "month": {"min": 1800, "max": 25000},
    #     "year": {"min": 25000, "max": 350000}
    # },

    "cs": {
    "hour":  {"min": 80, "max": 3000},
    "month": {"min": 15000, "max": 500000},
    "year":  {"min": 180000, "max": 6000000}
    }
    ,

    # "de": {
    #     "hour": {"min": 12, "max": 600},    
    #     "month": {"min": 1900, "max": 25000},
    #     "year": {"min": 26000, "max": 350000}
    # },

    # "el": {
    #     "hour": {"min": 6, "max": 300},
    #     "month": {"min": 900, "max": 12000},
    #     "year": {"min": 12000, "max": 180000}
    # },

    # "sv": {
    #     "hour": {"min": 15, "max": 700},
    #     "month": {"min": 2000, "max": 28000},
    #     "year": {"min": 28000, "max": 400000}
    # },

    # "nl": {
    #     "hour": {"min": 12, "max": 600},
    #     "month": {"min": 2300, "max": 25000},
    #     "year": {"min": 27600, "max": 350000}
    # }
}


# ============================================================
# ΒΟΗΘΗΤΙΚΕΣ ΣΥΝΑΡΤΗΣΕΙΣ
# ============================================================

def safe_json_loads(value, default_value):
    """
    Μετατρέπει JSON string σε Python dictionary ή list.
    Σε περίπτωση λάθους επιστρέφει την default τιμή.
    """

    if value is None:
        return default_value

    if isinstance(value, (dict, list)):
        return value

    try:
        if pd.isna(value):
            return default_value
    except (TypeError, ValueError):
        pass

    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError, ValueError):
        return default_value


def get_limit(country_code, period, key):
    """
    Επιστρέφει το αντίστοιχο όριο μισθού.
    """

    country_limits = salary_limits_dict.get(country_code)

    if country_limits is None:
        return np.nan

    period_limits = country_limits.get(period)

    if period_limits is None:
        return np.nan

    return period_limits.get(key, np.nan)


def calculate_salary(row, country_code):
    """
    Μετατρέπει τον μισθό σε ετήσιο μισθό.
    """

    period = row.get("salary.period")
    salary_value = row.get("salary_final")

    if pd.isna(salary_value):
        return np.nan

    country_limits = salary_limits_dict.get(country_code)

    if country_limits is None:
        return np.nan

    period_limits = country_limits.get(period)

    if period_limits is None:
        return np.nan

    minimum = period_limits["min"]
    maximum = period_limits["max"]

    if not minimum <= salary_value <= maximum:
        return np.nan

    if period == "month":
        return salary_value * 12

    if period == "hour":
        return salary_value * 35 * 4.33 * 12

    if period == "year":
        return salary_value

    return np.nan


def move_extractor_to_device(skill_extractor, device):
    """
    Μεταφέρει το εσωτερικό μοντέλο του SkillExtractor στη GPU.
    """

    possible_attributes = [
        "_model",
        "model",
        "sentence_transformer",
        "embedding_model",
        "transformer",
        "encoder"
    ]

    for attribute_name in possible_attributes:
        if not hasattr(skill_extractor, attribute_name):
            continue

        model = getattr(skill_extractor, attribute_name)

        if not hasattr(model, "to"):
            continue

        try:
            model.to(device)
            print(f"SkillExtractor: {device}")
            return True
        except Exception:
            continue

    for attribute_name, attribute_value in vars(skill_extractor).items():
        if not hasattr(attribute_value, "to"):
            continue

        try:
            attribute_value.to(device)
            print(f"SkillExtractor: {device}")
            return True
        except Exception:
            continue

    print("Το μοντέλο δεν μεταφέρθηκε στη GPU και ίσως τρέξει στη CPU.")
    return False


# ============================================================
# ΕΛΕΓΧΟΣ ΦΑΚΕΛΩΝ
# ============================================================

if not os.path.isdir(RAW_DIRECTORY):
    raise FileNotFoundError(
        f"Δεν βρέθηκε ο φάκελος: {RAW_DIRECTORY}"
    )

os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)


# ============================================================
# ΕΥΡΕΣΗ ΑΡΧΕΙΩΝ
# ============================================================

files = sorted(
    file_name
    for file_name in os.listdir(RAW_DIRECTORY)
    if file_name.endswith(".parquet")
)

if not files:
    raise FileNotFoundError(
        f"Δεν βρέθηκαν parquet αρχεία στον φάκελο {RAW_DIRECTORY}"
    )


# ============================================================
# ΔΗΜΙΟΥΡΓΙΑ SKILL EXTRACTOR
# ============================================================

print("Φόρτωση SkillExtractor...")

skill_extractor = SkillExtractor()

move_extractor_to_device(
    skill_extractor,
    DEVICE
)


# ============================================================
# ΕΠΕΞΕΡΓΑΣΙΑ ΑΡΧΕΙΩΝ
# ============================================================

processed_country_count = 0

for file_name in files:

    name_without_extension = os.path.splitext(file_name)[0]
    file_parts = name_without_extension.split("_")

    if len(file_parts) < 3:
        continue

    country_code = file_parts[-1].lower()

    # Επεξεργαζόμαστε μόνο τις χώρες που υπάρχουν στο dictionary.
    if country_code not in salary_limits_dict:
        continue

    processed_country_count += 1

    input_file = os.path.join(
        RAW_DIRECTORY,
        file_name
    )

    output_file = os.path.join(
        OUTPUT_DIRECTORY,
        f"extracted_skills_{country_code}.csv"
    )

    print()
    print(f"Χώρα: {country_code.upper()}")

    # --------------------------------------------------------
    # ΑΝΑΓΝΩΣΗ PARQUET
    # --------------------------------------------------------

    df = pd.read_parquet(input_file)

    required_columns = [
        "profile_remunerationPackage",
        "profile_description"
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        print(f"Παράλειψη: λείπουν οι στήλες {missing_columns}")
        continue

    # --------------------------------------------------------
    # REMUNERATION PACKAGE
    # --------------------------------------------------------

    df = df[
        df["profile_remunerationPackage"].notna()
    ].copy()

    if df.empty:
        print("Δεν υπάρχουν εγγραφές με μισθό.")
        continue

    df["profile_remunerationPackage_dict"] = (
        df["profile_remunerationPackage"]
        .apply(
            lambda value: safe_json_loads(
                value,
                {}
            )
        )
    )

    df_remuneration = pd.json_normalize(
        df["profile_remunerationPackage_dict"]
    )

    df = df.reset_index(drop=True)
    df_remuneration = df_remuneration.reset_index(drop=True)

    df_extended = pd.concat(
        [df, df_remuneration],
        axis=1
    )

    df_extended.drop(
        columns=[
            "profile_remunerationPackage",
            "profile_remunerationPackage_dict"
        ],
        inplace=True,
        errors="ignore"
    )

    # --------------------------------------------------------
    # ΜΙΣΘΟΣ
    # --------------------------------------------------------

    salary_columns = [
        "salary.amount",
        "salary.min",
        "salary.max"
    ]

    for column in salary_columns:
        if column not in df_extended.columns:
            df_extended[column] = np.nan

        df_extended[column] = pd.to_numeric(
            df_extended[column],
            errors="coerce"
        )

    salary_conditions = [
        df_extended["salary.amount"].notna(),

        (
            df_extended["salary.min"].notna()
            & df_extended["salary.max"].notna()
        ),

        df_extended["salary.min"].notna(),

        df_extended["salary.max"].notna()
    ]

    salary_choices = [
        df_extended["salary.amount"],

        (
            df_extended["salary.min"]
            + df_extended["salary.max"]
        ) / 2,

        df_extended["salary.min"],

        df_extended["salary.max"]
    ]

    df_extended["salary_final"] = np.select(
        salary_conditions,
        salary_choices,
        default=np.nan
    )

    df_extended = df_extended[
        df_extended["salary_final"].notna()
    ].copy()

    if df_extended.empty:
        print("Δεν υπάρχουν έγκυρες τιμές μισθού.")
        continue

    # --------------------------------------------------------
    # ΟΡΙΑ ΑΝΑ ΠΕΡΙΟΔΟ
    # --------------------------------------------------------

    for period in ["hour", "month", "year"]:
        for key in ["min", "max"]:
            df_extended[f"{period}_{key}"] = get_limit(
                country_code,
                period,
                key
            )

    # --------------------------------------------------------
    # ΑΝΑΓΝΩΡΙΣΗ ΠΕΡΙΟΔΟΥ ΜΙΣΘΟΥ
    # --------------------------------------------------------

    period_conditions = [
        df_extended["salary_final"].between(
            df_extended["month_min"],
            df_extended["month_max"]
        ),

        df_extended["salary_final"].between(
            df_extended["year_min"],
            df_extended["year_max"]
        ),

        df_extended["salary_final"].between(
            df_extended["hour_min"],
            df_extended["hour_max"]
        )
    ]

    period_choices = [
        "month",
        "year",
        "hour"
    ]

    df_extended["salary.period"] = np.select(
        period_conditions,
        period_choices,
        default="UNK"
    )

    # Κρατάμε μόνο μηνιαίες και ετήσιες τιμές.
    df_extended = df_extended[
        df_extended["salary.period"].isin(
            ["month", "year"]
        )
    ].copy()

    if df_extended.empty:
        print("Δεν έμειναν εγγραφές μετά το salary filtering.")
        continue

    # --------------------------------------------------------
    # ΕΤΗΣΙΟΣ ΜΙΣΘΟΣ
    # --------------------------------------------------------

    df_extended["annual_salary"] = df_extended.apply(
        lambda row: calculate_salary(
            row,
            country_code
        ),
        axis=1
    )

    df_extended.dropna(
        subset=[
            "annual_salary",
            "profile_description"
        ],
        inplace=True
    )

    # --------------------------------------------------------
    # ΚΑΘΑΡΙΣΜΟΣ ΠΕΡΙΓΡΑΦΗΣ
    # --------------------------------------------------------

    df_extended["profile_description"] = (
        df_extended["profile_description"]
        .astype(str)
        .str.strip()
    )

    df_extended = df_extended[
        df_extended["profile_description"].ne("")
        & df_extended["profile_description"].str.lower().ne("nan")
    ].copy()

    if df_extended.empty:
        print("Δεν υπάρχουν περιγραφές για ανάλυση.")
        continue

    # Δεν φιλτράρουμε με βάση το profile_skills.
    # Το ESCO θα αναλύσει όλες τις διαθέσιμες περιγραφές.

    # --------------------------------------------------------
    # SKILL EXTRACTION
    # --------------------------------------------------------

    total_rows = len(df_extended)

    total_batches = (
        total_rows + BATCH_SIZE - 1
    ) // BATCH_SIZE

    print(f"Αγγελίες: {total_rows:,}")
    print(f"Batches: {total_batches:,}")

    processed_batches = []

    for batch_number, start_index in enumerate(
        range(0, total_rows, BATCH_SIZE),
        start=1
    ):

        end_index = min(
            start_index + BATCH_SIZE,
            total_rows
        )

        if (
            batch_number == 1
            or batch_number % PROGRESS_EVERY == 0
            or batch_number == total_batches
        ):
            progress = batch_number / total_batches * 100

            print(
                f"Πρόοδος: {progress:5.1f}% "
                f"({batch_number}/{total_batches})"
            )

        batch = df_extended.iloc[
            start_index:end_index
        ].copy()

        descriptions = (
            batch["profile_description"]
            .fillna("")
            .astype(str)
            .tolist()
        )

        try:
            batch["Extracted Skills"] = (
                skill_extractor.get_skills(
                    descriptions
                )
            )

        except RuntimeError as error:
            error_message = str(error).lower()

            if "out of memory" in error_message:
                print()
                print("Δεν επαρκεί η μνήμη της GPU.")
                print("Μείωσε το BATCH_SIZE σε 128 ή 64.")

            raise

        processed_batches.append(batch)

    # --------------------------------------------------------
    # ΑΠΟΘΗΚΕΥΣΗ
    # --------------------------------------------------------

    if not processed_batches:
        print("Δεν δημιουργήθηκαν αποτελέσματα.")
        continue

    df_final = pd.concat(
        processed_batches,
        ignore_index=True
    )

    df_final.to_csv(
        output_file,
        index=False,
        sep=";"
    )

    print(f"Ολοκληρώθηκε: {len(df_final):,} εγγραφές")
    print(f"Αρχείο: {output_file}")


# ============================================================
# ΤΕΛΟΣ
# ============================================================

if processed_country_count == 0:
    print()
    print(
        "Δεν βρέθηκε αρχείο για κάποια ενεργή χώρα "
        "του salary_limits_dict."
    )
else:
    print()
    print("Η επεξεργασία ολοκληρώθηκε.")