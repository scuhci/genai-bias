library(visreg)

proportions = read.csv("../../scripts/output_converted.csv")
m_women.stereotyped = glm(genai_p_women ~ I(bls_p_women - 0.5), 
                          family=quasibinomial, data=proportions, weights=genai_n)


png(
  filename = "visreg_women_comparison.png",
  width    = 1500, height = 1000,
  res      = 150
)

visreg(
  m_women.stereotyped,
  "bls_p_women",
  scale = "response",
  rug   = FALSE,
  main  = "Difference in Representation Across 40 Career Terms for Gender: Women",
  xlab  = "BLS % Women",
  ylab  = "GPT-4 % Women"
)

points(genai_p_women ~ bls_p_women, data=proportions, pch=20)
#add some reference lines
abline(coef=c(0,1), lty="dashed")
abline(v=.5, lty="dashed")

dev.off()

