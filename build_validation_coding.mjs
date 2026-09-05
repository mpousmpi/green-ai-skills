import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const inputPath = "files/cleaned/fr_validation_sample.csv";
const backupPath = "files/cleaned/fr_validation_sample_uncoded.csv";
const outputDir = "outputs/france-validation-coding";

const csvText = await fs.readFile(inputPath, "utf8");

function parseDelimited(text, delimiter = ";") {
  const rows = [];
  let row = [], field = "", quoted = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"' && text[i + 1] === '"') { field += '"'; i++; }
      else if (ch === '"') quoted = false;
      else field += ch;
    } else if (ch === '"') quoted = true;
    else if (ch === delimiter) { row.push(field); field = ""; }
    else if (ch === "\n") { row.push(field.replace(/\r$/, "")); rows.push(row); row = []; field = ""; }
    else field += ch;
  }
  if (field || row.length) { row.push(field.replace(/\r$/, "")); rows.push(row); }
  return rows;
}

const values = parseDelimited(csvText);
const workbook = Workbook.create();
const sheet = workbook.worksheets.add("Validation");
sheet.getRange("A1:T301").values = values;

if (values.length !== 301 || values[0].length !== 20) {
  throw new Error(`Unexpected validation shape: ${values.length}x${values[0]?.length}`);
}

const falseTechnical = new Set([
  138, 163, 165, 174, 180, 221, 227, 238, 255, 263, 291, 293,
]);
const missedTechnical = new Set([49]);
const categoryIncorrect = new Set([
  49, 121, 132, 138, 163, 165, 174, 180, 181, 207, 209, 220, 221,
  222, 227, 233, 238, 240, 244, 246, 248, 255, 263, 273, 291, 293,
]);
const softIncorrect = new Set([89, 91, 92]);

const notes = new Map([
  [49, "False negative: ουσιαστικός ρόλος software testing/QA· προτείνεται software."],
  [89, "Το initiative/responsibility βασίζεται σε ασθενή γενική διατύπωση και όχι σε σαφή απαίτηση δεξιότητας."],
  [91, "False positive soft skill: η customer interaction προέρχεται από κείμενο του agency· η θέση είναι χειριστής/διαλογή."],
  [92, "Οι soft αντιστοιχίσεις προέρχονται κυρίως από γενικό κείμενο του agency και όχι από τα καθήκοντα εργαστηρίου."],
  [121, "Η κύρια κατηγορία software λείπει από τη strict ταξινόμηση Java developer."],
  [132, "Η κύρια κατηγορία software λείπει από τη strict ταξινόμηση Tech Lead Java."],
  [138, "False positive: εμπορική θέση σε employment agency· το business intelligence σημαίνει πληροφόρηση αγοράς, όχι data analytics."],
  [163, "False positive: το γαλλικό développeur territorial σημαίνει land/territory development, όχι software developer."],
  [165, "False positive: διοικητικός international back-office agent, όχι software role."],
  [174, "False positive: καθαρά εμπορικός Business Developer IT χωρίς ουσιαστικά τεχνικά καθήκοντα."],
  [180, "False positive: land/territory developer για έργα ΑΠΕ, όχι software developer."],
  [181, "Data/ETL integration role: απαιτούνται data engineering/analysis κατηγορίες, όχι μόνο software."],
  [207, "Η cybersecurity είναι σωστή αλλά λείπει networks/systems από τον Systems, Networks & Security Administrator."],
  [209, "Λείπει networks/systems από τον Network and Cybersecurity Administrator."],
  [220, "IT maintenance/support role: η κύρια κατηγορία είναι networks/systems, όχι μόνο cybersecurity."],
  [221, "False positive: junior business-development position· η αναφορά security αφορά το εμπορικό πεδίο."],
  [222, "Network expert: λείπει networks/systems από τη strict κατηγοριοποίηση."],
  [227, "False positive: electrical power-network engineer, όχι ICT networks/systems."],
  [233, "Systems and Networks Manager: λείπει networks/systems."],
  [238, "False positive: process/piping project manager· το safety δεν είναι cybersecurity."],
  [240, "Systems and Networks Administrator: λείπει networks/systems."],
  [244, "Γενικός IT technician: η κατηγορία cybersecurity δεν τεκμηριώνεται ως κύρια· προτείνεται networks/systems."],
  [246, "IT support N1/N2: προτείνεται networks/systems αντί cloud/DevOps."],
  [248, "Java/C#/React developer: λείπει η κύρια κατηγορία software."],
  [255, "False positive: εμπορικός ρόλος luxury-sector business development, χωρίς τεχνική υλοποίηση Data/AI."],
  [263, "False positive λόγω ακρωνυμίου IA: association intermédiaire/provisioning officer, καμία σχέση με artificial intelligence."],
  [273, "Business applications/Power BI/SQL role: λείπουν data analysis και software από τη strict κατηγοριοποίηση."],
  [291, "False positive: accounting document-validation role που ελέγχει έξοδο AI, χωρίς ανάπτυξη ή τεχνική εργασία AI."],
  [293, "False positive: SaaS/AI sales manager· εμπορικός ρόλος χωρίς τεχνικά καθήκοντα AI."],
]);

