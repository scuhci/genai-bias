library(ggplot2)
library(dplyr)
library(scales)

# Run this script from analysis/salary/
df <- read.csv("results/combined_models_comparison.csv")

plot_income <- function(df, model_col, model_name, out_pdf) {
  stopifnot(requireNamespace("visreg", quietly = TRUE))

  # Keep complete rows
  df0 <- df[complete.cases(df[, c("bls", model_col)]), ]

  x <- df0$bls
  y <- df0[[model_col]]

  # Model 
  m <- lm(y ~ poly(x, 3), data = df0)

  # Observed range
  min_bls <- min(x, na.rm = TRUE)
  max_bls <- max(x, na.rm = TRUE)

  # Device
  pdf(out_pdf, width = 8, height = 6); on.exit(dev.off(), add = TRUE)
  par(cex.main = 1.5, cex.lab = 1.3, cex.axis = 1.2, mar = c(7, 5, 4.5, 2))

  # Axes (RAW income scale)
  plot(NA,
     xlim = range(x, na.rm = TRUE) / 1000,
     ylim = range(y, na.rm = TRUE) / 1000,
     xlab = "BLS Income (Thousands USD)",
     ylab = sprintf("%s Income (Thousands USD)", model_name),
     main = NULL)

  title(main = sprintf("%s: Income vs. BLS", model_name), line = 2.3)

  # Grid
  xticks <- axTicks(1); yticks <- axTicks(2)
  abline(v = xticks, col = "grey70", lty = "dotted", lwd = 0.8)
  abline(h = yticks, col = "grey70", lty = "dotted", lwd = 0.8)

  # Shade outside observed range
  usr <- par("usr"); yr <- diff(usr[3:4])
  rect(usr[1], usr[3], min_bls / 1000, usr[4], col = rgb(0.5, 0.5, 0.5, 0.25), border = NA)

  rect(max_bls / 1000, usr[3], usr[2], usr[4], col = rgb(0.5, 0.5, 0.5, 0.25), border = NA)
  # ----------------------------
  # visreg curve
  # ----------------------------
  vr <- visreg::visreg(m, "x", scale = "response", plot = FALSE)
  df_fit <- vr$fit

  xv  <- df_fit$x
  ord <- order(xv)

  polygon(
    x = c(xv[ord], rev(xv[ord])) / 1000,
    y = c(df_fit$visregLwr[ord], rev(df_fit$visregUpr[ord])) / 1000,
    col = rgb(0.2, 0.4, 0.8, 0.2),
    border = NA
  )

  lines(xv[ord]/1000, df_fit$visregFit[ord]/1000, lwd = 2)

  # ----------------------------
  # Points
  # ----------------------------
  points(x / 1000, y / 1000, pch = 20)

  # ----------------------------
  # Parity line
  # ----------------------------
  abline(coef = c(0, 1), lty = "dashed")

  # ----------------------------
  # Min/Max verticals
  # ----------------------------
  abline(v = min_bls / 1000, col = "blue", lwd = 2, lty = "dotted")
  abline(v = max_bls / 1000, col = "red",  lwd = 2, lty = "dotted")

  # Labels
#   text(min_bls / 1000, usr[4] + 0.04*yr,
#      paste0("min observed = ", round(min_bls / 1000, 1)),
#      col = "blue", cex = 1.05, xpd = NA)

#   text(max_bls / 1000, usr[4] + 0.04*yr,
#      paste0("max observed = ", round(max_bls / 1000, 1)),
#      col = "red", cex = 1.05, xpd = NA)
}

df <- read.csv("results/combined_models_comparison.csv")

plot_income(df, "openai", "OpenAI", "regressions/openai_vs_bls.pdf")
plot_income(df, "gemini", "Gemini", "regressions/gemini_vs_bls.pdf")
plot_income(df, "deepseek", "DeepSeek", "regressions/deepseek_vs_bls.pdf")
plot_income(df, "mistral", "Mistral", "regressions/mistral_vs_bls.pdf")