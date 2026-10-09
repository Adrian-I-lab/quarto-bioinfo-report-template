# Shared setup for every R chapter.
#
# Quarto renders each chapter of a book in its own R session, so there is
# no global setup. The first (hidden) chunk of every chapter sources this
# file. The same helpers exist in Python in _setup.py.

suppressPackageStartupMessages({
  library(ggplot2)
  library(knitr)
  library(yaml)
})

`%||%` <- function(a, b) if (is.null(a)) b else a

set.seed(1)

# ---------------------------------------------------------------------------
# Locating the book
# ---------------------------------------------------------------------------

# The folder holding _quarto.yml. REPORT_ROOT wins when set. Otherwise walk
# up from the working directory. A book rendered against the wrong folder
# must fail, not guess.
report_root <- function() {
  env <- Sys.getenv("REPORT_ROOT", unset = "")
  if (nzchar(env)) {
    if (!file.exists(file.path(env, "_quarto.yml"))) {
      stop("REPORT_ROOT is set but holds no _quarto.yml: ", env, call. = FALSE)
    }
    return(normalizePath(env))
  }
  dir <- normalizePath(getwd())
  repeat {
    if (file.exists(file.path(dir, "_quarto.yml"))) return(dir)
    parent <- dirname(dir)
    if (identical(parent, dir)) {
      stop("No _quarto.yml found in the working directory or any parent. ",
           "Set REPORT_ROOT to the book folder.", call. = FALSE)
    }
    dir <- parent
  }
}

.params_cache <- new.env(parent = emptyenv())

# One analysis parameter from _params.yml. A missing or null value stops
# the render. There is never a default.
report_param <- function(name) {
  if (is.null(.params_cache$values)) {
    path <- file.path(report_root(), "_params.yml")
    .params_cache$values <- if (file.exists(path)) yaml::read_yaml(path) else list()
  }
  value <- .params_cache$values[[name]]
  if (is.null(value)) {
    stop("Parameter '", name, "' is not decided yet; record the decision in _params.yml",
         call. = FALSE)
  }
  value
}

# ---------------------------------------------------------------------------
# Numbers in prose (computed, never typed)
# ---------------------------------------------------------------------------

fmt <- function(x) format(x, big.mark = ",", scientific = FALSE, trim = TRUE)

pct <- function(x, d = 1) sprintf("%.*f%%", d, 100 * x)

# Every percentage carries its denominator.
frac <- function(k, n) sprintf("%s of %s (%s)", fmt(k), fmt(n), pct(k / n))

# ---------------------------------------------------------------------------
# Plot theme and palettes
# ---------------------------------------------------------------------------

theme_house <- function(base_size = 11) {
  theme_minimal(base_size = base_size) +
    theme(
      panel.grid.minor = element_blank(),
      panel.grid.major = element_line(colour = "#e6ebee"),
      strip.text = element_text(face = "bold"),
      plot.title = element_text(face = "bold"),
      plot.subtitle = element_text(colour = "#5a6b76"),
      plot.caption = element_text(colour = "#5a6b76")
    )
}

# Safe to set globally here: each chapter is its own R session.
theme_set(theme_house())

# One named palette for the whole book. Significance must be encoded by
# shape as well as colour, so no reader depends on colour alone.
HOUSE_PAL <- c(
  up = "#b5366a",
  down = "#2c7a93",
  ns = "#c2ccd2",
  warn = "#c9762f",
  ok = "#3f7d55"
)

# Okabe-Ito qualitative colours, for categories.
OKABE_ITO <- c(
  "#E69F00", "#56B4E9", "#009E73", "#F0E442",
  "#0072B2", "#D55E00", "#CC79A7", "#000000"
)

# ---------------------------------------------------------------------------
# Honest gaps
# ---------------------------------------------------------------------------

# One callout in place of a section that did not run.
not_applicable <- function(what, why) {
  knitr::asis_output(paste0(
    "\n::: {.callout-note appearance=\"simple\"}\n",
    "## Not applicable to this report\n\n",
    "This section covers ", what, ". It did not run because ", why, ". ",
    "Nothing was computed and nothing is hidden.\n",
    ":::\n"
  ))
}

# ---------------------------------------------------------------------------
# Checksums for provenance
# ---------------------------------------------------------------------------

