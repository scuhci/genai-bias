# ============================
# Regression Results by Model
# (quasibinomial GLM; FDR BH)
# ============================

library(broom)
library(dplyr)
library(purrr)
library(readr)   # for read_csv; swap to read.csv if you prefer base
library(stats)

# ----------------------------
# Configure: where the 4 CSVs live
# ----------------------------
csv_dir <- "analysis/logistic-regression-scripts/results/csvs"
files <- list.files(csv_dir, pattern = "\\.csv$", full.names = TRUE)
print(files)
stopifnot(length(files) >= 1)

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
# Read each model CSV, run 5 regressions, stack
# ----------------------------
results_list <- list()

for (fp in files) {
  model_name <- pretty_model_name(fp)
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

  tmp <- map_dfr(groups, ~ analyze_one(df, model_name, .x$key, .x$pretty))
  results_list[[length(results_list) + 1]] <- tmp
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

message("Wrote regression_results_all_models.csv with ",
        nrow(final_table), " rows.")