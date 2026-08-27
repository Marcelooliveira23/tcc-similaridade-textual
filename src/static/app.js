const textA = document.getElementById("text-a");
const textB = document.getElementById("text-b");
const fileA = document.getElementById("file-a");
const fileB = document.getElementById("file-b");
const fileAName = document.getElementById("file-a-name");
const fileBName = document.getElementById("file-b-name");
const statusEl = document.getElementById("status");

const scoreTfidf = document.getElementById("score-tfidf");
const scoreJaccard = document.getElementById("score-jaccard");
const scoreLevenshtein = document.getElementById("score-levenshtein");

// Mostrar nome do arquivo selecionado
fileA.addEventListener("change", () => {
  fileAName.textContent = fileA.files[0] ? fileA.files[0].name : "nenhum arquivo";
});
fileB.addEventListener("change", () => {
  fileBName.textContent = fileB.files[0] ? fileB.files[0].name : "nenhum arquivo";
});

function toPercent(value) {
  return `${(value * 100).toFixed(2)}%`;
}

function renderScores(result) {
  scoreTfidf.textContent = toPercent(result.tfidf_cosine);
  scoreJaccard.textContent = toPercent(result.jaccard);
  scoreLevenshtein.textContent = toPercent(result.levenshtein_similarity);
}

async function compareTexts() {
  statusEl.textContent = "Processando textos...";

  const response = await fetch("/compare", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text_a: textA.value,
      text_b: textB.value,
    }),
  });

  const body = await response.json();

  if (!response.ok) {
    statusEl.textContent = body.error || "Erro ao comparar textos.";
    return;
  }

  renderScores(body);
  statusEl.textContent = "Comparacao concluida e salva no historico.";
}

async function compareFiles() {
  if (!fileA.files.length || !fileB.files.length) {
    statusEl.textContent = "Selecione os dois arquivos.";
    return;
  }

  const nameA = fileA.files[0].name;
  const nameB = fileB.files[0].name;
  statusEl.textContent = `Extraindo texto de "${nameA}" e "${nameB}"...`;

  const formData = new FormData();
  formData.append("file_a", fileA.files[0]);
  formData.append("file_b", fileB.files[0]);

  const response = await fetch("/compare-files", {
    method: "POST",
    body: formData,
  });

  const body = await response.json();

  if (!response.ok) {
    statusEl.textContent = body.error || "Erro ao comparar arquivos.";
    return;
  }

  renderScores(body);
  statusEl.textContent = `✅ "${nameA}" × "${nameB}" — comparacao concluida.`;
}

document.getElementById("compare-btn").addEventListener("click", compareTexts);
document.getElementById("compare-files-btn").addEventListener("click", compareFiles);
