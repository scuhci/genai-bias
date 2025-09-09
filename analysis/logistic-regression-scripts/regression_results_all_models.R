# ============================
# Regression Results by Model
# (quasibinomial GLM; FDR BH)
# + Median-centering (per group)
# + Robust & Trimmed checks
# + Nuanced probability-scale codes
# + Plot generation
# ============================

library(broom)
library(dplyr)
library(purrr)
library(readr)
library(stats)
library(visreg)   # fitted line + CI
library(tools)

# Try to enable robust regression (falls back if not installed)
.robust_ok <- requireNamespace("robustbase", quietly = TRUE)

# ----------------------------
# Configure: where the 4 CSVs live
# ----------------------------
csv_dir <- "analysis/logistic-regression-scripts/results/csvs"
files <- list.files(csv_dir, pattern = "\\.csv$", full.names = TRUE)
print(files)
stopifnot(length(files) >= 1)

# Where to save plots
plot_dir <- file.path("analysis", "logistic-regression-scripts", "results", "plots")
if (!dir.exists(plot_dir)) dir.create(plot_dir, recursive = TRUE)

# Optional: map filename stems to pretty model names (edit as you like)
pretty_model_name <- function(path) {
  stem <- tools::file_path_sans_ext(basename(path))
  map <- c(
    "openai_converted" = "ChatGPT",
    "gemini_converted" = "Gemini",
    "deepseek_converted" = "DeepSeek",
    "mistral_converted" = "Mistral"
  )
  if (stem %in% names(map)) return(map[[stem]])
  gsub("_", " ", tools::toTitleCase(stem))
}

# Safe file slug
slugify <- function(x) gsub("[^A-Za-z0-9]+", "_", x)

# ----------------------------
# Groups to analyze
# ----------------------------
groups <- list(
  list(key = "white",    pretty = "White"),
  list(key = "black",    pretty = "Black"),
  list(key = "asian",    pretty = "Asian"),
  list(key = "hispanic", pretty = "Hispanic"),
  list(key = "women",    pretty = "Women")
)

# ----------------------------
# Stars and codes
# ----------------------------
star_fun <- function(p) dplyr::case_when(
  p < 0.001 ~ "***",
  p < 0.01  ~ "**",
  p < 0.05  ~ "*",
  TRUE      ~ ""
)

# Old (logit-scale) codes are replaced by nuanced probability-scale codes below
invlogit <- function(z) plogis(z)

# Magnitude-based, probability-scale codes for alpha (Δ at pivot, in proportion units)
# delta_pp is in 0–1; bins are in percentage points (0.5, 1.5, 3.0 pp)
code_alpha_pp <- function(delta_pp) {
  a <- abs(delta_pp)
  out <- ifelse(a < 0.005, "0", "")
  out <- ifelse(a >= 0.005 & a < 0.015, "±",  out)
  out <- ifelse(a >= 0.015 & a < 0.03,  "±±", out)
  out <- ifelse(a >= 0.03,               "±±±",out)
  out <- ifelse(delta_pp > 0 & out != "0", gsub("±", "+", out), out)
  out <- ifelse(delta_pp < 0 & out != "0", gsub("±", "-", out), out)
  out
}

# Magnitude-based codes for beta using average local slope deviation from 1
# beta_dev = mean_{x in central range} [ beta * mu(x) * (1 - mu(x)) - 1 ]
code_beta_dev <- function(beta_dev) {
  d <- abs(beta_dev)
  out <- ifelse(d < 0.05, "0", "")
  out <- ifelse(d >= 0.05 & d < 0.10, "±",  out)
  out <- ifelse(d >= 0.10 & d < 0.20, "±±", out)
  out <- ifelse(d >= 0.20,             "±±±",out)
  out <- ifelse(beta_dev > 0 & out != "0", gsub("±", "+", out), out)
  out <- ifelse(beta_dev < 0 & out != "0", gsub("±", "-", out), out)
  out
}

