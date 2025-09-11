# ============================
# Averaged diffs: single CSV (FIXED)
# Ensures raw points are plotted in probability space (0–1),
# regardless of whether inputs are proportions, percents, or logits.
# ============================

library(visreg)
library(broom)
library(dplyr)
library(purrr)
library(readr)
library(stats)
library(tools)

.robust_ok <- requireNamespace("robustbase", quietly = TRUE)

# ----------------------------
# Load data (single averaged file)
# ----------------------------
in_csv <- "analysis/logistic-regression-scripts/results/csvs/averaged_logreg.csv"
proportions <- suppressMessages(read_csv(in_csv, show_col_types = FALSE))

# ----------------------------
# Output dir for plots
# ----------------------------
plot_dir <- file.path("analysis", "percent-results", "results_vs_BLS", "plots_averaged")
if (!dir.exists(plot_dir)) dir.create(plot_dir, recursive = TRUE)

# ----------------------------
# Groups to analyze
# ----------------------------
groups <- list(
  list(key = "white",    pretty = "White",    file = file.path(plot_dir, "avg_logreg_white.pdf")),
  list(key = "black",    pretty = "Black",    file = file.path(plot_dir, "avg_logreg_black.pdf")),
  list(key = "asian",    pretty = "Asian",    file = file.path(plot_dir, "avg_logreg_asian.pdf")),
  list(key = "hispanic", pretty = "Hispanic", file = file.path(plot_dir, "avg_logreg_hispanic.pdf")),
  list(key = "women",    pretty = "Women",    file = file.path(plot_dir, "avg_logreg_women.pdf"))
)

# ----------------------------
# Helpers
# ----------------------------

# Convert any vector to proportions in [0,1]:
# - If already in [0,1], return as-is
# - If in [0,100], convert to [0,1]
# - Else assume logits and apply plogis
normalize_to_prop <- function(v) {
  if (all(is.na(v))) return(v)
  r <- range(v, na.rm = TRUE)
  if (r[1] >= 0 && r[2] <= 1) {
    v
  } else if (r[1] >= 0 && r[2] <= 100) {
    v / 100
  } else {
    plogis(v)
  }
}

invlogit <- function(z) plogis(z)

star_fun <- function(p) dplyr::case_when(
  p < 0.001 ~ "***",
  p < 0.01  ~ "**",
  p < 0.05  ~ "*",
  TRUE      ~ ""
)
# alpha magnitude coding on the PERCENT scale (units = percentage points)
# thresholds: 0.5pp / 1.5pp / 3.0pp
code_alpha_pp_pct <- function(delta_pp_pct) {
  a <- abs(delta_pp_pct)
  out <- ifelse(a < 0.5, "0", "")
  out <- ifelse(a >= 0.5 & a < 3,  "±",  out)
  out <- ifelse(a >= 3 & a < 10, "±±", out)
  out <- ifelse(a >= 10,           "±±±",out)
  out <- ifelse(delta_pp_pct > 0 & out != "0", gsub("±", "+", out), out)
  out <- ifelse(delta_pp_pct < 0 & out != "0", gsub("±", "-", out), out)
  out
}

# DEPRECATED alpha magnitude coding (pp = percentage points on probability scale)
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

# beta deviation coding (avg local response-scale slope dev from 1)
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

# Core model fitters (median-centered)
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

# Build response-scale fitted curve + 95% CI using predict()
build_curve <- function(model, xseq, bls_col) {
  nd <- data.frame(x = xseq); names(nd) <- bls_col
  pr <- predict(model, newdata = nd, type = "link", se.fit = TRUE)
  eta <- pr$fit; se <- pr$se.fit
  data.frame(
    x   = xseq,
    fit = plogis(eta),
    lwr = plogis(eta - 1.96 * se),
    upr = plogis(eta + 1.96 * se)
  )
}

