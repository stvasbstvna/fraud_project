import fs from "node:fs/promises";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { SpreadsheetFile, Workbook } = require("@oai/artifact-tool");

const outputPath = "data/review/final_sms_dataset_audit.xlsx";
const previewDir = "outputs/final_dataset_workbook_preview";

const bankingCsv = await fs.readFile("data/final/banking_original_test.csv", "utf8");
const auditCsv = await fs.readFile("data/final/banking_decision_audit.csv", "utf8");
const metricsCsv = await fs.readFile("results/final_detectors/metrics_by_model_and_split.csv", "utf8");

function parseCSV(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    if (quoted) {
      if (char === '"' && text[i + 1] === '"') {
        field += '"';
        i++;
      } else if (char === '"') {
        quoted = false;
      } else {
        field += char;
      }
    } else if (char === '"') {
      quoted = true;
    } else if (char === ",") {
      row.push(field);
      field = "";
    } else if (char === "\n") {
      row.push(field.replace(/\r$/, ""));
      rows.push(row);
      row = [];
      field = "";
    } else {
      field += char;
    }
  }
  if (field.length || row.length) {
    row.push(field.replace(/\r$/, ""));
    rows.push(row);
  }
  return rows.map((values, rowIndex) => values.map(value => {
    if (rowIndex > 0 && /^-?\d+(?:\.\d+)?$/.test(value)) return Number(value);
    if (rowIndex > 0 && value === "True") return true;
    if (rowIndex > 0 && value === "False") return false;
    return value;
  }));
}

function writeCsvSheet(workbook, sheetName, csvText) {
  const values = parseCSV(csvText);
  const sheet = workbook.worksheets.add(sheetName);
  if (values.length && values[0].length) {
    sheet.getRangeByIndexes(0, 0, values.length, values[0].length).values = values;
  }
  return sheet;
}

const workbook = Workbook.create();
const summary = workbook.worksheets.add("Summary");
writeCsvSheet(workbook, "DetectorResults", metricsCsv);
writeCsvSheet(workbook, "BankingTest", bankingCsv);
writeCsvSheet(workbook, "DecisionAudit", auditCsv);
const equations = workbook.worksheets.add("Equations");
const sources = workbook.worksheets.add("Sources");

const headerStyle = {
  fill: "#1F4E78",
  font: { bold: true, color: "#FFFFFF" },
  wrapText: true,
  verticalAlignment: "center",
};
const sectionStyle = {
  fill: "#D9EAF7",
  font: { bold: true, color: "#1F1F1F" },
};

summary.showGridLines = false;
summary.getRange("A1:D1").merge();
summary.getRange("A1").values = [["Final SMS Dataset and Detector Audit"]];
summary.getRange("A1:D1").format = {
  fill: "#1F4E78",
  font: { bold: true, color: "#FFFFFF", fontSize: 16 },
  horizontalAlignment: "center",
  verticalAlignment: "center",
};
summary.getRange("A1:D1").format.rowHeight = 32;
summary.getRange("A3:B3").values = [["Dataset metric", "Value"]];
summary.getRange("A3:B3").format = sectionStyle;
summary.getRange("A4:A13").values = [
  ["Rows after exact deduplication"],
  ["Training rows"],
  ["Validation rows"],
  ["Banking test rows"],
  ["Banking phishing rows"],
  ["Banking non-phishing rows"],
  ["SmishTank banking rows"],
  ["SmishX banking rows"],
  ["Manual/rule conflicts"],
  ["Label-quality exclusions"],
];
summary.getRange("B4:B13").formulas = [
  ["=COUNTA('DecisionAudit'!$A$2:$A$2118)"],
  ["=COUNTIF('DecisionAudit'!$L$2:$L$2118,\"train\")"],
  ["=COUNTIF('DecisionAudit'!$L$2:$L$2118,\"validation\")"],
  ["=COUNTA('BankingTest'!$A$2:$A$157)"],
  ["=COUNTIF('BankingTest'!$R$2:$R$157,1)"],
  ["=COUNTIF('BankingTest'!$R$2:$R$157,0)"],
  ["=COUNTIF('BankingTest'!$E$2:$E$157,\"SmishTank\")"],
  ["=COUNTIF('BankingTest'!$E$2:$E$157,\"SmishX\")"],
  ["=COUNTIF('DecisionAudit'!$J$2:$J$2118,\"rule_adjudicated_manual_conflict\")"],
  ["=COUNTIF('DecisionAudit'!$L$2:$L$2118,\"excluded_label_quality\")"],
];