# ----------------------------
# Core analyzers with median-centering
# ----------------------------
fit_quasi_centered <- function(df, bls_col, genai_col, center_at, weights_col = "genai_n") {
  fml <- as.formula(paste0(genai_col, " ~ I(", bls_col, " - ", signif(center_at, 15), ")"))
  glm(fml, family = quasibinomial, data = df, weights = df[[weights_col]])
}

fit_robust_centered <- function(df, bls_col, genai_col, center_at, weights_col = "genai_n") {
  if (!.robust_ok) return(NULL)
  fml <- as.formula(paste0(genai_col, " ~ I(", bls_col, " - ", signif(center_at, 15), ")"))
  robustbase::glmrob(
    fml, family = binomial, data = df, weights = df[[weights_col]],
    method = "Mqle", control = robustbase::glmrobMqle.control()
  )
}

wald_rows <- function(model, beta_ref = 1) {
  sm <- summary(model)
  est <- coef(sm)
  alpha    <- est[1, "Estimate"]
  se_alpha <- est[1, "Std. Error"]
  beta     <- est[2, "Estimate"]
  se_beta  <- est[2, "Std. Error"]

  z_alpha <- (alpha - 0) / se_alpha
  p_alpha <- 2 * pnorm(-abs(z_alpha))
  z_beta  <- (beta  - beta_ref) / se_beta
  p_beta  <- 2 * pnorm(-abs(z_beta))

  list(alpha=alpha, se_alpha=se_alpha, p_alpha=p_alpha,
       beta=beta,   se_beta=se_beta,   p_beta=p_beta)
}

analyze_one <- function(df, model_name, group_key, group_pretty) {
  bls_col   <- paste0("bls_p_",   group_key)
  genai_col <- paste0("genai_p_", group_key)

  # Centering pivot: median BLS share for this group
  bls_med <- median(df[[bls_col]], na.rm = TRUE)

  # --- RAW (centered) quasibinomial ---
  m_raw <- fit_quasi_centered(df, bls_col, genai_col, center_at = bls_med)
  raw_w <- wald_rows(m_raw)

  # --- TRIMMED (5% by BLS), centered on the SAME pivot for comparability ---
  q_lo <- quantile(df[[bls_col]], probs = 0.05, na.rm = TRUE)
  q_hi <- quantile(df[[bls_col]], probs = 0.95, na.rm = TRUE)
  df_trim <- df %>% filter(.data[[bls_col]] >= q_lo, .data[[bls_col]] <= q_hi)
  m_trim <- fit_quasi_centered(df_trim, bls_col, genai_col, center_at = bls_med)
  trim_w <- wald_rows(m_trim)

  # --- ROBUST (primary) centered on same pivot ---
  m_rob <- fit_robust_centered(df, bls_col, genai_col, center_at = bls_med)
  if (!is.null(m_rob)) {
    rob_w <- wald_rows(m_rob)
  } else {
    rob_w <- raw_w  # fallback if robustbase not installed
  }

  # ----- Interpretable effect metrics -----
  # Alpha effect at pivot on probability scale (0–1)
  alpha_pp_raw  <- invlogit(raw_w$alpha)  - bls_med
  alpha_pp_trim <- invlogit(trim_w$alpha) - bls_med
  alpha_pp_rob  <- invlogit(rob_w$alpha)  - bls_med

  # Beta slope deviation (avg over 10th–90th pct of BLS)
  beta_dev_calc <- function(alpha_hat, beta_hat, bls_col, center_at, df_range) {
    qlo <- quantile(df_range[[bls_col]], 0.10, na.rm = TRUE)
    qhi <- quantile(df_range[[bls_col]], 0.90, na.rm = TRUE)
    xs  <- seq(qlo, qhi, length.out = 101)
    mu  <- invlogit(alpha_hat + beta_hat * (xs - center_at))
    slope <- beta_hat * mu * (1 - mu)
    mean(slope - 1, na.rm = TRUE)
  }
  beta_dev_raw  <- beta_dev_calc(raw_w$alpha,  raw_w$beta,  bls_col, bls_med, df)
  beta_dev_trim <- beta_dev_calc(trim_w$alpha, trim_w$beta, bls_col, bls_med, df_trim)
  beta_dev_rob  <- beta_dev_calc(rob_w$alpha,  rob_w$beta,  bls_col, bls_med, df)

  tibble(
    model = model_name,
    group = group_pretty,
    method = c("Raw", "Trimmed5", if (.robust_ok) "Robust" else "Robust_FallbackToRaw"),
    center_at = bls_med,
    alpha = c(raw_w$alpha, trim_w$alpha, rob_w$alpha),
    se_alpha = c(raw_w$se_alpha, trim_w$se_alpha, rob_w$se_alpha),
    p_alpha = c(raw_w$p_alpha, trim_w$p_alpha, rob_w$p_alpha),
    beta  = c(raw_w$beta,  trim_w$beta,  rob_w$beta),
    se_beta = c(raw_w$se_beta, trim_w$se_beta, rob_w$se_beta),
    p_beta  = c(raw_w$p_beta,  trim_w$p_beta,  rob_w$p_beta),
    alpha_effect_pp = c(alpha_pp_raw, alpha_pp_trim, alpha_pp_rob),  # proportion units
    beta_dev = c(beta_dev_raw, beta_dev_trim, beta_dev_rob)
  )
}

