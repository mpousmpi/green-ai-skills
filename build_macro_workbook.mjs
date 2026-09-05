import fs from "node:fs/promises";
import path from "node:path";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const outputDir = "outputs/macro-economic-research";
const panel = JSON.parse(await fs.readFile(path.join(outputDir, "macro_panel.json"), "utf8"));
const workbook = Workbook.create();
const green = "#166534", dark = "#14532D", pale = "#DCFCE7", gold = "#F59E0B", light = "#F8FAFC";

function title(sheet, range, text) {
  sheet.getRange(range).merge();
  sheet.getRange(range.split(":")[0]).values = [[text]];
  sheet.getRange(range).format = { fill: dark, font: { bold: true, color: "#FFFFFF", size: 16 }, rowHeight: 30, verticalAlignment: "center" };
}
function header(range) {
  range.format = { fill: green, font: { bold: true, color: "#FFFFFF" }, wrapText: true, verticalAlignment: "center" };
}

const readme = workbook.worksheets.add("README");
readme.showGridLines = false;
title(readme, "A1:F1", "Macroeconomic research dataset — GenAI skills thesis");
readme.getRange("A3:B12").values = [
  ["Item", "Description"],
  ["Countries", "Belgium, Czechia, Germany, Greece, Spain, France, Netherlands, Sweden"],
  ["Period", "2019–2024 annual panel (48 country-year observations)"],
  ["Purpose", "Country-level controls and descriptive context for wage/skills analysis"],
  ["Primary sources", "Eurostat, OECD and World Bank — official sites/APIs only"],
  ["Salary recommendation", "Use OECD PPP wage for cross-country comparisons; use Eurostat EUR salary for nominal EU reporting"],
  ["STEM definition", "Tertiary graduates in ISCED-F 05 Natural sciences, 06 ICT, 07 Engineering/manufacturing/construction"],
  ["Missing values", "Kept blank; never replaced by zero. See Data Quality sheet."],
  ["Country codes", "Eurostat uses EL for Greece; World Bank uses GR/GRC; OECD uses GRC."],
  ["Causal caution", "Country indicators are contextual controls; with only 8 countries, avoid strong causal claims."],
];
header(readme.getRange("A3:B3"));
readme.getRange("A4:A12").format.font = { bold: true };
readme.getRange("A3:B12").format.borders = { preset: "outside", style: "thin", color: "#A7C7B3" };
readme.getRange("A1:A12").format.columnWidth = 25;
readme.getRange("B1:B12").format.columnWidth = 95;
readme.getRange("A3:B12").format.wrapText = true;

const headers = Object.keys(panel[0]);
const panelSheet = workbook.worksheets.add("Panel 2019-2024");
panelSheet.showGridLines = false;
panelSheet.getRangeByIndexes(0, 0, panel.length + 1, headers.length).values = [headers, ...panel.map(r => headers.map(h => r[h] ?? null))];
header(panelSheet.getRangeByIndexes(0, 0, 1, headers.length));
panelSheet.freezePanes.freezeRows(1);
panelSheet.freezePanes.freezeColumns(3);
panelSheet.getRange("A1:Q49").format.font = { name: "Aptos", size: 10 };
panelSheet.getRange("A1:Q1").format.rowHeight = 48;
panelSheet.getRange("A1:B49").format.columnWidth = 16;
panelSheet.getRange("C1:C49").format.columnWidth = 9;
panelSheet.getRange("D1:Q49").format.columnWidth = 20;
panelSheet.getRange("D2:Q49").format.numberFormat = "#,##0.0";
panelSheet.getRange("L2:L49").format.numberFormat = "#,##0";
panelSheet.getRange("N2:N49").format.numberFormat = "€#,##0";
panelSheet.getRange("P2:P49").format.numberFormat = "$#,##0";
panelSheet.getRange("Q2:Q49").format.numberFormat = "€#,##0";
panelSheet.getRange("A1:Q49").format.wrapText = true;

