library(visreg)

proportions = read.csv("output_converted.csv")
m_black.stereotyped = glm(
  genai_p_black ~ I(bls_p_black - 0.5), 
  family = quasibinomial, 
  data   = proportions, 
  weights = genai_n
)

pdf("visreg_black_comparison.pdf", width=8, height=6)
par(
  cex.main = 1.5,   # title
  cex.lab  = 1.5,   # axis labels
  cex.axis = 1.3,   # axis tick labels
  mar      = c(5, 5, 4, 2)  # margins
)

visreg(
  m_black.stereotyped,
  "bls_p_black",
  scale = "response",
  rug   = FALSE,
  main  = "Difference in Representation Across 40 Career Terms \nRace: black",
  xlab  = "BLS proportion black",
  ylab  = "GPT-4 proportion black",
  xlim  = c(0,1),    # force x-axis from 0–1
  ylim  = c(0,1)     # optional: force y-axis from 0–1 as well
)

points(genai_p_black ~ bls_p_black, data=proportions, pch=20)

# reference lines
abline(coef=c(0,1), lty="dashed") # y = x
abline(v=.5, lty="dashed")

dev.off()