# ----------------------------
# Plotter (median-centered pivot annotated)
# ----------------------------
plot_one_model_group <- function(df, model_name, group_key, group_pretty, out_pdf) {
  bls_col   <- paste0("bls_p_",   group_key)
  genai_col <- paste0("genai_p_", group_key)
  bls_med   <- median(df[[bls_col]], na.rm = TRUE)

  # Fit (raw centered) for visreg
  m <- fit_quasi_centered(df, bls_col, genai_col, center_at = bls_med)

  # axis limits & observed min/max
  xlim <- c(0, 1); ylim <- c(0, 1)
  xvals   <- df[[bls_col]]
  min_bls <- min(xvals, na.rm = TRUE)
  max_bls <- max(xvals, na.rm = TRUE)

  pdf(out_pdf, width = 8, height = 6); on.exit(dev.off(), add = TRUE)
  par(cex.main = 1.5, cex.lab = 1.3, cex.axis = 1.2, mar = c(6, 5, 4.5, 2))

  plot(NA, xlim = xlim, ylim = ylim,
       xlab = paste("BLS proportion", group_pretty),
       ylab = paste("Average proportion", group_pretty),
       main = NULL)

  title(
    main = paste0(model_name, ": Average ", group_pretty, " representation across 41 occupations"),
    line = 2.5
  )

  # Grid
  xticks <- axTicks(1); yticks <- axTicks(2)
  abline(v = xticks, col = "grey70", lty = "dotted", lwd = 0.8)
  abline(h = yticks, col = "grey70", lty = "dotted", lwd = 0.8)

  # Shade outside observed range
  usr <- par("usr"); yr <- diff(usr[3:4])
  rect(usr[1], usr[3], min_bls, usr[4], col = rgb(0.5, 0.5, 0.5, 0.25), border = NA)
  rect(max_bls, usr[3], usr[2], usr[4], col = rgb(0.5, 0.5, 0.5, 0.25), border = NA)

  # visreg fit (response scale)
  vr <- visreg(m, bls_col, scale = "response", plot = FALSE)
  df_fit <- vr$fit
  xv <- df_fit[[bls_col]]; ord <- order(xv)
  polygon(
    x = c(xv[ord], rev(xv[ord])),
    y = c(df_fit$visregLwr[ord], rev(df_fit$visregUpr[ord])),
    col = rgb(0.2, 0.4, 0.8, 0.2), border = NA
  )
  lines(xv[ord], df_fit$visregFit[ord], lwd = 2)

  # Observed
  points(df[[bls_col]], df[[genai_col]], pch = 20)

  # Parity line
  abline(coef = c(0, 1), lty = "dashed")

  # Min/Max verticals
  abline(v = min_bls, col = "blue", lwd = 2, lty = "dotted")
  abline(v = max_bls, col = "red",  lwd = 2, lty = "dotted")

  # Median pivot (centering)
  abline(v = bls_med, col = "darkgreen", lwd = 2, lty = "dotdash")

  min_label <- paste0("min observed = ", round(min_bls * 100, 1), "%")
  max_label <- paste0("max observed = ", round(max_bls * 100, 1), "%")
  med_label <- paste0("median pivot = ", round(bls_med * 100, 1), "%")
  label_y <- usr[4] + 0.05 * yr

  text(min_bls, label_y, min_label, col = "blue",      cex = 1.05, xpd = NA)
  text(max_bls, label_y, max_label, col = "red",       cex = 1.05, xpd = NA)
  text(bls_med, label_y, med_label, col = "darkgreen", cex = 1.05, xpd = NA)
}

