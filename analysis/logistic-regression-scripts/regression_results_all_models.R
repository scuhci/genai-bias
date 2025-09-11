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
