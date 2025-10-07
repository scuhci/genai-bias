# ============================
# Regression Results by Model (multiple CSVs)
# (quasibinomial GLM; FDR BH)
# + Median-centering (per group)
# + Robust & Trimmed checks
# + Nuanced probability-scale codes
# + Plot generation (title/y-axis per your spec)
# ============================

library(broom)
library(dplyr)
library(purrr)
library(readr)
library(stats)
library(visreg)
library(tools)

# Robust option (graceful fallback if not installed)
.robust_ok <- requireNamespace("robustbase", quietly = TRUE)

# ----------------------------
# Input CSVs & output dir
# ----------------------------
csv_dir <- "analysis/logistic-regression-scripts/results/csvs"
files <- list.files(csv_dir, pattern = "\\.csv$", full.names = TRUE)
print(files)
stopifnot(length(files) >= 1)

plot_dir <- file.path("analysis", "logistic-regression-scripts", "results", "plots")
if (!dir.exists(plot_dir)) dir.create(plot_dir, recursive = TRUE)

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

slugify <- function(x) gsub("[^A-Za-z0-9]+", "_", x)

groups <- list(
  list(key = "white",    pretty = "White"),
  list(key = "black",    pretty = "Black"),
  list(key = "asian",    pretty = "Asian"),
  list(key = "hispanic", pretty = "Hispanic"),
  list(key = "women",    pretty = "Women")
)

# ----------------------------
# Helpers
# ----------------------------
star_fun <- function(p) dplyr::case_when(
  p < 0.001 ~ "***",
  p < 0.01  ~ "**",
  p < 0.05  ~ "*",
  TRUE      ~ ""
)
invlogit <- function(z) plogis(z)

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
code_beta_dev <- function(beta_dev) {
  d <- abs(beta_dev)
  out <- ifelse(d < 0.1, "0", "")
  out <- ifelse(d >= 0.1 & d < 0.5, "±",  out)
  out <- ifelse(d >= 0.5 & d < 1.5, "±±", out)
  out <- ifelse(d >= 1.5,             "±±±",out)
  out <- ifelse(beta_dev > 0 & out != "0", gsub("±", "+", out), out)
  out <- ifelse(beta_dev < 0 & out != "0", gsub("±", "-", out), out)
  out
}

# NEW: signed formatter for display (keeps numeric columns unchanged)
fmt_signed <- function(x, digits = 2) {
  s <- formatC(x, format = "f", digits = digits)
  ifelse(x > 0, paste0("+", s), s)
}

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
  sm <- summary(model); est <- coef(sm)
  alpha    <- est[1, "Estimate"]; se_alpha <- est[1, "Std. Error"]
  beta     <- est[2, "Estimate"]; se_beta  <- est[2, "Std. Error"]
  z_alpha <- (alpha - 0) / se_alpha; p_alpha <- 2 * pnorm(-abs(z_alpha))
  z_beta  <- (beta  - beta_ref) / se_beta; p_beta <- 2 * pnorm(-abs(z_beta))
  list(alpha=alpha, se_alpha=se_alpha, p_alpha=p_alpha,
       beta=beta,   se_beta=se_beta,   p_beta=p_beta)
}

analyze_one <- function(df, model_name, group_key, group_pretty) {
  bls_col   <- paste0("bls_p_",   group_key)
  genai_col <- paste0("genai_p_", group_key)
  bls_med <- median(df[[bls_col]], na.rm = TRUE)

  m_raw  <- fit_quasi_centered(df, bls_col, genai_col, bls_med);  raw_w  <- wald_rows(m_raw)
  q_lo <- quantile(df[[bls_col]], 0.05, na.rm = TRUE)
  q_hi <- quantile(df[[bls_col]], 0.95, na.rm = TRUE)
  df_trim <- df %>% filter(.data[[bls_col]] >= q_lo, .data[[bls_col]] <= q_hi)
  m_trim <- fit_quasi_centered(df_trim, bls_col, genai_col, bls_med); trim_w <- wald_rows(m_trim)
  m_rob <- fit_robust_centered(df, bls_col, genai_col, bls_med)
  rob_w <- if (!is.null(m_rob)) wald_rows(m_rob) else raw_w

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
  beta_dev_raw  <- beta_dev_calc(raw_w$alpha,  raw_w$beta,  df)
  beta_dev_trim <- beta_dev_calc(trim_w$alpha, trim_w$beta, df_trim)
  beta_dev_rob  <- beta_dev_calc(rob_w$alpha,  rob_w$beta,  df)

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
    alpha_effect_pp = c(alpha_pp_raw, alpha_pp_trim, alpha_pp_rob),
    beta_dev = c(beta_dev_raw, beta_dev_trim, beta_dev_rob)
  )
}