# ----------------------------
# Analyzer for one group (Raw / Trimmed5 / Robust), with normalization
# ----------------------------
analyze_one <- function(df, group_key, group_pretty) {
  bls_col_raw   <- paste0("bls_p_",   group_key)
  genai_col_raw <- paste0("genai_p_", group_key)

  # required columns check
  req <- c("genai_n", bls_col_raw, genai_col_raw)
  miss <- setdiff(req, names(df))
  if (length(miss)) stop("Missing required columns for group ", group_key, ": ", paste(miss, collapse=", "))

  # Normalize to probability space
  df2 <- df %>%
    mutate(
      bls_prop   = normalize_to_prop(.data[[bls_col_raw]]),
      genai_prop = normalize_to_prop(.data[[genai_col_raw]])
    )

  bls_col   <- "bls_prop"
  genai_col <- "genai_prop"

  # pivot: median BLS for this group (on probability scale)
  bls_med <- median(df2[[bls_col]], na.rm = TRUE)

  # Raw (centered)
  m_raw <- fit_quasi_centered(df2, bls_col, genai_col, bls_med); raw_w <- wald_rows(m_raw)

  # Trimmed5 by BLS (same pivot for comparability)
  q_lo <- quantile(df2[[bls_col]], 0.05, na.rm = TRUE)
  q_hi <- quantile(df2[[bls_col]], 0.95, na.rm = TRUE)
  df_trim <- df2 %>% filter(.data[[bls_col]] >= q_lo, .data[[bls_col]] <= q_hi)
  m_trim <- fit_quasi_centered(df_trim, bls_col, genai_col, bls_med); trim_w <- wald_rows(m_trim)

  # Robust (primary)
  m_rob <- fit_robust_centered(df2, bls_col, genai_col, bls_med)
  rob_w <- if (!is.null(m_rob)) wald_rows(m_rob) else raw_w

  # Interpretable effect metrics (probability scale)
  alpha_pp_raw  <- invlogit(raw_w$alpha)  - bls_med
  alpha_pp_trim <- invlogit(trim_w$alpha) - bls_med
  alpha_pp_rob  <- invlogit(rob_w$alpha)  - bls_med

  beta_dev_calc <- function(alpha_hat, beta_hat, df_range) {
    qlo <- quantile(df_range[[bls_col]], 0.10, na.rm = TRUE)
    qhi <- quantile(df_range[[bls_col]], 0.90, na.rm = TRUE)
    xs  <- seq(qlo, qhi, length.out = 101)
    mu  <- invlogit(alpha_hat + beta_hat * (xs - bls_med))
    slope <- beta_hat * mu * (1 - mu)
    mean(slope - 1, na.rm = TRUE)
  }
  beta_dev_raw  <- beta_dev_calc(raw_w$alpha,  raw_w$beta,  df2)
  beta_dev_trim <- beta_dev_calc(trim_w$alpha, trim_w$beta, df_trim)
  beta_dev_rob  <- beta_dev_calc(rob_w$alpha,  rob_w$beta,  df2)

  tibble(
    group = group_pretty,
    method = c("Raw", "Trimmed5", if (.robust_ok) "Robust" else "Robust_FallbackToRaw"),
    center_at = bls_med,
    alpha = c(raw_w$alpha, trim_w$alpha, rob_w$alpha),
    se_alpha = c(raw_w$se_alpha, trim_w$se_alpha, rob_w$se_alpha),
    p_alpha = c(raw_w$p_alpha, trim_w$p_alpha, rob_w$p_alpha),
    beta  = c(raw_w$beta,  trim_w$beta,  rob_w$beta),
    se_beta = c(raw_w$se_beta, trim_w$se_beta, rob_w$se_beta),
    p_beta  = c(raw_w$p_beta,  trim_w$p_beta,  rob_w$p_beta),
    alpha_effect_pp = c(alpha_pp_raw, alpha_pp_trim, alpha_pp_rob),
    beta_dev = c(beta_dev_raw, beta_dev_trim, beta_dev_rob)
  )
}