summary.getRange("A15:D15").merge();
summary.getRange("A15").values = [["Interpretation"]];
summary.getRange("A15:D15").format = { fill: "#F4B183", font: { bold: true, color: "#7F6000" } };
summary.getRange("A16:D19").merge();
summary.getRange("A16").values = [[
  "The banking test set is held out before training. Its class distribution is strongly imbalanced, so accuracy alone is not sufficient. Report recall, false-negative rate, ROC-AUC, and the confusion-matrix counts. Random Forest predicts all ten non-phishing banking controls as phishing in this run, which demonstrates why the confusion matrix must be shown."
]];
summary.getRange("A16:D19").format = { fill: "#FFF2CC", wrapText: true, verticalAlignment: "top" };
summary.getRange("A:A").format.columnWidth = 40;
summary.getRange("B:B").format.columnWidth = 18;
summary.getRange("C:D").format.columnWidth = 22;

const results = workbook.worksheets.getItem("DetectorResults");
const resultUsed = results.getUsedRange(true);
const resultRows = resultUsed.values.length;
results.showGridLines = false;
results.freezePanes.freezeRows(1);
results.getRange(`A1:M1`).format = headerStyle;
results.getRange("N1:R1").values = [[
  "accuracy_formula", "precision_formula", "recall_formula", "f1_formula", "fnr_formula",
]];
results.getRange("N1:R1").format = { fill: "#548235", font: { bold: true, color: "#FFFFFF" }, wrapText: true };
for (let row = 2; row <= resultRows; row++) {
  results.getRange(`N${row}:R${row}`).formulas = [[
    `=(H${row}+K${row})/(H${row}+I${row}+J${row}+K${row})`,
    `=K${row}/(K${row}+I${row})`,
    `=K${row}/(K${row}+J${row})`,
    `=2*O${row}*P${row}/(O${row}+P${row})`,
    `=J${row}/(J${row}+K${row})`,
  ]];
}
results.getRange(`D2:G${resultRows}`).format.numberFormat = "0.0000";
results.getRange(`L2:R${resultRows}`).format.numberFormat = "0.0000";
results.getRange("A:A").format.columnWidth = 30;
results.getRange("B:B").format.columnWidth = 16;
results.getRange("C:C").format.columnWidth = 10;
results.getRange("D:R").format.columnWidth = 15;

for (const [sheetName, headerRange] of [["BankingTest", "A1:AA1"], ["DecisionAudit", "A1:L1"]]) {
  const sheet = workbook.worksheets.getItem(sheetName);
  sheet.showGridLines = false;
  sheet.freezePanes.freezeRows(1);
  sheet.freezePanes.freezeColumns(2);
  sheet.getRange(headerRange).format = headerStyle;
  sheet.getRange("A:A").format.columnWidth = 27;
  sheet.getRange("B:B").format.columnWidth = 17;
  sheet.getRange("C:C").format.columnWidth = 58;
  sheet.getRange("C:C").format.wrapText = true;
}

