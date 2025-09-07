# ============================
# Regression Results by Model
# (quasibinomial GLM; FDR BH)
# + Plot generation
# ============================

library(broom)
library(dplyr)
library(purrr)
library(readr) 
library(stats)
library(visreg)   # <-- needed for fitted line + CI
library(tools)

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
# Same 5 groups (keys = suffixes in columns)
# ----------------------------
groups <- list(
  list(key = "white",    pretty = "White"),
  list(key = "black",    pretty = "Black"),
  list(key = "asian",    pretty = "Asian"),
  list(key = "hispanic", pretty = "Hispanic"),
  list(key = "women",    pretty = "Women")
)

# ----------------------------
# Vectorized helpers (stars & codes)
# ----------------------------
star_fun <- function(p) dplyr::case_when(
  p < 0.001 ~ "***",
  p < 0.01  ~ "**",
  p < 0.05  ~ "*",
  TRUE      ~ ""
)

code_alpha <- function(a, sig) {
  out <- ifelse(sig, "", "0")
  out <- ifelse(sig & a >  0    & a <  0.10, "+",   out)
  out <- ifelse(sig & a >= 0.10 & a <  0.25, "++",  out)
  out <- ifelse(sig & a >= 0.25,               "+++", out)
  out <- ifelse(sig & a <= 0     & a > -0.10, "-",   out)
  out <- ifelse(sig & a <= -0.10 & a > -0.25, "--",  out)
  out <- ifelse(sig & a <= -0.25,              "---", out)
  out
}

code_beta <- function(b, sig) {
  d <- b - 1
  out <- ifelse(sig, "", "0")
  out <- ifelse(sig & d >  0    & d <  0.10, "+",   out)
  out <- ifelse(sig & d >= 0.10 & d <  0.25, "++",  out)
  out <- ifelse(sig & d >= 0.25,              "+++", out)
  out <- ifelse(sig & d <= 0     & d > -0.10, "-",   out)
  out <- ifelse(sig & d <= -0.10 & d > -0.25, "--",  out)
  out <- ifelse(sig & d <= -0.25,              "---", out)
  out
}

# ----------------------------
# Core analyzer (DO NOT change the regression itself)
# ----------------------------
analyze_one <- function(df, model_name, group_key, group_pretty) {
  bls_col   <- paste0("bls_p_",   group_key)
  genai_col <- paste0("genai_p_", group_key)

  # fit model exactly as before
  fml <- as.formula(paste0(genai_col, " ~ I(", bls_col, " - 0.5)"))
  m <- glm(
    fml,
    family  = quasibinomial,
    data    = df,
    weights = df$genai_n
  )

  est <- coef(summary(m))
  alpha    <- est[1, "Estimate"]
  se_alpha <- est[1, "Std. Error"]
  beta     <- est[2, "Estimate"]
  se_beta  <- est[2, "Std. Error"]

  # Wald tests (alpha vs 0; beta vs 1)
  z_alpha <- (alpha - 0) / se_alpha
  p_alpha <- 2 * pnorm(-abs(z_alpha))
  z_beta  <- (beta  - 1) / se_beta
  p_beta  <- 2 * pnorm(-abs(z_beta))

  tibble(
    model = model_name,
    group = group_pretty,
    alpha = alpha, se_alpha = se_alpha, p_alpha = p_alpha,
    beta  = beta,  se_beta  = se_beta,  p_beta  = p_beta
  )
}