const latest = workbook.worksheets.add("Latest 2024");
latest.showGridLines = false;
title(latest, "A1:I1", "Latest comparable indicators (2024)");
const latestHeaders = ["Country code", "Country", "Salary EUR (Eurostat)", "Wage PPP USD (OECD)", "STEM graduates / 1,000", "GDP pc PPP", "GDP growth %", "Unemployment %", "R&D % GDP (latest available)"];
latest.getRange("A3:I3").values = [latestHeaders]; header(latest.getRange("A3:I3"));
const countryRows = [...new Map(panel.map(r => [r.country_code, r.country])).entries()];
latest.getRange("A4:B11").values = countryRows;
for (let row = 4; row <= 11; row++) {
  const formulas = [];
  for (const col of [14, 16, 15, 4, 5, 6]) {
    const letter = String.fromCharCode(64 + col);
    formulas.push(`=IF(SUMIFS('Panel 2019-2024'!$${letter}$2:$${letter}$49,'Panel 2019-2024'!$A$2:$A$49,$A${row},'Panel 2019-2024'!$C$2:$C$49,2024)=0,"",SUMIFS('Panel 2019-2024'!$${letter}$2:$${letter}$49,'Panel 2019-2024'!$A$2:$A$49,$A${row},'Panel 2019-2024'!$C$2:$C$49,2024))`);
  }
  latest.getRange(`C${row}:H${row}`).formulas = [formulas];
  latest.getRange(`I${row}`).formulas = [[`=IF(COUNTIFS('Panel 2019-2024'!$A$2:$A$49,$A${row},'Panel 2019-2024'!$C$2:$C$49,2023)=0,"",SUMIFS('Panel 2019-2024'!$H$2:$H$49,'Panel 2019-2024'!$A$2:$A$49,$A${row},'Panel 2019-2024'!$C$2:$C$49,2023))`]];
}
latest.getRange("C4:C11").format.numberFormat = "€#,##0";
latest.getRange("D4:D11").format.numberFormat = "$#,##0";
latest.getRange("E4:I11").format.numberFormat = "#,##0.0";
latest.getRange("A3:I11").format.borders = { preset: "outside", style: "thin", color: "#A7C7B3" };
latest.getRange("A1:A11").format.columnWidth = 14;
latest.getRange("B1:B11").format.columnWidth = 18;
latest.getRange("C1:I11").format.columnWidth = 21;
latest.getRange("A3:I11").format.wrapText = true;
latest.getRange("C4:I11").conditionalFormats.add("colorScale", { colors: ["#FEE2E2", "#FEF3C7", "#DCFCE7"], thresholds: ["min", "50%", "max"] });
latest.getRange("A13:I15").values = [
  ["Interpretation note", null, null, null, null, null, null, null, null],
  ["PPP wages", "Preferred for comparing purchasing power across countries; constant 2025 USD PPP.", null, null, null, null, null, null, null],
  ["R&D 2024", "World Bank 2024 values were not yet available; the summary shows 2023, clearly labelled.", null, null, null, null, null, null, null],
];
latest.getRange("B14:I14").merge();
latest.getRange("B15:I15").merge();
latest.getRange("A13:I13").format = { fill: gold, font: { bold: true, color: "#FFFFFF" } };
latest.getRange("A14:I15").format.wrapText = true;
latest.getRange("A14:I15").format.rowHeight = 36;
latest.getRange("A14:A15").format.font = { bold: true };
latest.getRange("A14:I15").format.verticalAlignment = "center";

