library(visreg)

proportions <- read.csv("../percent-results/results_vs_BLS/averaged_differences_vs_BLS.csv")
m_hispanic.stereotyped <- glm(
  genai_p_hispanic ~ I(bls_p_hispanic - 0.5),
  family = quasibinomial,
  data   = proportions,
  weights = genai_n
)

pdf("logreg_hispanic.pdf", width = 8, height = 6)
par(
  cex.main = 1.5,
  cex.lab  = 1.5,
  cex.axis = 1.3,
  mar      = c(5, 5, 4, 2)
)

# Limits & max observed
xlim <- c(0, 1)
ylim <- c(0, 1)
max_bls <- max(proportions$bls_p_hispanic, na.rm = TRUE)

# --- Set up empty plot ---
plot(NA, xlim = xlim, ylim = ylim,
     xlab = "BLS proportion hispanic",
     ylab = "Average proportion hispanic",
     main = "Average Difference in Representation Across All Occupations \nRace: hispanic")

# --- Darker graph-paper style grid ---
xticks <- axTicks(1)  # x-axis tick positions
yticks <- axTicks(2)  # y-axis tick positions
abline(v = xticks, col = "grey70", lty = "dotted", lwd = 0.8)
abline(h = yticks, col = "grey70", lty = "dotted", lwd = 0.8)

# --- Shaded region to the right of max observed ---
usr <- par("usr")
rect(xleft = max_bls, xright = usr[2],
     ybottom = usr[3], ytop = usr[4],
     col = rgb(0.5, 0.5, 0.5, 0.25), border = NA)

# --- Visreg fit (compute only, then plot) ---
vr <- visreg(
  m_hispanic.stereotyped, "bls_p_hispanic",
  scale = "response",
  plot  = FALSE
)

df <- vr$fit
xv <- df$bls_p_hispanic
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
points(genai_p_hispanic ~ bls_p_hispanic, data = proportions, pch = 20)

# Reference line y = x
abline(coef = c(0, 1), lty = "dashed")

# Vertical red line + label at bottom
abline(v = max_bls, col = "red", lwd = 2, lty = "dotted")
text(x = max_bls, y = 0.05,   # <-- place near bottom
     labels = paste0("max observed = ", round(max_bls * 100, 1), "%"),
     pos = 4, col = "red", cex = 1.2)

dev.off()