equations.showGridLines = false;
equations.getRange("A1:C1").merge();
equations.getRange("A1").values = [["Equations Used in the Detector and Evaluation"]];
equations.getRange("A1:C1").format = {
  fill: "#1F4E78",
  font: { bold: true, color: "#FFFFFF", fontSize: 15 },
  horizontalAlignment: "center",
};
equations.getRange("A3:C3").values = [["Quantity", "Equation", "Meaning"]];
equations.getRange("A3:C3").format = sectionStyle;
equations.getRange("A4:C12").values = [
  ["Term frequency", "TF(t,d) = count(t,d) / sum_k count(k,d)", "Relative frequency of term t in document d."],
  ["Inverse document frequency", "IDF(t) = ln((1 + N) / (1 + DF(t))) + 1", "Downweights terms appearing in many documents."],
  ["TF-IDF", "TFIDF(t,d) = TF(t,d) × IDF(t)", "Text feature supplied to each classifier."],
  ["Logistic probability", "P(y=1|x) = 1 / (1 + exp(-(w^T x + b)))", "Estimated phishing probability."],
  ["Random Forest probability", "P_RF(y=1|x) = (1/T) × sum_t P_t(y=1|x)", "Mean probability across T decision trees."],
  ["Accuracy", "(TP + TN) / (TP + TN + FP + FN)", "Overall fraction classified correctly."],
  ["Precision", "TP / (TP + FP)", "Fraction of phishing predictions that are correct."],
  ["Recall", "TP / (TP + FN)", "Fraction of phishing rows detected."],
  ["F1", "2 × Precision × Recall / (Precision + Recall)", "Harmonic mean of precision and recall."],
];
equations.getRange("A14:C14").values = [["Quantity", "Equation", "Meaning"]];
equations.getRange("A14:C14").format = sectionStyle;
equations.getRange("A15:C17").values = [
  ["False-negative rate", "FN / (FN + TP)", "Share of phishing messages missed."],
  ["Attack success rate", "successful evasions / tested phishing rewrites", "Use after the paired rewrite set is completed."],
  ["Confidence drop", "P_original(phishing) - P_rewrite(phishing)", "Paired detector-confidence change after rewriting."],
];
equations.getRange("A:A").format.columnWidth = 27;
equations.getRange("B:B").format.columnWidth = 54;
equations.getRange("C:C").format.columnWidth = 58;
equations.getRange("A3:C17").format.wrapText = true;

sources.showGridLines = false;
sources.getRange("A1:F1").values = [["Dataset", "Raw rows", "Rows used after dedup", "Channel", "Role", "Source"]];
sources.getRange("A1:F1").format = headerStyle;
sources.getRange("A2:F3").values = [
  ["SmishX", 1200, 1106, "SMS", "Training, validation, and banking controls", "https://github.com/yizhu-joy/SmishX"],
  ["SmishTank", 1062, 1011, "SMS", "Training and banking phishing evaluation", "https://arxiv.org/abs/2402.18430"],
];
sources.getRange("A5:F5").merge();
sources.getRange("A5").values = [["Cross-model human/LLM email rows are excluded from the primary experiment because email and SMS are different channels/formats."]];
sources.getRange("A5:F5").format = { fill: "#FFF2CC", wrapText: true };
sources.getRange("A:A").format.columnWidth = 18;
sources.getRange("B:C").format.columnWidth = 17;
sources.getRange("D:D").format.columnWidth = 12;
sources.getRange("E:E").format.columnWidth = 42;
sources.getRange("F:F").format.columnWidth = 48;

await fs.mkdir(previewDir, { recursive: true });
for (const [sheetName, range] of [
  ["Summary", "A1:D19"],
  ["DetectorResults", `A1:R${resultRows}`],
  ["BankingTest", "A1:L18"],
  ["DecisionAudit", "A1:L18"],
  ["Equations", "A1:C17"],
  ["Sources", "A1:F5"],
]) {
  const preview = await workbook.render({ sheetName, range, scale: 1.15, format: "png" });
  await fs.writeFile(`${previewDir}/${sheetName}.png`, new Uint8Array(await preview.arrayBuffer()));
}

const keyCheck = await workbook.inspect({
  kind: "table",
  sheetId: "Summary",
  range: "A1:D19",
  include: "values,formulas",
  tableMaxRows: 20,
  tableMaxCols: 6,
  maxChars: 9000,
});
console.log(keyCheck.ndjson);
const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 200 },
  summary: "final formula error scan",
});
console.log(errors.ndjson);

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(outputPath);