# ----------------------------
# Plotter (same regression; PDF output)
# ----------------------------
plot_one_model_group <- function(df, model_name, group_key, group_pretty, out_pdf) {
  bls_col   <- paste0("bls_p_",   group_key)
  genai_col <- paste0("genai_p_", group_key)

  # --- Fit model EXACTLY as analysis ---
  fml <- as.formula(paste0(genai_col, " ~ I(", bls_col, " - 0.5)"))
  m <- glm(
    fml,
    family  = quasibinomial,
    data    = df,
    weights = df$genai_n
  )

  # axis limits & observed min/max
  xlim <- c(0, 1)
  ylim <- c(0, 1)
  xvals   <- df[[bls_col]]
  min_bls <- min(xvals, na.rm = TRUE)
  max_bls <- max(xvals, na.rm = TRUE)

  # open device
  pdf(out_pdf, width = 8, height = 6)
  on.exit(dev.off(), add = TRUE)

  par(
    cex.main = 1.5,
    cex.lab  = 1.3,
    cex.axis = 1.2,
    mar      = c(6, 5, 4, 2)
  )

  # Base empty plot, no main title yet
  plot(NA, xlim = xlim, ylim = ylim,
       xlab = paste("BLS proportion", group_pretty),
       ylab = paste("Average proportion", group_pretty),
       main = NULL)

  # Title (kept separate for cleaner spacing)
  title(
    main = paste0(model_name, ": Average ", group_pretty, " representation across 41 occupations"),
    line = 2
  )

  # Graph-paper grid
  xticks <- axTicks(1); yticks <- axTicks(2)
  abline(v = xticks, col = "grey70", lty = "dotted", lwd = 0.8)
  abline(h = yticks, col = "grey70", lty = "dotted", lwd = 0.8)

  # Shade regions outside observed range
  usr <- par("usr")
  yr  <- diff(usr[3:4])
  rect(xleft = usr[1], xright = min_bls, ybottom = usr[3], ytop = usr[4],
       col = rgb(0.5, 0.5, 0.5, 0.25), border = NA)
  rect(xleft = max_bls, xright = usr[2], ybottom = usr[3], ytop = usr[4],
       col = rgb(0.5, 0.5, 0.5, 0.25), border = NA)

  # visreg fit (compute only)
  vr <- visreg(m, bls_col, scale = "response", plot = FALSE)
  df_fit <- vr$fit
  xv <- df_fit[[bls_col]]
  ord <- order(xv)

  # CI band
  polygon(
    x = c(xv[ord], rev(xv[ord])),
    y = c(df_fit$visregLwr[ord], rev(df_fit$visregUpr[ord])),
    col = rgb(0.2, 0.4, 0.8, 0.2), border = NA
  )

  # Fitted line
  lines(xv[ord], df_fit$visregFit[ord], lwd = 2)

  # Observed points (weighted positions; plotting regular points is fine)
  points(df[[bls_col]], df[[genai_col]], pch = 20)

  # Reference y = x
  abline(coef = c(0, 1), lty = "dashed")

  # Vertical lines & labels at min/max
  abline(v = min_bls, col = "blue", lwd = 2, lty = "dotted")
  abline(v = max_bls, col = "red",  lwd = 2, lty = "dotted")

  min_label <- paste0("min observed = ", round(min_bls * 100, 1), "%")
  max_label <- paste0("max observed = ", round(max_bls * 100, 1), "%")
  label_y <- usr[4] + 0.05 * yr

  text(x = min_bls, y = label_y, labels = min_label, col = "blue", cex = 1.1, xpd = NA)
  text(x = max_bls, y = label_y, labels = max_label, col = "red",  cex = 1.1, xpd = NA)
}

# ----------------------------
# Read each model CSV, run 5 regressions, stack, and plot
# ----------------------------
results_list <- list()

for (fp in files) {
  model_pretty <- pretty_model_name(fp)
  df <- suppressMessages(suppressWarnings(read_csv(fp, show_col_types = FALSE)))

  # minimal sanity check for required columns
  req_cols <- c("genai_n",
                paste0("bls_p_",   sapply(groups, `[[`, "key")),
                paste0("genai_p_", sapply(groups, `[[`, "key")))
  missing <- setdiff(req_cols, names(df))
  if (length(missing) > 0) {
    stop(sprintf("File '%s' is missing required columns: %s",
                 basename(fp), paste(missing, collapse = ", ")))
  }

  # analysis rows
  tmp <- map_dfr(groups, ~ analyze_one(df, model_pretty, .x$key, .x$pretty))
  results_list[[length(results_list) + 1]] <- tmp

  # plots for this model across all 5 groups
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
# FDR (Benjamini–Hochberg) across ALL tests
# ----------------------------
raw_results <- raw_results %>%
  mutate(
    p_alpha_fdr = p.adjust(p_alpha, method = "BH"),
    p_beta_fdr  = p.adjust(p_beta,  method = "BH")
  )

# ----------------------------
# Format: stars & symbol codes
# ----------------------------
final_table <- raw_results %>%
  mutate(
    alpha_fmt  = paste0(round(alpha, 3), star_fun(p_alpha_fdr)),
    alpha_code = code_alpha(alpha, p_alpha_fdr < 0.05),
    beta_fmt   = paste0(round(beta,  3), star_fun(p_beta_fdr)),
    beta_code  = code_beta(beta,  p_beta_fdr  < 0.05)
  ) %>%
  select(
    model, group,
    alpha, se_alpha, p_alpha, p_alpha_fdr, alpha_fmt, alpha_code,
    beta,  se_beta,  p_beta,  p_beta_fdr,  beta_fmt,  beta_code
  ) %>%
  arrange(model, group)

# ----------------------------
# Export CSV
# ----------------------------
write.csv(final_table, "regression_results_all_models.csv", row.names = FALSE)

message("Wrote regression_results_all_models.csv with ", nrow(final_table), " rows.")
message("Wrote plots to: ", normalizePath(plot_dir, mustWork = FALSE))
