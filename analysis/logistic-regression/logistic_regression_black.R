library(visreg)

proportions = read.csv("../../scripts/output_converted.csv")
m_black.stereotyped = glm(genai_p_black ~ I(bls_p_black - 0.5), 
                          family=quasibinomial, data=proportions, weights=genai_n)


png(
  filename = "visreg_black_comparison.png",
  width    = 1500, height = 1000,
  res      = 150
)

visreg(
  m_black.stereotyped,
  "bls_p_black",
  scale = "response",
  rug   = FALSE,
  main  = "Difference in Representation Across 40 Career Terms for Race: Black",
  xlab  = "BLS % Black",
  ylab  = "GPT-4 % Black"
)

points(genai_p_black ~ bls_p_black, data=proportions, pch=20)
#add some reference lines
abline(coef=c(0,1), lty="dashed")
abline(v=.5, lty="dashed")

dev.off()
