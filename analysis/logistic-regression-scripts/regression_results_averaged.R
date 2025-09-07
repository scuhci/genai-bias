library(visreg)
library(broom)
library(dplyr)
library(purrr)
library(stats)

# ----------------------------
# Load data
# ----------------------------
proportions <- read.csv("analysis/percent-results/results_vs_BLS/averaged_differences_vs_BLS.csv")

# ----------------------------
# Helper to make one plot/PDF
# ----------------------------
plot_one <- function(group, pretty_group, out_pdf) {
  # dynamic column names
  bls_col   <- paste0("bls_p_", group)
  genai_col <- paste0("genai_p_", group)
  
  # fit model
  fml <- as.formula(paste0(genai_col, " ~ I(", bls_col, " - 0.5)"))
  m <- glm(
    fml,
    family  = quasibinomial,
    data    = proportions,
    weights = proportions$genai_n
  )
  
  # pdf device
  pdf(out_pdf, width = 8, height = 6)
  on.exit(dev.off(), add = TRUE)
  
  # Margins: normal top margin for title
  par(
    cex.main = 1.5,
    cex.lab  = 1.3,
    cex.axis = 1.3,
    mar      = c(6, 5, 4, 2)   # <- back to normal top margin
  )
  
  # axes limits
  xlim <- c(0, 1)
  ylim <- c(0, 1)
  
  # observed min/max for this group
  xvals   <- proportions[[bls_col]]
  min_bls <- min(xvals, na.rm = TRUE)
  max_bls <- max(xvals, na.rm = TRUE)
  
  # --- Empty plot ---
  # First draw the empty plot *without* main title
    plot(NA, xlim = xlim, ylim = ylim,
        xlab = paste("BLS proportion", pretty_group),
        ylab = paste("Average proportion", pretty_group),
        main = NULL)

    # Then add the title separately, nudged upward
    title(
    main = paste0(
        "Average ", pretty_group, " representation across 41 occupations"
    ),
    line = 2   # adjust padding above the plot
    )

  # --- Graph paper grid ---
  xticks <- axTicks(1)
  yticks <- axTicks(2)
  abline(v = xticks, col = "grey70", lty = "dotted", lwd = 0.8)
  abline(h = yticks, col = "grey70", lty = "dotted", lwd = 0.8)
  
  # --- Shade regions: left of min, right of max ---
  usr <- par("usr")
  yr  <- diff(usr[3:4])
  rect(xleft = usr[1], xright = min_bls,
       ybottom = usr[3], ytop = usr[4],
       col = rgb(0.5, 0.5, 0.5, 0.25), border = NA)
  rect(xleft = max_bls, xright = usr[2],
       ybottom = usr[3], ytop = usr[4],
       col = rgb(0.5, 0.5, 0.5, 0.25), border = NA)
  
  # --- visreg fit (compute only) ---
  vr <- visreg(m, bls_col, scale = "response", plot = FALSE)
  df <- vr$fit
  xv <- df[[bls_col]]
  ord <- order(xv)
  
  # CI band
  polygon(
    x = c(xv[ord], rev(xv[ord])),
    y = c(df$visregLwr[ord], rev(df$visregUpr[ord])),
    col = rgb(0.2, 0.4, 0.8, 0.2), border = NA
  )
  
  # Fitted line
  lines(xv[ord], df$visregFit[ord], lwd = 2)
  
  # Points
  points(proportions[[bls_col]], proportions[[genai_col]], pch = 20)
  
  # Reference line y = x
  abline(coef = c(0, 1), lty = "dashed")
  
  # --- Vertical lines for min & max observed ---
  abline(v = min_bls, col = "blue", lwd = 2, lty = "dotted")
  abline(v = max_bls, col = "red",  lwd = 2, lty = "dotted")
  
  # --- Labels ABOVE the plotting area, below the title ---
  min_label <- paste0("min observed = ", round(min_bls * 100, 1), "%")
  max_label <- paste0("max observed = ", round(max_bls * 100, 1), "%")
  
  # place labels just above the plotting region, not in the title space
  label_y <- usr[4] + 0.05 * yr   # adjust padding: 0.05 = modest, increase for more
  
  text(x = min_bls, y = label_y, labels = min_label, col = "blue", cex = 1.1, xpd = NA)
  text(x = max_bls, y = label_y, labels = max_label, col = "red",  cex = 1.1, xpd = NA)
}