for (let i = 1; i <= 300; i++) {
  const stratum = String(values[i][0] ?? "");
  let isTechnical = !["neither", "soft_only"].includes(stratum);
  if (falseTechnical.has(i)) isTechnical = false;
  if (missedTechnical.has(i)) isTechnical = true;
  values[i][16] = isTechnical ? "yes" : "no";
  values[i][17] = categoryIncorrect.has(i) ? "no" : "yes";
  values[i][18] = softIncorrect.has(i) ? "no" : "yes";
  values[i][19] = notes.get(i) ?? "Reviewed against title, duties, mapped skills and detection sources.";
}

sheet.getRange("A1:T301").values = values;
sheet.name = "Validation";
sheet.freezePanes.freezeRows(1);
sheet.freezePanes.freezeColumns(3);
sheet.showGridLines = false;
sheet.getRange("A1:T1").format = {
  fill: "#166534",
  font: { bold: true, color: "#FFFFFF" },
  wrapText: true,
  verticalAlignment: "center",
};
sheet.getRange("A2:T301").format.font = { name: "Aptos", size: 10 };
sheet.getRange("Q2:S301").format.horizontalAlignment = "center";
sheet.getRange("Q2:S301").dataValidation = {
  rule: { type: "list", values: ["yes", "no", "uncertain"] },
};
sheet.getRange("A2:A301").format.columnWidth = 18;
sheet.getRange("B2:B301").format.columnWidth = 20;
sheet.getRange("C2:C301").format.columnWidth = 34;
sheet.getRange("D2:D301").format.columnWidth = 72;
sheet.getRange("E2:E301").format.columnWidth = 14;
sheet.getRange("F2:P301").format.columnWidth = 24;
sheet.getRange("Q2:S301").format.columnWidth = 18;
sheet.getRange("T2:T301").format.columnWidth = 54;
sheet.getRange("C2:D301").format.wrapText = true;
sheet.getRange("G2:T301").format.wrapText = true;
sheet.getRange("Q2:S301").conditionalFormats.add("containsText", {
  text: "no", format: { fill: "#FEE2E2", font: { color: "#991B1B", bold: true } },
});
sheet.getRange("Q2:S301").conditionalFormats.add("containsText", {
  text: "yes", format: { fill: "#DCFCE7", font: { color: "#166534" } },
});