# ----------------------------
# Plotter (points & curve drawn in % space), with normalization
# ----------------------------
plot_one <- function(group, pretty_group, out_pdf, jitter_pp = 0.0) {
  stopifnot(requireNamespace("visreg", quietly = TRUE))

  bls_col   <- paste0("bls_p_", group)
  genai_col <- paste0("genai_p_", group)

  # Keep complete rows
  df0 <- proportions[complete.cases(proportions[, c(bls_col, genai_col, "genai_n")]), ]

  # ---- Scale logic: fit on proportions [0,1]; draw on percents [0,100] ----
  to_prop <- function(x) if (max(x, na.rm = TRUE) > 1) x/100 else x
  bls_prop   <- to_prop(df0[[bls_col]])
  genai_prop <- to_prop(df0[[genai_col]])

  # Optional tiny jitter (in percentage points, applied on the plotted % only)
  # e.g., jitter_pp = 0.15 means ~±0.15pp vertical jitter
  genai_pct <- genai_prop * 100
  if (jitter_pp > 0) {
    set.seed(42)
    genai_pct <- genai_pct + stats::rnorm(length(genai_pct), sd = jitter_pp)
    genai_pct <- pmax(pmin(genai_pct, 100), 0)  # clamp to 0–100 just in case
  }

  # Fit model in proportion space
  m <- glm(genai_prop ~ I(bls_prop - 0.5),
           family = quasibinomial,
           weights = df0$genai_n)

  # Observed range (proportion scale)
  min_bls <- min(bls_prop, na.rm = TRUE)
  max_bls <- max(bls_prop, na.rm = TRUE)

  # Device
  pdf(out_pdf, width = 8, height = 6); on.exit(dev.off(), add = TRUE)
  par(cex.main = 1.5, cex.lab = 1.3, cex.axis = 1.2, mar = c(7, 5, 4.5, 2))

  # Set up percent axes
  plot(NA, xlim = c(0, 100), ylim = c(0, 100),
       xlab = paste("BLS percent", pretty_group),
       ylab = sprintf("Average percent %s", pretty_group),
       main = NULL)
  title(main = sprintf("Average %s representation vs. BLS", pretty_group), line = 2.3)

  # Grid
  xticks <- axTicks(1); yticks <- axTicks(2)
  abline(v = xticks, col = "grey70", lty = "dotted", lwd = 0.8)
  abline(h = yticks, col = "grey70", lty = "dotted", lwd = 0.8)

  # Shade outside observed BLS range (convert to %)
  usr <- par("usr"); yr <- diff(usr[3:4])
  rect(usr[1], usr[3], min_bls*100, usr[4], col = rgb(0.5, 0.5, 0.5, 0.25), border = NA)
  rect(max_bls*100, usr[3], usr[2], usr[4], col = rgb(0.5, 0.5, 0.5, 0.25), border = NA)

  # Smooth curve (visreg on response scale), then convert to %
  vr <- visreg::visreg(m, "bls_prop", scale = "response", plot = FALSE)
  df_fit <- vr$fit
  xv  <- df_fit$bls_prop * 100
  ord <- order(xv)
  polygon(
    x = c(xv[ord], rev(xv[ord])),
    y = c(df_fit$visregLwr[ord]*100, rev(df_fit$visregUpr[ord]*100)),
    col = rgb(0.2, 0.4, 0.8, 0.2), border = NA
  )
  lines(xv[ord], df_fit$visregFit[ord]*100, lwd = 2)

  # Raw points on % scale (x from bls_prop, y from (optionally jittered) genai_pct)
  points(bls_prop*100, genai_pct, pch = 20)

  # Parity line y = x (in % space)
  abline(coef = c(0, 1), lty = "dashed")

  # Min/Max verticals (in %)
  abline(v = min_bls*100, col = "blue", lwd = 2, lty = "dotted")
  abline(v = max_bls*100, col = "red",  lwd = 2, lty = "dotted")

  # Min/Max labels above
  text(min_bls*100, usr[4] + 0.05*yr, paste0("min observed = ", round(min_bls*100, 1), "%"),
       col = "blue", cex = 1.05, xpd = NA)
  text(max_bls*100, usr[4] + 0.05*yr, paste0("max observed = ", round(max_bls*100, 1), "%"),
       col = "red",  cex = 1.05, xpd = NA)
}

# ----------------------------
# Run analyses for all groups
# ----------------------------
results <- map_dfr(groups, ~ analyze_one(proportions, .x$key, .x$pretty))

# FDR within each method (Raw / Trimmed5 / Robust)
results <- results %>%
  group_by(method) %>%
  mutate(
    p_alpha_fdr = p.adjust(p_alpha, method = "BH"),
    p_beta_fdr  = p.adjust(p_beta,  method = "BH")
  ) %>%
  ungroup()

# Final table with nuanced codes and human-friendly columns
final_table <- results %>%
  mutate(
    alpha_effect_pp_pct = round(alpha_effect_pp * 100, 2),  # convert to percentage points
    beta_dev_round      = round(beta_dev, 3),

    alpha_fmt  = paste0(round(alpha, 3), star_fun(p_alpha_fdr)),
    beta_fmt   = paste0(round(beta,  3), star_fun(p_beta_fdr)),

    # NOW: codes based on % scale (pp)
    alpha_code = code_alpha_pp_pct(alpha_effect_pp_pct),
    beta_code  = code_beta_dev(beta_dev)
  ) %>%
  select(
    group, method, center_at,
    alpha, se_alpha, p_alpha, p_alpha_fdr, alpha_fmt,
    alpha_effect_pp_pct, alpha_code,
    beta,  se_beta,  p_beta,  p_beta_fdr,  beta_fmt,
    beta_dev_round, beta_code
  ) %>%
  arrange(method, group)

# Write CSV
out_csv <- "regression_results_averaged_with_methods.csv"
write.csv(final_table, out_csv, row.names = FALSE)

message("Wrote ", out_csv, " with ", nrow(final_table), " rows.")
message("Robust available: ", .robust_ok, " (", if (.robust_ok) "glmrob" else "falling back to Raw for 'Robust'", ")")
message("Plot directory: ", normalizePath(plot_dir, mustWork = FALSE))

# ----------------------------
# Make plots
# ----------------------------
invisible(lapply(groups, function(g) {
  plot_one(group = g$key, pretty_group = g$pretty, out_pdf = g$file)
}))