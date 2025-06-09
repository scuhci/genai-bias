library(visreg)

proportions = read.csv("../../scripts/output_converted.csv")
m_asian.stereotyped = glm(genai_p_asian ~ I(bls_p_asian - 0.5), 
                          family=quasibinomial, data=proportions, weights=genai_n)


png(
  filename = "visreg_asian_comparison.png",
  width    = 1500, height = 1000,
  res      = 150
)

visreg(
  m_asian.stereotyped,
  "bls_p_asian",
  scale = "response",
  rug   = FALSE,
  main  = "Difference in Representation Across 40 Career Terms for Race: Asian",
  xlab  = "BLS % Asian",
  ylab  = "GPT-4 % Asian"
)

points(genai_p_asian ~ bls_p_asian, data=proportions, pch=20)
#add some reference lines
abline(coef=c(0,1), lty="dashed")
abline(v=.5, lty="dashed")

dev.off()