const summary = workbook.worksheets.add("Coding Summary");
summary.showGridLines = false;
summary.getRange("A1:F1").merge();
summary.getRange("A1").values = [["France validation sample — manual semantic coding"]];
summary.getRange("A1:F1").format = {
  fill: "#14532D", font: { bold: true, color: "#FFFFFF", size: 16 },
  rowHeight: 30, verticalAlignment: "center",
};
summary.getRange("A3:B8").values = [
  ["Metric", "Value"],
  ["Reviewed adverts", 300],
  ["Manually technical", null],
  ["Technical coding disagreements", null],
  ["Technical category disagreements", null],
  ["Soft-skill disagreements", null],
];
summary.getRange("B5").formulas = [["=COUNTIF('Validation'!$Q$2:$Q$301,\"yes\")"]];
summary.getRange("B6").formulas = [["=COUNTIFS('Validation'!$Q$2:$Q$51,\"yes\")+COUNTIFS('Validation'!$Q$52:$Q$101,\"yes\")+COUNTIFS('Validation'!$Q$102:$Q$301,\"no\")"]];
summary.getRange("B7").formulas = [["=COUNTIF('Validation'!$R$2:$R$301,\"no\")"]];
summary.getRange("B8").formulas = [["=COUNTIF('Validation'!$S$2:$S$301,\"no\")"]];
summary.getRange("A3:B3").format = { fill: "#166534", font: { bold: true, color: "#FFFFFF" } };
summary.getRange("A4:A8").format.font = { bold: true };
summary.getRange("A3:B8").format.borders = { preset: "outside", style: "thin", color: "#A7C7B3" };
summary.getRange("A10:F10").values = [["Coding rule", "yes", "no", "uncertain", "Unit of review", "Interpretation"]];
summary.getRange("A11:F13").values = [
  ["manual_is_technical", "Substantive digital/ICT work", "No substantive digital/ICT work", "Evidence is ambiguous", "Job advert", "Not inferred from employer sector alone"],
  ["manual_categories_correct", "Detected set adequately matches duties", "False positive or material missing/wrong category", "Insufficient detail", "Job advert", "Checks both relevance and material omissions"],
  ["manual_soft_skills_correct", "Soft set is supported", "False positive/material omission", "Insufficient detail", "Job advert", "Generic agency boilerplate is excluded"],
];
summary.getRange("A10:F10").format = { fill: "#166534", font: { bold: true, color: "#FFFFFF" }, wrapText: true };
summary.getRange("A11:F13").format.wrapText = true;
summary.getRange("A10:F13").format.borders = { preset: "outside", style: "thin", color: "#A7C7B3" };
summary.getRange("A1:A13").format.columnWidth = 38;
summary.getRange("B1:B13").format.columnWidth = 28;
summary.getRange("C1:D13").format.columnWidth = 34;
summary.getRange("E1:E13").format.columnWidth = 22;
summary.getRange("F1:F13").format.columnWidth = 42;
summary.freezePanes.freezeRows(1);

await fs.mkdir(outputDir, { recursive: true });
try { await fs.access(backupPath); } catch { await fs.copyFile(inputPath, backupPath); }

function encode(value) {
  const s = value == null ? "" : String(value);
  return /[;"\n\r]/.test(s) ? `"${s.replaceAll('"', '""')}"` : s;
}
const codedCsv = values.map(row => row.map(encode).join(";")).join("\n") + "\n";
await fs.writeFile(inputPath, codedCsv, "utf8");

const preview = await workbook.render({ sheetName: "Coding Summary", range: "A1:F13", scale: 1.5, format: "png" });
await fs.writeFile(path.join(outputDir, "coding_summary.png"), new Uint8Array(await preview.arrayBuffer()));
const xlsx = await SpreadsheetFile.exportXlsx(workbook);
await xlsx.save(path.join(outputDir, "fr_validation_sample_coded.xlsx"));

const check = await workbook.inspect({ kind: "table", range: "Coding Summary!A1:F13", include: "values,formulas", tableMaxRows: 15, tableMaxCols: 8 });
console.log(check.ndjson);
const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 100 },
  summary: "final formula error scan",
});
console.log(errors.ndjson);
console.log(JSON.stringify({ csv: inputPath, backup: backupPath, xlsx: path.join(outputDir, "fr_validation_sample_coded.xlsx") }));
