library(ggplot2)
library(dplyr)
library(scales)

# ── Output folder (run this script from analysis/salary/) ────────────────────
dir.create("regressions/gender", showWarnings = FALSE, recursive = TRUE)

# ── Core plotting function ────────────────────────────────────────────────────
# df        : data frame for one model (columns: occupation, bls_men, ai_men,
#             bls_women, ai_women)
# gender    : "men" or "women"
# model_name: label used in axis / title
# out_pdf   : output file path
plot_income_gender <- function(df, gender, model_name, out_pdf) {
  stopifnot(requireNamespace("visreg", quietly = TRUE))
  stopifnot(gender %in% c("men", "women"))

  bls_col <- paste0("bls_", gender)
  ai_col  <- paste0("ai_",  gender)

  # Drop rows missing either column for this gender
  df0 <- df[complete.cases(df[, c(bls_col, ai_col)]), ]

  x <- df0[[bls_col]]
  y <- df0[[ai_col]]

  # Cubic polynomial regression
  m <- lm(y ~ poly(x, 3), data = df0)

  min_bls <- min(x, na.rm = TRUE)
  max_bls <- max(x, na.rm = TRUE)

  gender_label <- tools::toTitleCase(gender)
  pdf(out_pdf, width = 8, height = 6)
  on.exit(dev.off(), add = TRUE)

  par(cex.main = 1.5, cex.lab = 1.3, cex.axis = 1.2, mar = c(7, 5, 4.5, 2))

  plot(NA,
       xlim = range(x, na.rm = TRUE) / 1000,
       ylim = range(y, na.rm = TRUE) / 1000,
       xlab = sprintf("BLS Income – %s (Thousands USD)", gender_label),
       ylab = sprintf("%s Income – %s (Thousands USD)", model_name, gender_label),
       main = NULL)

  title(main = sprintf("%s (%s): Income vs. BLS", model_name, gender_label),
        line = 2.3)

  # Grid
  xticks <- axTicks(1); yticks <- axTicks(2)
  abline(v = xticks, col = "grey70", lty = "dotted", lwd = 0.8)
  abline(h = yticks, col = "grey70", lty = "dotted", lwd = 0.8)

  # Shade outside observed range
  usr <- par("usr"); yr <- diff(usr[3:4])
  rect(usr[1], usr[3], min_bls / 1000, usr[4],
       col = rgb(0.5, 0.5, 0.5, 0.25), border = NA)
  rect(max_bls / 1000, usr[3], usr[2], usr[4],
       col = rgb(0.5, 0.5, 0.5, 0.25), border = NA)

  # visreg confidence band + fit line
  vr     <- visreg::visreg(m, "x", scale = "response", plot = FALSE)
  df_fit <- vr$fit
  xv     <- df_fit$x
  ord    <- order(xv)

  polygon(
    x = c(xv[ord], rev(xv[ord])) / 1000,
    y = c(df_fit$visregLwr[ord], rev(df_fit$visregUpr[ord])) / 1000,
    col    = rgb(0.2, 0.4, 0.8, 0.2),
    border = NA
  )
  lines(xv[ord] / 1000, df_fit$visregFit[ord] / 1000, lwd = 2)

  # Points
  points(x / 1000, y / 1000, pch = 20)

  # Parity line (y = x)
  abline(coef = c(0, 1), lty = "dashed")

  # Min / max observed verticals
  abline(v = min_bls / 1000, col = "blue", lwd = 2, lty = "dotted")
  abline(v = max_bls / 1000, col = "red",  lwd = 2, lty = "dotted")

#   text(min_bls / 1000, usr[4] + 0.04 * yr,
#        paste0("min observed = ", round(min_bls / 1000, 1)),
#        col = "blue", cex = 1.05, xpd = NA)
#   text(max_bls / 1000, usr[4] + 0.04 * yr,
#        paste0("max observed = ", round(max_bls / 1000, 1)),
#        col = "red", cex = 1.05, xpd = NA)
}

# ── Load per-model CSVs and drop incomplete occupations ──────────────────────
models <- list(
  list(name = "DeepSeek", file = "results/comparison_deepseek_gender.csv"),
  list(name = "Gemini",   file = "results/comparison_gemini_gender.csv"),
  list(name = "Mistral",  file = "results/comparison_mistral_gender.csv"),
  list(name = "OpenAI",   file = "results/comparison_openai_gender.csv")
)

for (m in models) {
  df_raw <- read.csv(m$file, stringsAsFactors = FALSE)

  # Keep only occupations that have ALL four key columns populated
  df_clean <- df_raw[
    complete.cases(df_raw[, c("bls_men", "ai_men", "bls_women", "ai_women")]),
  ]

  n_dropped <- nrow(df_raw) - nrow(df_clean)
  message(sprintf("%s: %d/%d occupations retained (%d dropped for missing data)",
                  m$name, nrow(df_clean), nrow(df_raw), n_dropped))

  slug <- tolower(m$name)

  plot_income_gender(df_clean, "men",   m$name,
                     sprintf("regressions/gender/%s_men_vs_bls.pdf",   slug))
  plot_income_gender(df_clean, "women", m$name,
                     sprintf("regressions/gender/%s_women_vs_bls.pdf", slug))
}