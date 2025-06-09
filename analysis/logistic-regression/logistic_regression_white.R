library(visreg)

proportions = read.csv("../../scripts/output_converted.csv")
m_white.stereotyped = glm(genai_p_white ~ I(bls_p_white - 0.5), 
                          family=quasibinomial, data=proportions, weights=genai_n)


png(
  filename = "visreg_white_comparison.png",
  width    = 1500, height = 1000,
  res      = 150
)

visreg(
  m_white.stereotyped,
  "bls_p_white",
  scale = "response",
  rug   = FALSE,
  main  = "Difference in Representation Across 40 Career Terms for Race: White",
  xlab  = "BLS % White",
  ylab  = "GPT-4 % White"
)

points(genai_p_white ~ bls_p_white, data=proportions, pch=20)
#add some reference lines
abline(coef=c(0,1), lty="dashed")
abline(v=.5, lty="dashed")

dev.off()