# SHA-256 of a file, truncated to the first n hex characters. Uses the
# digest package if installed, else a system tool. Returns NA when no tool
# can run. A check that could not run counts as a failure, not a pass.
sha256_file <- function(path, n = 16) {
  full <- NA_character_
  if (requireNamespace("digest", quietly = TRUE)) {
    full <- digest::digest(file = path, algo = "sha256")
  } else {
    tools <- list(
      c("sha256sum", ""),
      c("shasum", "-a 256"),
      c("openssl", "dgst -sha256 -r")
    )
    for (t in tools) {
      if (!nzchar(Sys.which(t[1]))) next
      out <- tryCatch(
        system2(t[1], c(t[2], shQuote(path)), stdout = TRUE, stderr = FALSE),
        error = function(e) character()
      )
      hex <- regmatches(out, regexpr("[0-9a-f]{64}", out))
      if (length(hex) == 1) {
        full <- hex
        break
      }
    }
  }
  if (is.na(full)) NA_character_ else substr(full, 1, n)
}

# ---------------------------------------------------------------------------
# Figures for papers
# ---------------------------------------------------------------------------

# Writes the same plot as PDF and PNG into figures/ (gitignored).
save_figure <- function(plot, name, width = 6, height = 4) {
  dir <- file.path(report_root(), "figures")
  dir.create(dir, showWarnings = FALSE, recursive = TRUE)
  paths <- file.path(dir, paste0(name, c(".pdf", ".png")))
  ggsave(paths[1], plot, width = width, height = height, device = "pdf")
  ggsave(paths[2], plot, width = width, height = height, dpi = 300)
  invisible(paths)
}

# ---------------------------------------------------------------------------
# Synthetic data (seeded, generated at render time, never committed)
# ---------------------------------------------------------------------------

# A negative-binomial count matrix for two groups with 40 planted changes.
synth_counts <- function(n_genes = 500, n_per_group = 3, seed = 1) {
  set.seed(seed)
  genes <- sprintf("gene%04d", seq_len(n_genes))
  n <- 2 * n_per_group
  samples <- data.frame(
    sample = paste0("S", seq_len(n)),
    group = factor(rep(c("control", "treated"), each = n_per_group),
                   levels = c("control", "treated"))
  )
  base_mean <- exp(rnorm(n_genes, mean = 4, sd = 1.5))
  lfc <- numeric(n_genes)
  planted <- sample(n_genes, 40)
  lfc[planted] <- sample(c(-1, 1), 40, replace = TRUE) * runif(40, 1, 3)
  mu <- outer(base_mean, rep(1, n))
  treated <- samples$group == "treated"
  mu[, treated] <- mu[, treated] * 2^lfc
  counts <- matrix(rnbinom(length(mu), mu = mu, size = 10),
                   nrow = n_genes, dimnames = list(genes, samples$sample))
  truth <- data.frame(gene = genes, planted = seq_len(n_genes) %in% planted,
                      log2FC_true = lfc)
  list(counts = counts, samples = samples, truth = truth)
}

# A synthetic results table. Illustrative only: a two-sample Welch t-test
# on log CPM, which is NOT a recommended method for count data.
synth_de <- function(seed = 1) {
  sc <- synth_counts(seed = seed)
  lib <- colSums(sc$counts)
  logcpm <- log2(t(t(sc$counts + 1) / (lib + 1) * 1e6))
  treated <- sc$samples$group == "treated"
  p <- apply(logcpm, 1, function(x) {
    tryCatch(t.test(x[treated], x[!treated])$p.value, error = function(e) 1)
  })
  out <- data.frame(
    gene = rownames(logcpm),
    log2FC = rowMeans(logcpm[, treated]) - rowMeans(logcpm[, !treated]),
    p = unname(p)
  )
  out$FDR <- p.adjust(out$p, method = "BH")
  rownames(out) <- NULL
  out
}

# A 2-D point cloud of k Gaussian clusters, for scatter examples.
synth_embedding <- function(n = 900, k = 3, seed = 1) {
  set.seed(seed)
  cluster <- sample(seq_len(k), n, replace = TRUE)
  centres <- matrix(rnorm(2 * k, sd = 4), ncol = 2)
  data.frame(
    dim1 = centres[cluster, 1] + rnorm(n),
    dim2 = centres[cluster, 2] + rnorm(n),
    cluster = factor(paste0("cluster ", cluster))
  )
}
