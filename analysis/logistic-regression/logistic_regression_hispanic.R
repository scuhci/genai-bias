library(visreg)

proportions = read.csv("../../scripts/output_converted.csv")
m_hispanic.stereotyped = glm(genai_p_hispanic ~ I(bls_p_hispanic - 0.5), 
                          family=quasibinomial, data=proportions, weights=genai_n)


png(
  filename = "visreg_hispanic_comparison.png",
  width    = 1500, height = 1000,
  res      = 150
)

visreg(
  m_hispanic.stereotyped,
  "bls_p_hispanic",
  scale = "response",
  rug   = FALSE,
  main  = "Difference in Representation Across 40 Career Terms for Race: Hispanic",
  xlab  = "BLS % Hispanic",
  ylab  = "GPT-4 % Hispanic"
)

points(genai_p_hispanic ~ bls_p_hispanic, data=proportions, pch=20)
#add some reference lines
abline(coef=c(0,1), lty="dashed")
abline(v=.5, lty="dashed")

dev.off()