# ----------------------------
# Plot (title & y-axis per spec; median label below ticks)
# ----------------------------
plot_one_model_group <- function(df, model_name, group_key, group_pretty, out_pdf) {
  bls_col   <- paste0("bls_p_",   group_key)
  genai_col <- paste0("genai_p_", group_key)

  # Regular regression (center at 0.5) for visuals
  fml <- as.formula(paste0(genai_col, " ~ I(", bls_col, " - 0.5)"))
  m <- glm(fml, family = quasibinomial, data = df, weights = df$genai_n)

  # Observed range
  xvals   <- df[[bls_col]]
  min_bls <- min(xvals, na.rm = TRUE)
  max_bls <- max(xvals, na.rm = TRUE)

  # Device
  pdf(out_pdf, width = 8, height = 6); on.exit(dev.off(), add = TRUE)
  par(cex.main = 1.5, cex.lab = 1.3, cex.axis = 1.2, mar = c(7, 5, 4.5, 2))

  # Percent axes
  plot(NA, xlim = c(0, 100), ylim = c(0, 100),
       xlab = paste("BLS percent", group_pretty),
       ylab = sprintf("%s percent %s", model_name, group_pretty),
       main = NULL)

  title(main = sprintf("%s: %s representation vs. BLS", model_name, group_pretty), line = 2.3)

  # Grid
  xticks <- axTicks(1); yticks <- axTicks(2)
  abline(v = xticks, col = "grey70", lty = "dotted", lwd = 0.8)
  abline(h = yticks, col = "grey70", lty = "dotted", lwd = 0.8)

  # Shade outside observed range (convert to %)
  usr <- par("usr"); yr <- diff(usr[3:4])
  rect(usr[1], usr[3], min_bls*100, usr[4], col = rgb(0.5, 0.5, 0.5, 0.25), border = NA)
  rect(max_bls*100, usr[3], usr[2], usr[4], col = rgb(0.5, 0.5, 0.5, 0.25), border = NA)

  # Smooth curve from visreg (converted to %)
  vr <- visreg(m, bls_col, scale = "response", plot = FALSE)
  df_fit <- vr$fit
  xv  <- df_fit[[bls_col]] * 100
  ord <- order(xv)
  polygon(
    x = c(xv[ord], rev(xv[ord])),
    y = c(df_fit$visregLwr[ord]*100, rev(df_fit$visregUpr[ord]*100)),
    col = rgb(0.2, 0.4, 0.8, 0.2), border = NA
  )
  lines(xv[ord], df_fit$visregFit[ord]*100, lwd = 2)

  # Points (convert to %)
  points(df[[bls_col]]*100, df[[genai_col]]*100, pch = 20)

  # Parity y = x (works in % space)
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
# Run analyses and plots
# ----------------------------
results_list <- list()
for (fp in files) {
  model_pretty <- pretty_model_name(fp)
  df <- suppressMessages(suppressWarnings(read_csv(fp, show_col_types = FALSE)))

  req_cols <- c("genai_n",
                paste0("bls_p_",   sapply(groups, `[[`, "key")),
                paste0("genai_p_", sapply(groups, `[[`, "key")))
  missing <- setdiff(req_cols, names(df))
  if (length(missing)) stop(sprintf("File '%s' missing: %s", basename(fp), paste(missing, collapse = ", ")))

  tmp <- purrr::map_dfr(groups, ~ analyze_one(df, model_pretty, .x$key, .x$pretty))
  results_list[[length(results_list)+1]] <- tmp

  model_slug <- slugify(model_pretty)
  for (g in groups) {
    out_pdf <- file.path(plot_dir, paste0("logreg_", model_slug, "_", g$key, ".pdf"))
    plot_one_model_group(df, model_pretty, g$key, g$pretty, out_pdf)
  }
}

raw_results <- bind_rows(results_list) %>%
  group_by(method) %>%
  mutate(
    p_alpha_fdr = p.adjust(p_alpha, method = "BH"),
    p_beta_fdr  = p.adjust(p_beta,  method = "BH")
  ) %>%
  ungroup()

final_table <- raw_results %>%
  mutate(
    # Compute once, then reuse consistently across *all* plots/tables
    alpha_effect_pp_pct = round(alpha_effect_pp * 100, 2),

    # numeric for analysis
    beta_dev_round      = round(beta_dev, 3),

    alpha_fmt  = paste0(round(alpha, 3), star_fun(p_alpha_fdr)),
    beta_fmt   = paste0(round(beta,  3), star_fun(p_beta_fdr)),

    # Unified α-coding on % scale everywhere
    alpha_code = code_alpha_pp_pct(alpha_effect_pp_pct),

    # Keep β coding as before
    beta_code  = code_beta_dev(beta_dev),

    # NEW: signed string for display (e.g., "+2.03", "-0.89", "0.00")
    beta_dev_fmt = fmt_signed(beta_dev_round, digits = 2)
  ) %>%
  select(
    model, group, method, center_at,
    alpha, se_alpha, p_alpha, p_alpha_fdr, alpha_fmt,
    alpha_effect_pp_pct, alpha_code,
    beta,  se_beta,  p_beta,  p_beta_fdr,  beta_fmt,
    beta_dev_round, beta_dev_fmt, beta_code
  ) %>%
  arrange(method, model, group)

out_csv <- "regression_results_all_models_with_methods.csv"
write.csv(final_table, out_csv, row.names = FALSE)

message("Wrote ", out_csv, " (rows: ", nrow(final_table), ")")
message("Robust available: ", .robust_ok)
message("Plots at: ", normalizePath(plot_dir, mustWork = FALSE))