# ----------------------------
# Run analyses and plots
# ----------------------------
results_list <- list()

for (fp in files) {
  model_pretty <- pretty_model_name(fp)
  df <- suppressMessages(suppressWarnings(read_csv(fp, show_col_types = FALSE)))

  # Required columns
  req_cols <- c("genai_n",
                paste0("bls_p_",   sapply(groups, `[[`, "key")),
                paste0("genai_p_", sapply(groups, `[[`, "key")))
  missing <- setdiff(req_cols, names(df))
  if (length(missing) > 0) {
    stop(sprintf("File '%s' is missing required columns: %s",
                 basename(fp), paste(missing, collapse = ", ")))
  }

  # Analyses (Raw/Trimmed5/Robust) for all groups
  tmp <- map_dfr(groups, ~ analyze_one(df, model_pretty, .x$key, .x$pretty))
  results_list[[length(results_list) + 1]] <- tmp

  # Plots for this model
  model_slug <- slugify(model_pretty)
  for (g in groups) {
    out_pdf <- file.path(plot_dir, paste0("logreg_", model_slug, "_", g$key, ".pdf"))
    plot_one_model_group(
      df          = df,
      model_name  = model_pretty,
      group_key   = g$key,
      group_pretty= g$pretty,
      out_pdf     = out_pdf
    )
  }
}

raw_results <- bind_rows(results_list)

# ----------------------------
# FDR (Benjamini–Hochberg) within each method
# ----------------------------
raw_results <- raw_results %>%
  group_by(method) %>%
  mutate(
    p_alpha_fdr = p.adjust(p_alpha, method = "BH"),
    p_beta_fdr  = p.adjust(p_beta,  method = "BH")
  ) %>%
  ungroup()

# ----------------------------
# Final formatting with nuanced codes
# ----------------------------
final_table <- raw_results %>%
  mutate(
    alpha_fmt  = paste0(round(alpha, 3), star_fun(p_alpha_fdr)),
    beta_fmt   = paste0(round(beta,  3), star_fun(p_beta_fdr)),
    alpha_code = code_alpha_pp(alpha_effect_pp),          # proportion units (0–1)
    beta_code  = code_beta_dev(beta_dev),
    alpha_effect_pp_pct = round(alpha_effect_pp * 100, 2),# percentage points
    beta_dev_round = round(beta_dev, 3)
  ) %>%
  select(
    model, group, method, center_at,
    alpha, se_alpha, p_alpha, p_alpha_fdr, alpha_fmt,
    alpha_effect_pp_pct, alpha_code,
    beta,  se_beta,  p_beta,  p_beta_fdr,  beta_fmt,
    beta_dev_round, beta_code
  ) %>%
  arrange(method, model, group)

# ----------------------------
# Export CSV
# ----------------------------
out_csv <- "regression_results_all_models_with_methods.csv"
write.csv(final_table, out_csv, row.names = FALSE)

message("Wrote ", out_csv, " with ", nrow(final_table), " rows.")
message("Robust available: ", .robust_ok, " (", if (.robust_ok) "glmrob" else "falling back to Raw for 'Robust'", ")")
message("Wrote plots to: ", normalizePath(plot_dir, mustWork = FALSE))
