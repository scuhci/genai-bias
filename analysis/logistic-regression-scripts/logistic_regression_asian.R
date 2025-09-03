library(visreg)

proportions <- read.csv("output.csv")
m_asian.stereotyped <- glm(
  genai_p_asian ~ I(bls_p_asian - 0.5),
  family = quasibinomial,
  data   = proportions,
  weights = genai_n
)

pdf("logreg_asian.pdf", width = 8, height = 6)
par(
  cex.main = 1.5,
  cex.lab  = 1.5,
  cex.axis = 1.3,
  mar      = c(5, 5, 4, 2)
)

# Limits & max observed
xlim <- c(0, 1)
ylim <- c(0, 1)
max_bls <- max(proportions$bls_p_asian, na.rm = TRUE)

# --- Set up empty plot ---
plot(NA, xlim = xlim, ylim = ylim,
     xlab = "BLS proportion asian",
     ylab = "Gemini 2.5 proportion asian",
     main = "Difference in Representation Across 40 Career Terms \nRace: asian")

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
  m_asian.stereotyped, "bls_p_asian",
  scale = "response",
  plot  = FALSE
)

df <- vr$fit
xv <- df$bls_p_asian
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
points(genai_p_asian ~ bls_p_asian, data = proportions, pch = 20)

# Reference line y = x
abline(coef = c(0, 1), lty = "dashed")

# Vertical red line + label at bottom
abline(v = max_bls, col = "red", lwd = 2, lty = "dotted")
text(x = max_bls, y = 0.05,   # <-- place near bottom
     labels = paste0("max observed = ", round(max_bls * 100, 1), "%"),
     pos = 4, col = "red", cex = 1.2)

dev.off()