const sources = workbook.worksheets.add("Sources & Definitions");
sources.showGridLines = false;
const sourceRows = [
  ["World Bank", "GDP per capita, PPP", "NY.GDP.PCAP.PP.KD", "GDP per capita in constant 2021 international dollars, PPP", "constant 2021 international $", "https://data.worldbank.org/indicator/NY.GDP.PCAP.PP.KD"],
  ["World Bank", "Real GDP growth", "NY.GDP.MKTP.KD.ZG", "Annual percentage growth of GDP at market prices", "%", "https://data.worldbank.org/indicator/NY.GDP.MKTP.KD.ZG"],
  ["World Bank", "Unemployment", "SL.UEM.TOTL.ZS", "Share of total labor force without work and seeking employment (ILO estimate)", "% labor force", "https://data.worldbank.org/indicator/SL.UEM.TOTL.ZS"],
  ["World Bank", "Inflation", "FP.CPI.TOTL.ZG", "Annual percentage change in consumer price index", "%", "https://data.worldbank.org/indicator/FP.CPI.TOTL.ZG"],
  ["World Bank", "R&D expenditure", "GB.XPD.RSDV.GD.ZS", "Gross domestic expenditure on research and development", "% GDP", "https://data.worldbank.org/indicator/GB.XPD.RSDV.GD.ZS"],
  ["World Bank", "Labor productivity", "SL.GDP.PCAP.EM.KD", "GDP per person employed", "constant 2021 PPP $", "https://data.worldbank.org/indicator/SL.GDP.PCAP.EM.KD"],
  ["World Bank", "Tertiary enrollment", "SE.TER.ENRR", "Total tertiary enrollment regardless of age relative to official tertiary-age population", "gross %", "https://data.worldbank.org/indicator/SE.TER.ENRR"],
  ["World Bank", "Internet users", "IT.NET.USER.ZS", "Individuals using the Internet", "% population", "https://data.worldbank.org/indicator/IT.NET.USER.ZS"],
  ["World Bank", "Population", "SP.POP.TOTL", "Total population", "persons", "https://data.worldbank.org/indicator/SP.POP.TOTL"],
  ["World Bank", "Trade openness", "NE.TRD.GNFS.ZS", "Exports plus imports of goods and services", "% GDP", "https://data.worldbank.org/indicator/NE.TRD.GNFS.ZS"],
  ["Eurostat", "Average full-time adjusted salary", "nama_10_fte", "Average annual salary adjusted to full-time equivalent using national accounts and EU-LFS", "current EUR", "https://ec.europa.eu/eurostat/cache/metadata/en/nama_10_fte_esms.htm"],
  ["Eurostat", "Tertiary STEM graduates", "educ_uoe_grad04", "Graduates in ISCED-F fields 05, 06 and 07 at tertiary levels 5–8", "per 1,000 inhabitants", "https://ec.europa.eu/eurostat/web/education-and-training/information-data"],
  ["OECD", "Average annual wages", "DSD_EARNINGS@AV_AN_WAGE", "Average annual wages per full-time-equivalent dependent employee; PPP series uses constant 2025 prices", "USD PPP / EUR", "https://www.oecd.org/en/data/indicators/average-annual-wages.html"],
  ["European Commission", "EURES job-advert source", "EURES", "Country identification was verified from country_code in the local parquet files", "job adverts", "https://eures.europa.eu/index_en"],
];
sources.getRange("A1:F15").values = [["Organisation", "Indicator", "Dataset code", "Definition", "Unit", "Official source URL"], ...sourceRows];
header(sources.getRange("A1:F1"));
sources.freezePanes.freezeRows(1);
sources.getRange("A1:C15").format.columnWidth = 24;
sources.getRange("D1:D15").format.columnWidth = 60;
sources.getRange("E1:E15").format.columnWidth = 24;
sources.getRange("F1:F15").format.columnWidth = 70;
sources.getRange("A1:F15").format.wrapText = true;
sources.getRange("A1:F15").format.borders = { preset: "outside", style: "thin", color: "#CBD5E1" };

const quality = workbook.worksheets.add("Data Quality");
quality.showGridLines = false;
title(quality, "A1:E1", "Coverage and limitations");
quality.getRange("A3:E3").values = [["Variable", "Expected observations", "Available", "Missing", "Treatment / note"]]; header(quality.getRange("A3:E3"));
const qualityVars = headers.slice(3);
const qualityRows = qualityVars.map(v => {
  const available = panel.filter(r => r[v] !== null && r[v] !== undefined).length;
  let note = "Use observed value; leave missing blank.";
  if (v === "rd_expenditure_percent_gdp") note = "2024 unavailable for all 8 countries; latest summary uses 2023.";
  if (v === "avg_full_time_adjusted_salary_eur") note = "Eurostat does not provide Netherlands in this table; use OECD wage series for complete comparison.";
  if (v === "avg_annual_wage_eur") note = "EUR series unavailable for Czechia and Sweden; PPP series is complete.";
  return [v, 48, available, 48 - available, note];
});
quality.getRangeByIndexes(3, 0, qualityRows.length, 5).values = qualityRows;
quality.getRange("A3:E17").format.borders = { preset: "outside", style: "thin", color: "#CBD5E1" };
quality.getRange("A1:A17").format.columnWidth = 48;
quality.getRange("B1:D17").format.columnWidth = 18;
quality.getRange("E1:E17").format.columnWidth = 72;
quality.getRange("A3:E17").format.wrapText = true;
quality.getRange("D4:D17").conditionalFormats.add("cellIs", { operator: "greaterThan", formula: 0, format: { fill: "#FEF3C7", font: { color: "#92400E", bold: true } } });

await fs.mkdir(outputDir, { recursive: true });
for (const name of ["README", "Latest 2024", "Panel 2019-2024", "Sources & Definitions", "Data Quality"]) {
  const preview = await workbook.render({ sheetName: name, autoCrop: "all", scale: 1, format: "png" });
  await fs.writeFile(path.join(outputDir, `preview_${name.replaceAll(/[^A-Za-z0-9]+/g, "_")}.png`), new Uint8Array(await preview.arrayBuffer()));
}
const inspect = await workbook.inspect({ kind: "table", range: "Latest 2024!A1:I15", include: "values,formulas", tableMaxRows: 16, tableMaxCols: 10 });
console.log(inspect.ndjson);
const errors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A", options: { useRegex: true, maxResults: 200 }, summary: "final formula error scan" });
console.log(errors.ndjson);
const out = await SpreadsheetFile.exportXlsx(workbook);
await out.save(path.join(outputDir, "official_macro_indicators_2019_2024.xlsx"));
