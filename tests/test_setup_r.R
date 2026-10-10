# Tests for _setup.R. Run from the repository root: Rscript tests/test_setup_r.R
# Base R stopifnot only. Exits non-zero on the first failure.

source("_setup.R")
n_pass <- 0
check <- function(desc, expr) {
  ok <- isTRUE(expr)
  if (!ok) stop("FAILED: ", desc, call. = FALSE)
  n_pass <<- n_pass + 1
}

a <- synth_counts(seed = 7)$counts
b <- synth_counts(seed = 7)$counts
check("counts are deterministic", identical(a, b))

sc <- synth_counts(n_genes = 500, n_per_group = 3)
check("counts shape", identical(dim(sc$counts), c(500L, 6L)))
check("gene names", rownames(sc$counts)[1] == "gene0001")
check("forty planted changes", sum(sc$truth$planted) == 40)
check("planted changes are at least 1 log2 unit",
      all(abs(sc$truth$log2FC_true[sc$truth$planted]) >= 1))

check("frac", frac(3, 12) == "3 of 12 (25.0%)")
check("fmt", fmt(1234567) == "1,234,567")

msg <- tryCatch(report_param("decided_later"), error = function(e) conditionMessage(e))
check("null parameter stops with the documented message",
      grepl("not decided yet; record the decision in _params.yml", msg, fixed = TRUE))
# Compared with the book's own _params.yml, so a user's decision does not break the test.
fdr_line <- grep("^fdr:", readLines("_params.yml"), value = TRUE)
check("decided parameter is read",
      length(fdr_line) == 1 && report_param("fdr") == as.numeric(sub("^fdr:\\s*", "", fdr_line)))

de <- synth_de()
check("de table rows", nrow(de) == 500)
check("FDR at least p", all(de$FDR >= de$p))
check("de deterministic", identical(de, synth_de()))

emb <- synth_embedding(n = 900, k = 3)
check("embedding shape", nrow(emb) == 900 && nlevels(emb$cluster) == 3)

old <- Sys.getenv("REPORT_ROOT")
Sys.setenv(REPORT_ROOT = tempdir())
msg <- tryCatch(report_root(), error = function(e) conditionMessage(e))
Sys.setenv(REPORT_ROOT = old)
check("REPORT_ROOT without _quarto.yml stops", grepl("holds no _quarto.yml", msg, fixed = TRUE))

tmp <- tempfile(fileext = ".txt")
writeLines("abc", tmp)
check("sha256 of a known file", identical(sha256_file(tmp), "edeaaff3f1774ad2"))

cat("R setup tests passed:", n_pass, "\n")