# ----------------------------
# Make all five plots
# ----------------------------
groups <- list(
  list(key = "white",    pretty = "White",    file = "logreg_white.pdf"),
  list(key = "black",    pretty = "Black",    file = "logreg_black.pdf"),
  list(key = "asian",    pretty = "Asian",    file = "logreg_asian.pdf"),
  list(key = "hispanic", pretty = "Hispanic", file = "logreg_hispanic.pdf"),
  list(key = "women",    pretty = "Women",    file = "logreg_women.pdf")
)

for (g in groups) {
  plot_one(group = g$key, pretty_group = g$pretty, out_pdf = g$file)
}

# ----------------------------
# Helper to run one regression & extract alpha/beta tests
# ----------------------------
analyze_one <- function(group, pretty_group) {
  bls_col   <- paste0("bls_p_", group)
  genai_col <- paste0("genai_p_", group)
  
  fml <- as.formula(paste0(genai_col, " ~ I(", bls_col, " - 0.5)"))
  m <- glm(
    fml,
    family  = quasibinomial,
    data    = proportions,
    weights = proportions$genai_n
  )
  
  # extract coefs
  est <- coef(summary(m))
  alpha <- est[1, "Estimate"]
  se_alpha <- est[1, "Std. Error"]
  beta <- est[2, "Estimate"]
  se_beta <- est[2, "Std. Error"]
  
  # Wald tests
  z_alpha <- (alpha - 0) / se_alpha
  p_alpha <- 2 * pnorm(-abs(z_alpha))
  
  z_beta <- (beta - 1) / se_beta
  p_beta <- 2 * pnorm(-abs(z_beta))
  
  tibble(
    group = pretty_group,
    alpha = alpha, se_alpha = se_alpha, p_alpha = p_alpha,
    beta  = beta,  se_beta  = se_beta,  p_beta  = p_beta
  )
}

# ----------------------------
# Run for all groups
# ----------------------------
raw_results <- map_dfr(groups, ~ analyze_one(.x$key, .x$pretty))

# ----------------------------
# FDR correction
# ----------------------------
raw_results <- raw_results %>%
  mutate(
    p_alpha_fdr = p.adjust(p_alpha, method = "BH"),
    p_beta_fdr  = p.adjust(p_beta, method = "BH")
  )

# ----------------------------
# Significance stars
# ----------------------------
star_fun <- function(p) {
  if (p < 0.001) return("***")
  if (p < 0.01)  return("**")
  if (p < 0.05)  return("*")
  return("")
}

# Strength coding
code_alpha <- function(a, sig) {
  if (!sig) return("0")
  if (a > 0) {
    if (a < 0.1) return("+")
    if (a < 0.25) return("++")
    return("+++")
  } else {
    if (a > -0.1) return("-")
    if (a > -0.25) return("--")
    return("---")
  }
}

code_beta <- function(b, sig) {
  if (!sig) return("0")
  diff <- b - 1
  if (diff > 0) {
    if (diff < 0.1) return("+")
    if (diff < 0.25) return("++")
    return("+++")
  } else {
    if (diff > -0.1) return("-")
    if (diff > -0.25) return("--")
    return("---")
  }
}

# ----------------------------
# Build final table
# ----------------------------
final_table <- raw_results %>%
  rowwise() %>%
  mutate(
    alpha_fmt = paste0(round(alpha, 3), star_fun(p_alpha_fdr)),
    alpha_code = code_alpha(alpha, p_alpha_fdr < 0.05),
    beta_fmt  = paste0(round(beta, 3),  star_fun(p_beta_fdr)),
    beta_code = code_beta(beta,  p_beta_fdr  < 0.05)
  ) %>%
  ungroup() %>%
  select(group, alpha_fmt, alpha_code, beta_fmt, beta_code)


print(final_table)

# ----------------------------
# Export final table to CSV
# ----------------------------
write.csv(
  final_table,
  file = "regression_results_by_model.csv",
  row.names = FALSE
)
